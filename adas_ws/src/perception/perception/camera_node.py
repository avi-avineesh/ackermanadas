#!/usr/bin/env python3
"""
camera_node.py — Perception Layer: YOLO11n Camera Processing
═════════════════════════════════════════════════════════════
Package : perception | Pi cores 0-1 (YOLO inference is CPU-heavy)

WHAT THIS NODE DOES:
  Subscribes /ego/camera/image_raw (640×480, 30Hz from Gazebo or IMX219).
  Runs YOLO11n (COCO 80 classes) inference on every frame.
  Filters: car(2), truck(7), bus(5), person(0). Confidence threshold: 0.35.
  Publishes Detection2DArray to /ego/detections for aeb_node consumption.
  Publishes annotated debug image to /ego/camera/debug.

HOW YOLO11n CONFIDENCE IS PASSED (no custom messages):
  The best vehicle detection confidence score (0.0–1.0) is encoded as:
    det.header.stamp.nanosec = int(best_conf * 1000)
  aeb_node reads it back as: conf = msg.detections[0].header.stamp.nanosec / 1000.0
  This avoids adding a custom ROS2 message definition for a single float.

CAMERA DISTANCE ESTIMATION (pinhole model):
  Focal length: f_x = (640/2) / tan(40°) ≈ 381 px  (hfov=80° → half=40°)
  Real obstacle height: H_real = 0.36m (black car body in aeb_world.sdf)
  Formula: dist_m = (H_real × f_x) / bbox_height_px = (0.36 × 381) / bbox_h
  Example: bbox_h=72px → dist=1.90m (WARNING zone)
           bbox_h=180px → dist=0.76m (HARD zone)
  Override: bbox_h > 220px → force dist = HARD_DIST (object fills camera)

DEBUG FRAME OVERLAY:
  Top-left confidence bar (300px wide, 14px tall):
    GREEN  (conf > 0.60) → "HIGH — AND mode"
    YELLOW (conf > 0.20) → "MED  — advisory"
    RED    (else)        → "LOW  — LiDAR only"
  Bottom-left status line: "Detections: N | YOLO: ON/OFF | Fusion: HIGH/MED/LOW"
  Bounding boxes: green=car, red=person, orange=truck/bus
  Label above box: "car 87%" | Distance below: "1.90m"
  Bottom-right: HH:MM:SS.mmm timestamp

HARDWARE NOTE:
  In simulation: Gazebo → ros_gz_bridge → /ego/camera/image_raw
  On Pi 5: picamera2 publishes the same topic from the IMX219 (MIPI-CSI).
  Zero code changes between simulation and hardware deployment.
  Run with taskset -c 0,1 for YOLO inference on Pi5 cores 0-1.

TOPICS:
  Subscribes: /ego/camera/image_raw  (sensor_msgs/Image)
  Publishes:  /ego/detections        (vision_msgs/Detection2DArray)
              /ego/camera/debug      (sensor_msgs/Image)
"""

import math
from datetime import datetime

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

# ── Optional imports (guarded) ────────────────────────────────────────────────
try:
    from ultralytics import YOLO
    YOLO_OK = True
except ImportError:
    YOLO_OK = False

try:
    from cv_bridge import CvBridge
    import cv2
    import numpy as np
    CV_OK = True
except ImportError:
    CV_OK = False

try:
    from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
    VISION_OK = True
except ImportError:
    VISION_OK = False
    from std_msgs.msg import String  # fallback

# ── Constants ─────────────────────────────────────────────────────────────────
FOCAL_PX        = 381.0   # px — (320 / tan(40°)) — IMX219 hfov=80°
OBJ_H_M         = 0.36    # m  — real height of car_obstacle body in world
CONF_THRESH     = 0.35    # —  — YOLO minimum confidence
CLASSES_OK      = {0, 2, 5, 7}  # person=0 car=2 bus=5 truck=7 (COCO IDs)
HARD_DIST_FORCE = 0.80    # m  — forced distance when bbox_h > 220px
BBOX_HARD_PX    = 220     # px — bbox height threshold for distance override

# Fusion mode confidence thresholds (mirrored in aeb_node)
CONF_HIGH = 0.60  # above this → AND mode (green)
CONF_MED  = 0.20  # above this → advisory (yellow), below → LiDAR-only (red)


class CameraNode(Node):
    """YOLO11n detection + debug publisher. Pi cores 0-1."""

    def __init__(self):
        super().__init__('camera_node')

        if not YOLO_OK:
            self.get_logger().warn(
                '[camera_node] YOLO11n not installed. Run:\n'
                '  pip install ultralytics --break-system-packages\n'
                'Publishing empty detections until installed.'
            )
        if not CV_OK:
            self.get_logger().warn('[camera_node] cv_bridge/cv2 unavailable — image processing disabled.')
        if not VISION_OK:
            self.get_logger().warn('[camera_node] vision_msgs unavailable — detections as String.')

        # ── Load YOLO11n model ────────────────────────────────────────────
        self._yolo = None
        if YOLO_OK:
            try:
                self._yolo = YOLO('/tmp/yolo_runs/adas_car_v2/weights/best.pt')  # ~6MB download on first run
                self.get_logger().info('[camera_node] YOLO11n model loaded.')
            except Exception as e:
                self.get_logger().error(f'[camera_node] Failed to load YOLO11n: {e}')

        self._bridge = CvBridge() if CV_OK else None

        # ── Publishers ────────────────────────────────────────────────────
        if VISION_OK:
            self._pub_det = self.create_publisher(Detection2DArray, '/ego/detections', 10)
        else:
            self._pub_det = self.create_publisher(String, '/ego/detections', 10)
        self._pub_debug = self.create_publisher(Image, '/ego/camera/debug', 10)

        # ── Subscriber ───────────────────────────────────────────────────
        self.create_subscription(Image, '/ego/camera/image_raw', self._image_cb, 10)

        self.get_logger().info('[camera_node] Ready — /ego/camera/image_raw')

    def _image_cb(self, msg: Image):
        """Run YOLO11n inference, publish detections + annotated debug frame."""
        if not CV_OK:
            return

        try:
            frame = self._bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'[camera_node] imgmsg_to_cv2 failed: {e}')
            return

        debug = frame.copy()

        if VISION_OK:
            det_arr = Detection2DArray()
            det_arr.header = msg.header
        else:
            det_arr = None

        raw_dets = []  # (cls_id, label, conf, dist_m, bbox_h, x1, y1, x2, y2)
        best_conf = 0.0

        if self._yolo is not None:
            try:
                results = self._yolo(frame, verbose=False, conf=CONF_THRESH)
                for result in results:
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        if cls_id not in CLASSES_OK:
                            continue
                        conf  = float(box.conf[0])
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        bbox_h = max(1, y2 - y1)
                        bbox_w = max(1, x2 - x1)
                        label  = result.names[cls_id]

                        # Distance estimate
                        if bbox_h > BBOX_HARD_PX:
                            dist_m = HARD_DIST_FORCE
                        elif bbox_h > 5:
                            dist_m = (OBJ_H_M * FOCAL_PX) / bbox_h
                        else:
                            dist_m = float('inf')

                        # Track best vehicle confidence
                        if cls_id in {2, 5, 7}:  # vehicle classes
                            best_conf = max(best_conf, conf)

                        raw_dets.append((cls_id, label, conf, dist_m, bbox_h, x1, y1, x2, y2))

                        if VISION_OK:
                            det = Detection2D()
                            det.header = msg.header
                            det.header.frame_id = f'{dist_m:.3f}'
                            det.bbox.center.position.x = (x1 + x2) / 2.0
                            det.bbox.center.position.y = (y1 + y2) / 2.0
                            det.bbox.size_x = float(bbox_w)
                            det.bbox.size_y = float(bbox_h)
                            hyp = ObjectHypothesisWithPose()
                            hyp.hypothesis.class_id = str(cls_id)
                            hyp.hypothesis.score    = conf
                            det.results.append(hyp)
                            det_arr.detections.append(det)

            except Exception as e:
                self.get_logger().error(f'[camera_node] YOLO inference error: {e}')

        # ── Encode best_conf in stamp.nanosec ─────────────────────────────
        if VISION_OK and det_arr is not None:
            det_arr.header.stamp.nanosec = int(best_conf * 1000)
            self._pub_det.publish(det_arr)
        else:
            s_msg = String()
            s_msg.data = f'detections:{len(raw_dets)}:conf:{best_conf:.3f}'
            self._pub_det.publish(s_msg)

        # ── Draw bounding boxes ───────────────────────────────────────────
        for (cls_id, label, conf, dist_m, bbox_h, x1, y1, x2, y2) in raw_dets:
            colour = (0, 255, 0) if cls_id == 2 else \
                     (0, 0, 255) if cls_id == 0 else (0, 165, 255)
            cv2.rectangle(debug, (x1, y1), (x2, y2), colour, 2)
            cv2.putText(debug, f'{label} {conf:.0%}', (x1, max(y1 - 8, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, colour, 2)
            dist_str = f'{dist_m:.2f}m' if math.isfinite(dist_m) else 'far'
            cv2.putText(debug, dist_str, (x1, y2 + 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.50, colour, 1)

        # ── Confidence bar top-left ───────────────────────────────────────
        if best_conf > CONF_HIGH:
            bar_col = (0, 230, 118)   # green
            mode_str = 'HIGH — AND mode'
        elif best_conf > CONF_MED:
            bar_col = (0, 234, 255)   # yellow
            mode_str = 'MED  — advisory'
        else:
            bar_col  = (0, 23, 255)   # red
            mode_str = 'LOW  — LiDAR only'

        bar_w = int(best_conf * 200)
        cv2.rectangle(debug, (8, 8), (8 + bar_w, 22), bar_col, -1)
        cv2.rectangle(debug, (8, 8), (208, 22), (100, 100, 100), 1)
        cv2.putText(debug, mode_str, (214, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, bar_col, 1)

        # ── Status line bottom-left ───────────────────────────────────────
        n = len(raw_dets)
        yolo_str = 'ON' if self._yolo else 'OFF'
        fusion_str = 'HIGH' if best_conf > CONF_HIGH else \
                     ('MED' if best_conf > CONF_MED else 'LOW')
        cv2.putText(debug,
                    f'Detections: {n} | YOLO: {yolo_str} | Fusion: {fusion_str}',
                    (8, 464), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 230), 1)

        # ── Timestamp bottom-right ────────────────────────────────────────
        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        cv2.putText(debug, ts, (490, 472),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (128, 128, 128), 1)

        # ── Publish debug frame ───────────────────────────────────────────
        try:
            dbg_msg = self._bridge.cv2_to_imgmsg(debug, 'bgr8')
            dbg_msg.header = msg.header
            self._pub_debug.publish(dbg_msg)
        except Exception as e:
            self.get_logger().error(f'[camera_node] debug publish failed: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, Exception):
        pass
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
