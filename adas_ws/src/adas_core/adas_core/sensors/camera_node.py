"""
camera_node.py
--------------
ROS2 Jazzy node for IMX219 camera via rpicam-still subprocess at 640×480, 10 Hz.

Publishes:
  /camera/image_raw        (sensor_msgs/Image)            — BGR8 raw frames
  /camera/image_compressed (sensor_msgs/CompressedImage)  — JPEG compressed

Uses CvBridge for numpy→ROS Image conversion.
Parameters: width, height, fps, jpeg_quality.
"""

import subprocess

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import CompressedImage, Image

import cv2
from cv_bridge import CvBridge

_TMP_FRAME = '/tmp/frame.jpg'
_CAPTURE_HZ = 10.0


class CameraNode(Node):
    """Captures IMX219 frames via rpicam-still and publishes raw + compressed images."""

    def __init__(self) -> None:
        super().__init__('camera_node')

        # Parameters
        self.declare_parameter('width',        640)
        self.declare_parameter('height',       480)
        self.declare_parameter('fps',          30)
        self.declare_parameter('jpeg_quality', 80)

        self._width  = self.get_parameter('width').get_parameter_value().integer_value
        self._height = self.get_parameter('height').get_parameter_value().integer_value
        self._jpeg_q = self.get_parameter('jpeg_quality').get_parameter_value().integer_value
        # fps parameter kept for API compatibility; capture rate is fixed at 10 Hz
        # because rpicam-still has ~100 ms minimum timeout per capture.

        # QoS
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # Publishers
        self._raw_pub  = self.create_publisher(Image,           '/camera/image_raw',        sensor_qos)
        self._comp_pub = self.create_publisher(CompressedImage, '/camera/image_compressed',  sensor_qos)

        # CvBridge
        self._bridge = CvBridge()

        self.get_logger().info(
            f'CameraNode ready: {self._width}x{self._height}, '
            f'{_CAPTURE_HZ:.0f} Hz, JPEG quality={self._jpeg_q}'
        )

        # 10 Hz timer
        self._timer = self.create_timer(1.0 / _CAPTURE_HZ, self._timer_callback)

    # ------------------------------------------------------------------
    # Timer callback
    # ------------------------------------------------------------------

    def _timer_callback(self) -> None:
        # Capture a single JPEG frame via rpicam-still
        try:
            result = subprocess.run(
                [
                    'rpicam-still',
                    '--nopreview',
                    '-o', _TMP_FRAME,
                    '--timeout', '1',
                    '--width',  str(self._width),
                    '--height', str(self._height),
                ],
                capture_output=True,
                timeout=5.0,
            )
            if result.returncode != 0:
                self.get_logger().error(
                    f'rpicam-still failed (rc={result.returncode}): '
                    f'{result.stderr.decode(errors="replace").strip()}',
                    throttle_duration_sec=2.0,
                )
                return
        except subprocess.TimeoutExpired:
            self.get_logger().error('rpicam-still timed out.', throttle_duration_sec=2.0)
            return
        except FileNotFoundError:
            self.get_logger().error(
                'rpicam-still not found. Is it installed?', throttle_duration_sec=5.0
            )
            return

        # Read the captured JPEG
        frame_bgr = cv2.imread(_TMP_FRAME)
        if frame_bgr is None:
            self.get_logger().error(
                f'cv2.imread failed for {_TMP_FRAME}', throttle_duration_sec=2.0
            )
            return

        now = self.get_clock().now().to_msg()

        # ------ Raw image ------
        try:
            img_msg = self._bridge.cv2_to_imgmsg(frame_bgr, encoding='bgr8')
            img_msg.header.stamp    = now
            img_msg.header.frame_id = 'camera_link'
            self._raw_pub.publish(img_msg)
        except Exception as exc:
            self.get_logger().error(f'Camera raw publish error: {exc}')

        # ------ Compressed image (JPEG) ------
        try:
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_q]
            success, buffer = cv2.imencode('.jpg', frame_bgr, encode_params)
            if not success:
                self.get_logger().warning('cv2.imencode failed, skipping compressed frame')
                return

            comp_msg = CompressedImage()
            comp_msg.header.stamp    = now
            comp_msg.header.frame_id = 'camera_link'
            comp_msg.format          = 'jpeg'
            comp_msg.data            = buffer.tobytes()
            self._comp_pub.publish(comp_msg)
        except Exception as exc:
            self.get_logger().error(f'Camera compressed publish error: {exc}')

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def destroy_node(self) -> None:
        self.get_logger().info('CameraNode shutting down.')
        super().destroy_node()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(args=None) -> None:
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
