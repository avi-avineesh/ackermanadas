from setuptools import find_packages, setup

package_name = 'dashboard'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ADAS Team',
    maintainer_email='adas@example.com',
    description='Operator dashboard GUI for ADAS',
    license='MIT',
    entry_points={
        'console_scripts': [
            'gui_node = dashboard.gui_node:main',
        ],
    },
)
