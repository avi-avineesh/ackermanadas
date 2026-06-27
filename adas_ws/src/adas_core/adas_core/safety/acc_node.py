"""
acc_node.py — Adaptive Cruise Control, TTC-based gap following.

Core pinning: CPU 3
"""

import os
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from sensor_msgs.msg import Range
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32, String, Bool
from geometry_msgs.msg import Twist

from adas_msgs.msg import VehicleParams


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PUBLISH_HZ      = 50.0
SENSOR_TIMEOUT  = 1.0    # s
LIDAR_GAP_MAX   = 4.0    # m — beyond this: no lead vehicle from lidar

# Gap control
K_GAP           = 1.5    # s (time headway)
GAP_MIN         = 0.30   # m (minimum gap offset)
GAP_HYSTERESIS  = 0.5    # m — CATCH_UP when gap > desired + this

# PID gains (gap control)
KP              = 0.8
KI              = 0.05
KD              = 0.2

# Integral anti-windup
INTEGRAL_CLAMP  = 1.0

# Fallback factor for single-sensor mode (20% more conservative gap threshold)
FALLBACK_FACTOR = 1.20

# AEB handoff TTC threshold
AEB_HANDOFF_TTC = 1.5    # s


def _make_best_effort_qos(depth: int = 10) -> QoSProfile:
    return QoSProfile(
        depth=depth,
        reliability=ReliabilityPolicy.BEST_EFFORT,
        durability=DurabilityPolicy.VOLATILE,
    )


class ACCNode(Node):
    """Adaptive Cruise Control node."""

    def __init__(self):
        super().__init__('acc_node')

        # ── Shared state (protected by _lock) ───────────────────────────────
        self._lock = threading.Lock()

        self._lidar_gap:        float = float('inf')
        self._lidar_last_t:     float = 0.0

        self._camera_gap:       float = -1.0    # -1 = no vehicle
        self._camera_last_t:    float = 0.0

        self._v_ego:            float = 0.0
        self._acc_switch:       bool  = False
        self._aeb_ttc:          float = float('inf')

        self._max_speed:        float = 1.0
        self._acc_state:        str   = 'IDLE'

        # PID state
        self._pid_integral:     float = 0.0
        self._pid_prev_error:   float = 0.0
        self._pid_prev_t:       float = time.monotonic()

        # ── QoS ─────────────────────────────────────────────────────────────
        be_qos  = _make_best_effort_qos()
        rel_qos = QoSProfile(depth=10)

        # ── Subscriptions ────────────────────────────────────────────────────
        self.create_subscription(Range,        '/sensor/lidar_range',           self._lidar_cb,    be_qos)
        self.create_subscription(Odometry,     '/vehicle/pose',                 self._pose_cb,     rel_qos)
        self.create_subscription(Float32,      '/perception/vehicle_distance',  self._cam_cb,      rel_qos)
        self.create_subscription(Bool,         '/adas/acc_switch',              self._switch_cb,   rel_qos)
        self.create_subscription(String,       '/safety/aeb_status',            self._aeb_status_cb, rel_qos)
        self.create_subscription(VehicleParams,'/vehicle/params',               self._params_cb,   rel_qos)

        # ── Publishers ───────────────────────────────────────────────────────
        self._pub_cmd    = self.create_publisher(Twist,  '/safety/acc_cmd',    rel_qos)
        self._pub_status = self.create_publisher(String, '/safety/acc_status', rel_qos)

        # ── 50 Hz timer ──────────────────────────────────────────────────────
        self.create_timer(1.0 / PUBLISH_HZ, self._timer_cb)

        self.get_logger().info('ACC node started.')

    # ────────────────────────────────────────────────────────────────────────
    # Callbacks
    # ────────────────────────────────────────────────────────────────────────
    def _lidar_cb(self, msg: Range):
        now = time.monotonic()
        with self._lock:
            self._lidar_gap    = float(msg.range)
            self._lidar_last_t = now

    def _pose_cb(self, msg: Odometry):
        with self._lock:
            self._v_ego = float(msg.twist.twist.linear.x)

    def _cam_cb(self, msg: Float32):
        now = time.monotonic()
        with self._lock:
            self._camera_gap    = float(msg.data)
            self._camera_last_t = now

    def _switch_cb(self, msg: Bool):
        with self._lock:
            self._acc_switch = bool(msg.data)
            if not msg.data:
                # Reset PID when ACC is turned off
                self._pid_integral   = 0.0
                self._pid_prev_error = 0.0

    def _aeb_status_cb(self, msg: String):
        """Parse TTC from AEB status string: STATE|TTC|SCORE|..."""
        try:
            parts = msg.data.split('|')
            if len(parts) >= 2:
                ttc_str = parts[1]
                ttc = float(ttc_str) if ttc_str != 'inf' else float('inf')
                with self._lock:
                    self._aeb_ttc = ttc
        except Exception as exc:
            self.get_logger().warn(
                f'ACC: AEB status parse error: {exc}', throttle_duration_sec=5.0
            )

    def _params_cb(self, msg: VehicleParams):
        with self._lock:
            self._max_speed = float(msg.max_speed)

    # ────────────────────────────────────────────────────────────────────────
    # Lead vehicle detection with AND logic
    # ────────────────────────────────────────────────────────────────────────
    def _detect_lead_vehicle(
        self,
        lidar_gap: float, lidar_age: float,
        camera_gap: float, camera_age: float,
    ):
        """
        Returns (lead_detected: bool, effective_gap: float, mode: str).
        AND logic: both sensors agree → lead detected.
        Fallback: single sensor with +20% conservative threshold.
        """
        lidar_ok  = (lidar_gap < LIDAR_GAP_MAX) and (lidar_age < SENSOR_TIMEOUT)
        camera_ok = (camera_gap > 0.0) and (camera_age < SENSOR_TIMEOUT)

        if lidar_ok and camera_ok:
            # Fused gap: prefer lidar for distance accuracy
            effective_gap = lidar_gap
            return True, effective_gap, 'DUAL'

        if lidar_ok and not camera_ok:
            # Lidar-only: more conservative (smaller threshold)
            conservative_max = LIDAR_GAP_MAX / FALLBACK_FACTOR
            if lidar_gap < conservative_max:
                return True, lidar_gap, 'LIDAR_ONLY'
            return False, lidar_gap, 'LIDAR_ONLY_NO_LEAD'

        if camera_ok and not lidar_ok:
            # Camera-only: use camera distance but require it to be close
            conservative_max = LIDAR_GAP_MAX / FALLBACK_FACTOR
            if 0.0 < camera_gap < conservative_max:
                return True, camera_gap, 'CAM_ONLY'
            return False, camera_gap, 'CAM_ONLY_NO_LEAD'

        return False, float('inf'), 'NO_SENSOR'

    # ────────────────────────────────────────────────────────────────────────
    # 50Hz control timer
    # ────────────────────────────────────────────────────────────────────────
    def _timer_cb(self):
        now = time.monotonic()

        with self._lock:
            lidar_gap   = self._lidar_gap
            lidar_age   = now - self._lidar_last_t
            camera_gap  = self._camera_gap
            camera_age  = now - self._camera_last_t
            v_ego       = self._v_ego
            acc_switch  = self._acc_switch
            aeb_ttc     = self._aeb_ttc
            max_speed   = self._max_speed

        # ── AEB handoff check ─────────────────────────────────────────────────
        if aeb_ttc < AEB_HANDOFF_TTC:
            state     = 'AEB_HANDOFF'
            speed_cmd = 0.0
            gap_info  = lidar_gap
            desired_g = 0.0
            self._publish(state, speed_cmd, gap_info, desired_g)
            return

        # ── ACC switch off → IDLE ─────────────────────────────────────────────
        if not acc_switch:
            state     = 'IDLE'
            speed_cmd = 0.0
            gap_info  = lidar_gap
            desired_g = 0.0
            self._publish(state, speed_cmd, gap_info, desired_g)
            return

        # ── Lead vehicle detection ────────────────────────────────────────────
        lead_detected, eff_gap, _sensor_mode = self._detect_lead_vehicle(
            lidar_gap, lidar_age, camera_gap, camera_age
        )

        if not lead_detected:
            state     = 'IDLE'
            speed_cmd = 0.0
            self._publish(state, speed_cmd, eff_gap, 0.0)
            with self._lock:
                self._pid_integral   = 0.0
                self._pid_prev_error = 0.0
            return

        # ── Desired gap ───────────────────────────────────────────────────────
        desired_gap = v_ego * K_GAP + GAP_MIN

        # ── State selection ───────────────────────────────────────────────────
        if eff_gap > desired_gap + GAP_HYSTERESIS:
            state     = 'CATCH_UP'
            speed_cmd = max_speed
            # Reset PID integral in transient states
            with self._lock:
                self._pid_integral   = 0.0
                self._pid_prev_error = 0.0

        elif eff_gap > desired_gap:
            state     = 'APPROACH'
            speed_cmd = max_speed * 0.7
            with self._lock:
                self._pid_integral   = 0.0
                self._pid_prev_error = 0.0

        else:
            state = 'FOLLOW'
            # ── PID control ───────────────────────────────────────────────────
            with self._lock:
                dt = now - self._pid_prev_t
                if dt <= 0.0:
                    dt = 1.0 / PUBLISH_HZ

                error = eff_gap - desired_gap   # positive = too far → speed up

                self._pid_integral += error * dt
                self._pid_integral  = max(-INTEGRAL_CLAMP,
                                         min(INTEGRAL_CLAMP, self._pid_integral))

                derivative = (error - self._pid_prev_error) / dt

                speed_cmd = (KP * error
                             + KI * self._pid_integral
                             + KD * derivative)
                speed_cmd = max(0.0, min(max_speed, speed_cmd))

                self._pid_prev_error = error
                self._pid_prev_t     = now

        self._publish(state, speed_cmd, eff_gap, desired_gap)

    # ────────────────────────────────────────────────────────────────────────
    # Publish helper
    # ────────────────────────────────────────────────────────────────────────
    def _publish(self, state: str, speed_cmd: float, gap: float, desired_gap: float):
        with self._lock:
            self._acc_state = state

        cmd_msg = Twist()
        cmd_msg.linear.x  = float(speed_cmd)
        cmd_msg.angular.z = 0.0
        self._pub_cmd.publish(cmd_msg)

        gap_str     = f'{gap:.2f}' if gap < float('inf') else 'inf'
        status_msg  = String()
        status_msg.data = (
            f'{state}|gap={gap_str}|desired={desired_gap:.2f}|cmd={speed_cmd:.2f}'
        )
        self._pub_status.publish(status_msg)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(args=None):
    try:
        os.sched_setaffinity(0, {3})
    except (OSError, AttributeError) as exc:
        print(f'[acc_node] CPU affinity not set: {exc}')

    rclpy.init(args=args)
    node = ACCNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        node.get_logger().error(f'ACC node exception: {exc}')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
