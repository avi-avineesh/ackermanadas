"""
pi.launch.py — Launch all ADAS nodes on Raspberry Pi 5  (serial-bridge variant)

Usage:
    export ROS_DOMAIN_ID=42
    source ~/adas_ws/install/setup.bash
    ros2 launch adas_core pi.launch.py

Optional overrides:
    ros2 launch adas_core pi.launch.py debug:=true
    ros2 launch adas_core pi.launch.py serial_port:=/dev/ttyUSB1
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # ── Arguments ──────────────────────────────────────────────────────────────
    args = [
        DeclareLaunchArgument('debug',       default_value='false',
                              description='Enable verbose debug output'),
        DeclareLaunchArgument('use_camera',  default_value='true'),
        DeclareLaunchArgument('use_yolo',    default_value='true'),
        DeclareLaunchArgument('model_path',  default_value='~/models/yolo11n_adas.pt',
                              description='Path to YOLO model file'),
        DeclareLaunchArgument('serial_port', default_value='/dev/ttyUSB0',
                              description='Serial port for combined_ecu_serial Arduino'),
    ]

    common = dict(output='screen', emulate_tty=True)

    nodes = [
        # ── Sensors ────────────────────────────────────────────────────────────
        Node(package='adas_core', executable='tf_luna_node',
             name='tf_luna_node', **common,
             parameters=[{'port': '/dev/ttyAMA2', 'baudrate': 115200}]),

        Node(package='adas_core', executable='camera_node',
             name='camera_node', **common,
             parameters=[{'width': 640, 'height': 480, 'fps': 30}]),

        # ── Perception ─────────────────────────────────────────────────────────
        Node(package='adas_core', executable='yolo_node',
             name='yolo_node', **common,
             parameters=[{
                 'model_path':     LaunchConfiguration('model_path'),
                 'conf_threshold': 0.45,
             }]),

        Node(package='adas_core', executable='lane_node',
             name='lane_node', **common,
             parameters=[{'debug_publish': True}]),

        # ── Safety (integrated: AEB + ACC + LKA + mode management) ────────────
        Node(package='adas_core', executable='adas_node',
             name='adas_node', **common),

        # ── Control ────────────────────────────────────────────────────────────
        Node(package='adas_core', executable='serial_bridge_node',
             name='serial_bridge_node', **common,
             parameters=[{
                 'serial_port': LaunchConfiguration('serial_port'),
                 'baudrate':    115200,
             }]),
    ]

    return LaunchDescription(args + nodes)
