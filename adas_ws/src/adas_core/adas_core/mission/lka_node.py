#!/usr/bin/env python3
"""
lka_node.py — Mission Layer: Lane Keep Assist (STUB)
═════════════════════════════════════════════════════
Package: adas_core.mission | Phase 3 (STUB in Phase 1) | Pi core 2

FULL IMPLEMENTATION (Phase 3):
  Algorithm: HSV S<50 AND V>μ+1.5σ (colour-agnostic white isolation)
             → IPM bird's-eye warp → np.polyfit 2nd-degree → PID

  WHY HSV OVER GRAYSCALE:
    Grayscale adaptive threshold depends on absolute intensity — fails on
    beige/yellow road surfaces where white lane lines have low contrast.
    HSV S-channel (saturation) is surface-colour-agnostic: white lane lines
    have S≈0 regardless of road colour. V>μ+1.5σ (per-frame adaptive
    brightness) handles shadows and lighting variation.

  LANE DETECTION STEPS:
    1. BGR→HSV: mask = (S < 50) AND (V > frame_mean_V * 0.7)
    2. IPM: getPerspectiveTransform(src_trapezoid, dst_rectangle)
       warpPerspective → bird's-eye view (parallel lane lines)
    3. Find nonzero pixels in left half (x<320) and right half (x>=320)
    4. polyfit degree=2 on each half: lane_poly_L, lane_poly_R
    5. Evaluate at y=480 (bottom): lane_cx = (L_cx + R_cx) / 2
    6. lateral_error = lane_cx - 320   (pixels; positive=drift right)
    7. PID → angular.z command

  PID PARAMETERS (proven on 0.54m wide track):
    KP=0.010  KI=0.0001  KD=0.005  MAX_STEER=1.2 rad/s
    Anti-windup: integral clamped ±5.0

TOPICS:
  Subscribes: /ego/camera/image_raw
  Publishes:  /mission/cmd_vel  /lka/status
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

KP = 0.010; KI = 0.0001; KD = 0.005; MAX_STEER = 1.2  # rad/s


class LkaNode(Node):
    """Phase 1 stub. Phase 3: HSV→IPM→polyfit→PID lane keep."""

    def __init__(self):
        super().__init__('lka_node')
        self._pub_cmd    = self.create_publisher(Twist,  '/mission/cmd_vel', 10)
        self._pub_status = self.create_publisher(String, '/lka/status',      10)
        self.create_timer(0.1, self._tick)  # 10Hz
        self.get_logger().info(
            '[LKA] STUB Phase 3. Full: HSV S<50 AND V>μ+1.5σ (colour-agnostic white '
            'isolation) → IPM bird\'s-eye warp → np.polyfit 2nd-degree → PID '
            f'KP={KP} KI={KI} KD={KD} MAX_STEER={MAX_STEER} rad/s.'
        )

    def _tick(self):
        """Publish zero command and stub status."""
        self._pub_cmd.publish(Twist())
        s = String(); s.data = 'STUB'
        self._pub_status.publish(s)


def main(args=None):
    rclpy.init(args=args)
    node = LkaNode()
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
