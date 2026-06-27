"""
tof_node.py
-----------
ROS2 Jazzy node for dual VL53L1X Time-of-Flight sensors via I2C1.

Hardware:
  LEFT  sensor: XSHUT on BCM17, reassigned I2C address 0x30
  RIGHT sensor: XSHUT on BCM27, stays at default I2C address 0x29

Boot sequence:
  1. Both XSHUT LOW  → both sensors held in reset
  2. LEFT XSHUT HIGH → LEFT wakes at 0x29
  3. Rewrite LEFT I2C address to 0x30 via register 0x0001
  4. RIGHT XSHUT HIGH → RIGHT wakes at 0x29 (no conflict now)

Uses lgpio (gpiochip4 on RPi 5) for GPIO and smbus2 + vl53l1x for I2C.
Publishes sensor_msgs/Range on /sensor/tof_left and /sensor/tof_right at 10 Hz.
"""

import math
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Range

import lgpio
import smbus2
import vl53l1x


# VL53L1X I2C addresses
ADDR_DEFAULT = 0x29
ADDR_LEFT    = 0x30
ADDR_RIGHT   = 0x29   # unchanged

# VL53L1X register for I2C address change (7-bit address stored as 8-bit shifted left)
VL53L1X_I2C_SLAVE_DEVICE_ADDRESS = 0x0001

# GPIO chip on Raspberry Pi 5
GPIO_CHIP = 4         # /dev/gpiochip4


class TofNode(Node):
    """Publishes left and right VL53L1X distance readings as Range messages."""

    def __init__(self) -> None:
        super().__init__('tof_node')

        # Parameters
        self.declare_parameter('i2c_bus', 1)
        self.declare_parameter('xshut_left_pin', 17)
        self.declare_parameter('xshut_right_pin', 27)

        i2c_bus          = self.get_parameter('i2c_bus').get_parameter_value().integer_value
        xshut_left_pin   = self.get_parameter('xshut_left_pin').get_parameter_value().integer_value
        xshut_right_pin  = self.get_parameter('xshut_right_pin').get_parameter_value().integer_value

        # QoS
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # Publishers
        self._pub_left  = self.create_publisher(Range, '/sensor/tof_left',  sensor_qos)
        self._pub_right = self.create_publisher(Range, '/sensor/tof_right', sensor_qos)

        # Thread lock
        self._lock = threading.Lock()

        # GPIO setup via lgpio (gpiochip4 on RPi 5)
        self._gpio_handle: int | None = None
        self._xshut_left  = xshut_left_pin
        self._xshut_right = xshut_right_pin

        self._tof_left:  vl53l1x.VL53L1X | None = None
        self._tof_right: vl53l1x.VL53L1X | None = None

        try:
            self._init_hardware(i2c_bus)
        except Exception as exc:
            self.get_logger().error(f'TofNode hardware init failed: {exc}')

        # 10 Hz timer
        self._timer = self.create_timer(0.1, self._timer_callback)

    # ------------------------------------------------------------------
    # Hardware initialisation
    # ------------------------------------------------------------------

    def _init_hardware(self, i2c_bus: int) -> None:
        """Bring up GPIO and both VL53L1X sensors with address reassignment."""
        # Open GPIO chip
        self._gpio_handle = lgpio.gpiochip_open(GPIO_CHIP)

        # Configure XSHUT pins as outputs
        lgpio.gpio_claim_output(self._gpio_handle, self._xshut_left)
        lgpio.gpio_claim_output(self._gpio_handle, self._xshut_right)

        # --- Step 1: Hold both sensors in reset ---
        lgpio.gpio_write(self._gpio_handle, self._xshut_left,  0)
        lgpio.gpio_write(self._gpio_handle, self._xshut_right, 0)
        time.sleep(0.01)

        # --- Step 2: Wake LEFT sensor (comes up at 0x29) ---
        lgpio.gpio_write(self._gpio_handle, self._xshut_left, 1)
        time.sleep(0.01)   # boot time

        # --- Step 3: Reassign LEFT address from 0x29 → 0x30 ---
        bus = smbus2.SMBus(i2c_bus)
        try:
            # Write new address (7-bit, shifted left by 1 per VL53L1X spec)
            bus.write_byte_data(
                ADDR_DEFAULT,
                VL53L1X_I2C_SLAVE_DEVICE_ADDRESS,
                ADDR_LEFT << 1,
            )
        finally:
            bus.close()
        time.sleep(0.005)

        # --- Step 4: Wake RIGHT sensor (comes up at 0x29, no conflict) ---
        lgpio.gpio_write(self._gpio_handle, self._xshut_right, 1)
        time.sleep(0.01)

        # --- Step 5: Initialise vl53l1x objects ---
        self._tof_left = vl53l1x.VL53L1X(i2c_bus=i2c_bus, i2c_address=ADDR_LEFT)
        self._tof_left.open()
        self._tof_left.start_ranging(1)   # 1 = Short range mode

        self._tof_right = vl53l1x.VL53L1X(i2c_bus=i2c_bus, i2c_address=ADDR_RIGHT)
        self._tof_right.open()
        self._tof_right.start_ranging(1)  # 1 = Short range mode

        self.get_logger().info(
            f'VL53L1X sensors initialised: LEFT=0x{ADDR_LEFT:02X}, RIGHT=0x{ADDR_RIGHT:02X}'
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_range_msg(self, distance_m: float, frame_id: str) -> Range:
        msg = Range()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        msg.radiation_type = Range.INFRARED   # 1
        msg.field_of_view  = 0.436            # ~25 degrees in radians
        msg.min_range  = 0.04
        msg.max_range  = 4.0
        msg.range = float(distance_m)
        return msg

    def _read_sensor(
        self,
        tof: 'vl53l1x.VL53L1X | None',
        label: str,
    ) -> float:
        """
        Read distance from a VL53L1X sensor.
        Returns distance in metres, or math.inf on error.
        """
        if tof is None:
            return math.inf
        try:
            distance_mm = tof.get_distance()
            if distance_mm <= 0:
                return math.inf
            return distance_mm / 1000.0
        except Exception as exc:
            self.get_logger().warning(f'TofNode {label} read error: {exc}')
            return math.inf

    # ------------------------------------------------------------------
    # Timer callback (10 Hz)
    # ------------------------------------------------------------------

    def _timer_callback(self) -> None:
        with self._lock:
            dist_left_m  = self._read_sensor(self._tof_left,  'LEFT')
            dist_right_m = self._read_sensor(self._tof_right, 'RIGHT')

        self._pub_left.publish(self._build_range_msg(dist_left_m,   'tof_left_link'))
        self._pub_right.publish(self._build_range_msg(dist_right_m, 'tof_right_link'))

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def destroy_node(self) -> None:
        # Stop ranging and close sensors
        for label, tof in [('LEFT', self._tof_left), ('RIGHT', self._tof_right)]:
            if tof is not None:
                try:
                    tof.stop_ranging()
                except Exception as exc:
                    self.get_logger().warning(f'TofNode {label} stop_ranging error: {exc}')

        # Release GPIO
        if self._gpio_handle is not None:
            try:
                lgpio.gpio_write(self._gpio_handle, self._xshut_left,  0)
                lgpio.gpio_write(self._gpio_handle, self._xshut_right, 0)
                lgpio.gpiochip_close(self._gpio_handle)
            except Exception as exc:
                self.get_logger().warning(f'TofNode GPIO cleanup error: {exc}')

        self.get_logger().info('TofNode hardware resources released.')
        super().destroy_node()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(args=None) -> None:
    rclpy.init(args=args)
    node = TofNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
