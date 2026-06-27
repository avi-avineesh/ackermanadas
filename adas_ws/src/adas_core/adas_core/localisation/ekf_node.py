"""
ekf_node.py — 5-state Extended Kalman Filter fusing wheel encoder odometry with IMU.

State vector: x = [x_pos, y_pos, theta, v, omega]
"""

import os
import threading
import time
from math import cos, sin, pi

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32
from geometry_msgs.msg import Quaternion


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WHEEL_CIRC      = 2.0 * pi * 0.047          # 0.29531 m
TICKS_PER_REV   = 16
DIST_PER_TICK   = WHEEL_CIRC / TICKS_PER_REV  # 0.01846 m/tick
TRACK_WIDTH     = 0.285                       # m

PUBLISH_HZ      = 50.0

# Default noise values
DEFAULT_Q = {
    'q_x':     1e-4,
    'q_y':     1e-4,
    'q_theta': 2.5e-5,
    'q_v':     1e-2,
    'q_omega': 2.5e-3,
}
DEFAULT_R_ENC_V  = 2.5e-3
DEFAULT_R_ENC_W  = 2.5e-3
DEFAULT_R_IMU_W  = 4e-4


class EKFNode(Node):
    """5-state EKF node fusing wheel odometry and IMU."""

    def __init__(self):
        super().__init__('ekf_node')

        # ── Parameters ──────────────────────────────────────────────────────
        self.declare_parameter('q_x',     DEFAULT_Q['q_x'])
        self.declare_parameter('q_y',     DEFAULT_Q['q_y'])
        self.declare_parameter('q_theta', DEFAULT_Q['q_theta'])
        self.declare_parameter('q_v',     DEFAULT_Q['q_v'])
        self.declare_parameter('q_omega', DEFAULT_Q['q_omega'])
        self.declare_parameter('r_enc_v', DEFAULT_R_ENC_V)
        self.declare_parameter('r_enc_w', DEFAULT_R_ENC_W)
        self.declare_parameter('r_imu_w', DEFAULT_R_IMU_W)

        q_x     = self.get_parameter('q_x').value
        q_y     = self.get_parameter('q_y').value
        q_theta = self.get_parameter('q_theta').value
        q_v     = self.get_parameter('q_v').value
        q_omega = self.get_parameter('q_omega').value

        self._r_enc_v = self.get_parameter('r_enc_v').value
        self._r_enc_w = self.get_parameter('r_enc_w').value
        self._r_imu_w = self.get_parameter('r_imu_w').value

        # ── EKF state ────────────────────────────────────────────────────────
        self._lock = threading.Lock()

        self._x = np.zeros(5)                                      # [x,y,theta,v,omega]
        self._P = np.diag([1.0, 1.0, 0.1, 0.5, 0.5])
        self._Q = np.diag([q_x, q_y, q_theta, q_v, q_omega])

        # ── Bookkeeping ──────────────────────────────────────────────────────
        self._prev_enc_l: int   = 0
        self._prev_enc_r: int   = 0
        self._prev_odom_t: float = time.monotonic()
        self._prev_imu_t: float  = time.monotonic()
        self._odom_initialised: bool = False

        self._omega_enc: float   = 0.0    # stored from latest odom callback
        self._omega_drift: float = 0.0    # omega_enc - omega_imu

        # ── QoS profiles ─────────────────────────────────────────────────────
        best_effort_qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        reliable_qos = QoSProfile(depth=10)

        # ── Subscriptions ────────────────────────────────────────────────────
        self.create_subscription(
            Odometry, '/vehicle/odom', self._odom_callback, best_effort_qos
        )
        self.create_subscription(
            Imu, '/sensor/imu', self._imu_callback, best_effort_qos
        )

        # ── Publishers ───────────────────────────────────────────────────────
        self._pub_pose  = self.create_publisher(Odometry, '/vehicle/pose', reliable_qos)
        self._pub_drift = self.create_publisher(Float32, '/vehicle/drift_correction', reliable_qos)

        # ── Publish timer ────────────────────────────────────────────────────
        self.create_timer(1.0 / PUBLISH_HZ, self._publish_callback)

        self.get_logger().info('EKF node started.')

    # ────────────────────────────────────────────────────────────────────────
    # Helper: EKF update step (generic)
    # ────────────────────────────────────────────────────────────────────────
    def _ekf_update(self, x: np.ndarray, P: np.ndarray,
                    z: np.ndarray, H: np.ndarray, R: np.ndarray):
        """Standard EKF measurement update. Returns updated (x, P)."""
        S = H @ P @ H.T + R
        K = P @ H.T @ np.linalg.inv(S)
        innovation = z - H @ x
        x_new = x + K @ innovation
        I = np.eye(len(x))
        P_new = (I - K @ H) @ P
        return x_new, P_new

    # ────────────────────────────────────────────────────────────────────────
    # Wheel odometry callback
    # ────────────────────────────────────────────────────────────────────────
    def _odom_callback(self, msg: Odometry):
        enc_l = int(msg.pose.pose.position.x)
        enc_r = int(msg.pose.pose.position.y)

        now = time.monotonic()

        with self._lock:
            if not self._odom_initialised:
                self._prev_enc_l = enc_l
                self._prev_enc_r = enc_r
                self._prev_odom_t = now
                self._odom_initialised = True
                return

            dt = now - self._prev_odom_t
            if dt <= 0.0:
                return

            d_enc_l = enc_l - self._prev_enc_l
            d_enc_r = enc_r - self._prev_enc_r

            self._prev_enc_l = enc_l
            self._prev_enc_r = enc_r
            self._prev_odom_t = now

            v_l = d_enc_l * DIST_PER_TICK / dt
            v_r = d_enc_r * DIST_PER_TICK / dt

            v_enc     = (v_l + v_r) / 2.0
            omega_enc = (v_r - v_l) / TRACK_WIDTH

            self._omega_enc = omega_enc

            # EKF measurement update with encoder velocities
            z = np.array([v_enc, omega_enc])
            H = np.array([
                [0.0, 0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 1.0],
            ])
            R_enc = np.diag([self._r_enc_v, self._r_enc_w])

            self._x, self._P = self._ekf_update(self._x, self._P, z, H, R_enc)

    # ────────────────────────────────────────────────────────────────────────
    # IMU callback — prediction + IMU update
    # ────────────────────────────────────────────────────────────────────────
    def _imu_callback(self, msg: Imu):
        omega_imu = msg.angular_velocity.z
        now = time.monotonic()

        with self._lock:
            dt_pred = now - self._prev_imu_t
            self._prev_imu_t = now

            if dt_pred <= 0.0 or dt_pred > 1.0:
                # Skip if dt is unreasonable (first call or stale)
                return

            # ── EKF Prediction ───────────────────────────────────────────────
            theta = self._x[2]
            v     = self._x[3]
            omega = self._x[4]

            x_new = np.array([
                self._x[0] + v * cos(theta) * dt_pred,
                self._x[1] + v * sin(theta) * dt_pred,
                self._x[2] + omega * dt_pred,
                self._x[3],
                self._x[4],
            ])

            # Jacobian F (5×5)
            F = np.eye(5)
            F[0][2] = -v * sin(theta) * dt_pred
            F[0][3] =  cos(theta) * dt_pred
            F[1][2] =  v * cos(theta) * dt_pred
            F[1][3] =  sin(theta) * dt_pred
            F[2][4] =  dt_pred

            P_new = F @ self._P @ F.T + self._Q

            self._x = x_new
            self._P = P_new

            # ── EKF Update: IMU omega ─────────────────────────────────────────
            z_imu = np.array([omega_imu])
            H_imu = np.array([[0.0, 0.0, 0.0, 0.0, 1.0]])
            R_imu = np.array([[self._r_imu_w]])

            self._x, self._P = self._ekf_update(self._x, self._P, z_imu, H_imu, R_imu)

            # ── Drift computation ─────────────────────────────────────────────
            self._omega_drift = self._omega_enc - omega_imu

    # ────────────────────────────────────────────────────────────────────────
    # 50Hz publish timer
    # ────────────────────────────────────────────────────────────────────────
    def _publish_callback(self):
        with self._lock:
            x     = self._x.copy()
            P_diag = np.diag(self._P).copy()
            drift  = self._omega_drift

        # ── /vehicle/pose ────────────────────────────────────────────────────
        odom_msg = Odometry()
        odom_msg.header.stamp    = self.get_clock().now().to_msg()
        odom_msg.header.frame_id = 'odom'
        odom_msg.child_frame_id  = 'base_link'

        odom_msg.pose.pose.position.x = float(x[0])
        odom_msg.pose.pose.position.y = float(x[1])
        odom_msg.pose.pose.position.z = 0.0

        theta = float(x[2])
        odom_msg.pose.pose.orientation = Quaternion(
            x=0.0,
            y=0.0,
            z=float(sin(theta / 2.0)),
            w=float(cos(theta / 2.0)),
        )

        odom_msg.twist.twist.linear.x  = float(x[3])
        odom_msg.twist.twist.angular.z = float(x[4])

        # Pose covariance (6×6 row-major, indices 0,7,35 for x,y,yaw)
        pose_cov = [0.0] * 36
        pose_cov[0]  = max(float(P_diag[0]), 1e-6)   # x
        pose_cov[7]  = max(float(P_diag[1]), 1e-6)   # y
        pose_cov[35] = max(float(P_diag[2]), 1e-6)   # yaw
        odom_msg.pose.covariance = pose_cov

        # Twist covariance (6×6 row-major, indices 0,35 for v,omega)
        twist_cov = [0.0] * 36
        twist_cov[0]  = max(float(P_diag[3]), 1e-6)  # v
        twist_cov[35] = max(float(P_diag[4]), 1e-6)  # omega
        odom_msg.twist.covariance = twist_cov

        self._pub_pose.publish(odom_msg)

        # ── /vehicle/drift_correction ────────────────────────────────────────
        drift_msg = Float32()
        drift_msg.data = float(drift)
        self._pub_drift.publish(drift_msg)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(args=None):
    rclpy.init(args=args)
    node = EKFNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        node.get_logger().error(f'EKF node exception: {exc}')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
