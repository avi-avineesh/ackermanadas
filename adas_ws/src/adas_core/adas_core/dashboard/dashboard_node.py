#!/usr/bin/env python3
"""
ADAS Full Dashboard v2 — fills entire window
Grid layout: left(sensors) | centre(camera+log) | right(adas panels)
All panels expand to fill available space.
"""

import threading, time, math
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String, Float32
from sensor_msgs.msg import Range, Imu, Image
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import cv2
import numpy as np

import tkinter as tk
from tkinter import font as tkfont
try:
    from cv_bridge import CvBridge
    from PIL import Image as PILImage, ImageTk
    HAS_IMG = True
except:
    HAS_IMG = False

# ─────────────────────────────────────────────────────────────────────────────
# Shared state
# ─────────────────────────────────────────────────────────────────────────────
class S:
    lock         = threading.Lock()
    mode         = 'MANUAL'
    lidar_m      = float('inf')
    tof_right_m  = float('inf')
    tof_left_m   = float('inf')
    gyro_z       = 0.0
    accel_z      = 9.81
    vehicle_spd  = 0.0
    aeb_state    = 'IDLE'
    aeb_ttc      = float('inf')
    aeb_score    = 0.0
    aeb_cam_conf = 0.0
    acc_state    = 'IDLE'
    acc_gap      = float('inf')
    lka_mode     = 'NONE'
    lka_err_m    = 0.0
    lka_steer    = 0.0
    lka_conf     = 0.0
    arb_state    = 'IDLE'
    arb_speed    = 0.0
    arb_steer    = 0.0
    can_status   = 'DRY-RUN'
    can_rx_220   = 0
    can_rx_310   = 0
    can_rx_320   = 0
    debug_img    = None
    connected    = False
    last_t       = 0.0
    history      = []

def _log(txt):
    S.history.append(f'{time.strftime("%H:%M:%S")}  {txt}')
    S.history = S.history[-12:]

S._log = staticmethod(_log)

# ─────────────────────────────────────────────────────────────────────────────
# ROS2 Node
# ─────────────────────────────────────────────────────────────────────────────
class DashboardNode(Node):
    def __init__(self):
        super().__init__('dashboard_node')
        if HAS_IMG:
            self._bridge = CvBridge()

        be = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                        history=HistoryPolicy.KEEP_LAST, depth=1)
        re = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                        history=HistoryPolicy.KEEP_LAST, depth=10)

        self.create_subscription(Range,   '/sensor/lidar_range',    self._lidar,   be)
        self.create_subscription(Range,   '/sensor/tof_right',      self._tof_r,   be)
        self.create_subscription(Range,   '/sensor/tof_left',       self._tof_l,   be)
        self.create_subscription(Imu,     '/sensor/imu',            self._imu,     be)
        self.create_subscription(Float32, '/sensor/gyro_z',         self._gyro,    be)
        self.create_subscription(String,  '/safety/aeb_status',     self._aeb,     re)
        self.create_subscription(String,  '/safety/acc_status',     self._acc,     re)
        self.create_subscription(String,  '/safety/lka_status',     self._lka,     re)
        self.create_subscription(String,  '/safety/arbiter_status', self._arb,     re)
        self.create_subscription(String,  '/adas/mode',             self._mode,    re)
        self.create_subscription(Odometry,'/vehicle/odom',          self._odom,    be)
        self.create_subscription(Twist,   '/vehicle/cmd_vel_safe',  self._cmdvel,  be)
        self.create_subscription(String,  '/vehicle/rpm',           self._rpm,     re)
        if HAS_IMG:
            self.create_subscription(Image,'/lane/debug_image',     self._dbg_img, be)

        self.get_logger().info('Dashboard node started')

    def _touch(self):
        with S.lock:
            S.connected = True
            S.last_t    = time.time()

    def _lidar(self, m):
        self._touch()
        with S.lock:
            S.lidar_m = float(m.range) if math.isfinite(m.range) else float('inf')

    def _tof_r(self, m):
        with S.lock:
            S.tof_right_m = float(m.range) if math.isfinite(m.range) else float('inf')

    def _tof_l(self, m):
        with S.lock:
            S.tof_left_m = float(m.range) if math.isfinite(m.range) else float('inf')

    def _imu(self, m):
        with S.lock:
            S.gyro_z  = m.angular_velocity.z
            S.accel_z = m.linear_acceleration.z

    def _gyro(self, m):
        with S.lock: S.gyro_z = m.data

    def _aeb(self, m):
        self._touch()
        p = m.data.split('|')
        prev = S.aeb_state
        with S.lock:
            S.aeb_state = p[0] if p else 'IDLE'
            try: S.aeb_ttc      = float(p[1]) if p[1]!='inf' else float('inf')
            except: pass
            try: S.aeb_score    = float(p[2])
            except: pass
            try: S.aeb_cam_conf = float(p[4])
            except: pass
            if S.aeb_state != prev:
                S._log(f'AEB → {S.aeb_state}')

    def _acc(self, m):
        self._touch()
        p = m.data.split('|')
        with S.lock:
            S.acc_state = p[0] if p else 'IDLE'
            try: S.acc_gap = float(p[1])
            except: pass

    def _lka(self, m):
        self._touch()
        p = m.data.split('|')
        with S.lock:
            S.lka_mode  = p[0] if p else 'NONE'
            try: S.lka_err_m = float(p[1])
            except: pass
            try: S.lka_steer = float(p[2])
            except: pass
            try: S.lka_conf  = float(p[3])
            except: pass

    def _arb(self, m):
        self._touch()
        p = m.data.split('|')
        with S.lock:
            S.arb_state = p[0] if p else 'IDLE'
            try: S.arb_speed = float(p[1])
            except: pass
            try: S.arb_steer = float(p[2])
            except: pass

    def _mode(self, m):
        with S.lock: S.mode = m.data.upper()

    def _odom(self, m):
        with S.lock: S.vehicle_spd = abs(m.twist.twist.linear.x)

    def _cmdvel(self, m):
        with S.lock:
            S.arb_speed = m.linear.x
            S.arb_steer = m.angular.z

    def _rpm(self, m):
        with S.lock:
            S.can_rx_320 += 1
            S.can_status = 'LIVE' if 'DRY' not in m.data else 'DRY-RUN'

    def _dbg_img(self, m):
        if not HAS_IMG: return
        try:
            frame = self._bridge.imgmsg_to_cv2(m, 'bgr8')
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            with S.lock:
                S.debug_img = PILImage.fromarray(rgb)
        except: pass

# ─────────────────────────────────────────────────────────────────────────────
# Colours
# ─────────────────────────────────────────────────────────────────────────────
C = {
    'bg':    '#080e1a', 'panel': '#0f1c30', 'border':'#1a3050',
    'cyan':  '#00d4ff', 'green': '#00e676', 'orange':'#ff9100',
    'red':   '#ff3d57', 'yellow':'#ffd600', 'purple':'#9b59ff',
    'white': '#e8eeff', 'grey':  '#3d5a70', 'lgrey': '#8faabb',
}

# ─────────────────────────────────────────────────────────────────────────────
# GUI
# ─────────────────────────────────────────────────────────────────────────────
class ADASGUI:
    def __init__(self, root, node):
        self.root  = root
        self.node  = node
        self._tk_debug = None

        root.title('ADAS Full Dashboard')
        root.configure(bg=C['bg'])
        root.attributes('-zoomed', True)  # start maximised Linux
        root.resizable(True, True)

        self._build()
        self._update()

    # ── helpers ───────────────────────────────────────────────────────────────
    def F(self, parent, **kw):
        kw.setdefault('bg', C['panel'])
        return tk.Frame(parent, **kw)

    def LF(self, parent, title, color=None, **kw):
        kw.setdefault('bg', C['panel'])
        kw['fg']      = color or C['cyan']
        kw['font']    = tkfont.Font(family='Courier', size=9, weight='bold')
        kw['bd']      = 1
        kw['relief']  = 'groove'
        return tk.LabelFrame(parent, text=f' {title} ', **kw)

    def L(self, parent, text, color=None, size=9, bold=False, **kw):
        kw.setdefault('bg', C['panel'])
        kw['fg']   = color or C['lgrey']
        kw['font'] = tkfont.Font(family='Courier', size=size,
                                 weight='bold' if bold else 'normal')
        kw['text'] = text
        return tk.Label(parent, **kw)

    def SV(self, parent, color=None, size=10, bold=True, width=14, anchor='w'):
        var = tk.StringVar(value='---')
        lbl = tk.Label(parent, textvariable=var, bg=C['panel'],
                       fg=color or C['white'],
                       font=tkfont.Font(family='Courier', size=size,
                                        weight='bold' if bold else 'normal'),
                       width=width, anchor=anchor)
        return var, lbl

    def hbar(self, parent, w=180, h=10, color=None):
        cv = tk.Canvas(parent, width=w, height=h, bg=C['grey'],
                       highlightthickness=0)
        rect = cv.create_rectangle(0, 0, 0, h, fill=color or C['green'],
                                   outline='')
        return cv, rect

    def dot(self, parent, label, color):
        f  = self.F(parent)
        cv = tk.Canvas(f, width=16, height=16, bg=C['panel'],
                       highlightthickness=0)
        cv.pack()
        circ = cv.create_oval(2, 2, 14, 14, fill=C['grey'], outline='')
        self.L(f, label, size=8).pack()
        f.pack(side='left', padx=5, pady=2)
        return cv, circ, color

    def datarow(self, parent, label, color=None, size=10):
        f = self.F(parent); f.pack(fill='x', padx=8, pady=2)
        self.L(f, label+':', size=9, color=C['lgrey'],
               width=14, anchor='w').pack(side='left')
        var, lbl = self.SV(f, color=color or C['white'], size=size)
        lbl.pack(side='left', fill='x', expand=True)
        return var, lbl

    # ── build ──────────────────────────────────────────────────────────────────
    def _build(self):
        # ── Title ─────────────────────────────────────────────────────────────
        tb = tk.Frame(self.root, bg='#0a1525', height=48)
        tb.pack(fill='x')
        tb.pack_propagate(False)
        tk.Label(tb, text='██  ADAS FULL DASHBOARD  ██',
                 font=tkfont.Font(family='Courier', size=15, weight='bold'),
                 bg='#0a1525', fg=C['cyan']).pack(side='left', padx=18, pady=10)
        self._time_lbl = tk.Label(tb, text='', bg='#0a1525', fg=C['grey'],
                                  font=tkfont.Font(family='Courier', size=9))
        self._time_lbl.pack(side='left', padx=10)
        self._conn_lbl = tk.Label(tb, text='● OFFLINE', bg='#0a1525', fg=C['red'],
                                  font=tkfont.Font(family='Courier', size=10, weight='bold'))
        self._conn_lbl.pack(side='right', padx=18)
        self._mode_lbl = tk.Label(tb, text='MODE: ---', bg='#0a1525', fg=C['yellow'],
                                  font=tkfont.Font(family='Courier', size=11, weight='bold'))
        self._mode_lbl.pack(side='right', padx=18)

        # ── Body: 3 columns ───────────────────────────────────────────────────
        body = tk.Frame(self.root, bg=C['bg'])
        body.pack(fill='both', expand=True, padx=6, pady=4)

        body.columnconfigure(0, weight=2, minsize=260)
        body.columnconfigure(1, weight=5)
        body.columnconfigure(2, weight=3, minsize=320)
        body.rowconfigure(0, weight=1)

        left   = tk.Frame(body, bg=C['bg'])
        centre = tk.Frame(body, bg=C['bg'])
        right  = tk.Frame(body, bg=C['bg'])

        left.grid(  row=0, column=0, sticky='nsew', padx=(0,3))
        centre.grid(row=0, column=1, sticky='nsew', padx=3)
        right.grid( row=0, column=2, sticky='nsew', padx=(3,0))

        self._build_left(left)
        self._build_centre(centre)
        self._build_right(right)

    # ── LEFT COLUMN ───────────────────────────────────────────────────────────
    def _build_left(self, parent):
        parent.rowconfigure(0, weight=0)
        parent.rowconfigure(1, weight=0)
        parent.rowconfigure(2, weight=1)
        parent.columnconfigure(0, weight=1)

        # Sensors
        sf = self.LF(parent, 'SENSORS', C['cyan'])
        sf.grid(row=0, column=0, sticky='ew', pady=(0,4))

        self.L(sf, '─── DISTANCE ───', size=8, color=C['grey']).pack(pady=(6,2))

        # LiDAR row with bar
        lr = self.F(sf); lr.pack(fill='x', padx=8, pady=2)
        self.L(lr, 'TF-Luna LiDAR:', size=9, width=16, anchor='w').pack(side='left')
        self._lidar_var = tk.StringVar(value='--- m')
        self._lidar_lbl = tk.Label(lr, textvariable=self._lidar_var,
                                   bg=C['panel'], fg=C['orange'],
                                   font=tkfont.Font(family='Courier', size=10, weight='bold'),
                                   width=8)
        self._lidar_lbl.pack(side='left')
        self._lidar_cv, self._lidar_bar = self.hbar(lr, w=100, color=C['orange'])
        self._lidar_cv.pack(side='left', padx=4)

        self._tof_r_var, self._tof_r_lbl = self.datarow(sf, 'ToF Right', C['yellow'])
        self._tof_l_var, self._tof_l_lbl = self.datarow(sf, 'ToF Left',  C['yellow'])

        self.L(sf, '─── IMU ───', size=8, color=C['grey']).pack(pady=(6,2))
        self._gyro_var,  self._gyro_lbl  = self.datarow(sf, 'Gyro Z',  C['cyan'])
        self._accel_var, self._accel_lbl = self.datarow(sf, 'Accel Z', C['cyan'])

        self.L(sf, '─── VEHICLE ───', size=8, color=C['grey']).pack(pady=(6,2))
        sr = self.F(sf); sr.pack(fill='x', padx=8, pady=2)
        self.L(sr, 'Speed:', size=9, width=16, anchor='w').pack(side='left')
        self._spd_var = tk.StringVar(value='0.00 m/s')
        tk.Label(sr, textvariable=self._spd_var, bg=C['panel'], fg=C['green'],
                 font=tkfont.Font(family='Courier', size=10, weight='bold'),
                 width=8).pack(side='left')
        self._spd_cv, self._spd_bar = self.hbar(sr, w=100, color=C['green'])
        self._spd_cv.pack(side='left', padx=4)
        tk.Frame(sf, bg=C['panel'], height=6).pack()

        # CAN
        cf = self.LF(parent, 'CAN BUS', C['purple'])
        cf.grid(row=1, column=0, sticky='ew', pady=4)
        self._can_mode_var, _ = self.datarow(cf, 'Mode',   C['purple'])
        self._can_tx_var      = tk.StringVar(value='TX: 0x110 0x120')
        self._can_rx_var      = tk.StringVar(value='RX: enc=0 sbw=0 rpm=0')
        tk.Label(cf, textvariable=self._can_tx_var, bg=C['panel'], fg=C['cyan'],
                 font=tkfont.Font(family='Courier', size=8),
                 anchor='w').pack(fill='x', padx=8, pady=1)
        tk.Label(cf, textvariable=self._can_rx_var, bg=C['panel'], fg=C['green'],
                 font=tkfont.Font(family='Courier', size=8),
                 anchor='w').pack(fill='x', padx=8, pady=1)
        tk.Frame(cf, bg=C['panel'], height=4).pack()

        # Arbiter
        af = self.LF(parent, 'SAFETY ARBITER', C['yellow'])
        af.grid(row=2, column=0, sticky='nsew', pady=(4,0))
        self._arb_state_var, self._arb_state_lbl = self.datarow(af, 'Priority', C['yellow'], size=10)
        self._arb_speed_var, _                   = self.datarow(af, 'Safe Speed', C['green'])
        self._arb_steer_var, _                   = self.datarow(af, 'Safe Steer', C['cyan'])

        # History log in arbiter panel
        self.L(af, '─── EVENT LOG ───', size=8, color=C['grey']).pack(pady=(8,2))
        self._log_text = tk.Text(af, bg='#070d1a', fg=C['lgrey'],
                                 font=tkfont.Font(family='Courier', size=8),
                                 relief='flat', state='disabled', wrap='word')
        self._log_text.pack(fill='both', expand=True, padx=6, pady=(0,6))

    # ── CENTRE COLUMN ─────────────────────────────────────────────────────────
    def _build_centre(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=0)
        parent.columnconfigure(0, weight=1)

        # Camera frame
        cam_lf = self.LF(parent, 'LANE DEBUG IMAGE  /lane/debug_image', C['cyan'])
        cam_lf.grid(row=0, column=0, sticky='nsew', pady=(0,4))
        cam_lf.rowconfigure(0, weight=1)
        cam_lf.columnconfigure(0, weight=1)

        self._cam_canvas = tk.Canvas(cam_lf, bg='#050a14',
                                     highlightthickness=0)
        self._cam_canvas.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
        self._cam_canvas.create_text(320, 240,
                                     text='Waiting for /lane/debug_image...',
                                     fill=C['grey'],
                                     font=tkfont.Font(family='Courier', size=11))

        # Stats bar below camera
        stats = tk.Frame(parent, bg=C['panel'])
        stats.grid(row=1, column=0, sticky='ew', pady=(0,0))
        for i in range(4): stats.columnconfigure(i, weight=1)

        for col, (lbl, var_name, color) in enumerate([
            ('LiDAR', '_stat_lidar', C['orange']),
            ('LKA Err','_stat_lka',  C['cyan']),
            ('AEB',    '_stat_aeb',  C['red']),
            ('Speed',  '_stat_spd',  C['green']),
        ]):
            f = tk.Frame(stats, bg=C['panel'])
            f.grid(row=0, column=col, sticky='ew', padx=4, pady=4)
            self.L(f, lbl, size=8, color=C['lgrey']).pack()
            var = tk.StringVar(value='---')
            setattr(self, var_name, var)
            tk.Label(f, textvariable=var, bg=C['panel'], fg=color,
                     font=tkfont.Font(family='Courier', size=13, weight='bold')
                     ).pack()

    # ── RIGHT COLUMN ──────────────────────────────────────────────────────────
    def _build_right(self, parent):
        for i in range(3): parent.rowconfigure(i, weight=1)
        parent.columnconfigure(0, weight=1)

        # AEB
        aeb = self.LF(parent, 'AEB — Emergency Braking', C['red'])
        aeb.grid(row=0, column=0, sticky='nsew', pady=(0,3))
        aeb.columnconfigure(0, weight=1)

        self._aeb_state_var, self._aeb_state_lbl = self.datarow(aeb, 'State',    C['red'],    12)
        self._aeb_ttc_var,   _                   = self.datarow(aeb, 'TTC',      C['orange'])
        self._aeb_score_var, _                   = self.datarow(aeb, 'Fusion',   C['yellow'])
        self._aeb_cam_var,   _                   = self.datarow(aeb, 'Cam Conf', C['green'])

        ind_aeb = self.F(aeb); ind_aeb.pack(pady=4)
        self._aeb_dots = {}
        for k, l, c in [('warn','WARNING',C['yellow']),('partial','PARTIAL',C['orange']),
                         ('hard','HARD',C['red']),('stop','STOP',C['red'])]:
            self._aeb_dots[k] = self.dot(ind_aeb, l, c)

        # TTC bar
        tr = self.F(aeb); tr.pack(fill='x', padx=8, pady=2)
        self.L(tr, 'TTC:', size=9, width=6, anchor='w').pack(side='left')
        self._ttc_cv, self._ttc_bar = self.hbar(tr, w=180, color=C['green'])
        self._ttc_cv.pack(side='left', padx=4, fill='x', expand=True)

        # ACC
        acc = self.LF(parent, 'ACC — Adaptive Cruise', C['orange'])
        acc.grid(row=1, column=0, sticky='nsew', pady=3)

        self._acc_state_var, self._acc_state_lbl = self.datarow(acc, 'State', C['orange'], 12)
        self._acc_gap_var,   _                   = self.datarow(acc, 'Gap',   C['cyan'])

        ind_acc = self.F(acc); ind_acc.pack(pady=4)
        self._acc_dots = {}
        for k, l, c in [('catch','CATCH',C['cyan']),('follow','FOLLOW',C['green']),
                         ('hard','HARD',C['red']),('stop','STOP',C['red'])]:
            self._acc_dots[k] = self.dot(ind_acc, l, c)

        # Gap bar
        gr = self.F(acc); gr.pack(fill='x', padx=8, pady=2)
        self.L(gr, 'Gap:', size=9, width=6, anchor='w').pack(side='left')
        self._gap_cv, self._gap_bar = self.hbar(gr, w=180, color=C['cyan'])
        self._gap_cv.pack(side='left', padx=4, fill='x', expand=True)

        # LKA
        lka = self.LF(parent, 'LKA — Lane Keep Assist', C['green'])
        lka.grid(row=2, column=0, sticky='nsew', pady=(3,0))

        self._lka_mode_var,  self._lka_mode_lbl  = self.datarow(lka, 'Recovery', C['green'], 11)
        self._lka_err_var,   self._lka_err_lbl   = self.datarow(lka, 'Lat Error',C['cyan'])
        self._lka_steer_var, _                   = self.datarow(lka, 'Steer Cmd',C['yellow'])
        self._lka_conf_var,  _                   = self.datarow(lka, 'Confidence',C['lgrey'])

        # Lateral error bar (centre = 0)
        er = self.F(lka); er.pack(fill='x', padx=8, pady=4)
        self.L(er, 'L◄', size=8, color=C['lgrey']).pack(side='left')
        self._err_cv = tk.Canvas(er, height=16, bg='#0d1f30',
                                 highlightthickness=1,
                                 highlightbackground=C['grey'])
        self._err_cv.pack(side='left', fill='x', expand=True, padx=4)
        self._err_bar    = self._err_cv.create_rectangle(0,2,0,14, fill=C['cyan'], outline='')
        self._err_centre = self._err_cv.create_line(0,0,0,16, fill=C['yellow'], width=2)
        self.L(er, '►R', size=8, color=C['lgrey']).pack(side='left')

    # ── UPDATE ────────────────────────────────────────────────────────────────
    def _update(self):
        with S.lock:
            lidar   = S.lidar_m;      tof_r    = S.tof_right_m
            tof_l   = S.tof_left_m;   gyro     = S.gyro_z
            az      = S.accel_z;      spd      = S.vehicle_spd
            mode    = S.mode
            aeb_st  = S.aeb_state;    aeb_ttc  = S.aeb_ttc
            aeb_sc  = S.aeb_score;    aeb_cc   = S.aeb_cam_conf
            acc_st  = S.acc_state;    acc_gap  = S.acc_gap
            lka_mod = S.lka_mode;     lka_err  = S.lka_err_m
            lka_str = S.lka_steer;    lka_con  = S.lka_conf
            arb_st  = S.arb_state;    arb_spd  = S.arb_speed
            arb_str = S.arb_steer;    can_st   = S.can_status
            can_220 = S.can_rx_220;   can_310  = S.can_rx_310
            can_320 = S.can_rx_320
            online  = S.connected and (time.time() - S.last_t < 3.0)
            hist    = list(S.history)
            dbg     = S.debug_img

        # Time
        self._time_lbl.config(text=time.strftime('%H:%M:%S'))

        # Connection
        self._conn_lbl.config(
            text='● ONLINE' if online else '● OFFLINE',
            fg=C['green'] if online else C['red'])

        # Mode
        mc = {'MANUAL':C['cyan'],'AUTO':C['green'],'ESTOP':C['red']}.get(mode,C['yellow'])
        self._mode_lbl.config(text=f'MODE: {mode}', fg=mc)

        # ── Sensors ───────────────────────────────────────────────────────────
        lidar_s = f'{lidar:.2f} m' if lidar < 8.0 else '∞  clear'
        lc = C['red'] if lidar<0.5 else C['orange'] if lidar<1.5 else C['green']
        self._lidar_var.set(lidar_s)
        self._lidar_lbl.config(fg=lc)
        bw = int(min(lidar/8.0,1.0)*100) if lidar<8 else 100
        self._lidar_cv.coords(self._lidar_bar,0,0,bw,10)
        self._lidar_cv.itemconfig(self._lidar_bar,fill=lc)

        self._tof_r_var.set(f'{tof_r:.2f} m' if tof_r<2 else '∞')
        self._tof_l_var.set(f'{tof_l:.2f} m' if tof_l<2 else '∞')
        self._gyro_var.set(f'{math.degrees(gyro):+.1f} °/s')
        self._accel_var.set(f'{az:.2f} m/s²')

        self._spd_var.set(f'{spd:.2f} m/s')
        sw = int(min(spd/1.77,1.0)*100)
        sc = C['red'] if spd>1.4 else C['orange'] if spd>0.8 else C['green']
        self._spd_cv.coords(self._spd_bar,0,0,sw,10)
        self._spd_cv.itemconfig(self._spd_bar,fill=sc)

        # ── CAN ───────────────────────────────────────────────────────────────
        self._can_mode_var.set(can_st)
        self._can_rx_var.set(f'RX: enc={can_220} sbw={can_310} rpm={can_320}')

        # ── Arbiter ───────────────────────────────────────────────────────────
        arb_c = {
            'SIDE_EMRG':C['red'],'AEB_STOP':C['red'],'AEB_HARD':C['red'],
            'AEB_PARTIAL':C['orange'],'ACC_FOLLOW':C['cyan'],
            'LKA_STEER':C['green'],'MANUAL':C['yellow'],'IDLE':C['grey'],
        }.get(arb_st, C['white'])
        self._arb_state_var.set(arb_st)
        self._arb_state_lbl.config(fg=arb_c)
        self._arb_speed_var.set(f'{arb_spd:.3f} m/s')
        self._arb_steer_var.set(f'{arb_str*1000:+.0f} mrad'
                                if abs(arb_str)<10 else f'{arb_str:+.3f} rad')

        # ── Log ───────────────────────────────────────────────────────────────
        self._log_text.config(state='normal')
        self._log_text.delete('1.0','end')
        for h in hist: self._log_text.insert('end', h+'\n')
        self._log_text.config(state='disabled')

        # ── AEB ───────────────────────────────────────────────────────────────
        aeb_c = {'CLEAR':C['green'],'WARNING':C['yellow'],'PARTIAL_BRAKE':C['orange'],
                 'HARD_BRAKE':C['red'],'STOP':C['red'],'IDLE':C['grey']}.get(aeb_st,C['white'])
        self._aeb_state_var.set(aeb_st)
        self._aeb_state_lbl.config(fg=aeb_c)
        self._aeb_ttc_var.set(f'{aeb_ttc:.2f} s' if aeb_ttc<99 else '∞')
        self._aeb_score_var.set(f'{aeb_sc:.2f}')
        self._aeb_cam_var.set(f'{aeb_cc:.2f}')
        for k,active in [('warn','WARNING' in aeb_st),('partial','PARTIAL' in aeb_st),
                          ('hard','HARD' in aeb_st),('stop','STOP' in aeb_st)]:
            cv,circ,col = self._aeb_dots[k]
            cv.itemconfig(circ, fill=col if active else C['grey'])
        ttc_w = int(min(1.0, aeb_ttc/5.0)*180) if aeb_ttc<99 else 180
        self._ttc_cv.coords(self._ttc_bar,0,0,ttc_w,10)
        self._ttc_cv.itemconfig(self._ttc_bar,
            fill=C['red'] if aeb_ttc<0.5 else C['orange'] if aeb_ttc<1.5 else C['green'])

        # ── ACC ───────────────────────────────────────────────────────────────
        acc_c = {'CATCH_UP':C['cyan'],'FOLLOW':C['green'],'APPROACH':C['yellow'],
                 'HARD_BRAKE':C['red'],'STOP':C['red'],'IDLE':C['grey']}.get(acc_st,C['white'])
        self._acc_state_var.set(acc_st)
        self._acc_state_lbl.config(fg=acc_c)
        self._acc_gap_var.set(f'{acc_gap:.2f} m' if acc_gap<99 else '∞')
        for k,active in [('catch','CATCH' in acc_st),('follow','FOLLOW' in acc_st),
                          ('hard','HARD' in acc_st),('stop','STOP' in acc_st)]:
            cv,circ,col = self._acc_dots[k]
            cv.itemconfig(circ, fill=col if active else C['grey'])
        gw = int(min(acc_gap/3.0,1.0)*180) if acc_gap<99 else 180
        self._gap_cv.coords(self._gap_bar,0,0,gw,10)
        self._gap_cv.itemconfig(self._gap_bar,
            fill=C['red'] if acc_gap<0.4 else C['orange'] if acc_gap<0.8 else C['cyan'])

        # ── LKA ───────────────────────────────────────────────────────────────
        lka_c = {'BOTH_LANES':C['green'],'PREDICT':C['cyan'],
                 'SINGLE_LANE':C['orange'],'EMERGENCY_STOP':C['red'],
                 'NONE':C['grey']}.get(lka_mod,C['white'])
        self._lka_mode_var.set(lka_mod)
        self._lka_mode_lbl.config(fg=lka_c)
        ec = C['green'] if abs(lka_err)<0.03 else C['orange'] if abs(lka_err)<0.08 else C['red']
        self._lka_err_var.set(f'{lka_err*100:+.1f} cm')
        self._lka_err_lbl.config(fg=ec)
        self._lka_steer_var.set(f'{lka_str:+.0f} mrad')
        self._lka_conf_var.set(f'{lka_con:.2f}')
        # Error bar
        cw = self._err_cv.winfo_width()
        if cw > 10:
            mid = cw // 2
            pct = float(np.clip(lka_err/0.15, -1.0, 1.0))
            ex  = mid + int(pct * (mid-4))
            self._err_cv.coords(self._err_bar,
                min(mid,ex),2, max(mid,ex),14)
            self._err_cv.itemconfig(self._err_bar,
                fill=C['orange'] if pct<0 else C['cyan'])
            self._err_cv.coords(self._err_centre, mid,0, mid,16)

        # ── Stats bar ─────────────────────────────────────────────────────────
        self._stat_lidar.set(f'{lidar:.2f}m' if lidar<8 else '∞')
        self._stat_lka.set(f'{lka_err*100:+.1f}cm')
        self._stat_aeb.set(aeb_st[:8])
        self._stat_spd.set(f'{spd:.2f}m/s')

        # ── Camera image ──────────────────────────────────────────────────────
        if dbg is not None and HAS_IMG:
            cw = self._cam_canvas.winfo_width()
            ch = self._cam_canvas.winfo_height()
            if cw > 10 and ch > 10:
                img = dbg.resize((cw, ch), PILImage.LANCZOS)
                self._tk_debug = ImageTk.PhotoImage(image=img)
                self._cam_canvas.create_image(0,0,anchor='nw',image=self._tk_debug)

        self.root.after(100, self._update)

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    rclpy.init()
    node = DashboardNode()
    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

    root = tk.Tk()
    ADASGUI(root, node)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
