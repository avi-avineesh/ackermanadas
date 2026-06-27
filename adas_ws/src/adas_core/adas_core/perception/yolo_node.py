"""
yolo_node.py — YOLOv11n INT8 object detection (vehicle detection only).

Subscribes : /camera/image_raw          (sensor_msgs/Image)
Publishes  : /perception/detections     (BoundingBox2DArray)
             /perception/vehicle_distance    (std_msgs/Float32)

Core affinity: os.sched_setaffinity(0, {0, 1}) is called in main() before rclpy.init().
"""

import os
import threading

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from std_msgs.msg import Float32

from adas_msgs.msg import BoundingBox2D, BoundingBox2DArray

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

INFER_W = 320
INFER_H = 240
ORIG_W = 640
ORIG_H = 480
SCALE_X = ORIG_W / INFER_W   # 2.0
SCALE_Y = ORIG_H / INFER_H   # 2.0

CLASS_VEHICLE = 0

FOCAL_PX = 800.0
VEHICLE_HEIGHT_M = 0.30


# ──────────────────────────────────────────────────────────────────────────────
# Node
# ──────────────────────────────────────────────────────────────────────────────

class YoloNode(Node):
    """
    YOLOv11n object detection node (vehicle detection only).

    Architecture:
      - ROS callback stores the latest frame under a Lock.
      - A dedicated inference thread wakes on a threading.Event, runs YOLO,
        and publishes results — decoupling network I/O from the ROS executor.
    """

    def __init__(self) -> None:
        super().__init__('yolo_node')

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter('model_path', '~/models/yolo11n_adas.pt')
        self.declare_parameter('conf_threshold', 0.45)

        model_path_raw: str = self.get_parameter('model_path').get_parameter_value().string_value
        self._conf_thresh: float = (
            self.get_parameter('conf_threshold').get_parameter_value().double_value
        )
        model_path = os.path.expanduser(model_path_raw)

        # ── CV Bridge ─────────────────────────────────────────────────────────
        self._bridge = CvBridge()

        # ── Model loading ─────────────────────────────────────────────────────
        self._model = None
        self._model_ready = False
        self._load_model(model_path)

        # ── Threading ─────────────────────────────────────────────────────────
        self._frame_lock = threading.Lock()
        self._latest_frame: np.ndarray | None = None
        self._new_frame_event = threading.Event()
        self._shutdown_flag = threading.Event()

        self._inference_thread = threading.Thread(
            target=self._inference_loop,
            name='yolo_inference',
            daemon=True,
        )

        # ── QoS ───────────────────────────────────────────────────────────────
        img_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # ── Subscribers ───────────────────────────────────────────────────────
        self._image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self._image_callback,
            img_qos,
        )

        # ── Publishers ────────────────────────────────────────────────────────
        self._det_pub  = self.create_publisher(BoundingBox2DArray, '/perception/detections', 10)
        self._dist_pub = self.create_publisher(Float32, '/perception/vehicle_distance', 10)

        # ── Start inference thread ────────────────────────────────────────────
        self._inference_thread.start()
        self.get_logger().info(
            f'YoloNode ready — model_path={model_path}, conf={self._conf_thresh}'
        )

    # ── Model loading ─────────────────────────────────────────────────────────

    def _load_model(self, model_path: str) -> None:
        if not os.path.isfile(model_path):
            self.get_logger().error(
                f'YOLO model not found at "{model_path}". '
                'Node will publish empty detections until a valid model is provided.'
            )
            return
        try:
            from ultralytics import YOLO  # type: ignore[import]
            self._model = YOLO(model_path)
            # Warm-up pass to initialise CUDA / TensorRT contexts
            dummy = np.zeros((INFER_H, INFER_W, 3), dtype=np.uint8)
            self._model(dummy, verbose=False, conf=self._conf_thresh)
            self._model_ready = True
            self.get_logger().info(f'YOLO model loaded from "{model_path}".')
        except Exception as exc:  # noqa: BLE001
            self.get_logger().error(f'Failed to load YOLO model: {exc}')

    # ── ROS image callback ────────────────────────────────────────────────────

    def _image_callback(self, msg: Image) -> None:
        """Store the latest frame and signal the inference thread."""
        try:
            frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warning(f'cv_bridge conversion failed: {exc}')
            return

        with self._frame_lock:
            self._latest_frame = frame
        self._new_frame_event.set()

    # ── Inference thread ──────────────────────────────────────────────────────

    def _inference_loop(self) -> None:
        """Blocking loop that runs YOLO on the latest frame whenever one arrives."""
        while not self._shutdown_flag.is_set():
            triggered = self._new_frame_event.wait(timeout=0.5)
            if not triggered:
                continue
            self._new_frame_event.clear()

            with self._frame_lock:
                frame = self._latest_frame
                if frame is None:
                    continue
                frame = frame.copy()  # release lock quickly

            try:
                self._run_inference(frame)
            except Exception as exc:  # noqa: BLE001
                self.get_logger().error(f'Inference error: {exc}', throttle_duration_sec=2.0)
                self._publish_empty()

    # ── Core inference ────────────────────────────────────────────────────────

    def _run_inference(self, frame_orig: np.ndarray) -> None:
        """Run YOLO on a resized frame, then post-process and publish."""
        if not self._model_ready:
            self._publish_empty()
            return

        # ── Resize for inference ──────────────────────────────────────────────
        img_320 = cv2.resize(frame_orig, (INFER_W, INFER_H))

        results = self._model(img_320, verbose=False, conf=self._conf_thresh)
        if results is None or len(results) == 0:
            self._publish_empty()
            return

        boxes_result = results[0].boxes
        if boxes_result is None or len(boxes_result) == 0:
            self._publish_empty()
            return

        # ── Extract boxes ─────────────────────────────────────────────────────
        # xyxy coords are in INFER space; scale back to original
        xyxy_infer   = boxes_result.xyxy.cpu().numpy()     # (N, 4)
        confidences  = boxes_result.conf.cpu().numpy()     # (N,)
        class_ids    = boxes_result.cls.cpu().numpy().astype(int)  # (N,)

        class_names_map = results[0].names  # dict {int: str}

        det_array = BoundingBox2DArray()
        det_array.header.stamp = self.get_clock().now().to_msg()
        det_array.header.frame_id = 'camera_link'

        vehicle_distances: list[float] = []

        for i in range(len(class_ids)):
            cls_id  = int(class_ids[i])
            conf    = float(confidences[i])
            x1_i, y1_i, x2_i, y2_i = xyxy_infer[i]

            # Scale to original image coordinates
            x1 = x1_i * SCALE_X
            y1 = y1_i * SCALE_Y
            x2 = x2_i * SCALE_X
            y2 = y2_i * SCALE_Y
            w  = x2 - x1
            h  = y2 - y1

            # Build BoundingBox2D (x,y = top-left corner)
            bbox = BoundingBox2D()
            bbox.x          = float(x1)
            bbox.y          = float(y1)
            bbox.w          = float(w)
            bbox.h          = float(h)
            bbox.confidence = conf
            bbox.class_id   = cls_id
            bbox.class_name = class_names_map.get(cls_id, str(cls_id))
            det_array.boxes.append(bbox)

            # ── Vehicle distance estimation ───────────────────────────────────
            if cls_id == CLASS_VEHICLE and h > 0:
                dist = (FOCAL_PX * VEHICLE_HEIGHT_M) / h
                vehicle_distances.append(dist)

        # ── Publish ───────────────────────────────────────────────────────────
        self._det_pub.publish(det_array)

        dist_msg = Float32()
        dist_msg.data = float(min(vehicle_distances)) if vehicle_distances else -1.0
        self._dist_pub.publish(dist_msg)

    # ── Empty-publish helper ──────────────────────────────────────────────────

    def _publish_empty(self) -> None:
        """Publish empty/default messages when inference cannot run."""
        empty = BoundingBox2DArray()
        empty.header.stamp = self.get_clock().now().to_msg()
        empty.header.frame_id = 'camera_link'
        self._det_pub.publish(empty)

        dist_msg = Float32()
        dist_msg.data = -1.0
        self._dist_pub.publish(dist_msg)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def destroy_node(self) -> None:
        """Cleanly stop the inference thread before shutting down."""
        self.get_logger().info('YoloNode shutting down — stopping inference thread.')
        self._shutdown_flag.set()
        self._new_frame_event.set()  # unblock any waiting call
        self._inference_thread.join(timeout=3.0)
        super().destroy_node()


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main(args=None) -> None:
    # Pin this process to cores 0 and 1 before initialising ROS
    try:
        os.sched_setaffinity(0, {0, 1})
    except (AttributeError, OSError) as exc:
        # sched_setaffinity is Linux-only; ignore gracefully on other platforms
        print(f'[yolo_node] sched_setaffinity unavailable: {exc}')

    rclpy.init(args=args)
    node = YoloNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
