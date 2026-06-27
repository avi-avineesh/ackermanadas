"""
laptop.launch.py — Launch ADAS dashboard on laptop

Usage:
    export ROS_DOMAIN_ID=42
    source ~/adas_ws/install/setup.bash
    ros2 launch adas_core laptop.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='adas_core',
            executable='dashboard_node',
            name='dashboard_node',
            output='screen',
            emulate_tty=True,
        ),
    ])
