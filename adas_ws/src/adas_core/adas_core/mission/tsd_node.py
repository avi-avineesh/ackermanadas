#!/usr/bin/env python3
"""
tsd_node.py — Mission Layer: Traffic Sign Detection (STUB)
═══════════════════════════════════════════════════════════
Package: adas_core.mission | Phase 4 (STUB in Phase 1) | Pi core 2

FULL IMPLEMENTATION (Phase 4):
  Input: /ego/detections (YOLO11n bounding boxes — any sign-class detection)
  Step 1: Crop detected bounding box region from /ego/camera/image_raw.
  Step 2: Convert crop to HSV.
  Step 3: Classify sign by dominant hue:
    Red   (H=0-10 or H=160-180, S>120, V>80):  STOP / speed restriction
    Yellow (H=20-35, S>120, V>100):             YIELD / caution
    Green  (H=40-80, S>80, V>80):               GO / clear
  Step 4: Publish /tsd/status and velocity modifier to /mission/cmd_vel.
    STOP sign: Twist(0,0) for 3.0s then resume
    YIELD: reduce to 50% speed for 2.0s
    GO: resume normal speed

TOPICS:
  Subscribes: /ego/detections
  Publishes:  /tsd/status  /mission/cmd_vel
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String


class TsdNode(Node):
    """Phase 1 stub. Phase 4: YOLO11n bbox crop → HSV classification → stop/go."""

    def __init__(self):
        super().__init__('tsd_node')
        self._pub_cmd    = self.create_publisher(Twist,  '/mission/cmd_vel', 10)
        self._pub_status = self.create_publisher(String, '/tsd/status',      10)
        self.create_timer(0.1, self._tick)
        self.get_logger().info(
            '[TSD] STUB Phase 4. Full: YOLO11n bbox crop → HSV red/yellow/green '
            'classification → stop/go command via /mission/cmd_vel.'
        )

    def _tick(self):
        """Publish zero command and stub status."""
        self._pub_cmd.publish(Twist())
        s = String(); s.data = 'STUB'
        self._pub_status.publish(s)


def main(args=None):
    rclpy.init(args=args)
    node = TsdNode()
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
