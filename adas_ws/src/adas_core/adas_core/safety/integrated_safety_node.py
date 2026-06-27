#!/usr/bin/env python3
"""
integrated_safety_node.py
Single integrated safety controller for RC ADAS vehicle.

Handles: AEB · ACC · LKA · mode management · watchdogs · GPIO LEDs
Publishes at 20 Hz on /vehicle/cmd_vel_safe.

Safety priority (highest → lowest):
  1. ESTOP watchdog
  2. AEB STOP
  3. AEB PARTIAL/HARD (scale speed)
  4. ACC speed command
  5. AUTO constant speed 250 mm/s
  6. MANUAL cmd_vel_input passthrough
"""

import math
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String, Bool
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Range, Imu

try:
    import RPi.GPIO as GPIO
    _GPIO_OK = True
except (ImportError, RuntimeError):
    _GPIO_OK = False


# ── GPIO pin assignments (BCM) ────────────────────────────────────────────────
PIN_POWER    = 17   # White  – Power / Status
PIN_MANUAL   = 27   # Green  – Manual mode
PIN_AUTO     = 22   # Blue   – Autonomous mode
PIN_LKA      = 23   # Green  – LKA active
PIN_ACC      = 24   # Cyan   – ACC active
PIN_AEB_WARN = 16   # Yellow – AEB Warning (blink 2 Hz)
PIN_AEB_STOP = 26   # Red    – AEB Stop

_ALL_PINS = [PIN_POWER, PIN_MANUAL, PIN_AUTO, PIN_LKA,
             PIN_ACC, PIN_AEB_WARN, PIN_AEB_STOP]

# ── Vehicle constants ─────────────────────────────────────────────────────────
SPEED_AUTO_MS   = 0.250   # 250 mm/s in m/s
SPEED_MAX_MS    = 0.500   # 500 mm/s in m/s
STEER_MAX_RAD   = 2.500   # 2500 mrad

# ── AEB thresholds (metres) ───────────────────────────────────────────────────
_AEB_CLEAR   = 0.30
_AEB_WARN    = 0.20
_AEB_PARTIAL = 0.10
_AEB_HARD    = 0.05

_AEB_FACTOR = {
    'CLEAR':      1.00,
    'WARNING':    0.80,
    'PARTIAL':    0.50,
    'HARD_BRAKE': 0.10,
    'STOP':       0.00,
}

# ── ACC parameters ────────────────────────────────────────────────────────────
ACC_TARGET_M  = 0.50
ACC_TRIGGER_M = 0.65
ACC_KP, ACC_KI, ACC_KD = 1.2, 0.03, 0.20

# ── LKA parameters ────────────────────────────────────────────────────────────
LKA_KP, LKA_KI, LKA_KD = 1.5, 0.05, 0.10
LKA_MAX_STEER   = 2.50    # rad
LKA_DEADBAND_M  = 0.02    # m
LKA_MIN_SPEED   = 0.05    # m/s

# ── Watchdog timeouts ─────────────────────────────────────────────────────────
WD_CAN_S       = 0.500
WD_LIDAR_WARN  = 1.000
WD_LIDAR_ESTOP = 2.000
WD_STEER_RAD   = 2.300
WD_IMU_YAW     = 2.500   # rad/s
WD_LANE_FRAMES = 5

# ── Mode strings ──────────────────────────────────────────────────────────────
MANUAL = 'MANUAL'
AUTO   = 'AUTO'
ESTOP  = 'EMERGENCY_STOP'


# ─────────────────────────────────────────────────────────────────────────────
class _PID:
    """Discrete PID controller with anti-windup clamp."""

    def __init__(self, kp: float, ki: float, kd: float,
                 out_min: float = None, out_max: float = None):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.out_min, self.out_max = out_min, out_max
        self._integral   = 0.0
        self._prev_error = 0.0
        self._prev_t     = None

    def reset(self):
        self._integral   = 0.0
        self._prev_error = 0.0
        self._prev_t     = None

    def compute(self, error: float) -> float:
        now = time.monotonic()
        dt  = (now - self._prev_t) if self._prev_t else 0.05
        dt  = max(dt, 1e-6)
        self._prev_t = now

        self._integral += error * dt
        # Anti-windup: clamp integral contribution
        if self.out_max is not None and self.ki:
            self._integral = min(self._integral, self.out_max / self.ki)
        if self.out_min is not None and self.ki:
            self._integral = max(self._integral, self.out_min / self.ki)

        deriv = (error - self._prev_error) / dt
        self._prev_error = error

        out = self.kp * error + self.ki * self._integral + self.kd * deriv
        if self.out_min is not None:
            out = max(out, self.out_min)
        if self.out_max is not None:
            out = min(out, self.out_max)
        return out


# ─────────────────────────────────────────────────────────────────────────────
class IntegratedSafetyNode(Node):

    def __init__(self):
        super().__init__('integrated_safety_node')
        self._lock = threading.Lock()

        # ── Mode & switches ───────────────────────────────────────────────────
        self._mode    = MANUAL
        self._sw_auto = False
        self._sw_acc  = False
        self._sw_lka  = False

        # ── Sensor state ──────────────────────────────────────────────────────
        self._lidar_m        : float | None = None
        self._lidar_stamp    : float | None = None
        self._imu_yaw_rate   : float        = 0.0
        self._cmd_vel_input  : Twist        = Twist()
        self._lane_error_m   : float        = 0.0
        self._lane_recovery  : str          = ''
        self._lane_estop_cnt : int          = 0

        # ── CAN heartbeat ─────────────────────────────────────────────────────
        self._can_last_t : float = time.monotonic()

        # ── AEB state ─────────────────────────────────────────────────────────
        self._aeb_state          : str  = 'CLEAR'
        self._aeb_blink_phase    : bool = False   # toggled 4 Hz → 2 Hz blink

        # ── PID controllers ───────────────────────────────────────────────────
        self._acc_pid = _PID(ACC_KP, ACC_KI, ACC_KD,
                             out_min=0.0, out_max=SPEED_AUTO_MS)
        self._lka_pid = _PID(LKA_KP, LKA_KI, LKA_KD,
                             out_min=-LKA_MAX_STEER, out_max=LKA_MAX_STEER)

        # ── Watchdog flags ────────────────────────────────────────────────────
        self._wd_can   = True
        self._wd_lidar = True
        self._wd_steer = True
        self._wd_imu   = True
        self._wd_lane  = True

        # ── Current output (for watchdog steer check) ─────────────────────────
        self._cur_speed  : float = 0.0
        self._cur_steer  : float = 0.0

        # ── GPIO ──────────────────────────────────────────────────────────────
        self._init_gpio()

        # ── QoS profiles ──────────────────────────────────────────────────────
        be = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1)
        rel = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10)

        # ── Subscriptions ──────────────────────────────────────────────────────
        self.create_subscription(Range,  '/sensor/lidar_range',
                                 self._on_lidar,       be)
        self.create_subscription(Imu,    '/sensor/imu',
                                 self._on_imu,         be)
        self.create_subscription(Twist,  '/vehicle/cmd_vel_input',
                                 self._on_cmd_vel,     rel)
        self.create_subscription(Bool,   '/switch/autonomous',
                                 self._on_sw_auto,     rel)
        self.create_subscription(Bool,   '/switch/acc',
                                 self._on_sw_acc,      rel)
        self.create_subscription(Bool,   '/switch/lka',
                                 self._on_sw_lka,      rel)
        self.create_subscription(Bool,   '/switch/manual_override',
                                 self._on_sw_manual,   rel)
        # CAN heartbeat – accept either dedicated topic or vehicle feedback
        self.create_subscription(String, '/can/heartbeat',
                                 self._on_can_hb,      rel)
        self.create_subscription(String, '/vehicle/rpm',
                                 self._on_can_hb,      be)
        # Lane data – try custom msg, fall back to String
        try:
            from adas_core_msgs.msg import LaneData  # type: ignore
            self.create_subscription(LaneData, '/lane/data',
                                     self._on_lane_msg, be)
            self.get_logger().info('Using adas_core_msgs/LaneData for /lane/data')
        except ImportError:
            self.create_subscription(String, '/lane/data',
                                     self._on_lane_str, be)
            self.get_logger().warn(
                'adas_core_msgs not found – /lane/data parsed as String '
                '"lateral_error_m|recovery_mode"')

        # ── Publishers ────────────────────────────────────────────────────────
        self._pub_cmd    = self.create_publisher(Twist,  '/vehicle/cmd_vel_safe', rel)
        self._pub_mode   = self.create_publisher(String, '/system/mode',          rel)
        self._pub_status = self.create_publisher(String, '/system/status',        rel)
        self._pub_leds   = self.create_publisher(String, '/led/states',           rel)
        self._pub_wd     = self.create_publisher(String, '/system/watchdog',      rel)

        # ── Timers ────────────────────────────────────────────────────────────
        self.create_timer(1.0 / 20.0, self._safety_loop)   # 20 Hz – main loop
        self.create_timer(0.25,        self._blink_tick)    # 4 Hz  – 2 Hz blink
        self.create_timer(0.10,        self._watchdog_tick) # 10 Hz – watchdogs

        self.get_logger().info('integrated_safety_node ready')

    # ─────────────────────────────────────────────────────────────────────────
    # GPIO helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _init_gpio(self):
        if not _GPIO_OK:
            self.get_logger().warn('RPi.GPIO unavailable – LED output disabled')
            return
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in _ALL_PINS:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.output(PIN_POWER, GPIO.HIGH)   # power LED always on at startup

    def _gpio_set(self, pin: int, on: bool):
        if _GPIO_OK:
            GPIO.output(pin, GPIO.HIGH if on else GPIO.LOW)

    def _gpio_cleanup(self):
        if _GPIO_OK:
            for pin in _ALL_PINS:
                GPIO.output(pin, GPIO.LOW)
            GPIO.cleanup()

    # ─────────────────────────────────────────────────────────────────────────
    # Subscription callbacks
    # ─────────────────────────────────────────────────────────────────────────
    def _on_lidar(self, msg: Range):
        with self._lock:
            self._lidar_m     = float(msg.range)
            self._lidar_stamp = time.monotonic()

    def _on_imu(self, msg: Imu):
        with self._lock:
            self._imu_yaw_rate = msg.angular_velocity.z

    def _on_cmd_vel(self, msg: Twist):
        with self._lock:
            self._cmd_vel_input = msg

    def _on_sw_auto(self, msg: Bool):
        with self._lock:
            self._sw_auto = msg.data
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

    def _on_sw_manual(self, msg: Bool):
        with self._lock:
            if msg.data:
                self._mode    = MANUAL
                self._sw_auto = False
                self.get_logger().warn('Manual override → MANUAL')

    def _on_can_hb(self, _msg):
        with self._lock:
            self._can_last_t = time.monotonic()

    def _on_lane_msg(self, msg):
        """Handler for adas_core_msgs/LaneData."""
        with self._lock:
            self._lane_error_m  = float(msg.lateral_error_m)
            self._lane_recovery = str(getattr(msg, 'recovery_mode', ''))
            self._update_lane_estop_count()

    def _on_lane_str(self, msg: String):
        """Fallback handler: 'lateral_error_m|recovery_mode'."""
        parts = msg.data.split('|')
        with self._lock:
            try:
                self._lane_error_m  = float(parts[0]) if parts else 0.0
                self._lane_recovery = parts[1].strip() if len(parts) > 1 else ''
            except (ValueError, IndexError):
                pass
            self._update_lane_estop_count()

    def _update_lane_estop_count(self):
        """Must be called while _lock is held."""
        if self._lane_recovery == ESTOP:
            self._lane_estop_count += 1
        else:
            self._lane_estop_count = 0

    # ─────────────────────────────────────────────────────────────────────────
    # Blink tick  (4 Hz → toggles phase → 2 Hz LED blink)
    # ─────────────────────────────────────────────────────────────────────────
    def _blink_tick(self):
        self._aeb_blink_phase = not self._aeb_blink_phase

    # ─────────────────────────────────────────────────────────────────────────
    # Watchdog tick (10 Hz)
    # ─────────────────────────────────────────────────────────────────────────
    def _watchdog_tick(self):
        now     = time.monotonic()
        reasons = []

        with self._lock:
            # CAN silence
            can_age      = now - self._can_last_t
            self._wd_can = can_age < WD_CAN_S
            if not self._wd_can:
                reasons.append(f'CAN_SILENCE({can_age:.2f}s)')

            # LiDAR silence
            if self._lidar_stamp is not None:
                age = now - self._lidar_stamp
                if age > WD_LIDAR_ESTOP:
                    self._wd_lidar = False
                    reasons.append(f'LIDAR_SILENCE({age:.2f}s)')
                elif age > WD_LIDAR_WARN:
                    self._wd_lidar = False
                    self.get_logger().warn(f'LiDAR silent {age:.2f}s')
                else:
                    self._wd_lidar = True

            # IMU yaw rate
            yaw = abs(self._imu_yaw_rate)
            self._wd_imu = yaw < WD_IMU_YAW
            if not self._wd_imu:
                reasons.append(f'IMU_YAW_RATE({yaw:.2f}rad/s)')

            # Steering overflow (only meaningful in AUTO – triggers MANUAL demotion)
            steer_abs    = abs(self._cur_steer)
            self._wd_steer = steer_abs < WD_STEER_RAD
            if not self._wd_steer and self._mode == AUTO:
                self._mode = MANUAL
                self.get_logger().warn(
                    f'Steer overflow {steer_abs:.3f} rad → MANUAL')

            # Lane consecutive ESTOP frames
            self._wd_lane = self._lane_estop_count < WD_LANE_FRAMES
            if not self._wd_lane:
                self._sw_lka = False
                self._lka_pid.reset()
                self._lane_estop_count = 0
                self.get_logger().warn('Lane ESTOP×5 → LKA disabled')

            # Trigger ESTOP
            if reasons and self._mode != ESTOP:
                self._mode = ESTOP
                for r in reasons:
                    self.get_logger().error(f'WATCHDOG ESTOP: {r}')

        # Publish watchdog state string
        wd = String()
        wd.data = (
            f'CAN:{"OK"   if self._wd_can   else "FAIL"}|'
            f'LIDAR:{"OK" if self._wd_lidar else "FAIL"}|'
            f'STEER:{"OK" if self._wd_steer else "FAIL"}|'
            f'IMU:{"OK"   if self._wd_imu   else "FAIL"}|'
            f'LANE:{"OK"  if self._wd_lane  else "FAIL"}'
        )
        self._pub_wd.publish(wd)

    # ─────────────────────────────────────────────────────────────────────────
    # AEB  (always active in all modes)
    # ─────────────────────────────────────────────────────────────────────────
    def _aeb_filter(self, dist_m: float | None,
                    base_speed: float,
                    mode: str) -> tuple[float, str]:
        """
        Returns (filtered_speed_ms, aeb_state_str).
        Caller must handle STOP-in-AUTO → mode switch.
        """
        if dist_m is None:
            return base_speed, 'CLEAR'

        if   dist_m > _AEB_CLEAR:   state = 'CLEAR'
        elif dist_m > _AEB_WARN:    state = 'WARNING'
        elif dist_m > _AEB_PARTIAL: state = 'PARTIAL'
        elif dist_m > _AEB_HARD:    state = 'HARD_BRAKE'
        else:                        state = 'STOP'

        speed = base_speed * _AEB_FACTOR[state]
        return speed, state

    # ─────────────────────────────────────────────────────────────────────────
    # ACC
    # ─────────────────────────────────────────────────────────────────────────
    def _acc_speed(self, dist_m: float | None) -> float:
        """Returns target speed (m/s) before AEB filter."""
        if dist_m is None or dist_m > ACC_TRIGGER_M:
            self._acc_pid.reset()
            return SPEED_AUTO_MS
        # Negative error when too close (distance < target) → slow down
        error  = dist_m - ACC_TARGET_M
        adjust = self._acc_pid.compute(error)
        return max(0.0, min(SPEED_AUTO_MS + adjust, SPEED_AUTO_MS))

    # ─────────────────────────────────────────────────────────────────────────
    # LKA
    # ─────────────────────────────────────────────────────────────────────────
    def _lka_steer(self, speed_ms: float) -> float:
        """Returns steering command (rad). 0 if below threshold."""
        if speed_ms < LKA_MIN_SPEED:
            return 0.0
        err = self._lane_error_m
        if abs(err) < LKA_DEADBAND_M:
            return 0.0
        # Negate: positive lateral error (car right of centre) → steer left (negative)
        steer = self._lka_pid.compute(-err)
        return max(-LKA_MAX_STEER, min(steer, LKA_MAX_STEER))

    # ─────────────────────────────────────────────────────────────────────────
    # Main 20 Hz safety loop
    # ─────────────────────────────────────────────────────────────────────────
    def _safety_loop(self):
        # Snapshot shared state under lock
        with self._lock:
            mode          = self._mode
            lidar         = self._lidar_m
            sw_acc        = self._sw_acc
            sw_lka        = self._sw_lka
            lane_recovery = self._lane_recovery
            cmd_in        = self._cmd_vel_input

        steer_cmd = 0.0

        # ── Priority 1: ESTOP ───────────────────────────────────────────────
        if mode == ESTOP:
            speed_ms  = 0.0
            aeb_state = 'STOP'
            steer_cmd = 0.0

        # ── Priority 6: MANUAL passthrough ──────────────────────────────────
        elif mode == MANUAL:
            speed_ms  = cmd_in.linear.x
            steer_cmd = cmd_in.angular.z
            # AEB still active in manual
            speed_ms, aeb_state = self._aeb_filter(lidar, speed_ms, mode)
            # In MANUAL, STOP just holds at 0 (no mode switch)

        # ── AUTO ─────────────────────────────────────────────────────────────
        else:
            # Priority 5: constant 250 mm/s
            speed_ms = SPEED_AUTO_MS

            # Priority 4: ACC overrides constant speed
            if sw_acc:
                speed_ms = self._acc_speed(lidar)
            else:
                self._acc_pid.reset()

            # Priority 2+3: AEB filter
            speed_ms, aeb_state = self._aeb_filter(lidar, speed_ms, AUTO)

            # AEB STOP in AUTO → demote to MANUAL
            if aeb_state == 'STOP':
                with self._lock:
                    self._mode    = MANUAL
                    self._sw_auto = False
                mode = MANUAL
                self.get_logger().warn('AEB STOP in AUTO → MANUAL')

            # LKA steering
            if sw_lka and lane_recovery != ESTOP:
                steer_cmd = self._lka_steer(speed_ms)
            else:
                if sw_lka and lane_recovery == ESTOP:
                    with self._lock:
                        self._sw_lka = False
                    self._lka_pid.reset()
                    self.get_logger().warn('Lane recovery ESTOP → LKA disabled')
                steer_cmd = 0.0

        # Update for watchdog steer-overflow check
        with self._lock:
            self._aeb_state = aeb_state
            self._cur_speed = speed_ms
            self._cur_steer = steer_cmd

        # ── Publish /vehicle/cmd_vel_safe ────────────────────────────────────
        cmd = Twist()
        cmd.linear.x  = float(speed_ms)
        cmd.angular.z = float(steer_cmd)
        self._pub_cmd.publish(cmd)

        # ── Publish mode ─────────────────────────────────────────────────────
        self._pub_mode.publish(String(data=mode))

        # ── LEDs ─────────────────────────────────────────────────────────────
        led_str = self._drive_leds(mode, aeb_state, sw_acc, sw_lka)
        self._pub_leds.publish(String(data=led_str))

        # ── Status ───────────────────────────────────────────────────────────
        dist_s = f'{lidar:.3f}' if lidar is not None else 'N/A'
        status = (
            f'MODE:{mode}|'
            f'AEB:{aeb_state}|'
            f'DIST:{dist_s}|'
            f'SPD:{speed_ms * 1000:.1f}mms|'
            f'STEER:{steer_cmd:.3f}rad|'
            f'ACC:{"ON" if sw_acc else "OFF"}|'
            f'LKA:{"ON" if sw_lka else "OFF"}|'
            f'CAN:{"OK" if self._wd_can else "FAIL"}|'
            f'LIDAR:{"OK" if self._wd_lidar else "FAIL"}'
        )
        self._pub_status.publish(String(data=status))

    # ─────────────────────────────────────────────────────────────────────────
    # LED driver
    # ─────────────────────────────────────────────────────────────────────────
    def _drive_leds(self, mode: str, aeb_state: str,
                    sw_acc: bool, sw_lka: bool) -> str:
        is_auto  = mode == AUTO
        is_estop = mode == ESTOP

        pwr     = True
        manual  = (mode == MANUAL) or is_estop
        auto_l  = is_auto
        lka_l   = is_auto and sw_lka
        acc_l   = is_auto and sw_acc
        warn_l  = (aeb_state == 'WARNING') and self._aeb_blink_phase
        stop_l  = (aeb_state == 'STOP') or is_estop

        self._gpio_set(PIN_POWER,    pwr)
        self._gpio_set(PIN_MANUAL,   manual)
        self._gpio_set(PIN_AUTO,     auto_l)
        self._gpio_set(PIN_LKA,      lka_l)
        self._gpio_set(PIN_ACC,      acc_l)
        self._gpio_set(PIN_AEB_WARN, warn_l)
        self._gpio_set(PIN_AEB_STOP, stop_l)

        return (
            f'POWER:{int(pwr)}|'
            f'MANUAL:{int(manual)}|'
            f'AUTO:{int(auto_l)}|'
            f'LKA:{int(lka_l)}|'
            f'ACC:{int(acc_l)}|'
            f'AEB_WARN:{int(warn_l)}|'
            f'AEB_STOP:{int(stop_l)}'
        )

    # ─────────────────────────────────────────────────────────────────────────
    def destroy_node(self):
        self._gpio_cleanup()
        super().destroy_node()


# ─────────────────────────────────────────────────────────────────────────────
def main(args=None):
    rclpy.init(args=args)
    node = IntegratedSafetyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
