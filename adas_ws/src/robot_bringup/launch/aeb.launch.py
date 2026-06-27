#!/usr/bin/env python3
"""
aeb.launch.py — Phase 1 AEB Launch
════════════════════════════════════
t=0s   Gazebo (aeb_world)
t=8s   spawn_ego (ros_gz_sim create)
t=13s  ros_gz_bridge (all /ego/ topics)
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('robot_bringup')
    world_file = os.path.join(pkg_share, 'worlds', 'aeb_world.sdf')

    gz_sim = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_file],
        output='screen',
    )

    spawn = TimerAction(
        period=8.0,
        actions=[ExecuteProcess(
            cmd=['ros2', 'run', 'robot_bringup', 'spawn_ego'],
            output='screen',
        )],
    )

    bridge = TimerAction(
        period=13.0,
        actions=[Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='ego_bridge',
            arguments=[
                '/ego/lidar_range@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                '/ego/tof_left@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                '/ego/tof_right@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                '/ego/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
                '/ego/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                '/ego/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            ],
            output='screen',
        )],
    )

    return LaunchDescription([gz_sim, spawn, bridge])
