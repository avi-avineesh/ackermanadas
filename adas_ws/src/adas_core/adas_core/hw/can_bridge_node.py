#!/usr/bin/env python3
"""
can_bridge_node.py — Dual-ECU CAN Bus Bridge
═════════════════════════════════════════════
Package: adas_core.hw | Phase 2 (STUB in Phase 1) | Pi core 2

ARCHITECTURE — 3-node CAN bus, one shared twisted pair:

  Raspberry Pi 5 (domain controller)
      │
      └── Waveshare RS485 CAN HAT (SPI)
              │
              CAN_H / CAN_L twisted pair · 500 kbps
              │
              ├── Arduino Uno R3 #1 — SBW ECU (Steer-By-Wire)
              │       MCP2515 (SPI 10-13, INT 2)
              │       Controls: MG995 servo on D9 PWM
              │       Receives: 0x110 (steer command)
              │       Sends:    0x310 (actual angle + status)
              │       Watchdog: no 0x110 in 500ms → servo to 1500µs (centre)
              │
              └── Arduino Uno R3 #2 — TBW ECU (Throttle-By-Wire)
                      MCP2515 (SPI 10-13, INT 2)
                      Controls: SmartElex D4/D5/D6/D7 (throttle + brake)
                      Reads:    OE-37 encoders A0/A1/A2/A3 (interrupt-driven)
                      Receives: 0x120 (speed + brake command)
                      Sends:    0x220 (encoder ticks), 0x320 (rpm + status)
                      Watchdog: no 0x120 in 500ms → zero PWM both motors

  120Ω termination at Pi HAT end and TBW end only.

CAN MESSAGE PROTOCOL:

  0x110  Pi→SBW    bytes 0-1: int16 steer_angle_mrad
                     signed, ±600 mrad limit, 0 = straight ahead
                     map to servo: us = 1500 + (mrad * 0.286)
                     clamped: [1000, 2000] µs

  0x310  SBW→Pi    byte  0-1: int16 actual_angle_mrad (echo back)
                     byte  2:   uint8 status (0=ok 1=watchdog 2=fault)

  0x120  Pi→TBW    bytes 0-1: int16 speed_mm_s (signed, +fwd/-rev)
                     byte  2:   uint8 brake_pct (0–100 proportional)
                     speed → PWM: abs(speed_mm_s)/MAX_SPEED_MM_S * 255
                     direction → D4/D7 HIGH=fwd LOW=rev
                     brake → pwm *= (1.0 - brake_pct/100.0)

  0x220  TBW→Pi    bytes 0-3: int32 enc_L_ticks (cumulative, signed)
                     bytes 4-7: int32 enc_R_ticks
                     → compute odometry → publish /ego/odom

  0x320  TBW→Pi    bytes 0-1: int16 rpm_L
                     bytes 2-3: int16 rpm_R
                     byte  4:   uint8 status (0=ok 1=watchdog 2=fault)

can_bridge_node RESPONSIBILITIES (Phase 2 implementation):
  Subscribe /safety/cmd_vel (geometry_msgs/Twist):
    linear.x  → speed_mm_s = int(linear.x * 1000)
    angular.z → steer_mrad = int(angular.z * (WHEELBASE/2) * 1000)
                WHEELBASE = 0.3005m
  Send 0x110 to SBW at 20Hz
  Send 0x120 to TBW at 20Hz
  Receive 0x220 → compute odom → publish /ego/odom at 50Hz
  Receive 0x310, 0x320 → publish /can/sbw_status, /can/tbw_status
  python-can: Bus('can0', bustype='socketcan', bitrate=500000)
  Pi CAN setup:
    sudo ip link set can0 up type can bitrate 500000
    sudo ip link set can0 txqueuelen 1000

PHASE 1 STATUS: STUB — subscribes /safety/cmd_vel, does nothing.
  In simulation: Gazebo AckermannSteering plugin handles cmd_vel directly.
  In hardware: full implementation above replaces simulation plugin.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class CanBridgeNode(Node):
    """Phase 1 stub. Phase 2: dual-ECU SBW (0x110/0x310) + TBW (0x120/0x220/0x320)."""

    def __init__(self):
        super().__init__('can_bridge_node')
        self.create_subscription(Twist, '/safety/cmd_vel', self._cmd_cb, 10)
        self.get_logger().info(
            '[CAN] STUB Phase 2 — subscribed to /safety/cmd_vel.\n'
            '  In sim: Gazebo handles cmd_vel. On hardware: two-ECU CAN bridge activates.\n'
            '  SBW ECU (0x110/0x310): steering.  TBW ECU (0x120/0x220/0x320): throttle+odom.'
        )

    def _cmd_cb(self, msg: Twist):
        """Log received command (not forwarded to CAN in Phase 1)."""
        self.get_logger().debug(
            f'[CAN] cmd_vel linear.x={msg.linear.x:.3f} angular.z={msg.angular.z:.3f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = CanBridgeNode()
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
