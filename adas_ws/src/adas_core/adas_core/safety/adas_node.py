#!/usr/bin/env python3
"""
adas_node.py — Main ADAS controller (serial-bridge variant)

Single 20 Hz node that integrates AEB, ACC, LKA and mode management.
Replaces the individual aeb_node / acc_node / lka_node / safety_arbiter
pipeline that existed in the CAN-bus build.

━━━ Subscriptions ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  /sensor/lidar_range   Range      BEST_EFFORT   AEB + ACC ranging
  /lane/data            LaneData   BEST_EFFORT   LKA lateral error
  /switch/autonomous    Bool       RELIABLE      engage/disengage AUTO
  /switch/acc           Bool       RELIABLE      toggle ACC in AUTO
  /switch/lka           Bool       RELIABLE      toggle LKA in AUTO
  /adas/manual_cmd      Twist      RELIABLE      manual drive from dashboard

━━━ Publications ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  /vehicle/cmd_vel_safe  Twist    RELIABLE  → serial_bridge_node
  /system/mode           String   RELIABLE  MANUAL / AUTO / EMERGENCY_STOP
  /system/aeb_state      String   RELIABLE  CLEAR/WARNING/PARTIAL/HARD/STOP
  /system/acc_state      String   RELIABLE  IDLE/APPROACH/FOLLOW/STOP
  /system/lka_state      String   RELIABLE  IDLE/ACTIVE/EMERGENCY
  /system/distance       Float32  RELIABLE  latest lidar range in metres
  /system/ttc            Float32  RELIABLE  Time-To-Collision in seconds (-1 = N/A)

━━━ Safety priority (highest → lowest) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. AEB STOP  → zero speed (MANUAL: hold; AUTO: demote to MANUAL)
  2. TTC override → force STOP when TTC < TTC_STOP_S
  3. AEB scale → multiply base speed by zone factor
  4. ACC speed → replaces constant AUTO speed when in range
  5. AUTO constant 250 mm/s
  6. MANUAL passthrough from /adas/manual_cmd
"""

import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String, Bool, Float32
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Range

try:
    from adas_msgs.msg import LaneData
    _HAVE_LANE_MSG = True
except ImportError:
    _HAVE_LANE_MSG = False

# ── AEB zone thresholds (metres) ─────────────────────────────────────────────
_AEB_CLEAR   = 0.40   # > 40 cm  → CLEAR
_AEB_WARN    = 0.30   # 30-40 cm → WARNING
_AEB_PARTIAL = 0.20   # 20-30 cm → PARTIAL
_AEB_HARD    = 0.10   # 10-20 cm → HARD
                      # <  10 cm → STOP

_AEB_FACTOR: dict[str, float] = {
    'CLEAR':   1.00,
    'WARNING': 0.80,
    'PARTIAL': 0.50,
    'HARD':    0.10,
    'STOP':    0.00,
}

# ── TTC (Time-To-Collision) thresholds ───────────────────────────────────────
TTC_WARN_S  = 3.0   # TTC < 3 s → at least WARNING zone
TTC_STOP_S  = 0.5   # TTC < 0.5 s → force STOP regardless of distance zone
TTC_INVALID = -1.0  # published when TTC cannot be estimated

# ── Vehicle constants ─────────────────────────────────────────────────────────
SPEED_AUTO_MS  = 0.250   # 250 mm/s expressed in m/s

# ── ACC parameters ────────────────────────────────────────────────────────────
ACC_TARGET_M   = 0.40
ACC_TRIGGER_M  = 0.40
ACC_KP, ACC_KI, ACC_KD = 1.2, 0.03, 0.20

# ── LKA parameters ────────────────────────────────────────────────────────────
LKA_KP, LKA_KI, LKA_KD = 1.5, 0.05, 0.10
LKA_MAX_STEER  = 2.5    # rad
LKA_DEADBAND   = 0.02   # m
LKA_MIN_SPEED  = 0.05   # m/s

# ── Mode strings ──────────────────────────────────────────────────────────────
MANUAL = 'MANUAL'
AUTO   = 'AUTO'
ESTOP  = 'EMERGENCY_STOP'


# ─────────────────────────────────────────────────────────────────────────────
class _PID:
    """Discrete PID with anti-windup integral clamp."""

    def __init__(self, kp: float, ki: float, kd: float,
                 out_min: float | None = None,
                 out_max: float | None = None):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.out_min, self.out_max = out_min, out_max
        self._integral  = 0.0
        self._prev_err  = 0.0
        self._prev_t    = None

    def reset(self):
        self._integral = 0.0
        self._prev_err = 0.0
        self._prev_t   = None

    def compute(self, error: float) -> float:
        now = time.monotonic()
        dt  = (now - self._prev_t) if self._prev_t is not None else 0.05
        dt  = max(dt, 1e-6)
        self._prev_t = now

        self._integral += error * dt
        if self.out_max is not None and self.ki:
            self._integral = min(self._integral, self.out_max / self.ki)
        if self.out_min is not None and self.ki:
            self._integral = max(self._integral, self.out_min / self.ki)

        deriv = (error - self._prev_err) / dt
        self._prev_err = error

        out = self.kp * error + self.ki * self._integral + self.kd * deriv
        if self.out_min is not None:
            out = max(out, self.out_min)
        if self.out_max is not None:
            out = min(out, self.out_max)
        return out


# ─────────────────────────────────────────────────────────────────────────────
class AdasNode(Node):

    def __init__(self):
        super().__init__('adas_node')
        self._lock = threading.Lock()

        # ── Mode & feature switches ───────────────────────────────────────────
        self._mode    : str  = MANUAL
        self._sw_acc  : bool = False
        self._sw_lka  : bool = False

        # ── Latest sensor readings ────────────────────────────────────────────
        self._lidar_m       : float | None = None
        self._lidar_t       : float        = 0.0    # monotonic time of last reading
        self._lane_error_m  : float        = 0.0
        self._lane_recovery : str          = ''
        self._manual_cmd    : Twist        = Twist()

        # ── Published state cache ─────────────────────────────────────────────
        self._aeb_state : str = 'CLEAR'
        self._acc_state : str = 'IDLE'
        self._lka_state : str = 'IDLE'

        # ── PID controllers ───────────────────────────────────────────────────
        self._acc_pid = _PID(ACC_KP, ACC_KI, ACC_KD,
                             out_min=0.0, out_max=SPEED_AUTO_MS)
        self._lka_pid = _PID(LKA_KP, LKA_KI, LKA_KD,
                             out_min=-LKA_MAX_STEER, out_max=LKA_MAX_STEER)

        # ── QoS ───────────────────────────────────────────────────────────────
        _be = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                         history=HistoryPolicy.KEEP_LAST, depth=1)
        _rel = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                          history=HistoryPolicy.KEEP_LAST, depth=10)

        # ── Subscriptions ─────────────────────────────────────────────────────
        self.create_subscription(
            Range,  '/sensor/lidar_range', self._on_lidar,   _be)
        self.create_subscription(
            Bool,   '/switch/autonomous',  self._on_sw_auto, _rel)
        self.create_subscription(
            Bool,   '/switch/acc',         self._on_sw_acc,  _rel)
        self.create_subscription(
            Bool,   '/switch/lka',         self._on_sw_lka,  _rel)
        self.create_subscription(
            Twist,  '/adas/manual_cmd',    self._on_manual,  _rel)

        if _HAVE_LANE_MSG:
            self.create_subscription(
                LaneData, '/lane/data', self._on_lane, _be)
        else:
            self.get_logger().warning(
                'adas_msgs not found — /lane/data disabled (LKA inactive)')

        # ── Publishers ────────────────────────────────────────────────────────
        self._pub_cmd  = self.create_publisher(Twist,   '/vehicle/cmd_vel_safe', _rel)
        self._pub_mode = self.create_publisher(String,  '/system/mode',          _rel)
        self._pub_aeb  = self.create_publisher(String,  '/system/aeb_state',     _rel)
        self._pub_acc  = self.create_publisher(String,  '/system/acc_state',     _rel)
        self._pub_lka  = self.create_publisher(String,  '/system/lka_state',     _rel)
        self._pub_dist = self.create_publisher(Float32, '/system/distance',      _rel)
        self._pub_ttc  = self.create_publisher(Float32, '/system/ttc',           _rel)

        # ── 20 Hz main loop ───────────────────────────────────────────────────
        self.create_timer(0.05, self._loop)

        self.get_logger().info(
            'adas_node ready — AUTO speed 250 mm/s  '
            'AEB thresholds 40/30/20/10 cm  '
            'TTC stop 0.5 s warn 3 s  '
            'ACC target 40 cm  LKA deadband 2 cm')

    # ─────────────────────────────────────────────────────────────────────────
    # Subscription callbacks
    # ─────────────────────────────────────────────────────────────────────────
    def _on_lidar(self, msg: Range):
        with self._lock:
            self._lidar_m = float(msg.range)
            self._lidar_t = time.monotonic()

    def _on_sw_auto(self, msg: Bool):
        with self._lock:
            if msg.data and self._mode == MANUAL:
                self._mode = AUTO
                self._acc_pid.reset()
                self._lka_pid.reset()
                self.get_logger().info('Mode → AUTO')
            elif not msg.data and self._mode == AUTO:
                self._mode = MANUAL
                self.get_logger().info('Mode → MANUAL (switch off)')

    def _on_sw_acc(self, msg: Bool):
        with self._lock:
            self._sw_acc = msg.data
            if not msg.data:
                self._acc_pid.reset()

    def _on_sw_lka(self, msg: Bool):
        with self._lock:
            self._sw_lka = msg.data
            if not msg.data:
                self._lka_pid.reset()

    def _on_manual(self, msg: Twist):
        with self._lock:
            self._manual_cmd = msg

    def _on_lane(self, msg: 'LaneData'):
        with self._lock:
            self._lane_error_m  = float(msg.lateral_error_m)
            self._lane_recovery = str(msg.recovery_mode)

    # ─────────────────────────────────────────────────────────────────────────
    # TTC estimation
    # ─────────────────────────────────────────────────────────────────────────
    def _compute_ttc(self, dist: float | None,
                     speed_ms: float) -> float:
        """
        Estimate Time-To-Collision in seconds.

        TTC = dist / |speed|  — only valid when approaching (speed > 0 = forward)
        and distance is known.

        Returns TTC_INVALID (-1.0) when TTC cannot be estimated.
        """
        if dist is None or dist <= 0.0:
            return TTC_INVALID
        if speed_ms < 0.01:   # stationary or reversing — no collision risk
            return TTC_INVALID
        return dist / speed_ms

    # ─────────────────────────────────────────────────────────────────────────
    # AEB  (distance-based zones + TTC override)
    # ─────────────────────────────────────────────────────────────────────────
    def _aeb_filter(self, dist: float | None,
                    base_speed: float,
                    ttc: float) -> tuple[float, str]:
        """
        Returns (filtered_speed_ms, aeb_zone_str).

        Distance zones:
          > 0.40 m → CLEAR   (100% speed)
          > 0.30 m → WARNING (80%)
          > 0.20 m → PARTIAL (50%)
          > 0.10 m → HARD    (10%)
          ≤ 0.10 m → STOP    (0%)

        TTC overrides:
          TTC < TTC_STOP_S (0.5 s) → force STOP
          TTC < TTC_WARN_S (3.0 s) → at least WARNING zone
        """
        if dist is None:
            return base_speed, 'CLEAR'

        # Distance-based zone
        if   dist > _AEB_CLEAR:   zone = 'CLEAR'
        elif dist > _AEB_WARN:    zone = 'WARNING'
        elif dist > _AEB_PARTIAL: zone = 'PARTIAL'
        elif dist > _AEB_HARD:    zone = 'HARD'
        else:                      zone = 'STOP'

        # TTC overrides — escalate zone if TTC is dangerously low
        if ttc > 0.0:
            if ttc < TTC_STOP_S:
                zone = 'STOP'
            elif ttc < TTC_WARN_S and zone == 'CLEAR':
                zone = 'WARNING'

        return base_speed * _AEB_FACTOR[zone], zone

    # ─────────────────────────────────────────────────────────────────────────
    # ACC
    # ─────────────────────────────────────────────────────────────────────────
    def _acc_compute(self, dist: float | None) -> tuple[float, str]:
        """
        Returns (target_speed_ms, acc_state_str) before AEB filter.
        PID error positive → closing → slow down.
        """
        if dist is None or dist > ACC_TRIGGER_M:
            self._acc_pid.reset()
            return SPEED_AUTO_MS, 'IDLE'

        error = dist - ACC_TARGET_M
        adj   = self._acc_pid.compute(error)
        speed = max(0.0, min(SPEED_AUTO_MS + adj, SPEED_AUTO_MS))

        if speed < 1e-3:
            return 0.0, 'STOP'
        if dist <= ACC_TARGET_M:
            return speed, 'FOLLOW'
        return speed, 'APPROACH'

    # ─────────────────────────────────────────────────────────────────────────
    # LKA
    # ─────────────────────────────────────────────────────────────────────────
    def _lka_compute(self, speed_ms: float,
                     error_m: float,
                     recovery: str) -> tuple[float, str]:
        """
        Returns (steer_rad, lka_state_str).
        Positive steer = left; negative = right.
        Negate error: positive lateral error means car is right of centre → steer left.
        """
        if recovery == ESTOP:
            return 0.0, 'EMERGENCY'
        if speed_ms < LKA_MIN_SPEED:
            return 0.0, 'IDLE'
        if abs(error_m) < LKA_DEADBAND:
            return 0.0, 'IDLE'

        steer = self._lka_pid.compute(-error_m)
        steer = max(-LKA_MAX_STEER, min(steer, LKA_MAX_STEER))
        return steer, 'ACTIVE'

    # ─────────────────────────────────────────────────────────────────────────
    # Main 20 Hz loop
    # ─────────────────────────────────────────────────────────────────────────
    def _loop(self):
        # ── Snapshot shared state ────────────────────────────────────────────
        with self._lock:
            mode        = self._mode
            dist        = self._lidar_m
            sw_acc      = self._sw_acc
            sw_lka      = self._sw_lka
            lane_err    = self._lane_error_m
            lane_rc     = self._lane_recovery
            cmd_in      = self._manual_cmd

        steer_cmd = 0.0
        acc_state = 'IDLE'
        lka_state = 'IDLE'

        # ── Speed selection ───────────────────────────────────────────────────
        if mode == MANUAL:
            speed_ms  = cmd_in.linear.x
            steer_cmd = cmd_in.angular.z
            # Compute TTC using current manual speed
            ttc = self._compute_ttc(dist, abs(speed_ms))
            # AEB still active — scales speed, holds at 0 if STOP
            speed_ms, aeb_state = self._aeb_filter(dist, speed_ms, ttc)

        else:  # AUTO
            speed_ms = SPEED_AUTO_MS

            if sw_acc:
                speed_ms, acc_state = self._acc_compute(dist)
            else:
                self._acc_pid.reset()

            ttc = self._compute_ttc(dist, abs(speed_ms))
            speed_ms, aeb_state = self._aeb_filter(dist, speed_ms, ttc)

            if aeb_state == 'STOP':
                with self._lock:
                    self._mode = MANUAL
                mode = MANUAL
                self.get_logger().warning('AEB STOP in AUTO → MANUAL')

            if sw_lka:
                steer_cmd, lka_state = self._lka_compute(speed_ms, lane_err, lane_rc)
                if lka_state == 'EMERGENCY':
                    with self._lock:
                        self._sw_lka = False
                    self._lka_pid.reset()
                    self.get_logger().warning('Lane EMERGENCY_STOP → LKA disabled')
            else:
                self._lka_pid.reset()

        # ── Update published state cache ─────────────────────────────────────
        with self._lock:
            self._aeb_state = aeb_state
            self._acc_state = acc_state
            self._lka_state = lka_state

        # ── Publish /vehicle/cmd_vel_safe ────────────────────────────────────
        cmd = Twist()
        cmd.linear.x  = float(speed_ms)
        cmd.angular.z = float(steer_cmd)
        self._pub_cmd.publish(cmd)

        # ── Publish /system/mode ─────────────────────────────────────────────
        pub_mode = ESTOP if aeb_state == 'STOP' else mode
        self._pub_mode.publish(String(data=pub_mode))

        # ── Publish feature states ───────────────────────────────────────────
        self._pub_aeb.publish(String(data=aeb_state))
        self._pub_acc.publish(String(data=acc_state))
        self._pub_lka.publish(String(data=lka_state))

        # ── Publish distance ─────────────────────────────────────────────────
        if dist is not None:
            self._pub_dist.publish(Float32(data=float(dist)))

        # ── Publish TTC ──────────────────────────────────────────────────────
        self._pub_ttc.publish(Float32(data=float(ttc)))


# ─────────────────────────────────────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)
    node = AdasNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
