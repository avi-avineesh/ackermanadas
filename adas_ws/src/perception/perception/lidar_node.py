#!/usr/bin/env python3
"""
lidar_node.py — Perception Layer: LiDAR and ToF Validation
═══════════════════════════════════════════════════════════
Package : perception | Pi core 2

SENSOR PHYSICS:
  TF-Luna: Time-of-Flight infrared laser (850nm). Emits 1-ray pulse, measures
  round-trip time. At 10Hz gives 10 range readings/sec. UART at 115200 baud.
  Noise: ~5mm 1σ at 1m range (modelled in Gazebo as gaussian stddev=0.005).
  In simulation: Gazebo gpu_lidar plugin (1 ray, 0°, 0.2–8m) → ros_gz_bridge.

  VL53L0X: 940nm VCSEL laser ranging (I2C). Max range 2m. Very fast (30Hz
  capability, run at 10Hz here). Two units on left/right flanks, address-offset
  via GPIO XSHUT: left=0x29 (default), right=0x30 (XSHUT on GPIO1 during boot).
  In simulation: Gazebo gpu_lidar (1 ray, side-facing, 0.03–2m) → bridge.

WHAT THIS NODE DOES:
  Receives raw LaserScan messages from three sensors, applies range gating
  (reject non-finite and out-of-bounds values → replace with inf), re-publishes
  the cleaned forward scan, and publishes a status string for the side sensors.

  SIDE_WARNING triggers if either flank ToF < 0.20m — this is forwarded to
  aeb_node via /ego/tof_left and /ego/tof_right directly (aeb_node subscribes
  there). /ego/tof_status is an additional human-readable status string.

SILENCE MONITORING:
  If any sensor stops publishing for > 2s, a WARN log is emitted once per
  timer tick until it recovers. Helps diagnose disconnected sensors on hardware.

TOPICS:
  Subscribes:  /ego/lidar_range    sensor_msgs/LaserScan
               /ego/tof_left       sensor_msgs/LaserScan
               /ego/tof_right      sensor_msgs/LaserScan
  Publishes:   /ego/lidar_processed  sensor_msgs/LaserScan (filtered)
               /ego/tof_status       std_msgs/String
"""

import math
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String

SILENT_TIMEOUT = 2.0  # s — warn if no data longer than this


class LidarNode(Node):
    """Validates all range sensors, republishes clean data, monitors silence."""

    def __init__(self):
        super().__init__('lidar_node')

        self._last_t = {'lidar': time.time(), 'tof_l': time.time(), 'tof_r': time.time()}
        self._tof_left_dist  = float('inf')
        self._tof_right_dist = float('inf')

        self._pub_lidar  = self.create_publisher(LaserScan, '/ego/lidar_processed', 10)
        self._pub_status = self.create_publisher(String,    '/ego/tof_status',      10)

        self.create_subscription(LaserScan, '/ego/lidar_range', self._lidar_cb,  10)
        self.create_subscription(LaserScan, '/ego/tof_left',    self._tof_l_cb,  10)
        self.create_subscription(LaserScan, '/ego/tof_right',   self._tof_r_cb,  10)

        self.create_timer(0.1, self._status_timer)  # 10Hz

        self.get_logger().info(
            '[lidar_node] Ready — /ego/lidar_range + /ego/tof_left + /ego/tof_right'
        )

    @staticmethod
    def _gate(scan: LaserScan) -> LaserScan:
        """Replace non-finite or out-of-range values with inf."""
        rmin, rmax = scan.range_min, scan.range_max
        scan.ranges = tuple(
            r if (math.isfinite(r) and rmin <= r <= rmax) else float('inf')
            for r in scan.ranges
        )
        return scan

    @staticmethod
    def _best(scan: LaserScan) -> float:
        """Return minimum finite range from scan, or inf."""
        finite = [r for r in scan.ranges if math.isfinite(r)]
        return min(finite) if finite else float('inf')

    def _lidar_cb(self, msg: LaserScan):
        """Validate and republish forward TF-Luna scan."""
        self._last_t['lidar'] = time.time()
        self._pub_lidar.publish(self._gate(msg))

    def _tof_l_cb(self, msg: LaserScan):
        """Validate left VL53L0X, cache for status."""
        self._last_t['tof_l'] = time.time()
        self._tof_left_dist = self._best(self._gate(msg))

    def _tof_r_cb(self, msg: LaserScan):
        """Validate right VL53L0X, cache for status."""
        self._last_t['tof_r'] = time.time()
        self._tof_right_dist = self._best(self._gate(msg))

    def _status_timer(self):
        """Publish ToF status string and check sensor silence at 10Hz."""
        now = time.time()
        names = {'lidar': '/ego/lidar_range', 'tof_l': '/ego/tof_left', 'tof_r': '/ego/tof_right'}
        for key, topic in names.items():
            if now - self._last_t[key] > SILENT_TIMEOUT:
                self.get_logger().warn(f'[lidar_node] SILENT >2s: {topic}')

        l = self._tof_left_dist
        r = self._tof_right_dist
        l_s = f'{l:.2f}' if math.isfinite(l) else 'inf'
        r_s = f'{r:.2f}' if math.isfinite(r) else 'inf'
        side_warn = (math.isfinite(l) and l < 0.20) or (math.isfinite(r) and r < 0.20)
        status = 'SIDE_WARNING' if side_warn else 'ok'

        msg = String()
        msg.data = f'left:{l_s}|right:{r_s}|{status}'
        self._pub_status.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = LidarNode()
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
