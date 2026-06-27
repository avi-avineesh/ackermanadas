"""
mode_manager.py — ADAS Mode Manager
Routes velocity commands based on the active operating mode.

Modes
-----
  MANUAL  — passes /adas/manual_cmd through to /vehicle/cmd_vel_input
  AUTO    — ADAS nodes drive via arbiter; manual_cmd forwarded as base
  ESTOP   — zeroes /vehicle/cmd_vel_input; latches until RESET received

Subscribes
----------
  /adas/mode_cmd     (std_msgs/String)   : MANUAL / AUTO / ESTOP / RESET
  /adas/manual_cmd   (geometry_msgs/Twist): keyboard / joystick command
  /vehicle/params    (adas_core/VehicleParams): forwarded to downstream nodes

Publishes
---------
  /adas/mode              (std_msgs/String)     : current mode at 10 Hz
  /vehicle/cmd_vel_input  (geometry_msgs/Twist) : routed command at 20 Hz
  /safety/reset           (std_msgs/Empty)      : pulse on RESET transition
"""

from __future__ import annotations

import threading
import time
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

from geometry_msgs.msg import Twist
from std_msgs.msg import String, Empty

# VehicleParams is a custom message — import with graceful fallback so the
# file can be linted without the workspace built.
try:
    from adas_msgs.msg import VehicleParams
    _HAVE_VEHICLE_PARAMS = True
except ImportError:
    _HAVE_VEHICLE_PARAMS = False

# ---------------------------------------------------------------------------
# Mode constants
# ---------------------------------------------------------------------------
MODE_MANUAL = 'MANUAL'
MODE_AUTO   = 'AUTO'
MODE_ESTOP  = 'ESTOP'

CMD_MANUAL = 'MANUAL'
CMD_AUTO   = 'AUTO'
CMD_ESTOP  = 'ESTOP'
CMD_RESET  = 'RESET'

VALID_MODES = {MODE_MANUAL, MODE_AUTO, MODE_ESTOP}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _zero_twist() -> Twist:
    """Return a Twist message with all fields set to zero."""
    return Twist()


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class ModeManagerNode(Node):
    """ADAS mode manager: routes commands based on operating mode."""

    def __init__(self) -> None:
        super().__init__('mode_manager')

        # ── Parameters ──────────────────────────────────────────────────────
        self.declare_parameter('default_mode', MODE_MANUAL)
        self.declare_parameter('watchdog_sec',  0.5)

        default_mode_param = self.get_parameter('default_mode').value.upper()
        if default_mode_param not in VALID_MODES:
            self.get_logger().warning(
                f'Invalid default_mode "{default_mode_param}", falling back to MANUAL.'
            )
            default_mode_param = MODE_MANUAL

        self._watchdog_sec: float = self.get_parameter('watchdog_sec').value

        # ── Shared state (protected by _lock) ───────────────────────────────
        self._lock                = threading.Lock()
        self._mode: str           = default_mode_param
        self._manual_cmd: Twist   = _zero_twist()
        self._last_manual_time: float = 0.0   # monotonic

        # ── QoS profiles ────────────────────────────────────────────────────
        reliable_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )
        best_effort_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        latching_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        # ── Subscribers ──────────────────────────────────────────────────────
        self._mode_cmd_sub = self.create_subscription(
            String,
            '/adas/mode_cmd',
            self._mode_cmd_cb,
            reliable_qos,
        )
        self._manual_cmd_sub = self.create_subscription(
            Twist,
            '/adas/manual_cmd',
            self._manual_cmd_cb,
            best_effort_qos,
        )

        if _HAVE_VEHICLE_PARAMS:
            self._params_sub = self.create_subscription(
                VehicleParams,
                '/vehicle/params',
                self._params_cb,
                reliable_qos,
            )
            self._params_pub = self.create_publisher(
                VehicleParams,
                '/vehicle/params',
                reliable_qos,
            )
        else:
            self.get_logger().warning(
                'adas_msgs.msg.VehicleParams not found — /vehicle/params forwarding disabled.'
            )

        # ── Publishers ───────────────────────────────────────────────────────
        self._mode_pub = self.create_publisher(
            String,
            '/adas/mode',
            latching_qos,
        )
        self._cmd_vel_pub = self.create_publisher(
            Twist,
            '/vehicle/cmd_vel_input',
            best_effort_qos,
        )
        self._safety_reset_pub = self.create_publisher(
            Empty,
            '/safety/reset',
            reliable_qos,
        )

        # ── Timers ───────────────────────────────────────────────────────────
        self._mode_timer = self.create_timer(
            1.0 / 10.0,      # 10 Hz
            self._mode_pub_timer_cb,
        )
        self._cmd_timer = self.create_timer(
            1.0 / 20.0,      # 20 Hz
            self._cmd_timer_cb,
        )

        self.get_logger().info(
            f'ModeManagerNode started — default mode: {self._mode}'
        )

    # ────────────────────────────────────────────────────────────────────────
    # Subscriber callbacks
    # ────────────────────────────────────────────────────────────────────────

    def _mode_cmd_cb(self, msg: String) -> None:
        """Handle a mode command request."""
        cmd = msg.data.strip().upper()

        with self._lock:
            current = self._mode

            if cmd == CMD_ESTOP:
                # Always accept ESTOP regardless of current mode
                self._mode = MODE_ESTOP
                self.get_logger().warning('ESTOP received — latching ESTOP mode.')

            elif cmd == CMD_RESET:
                if current == MODE_ESTOP:
                    self._mode = MODE_MANUAL
                    do_safety_reset = True
                    self.get_logger().info('RESET received — returning to MANUAL.')
                else:
                    do_safety_reset = False
                    self.get_logger().info(
                        f'RESET received but mode is {current} (not ESTOP) — ignored.'
                    )
                # Publish safety reset outside the lock
                if do_safety_reset:
                    # We must release the lock before publishing to avoid
                    # potential deadlock with ROS callbacks.
                    pass   # handled after with-block
            elif cmd == CMD_MANUAL:
                if current == MODE_ESTOP:
                    self.get_logger().warning(
                        'Mode transition to MANUAL blocked — ESTOP is latched. Send RESET first.'
                    )
                else:
                    self._mode = MODE_MANUAL
                    self.get_logger().info('Mode → MANUAL')

            elif cmd == CMD_AUTO:
                if current == MODE_ESTOP:
                    self.get_logger().warning(
                        'Mode transition to AUTO blocked — ESTOP is latched. Send RESET first.'
                    )
                else:
                    self._mode = MODE_AUTO
                    self.get_logger().info('Mode → AUTO')

            else:
                self.get_logger().warning(f'Unknown mode_cmd: "{cmd}" — ignored.')
                return

        # Publish safety/reset pulse outside the lock
        if cmd == CMD_RESET and current == MODE_ESTOP:
            self._safety_reset_pub.publish(Empty())

    def _manual_cmd_cb(self, msg: Twist) -> None:
        """Cache the latest manual command and update watchdog timestamp."""
        with self._lock:
            self._manual_cmd       = msg
            self._last_manual_time = time.monotonic()

    def _params_cb(self, msg) -> None:
        """Forward VehicleParams to any downstream subscriber."""
        if _HAVE_VEHICLE_PARAMS:
            self._params_pub.publish(msg)

    # ────────────────────────────────────────────────────────────────────────
    # Timer callbacks
    # ────────────────────────────────────────────────────────────────────────

    def _mode_pub_timer_cb(self) -> None:
        """10 Hz — publish current mode string."""
        with self._lock:
            mode = self._mode
        out = String()
        out.data = mode
        self._mode_pub.publish(out)

    def _cmd_timer_cb(self) -> None:
        """20 Hz — compute and publish routed velocity command."""
        with self._lock:
            mode     = self._mode
            manual   = self._manual_cmd
            age      = time.monotonic() - self._last_manual_time
            watchdog_expired = age > self._watchdog_sec

        if mode == MODE_ESTOP:
            # Hard zero — do not move
            self._cmd_vel_pub.publish(_zero_twist())
            return

        if mode == MODE_MANUAL:
            if watchdog_expired:
                # No recent manual input — safety zero
                self._cmd_vel_pub.publish(_zero_twist())
            else:
                self._cmd_vel_pub.publish(manual)
            return

        if mode == MODE_AUTO:
            # In AUTO mode the arbiter (separate node) generates the
            # final safe command on /vehicle/cmd_vel_safe.  We forward
            # manual_cmd here as the base layer so the arbiter has a
            # fallback; ADAS-specific nodes override via priority stack.
            if watchdog_expired:
                self._cmd_vel_pub.publish(_zero_twist())
            else:
                self._cmd_vel_pub.publish(manual)
            return

        # Fallback (should never reach)
        self._cmd_vel_pub.publish(_zero_twist())

    # ────────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ────────────────────────────────────────────────────────────────────────

    def destroy_node(self) -> None:
        """Clean shutdown: cancel timers, publish zero before exit."""
        self.get_logger().info('ModeManagerNode shutting down…')

        if hasattr(self, '_mode_timer'):
            self._mode_timer.cancel()
        if hasattr(self, '_cmd_timer'):
            self._cmd_timer.cancel()

        # Publish a final zero command and ESTOP mode
        try:
            self._cmd_vel_pub.publish(_zero_twist())
            mode_msg = String()
            mode_msg.data = MODE_ESTOP
            self._mode_pub.publish(mode_msg)
        except Exception:  # noqa: BLE001
            pass

        super().destroy_node()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(args=None) -> None:
    rclpy.init(args=args)
    node = ModeManagerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
