#!/usr/bin/env python3
"""
spawn_ego.py — Spawn ego car in Gazebo Harmonic
================================================
Package: robot_bringup

Uses ros_gz_sim create to spawn URDF into Gazebo.
This correctly handles URDF format (unlike gz service sdf_filename
which requires actual SDF format and silently fails with URDF).

Substitutions applied to URDF before spawn:
  - package://robot_bringup/meshes/ → file:///absolute/path/
  - topic names namespaced to ns= (default: ego)
"""
import subprocess
import os
import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory


def resolve_urdf(urdf_path: str, ns: str, meshes_abs: str) -> str:
    """Read URDF and apply mesh path + topic namespace substitutions."""
    with open(urdf_path, 'r') as f:
        urdf = f.read()

    # Mesh paths — replace both possible package names
    for pkg_ref in ['package://autonomous_car/meshes/',
                    'package://robot_bringup/meshes/']:
        urdf = urdf.replace(pkg_ref, f'file://{meshes_abs}/')

    # Topic namespace substitutions
    subs = [
        ('<topic>cmd_vel</topic>',          f'<topic>{ns}/cmd_vel</topic>'),
        ('<odom_topic>odom</odom_topic>',    f'<odom_topic>{ns}/odom</odom_topic>'),
        ('<tf_topic>tf</tf_topic>',          f'<tf_topic>{ns}/tf</tf_topic>'),
        ('<topic>/gz/lidar_range</topic>',   f'<topic>/{ns}/lidar_range</topic>'),
        ('<topic>/gz/camera/image</topic>',  f'<topic>/{ns}/camera/image_raw</topic>'),
        ('<topic>/gz/tof_left</topic>',      f'<topic>/{ns}/tof_left</topic>'),
        ('<topic>/gz/tof_right</topic>',     f'<topic>/{ns}/tof_right</topic>'),
    ]
    for old, new in subs:
        urdf = urdf.replace(old, new)

    return urdf


class SpawnEgo(Node):

    def __init__(self):
        super().__init__('spawn_ego')

        self.declare_parameter('world', 'aeb_world')
        self.declare_parameter('ns',    'ego')
        self.declare_parameter('x',     0.3)
        self.declare_parameter('y',     0.0)
        self.declare_parameter('z',     0.15)

        world = self.get_parameter('world').value
        ns    = self.get_parameter('ns').value
        x     = self.get_parameter('x').value
        y     = self.get_parameter('y').value
        z     = self.get_parameter('z').value

        self.get_logger().info(
            f'[spawn_ego] world={world}  pose=({x},{y},{z})  ns={ns}')

        pkg         = get_package_share_directory('robot_bringup')
        urdf_path   = os.path.join(pkg, 'urdf', 'autonomous_car.urdf')
        meshes_path = os.path.join(pkg, 'meshes')

        if not os.path.isdir(meshes_path):
            self.get_logger().warn(
                f'[spawn_ego] meshes/ NOT found at: {meshes_path}\n'
                f'           Run: cp -r ~/project_ws/src/autonomous_car/meshes '
                f'{meshes_path}')

        # Resolve URDF
        urdf = resolve_urdf(urdf_path, ns, meshes_path)
        tmp_urdf = f'/tmp/{ns}_resolved.urdf'
        with open(tmp_urdf, 'w') as f:
            f.write(urdf)
        self.get_logger().info(f'[spawn_ego] Resolved URDF → {tmp_urdf}')

        # Spawn using ros_gz_sim create (handles URDF natively)
        self.get_logger().info('[spawn_ego] Spawning via ros_gz_sim create...')
        result = subprocess.run([
            'ros2', 'run', 'ros_gz_sim', 'create',
            '-world', world,
            '-file',  tmp_urdf,
            '-name',  ns,
            '-x', str(x),
            '-y', str(y),
            '-z', str(z),
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            self.get_logger().info('[spawn_ego] Spawned OK ✓')
        else:
            self.get_logger().error(
                f'[spawn_ego] ros_gz_sim create failed (rc={result.returncode}):\n'
                f'stdout: {result.stdout}\nstderr: {result.stderr}')
            self.get_logger().info('[spawn_ego] Trying gz service fallback...')
            self._gz_service_spawn(world, tmp_urdf, ns, x, y, z)

        raise SystemExit

    def _gz_service_spawn(self, world, urdf_path, ns, x, y, z):
        """Fallback: read URDF content and pass as raw sdf string."""
        with open(urdf_path, 'r') as f:
            content = f.read()
        # Escape for protobuf text format
        content = content.replace('"', '\\"').replace('\n', '\\n')
        req = (
            f'sdf: "{content}", '
            f'name: "{ns}", '
            f'pose: {{position: {{x: {x}, y: {y}, z: {z}}}}}'
        )
        result = subprocess.run([
            'gz', 'service',
            '-s', f'/world/{world}/create',
            '--reqtype', 'gz.msgs.EntityFactory',
            '--reptype', 'gz.msgs.Boolean',
            '--timeout', '10000',
            '--req', req,
        ], capture_output=True, text=True, timeout=15)

        if 'true' in result.stdout.lower():
            self.get_logger().info('[spawn_ego] gz service fallback OK ✓')
        else:
            self.get_logger().error(
                f'[spawn_ego] Both methods failed.\n'
                f'stdout: {result.stdout}\nstderr: {result.stderr}')


def main(args=None):
    rclpy.init(args=args)
    try:
        SpawnEgo()
    except SystemExit:
        pass
    except Exception as e:
        import traceback
        print(f'[spawn_ego] Exception: {e}')
        traceback.print_exc()
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()
