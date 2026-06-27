#!/usr/bin/env python3
"""
generate_lka_world.py — Procedurally generate lka_world.sdf
=============================================================
Track layout (12 m along +X):
  S1  x=0→2    straight,    y_centre=0.0
  S2  x=2→4    curve left,  y=0.3·sin(π(x-2)/2)
  S3  x=4→6    straight,    y_centre=+0.3
  S4  x=6→8    curve right, y=0.3·cos(π(x-6)/2)
  S5  x=8→12   straight,    y_centre=-0.3

Run:  python3 generate_lka_world.py
"""
import math
import os

# ── Geometry constants ─────────────────────────────────────────────────────
ROAD_W       = 0.66     # road width [m]
ROAD_THICK   = 0.002    # road box thickness [m]
LANE_W       = 0.035    # white tape width [m]
LANE_THICK   = 0.003    # tape box thickness [m]
LANE_OFFSET  = 0.3125   # distance from road centre to tape centre [m]
ROAD_Z       = 0.001    # road box centre z [m]
LANE_Z       = 0.004    # lane box centre z [m] — above road top (0.002) to avoid z-fight

N_CURVE_SEGS = 32
CURVE_LEN    = 2.0

# ── Material XML ──────────────────────────────────────────────────────────
ROAD_MAT = """\
          <material>
            <ambient>0.05 0.05 0.05 1</ambient>
            <diffuse>0.08 0.08 0.08 1</diffuse>
            <specular>0.01 0.01 0.01 1</specular>
          </material>"""

LANE_MAT = """\
          <material>
            <ambient>1.0 1.0 1.0 1</ambient>
            <diffuse>1.0 1.0 1.0 1</diffuse>
            <specular>0.5 0.5 0.5 1</specular>
          </material>"""

RED_MAT = """\
          <material>
            <ambient>0.9 0.0 0.0 1</ambient>
            <diffuse>0.9 0.0 0.0 1</diffuse>
          </material>"""

GREEN_MAT = """\
          <material>
            <ambient>0.0 0.8 0.0 1</ambient>
            <diffuse>0.0 0.8 0.0 1</diffuse>
          </material>"""


# ── Low-level SDF helpers ──────────────────────────────────────────────────
def _box_link(sx, sy, sz, material, with_collision=True):
    col = ""
    if with_collision:
        col = f"""\
        <collision name="col">
          <geometry><box><size>{sx:.5f} {sy:.5f} {sz:.5f}</size></box></geometry>
        </collision>
"""
    return f"""\
      <link name="link">
{col}        <visual name="vis">
          <geometry><box><size>{sx:.5f} {sy:.5f} {sz:.5f}</size></box></geometry>
{material}
        </visual>
      </link>"""


def _model(name, px, py, pz, yaw, link_xml):
    return (
        f'    <model name="{name}">\n'
        f'      <static>true</static>\n'
        f'      <pose>{px:.5f} {py:.5f} {pz:.5f} 0 0 {yaw:.6f}</pose>\n'
        f'{link_xml}\n'
        f'    </model>'
    )


# ── Section generators ────────────────────────────────────────────────────
def straight_section(tag, x0, x1, yc, seg_len=None):
    """One road + two lane models for a straight section."""
    length = seg_len if seg_len is not None else (x1 - x0)
    xm = (x0 + x1) / 2.0
    out = []
    out.append(_model(f'{tag}_road',
                      xm, yc, ROAD_Z, 0.0,
                      _box_link(length, ROAD_W, ROAD_THICK, ROAD_MAT)))
    out.append(_model(f'{tag}_left',
                      xm, yc + LANE_OFFSET, LANE_Z, 0.0,
                      _box_link(length, LANE_W, LANE_THICK, LANE_MAT,
                                with_collision=False)))
    out.append(_model(f'{tag}_right',
                      xm, yc - LANE_OFFSET, LANE_Z, 0.0,
                      _box_link(length, LANE_W, LANE_THICK, LANE_MAT,
                                with_collision=False)))
    return '\n\n'.join(out)


def curved_section(tag, x_offset, y_func):
    """32 micro-segments for a curved section with derivative-based alignment."""
    out = []
    seg_len = CURVE_LEN / N_CURVE_SEGS
    for i in range(N_CURVE_SEGS):
        xs = x_offset + i * seg_len
        xe = x_offset + (i + 1) * seg_len
        xm = (xs + xe) / 2.0
        ym = y_func(xm)

        # Tangent angle: central-difference derivative at segment midpoint
        _dx = 0.001
        _dy = y_func(xm + _dx) - y_func(xm - _dx)
        angle = math.atan2(_dy, 2.0 * _dx)

        # Arc length of this segment (chord approximation)
        actual_len = math.sqrt(seg_len**2 + (y_func(xe) - y_func(xs))**2)
        box_len = actual_len + 0.005   # small overlap to close gaps

        # Perpendicular offsets (left = +90° from travel direction)
        lx = xm - math.sin(angle) * LANE_OFFSET
        ly = ym + math.cos(angle) * LANE_OFFSET
        rx = xm + math.sin(angle) * LANE_OFFSET
        ry = ym - math.cos(angle) * LANE_OFFSET

        out.append(_model(f'{tag}_road_{i}',
                          xm, ym, ROAD_Z, angle,
                          _box_link(box_len, ROAD_W, ROAD_THICK, ROAD_MAT)))
        out.append(_model(f'{tag}_left_{i}',
                          lx, ly, LANE_Z, angle,
                          _box_link(box_len, LANE_W, LANE_THICK, LANE_MAT,
                                    with_collision=False)))
        out.append(_model(f'{tag}_right_{i}',
                          rx, ry, LANE_Z, angle,
                          _box_link(box_len, LANE_W, LANE_THICK, LANE_MAT,
                                    with_collision=False)))
    return '\n\n'.join(out)


# ── Y-functions for curves ────────────────────────────────────────────────
def y_s2(x):
    """Section 2 — curve left: y = 0.3·sin(π(x-2)/2)"""
    return 0.3 * math.sin(math.pi * (x - 2.0) / 2.0)


def y_s4(x):
    """Section 4 — curve right: y = 0.3·cos(π(x-6)/2)"""
    return 0.3 * math.cos(math.pi * (x - 6.0) / 2.0)


# ── World assembly ────────────────────────────────────────────────────────
def build_world():
    track_parts = [
        straight_section('s1', 0.0, 2.0, 0.0),
        curved_section('s2', 2.0, y_s2),
        straight_section('s3', 4.0, 6.0, 0.3),
        curved_section('s4', 6.0, y_s4),
        straight_section('s5', 8.0, 12.0, -0.3, seg_len=4.0),
    ]
    track_xml = '\n\n'.join(track_parts)

    start_marker = _model(
        'start_marker', 0.05, 0.0, 0.05, 0.0,
        _box_link(0.05, 0.66, 0.08, RED_MAT, with_collision=False))

    end_marker = _model(
        'end_marker', 11.9, -0.3, 0.05, 0.0,
        _box_link(0.05, 0.66, 0.08, GREEN_MAT, with_collision=False))

    return f"""<?xml version="1.0" ?>
<sdf version="1.9">
  <world name="lka_world">

    <!-- ═══ PLUGINS ═══ -->
    <plugin filename="gz-sim-physics-system"           name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system"     name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system"           name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>
    <plugin filename="gz-sim-contact-system"           name="gz::sim::systems::Contact"/>

    <!-- ═══ PHYSICS ═══ -->
    <physics name="default_physics" type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <!-- ═══ SCENE ═══ -->
    <scene>
      <ambient>0.4 0.4 0.4 1</ambient>
      <background>0.08 0.08 0.12 1</background>
      <shadows>true</shadows>
    </scene>

    <!-- ═══ SUN ═══ -->
    <light name="sun" type="directional">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.9 0.9 0.9 1</diffuse>
      <specular>0.3 0.3 0.3 1</specular>
      <attenuation>
        <range>1000</range><constant>0.9</constant>
        <linear>0.01</linear><quadratic>0.001</quadratic>
      </attenuation>
      <direction>-0.5 0.1 -0.9</direction>
    </light>

    <!-- ═══ GROUND PLANE — brown earth, 20×20 m ═══ -->
    <model name="ground_plane">
      <static>true</static>
      <pose>6 0 0 0 0 0</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>20 20 0.01</size></box></geometry>
          <pose>0 0 -0.005 0 0 0</pose>
          <surface>
            <friction><ode><mu>0.8</mu><mu2>0.8</mu2></ode></friction>
          </surface>
        </collision>
        <visual name="visual">
          <geometry><box><size>20 20 0.01</size></box></geometry>
          <pose>0 0 -0.005 0 0 0</pose>
          <material>
            <ambient>0.45 0.28 0.10 1</ambient>
            <diffuse>0.55 0.35 0.15 1</diffuse>
            <specular>0.02 0.02 0.02 1</specular>
          </material>
        </visual>
      </link>
    </model>

    <!-- ═══════════════════════════════════════════
         TRACK — 5 sections
         S1 straight x=0→2   y=0.0
         S2 curve L  x=2→4   y=0.3·sin(π(x-2)/2)
         S3 straight x=4→6   y=+0.3
         S4 curve R  x=6→8   y=0.3·cos(π(x-6)/2)
         S5 straight x=8→12  y=-0.3
         ═══════════════════════════════════════════ -->

{track_xml}

    <!-- ═══ MARKERS ═══ -->

{start_marker}

{end_marker}

  </world>
</sdf>
"""


# ── Entry point ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    out_dir  = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, 'lka_world.sdf')
    content  = build_world()
    with open(out_path, 'w') as f:
        f.write(content)
    n_lines  = content.count('\n')
    n_models = content.count('<model name=')
    print(f'Written : {out_path}')
    print(f'Lines   : {n_lines}')
    print(f'Models  : {n_models}')
