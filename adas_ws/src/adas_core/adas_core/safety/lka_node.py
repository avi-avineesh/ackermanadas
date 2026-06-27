"""
lka_node.py — Lane Keeping Assist, lateral PID on lane centre error.

Core pinning: CPU 2
"""

import os
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from std_msgs.msg import Float32, String, Bool
from geometry_msgs.msg import Twist

from adas_msgs.msg import LaneData, VehicleParams


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PUBLISH_HZ      = 30.0
LANE_DATA_TIMEOUT = 1.0    # s — watchdog timeout for LaneData

# Lateral PID gains (on lateral_error_m)
KP_LAT  = 0.012
KI_LAT  = 0.0001
KD_LAT  = 0.006

# Anti-windup clamp for integral (in rad equivalent)
INTEGRAL_CLAMP_RAD = 0.15

# Drift correction weight
DRIFT_GAIN = 0.3

# Speed profile
BASE_SPEED = 0.40    # m/s
MIN_SPEED  = 0.12    # m/s


def _make_best_effort_qos(depth: int = 10) -> QoSProfile:
    return QoSProfile(
        depth=depth,
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.VOLATILE,
    )


class LKANode(Node):
    """Lane Keeping Assist node."""

    def __init__(self):
        super().__init__('lka_node')

        # ── Shared state (protected by _lock) ───────────────────────────────
        self._lock = threading.Lock()

        self._lane_data:          LaneData | None = None
        self._lane_data_t:        float           = 0.0

        self._gyro_z:             float = 0.0
        self._drift_correction:   float = 0.0

        self._max_speed:          float = BASE_SPEED
        self._max_steer_mrad:     float = 700.0   # default 700 mrad

        self._lka_switch:         bool  = False

        # PID state
        self._pid_integral:       float = 0.0
        self._pid_prev_error:     float = 0.0
        self._pid_prev_t:         float = time.monotonic()

        self._last_steer_rad:     float = 0.0

        # ── QoS ─────────────────────────────────────────────────────────────
        be_qos  = _make_best_effort_qos()
        rel_qos = QoSProfile(depth=10)

        # ── Subscriptions ────────────────────────────────────────────────────
        self.create_subscription(LaneData,    '/lane/data',                  self._lane_cb,   rel_qos)
        self.create_subscription(Float32,     '/sensor/gyro_z',              self._gyro_cb,   be_qos)
        self.create_subscription(Float32,     '/vehicle/drift_correction',   self._drift_cb,  rel_qos)
        self.create_subscription(VehicleParams,'/vehicle/params',            self._params_cb, rel_qos)
        self.create_subscription(Bool,        '/adas/lka_switch',            self._switch_cb, rel_qos)

        # ── Publishers ───────────────────────────────────────────────────────
        self._pub_cmd    = self.create_publisher(Twist,  '/safety/lka_cmd',    rel_qos)
        self._pub_status = self.create_publisher(String, '/safety/lka_status', rel_qos)

        # ── 30 Hz timer ──────────────────────────────────────────────────────
        self.create_timer(1.0 / PUBLISH_HZ, self._timer_cb)

        self.get_logger().info('LKA node started.')

    # ────────────────────────────────────────────────────────────────────────
    # Callbacks
    # ────────────────────────────────────────────────────────────────────────
    def _lane_cb(self, msg: LaneData):
        now = time.monotonic()
        with self._lock:
            self._lane_data   = msg
            self._lane_data_t = now

    def _gyro_cb(self, msg: Float32):
        with self._lock:
            self._gyro_z = float(msg.data)

    def _drift_cb(self, msg: Float32):
        with self._lock:
            self._drift_correction = float(msg.data)

    def _params_cb(self, msg: VehicleParams):
        with self._lock:
            self._max_speed      = float(msg.max_speed)
            self._max_steer_mrad = float(msg.max_steer)

    def _switch_cb(self, msg: Bool):
        with self._lock:
            self._lka_switch = bool(msg.data)
            if not msg.data:
                self._pid_integral   = 0.0
                self._pid_prev_error = 0.0
                self._last_steer_rad = 0.0

    # ────────────────────────────────────────────────────────────────────────
    # 30Hz control timer
    # ────────────────────────────────────────────────────────────────────────
    def _timer_cb(self):
        now = time.monotonic()

        with self._lock:
            lane_data       = self._lane_data
            lane_data_age   = now - self._lane_data_t
            drift           = self._drift_correction
            lka_switch      = self._lka_switch
            max_speed_param = self._max_speed
            max_steer_mrad  = self._max_steer_mrad

        max_steer_rad = max_steer_mrad / 1000.0

        # ── Watchdog: no lane data ────────────────────────────────────────────
        if lane_data is None or lane_data_age > LANE_DATA_TIMEOUT:
            self.get_logger().warn(
                'LKA: No LaneData received — publishing zero.',
                throttle_duration_sec=2.0
            )
            self._publish_zero(max_speed_param, max_steer_rad)
            return

        # ── Unpack LaneData ───────────────────────────────────────────────────
        lateral_error = float(getattr(lane_data, 'lateral_error_m', 0.0))
        curvature     = float(getattr(lane_data, 'curvature',        0.0))
        confidence    = float(getattr(lane_data, 'confidence',        0.0))
        recovery_mode = str(  getattr(lane_data, 'recovery_mode',    ''))

        # ── Recovery mode handling ────────────────────────────────────────────
        if recovery_mode == 'EMERGENCY_STOP':
            self._publish(0.0, 0.0, lateral_error, curvature, recovery_mode)
            return

        # ── LKA disabled or low confidence ───────────────────────────────────
        if not lka_switch:
            self._publish_zero(max_speed_param, max_steer_rad)
            return

        # Reduce confidence weight in prediction / single-lane recovery modes
        effective_conf = confidence
        if recovery_mode in ('PREDICT', 'SINGLE_LANE'):
            effective_conf *= 0.7

        if effective_conf < 0.3:
            # Not confident enough — output zero steer
            self._publish_zero(max_speed_param, max_steer_rad)
            return

        # ── Lateral PID ───────────────────────────────────────────────────────
        with self._lock:
            dt = now - self._pid_prev_t
            if dt <= 0.0:
                dt = 1.0 / PUBLISH_HZ

            error = lateral_error   # positive = car right of centre → steer left (positive)

            self._pid_integral += error * dt
            self._pid_integral  = max(-INTEGRAL_CLAMP_RAD,
                                      min(INTEGRAL_CLAMP_RAD, self._pid_integral))

            derivative = (error - self._pid_prev_error) / dt

            # Negative sign: positive error (right of centre) → positive steer (left)
            steer_rad = -(KP_LAT * error
                          + KI_LAT * self._pid_integral
                          + KD_LAT * derivative)

            # IMU drift correction
            steer_rad += -DRIFT_GAIN * drift

            # Clamp to vehicle limits
            steer_rad = max(-max_steer_rad, min(max_steer_rad, steer_rad))

            self._last_steer_rad  = steer_rad
            self._pid_prev_error  = error
            self._pid_prev_t      = now

        # ── Speed profile from curvature ──────────────────────────────────────
        # curvature in metres (radius) — normalise to [0,1] factor
        curvature_factor = min(1.0, 10.0 / (abs(curvature) + 1.0))
        speed_cmd = max(MIN_SPEED,
                        max_speed_param * curvature_factor * 0.8)
        speed_cmd = min(speed_cmd, max_speed_param)

        # Recovery mode: reduce speed further
        if recovery_mode in ('PREDICT', 'SINGLE_LANE'):
            speed_cmd *= 0.6
            speed_cmd = max(MIN_SPEED, speed_cmd)

        self._publish(speed_cmd, steer_rad, lateral_error, curvature, recovery_mode)

    # ────────────────────────────────────────────────────────────────────────
    # Publish helpers
    # ────────────────────────────────────────────────────────────────────────
    def _publish(
        self,
        speed_cmd: float,
        steer_rad: float,
        error:     float,
        curvature: float,
        mode:      str,
    ):
        state = 'ACTIVE' if abs(steer_rad) > 1e-6 or speed_cmd > 0.0 else 'IDLE'

        cmd_msg = Twist()
        cmd_msg.linear.x  = float(speed_cmd)
        cmd_msg.angular.z = float(steer_rad)
        self._pub_cmd.publish(cmd_msg)

        status_msg = String()
        status_msg.data = (
            f'{state}|err={error:.3f}m|steer={steer_rad:.4f}rad'
            f'|curv={curvature:.1f}m|mode={mode}'
        )
        self._pub_status.publish(status_msg)

    def _publish_zero(self, max_speed_param: float, max_steer_rad: float):
        self._publish(0.0, 0.0, 0.0, 0.0, 'IDLE')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(args=None):
    try:
        os.sched_setaffinity(0, {2})
    except (OSError, AttributeError) as exc:
        print(f'[lka_node] CPU affinity not set: {exc}')

    rclpy.init(args=args)
    node = LKANode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        node.get_logger().error(f'LKA node exception: {exc}')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
