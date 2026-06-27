from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'adas_core'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ADAS Team',
    maintainer_email='adas@icarm2026.org',
    description='Production-grade ADAS system for RC-scale autonomous car — ICARM 2026',
    license='MIT',
    entry_points={
        'console_scripts': [
            'tf_luna_node = adas_core.sensors.tf_luna_node:main',
            'tof_node = adas_core.sensors.tof_node:main',
            'imu_node = adas_core.sensors.imu_node:main',
            'camera_node = adas_core.sensors.camera_node:main',
            'yolo_node = adas_core.perception.yolo_node:main',
            'lane_node = adas_core.perception.lane_node:main',
            'ekf_node = adas_core.localisation.ekf_node:main',
            'aeb_node = adas_core.safety.aeb_node:main',
            'acc_node = adas_core.safety.acc_node:main',
            'lka_node = adas_core.safety.lka_node:main',
            'traffic_node = adas_core.safety.traffic_node:main',
            'safety_arbiter = adas_core.safety.safety_arbiter:main',
            'can_bridge_node = adas_core.control.can_bridge_node:main',
            'mode_manager = adas_core.control.mode_manager:main',
            'dashboard_node = adas_core.dashboard.dashboard_node:main',
            'integrated_safety_node = adas_core.safety.integrated_safety_node:main',
            'dashboard_v3 = adas_core.dashboard.dashboard_v3:main',
            'adas_node = adas_core.safety.adas_node:main',
            'dashboard_v4 = adas_core.dashboard.dashboard_v4:main',
        ],
    },
)
