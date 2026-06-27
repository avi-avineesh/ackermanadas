#!/usr/bin/env python3
"""
dashboard_v4.py — Laptop ADAS dashboard (serial-bridge variant)

Full-window dark-theme Tkinter UI.
Communicates with the Pi (10.162.11.52) over WiFi ROS2 — both sides must
share the same ROS_DOMAIN_ID.

━━━ Subscriptions (all BEST_EFFORT for sensor topics) ━━━━━━━━━━━━━━━━━━━━━━
  /lane/debug_image   Image    BEST_EFFORT  camera view (320×240)
  /system/mode        String   RELIABLE     MANUAL / AUTO / EMERGENCY_STOP
  /system/aeb_state   String   RELIABLE     CLEAR/WARNING/PARTIAL/HARD/STOP
  /system/acc_state   String   RELIABLE     IDLE/APPROACH/FOLLOW/STOP
  /system/lka_state   String   RELIABLE     IDLE/ACTIVE/EMERGENCY
  /system/distance    Float32  BEST_EFFORT  lidar range in metres
  /system/ttc         Float32  BEST_EFFORT  Time-To-Collision in seconds
  /vehicle/heartbeat  String   BEST_EFFORT  serial-bridge heartbeat

━━━ Publications (all RELIABLE) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  /switch/autonomous  Bool    engage/disengage AUTO
  /switch/acc         Bool    toggle ACC
  /switch/lka         Bool    toggle LKA
  /adas/manual_cmd    Twist   20 Hz drive commands while button held
"""

import threading
import time
from collections import deque
from datetime import datetime

import tkinter as tk
from tkinter import font as tkfont

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String, Bool, Float32
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist

try:
    import numpy as np
    from PIL import Image as PILImage, ImageTk
    _IMG_OK = True
except ImportError:
    _IMG_OK = False

# ── Colour palette ────────────────────────────────────────────────────────────
BG         = '#12121f'
BG2        = '#1a1a2e'
BG3        = '#0f3460'
BG4        = '#0a0a18'
FG         = '#dde1e7'
FG2        = '#7a8090'
GREEN      = '#00e676'
BLUE       = '#2196f3'
RED        = '#f44336'
YELLOW     = '#ffeb3b'
CYAN       = '#00bcd4'
ORANGE     = '#ff9800'
WHITE      = '#ffffff'
DARK_BTN   = '#1e2030'
MASTER_ON  = '#1a3a1a'
MASTER_OFF = '#3a1a1a'

_MODE_COLOR = {
    'MANUAL':         GREEN,
    'AUTO':           BLUE,
    'EMERGENCY_STOP': RED,
}

# AEB zone colours — >40cm GREEN, 30-40cm YELLOW, 20-30cm ORANGE, <20cm RED
_AEB_COLOR = {
    'CLEAR':   GREEN,
    'WARNING': YELLOW,
    'PARTIAL': ORANGE,
    'HARD':    RED,
    'STOP':    RED,
}
_ACC_COLOR = {
    'IDLE':     FG2,
    'APPROACH': ORANGE,
    'FOLLOW':   GREEN,
    'STOP':     RED,
}
_LKA_COLOR = {
    'IDLE':      FG2,
    'ACTIVE':    GREEN,
    'EMERGENCY': RED,
}

# TTC colour thresholds (seconds)
_TTC_COLOR_SAFE    = GREEN    # TTC > 3 s
_TTC_COLOR_WARN    = YELLOW   # 0.5 s < TTC ≤ 3 s
_TTC_COLOR_DANGER  = RED      # TTC ≤ 0.5 s

# Map direction → (linear_x_sign, angular_z_sign)
_DIR_AXES = {
    'fwd':   ( 1.0,  0.0),
    'rev':   (-1.0,  0.0),
    'left':  ( 0.0,  1.0),
    'right': ( 0.0, -1.0),
}

# Heartbeat timeout for serial-bridge indicator
_HB_TIMEOUT_S = 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard application  (Tk main thread only)
# ─────────────────────────────────────────────────────────────────────────────
class DashboardApp:

    def __init__(self, root: tk.Tk, node: '_LazyRosNode'):
        self._root = root
        self._node = node

        # ── Autonomous state ─────────────────────────────────────────────────
        self._mode      = 'MANUAL'
        self._auto_on   = False
        self._acc_on    = False
        self._lka_on    = False

        # ── ADAS subsystem states ────────────────────────────────────────────
        self._aeb_state = 'CLEAR'
        self._acc_state = 'IDLE'
        self._lka_state = 'IDLE'
        self._distance  = 0.65      # metres
        self._ttc       = -1.0      # seconds; -1 = N/A

        # ── Master / manual drive state ──────────────────────────────────────
        self._master_on      = False
        self._max_speed_mms  = 200.0
        self._max_steer_rad  = 1.0
        self._held: dict[str, bool] = {d: False for d in _DIR_AXES}
        self._dpad_btns: dict[str, tk.Button] = {}
        # after() IDs for keyboard release debounce (handles X11 auto-repeat)
        self._kr_timers: dict[str, str] = {}
        # Background drive thread
        self._drive_running = True

        # ── Display state ────────────────────────────────────────────────────
        self._cmd_speed_ms  = 0.0
        self._cmd_steer_rad = 0.0
        self._last_hb_time  = time.monotonic()
        self._blink_phase   = False
        self._photo         = None
        self._last_img_t    = 0.0
        self._events        = deque(maxlen=10)

        root.title('ADAS Dashboard v4  |  Pi 10.162.11.52')
        root.configure(bg=BG)
        try:
            root.state('zoomed')
        except tk.TclError:
            root.attributes('-zoomed', True)

        self._build_ui()

        # ── WASD keyboard bindings: hold = drive, release = stop ──────────────
        for key, direction in (
                ('w', 'fwd'), ('W', 'fwd'),
                ('s', 'rev'), ('S', 'rev'),
                ('a', 'left'), ('A', 'left'),
                ('d', 'right'), ('D', 'right')):
            root.bind(f'<KeyPress-{key}>',
                      lambda e, dr=direction: self._kbd_press(dr))
            root.bind(f'<KeyRelease-{key}>',
                      lambda e, dr=direction: self._kbd_release(dr))
        root.bind('<KeyPress-space>',   lambda e: self._release_all())
        root.bind('<KeyRelease-space>', lambda e: None)

        self._add_event('Dashboard v4 online')
        self._blink_tick()
        self._start_drive_thread()
        self._switch_tick()
        self._redraw_tick()

    # ─────────────────────────────────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        r = self._root
        r.columnconfigure(0, weight=22, uniform='c')
        r.columnconfigure(1, weight=30, uniform='c')
        r.columnconfigure(2, weight=22, uniform='c')
        r.rowconfigure(0, weight=1)

        self._pL = tk.Frame(r, bg=BG,  padx=10, pady=8)
        self._pC = tk.Frame(r, bg=BG2, padx=10, pady=8)
        self._pR = tk.Frame(r, bg=BG,  padx=10, pady=8)
        self._pL.grid(row=0, column=0, sticky='nsew')
        self._pC.grid(row=0, column=1, sticky='nsew')
        self._pR.grid(row=0, column=2, sticky='nsew')

        self._build_left()
        self._build_centre()
        self._build_right()

    # ── helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _font(size=10, bold=False):
        return tkfont.Font(family='Courier New', size=size,
                           weight='bold' if bold else 'normal')

    def _lbl(self, parent, text, fg=FG, size=10, bold=False, **kw):
        return tk.Label(parent, text=text, fg=fg,
                        bg=kw.pop('bg', parent['bg']),
                        font=self._font(size, bold), **kw)

    def _section(self, parent, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=BG3, padx=6, pady=4)
        outer.pack(fill='x', pady=4)
        self._lbl(outer, f'  {title}', fg=CYAN, size=8,
                  bold=True, bg=BG3).pack(anchor='w')
        inner = tk.Frame(outer, bg=BG3)
        inner.pack(fill='x')
        return inner

    def _bar(self, parent, h=22) -> tk.Canvas:
        c = tk.Canvas(parent, height=h, bg=BG4,
                      highlightthickness=1, highlightbackground=BG3)
        c.pack(fill='x', pady=2)
        return c

    # ── LEFT panel ────────────────────────────────────────────────────────────
    def _build_left(self):
        p = self._pL

        self._master_btn = tk.Button(
            p, text='⏻   MASTER   OFF',
            font=self._font(13, True),
            bg=MASTER_OFF, fg='#ff6666',
            activebackground=GREEN, activeforeground='black',
            relief='raised', bd=3, pady=10,
            command=self._toggle_master)
        self._master_btn.pack(fill='x', pady=(0, 5))

        mf = self._section(p, 'VEHICLE MODE')
        self._mode_lbl = self._lbl(mf, 'MANUAL', fg=GREEN,
                                    size=20, bold=True, bg=BG3)
        self._mode_lbl.pack(pady=6)

        self._auto_btn = tk.Button(
            p, text='▶  ENGAGE AUTONOMOUS',
            font=self._font(11, True),
            bg=DARK_BTN, fg=WHITE,
            activebackground=BLUE, activeforeground=WHITE,
            relief='raised', bd=2, pady=9,
            command=self._toggle_auto)
        self._auto_btn.pack(fill='x', pady=4)

        ff = self._section(p, 'FEATURE SWITCHES')
        self._acc_btn = tk.Button(
            ff, text='  ACC   OFF  ', font=self._font(10, True),
            bg=DARK_BTN, fg=FG2, state='disabled',
            relief='raised', bd=2, pady=6,
            command=self._toggle_acc)
        self._acc_btn.pack(fill='x', pady=2)

        self._lka_btn = tk.Button(
            ff, text='  LKA   OFF  ', font=self._font(10, True),
            bg=DARK_BTN, fg=FG2, state='disabled',
            relief='raised', bd=2, pady=6,
            command=self._toggle_lka)
        self._lka_btn.pack(fill='x', pady=2)

        self._build_drive_panel(p)

        self._estop_btn = tk.Button(
            p, text='⬛  EMERGENCY STOP',
            font=self._font(11, True),
            bg=RED, fg=WHITE,
            activebackground='#c62828', activeforeground=WHITE,
            relief='raised', bd=3, pady=11,
            command=self._emergency_stop)
        self._estop_btn.pack(fill='x', pady=8)

    def _build_drive_panel(self, parent):
        outer = tk.Frame(parent, bg=BG3, padx=6, pady=4)
        outer.pack(fill='x', pady=4)
        self._lbl(outer, '  MANUAL DRIVE  (WASD / Space)',
                  fg=CYAN, size=8, bold=True, bg=BG3).pack(anchor='w')

        dpad = tk.Frame(outer, bg=BG3)
        dpad.pack(pady=3)

        def _mk(text, direction, gr, gc):
            btn = tk.Button(dpad, text=text,
                            font=self._font(11, True),
                            bg=DARK_BTN, fg=FG,
                            activebackground=GREEN, activeforeground='black',
                            width=4, height=2, relief='raised', bd=2,
                            takefocus=False)
            btn.grid(row=gr, column=gc, padx=3, pady=2)
            btn.bind('<ButtonPress-1>',
                     lambda e, d=direction, b=btn: self._dpad_press(d, b))
            btn.bind('<ButtonRelease-1>',
                     lambda e, d=direction, b=btn: self._dpad_release(d, b))
            self._dpad_btns[direction] = btn

        _mk('▲\nW',  'fwd',   0, 1)
        _mk('◄\nA',  'left',  1, 0)
        _mk('►\nD',  'right', 1, 2)
        _mk('▼\nS',  'rev',   2, 1)

        stop_btn = tk.Button(dpad, text='■\nSPC',
                             font=self._font(10, True),
                             bg='#2a1818', fg=RED,
                             activebackground=RED, activeforeground=WHITE,
                             width=4, height=2, relief='raised', bd=2,
                             takefocus=False,
                             command=self._release_all)
        stop_btn.grid(row=1, column=1, padx=3, pady=2)
        self._dpad_stop = stop_btn

        # Speed slider
        sf = tk.Frame(outer, bg=BG3)
        sf.pack(fill='x', pady=(5, 1))
        sr = tk.Frame(sf, bg=BG3); sr.pack(fill='x')
        self._lbl(sr, 'MAX SPEED', fg=FG2, size=8, bold=True, bg=BG3).pack(side='left')
        self._spd_val = self._lbl(sr, '200 mm/s', fg=GREEN, size=8, bold=True, bg=BG3)
        self._spd_val.pack(side='right')
        self._spd_scale = tk.Scale(
            sf, from_=50, to=500, orient='horizontal',
            resolution=10, showvalue=False,
            bg=BG3, fg=FG, troughcolor=BG4,
            activebackground=GREEN, highlightthickness=0,
            command=lambda v: self._on_spd_scale(v))
        self._spd_scale.set(200)
        self._spd_scale.pack(fill='x')

        # Steer slider
        stf = tk.Frame(outer, bg=BG3)
        stf.pack(fill='x', pady=(3, 1))
        str_r = tk.Frame(stf, bg=BG3); str_r.pack(fill='x')
        self._lbl(str_r, 'MAX STEER', fg=FG2, size=8, bold=True, bg=BG3).pack(side='left')
        self._str_val = self._lbl(str_r, '1.00 rad', fg=CYAN, size=8, bold=True, bg=BG3)
        self._str_val.pack(side='right')
        self._str_scale = tk.Scale(
            stf, from_=30, to=250, orient='horizontal',
            resolution=5, showvalue=False,
            bg=BG3, fg=FG, troughcolor=BG4,
            activebackground=CYAN, highlightthickness=0,
            command=lambda v: self._on_str_scale(v))
        self._str_scale.set(100)   # ×0.01 = 1.00 rad
        self._str_scale.pack(fill='x')

    # ── CENTRE panel ──────────────────────────────────────────────────────────
    def _build_centre(self):
        p = self._pC

        # Camera
        cf = self._section(p, 'LANE CAMERA  320×240  (10 Hz)')
        self._cam = tk.Canvas(cf, width=320, height=240, bg='#000010',
                              highlightthickness=2, highlightbackground=BG3)
        self._cam.pack(pady=4)
        self._cam_nosig = self._cam.create_text(
            160, 120, text='NO SIGNAL', fill=FG2,
            font=self._font(12, True))

        # Distance section
        df = self._section(p, 'LIDAR DISTANCE')

        self._dist_num_lbl = self._lbl(df, '--.- cm',
                                        fg=FG, size=20, bold=True, bg=BG3)
        self._dist_num_lbl.pack(pady=4)

        self._aeb_lbl = self._lbl(df, 'AEB:  CLEAR',
                                   fg=GREEN, size=11, bold=False, bg=BG3)
        self._aeb_lbl.pack(pady=2)

        self._dist_bar = self._bar(df, h=28)

        # TTC section
        tf = self._section(p, 'TIME-TO-COLLISION')

        self._ttc_lbl = self._lbl(tf, 'TTC:  N/A',
                                   fg=FG2, size=14, bold=True, bg=BG3)
        self._ttc_lbl.pack(pady=4)

    # ── RIGHT panel ───────────────────────────────────────────────────────────
    def _build_right(self):
        p = self._pR

        lf = self._section(p, 'LED INDICATORS')
        grid = tk.Frame(lf, bg=BG3)
        grid.pack(pady=4)
        _led_defs = [
            ('SYS',      WHITE,  'SYS'),
            ('MANUAL',   GREEN,  'MAN'),
            ('AUTO',     BLUE,   'AUTO'),
            ('LKA',      GREEN,  'LKA'),
            ('ACC',      WHITE,  'ACC'),
            ('AEB_WARN', YELLOW, 'WARN'),
            ('AEB_STOP', RED,    'STOP'),
        ]
        self._led_ovals: dict = {}
        for i, (key, color, label) in enumerate(_led_defs):
            cell = tk.Frame(grid, bg=BG3, padx=5, pady=2)
            cell.grid(row=i // 4, column=i % 4)
            c = tk.Canvas(cell, width=24, height=24, bg=BG3,
                          highlightthickness=0)
            c.pack()
            oval = c.create_oval(2, 2, 22, 22,
                                  fill='#2a2a3a', outline=color, width=1)
            self._lbl(cell, label, size=7, fg=FG2, bg=BG3).pack()
            self._led_ovals[key] = (c, oval, color)

        sf = self._section(p, 'COMMAND SPEED')
        self._speed_lbl = self._lbl(sf, '0 mm/s',
                                     fg=GREEN, size=13, bold=True, bg=BG3)
        self._speed_lbl.pack()
        self._speed_bar = self._bar(sf, h=20)

        stf = self._section(p, 'COMMAND STEER')
        self._steer_lbl = self._lbl(stf, '0.000 rad',
                                     fg=CYAN, size=10, bold=True, bg=BG3)
        self._steer_lbl.pack()
        self._steer_bar = self._bar(stf, h=20)

        sl = self._section(p, 'SYSTEM STATES')
        row_acc = tk.Frame(sl, bg=BG3); row_acc.pack(fill='x', pady=1)
        self._lbl(row_acc, 'ACC: ', fg=FG2, size=9, bg=BG3).pack(side='left')
        self._acc_state_lbl = self._lbl(row_acc, 'IDLE',
                                         fg=FG2, size=9, bold=True, bg=BG3)
        self._acc_state_lbl.pack(side='left')

        row_lka = tk.Frame(sl, bg=BG3); row_lka.pack(fill='x', pady=1)
        self._lbl(row_lka, 'LKA: ', fg=FG2, size=9, bg=BG3).pack(side='left')
        self._lka_state_lbl = self._lbl(row_lka, 'IDLE',
                                         fg=FG2, size=9, bold=True, bg=BG3)
        self._lka_state_lbl.pack(side='left')

        hf = self._section(p, 'ECU HEARTBEAT')
        hb_row = tk.Frame(hf, bg=BG3); hb_row.pack(fill='x', pady=2)
        self._hb_canvas = tk.Canvas(hb_row, width=16, height=16, bg=BG3,
                                     highlightthickness=0)
        self._hb_canvas.pack(side='left', padx=4)
        self._hb_oval = self._hb_canvas.create_oval(
            1, 1, 15, 15, fill=FG2, outline='')
        self._hb_lbl = self._lbl(hb_row, 'Waiting…', fg=FG2, size=9, bg=BG3)
        self._hb_lbl.pack(side='left')

        ef = self._section(p, 'EVENT LOG')
        self._event_box = tk.Text(
            ef, height=10, bg=BG4, fg=FG,
            font=self._font(8), state='disabled',
            relief='flat', wrap='word', padx=4)
        self._event_box.pack(fill='both', expand=True, pady=2)
        self._event_box.tag_config('ok',    foreground=GREEN)
        self._event_box.tag_config('warn',  foreground=YELLOW)
        self._event_box.tag_config('error', foreground=RED)

    # ─────────────────────────────────────────────────────────────────────────
    # Button handlers
    # ─────────────────────────────────────────────────────────────────────────
    def _toggle_master(self):
        self._master_on = not self._master_on
        if self._master_on:
            self._master_btn.config(text='⏻   MASTER   ON ',
                                     bg=MASTER_ON, fg=GREEN)
            self._add_event('Master ON', 'ok')
        else:
            self._master_btn.config(text='⏻   MASTER   OFF',
                                     bg=MASTER_OFF, fg='#ff6666')
            self._release_all()
            self._add_event('Master OFF', 'warn')
        self._refresh_controls()

    def _toggle_auto(self):
        if not self._master_on:
            return
        was_on = self._auto_on
        self._auto_on = not self._auto_on
        if was_on and not self._auto_on:
            # AUTO → MANUAL: send zero cmd immediately and disengage ACC/LKA
            self._node.pub_manual_cmd(Twist())
            self._acc_on = False
            self._lka_on = False
            self._node.pub('acc', False)
            self._node.pub('lka', False)
        self._node.pub('auto', self._auto_on)
        tag = 'ok' if self._auto_on else 'warn'
        self._add_event(
            f'AUTO {"ENGAGED" if self._auto_on else "DISENGAGED"}', tag)
        self._refresh_controls()

    def _toggle_acc(self):
        if not self._master_on or not (self._auto_on or self._mode == 'AUTO'):
            return
        self._acc_on = not self._acc_on
        self._node.pub('acc', self._acc_on)
        self._add_event(f'ACC {"ON" if self._acc_on else "OFF"}',
                         'ok' if self._acc_on else 'warn')
        self._refresh_controls()

    def _toggle_lka(self):
        if not self._master_on or not (self._auto_on or self._mode == 'AUTO'):
            return
        self._lka_on = not self._lka_on
        self._node.pub('lka', self._lka_on)
        self._add_event(f'LKA {"ON" if self._lka_on else "OFF"}',
                         'ok' if self._lka_on else 'warn')
        self._refresh_controls()

    def _emergency_stop(self):
        self._auto_on = False
        self._acc_on  = False
        self._lka_on  = False
        self._release_all()
        self._node.pub_manual_cmd(Twist())  # immediate zero
        self._node.pub('auto', False)
        self._node.pub('acc',  False)
        self._node.pub('lka',  False)
        self._add_event('!!! EMERGENCY STOP !!!', 'error')
        self._refresh_controls()

    def _refresh_controls(self):
        is_auto   = self._mode == 'AUTO'
        master    = self._master_on
        can_drive = master and self._mode == 'MANUAL'

        if not master:
            self._auto_btn.config(state='disabled', text='▶  ENGAGE AUTONOMOUS',
                                   bg=DARK_BTN, fg=FG2)
        elif self._auto_on or is_auto:
            self._auto_btn.config(state='normal',
                                   text='■  DISENGAGE AUTONOMOUS',
                                   bg=BLUE, fg=WHITE)
        else:
            self._auto_btn.config(state='normal',
                                   text='▶  ENGAGE AUTONOMOUS',
                                   bg=DARK_BTN, fg=WHITE)

        # ACC/LKA enabled as soon as master + user engaged auto (don't wait for
        # mode echo from Pi, which may lag by a ROS spin cycle)
        if master and (self._auto_on or is_auto):
            self._acc_btn.config(
                state='normal',
                bg=GREEN   if self._acc_on else DARK_BTN,
                fg='black' if self._acc_on else FG2,
                text=f'  ACC   {"ON " if self._acc_on else "OFF"}  ')
            self._lka_btn.config(
                state='normal',
                bg=CYAN    if self._lka_on else DARK_BTN,
                fg='black' if self._lka_on else FG2,
                text=f'  LKA   {"ON " if self._lka_on else "OFF"}  ')
        else:
            self._acc_btn.config(state='disabled', bg=DARK_BTN, fg=FG2,
                                  text='  ACC   OFF  ')
            self._lka_btn.config(state='disabled', bg=DARK_BTN, fg=FG2,
                                  text='  LKA   OFF  ')

        for d, btn in self._dpad_btns.items():
            btn.config(state='normal' if can_drive else 'disabled',
                       fg=FG if can_drive else FG2)
        self._dpad_stop.config(state='normal' if can_drive else 'disabled')
        self._spd_scale.config(state='normal' if master else 'disabled')
        self._str_scale.config(state='normal' if master else 'disabled')

    # ─────────────────────────────────────────────────────────────────────────
    # D-pad / keyboard drive
    # ─────────────────────────────────────────────────────────────────────────
    def _dpad_press(self, direction: str, btn: tk.Button):
        if not self._master_on or self._mode != 'MANUAL':
            return
        self._held[direction] = True
        btn.config(bg=GREEN, fg='black')

    def _dpad_release(self, direction: str, btn: tk.Button):
        self._held[direction] = False
        btn.config(bg=DARK_BTN, fg=FG)

    def _kbd_press(self, direction: str):
        if not self._master_on or self._mode != 'MANUAL':
            return
        # Cancel any pending release — handles X11 key auto-repeat spurious releases
        if direction in self._kr_timers:
            self._root.after_cancel(self._kr_timers.pop(direction))
        if not self._held[direction]:
            self._held[direction] = True
            if (btn := self._dpad_btns.get(direction)):
                btn.config(bg=GREEN, fg='black')

    def _kbd_release(self, direction: str):
        # Small delay before committing release filters X11 auto-repeat false fires
        if direction in self._kr_timers:
            self._root.after_cancel(self._kr_timers[direction])
        self._kr_timers[direction] = self._root.after(
            30, self._kbd_release_commit, direction)

    def _kbd_release_commit(self, direction: str):
        self._kr_timers.pop(direction, None)
        self._held[direction] = False
        if (btn := self._dpad_btns.get(direction)):
            btn.config(bg=DARK_BTN, fg=FG)

    def _release_all(self):
        for d in list(self._kr_timers):
            self._root.after_cancel(self._kr_timers.pop(d))
        for d in _DIR_AXES:
            self._held[d] = False
        for btn in self._dpad_btns.values():
            btn.config(bg=DARK_BTN, fg=FG)

    def _on_spd_scale(self, val):
        self._max_speed_mms = float(val)
        self._spd_val.config(text=f'{int(float(val))} mm/s')

    def _on_str_scale(self, val):
        rad = float(val) * 0.01
        self._max_steer_rad = rad
        self._str_val.config(text=f'{rad:.2f} rad')

    # ─────────────────────────────────────────────────────────────────────────
    # 20 Hz manual drive background thread
    # Publishes at 20 Hz only while a key is held.
    # On transition to no-keys-held: publishes exactly ONE zero Twist, then
    # goes idle (no further traffic until a key is pressed again).
    # ─────────────────────────────────────────────────────────────────────────
    def _start_drive_thread(self):
        def _loop():
            was_driving = False
            interval    = 1.0 / 20.0   # 50 ms

            while self._drive_running:
                t0 = time.monotonic()

                if self._master_on and self._mode == 'MANUAL':
                    any_held = any(self._held.values())
                    if any_held:
                        lin = ang = 0.0
                        for d, (lx, az) in _DIR_AXES.items():
                            if self._held[d]:
                                lin += lx * (self._max_speed_mms / 1000.0)
                                ang += az * self._max_steer_rad
                        max_s = self._max_speed_mms / 1000.0
                        tw = Twist()
                        tw.linear.x  = max(-max_s, min(lin, max_s))
                        tw.angular.z = max(-self._max_steer_rad,
                                          min(ang, self._max_steer_rad))
                        self._node.pub_manual_cmd(tw)
                        self._cmd_speed_ms  = tw.linear.x
                        self._cmd_steer_rad = tw.angular.z
                        was_driving = True
                    elif was_driving:
                        # Keys just released — one final zero, then go idle
                        self._node.pub_manual_cmd(Twist())
                        self._cmd_speed_ms  = 0.0
                        self._cmd_steer_rad = 0.0
                        was_driving = False
                else:
                    if was_driving:
                        # Master turned off or mode changed while driving
                        self._node.pub_manual_cmd(Twist())
                        self._cmd_speed_ms  = 0.0
                        self._cmd_steer_rad = 0.0
                        was_driving = False

                elapsed = time.monotonic() - t0
                rem = interval - elapsed
                if rem > 0.0:
                    time.sleep(rem)

        t = threading.Thread(target=_loop, daemon=True, name='manual_drive')
        t.start()

    # ─────────────────────────────────────────────────────────────────────────
    # 5 Hz switch heartbeat — keeps /switch/* alive on the Pi side
    # ─────────────────────────────────────────────────────────────────────────
    def _switch_tick(self):
        if self._master_on:
            if self._auto_on:
                self._node.pub('auto', True)
            if self._acc_on:
                self._node.pub('acc', True)
            if self._lka_on:
                self._node.pub('lka', True)
        self._root.after(200, self._switch_tick)

    # ─────────────────────────────────────────────────────────────────────────
    # Blink tick (4 Hz → 2 Hz blink on AEB_WARN LED)
    # ─────────────────────────────────────────────────────────────────────────
    def _blink_tick(self):
        self._blink_phase = not self._blink_phase
        self._root.after(250, self._blink_tick)

    # ─────────────────────────────────────────────────────────────────────────
    # Apply methods  (called on Tk thread via root.after)
    # ─────────────────────────────────────────────────────────────────────────
    def _apply_mode(self, mode: str):
        prev = self._mode
        self._mode = mode
        color = _MODE_COLOR.get(mode, FG)
        self._mode_lbl.config(text=mode, fg=color)
        if mode != prev:
            if prev == 'AUTO' and mode != 'AUTO':
                # System left AUTO (emergency, external override, etc.)
                # Send zero immediately and reset all auto flags
                self._node.pub_manual_cmd(Twist())
                if self._auto_on:
                    self._node.pub('auto', False)
                if self._acc_on:
                    self._node.pub('acc', False)
                if self._lka_on:
                    self._node.pub('lka', False)
                self._auto_on = False
                self._acc_on  = False
                self._lka_on  = False
            elif prev == 'MANUAL' and mode != 'AUTO':
                self._release_all()
            tag = ('error' if mode == 'EMERGENCY_STOP' else
                   ('ok'   if mode == 'AUTO'            else 'warn'))
            self._add_event(f'Mode → {mode}', tag)
        self._refresh_controls()

    def _apply_aeb(self, aeb: str):
        if aeb != self._aeb_state:
            self._aeb_state = aeb
        color = _AEB_COLOR.get(aeb, GREEN)
        # STOP shown bold; HARD and below normal weight
        bold = (aeb == 'STOP')
        self._aeb_lbl.config(
            text=f'AEB:  {aeb}', fg=color,
            font=self._font(11, bold))

    def _apply_acc(self, acc: str):
        self._acc_state = acc
        color = _ACC_COLOR.get(acc, FG2)
        self._acc_state_lbl.config(text=acc, fg=color)

    def _apply_lka(self, lka: str):
        self._lka_state = lka
        color = _LKA_COLOR.get(lka, FG2)
        self._lka_state_lbl.config(text=lka, fg=color)

    def _apply_distance(self, dist: float):
        self._distance = dist
        self._dist_num_lbl.config(text=f'{dist * 100:.1f} cm')
        self._draw_dist_bar(dist)

    def _apply_ttc(self, ttc: float):
        self._ttc = ttc
        if ttc < 0.0:
            self._ttc_lbl.config(text='TTC:  N/A', fg=FG2)
        elif ttc <= 0.5:
            self._ttc_lbl.config(text=f'TTC:  {ttc:.1f} s', fg=_TTC_COLOR_DANGER)
        elif ttc <= 3.0:
            self._ttc_lbl.config(text=f'TTC:  {ttc:.1f} s', fg=_TTC_COLOR_WARN)
        else:
            self._ttc_lbl.config(text=f'TTC:  {ttc:.1f} s', fg=_TTC_COLOR_SAFE)

    def _apply_heartbeat(self, _data: str):
        self._last_hb_time = time.monotonic()

    def _apply_image(self, pil_img):
        if not _IMG_OK:
            return
        photo = ImageTk.PhotoImage(pil_img)
        self._cam.delete('all')
        self._cam.create_image(0, 0, anchor='nw', image=photo)
        self._photo = photo

    # ─────────────────────────────────────────────────────────────────────────
    # Drawing helpers
    # ─────────────────────────────────────────────────────────────────────────
    def _draw_dist_bar(self, dist: float):
        # Bar colour tracks AEB zone
        color = _AEB_COLOR.get(self._aeb_state, GREEN)
        c = self._dist_bar
        c.update_idletasks()
        w = c.winfo_width() or 300
        h = 28
        c.delete('all')
        c.create_rectangle(0, 0, w, h, fill=BG4, outline='')
        fill_w = max(int(min(dist / 0.65, 1.0) * w), 4)
        c.create_rectangle(2, 3, fill_w, h - 3, fill=color, outline='')
        c.create_text(w // 2, h // 2,
                      text=f'{dist * 100:.1f} cm  |  {self._aeb_state}',
                      fill=WHITE, font=self._font(8, True))

    def _draw_speed_bar(self, speed_ms: float):
        mms = speed_ms * 1000.0
        self._speed_lbl.config(text=f'{mms:+.1f} mm/s')
        c = self._speed_bar
        c.update_idletasks()
        w = c.winfo_width() or 200
        h = 20
        c.delete('all')
        c.create_rectangle(0, 0, w, h, fill=BG4, outline='')
        frac   = min(abs(speed_ms) / 0.5, 1.0)
        fill_w = max(int(frac * w), 2)
        col    = GREEN if speed_ms >= 0 else ORANGE
        c.create_rectangle(2, 3, fill_w, h - 3, fill=col, outline='')

    def _draw_steer_bar(self, steer_rad: float):
        self._steer_lbl.config(text=f'{steer_rad:+.3f} rad')
        c = self._steer_bar
        c.update_idletasks()
        w   = c.winfo_width() or 200
        h   = 20
        mid = w // 2
        c.delete('all')
        c.create_rectangle(0, 0, w, h, fill=BG4, outline='')
        c.create_line(mid, 0, mid, h, fill='#444466', width=1)
        norm    = max(-1.0, min(steer_rad / 2.5, 1.0))
        bar_end = mid + int(norm * mid)
        col     = CYAN if norm >= 0 else ORANGE
        x0, x1  = (mid, bar_end) if norm >= 0 else (bar_end, mid)
        if x0 != x1:
            c.create_rectangle(x0, 3, x1, h - 3, fill=col, outline='')

    def _update_leds(self):
        mode    = self._mode
        aeb     = self._aeb_state
        hb_age  = time.monotonic() - self._last_hb_time
        hb_ok   = hb_age < _HB_TIMEOUT_S

        states = {
            'SYS':      hb_ok,
            'MANUAL':   mode == 'MANUAL',
            'AUTO':     mode == 'AUTO',
            'LKA':      self._lka_state == 'ACTIVE',
            'ACC':      self._acc_state != 'IDLE',
            # WARN LED blinks at 2 Hz for both WARNING and PARTIAL zones
            'AEB_WARN': aeb in ('WARNING', 'PARTIAL') and self._blink_phase,
            # STOP LED solid red for HARD or STOP
            'AEB_STOP': aeb in ('HARD', 'STOP'),
        }
        for key, (c, oval, color) in self._led_ovals.items():
            on = states.get(key, False)
            c.itemconfig(oval, fill=color if on else '#2a2a3a')

        col = GREEN if hb_ok else RED
        txt = f'OK  ({hb_age * 1000:.0f} ms)' if hb_ok else \
              f'LOST  ({hb_age:.1f} s)'
        self._hb_canvas.itemconfig(self._hb_oval, fill=col)
        self._hb_lbl.config(text=txt, fg=col)

    # ─────────────────────────────────────────────────────────────────────────
    # Event log
    # ─────────────────────────────────────────────────────────────────────────
    def _add_event(self, msg: str, tag: str = ''):
        ts    = datetime.now().strftime('%H:%M:%S')
        entry = f'[{ts}]  {msg}\n'
        t = self._event_box
        t.config(state='normal')
        t.insert('1.0', entry, tag if tag else ())
        lines = int(t.index('end-1c').split('.')[0])
        if lines > 10:
            t.delete(f'{lines}.0', 'end')
        t.config(state='disabled')

    # ─────────────────────────────────────────────────────────────────────────
    # 10 Hz redraw tick
    # ─────────────────────────────────────────────────────────────────────────
    def _redraw_tick(self):
        self._draw_dist_bar(self._distance)
        self._draw_speed_bar(self._cmd_speed_ms)
        self._draw_steer_bar(self._cmd_steer_rad)
        self._update_leds()
        self._root.after(100, self._redraw_tick)


# ─────────────────────────────────────────────────────────────────────────────
# ROS2 node  (background thread — never touches Tk directly)
# ─────────────────────────────────────────────────────────────────────────────
class _LazyRosNode(Node):
    """Publishers created immediately; subscriptions wired in late_init()."""

    def __init__(self):
        super().__init__('dashboard_v4_node')
        self._app: DashboardApp | None = None

        rel = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                         history=HistoryPolicy.KEEP_LAST, depth=10)

        self._pub_auto = self.create_publisher(Bool,  '/switch/autonomous', rel)
        self._pub_acc  = self.create_publisher(Bool,  '/switch/acc',        rel)
        self._pub_lka  = self.create_publisher(Bool,  '/switch/lka',        rel)
        self._pub_cmd  = self.create_publisher(Twist, '/adas/manual_cmd',   rel)

    def pub(self, key: str, value: bool):
        msg = Bool(data=value)
        {'auto': self._pub_auto,
         'acc':  self._pub_acc,
         'lka':  self._pub_lka}[key].publish(msg)

    def pub_manual_cmd(self, twist: Twist):
        self._pub_cmd.publish(twist)

    def late_init(self, app: DashboardApp):
        self._app = app
        be  = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                         history=HistoryPolicy.KEEP_LAST, depth=1)
        rel = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                         history=HistoryPolicy.KEEP_LAST, depth=10)

        def _ui(fn, *a):
            app._root.after(0, fn, *a)

        self.create_subscription(String,  '/system/mode',
            lambda m: _ui(app._apply_mode, m.data), rel)
        self.create_subscription(String,  '/system/aeb_state',
            lambda m: _ui(app._apply_aeb, m.data), rel)
        self.create_subscription(String,  '/system/acc_state',
            lambda m: _ui(app._apply_acc, m.data), rel)
        self.create_subscription(String,  '/system/lka_state',
            lambda m: _ui(app._apply_lka, m.data), rel)
        self.create_subscription(Float32, '/system/distance',
            lambda m: _ui(app._apply_distance, float(m.data)), be)
        self.create_subscription(Float32, '/system/ttc',
            lambda m: _ui(app._apply_ttc, float(m.data)), be)
        self.create_subscription(String,  '/vehicle/heartbeat',
            lambda m: _ui(app._apply_heartbeat, m.data), be)
        self.create_subscription(Image,   '/lane/debug_image',
            lambda m: self._on_image(m, app), be)

    def _on_image(self, msg: Image, app: DashboardApp):
        if not _IMG_OK:
            return
        now = time.monotonic()
        if now - app._last_img_t < 0.09:
            return
        app._last_img_t = now
        try:
            arr = np.frombuffer(msg.data, dtype=np.uint8)
            if msg.encoding == 'bgr8':
                arr = arr.reshape(msg.height, msg.width, 3)[..., ::-1]
            elif msg.encoding == 'rgb8':
                arr = arr.reshape(msg.height, msg.width, 3)
            elif msg.encoding in ('mono8', '8UC1'):
                arr = np.stack(
                    [arr.reshape(msg.height, msg.width)] * 3, axis=-1)
            else:
                return
            img = PILImage.fromarray(arr.astype('uint8')).resize(
                (320, 240), PILImage.LANCZOS)
            app._root.after(0, app._apply_image, img)
        except Exception as exc:
            self.get_logger().debug(f'Image decode: {exc}')


# ─────────────────────────────────────────────────────────────────────────────
def main():
    rclpy.init()
    root     = tk.Tk()
    ros_node = _LazyRosNode()
    app      = DashboardApp(root, ros_node)
    ros_node.late_init(app)

    spin_thread = threading.Thread(
        target=rclpy.spin, args=(ros_node,), daemon=True)
    spin_thread.start()

    try:
        root.mainloop()
    finally:
        app._drive_running = False
        ros_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
