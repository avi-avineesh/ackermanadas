# ADAS — Autonomous Driving Assistance System

## Abstract

This paper presents the design and simulation-validated deployment of a
complete Autonomous Driving Assistance System (ADAS) on a resource-
constrained RC-scale vehicle platform. The system implements four features
— Automatic Emergency Braking (AEB), Adaptive Cruise Control (ACC), Lane
Keep Assist (LKA), and Traffic Sign Detection (TSD) — using a four-package
ROS2 Jazzy architecture on a Raspberry Pi 5 with a dual-ECU CAN bus
actuation architecture: a dedicated Steer-By-Wire ECU (Arduino Uno R3)
controlling the front steering servo, and a Throttle-By-Wire ECU (Arduino
Uno R3) controlling rear motors, braking, and wheel encoder odometry.

The primary contribution is a confidence-weighted dual-modality AEB
architecture fusing a Benewake TF-Luna LiDAR (distance and Time-To-
Collision via EMA-smoothed relative velocity) with a YOLO11n camera channel
(vehicle classification and visual distance estimation). Unlike hard AND
fusion — which catastrophically suppresses braking when the camera degrades
in low light or occlusion — or hard OR fusion — which reintroduces false-
positive braking from non-vehicle obstacles — the proposed system
dynamically weights camera contribution via the YOLO11n detection confidence
score. Three adaptive modes operate: AND mode (confidence > 0.60) enforces
vehicle classification to suppress false positives; advisory mode (0.20–
0.60) allows LiDAR to decide while camera can only escalate severity; and
LiDAR-only mode (< 0.20) preserves full braking under degraded camera
conditions. A hard safety override ensures the vehicle always stops within
50 cm regardless of camera state.

The secondary contribution is a colour-agnostic LKA algorithm using HSV-
space white isolation (S < 50, V > μ + 1.5σ per frame) with Inverse
Perspective Mapping and 2nd-degree polynomial lane fitting, replacing
grayscale adaptive thresholding to enable reliable lane detection on any
road surface colour. All algorithms are validated in Gazebo Harmonic
simulation and targeted for hardware deployment via the same ROS2 node
graph with zero code changes.

---

## Hardware Platform

| Component | Model | Role |
|-----------|-------|------|
| Brain | Raspberry Pi 5 (8 GB) | Main compute, ROS2 Jazzy, Ubuntu 24.04 |
| SBW ECU | Arduino Uno R3 #1 | Steer-By-Wire via CAN 0x110/0x310 |
| TBW ECU | Arduino Uno R3 #2 | Throttle-By-Wire + encoder odometry via CAN |
| Motors | PG36M555 DC 12V 359 RPM ×2 | Rear-wheel drive |
| Driver | SmartElex 10D Dual PWM | Motor driver (controlled by TBW ECU D4-D7) |
| Servo | TowerPro MG995 180° | Ackermann front steering (SBW ECU D9) |
| Encoders | OE-37 Hall Effect ×2 | Rear wheel odometry (TBW ECU A0-A3) |
| LiDAR | Benewake TF-Luna | Forward ranging, 0.2–8m, 10Hz, UART |
| Camera | Waveshare IMX219 8MP | MIPI-CSI, 640×480 @ 30Hz |
| IMU | MPU6050 6-axis | I2C accelerometer + gyro |
| ToF | VL53L0X ×2 | Left/right flanks, I2C, 0.03–2m |
| CAN Pi | Waveshare RS485 CAN HAT | SPI on Pi 5 |
| CAN SBW | MCP2515 + TJA1050 | SPI pins 10-13, INT 2 (Arduino #1) |
| CAN TBW | MCP2515 + TJA1050 | SPI pins 10-13, INT 2 (Arduino #2) |
| Battery | 11.1V 3S 3300 mAh 35C LiPo | Main power |
| BEC | 5V 5A | Pi USB-C + servo power |

## Dual-ECU CAN Architecture

```
Pi (CAN HAT) ─────────── CAN bus 500kbps ─────────── SBW Arduino ─── TBW Arduino
  [Waveshare RS485]         [0x110→/0x310←]              #1               #2
                            Steer-By-Wire             [0x120→/0x220←/0x320←]
                                                       Throttle-By-Wire + Odometry

Pi core pinning:
  Cores 0-1 → YOLO11n inference (perception/camera_node)
  Core 2    → LKA + CAN bridge (adas_core hw + mission)
  Core 3    → AEB + ACC + EKF (adas_core safety + localization)

CAN ID table:
  0x110  Pi→SBW   int16 steer_angle_mrad (±600 mrad)
  0x310  SBW→Pi   int16 actual_mrad + uint8 status
  0x120  Pi→TBW   int16 speed_mm_s + uint8 brake_pct
  0x220  TBW→Pi   int32 enc_L_ticks + int32 enc_R_ticks
  0x320  TBW→Pi   int16 rpm_L + int16 rpm_R + uint8 status

Termination: 120Ω at Pi HAT end and TBW Arduino end only.
```

## Package Architecture

| Package | Type | Purpose | Status |
|---------|------|---------|--------|
| `robot_bringup` | ament_cmake | URDF, Gazebo world, spawn, launch | Full |
| `perception` | ament_python | YOLO11n camera + LiDAR/ToF validation | Full |
| `adas_core` | ament_python | AEB (full), ACC/LKA/TSD/EKF/CAN stubs | AEB Full |
| `dashboard` | ament_python | Tkinter GUI: manual drive + AEB monitor | Full |

**Why 4 packages?**
All logic nodes run on the same Pi, share the same ROS2 graph, one developer.
Perception is separate because YOLO inference is CPU-heavy with different deps.
Dashboard is separate because a Tkinter crash must not stop the car.

### adas_core internal structure
```
adas_core/
  safety/    aeb_node (FULL)  acc_node (STUB)  safety_arbiter (STUB)
  mission/   lka_node (STUB)  tsd_node (STUB)
  localization/ ekf_node (STUB)
  hw/        can_bridge_node (STUB)
```

## Confidence-Weighted Fusion Logic

| Confidence | Mode | Behaviour |
|-----------|------|-----------|
| > 0.60 | AND (HIGH) | `fused_dist = min(lidar, cam_dist)` only when car detected |
| 0.20–0.60 | Advisory (MED) | LiDAR decides; camera can only escalate |
| < 0.20 | LiDAR-only (LOW) | Camera ignored completely |
| Any | Safety override | If `lidar_dist < 0.50m` → AEB_STOP regardless |

## Braking Profile

| State | Trigger | Speed |
|-------|---------|-------|
| RAMP | Started, < 3s | 0→100% over 3s |
| CLEAR | dist > 3m AND ttc > 4s | 100% (1.0 m/s) |
| WARNING | dist < 3m OR ttc < 4s | 100% (alert only) |
| PARTIAL_BRAKE | dist < 2m OR ttc < 2.5s | 50% |
| HARD_BRAKE | dist < 0.8m OR ttc < 1.2s | 8% |
| AEB_STOP | dist < 0.5m OR ttc < 0.5s | 0% LATCHED |
| SIDE_EMERGENCY | either ToF < 0.20m | 0% (unlatched) |

## Building and Running

### One-Time Setup
```bash
# Copy SolidWorks meshes (for visual model)
cp -r ~/project_ws/src/autonomous_car/meshes \
      ~/adas_ws/src/robot_bringup/

# Install YOLO11n
pip install ultralytics --break-system-packages
```

### Build
```bash
cd ~/adas_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### Run — 5 terminals
```bash
# T1 — Simulation (Gazebo + spawn + bridge)
source ~/adas_ws/install/setup.bash
ros2 launch robot_bringup aeb.launch.py

# T2 — Perception (YOLO11n)
source ~/adas_ws/install/setup.bash
ros2 run perception camera_node

# T3 — AEB
source ~/adas_ws/install/setup.bash
ros2 run adas_core aeb_node

# T4 — Dashboard
source ~/adas_ws/install/setup.bash
ros2 run dashboard gui_node

# T5 — Camera debug view
ros2 run rqt_image_view rqt_image_view
# → select /ego/camera/debug
# → GREEN bar = AND mode | YELLOW = advisory | RED = LiDAR only
```

### Operate
Dashboard → AUTO tab → START AEB
Car ramps to 1.0 m/s → detects black car obstacle → stops at 50cm gap.

### Monitor
```bash
ros2 topic echo /aeb/status    # 11-field pipe-separated telemetry at 50Hz
ros2 topic hz /ego/detections  # YOLO11n output rate
```

### Hardware Phase 2 — CAN bridge
```bash
sudo ip link set can0 up type can bitrate 500000
sudo ip link set can0 txqueuelen 1000
ros2 run adas_core can_bridge_node
candump can0   # should show 0x310 from SBW and 0x320 from TBW
```

## Future Phases

| Phase | Feature | Key Tech |
|-------|---------|---------|
| 1 | AEB ✅ | Confidence-weighted LiDAR+YOLO11n fusion |
| 2 | ACC + CAN | PID gap-hold, dual-ECU CAN bridge, EKF |
| 3 | LKA | HSV→IPM→polyfit→PID lane keep |
| 4 | TSD | YOLO11n crop + HSV sign classification |
| 5 | Hardware | Pi 5 deployment, real sensors, CAN bus |
