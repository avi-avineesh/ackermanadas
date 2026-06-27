"""
imu_node.py
-----------
ROS2 Jazzy node for MPU6050 IMU via smbus2 on I2C1, address 0x68.

Register map:
  PWR_MGMT_1  = 0x6B → write 0x00 to wake sensor
  ACCEL_XOUT_H = 0x3B  (6 bytes: Ax_H, Ax_L, Ay_H, Ay_L, Az_H, Az_L)
  GYRO_XOUT_H  = 0x43  (6 bytes: Gx_H, Gx_L, Gy_H, Gy_L, Gz_H, Gz_L)

Scale factors:
  accel: ±2 g default  → 9.81 / 16384.0 m/s²  per LSB
  gyro:  ±250°/s default → π / (180 × 131) rad/s per LSB

Startup calibration:
  Collect 200 samples at ~100 Hz with the sensor at rest.
  Compute mean gyro on each axis → bias.
  Persist to /tmp/imu_cal.json; reload on subsequent starts unless
  force_calibrate=True is set.

Publishes:
  /sensor/imu    (sensor_msgs/Imu)    at 100 Hz
  /sensor/gyro_z (std_msgs/Float32)   at 100 Hz
"""

import json
import math
import os
import struct
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Imu
from std_msgs.msg import Float32

import smbus2


# MPU6050 registers
REG_PWR_MGMT_1  = 0x6B
REG_ACCEL_XOUT_H = 0x3B
REG_GYRO_XOUT_H  = 0x43

# Scale factors
ACCEL_SCALE = 9.81 / 16384.0             # m/s² per LSB  (±2 g range)
GYRO_SCALE  = math.pi / (180.0 * 131.0)  # rad/s per LSB (±250°/s range)

# Calibration
CAL_SAMPLES = 200
CAL_FILE    = '/tmp/imu_cal.json'
CAL_RATE_HZ = 100.0


def _to_signed16(high: int, low: int) -> int:
    """Combine two bytes into a signed 16-bit integer."""
    val = (high << 8) | low
    if val >= 0x8000:
        val -= 0x10000
    return val


class ImuNode(Node):
    """Reads MPU6050 and publishes Imu + gyro_z Float32 at 100 Hz."""

    def __init__(self) -> None:
        super().__init__('imu_node')

        # Parameters
        self.declare_parameter('i2c_bus',        1)
        self.declare_parameter('address',        0x68)
        self.declare_parameter('force_calibrate', False)

        i2c_bus         = self.get_parameter('i2c_bus').get_parameter_value().integer_value
        address         = self.get_parameter('address').get_parameter_value().integer_value
        force_calibrate = self.get_parameter('force_calibrate').get_parameter_value().bool_value

        self._addr = address

        # QoS
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # Publishers
        self._imu_pub   = self.create_publisher(Imu,     '/sensor/imu',    sensor_qos)
        self._gyro_pub  = self.create_publisher(Float32, '/sensor/gyro_z', sensor_qos)

        # Thread lock (guards smbus and bias values)
        self._lock = threading.Lock()

        # Gyro bias (rad/s)
        self._bias_x: float = 0.0
        self._bias_y: float = 0.0
        self._bias_z: float = 0.0

        # Open I2C bus
        self._bus: smbus2.SMBus | None = None
        try:
            self._bus = smbus2.SMBus(i2c_bus)
            self._wake_sensor()
            self.get_logger().info(
                f'MPU6050 connected on I2C bus {i2c_bus} at address 0x{address:02X}'
            )
        except Exception as exc:
            self.get_logger().error(f'MPU6050 init failed: {exc}')

        # Calibration
        if not force_calibrate and os.path.isfile(CAL_FILE):
            self._load_calibration()
        else:
            self._run_calibration()

        # 100 Hz timer
        self._timer = self.create_timer(1.0 / 100.0, self._timer_callback)

    # ------------------------------------------------------------------
    # Sensor communication
    # ------------------------------------------------------------------

    def _wake_sensor(self) -> None:
        """Clear sleep bit to wake MPU6050."""
        if self._bus is None:
            return
        self._bus.write_byte_data(self._addr, REG_PWR_MGMT_1, 0x00)
        time.sleep(0.1)

    def _read_raw(self) -> tuple[float, float, float, float, float, float]:
        """
        Read accel (m/s²) and gyro (rad/s) from MPU6050.
        Returns (ax, ay, az, gx, gy, gz).
        Raises OSError on I2C failure.
        """
        if self._bus is None:
            raise OSError('I2C bus not open')

        accel_data = self._bus.read_i2c_block_data(self._addr, REG_ACCEL_XOUT_H, 6)
        gyro_data  = self._bus.read_i2c_block_data(self._addr, REG_GYRO_XOUT_H,  6)

        ax = _to_signed16(accel_data[0], accel_data[1]) * ACCEL_SCALE
        ay = _to_signed16(accel_data[2], accel_data[3]) * ACCEL_SCALE
        az = _to_signed16(accel_data[4], accel_data[5]) * ACCEL_SCALE

        gx = _to_signed16(gyro_data[0], gyro_data[1]) * GYRO_SCALE
        gy = _to_signed16(gyro_data[2], gyro_data[3]) * GYRO_SCALE
        gz = _to_signed16(gyro_data[4], gyro_data[5]) * GYRO_SCALE

        return ax, ay, az, gx, gy, gz

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def _run_calibration(self) -> None:
        """Collect CAL_SAMPLES gyro readings at rest and compute bias."""
        if self._bus is None:
            self.get_logger().warning('IMU: skipping calibration — I2C bus not available')
            return

        self.get_logger().info(
            f'IMU calibration: collecting {CAL_SAMPLES} samples, keep sensor still...'
        )

        sum_gx = sum_gy = sum_gz = 0.0
        collected = 0
        interval = 1.0 / CAL_RATE_HZ

        for _ in range(CAL_SAMPLES):
            start = time.monotonic()
            try:
                _, _, _, gx, gy, gz = self._read_raw()
                sum_gx += gx
                sum_gy += gy
                sum_gz += gz
                collected += 1
            except Exception as exc:
                self.get_logger().warning(f'IMU calibration sample read error: {exc}')
            elapsed = time.monotonic() - start
            remaining = interval - elapsed
            if remaining > 0:
                time.sleep(remaining)

        if collected == 0:
            self.get_logger().error('IMU calibration failed: no samples collected')
            return

        with self._lock:
            self._bias_x = sum_gx / collected
            self._bias_y = sum_gy / collected
            self._bias_z = sum_gz / collected

        cal_data = {
            'gyro_bias_x': self._bias_x,
            'gyro_bias_y': self._bias_y,
            'gyro_bias_z': self._bias_z,
        }
        try:
            with open(CAL_FILE, 'w') as f:
                json.dump(cal_data, f, indent=2)
        except OSError as exc:
            self.get_logger().warning(f'IMU: could not save calibration file: {exc}')

        self.get_logger().info(
            f'IMU calibration complete ({collected} samples): '
            f'bias_x={self._bias_x:.6f}, bias_y={self._bias_y:.6f}, bias_z={self._bias_z:.6f} rad/s'
        )

    def _load_calibration(self) -> None:
        """Load previously saved gyro bias from /tmp/imu_cal.json."""
        try:
            with open(CAL_FILE, 'r') as f:
                cal_data = json.load(f)
            with self._lock:
                self._bias_x = float(cal_data['gyro_bias_x'])
                self._bias_y = float(cal_data['gyro_bias_y'])
                self._bias_z = float(cal_data['gyro_bias_z'])
            self.get_logger().info(
                f'IMU calibration loaded from {CAL_FILE}: '
                f'bias_x={self._bias_x:.6f}, bias_y={self._bias_y:.6f}, bias_z={self._bias_z:.6f} rad/s'
            )
        except Exception as exc:
            self.get_logger().warning(
                f'IMU: failed to load calibration file ({exc}), re-calibrating...'
            )
            self._run_calibration()

    # ------------------------------------------------------------------
    # Message construction
    # ------------------------------------------------------------------

    def _build_imu_msg(
        self,
        ax: float, ay: float, az: float,
        gx: float, gy: float, gz: float,
    ) -> Imu:
        msg = Imu()
        stamp = self.get_clock().now().to_msg()
        msg.header.stamp    = stamp
        msg.header.frame_id = 'imu_link'

        # Orientation unknown (no magnetometer) — signal with covariance[0] = -1
        msg.orientation.x = 0.0
        msg.orientation.y = 0.0
        msg.orientation.z = 0.0
        msg.orientation.w = 1.0
        msg.orientation_covariance[0] = -1.0

        # Angular velocity (bias-subtracted)
        msg.angular_velocity.x = gx
        msg.angular_velocity.y = gy
        msg.angular_velocity.z = gz
        msg.angular_velocity_covariance = [
            0.01, 0.0,  0.0,
            0.0,  0.01, 0.0,
            0.0,  0.0,  0.01,
        ]

        # Linear acceleration
        msg.linear_acceleration.x = ax
        msg.linear_acceleration.y = ay
        msg.linear_acceleration.z = az
        msg.linear_acceleration_covariance = [
            0.1, 0.0, 0.0,
            0.0, 0.1, 0.0,
            0.0, 0.0, 0.1,
        ]

        return msg

    # ------------------------------------------------------------------
    # Timer callback (100 Hz)
    # ------------------------------------------------------------------

    def _timer_callback(self) -> None:
        try:
            with self._lock:
                ax, ay, az, gx_raw, gy_raw, gz_raw = self._read_raw()
                bias_x = self._bias_x
                bias_y = self._bias_y
                bias_z = self._bias_z

            # Subtract bias
            gx = gx_raw - bias_x
            gy = gy_raw - bias_y
            gz = gz_raw - bias_z

        except Exception as exc:
            self.get_logger().warning(f'IMU read error (skipping sample): {exc}')
            return

        # Publish IMU message
        imu_msg = self._build_imu_msg(ax, ay, az, gx, gy, gz)
        self._imu_pub.publish(imu_msg)

        # Publish gyro_z
        gyro_z_msg = Float32()
        gyro_z_msg.data = float(gz)
        self._gyro_pub.publish(gyro_z_msg)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def destroy_node(self) -> None:
        if self._bus is not None:
            try:
                self._bus.close()
            except Exception as exc:
                self.get_logger().warning(f'IMU smbus close error: {exc}')
        self.get_logger().info('ImuNode I2C bus closed.')
        super().destroy_node()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(args=None) -> None:
    rclpy.init(args=args)
    node = ImuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
