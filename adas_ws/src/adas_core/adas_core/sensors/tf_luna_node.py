"""
tf_luna_node.py
---------------
ROS2 Jazzy node for TF-Luna ToF LiDAR sensor via serial /dev/ttyAMA2.

Frame format (9 bytes):
  [0x59, 0x59, distL, distH, ampL, ampH, tempL, tempH, checksum]
  distance_cm = distL | (distH << 8)
  checksum    = sum(bytes[0:8]) & 0xFF

EMA filter: alpha=0.35
Publishes sensor_msgs/Range to /sensor/lidar_range at 10 Hz.
"""

import math
import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Range

import serial


FRAME_HEADER = 0x59
FRAME_LEN = 9
EMA_ALPHA = 0.35


class TFLunaNode(Node):
    """Publishes TF-Luna distance readings as sensor_msgs/Range."""

    def __init__(self) -> None:
        super().__init__('tf_luna_node')

        # Parameters
        self.declare_parameter('port', '/dev/ttyAMA2')
        self.declare_parameter('baudrate', 115200)

        port = self.get_parameter('port').get_parameter_value().string_value
        baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value

        # QoS
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # Publisher
        self.pub = self.create_publisher(Range, '/sensor/lidar_range', sensor_qos)

        # Shared state
        self._lock = threading.Lock()
        self._ema_distance_m: float = 0.0
        self._has_valid = False

        # Open serial port
        self._serial: serial.Serial | None = None
        try:
            self._serial = serial.Serial(port, baudrate, timeout=0.1)
            self.get_logger().info(f'TF-Luna serial opened: {port} @ {baudrate}')
        except serial.SerialException as exc:
            self.get_logger().error(f'Failed to open serial port {port}: {exc}')

        # 10 Hz timer
        self._timer = self.create_timer(0.1, self._timer_callback)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_frame(self) -> float | None:
        """
        Attempt to read one valid 9-byte TF-Luna frame from serial.
        Returns distance in metres on success, None on failure.
        """
        if self._serial is None or not self._serial.is_open:
            return None

        try:
            # Synchronise to frame header (two consecutive 0x59 bytes)
            sync_attempts = 0
            while sync_attempts < 20:
                b = self._serial.read(1)
                if not b:
                    return None
                if b[0] == FRAME_HEADER:
                    b2 = self._serial.read(1)
                    if b2 and b2[0] == FRAME_HEADER:
                        # Read remaining 7 bytes
                        rest = self._serial.read(FRAME_LEN - 2)
                        if len(rest) != FRAME_LEN - 2:
                            return None
                        frame = bytes([FRAME_HEADER, FRAME_HEADER]) + rest
                        break
                sync_attempts += 1
            else:
                return None

            # Validate checksum
            expected_checksum = sum(frame[0:8]) & 0xFF
            if frame[8] != expected_checksum:
                self.get_logger().warning(
                    f'TF-Luna checksum mismatch: got {frame[8]:#04x}, '
                    f'expected {expected_checksum:#04x}'
                )
                return None

            # Parse distance
            dist_cm = frame[2] | (frame[3] << 8)
            dist_m = dist_cm / 100.0
            return dist_m

        except serial.SerialException as exc:
            self.get_logger().warning(f'TF-Luna serial read error: {exc}')
            return None

    def _build_range_msg(self, distance_m: float) -> Range:
        msg = Range()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'lidar_link'
        msg.radiation_type = Range.INFRARED   # 1
        msg.field_of_view = 0.00872           # ~0.5 degrees in radians
        msg.min_range = 0.2
        msg.max_range = 8.0
        msg.range = float(distance_m)
        return msg

    # ------------------------------------------------------------------
    # Timer callback (10 Hz)
    # ------------------------------------------------------------------

    def _timer_callback(self) -> None:
        raw_m = self._read_frame()

        with self._lock:
            if raw_m is not None:
                if not self._has_valid:
                    # Initialise EMA with first reading
                    self._ema_distance_m = raw_m
                    self._has_valid = True
                else:
                    self._ema_distance_m = (
                        EMA_ALPHA * raw_m + (1.0 - EMA_ALPHA) * self._ema_distance_m
                    )
            else:
                if not self._has_valid:
                    # No valid reading yet; nothing to publish
                    self.get_logger().warning('TF-Luna: no valid frame received yet')
                    return

            publish_distance = self._ema_distance_m

        msg = self._build_range_msg(publish_distance)
        self.pub.publish(msg)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def destroy_node(self) -> None:
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
            self.get_logger().info('TF-Luna serial port closed.')
        super().destroy_node()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(args=None) -> None:
    rclpy.init(args=args)
    node = TFLunaNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
