#!/usr/bin/env python3
"""
ekf_node.py — Localization Layer: Extended Kalman Filter (STUB)
═══════════════════════════════════════════════════════════════
Package: adas_core.localization | Phase 2 (STUB in Phase 1) | Pi core 3

FULL IMPLEMENTATION (Phase 2):
  OE-37 encoders (via TBW ECU CAN 0x220) + MPU6050 IMU →
  5-state Kalman [x, y, θ, v, ω] bicycle kinematic model.
  Pi core 3. Corrects encoder drift with IMU heading.

STATE VECTOR: [x, y, θ, v, ω]
  x, y  : 2D position in odom frame (m)
  θ     : heading angle (rad, CCW from X-axis)
  v     : forward velocity (m/s)
  ω     : yaw rate (rad/s)

PROCESS MODEL (bicycle kinematics, timestep dt):
  x_k+1 = x_k + v*cos(θ)*dt
  y_k+1 = y_k + v*sin(θ)*dt
  θ_k+1 = θ_k + (v/L)*tan(δ)*dt     (L=0.3005m, δ=steering angle from 0x310)
  v_k+1 = v_k + a_x*dt               (a_x from MPU6050 accelerometer)
  ω_k+1 = ω_k                        (random walk)

OBSERVATION MODELS:
  Encoder obs (from 0x220):   z = [v_enc]     H = [0,0,0,1,0]
  IMU gyro   (from MPU6050):  z = [ω_gyro]    H = [0,0,0,0,1]

WHY EKF:
  Encoders alone drift ~5-10cm per 10m travel at 500 ticks/rev, 0.047m radius.
  IMU alone has gyroscope bias. Fusing both via EKF gives <2cm error on
  the 10m AEB track. Phase 2 ACC and Phase 3 LKA need this accuracy.

TOPICS:
  Subscribes: /ego/odom    nav_msgs/Odometry
  Publishes:  /ego/pose    geometry_msgs/PoseStamped
              /ego/velocity geometry_msgs/TwistStamped
"""

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped, TwistStamped


class EkfNode(Node):
    """Phase 1 stub: odom passthrough. Phase 2: full EKF encoder+IMU fusion."""

    def __init__(self):
        super().__init__('ekf_node')
        self._latest = None
        self._pub_pose = self.create_publisher(PoseStamped,  '/ego/pose',     10)
        self._pub_vel  = self.create_publisher(TwistStamped, '/ego/velocity', 10)
        self.create_subscription(Odometry, '/ego/odom', self._odom_cb, 10)
        self.create_timer(0.1, self._tick)  # 10Hz
        self.get_logger().info(
            '[EKF] STUB Phase 2. Full: OE-37 encoders (via TBW ECU CAN 0x220) + '
            'MPU6050 IMU → 5-state Kalman [x,y,θ,v,ω] bicycle kinematic model. '
            'Pi core 3. Corrects encoder drift with IMU heading.'
        )

    def _odom_cb(self, msg: Odometry):
        """Cache latest odometry."""
        self._latest = msg

    def _tick(self):
        """Republish odom as PoseStamped + TwistStamped at 10Hz."""
        if self._latest is None:
            return
        pm = PoseStamped()
        pm.header = self._latest.header
        pm.pose   = self._latest.pose.pose
        self._pub_pose.publish(pm)

        tm = TwistStamped()
        tm.header = self._latest.header
        tm.twist  = self._latest.twist.twist
        self._pub_vel.publish(tm)


def main(args=None):
    rclpy.init(args=args)
    node = EkfNode()
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
