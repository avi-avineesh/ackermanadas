"""
can_bridge_node.py — ADAS CAN Bridge  (single-Arduino revision)
Bridges ROS 2 topics to the combined_ecu Arduino via can0 (socketcan).

CAN TX (RPi → Arduino):
  0x110  steer_mrad   int16 BE  bytes 0-1   ±2500 mrad
  0x120  speed_mms    int16 BE  bytes 0-1   ±500  mm/s
         brake_pct    uint8     byte  2     0-100 %
         mode         uint8     byte  3     0=IDLE 1=AUTO 2=ESTOP

CAN RX (Arduino → RPi):
  0x320  status       uint8     byte  0     0=IDLE 1=RUNNING 2=ESTOP
         hb_counter   uint8     byte  1     wraps 0-255

ROS Subscribes : /vehicle/cmd_vel_safe  (geometry_msgs/Twist)
ROS Publishes  : /vehicle/rpm           (std_msgs/String)  "status,counter"
                 /can/heartbeat         (std_msgs/String)  "status,counter"

Watchdogs:
  cmd_vel silence  > watchdog_sec (default 10 s) → send MODE_IDLE
  0x320 silence    > 500 ms                       → send MODE_ESTOP + log error
"""

from __future__ import annotations

import os
import struct
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from geometry_msgs.msg import Twist
from std_msgs.msg import String

# ── CAN IDs ──────────────────────────────────────────────────────────────────
CAN_ID_TX_STEER = 0x110
CAN_ID_TX_DRIVE = 0x120
CAN_ID_RX_HB    = 0x320

# ── Vehicle limits ────────────────────────────────────────────────────────────
SPEED_MAX_MMS  = 500    # ±500 mm/s
STEER_MAX_MRAD = 2500   # ±2500 mrad

# ── TX rate ───────────────────────────────────────────────────────────────────
TX_RATE_HZ = 20

# ── Heartbeat watchdog ────────────────────────────────────────────────────────
HB_WATCHDOG_S = 0.500   # 500 ms — fixed per spec, not a ROS parameter

# ── Mode bytes ────────────────────────────────────────────────────────────────
MODE_IDLE  = 0
MODE_AUTO  = 1
MODE_ESTOP = 2


def _clamp(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


# ─────────────────────────────────────────────────────────────────────────────
class CanBridgeNode(Node):
    """Bridges /vehicle/cmd_vel_safe ↔ combined_ecu Arduino over CAN (socketcan)."""

    def __init__(self) -> None:
        super().__init__('can_bridge_node')

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter('channel',      'can0')
        self.declare_parameter('bitrate',      500_000)
        self.declare_parameter('watchdog_sec', 10.0)    # cmd_vel silence timeout
        self.declare_parameter('dry_run',      False)

        self._channel      = self.get_parameter('channel').value
        self._bitrate      = self.get_parameter('bitrate').value
        self._watchdog_sec = self.get_parameter('watchdog_sec').value
        self._dry_run      = self.get_parameter('dry_run').value

        # ── Shared command state ──────────────────────────────────────────────
        self._lock           = threading.Lock()
        self._speed_mms      : int   = 0
        self._steer_mrad     : int   = 0
        self._brake_pct      : int   = 0
        self._tbw_mode       : int   = MODE_IDLE
        # Initialise both timestamps to NOW so watchdogs don't fire at startup
        self._last_cmd_time  : float = time.monotonic()
        self._last_hb_time   : float = time.monotonic()
        self._hb_wd_ok       : bool  = True

        # ── QoS ───────────────────────────────────────────────────────────────
        _be = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1)
        _rel = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10)

        # ── Subscriber ────────────────────────────────────────────────────────
        self.create_subscription(
            Twist, '/vehicle/cmd_vel_safe', self._cmd_vel_cb, _be)

        # ── Publishers ────────────────────────────────────────────────────────
        self._rpm_pub = self.create_publisher(String, '/vehicle/rpm',   _rel)
        self._hb_pub  = self.create_publisher(String, '/can/heartbeat', _rel)

        # ── CAN bus ───────────────────────────────────────────────────────────
        self._bus = None
        self._init_can()

        # ── Background RX thread ──────────────────────────────────────────────
        self._rx_stop   = threading.Event()
        self._rx_thread = threading.Thread(
            target=self._rx_loop, name='can_rx', daemon=True)
        self._rx_thread.start()

        # ── TX timer at 20 Hz ─────────────────────────────────────────────────
        self._tx_timer = self.create_timer(1.0 / TX_RATE_HZ, self._tx_cb)

        self.get_logger().info(
            f'CanBridgeNode ready — channel={self._channel} '
            f'bitrate={self._bitrate} dry_run={self._dry_run} '
            f'cmd_vel_wd={self._watchdog_sec}s '
            f'hb_wd={HB_WATCHDOG_S}s')

    # ─────────────────────────────────────────────────────────────────────────
    # CAN initialisation
    # ─────────────────────────────────────────────────────────────────────────
    def _init_can(self) -> None:
        try:
            import can
            # python-can 4+: use interface= (bustype= is deprecated)
            self._bus = can.Bus(
                channel=self._channel,
                interface='socketcan')
            self.get_logger().info(
                f'CAN bus opened: {self._channel} (socketcan)')
        except Exception as exc:
            msg = f'CAN bus unavailable ({exc})'
            if self._dry_run:
                self.get_logger().warning(f'{msg} — dry-run mode active')
            else:
                self.get_logger().error(
                    f'{msg} — set dry_run:=true to suppress. '
                    'Continuing without hardware.')
            self._bus = None

    # ─────────────────────────────────────────────────────────────────────────
    # ROS callback
    # ─────────────────────────────────────────────────────────────────────────
    def _cmd_vel_cb(self, msg: Twist) -> None:
        speed_mms  = _clamp(int(msg.linear.x  * 1000.0),
                            -SPEED_MAX_MMS,  SPEED_MAX_MMS)
        steer_mrad = _clamp(int(msg.angular.z * 1000.0),
                            -STEER_MAX_MRAD, STEER_MAX_MRAD)
        with self._lock:
            self._speed_mms     = speed_mms
            self._steer_mrad    = steer_mrad
            self._tbw_mode      = MODE_AUTO
            self._last_cmd_time = time.monotonic()

    # ─────────────────────────────────────────────────────────────────────────
    # 20 Hz TX timer  (watchdog checks + CAN TX)
    # ─────────────────────────────────────────────────────────────────────────
    def _tx_cb(self) -> None:
        now = time.monotonic()

        with self._lock:
            cmd_age = now - self._last_cmd_time
            hb_age  = now - self._last_hb_time

            # ── cmd_vel watchdog → IDLE ───────────────────────────────────────
            if cmd_age > self._watchdog_sec:
                if self._tbw_mode != MODE_IDLE:
                    self.get_logger().warning(
                        f'cmd_vel silent {cmd_age:.2f} s → MODE_IDLE')
                self._speed_mms  = 0
                self._steer_mrad = 0
                self._brake_pct  = 0
                self._tbw_mode   = MODE_IDLE

            # ── heartbeat watchdog → ESTOP ────────────────────────────────────
            hb_ok = hb_age < HB_WATCHDOG_S
            if not hb_ok and self._hb_wd_ok:
                # Transition from OK → FAIL
                self.get_logger().error(
                    f'0x320 heartbeat silent {hb_age * 1000:.0f} ms → ESTOP')
            self._hb_wd_ok = hb_ok
            if not hb_ok:
                self._tbw_mode = MODE_ESTOP

            speed_mms  = self._speed_mms
            steer_mrad = self._steer_mrad
            brake_pct  = self._brake_pct
            tbw_mode   = self._tbw_mode

        self._send_steer(steer_mrad)
        self._send_drive(speed_mms, brake_pct, tbw_mode)

    # ─────────────────────────────────────────────────────────────────────────
    # CAN TX helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _send_steer(self, steer_mrad: int) -> None:
        """TX 0x110 — steer command: int16 BE, 2 bytes."""
        self._can_send(CAN_ID_TX_STEER, struct.pack('>h', steer_mrad))

    def _send_drive(self, speed_mms: int, brake_pct: int, mode: int) -> None:
        """TX 0x120 — drive command: int16 speed, uint8 brake, uint8 mode."""
        self._can_send(CAN_ID_TX_DRIVE,
                       struct.pack('>hBB',
                                   speed_mms, brake_pct & 0xFF, mode & 0xFF))

    def _can_send(self, can_id: int, data: bytes) -> None:
        if self._bus is not None:
            try:
                import can
                self._bus.send(can.Message(
                    arbitration_id=can_id,
                    data=data,
                    is_extended_id=False))
            except Exception as exc:
                self.get_logger().error(f'CAN TX 0x{can_id:03X}: {exc}')
        else:
            self.get_logger().debug(
                f'[DRY-RUN] TX 0x{can_id:03X} {data.hex()}')

    # ─────────────────────────────────────────────────────────────────────────
    # CAN RX thread
    # ─────────────────────────────────────────────────────────────────────────
    def _rx_loop(self) -> None:
        if self._bus is None:
            self.get_logger().info('[DRY-RUN] RX thread idle — no hardware')
            return
        while not self._rx_stop.is_set():
            try:
                msg = self._bus.recv(timeout=0.1)
                if msg is None:
                    continue
                self._dispatch_rx(msg)
            except Exception as exc:
                if not self._rx_stop.is_set():
                    self.get_logger().error(f'CAN RX: {exc}')

    def _dispatch_rx(self, msg) -> None:
        cid = msg.arbitration_id
        d   = bytes(msg.data)
        try:
            if cid == CAN_ID_RX_HB:
                self._handle_heartbeat(d)
            # All other IDs silently ignored (no encoder / SBW-FB frames expected)
        except Exception as exc:
            self.get_logger().error(f'RX dispatch 0x{cid:03X}: {exc}')

    # ── RX handler ────────────────────────────────────────────────────────────
    def _handle_heartbeat(self, d: bytes) -> None:
        """
        0x320 — status uint8 (byte 0) + heartbeat counter uint8 (byte 1).
        Updates HB watchdog timestamp and publishes to /vehicle/rpm and
        /can/heartbeat so integrated_safety_node can monitor CAN liveness.
        """
        if len(d) < 2:
            return

        status, counter = d[0], d[1]

        with self._lock:
            prev_ok          = self._hb_wd_ok
            self._last_hb_time = time.monotonic()
            self._hb_wd_ok   = True

        if not prev_ok:
            self.get_logger().info(
                f'0x320 heartbeat restored (status={status} cnt={counter})')

        payload = f'{status},{counter}'
        self._rpm_pub.publish(String(data=payload))
        self._hb_pub.publish(String(data=payload))

    # ─────────────────────────────────────────────────────────────────────────
    # ESTOP burst  (clean shutdown)
    # ─────────────────────────────────────────────────────────────────────────
    def _send_estop_burst(self) -> None:
        """Send ESTOP three times with 20 ms gaps to ensure delivery."""
        for _ in range(3):
            self._send_steer(0)
            self._send_drive(0, 0, MODE_ESTOP)
            time.sleep(0.02)

    # ─────────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────────
    def destroy_node(self) -> None:
        self.get_logger().info('CanBridgeNode shutting down — sending ESTOP…')

        if hasattr(self, '_tx_timer'):
            self._tx_timer.cancel()

        self._send_estop_burst()

        self._rx_stop.set()
        if hasattr(self, '_rx_thread'):
            self._rx_thread.join(timeout=1.0)

        if self._bus is not None:
            try:
                self._bus.shutdown()
                self.get_logger().info('CAN bus closed')
            except Exception as exc:
                self.get_logger().error(f'CAN shutdown: {exc}')

        super().destroy_node()


# ─────────────────────────────────────────────────────────────────────────────
def main(args=None) -> None:
    # Pin to CPU core 2 for deterministic CAN timing (Pi 5 has cores 0-3)
    try:
        os.sched_setaffinity(0, {2})
    except (AttributeError, OSError) as exc:
        print(f'[WARN] CPU affinity unavailable: {exc}')

    rclpy.init(args=args)
    node = CanBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
