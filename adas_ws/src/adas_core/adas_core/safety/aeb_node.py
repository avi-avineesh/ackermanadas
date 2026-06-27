"""
aeb_node.py — Autonomous Emergency Braking with AND-logic dual-modality fusion.

Core pinning: CPU 3
"""

import os
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from sensor_msgs.msg import Range
from std_msgs.msg import Float32, String
from geometry_msgs.msg import Twist

from adas_msgs.msg import BoundingBox2DArray


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PUBLISH_HZ        = 50.0
LIDAR_MAX_RANGE   = 8.0      # m — beyond this treated as inf/no obstacle
SENSOR_TIMEOUT    = 2.0      # s — sensor considered unavailable after this
EMA_ALPHA         = 0.35

TTC_WARNING       = 3.0      # s
TTC_PARTIAL       = 2.0      # s
TTC_HARD          = 1.0      # s
TTC_STOP          = 0.5      # s

SCORE_WARNING     = 0.30
SCORE_PARTIAL     = 0.60
SCORE_HARD        = 0.80
SCORE_STOP        = 0.95

CAM_CONF_THRESH   = 0.40
CAM_CONF_FALLBACK = 0.48     # 0.40 * 1.2

FALLBACK_FACTOR   = 1.20     # multiplier on TTC thresholds in single-sensor mode

# Sentinel: no speed cap
NO_LIMIT_SENTINEL = 999.0


def _make_best_effort_qos(depth: int = 10) -> QoSProfile:
    return QoSProfile(
        depth=depth,
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.VOLATILE,
    )


class AEBNode(Node):
    """Autonomous Emergency Braking node."""

    def __init__(self):
        super().__init__('aeb_node')

        # ── Shared state (protected by _lock) ───────────────────────────────
        self._lock = threading.Lock()

        self._lidar_range_ema:    float = float('inf')
        self._lidar_last_valid_t: float = 0.0
        self._lidar_quality:      float = 0.0

        self._cam_conf:           float = 0.0
        self._cam_last_valid_t:   float = 0.0

        self._tof_left_range:     float = float('inf')
        self._tof_right_range:    float = float('inf')

        self._aeb_state:          str   = 'CLEAR'
        self._vehicle_speed:      float = 0.0   # from /vehicle/cmd_vel_safe

        # ── QoS ─────────────────────────────────────────────────────────────
        be_qos  = _make_best_effort_qos()
        rel_qos = QoSProfile(depth=10)

        # ── Subscriptions ────────────────────────────────────────────────────
        self.create_subscription(Range,              '/sensor/lidar_range',    self._lidar_cb,     be_qos)
        self.create_subscription(Range,              '/sensor/tof_left',       self._tof_left_cb,  be_qos)
        self.create_subscription(Range,              '/sensor/tof_right',      self._tof_right_cb, be_qos)
        self.create_subscription(BoundingBox2DArray, '/perception/detections', self._detection_cb, be_qos)
        self.create_subscription(Twist,              '/vehicle/cmd_vel_safe',  self._speed_cb,     rel_qos)

        # ── Publishers ───────────────────────────────────────────────────────
        self._pub_cmd    = self.create_publisher(Twist,  '/safety/aeb_cmd',    rel_qos)
        self._pub_status = self.create_publisher(String, '/safety/aeb_status', rel_qos)

        # ── 50 Hz timer ──────────────────────────────────────────────────────
        self.create_timer(1.0 / PUBLISH_HZ, self._timer_cb)

        self.get_logger().info('AEB node started.')

    # ────────────────────────────────────────────────────────────────────────
    # Sensor callbacks
    # ────────────────────────────────────────────────────────────────────────
    def _lidar_cb(self, msg: Range):
        r = float(msg.range)
        now = time.monotonic()
        with self._lock:
            if 0.0 < r < LIDAR_MAX_RANGE:
                # Valid measurement — apply EMA filter
                if self._lidar_range_ema == float('inf'):
                    self._lidar_range_ema = r
                else:
                    self._lidar_range_ema = (
                        EMA_ALPHA * r + (1.0 - EMA_ALPHA) * self._lidar_range_ema
                    )
                self._lidar_quality = 1.0
                self._lidar_last_valid_t = now
            else:
                # Out-of-range — reset EMA, decay quality
                self._lidar_range_ema = float('inf')
                self._lidar_quality = max(0.2, self._lidar_quality - 0.05)

    def _tof_left_cb(self, msg: Range):
        with self._lock:
            self._tof_left_range = float(msg.range)

    def _tof_right_cb(self, msg: Range):
        with self._lock:
            self._tof_right_range = float(msg.range)

    def _detection_cb(self, msg: BoundingBox2DArray):
        """Extract highest confidence vehicle detection."""
        now = time.monotonic()
        best_conf = 0.0
        try:
            for box in msg.boxes:
                conf = float(getattr(box, 'confidence', 1.0))
                if conf > best_conf:
                    best_conf = conf
        except Exception as exc:
            self.get_logger().warn(
                f'Detection parse error: {exc}', throttle_duration_sec=5.0
            )
        with self._lock:
            self._cam_conf = best_conf
            if best_conf > 0.0:
                self._cam_last_valid_t = now

    def _speed_cb(self, msg: Twist):
        with self._lock:
            self._vehicle_speed = float(msg.linear.x)

    # ────────────────────────────────────────────────────────────────────────
    # 50Hz arbitration timer
    # ────────────────────────────────────────────────────────────────────────
    def _timer_cb(self):
        now = time.monotonic()

        with self._lock:
            lidar_ema   = self._lidar_range_ema
            lidar_qual  = self._lidar_quality
            lidar_age   = now - self._lidar_last_valid_t
            cam_conf    = self._cam_conf
            cam_age     = now - self._cam_last_valid_t
            speed       = self._vehicle_speed

        # ── Availability flags ────────────────────────────────────────────────
        lidar_available = lidar_age < SENSOR_TIMEOUT
        cam_available   = cam_age < SENSOR_TIMEOUT

        # ── TTC ──────────────────────────────────────────────────────────────
        if speed > 0.1 and lidar_ema < float('inf'):
            ttc = lidar_ema / speed
        else:
            ttc = float('inf')

        # ── Fusion score ──────────────────────────────────────────────────────
        alpha     = 0.6 * lidar_qual
        ttc_score = max(0.0, 1.0 - ttc / 3.0)
        score     = alpha * ttc_score + (1.0 - alpha) * cam_conf

        # ── Threat detection (closure captures per-mode logic) ────────────────
        if lidar_available and cam_available:
            # Normal dual-sensor mode: AND logic
            def _threat(ttc_thresh: float) -> bool:
                lidar_threat = lidar_qual > 0.5 and ttc < ttc_thresh
                camera_threat = cam_conf > CAM_CONF_THRESH
                return lidar_threat and camera_threat

        elif lidar_available and not cam_available:
            # Lidar-only fallback — more conservative thresholds
            def _threat(ttc_thresh: float) -> bool:
                return lidar_qual > 0.5 and ttc < ttc_thresh * FALLBACK_FACTOR

        elif cam_available and not lidar_available:
            # Camera-only fallback — elevated confidence threshold
            def _threat(_ttc_thresh: float) -> bool:
                return cam_conf > CAM_CONF_FALLBACK

        else:
            # No sensors available — no threat
            def _threat(_ttc_thresh: float) -> bool:
                return False

        # ── State machine (no hysteresis — safety first) ──────────────────────
        if score >= SCORE_STOP and _threat(TTC_STOP):
            state = 'STOP'
        elif score >= SCORE_HARD and _threat(TTC_HARD):
            state = 'HARD_BRAKE'
        elif score >= SCORE_PARTIAL and _threat(TTC_PARTIAL):
            state = 'PARTIAL_BRAKE'
        elif score >= SCORE_WARNING and _threat(TTC_WARNING):
            state = 'WARNING'
        else:
            state = 'CLEAR'

        with self._lock:
            self._aeb_state = state

        # ── Speed limit sentinel ──────────────────────────────────────────────
        if state == 'STOP':
            speed_limit = 0.0
        elif state == 'HARD_BRAKE':
            speed_limit = 0.08
        elif state == 'PARTIAL_BRAKE':
            speed_limit = 0.50
        else:
            speed_limit = NO_LIMIT_SENTINEL   # CLEAR or WARNING — no cap

        # ── Publish cmd ───────────────────────────────────────────────────────
        cmd_msg = Twist()
        cmd_msg.linear.x  = float(speed_limit)
        cmd_msg.angular.z = 0.0
        self._pub_cmd.publish(cmd_msg)

        # ── Publish status ────────────────────────────────────────────────────
        ttc_str   = f'{ttc:.2f}' if ttc < float('inf') else 'inf'
        lidar_str = f'{lidar_ema:.2f}' if lidar_ema < float('inf') else '-1.00'
        status_msg = String()
        status_msg.data = (
            f'{state}|{ttc_str}|{score:.2f}|{lidar_str}|{cam_conf:.2f}|{alpha:.2f}'
        )
        self._pub_status.publish(status_msg)

    # ────────────────────────────────────────────────────────────────────────
    # Clean shutdown helper
    # ────────────────────────────────────────────────────────────────────────
    def publish_clear(self):
        """Publish a CLEAR state before shutting down."""
        cmd_msg = Twist()
        cmd_msg.linear.x  = NO_LIMIT_SENTINEL
        cmd_msg.angular.z = 0.0
        self._pub_cmd.publish(cmd_msg)

        status_msg = String()
        status_msg.data = 'CLEAR|inf|0.00|-1.00|0.00|0.00'
        self._pub_status.publish(status_msg)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(args=None):
    try:
        os.sched_setaffinity(0, {3})
    except (OSError, AttributeError) as exc:
        print(f'[aeb_node] CPU affinity not set: {exc}')

    rclpy.init(args=args)
    node = AEBNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        node.get_logger().error(f'AEB node exception: {exc}')
    finally:
        try:
            node.publish_clear()
        except Exception:
            pass
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
