"""
safety_arbiter.py — 7-level priority safety arbiter.

Priority levels (1 = highest):
  P1: ESTOP (latching)
  P2: AEB STOP
  P3: AEB HARD_BRAKE
  P4: AEB PARTIAL_BRAKE
  P5: ACC_FOLLOW speed override
  P6: LKA_STEER steer + speed profile
  P7: MANUAL command pass-through
  P8: IDLE

Core pinning: CPU 3
"""

import os
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

from std_msgs.msg import String, Bool, Empty
from geometry_msgs.msg import Twist

from adas_msgs.msg import VehicleParams


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PUBLISH_HZ          = 50.0
BASE_CMD_TIMEOUT    = 0.5    # s — watchdog for /vehicle/cmd_vel_input

# Sentinels
NO_LIMIT_SENTINEL   = 999.0


class SafetyArbiter(Node):
    """7-level priority safety arbiter node."""

    def __init__(self):
        super().__init__('safety_arbiter')

        # ── Shared state (protected by _lock) ───────────────────────────────
        self._lock = threading.Lock()

        # ESTOP
        self._estop_latched: bool  = False

        # AEB
        self._aeb_state:    str   = 'CLEAR'
        self._aeb_fraction: float = NO_LIMIT_SENTINEL

        # ACC
        self._acc_cmd_spd:  float = 0.0
        self._acc_state:    str   = 'IDLE'

        # LKA
        self._lka_cmd_steer: float = 0.0
        self._lka_cmd_spd:   float = 0.0
        self._lka_state:     str   = 'IDLE'

        # Mode / switches
        self._mode:          str   = 'MANUAL'
        self._acc_active:    bool  = False
        self._lka_active:    bool  = False

        # Base command (from mode_manager)
        self._base_speed:    float = 0.0
        self._base_steer:    float = 0.0
        self._base_cmd_t:    float = 0.0   # time.monotonic() of last base cmd

        # Vehicle limits
        self._max_speed:     float = 1.0
        self._max_steer:     float = 0.7   # rad

        # ── QoS ─────────────────────────────────────────────────────────────
        rel_qos = QoSProfile(depth=10)

        # ── Subscriptions ────────────────────────────────────────────────────
        self.create_subscription(Twist,         '/vehicle/cmd_vel_input',  self._base_cmd_cb,   rel_qos)
        self.create_subscription(Twist,         '/safety/aeb_cmd',         self._aeb_cmd_cb,    rel_qos)
        self.create_subscription(String,        '/safety/aeb_status',      self._aeb_status_cb, rel_qos)
        self.create_subscription(Twist,         '/safety/acc_cmd',         self._acc_cmd_cb,    rel_qos)
        self.create_subscription(String,        '/safety/acc_status',      self._acc_status_cb, rel_qos)
        self.create_subscription(Twist,         '/safety/lka_cmd',         self._lka_cmd_cb,    rel_qos)
        self.create_subscription(String,        '/safety/lka_status',      self._lka_status_cb, rel_qos)
        self.create_subscription(Empty,         '/safety/reset',           self._reset_cb,      rel_qos)
        self.create_subscription(String,        '/adas/mode',              self._mode_cb,       rel_qos)
        self.create_subscription(Bool,          '/adas/acc_switch',        self._acc_switch_cb, rel_qos)
        self.create_subscription(Bool,          '/adas/lka_switch',        self._lka_switch_cb, rel_qos)
        self.create_subscription(VehicleParams, '/vehicle/params',         self._params_cb,     rel_qos)

        # ── Publishers ───────────────────────────────────────────────────────
        self._pub_cmd_safe = self.create_publisher(Twist,  '/vehicle/cmd_vel_safe',    rel_qos)
        self._pub_status   = self.create_publisher(String, '/safety/arbiter_status',   rel_qos)

        # ── 50 Hz timer ──────────────────────────────────────────────────────
        self.create_timer(1.0 / PUBLISH_HZ, self._timer_cb)

        self.get_logger().info('Safety arbiter started.')

    # ────────────────────────────────────────────────────────────────────────
    # Subscription callbacks
    # ────────────────────────────────────────────────────────────────────────
    def _base_cmd_cb(self, msg: Twist):
        now = time.monotonic()
        with self._lock:
            self._base_speed  = float(msg.linear.x)
            self._base_steer  = float(msg.angular.z)
            self._base_cmd_t  = now

    def _aeb_cmd_cb(self, msg: Twist):
        with self._lock:
            self._aeb_fraction = float(msg.linear.x)

    def _aeb_status_cb(self, msg: String):
        try:
            state = msg.data.split('|')[0].strip()
            with self._lock:
                self._aeb_state = state
        except Exception as exc:
            self.get_logger().warn(
                f'Arbiter: AEB status parse error: {exc}', throttle_duration_sec=5.0
            )

    def _acc_cmd_cb(self, msg: Twist):
        with self._lock:
            self._acc_cmd_spd = float(msg.linear.x)

    def _acc_status_cb(self, msg: String):
        try:
            state = msg.data.split('|')[0].strip()
            with self._lock:
                self._acc_state = state
        except Exception as exc:
            self.get_logger().warn(
                f'Arbiter: ACC status parse error: {exc}', throttle_duration_sec=5.0
            )

    def _lka_cmd_cb(self, msg: Twist):
        with self._lock:
            self._lka_cmd_steer = float(msg.angular.z)
            self._lka_cmd_spd   = float(msg.linear.x)

    def _lka_status_cb(self, msg: String):
        try:
            state = msg.data.split('|')[0].strip()
            with self._lock:
                self._lka_state = state
        except Exception as exc:
            self.get_logger().warn(
                f'Arbiter: LKA status parse error: {exc}', throttle_duration_sec=5.0
            )

    def _reset_cb(self, _msg: Empty):
        with self._lock:
            if self._mode != 'ESTOP':
                self._estop_latched = False
                self.get_logger().info('Arbiter: ESTOP latch released.')
            else:
                self.get_logger().warn(
                    'Arbiter: Reset received but mode is still ESTOP — latch kept.'
                )

    def _mode_cb(self, msg: String):
        mode = msg.data.strip().upper()
        with self._lock:
            self._mode = mode
            if mode == 'ESTOP':
                self._estop_latched = True
                self.get_logger().warn('Arbiter: ESTOP latched.')

    def _acc_switch_cb(self, msg: Bool):
        with self._lock:
            self._acc_active = bool(msg.data)

    def _lka_switch_cb(self, msg: Bool):
        with self._lock:
            self._lka_active = bool(msg.data)

    def _params_cb(self, msg: VehicleParams):
        with self._lock:
            self._max_speed = float(msg.max_speed)
            # max_steer from VehicleParams is in mrad; convert to rad
            self._max_steer = float(msg.max_steer) / 1000.0

    # ────────────────────────────────────────────────────────────────────────
    # 50Hz arbitration timer
    # ────────────────────────────────────────────────────────────────────────
    def _timer_cb(self):
        now = time.monotonic()

        # ── Snapshot all state under lock ─────────────────────────────────────
        with self._lock:
            estop_latched = self._estop_latched
            aeb_state     = self._aeb_state
            aeb_fraction  = self._aeb_fraction
            acc_cmd_spd   = self._acc_cmd_spd
            acc_state     = self._acc_state
            lka_cmd_steer = self._lka_cmd_steer
            lka_cmd_spd   = self._lka_cmd_spd
            lka_state     = self._lka_state
            mode          = self._mode
            acc_active    = self._acc_active
            lka_active    = self._lka_active
            max_speed     = self._max_speed
            max_steer     = self._max_steer
            base_cmd_age  = now - self._base_cmd_t

            # Watchdog: no base command in 500ms
            if base_cmd_age > BASE_CMD_TIMEOUT:
                base_speed = 0.0
                base_steer = 0.0
            else:
                base_speed = self._base_speed
                base_steer = self._base_steer

        # ── Arbitration ───────────────────────────────────────────────────────
        speed    = base_speed
        steer    = base_steer
        priority = 8
        mode_str = 'IDLE'

        # P7: MANUAL — base command pass-through
        if base_cmd_age <= BASE_CMD_TIMEOUT:
            priority = 7
            mode_str = 'MANUAL'

        # P6: LKA_STEER — steer override (when lka_active AND AUTO mode)
        if lka_active and mode == 'AUTO' and lka_state not in ('IDLE',):
            steer = lka_cmd_steer
            if lka_cmd_spd > 0.0:
                speed = min(speed, lka_cmd_spd)
            priority = min(priority, 6)
            mode_str = f'LKA_STEER|{mode_str}'

        # P5: ACC_FOLLOW — speed override (when acc_active AND AUTO mode)
        if acc_active and mode == 'AUTO' and acc_state not in ('IDLE', 'AEB_HANDOFF'):
            speed    = acc_cmd_spd
            priority = min(priority, 5)
            mode_str = f'ACC_FOLLOW|{mode_str}'

        # P4: AEB PARTIAL_BRAKE — cap speed fraction (not elif: allow accumulation)
        if aeb_state == 'PARTIAL_BRAKE':
            speed    = speed * 0.50
            priority = 4
            mode_str = 'AEB_PARTIAL'

        # P3: AEB HARD_BRAKE
        elif aeb_state == 'HARD_BRAKE':
            speed    = speed * 0.08
            priority = 3
            mode_str = 'AEB_HARD'

        # P2: AEB STOP
        if aeb_state == 'STOP':
            speed    = 0.0
            steer    = 0.0
            priority = 2
            mode_str = 'AEB_STOP'

        # P1: ESTOP (latching) — highest priority, overrides everything
        if estop_latched:
            speed    = 0.0
            steer    = 0.0
            priority = 1
            mode_str = 'ESTOP'

        # ── Clamp final output ────────────────────────────────────────────────
        speed = max(-max_speed, min(max_speed, speed))
        steer = max(-max_steer, min(max_steer, steer))

        # ── Publish /vehicle/cmd_vel_safe ─────────────────────────────────────
        cmd_msg = Twist()
        cmd_msg.linear.x  = float(speed)
        cmd_msg.angular.z = float(steer)
        self._pub_cmd_safe.publish(cmd_msg)

        # ── Publish arbiter status ────────────────────────────────────────────
        status_msg = String()
        status_msg.data = (
            f'priority={priority}|mode={mode_str}'
            f'|aeb={aeb_state}|acc={acc_state}|lka={lka_state}'
            f'|speed={speed:.3f}'
        )
        self._pub_status.publish(status_msg)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(args=None):
    try:
        os.sched_setaffinity(0, {3})
    except (OSError, AttributeError) as exc:
        print(f'[safety_arbiter] CPU affinity not set: {exc}')

    rclpy.init(args=args)
    node = SafetyArbiter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        node.get_logger().error(f'Safety arbiter exception: {exc}')
    finally:
        # Publish a safe zero command on shutdown
        try:
            stop_msg = Twist()
            stop_msg.linear.x  = 0.0
            stop_msg.angular.z = 0.0
            node._pub_cmd_safe.publish(stop_msg)
        except Exception:
            pass
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
