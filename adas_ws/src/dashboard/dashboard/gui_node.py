#!/usr/bin/env python3
"""
gui_node.py — Dashboard Layer: Unified Operator GUI
════════════════════════════════════════════════════
Package : dashboard | 820×760 Tkinter | ROS2 node in daemon thread

LAYOUT:
  Title bar: "██  ADAS DASHBOARD  v1.0  ██"  [MANUAL] [AUTO]
  Content area: MANUAL panel or AUTO panel (swapped on mode change)
  Status bar (bottom, 1 line)

AUTO PANEL shows: Fusion Mode (most prominent), Live Sensors,
  AEB State indicators, Ego speed, Start/Reset buttons.

FUSION MODE BAR (most prominent widget in AUTO tab):
  GREEN  (conf > 0.60) — AND mode active
  YELLOW (0.20–0.60)   — advisory mode
  RED    (< 0.20)      — LiDAR only

STATUS parsing from /aeb/status (11 fields, pipe-separated):
  STATE|lidar|ttc|cam_dist|bbox_h|cam_conf|fusion_mode|tof_l|tof_r|spd|cv

PUBLISHERS: /ego/cmd_vel  /aeb/cmd
SUBSCRIBERS: /aeb/status  /ego/odom
"""

import math
import threading
import tkinter as tk
import tkinter.font as tkfont

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String

# ═══ COLOURS ═════════════════════════════════════════════════════════════════
C = dict(
    bg='#080818',     panel='#10102a',  border='#1a1a3a',
    green='#00e676',  yellow='#ffea00', red='#ff1744',
    cyan='#00e5ff',   white='#e8e8ff',  grey='#252545',
    orange='#ff6d00', purple='#d500f9', teal='#1de9b6',
)

STATE_COLOUR = {
    'IDLE': C['grey'], 'RAMP': C['cyan'], 'CLEAR': C['green'],
    'WARNING': C['yellow'], 'PARTIAL_BRAKE': C['orange'],
    'HARD_BRAKE': C['red'], 'AEB_STOP': C['red'], 'SIDE_EMERGENCY': C['red'],
}
STATE_IDX = {
    'RAMP': 0, 'WARNING': 1, 'PARTIAL_BRAKE': 2,
    'HARD_BRAKE': 3, 'AEB_STOP': 4, 'SIDE_EMERGENCY': 5,
}
FUSION_COLOUR = {'HIGH': C['green'], 'MED': C['yellow'], 'LOW': C['red']}
FUSION_LABEL  = {
    'HIGH': 'HIGH CONFIDENCE — AND mode active',
    'MED':  'MED CONFIDENCE  — advisory mode',
    'LOW':  'LOW CONFIDENCE  — LiDAR only',
}


# ═══ GLOBAL STATE (thread-safe) ═══════════════════════════════════════════════
class GS:
    lock        = threading.Lock()
    state       = 'IDLE'
    lidar_dist  = float('inf')
    ttc         = float('inf')
    cam_dist    = float('inf')
    bbox_h      = 0
    cam_conf    = 0.0
    fusion_mode = 'LOW'
    tof_left    = float('inf')
    tof_right   = float('inf')
    ego_speed   = 0.0
    closing_vel = 0.0
    aeb_alive   = False


def _parse_status(data: str):
    """Parse 11-field pipe-separated /aeb/status into GS."""
    parts = data.split('|')
    if len(parts) < 11:
        return
    try:
        def f(s): return float(s) if s != 'inf' else float('inf')
        with GS.lock:
            GS.state       = parts[0]
            GS.lidar_dist  = f(parts[1])
            GS.ttc         = f(parts[2])
            GS.cam_dist    = f(parts[3])
            GS.bbox_h      = int(parts[4]) if parts[4].lstrip('-').isdigit() else 0
            GS.cam_conf    = f(parts[5])
            GS.fusion_mode = parts[6]  # HIGH / MED / LOW
            GS.tof_left    = f(parts[7])
            GS.tof_right   = f(parts[8])
            GS.ego_speed   = f(parts[9])
            GS.closing_vel = f(parts[10])
            GS.aeb_alive   = True
    except (ValueError, IndexError):
        pass


# ═══ ROS2 NODE ════════════════════════════════════════════════════════════════
class DashboardNode(Node):
    """ROS2 node — spins in daemon thread."""

    def __init__(self):
        super().__init__('gui_node')
        self._pub_cmd = self.create_publisher(Twist,  '/ego/cmd_vel', 10)
        self._pub_aeb = self.create_publisher(String, '/aeb/cmd',     10)
        self.create_subscription(String,   '/aeb/status', self._aeb_cb,  10)
        self.create_subscription(Odometry, '/ego/odom',   self._odom_cb, 10)
        self.get_logger().info('[dashboard] GUI node ready.')

    def _aeb_cb(self, msg: String):
        _parse_status(msg.data)

    def _odom_cb(self, msg: Odometry):
        vx = msg.twist.twist.linear.x
        vy = msg.twist.twist.linear.y
        with GS.lock:
            GS.ego_speed = math.sqrt(vx * vx + vy * vy)

    def send_vel(self, lin: float, ang: float):
        msg = Twist(); msg.linear.x = lin; msg.angular.z = ang
        self._pub_cmd.publish(msg)

    def send_aeb(self, cmd: str):
        msg = String(); msg.data = cmd
        self._pub_aeb.publish(msg)


# ═══ GUI ══════════════════════════════════════════════════════════════════════
class DashboardGUI:
    """820×760 dark Tkinter dashboard."""

    def __init__(self, node: DashboardNode):
        self._node = node
        self._mode = 'AUTO'

        self._root = tk.Tk()
        self._root.title('ADAS Dashboard v1.0')
        self._root.geometry('820x760')
        self._root.resizable(False, False)
        self._root.configure(bg=C['bg'])

        TF = tkfont.Font
        self._F = {
            'title': TF(family='Courier', size=14, weight='bold'),
            'head':  TF(family='Courier', size=10, weight='bold'),
            'body':  TF(family='Courier', size=9),
            'big':   TF(family='Courier', size=18, weight='bold'),
            'med':   TF(family='Courier', size=12, weight='bold'),
        }

        self._build_title()
        self._content = tk.Frame(self._root, bg=C['bg'])
        self._content.pack(fill='both', expand=True, padx=4, pady=2)
        self._build_manual_panel()
        self._build_auto_panel()
        self._build_status_bar()

        self._root.bind('<KeyPress>',   self._key_press)
        self._root.bind('<KeyRelease>', self._key_release)

        self._switch_auto()
        self._root.after(100, self._update)

    # ── Build helpers ──────────────────────────────────────────────────────────

    def _lf(self, parent, text, fg=None, bd=1):
        """Create a dark-theme LabelFrame."""
        return tk.LabelFrame(parent, text=text, font=self._F['head'],
                              bg=C['bg'], fg=fg or C['white'], bd=bd, relief='solid')

    def _build_title(self):
        """Top bar with title and mode buttons."""
        bar = tk.Frame(self._root, bg=C['panel'], height=42)
        bar.pack(fill='x', padx=4, pady=(4, 0))
        tk.Label(bar, text='██  ADAS DASHBOARD  v1.0  ██',
                 font=self._F['title'], bg=C['panel'], fg=C['cyan']).pack(side='left', padx=10)
        self._btn_auto = tk.Button(bar, text='AUTO',   font=self._F['head'], bg=C['panel'],
                                    fg=C['grey'], width=8, command=self._switch_auto,  relief='flat')
        self._btn_auto.pack(side='right', padx=4)
        self._btn_man  = tk.Button(bar, text='MANUAL', font=self._F['head'], bg=C['panel'],
                                    fg=C['grey'], width=8, command=self._switch_manual, relief='flat')
        self._btn_man.pack(side='right', padx=4)

    def _build_manual_panel(self):
        """MANUAL drive panel."""
        self._man_frame = tk.Frame(self._content, bg=C['bg'])

        drive = self._lf(self._man_frame, '── Manual Drive ──')
        drive.pack(fill='x', padx=6, pady=6)
        tk.Label(drive, text='Controlling: ego car', font=self._F['body'],
                  bg=C['bg'], fg=C['grey']).pack(pady=2)

        dpad = tk.Frame(drive, bg=C['bg'])
        dpad.pack(pady=8)
        bk = dict(width=5, height=2, font=tkfont.Font(family='Courier', size=13, weight='bold'),
                  relief='raised', bd=2)
        tk.Button(dpad, text='▲', bg=C['panel'], fg=C['green'], **bk,
                  command=lambda: self._node.send_vel(0.6, 0.0)  ).grid(row=0, column=1, padx=2, pady=2)
        tk.Button(dpad, text='◄', bg=C['panel'], fg=C['cyan'],  **bk,
                  command=lambda: self._node.send_vel(0.0, 0.6)  ).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(dpad, text='■', bg=C['red'],   fg=C['white'], **bk,
                  command=lambda: self._node.send_vel(0.0, 0.0)  ).grid(row=1, column=1, padx=2, pady=2)
        tk.Button(dpad, text='►', bg=C['panel'], fg=C['cyan'],  **bk,
                  command=lambda: self._node.send_vel(0.0,-0.6)  ).grid(row=1, column=2, padx=2, pady=2)
        tk.Button(dpad, text='▼', bg=C['panel'], fg=C['orange'],**bk,
                  command=lambda: self._node.send_vel(-0.6,0.0)  ).grid(row=2, column=1, padx=2, pady=2)
        tk.Label(drive, text='W/S/A/D + Arrow keys · Space = stop',
                  font=self._F['body'], bg=C['bg'], fg=C['grey']).pack(pady=4)

        spd_lf = self._lf(self._man_frame, '── Speed ──')
        spd_lf.pack(fill='x', padx=6, pady=4)
        self._man_spd_var = tk.StringVar(value='0.00 m/s')
        tk.Label(spd_lf, textvariable=self._man_spd_var, font=self._F['big'],
                  bg=C['bg'], fg=C['green']).pack(pady=4)
        self._man_spd_bar = tk.Canvas(spd_lf, width=280, height=18,
                                       bg=C['panel'], highlightthickness=0)
        self._man_spd_bar.pack(pady=4)

    def _build_auto_panel(self):
        """AUTO (AEB monitoring) panel."""
        self._auto_frame = tk.Frame(self._content, bg=C['bg'])

        # AEB Control
        ctrl = self._lf(self._auto_frame, '── AEB Control ──', fg=C['cyan'])
        ctrl.pack(fill='x', padx=6, pady=4)
        btn_row = tk.Frame(ctrl, bg=C['bg'])
        btn_row.pack(pady=6)
        tk.Button(btn_row, text='START AEB', width=14, bg='#1b5e20', fg=C['green'],
                  font=self._F['head'], relief='raised', bd=2,
                  command=self._start_aeb).pack(side='left', padx=8)
        tk.Button(btn_row, text='STOP / RESET', width=14, bg='#b71c1c', fg=C['white'],
                  font=self._F['head'], relief='raised', bd=2,
                  command=self._reset_aeb).pack(side='left', padx=8)

        # Fusion Mode — most prominent widget
        self._fusion_lf = self._lf(self._auto_frame, '── Fusion Mode ──', fg=C['grey'])
        self._fusion_lf.pack(fill='x', padx=6, pady=4)
        self._fusion_var = tk.StringVar(value='LOW CONFIDENCE  — LiDAR only')
        self._fusion_label = tk.Label(self._fusion_lf, textvariable=self._fusion_var,
                                       font=self._F['med'], bg=C['bg'], fg=C['red'])
        self._fusion_label.pack(pady=6)
        conf_row = tk.Frame(self._fusion_lf, bg=C['bg'])
        conf_row.pack(pady=2)
        self._conf_bar = tk.Canvas(conf_row, width=300, height=14,
                                    bg=C['panel'], highlightthickness=0)
        self._conf_bar.pack(side='left', padx=4)
        self._conf_var = tk.StringVar(value='Camera confidence: 0.000')
        tk.Label(conf_row, textvariable=self._conf_var, font=self._F['body'],
                  bg=C['bg'], fg=C['grey']).pack(side='left', padx=6)

        # Live Sensors
        sens_lf = self._lf(self._auto_frame, '── Live Sensors ──')
        sens_lf.pack(fill='x', padx=6, pady=4)
        self._sv = {}
        self._bars = {}
        sensors = [
            ('lidar_dist', 'LiDAR dist   :', C['cyan'],   8.0),
            ('ttc',        'TTC          :', C['yellow'], 10.0),
            ('cam_dist',   'Camera dist  :', C['purple'],  8.0),
            ('closing_vel','Closing vel  :', C['teal'],   None),
            ('tof_lr',     'ToF L / R    :', C['orange'], None),
            ('bbox_h',     'Camera bbox  :', C['purple'], None),
        ]
        for key, lbl, col, scale in sensors:
            row = tk.Frame(sens_lf, bg=C['bg'])
            row.pack(fill='x', padx=8, pady=1)
            tk.Label(row, text=lbl, font=self._F['body'], bg=C['bg'],
                      fg=col, width=16, anchor='w').pack(side='left')
            if scale:
                bar = tk.Canvas(row, width=220, height=14, bg=C['panel'],
                                 highlightthickness=0)
                bar.pack(side='left', padx=4)
                self._bars[key] = (bar, scale)
            var = tk.StringVar(value='---')
            self._sv[key] = var
            tk.Label(row, textvariable=var, font=self._F['body'],
                      bg=C['bg'], fg=col, width=22, anchor='w').pack(side='left')

        # AEB State indicators
        self._state_lf = self._lf(self._auto_frame, '── AEB State ──', fg=C['grey'])
        self._state_lf.pack(fill='x', padx=6, pady=4)
        ind_frame = tk.Frame(self._state_lf, bg=C['bg'])
        ind_frame.pack(pady=4)
        ind_defs = [
            ('RAMP',         C['cyan'],   0, 0),
            ('WARNING',      C['yellow'], 0, 1),
            ('PARTIAL BRK',  C['orange'], 0, 2),
            ('HARD BRK',     C['red'],    1, 0),
            ('AEB STOP',     C['red'],    1, 1),
            ('SIDE EMRG',    C['red'],    1, 2),
        ]
        self._ind_dots = []
        for label, colour, row, col in ind_defs:
            cell = tk.Frame(ind_frame, bg=C['bg'])
            cell.grid(row=row, column=col, padx=12, pady=3)
            cv = tk.Canvas(cell, width=16, height=16, bg=C['bg'], highlightthickness=0)
            cv.pack(side='left')
            oval = cv.create_oval(2, 2, 14, 14, fill=C['panel'], outline='')
            tk.Label(cell, text=label, font=self._F['body'],
                      bg=C['bg'], fg=C['grey']).pack(side='left', padx=3)
            self._ind_dots.append((cv, oval, colour))

        # Ego speed
        spd_lf = self._lf(self._auto_frame, '── Ego Speed ──')
        spd_lf.pack(fill='x', padx=6, pady=4)
        sr = tk.Frame(spd_lf, bg=C['bg'])
        sr.pack(fill='x', padx=8, pady=4)
        self._auto_spd_var = tk.StringVar(value='0.00 m/s')
        tk.Label(sr, textvariable=self._auto_spd_var, font=self._F['med'],
                  bg=C['bg'], fg=C['green']).pack(side='left', padx=8)
        self._auto_spd_bar = tk.Canvas(sr, width=320, height=15,
                                        bg=C['panel'], highlightthickness=0)
        self._auto_spd_bar.pack(side='left')

    def _build_status_bar(self):
        """Bottom status bar."""
        self._status_var = tk.StringVar(value='ADAS Dashboard v1.0 — Phase 1: AEB')
        tk.Label(self._root, textvariable=self._status_var, font=self._F['body'],
                  bg=C['panel'], fg=C['grey'], anchor='w', padx=8).pack(fill='x', side='bottom')

    # ── Mode switching ──────────────────────────────────────────────────────────

    def _switch_manual(self):
        self._mode = 'MANUAL'
        self._node.send_vel(0.0, 0.0)
        self._node.send_aeb('manual_on')
        self._btn_man.configure(fg=C['green'])
        self._btn_auto.configure(fg=C['grey'])
        self._auto_frame.pack_forget()
        self._man_frame.pack(fill='both', expand=True)
        self._status_var.set('MANUAL mode — WASD / D-pad / Arrow keys · Space = stop')

    def _switch_auto(self):
        self._mode = 'AUTO'
        self._node.send_vel(0.0, 0.0)
        self._node.send_aeb('manual_off')
        self._btn_auto.configure(fg=C['cyan'])
        self._btn_man.configure(fg=C['grey'])
        self._man_frame.pack_forget()
        self._auto_frame.pack(fill='both', expand=True)
        self._status_var.set('AUTO mode — click START AEB to begin scenario')

    def _start_aeb(self):
        self._node.send_aeb('start')
        self._status_var.set('AEB started — ramping to 1.0 m/s')

    def _reset_aeb(self):
        self._node.send_aeb('reset')
        self._status_var.set('AEB reset — send START to begin again')

    # ── 10Hz update loop ───────────────────────────────────────────────────────

    def _update(self):
        """Read GS under lock, update all widgets at 10Hz."""
        with GS.lock:
            state       = GS.state
            lidar_dist  = GS.lidar_dist
            ttc         = GS.ttc
            cam_dist    = GS.cam_dist
            bbox_h      = GS.bbox_h
            cam_conf    = GS.cam_conf
            fusion_mode = GS.fusion_mode
            tof_left    = GS.tof_left
            tof_right   = GS.tof_right
            ego_speed   = GS.ego_speed
            closing_vel = GS.closing_vel

        if self._mode == 'AUTO':
            # ── Fusion Mode widget ────────────────────────────────────────
            fm_col = FUSION_COLOUR.get(fusion_mode, C['red'])
            fm_txt = FUSION_LABEL.get(fusion_mode, 'LOW CONFIDENCE  — LiDAR only')
            self._fusion_var.set(fm_txt)
            self._fusion_label.configure(fg=fm_col)
            self._fusion_lf.configure(fg=fm_col)

            # Confidence bar
            self._conf_bar.delete('all')
            bar_w = int(cam_conf * 300)
            if bar_w > 0:
                self._conf_bar.create_rectangle(0, 0, bar_w, 14, fill=fm_col, outline='')
            self._conf_var.set(f'Camera confidence: {cam_conf:.3f}')

            # ── Sensor values ─────────────────────────────────────────────
            def fd(v): return f'{v:.3f}m' if math.isfinite(v) else 'inf m'
            cv_sign = '+' if closing_vel >= 0 else ''
            cv_desc = 'approaching' if closing_vel > 0.01 else ('receding' if closing_vel < -0.01 else 'static')
            bbox_desc = f'{bbox_h}px  (car ✓)' if bbox_h > 10 else f'{bbox_h}px'
            tof_str = f'{tof_left:.2f}m  /  {tof_right:.2f}m' if (math.isfinite(tof_left) and math.isfinite(tof_right)) else 'inf / inf'

            self._sv['lidar_dist'].set(fd(lidar_dist))
            self._sv['ttc'].set(f'{ttc:.2f}s' if math.isfinite(ttc) else 'inf s')
            self._sv['cam_dist'].set(fd(cam_dist))
            self._sv['closing_vel'].set(f'{cv_sign}{closing_vel:.3f} m/s  ({cv_desc})')
            self._sv['tof_lr'].set(tof_str)
            self._sv['bbox_h'].set(bbox_desc)

            # Bar drawing — close=red, far=green
            self._draw_bar(self._bars.get('lidar_dist'), lidar_dist)
            self._draw_bar(self._bars.get('ttc'),        ttc)
            self._draw_bar(self._bars.get('cam_dist'),   cam_dist)

            # ── Indicator dots ────────────────────────────────────────────
            active = STATE_IDX.get(state, -1)
            for i, (cv, oval, col) in enumerate(self._ind_dots):
                cv.itemconfig(oval, fill=col if i == active else C['panel'])

            # State frame border
            self._state_lf.configure(fg=STATE_COLOUR.get(state, C['grey']))

            # Ego speed bar
            ratio = min(ego_speed / 1.0, 1.0)
            bc = C['green'] if ratio < 0.4 else (C['yellow'] if ratio < 0.8 else C['red'])
            self._auto_spd_bar.delete('all')
            self._auto_spd_bar.create_rectangle(0, 0, int(320 * ratio), 15, fill=bc, outline='')
            self._auto_spd_var.set(f'{ego_speed:.2f} m/s')

        else:
            # MANUAL panel speed bar
            ratio = min(ego_speed / 1.0, 1.0)
            bc = C['green'] if ratio < 0.4 else (C['yellow'] if ratio < 0.8 else C['red'])
            self._man_spd_bar.delete('all')
            self._man_spd_bar.create_rectangle(0, 0, int(280 * ratio), 18, fill=bc, outline='')
            self._man_spd_var.set(f'{ego_speed:.2f} m/s')

        self._root.after(100, self._update)

    def _draw_bar(self, bar_info, value):
        """Draw distance/TTC bar — low value = red (danger closer)."""
        if bar_info is None:
            return
        canvas, scale = bar_info
        canvas.delete('all')
        if not math.isfinite(value):
            return
        ratio = min(value / scale, 1.0)
        colour = C['red'] if ratio < 0.25 else (C['yellow'] if ratio < 0.5 else C['green'])
        canvas.create_rectangle(0, 0, int(220 * ratio), 14, fill=colour, outline='')

    # ── Keyboard ───────────────────────────────────────────────────────────────

    def _key_press(self, event):
        if self._mode != 'MANUAL':
            return
        k = event.keysym.lower()
        if k in ('w', 'up'):       self._node.send_vel(0.6,  0.0)
        elif k in ('s', 'down'):   self._node.send_vel(-0.6, 0.0)
        elif k in ('a', 'left'):   self._node.send_vel(0.0,  0.6)
        elif k in ('d', 'right'):  self._node.send_vel(0.0, -0.6)
        elif k == 'space':         self._node.send_vel(0.0,  0.0)

    def _key_release(self, event):
        if self._mode != 'MANUAL':
            return
        k = event.keysym.lower()
        if k in ('w', 'up', 's', 'down', 'a', 'left', 'd', 'right'):
            self._node.send_vel(0.0, 0.0)

    def run(self):
        """Blocking Tkinter main loop."""
        self._root.mainloop()


# ═══ MAIN ════════════════════════════════════════════════════════════════════

def main(args=None):
    rclpy.init(args=args)
    node = DashboardNode()
    ros_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()
    gui = DashboardGUI(node)
    try:
        gui.run()
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        try:
            rclpy.shutdown()
        except Exception:
            pass


if __name__ == '__main__':
    main()
