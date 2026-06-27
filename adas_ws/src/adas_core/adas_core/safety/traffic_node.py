"""
traffic_node.py — Stub: traffic light detection removed.

Publishes a constant UNKNOWN state so downstream subscribers
(safety_arbiter, dashboard) receive valid messages on startup.
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

from std_msgs.msg import String
from geometry_msgs.msg import Twist

NO_LIMIT_SENTINEL = 999.0
PUBLISH_HZ = 10.0


class TrafficNode(Node):
    def __init__(self):
        super().__init__('traffic_node')

        rel_qos = QoSProfile(depth=10)

        self._pub_cmd    = self.create_publisher(Twist,  '/safety/traffic_cmd',    rel_qos)
        self._pub_status = self.create_publisher(String, '/safety/traffic_status', rel_qos)
        self._pub_light  = self.create_publisher(String, '/safety/traffic_light',  rel_qos)

        self.create_timer(1.0 / PUBLISH_HZ, self._timer_cb)
        self.get_logger().info('Traffic node stub started — publishing UNKNOWN.')

    def _timer_cb(self):
        cmd = Twist()
        cmd.linear.x  = NO_LIMIT_SENTINEL
        cmd.angular.z = 0.0
        self._pub_cmd.publish(cmd)

        status = String()
        status.data = 'UNKNOWN'
        self._pub_status.publish(status)

        light = String()
        light.data = 'UNKNOWN'
        self._pub_light.publish(light)


def main(args=None):
    rclpy.init(args=args)
    node = TrafficNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
