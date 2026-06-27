#!/usr/bin/env python3
"""
dashboard_v3.py
Laptop dashboard for RC ADAS vehicle.

Dark-theme Tkinter full-window UI.  ROS2 traffic flows over WiFi; the Pi
must share the same ROS_DOMAIN_ID.  Pi IP: 10.162.11.52

Subscribes:
  /lane/debug_image         sensor_msgs/Image   (BEST_EFFORT)
  /sensor/lidar_range       sensor_msgs/Range   (BEST_EFFORT)
  /system/mode              std_msgs/String     (RELIABLE)
  /system/status            std_msgs/String     (RELIABLE)
  /led/states               std_msgs/String     (RELIABLE)
  /system/watchdog          std_msgs/String     (RELIABLE)
  /vehicle/rpm              std_msgs/String     (BEST_EFFORT)
  /vehicle/steer_feedback   geometry_msgs/Twist (BEST_EFFORT)

Publishes:
  /switch/autonomous        std_msgs/Bool       (RELIABLE)
  /switch/acc               std_msgs/Bool       (RELIABLE)
  /switch/lka               std_msgs/Bool       (RELIABLE)
  /switch/manual_override   std_msgs/Bool       (RELIABLE)
  /adas/manual_cmd          geometry_msgs/Twist (RELIABLE)  20 Hz
"""

import threading
from collections import deque
from datetime import datetime

import tkinter as tk
from tkinter import font as tkfont

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from std_msgs.msg import String, Bool
from sensor_msgs.msg import Range, Image
from geometry_msgs.msg import Twist

try:
    import numpy as np
    from PIL import Image as PILImage, ImageTk
    _IMG_OK = True
except ImportError:
    _IMG_OK = False

# ── Colour palette ────────────────────────────────────────────────────────────
BG        = '#12121f'
BG2       = '#1a1a2e'
BG3       = '#0f3460'
BG4       = '#0a0a18'
FG        = '#dde1e7'
FG2       = '#7a8090'
GREEN     = '#00e676'
BLUE      = '#2196f3'
RED       = '#f44336'
YELLOW    = '#ffeb3b'
CYAN      = '#00bcd4'
ORANGE    = '#ff9800'
WHITE     = '#ffffff'
DARK_BTN  = '#1e2030'
MASTER_ON_BG  = '#1a3a1a'
MASTER_OFF_BG = '#3a1a1a'

_MODE_COLOR = {
    'MANUAL':         GREEN,
    'AUTO':           BLUE,
    'EMERGENCY_STOP': RED,
}
_AEB_COLOR = {
    'CLEAR':      GREEN,
    'WARNING':    YELLOW,
    'PARTIAL':    ORANGE,
    'HARD_BRAKE': '#ff5722',
    'STOP':       RED,
}

# Direction keys: name → (linear_x_sign, angular_z_sign)
_DIR_AXES = {
    'fwd':   ( 1.0,  0.0),
    'rev':   (-1.0,  0.0),
    'left':  ( 0.0,  1.0),
    'right': ( 0.0, -1.0),
}


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard application  (always runs on Tk main thread)
# ─────────────────────────────────────────────────────────────────────────────
class DashboardApp:

    def __init__(self, root: tk.Tk, node):
        self._root = root
        self._node = node

        # ── Autonomous / feature state ────────────────────────────────────────
        self._mode     = 'MANUAL'
        self._auto_on  = False
        self._acc_on   = False
        self._lka_on   = False

        # ── Master switch & manual drive state ───────────────────────────────
        self._master_on     : bool       = False
        self._max_speed_mms : float      = 250.0   # mm/s
        self._max_steer_rad : float      = 1.0     # rad
        # Held directions — shared between keyboard and dpad buttons
        self._held: dict[str, bool] = {d: False for d in _DIR_AXES}
        # Refs to dpad Button widgets so we can update their colour
        self._dpad_btns: dict[str, tk.Button] = {}

        # ── Telemetry display state ───────────────────────────────────────────
        self._aeb_state = 'CLEAR'
        self._aeb_dist  = 0.65
        self._speed_ms  = 0.0
        self._steer_rad = 0.0
        self._photo     = None          # keep ImageTk ref alive
        self._events    = deque(maxlen=10)

        root.title('ADAS Dashboard v3  |  Pi 10.162.11.52')
        root.configure(bg=BG)
        try:
            root.state('zoomed')
        except tk.TclError:
            root.attributes('-zoomed', True)

        self._build_ui()

        # ── WASD keyboard bindings (bound to root so always active) ──────────
        for key, direction in (
                ('w', 'fwd'), ('W', 'fwd'),
                ('s', 'rev'), ('S', 'rev'),
                ('a', 'left'), ('A', 'left'),
                ('d', 'right'), ('D', 'right')):
            root.bind(f'<KeyPress-{key}>',
                      lambda e, dr=direction: self._kbd_press(dr))
            root.bind(f'<KeyRelease-{key}>',
                      lambda e, dr=direction: self._kbd_release(dr))
        root.bind('<KeyPress-space>',   lambda e: self._kbd_stop())
        root.bind('<KeyRelease-space>', lambda e: None)

        self._add_event('Dashboard online')
        self._manual_tick()   # start 20 Hz drive-cmd loop
        self._tick()          # start 10 Hz redraw loop

    # ─────────────────────────────────────────────────────────────────────────
    # UI builders
    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        r = self._root
        r.columnconfigure(0, weight=22, uniform='col')
        r.columnconfigure(1, weight=30, uniform='col')
        r.columnconfigure(2, weight=22, uniform='col')
        r.rowconfigure(0, weight=1)

        self._pL = tk.Frame(r, bg=BG,  padx=10, pady=10)
        self._pC = tk.Frame(r, bg=BG2, padx=10, pady=10)
        self._pR = tk.Frame(r, bg=BG,  padx=10, pady=10)
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

    def _section_frame(self, parent, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=BG3, padx=6, pady=4)
        outer.pack(fill='x', pady=5)
        self._lbl(outer, f'  {title}', fg=CYAN, size=8,
                  bold=True, bg=BG3).pack(anchor='w')
        inner = tk.Frame(outer, bg=BG3)
        inner.pack(fill='x')
        return inner

    def _bar_canvas(self, parent, h=24) -> tk.Canvas:
        c = tk.Canvas(parent, height=h, bg=BG4,
                      highlightthickness=1, highlightbackground=BG3)
        c.pack(fill='x', pady=2)
        return c

    # ── LEFT panel ────────────────────────────────────────────────────────────
    def _build_left(self):
        p = self._pL

        # ── 1. MASTER ON/OFF ──────────────────────────────────────────────────
        self._master_btn = tk.Button(
            p, text='⏻   MASTER   OFF',
            font=self._font(14, True),
            bg=MASTER_OFF_BG, fg='#ff6666',
            activebackground=GREEN, activeforeground='black',
            relief='raised', bd=3, pady=12,
            command=self._toggle_master)
        self._master_btn.pack(fill='x', pady=(0, 6))

        # ── 2. VEHICLE MODE ───────────────────────────────────────────────────
        mf = self._section_frame(p, 'VEHICLE MODE')
        self._mode_lbl = self._lbl(mf, 'MANUAL', fg=GREEN,
                                    size=22, bold=True, bg=BG3)
        self._mode_lbl.pack(pady=6)

        # ── 3. BIG AUTO TOGGLE ────────────────────────────────────────────────
        self._auto_btn = tk.Button(
            p, text='▶  ENGAGE AUTONOMOUS',
            font=self._font(12, True),
            bg=DARK_BTN, fg=WHITE,
            activebackground=BLUE, activeforeground=WHITE,
            relief='raised', bd=2, pady=10,
            command=self._toggle_auto)
        self._auto_btn.pack(fill='x', pady=4)

        # ── 4. FEATURE SWITCHES (ACC / LKA) ──────────────────────────────────
        ff = self._section_frame(p, 'FEATURE SWITCHES')
        self._acc_btn = tk.Button(
            ff, text='  ACC   OFF  ',
            font=self._font(10, True),
            bg=DARK_BTN, fg=FG2, state='disabled',
            relief='raised', bd=2, pady=6,
            command=self._toggle_acc)
        self._acc_btn.pack(fill='x', pady=2)

        self._lka_btn = tk.Button(
            ff, text='  LKA   OFF  ',
            font=self._font(10, True),
            bg=DARK_BTN, fg=FG2, state='disabled',
            relief='raised', bd=2, pady=6,
            command=self._toggle_lka)
        self._lka_btn.pack(fill='x', pady=2)

        # ── 5. MANUAL DRIVE CONTROLS ──────────────────────────────────────────
        self._build_drive_panel(p)

        # ── 6. EMERGENCY STOP ─────────────────────────────────────────────────
        self._estop_btn = tk.Button(
            p, text='⬛  EMERGENCY STOP',
            font=self._font(12, True),
            bg=RED, fg=WHITE,
            activebackground='#c62828', activeforeground=WHITE,
            relief='raised', bd=3, pady=12,
            command=self._emergency_stop)
        self._estop_btn.pack(fill='x', pady=8)

        # ── 7. CAN STATUS ─────────────────────────────────────────────────────
        cs = self._section_frame(p, 'CAN BUS')
        self._can_lbl = self._lbl(cs, 'CAN:  --', fg=FG2, size=10, bg=BG3)
        self._can_lbl.pack(anchor='w', pady=2)

        # ── 8. WATCHDOGS ──────────────────────────────────────────────────────
        ws = self._section_frame(p, 'WATCHDOGS')
        self._wd_labels: dict = {}
        for name in ('CAN', 'LIDAR', 'STEER', 'IMU', 'LANE'):
            row = tk.Frame(ws, bg=BG3)
            row.pack(fill='x', pady=1)
            self._lbl(row, f'{name:<6}', fg=FG2, size=9, bg=BG3).pack(side='left')
            dot = tk.Canvas(row, width=12, height=12, bg=BG3,
                            highlightthickness=0)
            dot.pack(side='left', padx=4)
            ov  = dot.create_oval(1, 1, 11, 11, fill=GREEN, outline='')
            lbl = self._lbl(row, 'OK', fg=GREEN, size=9, bold=True, bg=BG3)
            lbl.pack(side='left')
            self._wd_labels[name] = (lbl, dot, ov)

    def _build_drive_panel(self, parent):
        """D-pad + speed/steer sliders section."""
        outer = tk.Frame(parent, bg=BG3, padx=6, pady=4)
        outer.pack(fill='x', pady=5)
        self._lbl(outer, '  MANUAL DRIVE  (WASD / Space)',
                  fg=CYAN, size=8, bold=True, bg=BG3).pack(anchor='w')

        # ── D-pad grid ────────────────────────────────────────────────────────
        dpad = tk.Frame(outer, bg=BG3)
        dpad.pack(pady=4)

        # Dpad button factory
        def _make_dpad_btn(text, direction, gr, gc):
            btn = tk.Button(
                dpad, text=text,
                font=self._font(12, True),
                bg=DARK_BTN, fg=FG,
                activebackground=GREEN, activeforeground='black',
                width=4, height=2, relief='raised', bd=2,
                takefocus=False)           # don't steal keyboard focus
            btn.grid(row=gr, column=gc, padx=3, pady=3)
            btn.bind('<ButtonPress-1>',
                     lambda e, d=direction, b=btn: self._dpad_press(d, b))
            btn.bind('<ButtonRelease-1>',
                     lambda e, d=direction, b=btn: self._dpad_release(d, b))
            self._dpad_btns[direction] = btn
            return btn

        #          text      direction   row  col
        _make_dpad_btn('▲\nW',  'fwd',   0,   1)
        _make_dpad_btn('◄\nA',  'left',  1,   0)
        _make_dpad_btn('►\nD',  'right', 1,   2)
        _make_dpad_btn('▼\nS',  'rev',   2,   1)

        # Centre stop button
        stop_btn = tk.Button(
            dpad, text='■\nSPC',
            font=self._font(11, True),
            bg='#2a1818', fg=RED,
            activebackground=RED, activeforeground=WHITE,
            width=4, height=2, relief='raised', bd=2,
            takefocus=False,
            command=self._kbd_stop)
        stop_btn.grid(row=1, column=1, padx=3, pady=3)
        self._dpad_stop_btn = stop_btn

        # ── MAX SPEED slider ──────────────────────────────────────────────────
        sf = tk.Frame(outer, bg=BG3)
        sf.pack(fill='x', pady=(6, 2))
        spd_row = tk.Frame(sf, bg=BG3)
        spd_row.pack(fill='x')
        self._lbl(spd_row, 'MAX SPEED', fg=FG2, size=8,
                  bold=True, bg=BG3).pack(side='left')
        self._speed_val_lbl = self._lbl(spd_row, '250 mm/s',
                                         fg=GREEN, size=8, bold=True, bg=BG3)
        self._speed_val_lbl.pack(side='right')
        self._speed_scale = tk.Scale(
            sf, from_=50, to=500, orient='horizontal',
            resolution=10, showvalue=False,
            bg=BG3, fg=FG, troughcolor=BG4,
            activebackground=GREEN, highlightthickness=0,
            command=self._on_speed_scale)
        self._speed_scale.set(250)
        self._speed_scale.pack(fill='x')

        # ── MAX STEER slider ──────────────────────────────────────────────────
        stf = tk.Frame(outer, bg=BG3)
        stf.pack(fill='x', pady=(4, 2))
        str_row = tk.Frame(stf, bg=BG3)
        str_row.pack(fill='x')
        self._lbl(str_row, 'MAX STEER', fg=FG2, size=8,
                  bold=True, bg=BG3).pack(side='left')
        self._steer_val_lbl = self._lbl(str_row, '1.00 rad',
                                         fg=CYAN, size=8, bold=True, bg=BG3)
        self._steer_val_lbl.pack(side='right')
        self._steer_scale = tk.Scale(
            stf, from_=30, to=250, orient='horizontal',
            resolution=5, showvalue=False,
            bg=BG3, fg=FG, troughcolor=BG4,
            activebackground=CYAN, highlightthickness=0,
            command=self._on_steer_scale)
        self._steer_scale.set(100)   # 100 internal units = 1.00 rad (×0.01)
        self._steer_scale.pack(fill='x')

    # ── CENTRE panel ──────────────────────────────────────────────────────────
    def _build_centre(self):
        p = self._pC

        cf = self._section_frame(p, 'LANE DEBUG CAMERA  320×240')
        self._cam = tk.Canvas(cf, width=320, height=240, bg='#000010',
                              highlightthickness=2, highlightbackground=BG3)
        self._cam.pack(pady=4)
        self._cam.create_text(160, 120, text='NO SIGNAL', fill=FG2,
                              font=self._font(12, True))

        df = self._section_frame(p, 'AEB DISTANCE')
        self._dist_lbl = self._lbl(df, 'Dist:  -- m',
                                    fg=FG, size=13, bold=True, bg=BG3)
        self._dist_lbl.pack(pady=2)
        self._aeb_lbl = self._lbl(df, 'AEB:  CLEAR',
                                   fg=GREEN, size=11, bold=True, bg=BG3)
        self._aeb_lbl.pack(pady=2)
        self._dist_bar = self._bar_canvas(df, h=30)

    # ── RIGHT panel ───────────────────────────────────────────────────────────
    def _build_right(self):
        p = self._pR

        sf = self._section_frame(p, 'SPEED')
        self._speed_lbl = self._lbl(sf, '0 mm/s',
                                     fg=GREEN, size=14, bold=True, bg=BG3)
        self._speed_lbl.pack()
        self._speed_bar = self._bar_canvas(sf, h=22)

        stf = self._section_frame(p, 'STEERING')
        self._steer_lbl = self._lbl(stf, '0.000 rad',
                                     fg=CYAN, size=11, bold=True, bg=BG3)
        self._steer_lbl.pack()
        self._steer_bar = self._bar_canvas(stf, h=22)

        lf = self._section_frame(p, 'LED MIRROR')
        grid = tk.Frame(lf, bg=BG3)
        grid.pack(pady=4)
        _led_defs = [
            ('POWER',    WHITE,  'PWR'),
            ('MANUAL',   GREEN,  'MAN'),
            ('AUTO',     BLUE,   'AUTO'),
            ('LKA',      GREEN,  'LKA'),
            ('ACC',      CYAN,   'ACC'),
            ('AEB_WARN', YELLOW, 'WARN'),
            ('AEB_STOP', RED,    'STOP'),
        ]
        self._led_ovals: dict = {}
        for i, (key, color, label) in enumerate(_led_defs):
            cell = tk.Frame(grid, bg=BG3, padx=6, pady=2)
            cell.grid(row=i // 4, column=i % 4)
            c = tk.Canvas(cell, width=24, height=24, bg=BG3,
                          highlightthickness=0)
            c.pack()
            oval = c.create_oval(2, 2, 22, 22,
                                  fill='#2a2a3a', outline=color, width=1)
            self._lbl(cell, label, size=7, fg=FG2, bg=BG3).pack()
            self._led_ovals[key] = (c, oval, color)

        ef = self._section_frame(p, 'EVENT LOG')
        self._event_box = tk.Text(
            ef, height=11, bg=BG4, fg=FG,
            font=self._font(8), state='disabled',
            relief='flat', wrap='word', padx=4)
        self._event_box.pack(fill='both', expand=True, pady=2)
        self._event_box.tag_config('warn',  foreground=YELLOW)
        self._event_box.tag_config('error', foreground=RED)
        self._event_box.tag_config('ok',    foreground=GREEN)

    # ─────────────────────────────────────────────────────────────────────────
    # Master switch
    # ─────────────────────────────────────────────────────────────────────────
    def _toggle_master(self):
        self._master_on = not self._master_on
        if self._master_on:
            self._master_btn.config(
                text='⏻   MASTER   ON ',
                bg=MASTER_ON_BG, fg=GREEN)
            self._add_event('Master switch ON', 'ok')
        else:
            self._master_btn.config(
                text='⏻   MASTER   OFF',
                bg=MASTER_OFF_BG, fg='#ff6666')
            # Release all held directions
            self._release_all_dirs()
            self._add_event('Master switch OFF', 'warn')
        self._refresh_controls()

    # ─────────────────────────────────────────────────────────────────────────
    # Autonomous / feature toggles
    # ─────────────────────────────────────────────────────────────────────────
    def _toggle_auto(self):
        if not self._master_on:
            return
        self._auto_on = not self._auto_on
        self._node.pub('auto', self._auto_on)
        tag = 'ok' if self._auto_on else 'warn'
        self._add_event(
            f'AUTONOMOUS {"ENGAGED" if self._auto_on else "DISENGAGED"}', tag)
        self._refresh_controls()

    def _toggle_acc(self):
        if not self._master_on:
            return
        self._acc_on = not self._acc_on
        self._node.pub('acc', self._acc_on)
        self._add_event(f'ACC {"ON" if self._acc_on else "OFF"}',
                         'ok' if self._acc_on else 'warn')
        self._refresh_controls()

    def _toggle_lka(self):
        if not self._master_on:
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
        self._release_all_dirs()
        self._node.pub('manual', True)
        self._add_event('!!! EMERGENCY STOP PRESSED !!!', 'error')
        self._refresh_controls()

    # ─────────────────────────────────────────────────────────────────────────
    # D-pad button press / release
    # ─────────────────────────────────────────────────────────────────────────
    def _dpad_press(self, direction: str, btn: tk.Button):
        if not self._master_on or self._mode != 'MANUAL':
            return
        self._held[direction] = True
        btn.config(bg=GREEN, fg='black')

    def _dpad_release(self, direction: str, btn: tk.Button):
        self._held[direction] = False
        btn.config(bg=DARK_BTN, fg=FG)

    # ─────────────────────────────────────────────────────────────────────────
    # Keyboard drive handlers
    # ─────────────────────────────────────────────────────────────────────────
    def _kbd_press(self, direction: str):
        if not self._master_on or self._mode != 'MANUAL':
            return
        if self._held[direction]:
            return                        # ignore auto-repeat
        self._held[direction] = True
        btn = self._dpad_btns.get(direction)
        if btn:
            btn.config(bg=GREEN, fg='black')

    def _kbd_release(self, direction: str):
        self._held[direction] = False
        btn = self._dpad_btns.get(direction)
        if btn:
            btn.config(bg=DARK_BTN, fg=FG)

    def _kbd_stop(self):
        self._release_all_dirs()

    def _release_all_dirs(self):
        for d in _DIR_AXES:
            self._held[d] = False
        for d, btn in self._dpad_btns.items():
            btn.config(bg=DARK_BTN, fg=FG)

    # ─────────────────────────────────────────────────────────────────────────
    # Slider callbacks
    # ─────────────────────────────────────────────────────────────────────────
    def _on_speed_scale(self, val):
        self._max_speed_mms = float(val)
        self._speed_val_lbl.config(text=f'{int(float(val))} mm/s')

    def _on_steer_scale(self, val):
        # Internal range 30–250 → 0.30–2.50 rad (×0.01)
        rad = float(val) * 0.01
        self._max_steer_rad = rad
        self._steer_val_lbl.config(text=f'{rad:.2f} rad')

    # ─────────────────────────────────────────────────────────────────────────
    # Refresh all control widget states
    # ─────────────────────────────────────────────────────────────────────────
    def _refresh_controls(self):
        is_auto   = self._mode == 'AUTO'
        master    = self._master_on
        can_drive = master and self._mode == 'MANUAL'

        # ── AUTO button ───────────────────────────────────────────────────────
        if not master:
            self._auto_btn.config(state='disabled',
                                   text='▶  ENGAGE AUTONOMOUS',
                                   bg=DARK_BTN, fg=FG2)
        elif self._auto_on or is_auto:
            self._auto_btn.config(state='normal',
                                   text='■  DISENGAGE AUTONOMOUS',
                                   bg=BLUE, fg=WHITE)
        else:
            self._auto_btn.config(state='normal',
                                   text='▶  ENGAGE AUTONOMOUS',
                                   bg=DARK_BTN, fg=WHITE)

        # ── ACC / LKA ─────────────────────────────────────────────────────────
        if master and is_auto:
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

        # ── D-pad ─────────────────────────────────────────────────────────────
        dpad_state = 'normal' if can_drive else 'disabled'
        dpad_fg    = FG       if can_drive else FG2
        for d, btn in self._dpad_btns.items():
            if not can_drive:
                btn.config(state='disabled', bg=DARK_BTN, fg=FG2)
            else:
                btn.config(state='normal', fg=dpad_fg)
        self._dpad_stop_btn.config(state=dpad_state)

        # ── Sliders ───────────────────────────────────────────────────────────
        slider_state = 'normal' if master else 'disabled'
        self._speed_scale.config(state=slider_state)
        self._steer_scale.config(state=slider_state)

    # ─────────────────────────────────────────────────────────────────────────
    # 20 Hz manual drive publish loop
    # ─────────────────────────────────────────────────────────────────────────
    def _manual_tick(self):
        twist = Twist()
        if self._master_on and self._mode == 'MANUAL':
            lin = 0.0
            ang = 0.0
            for direction, (lx, az) in _DIR_AXES.items():
                if self._held[direction]:
                    lin += lx * (self._max_speed_mms / 1000.0)
                    ang += az * self._max_steer_rad
            # Clamp to ±max in case of combined inputs
            max_spd = self._max_speed_mms / 1000.0
            twist.linear.x  = max(-max_spd, min(lin, max_spd))
            twist.angular.z = max(-self._max_steer_rad,
                                  min(ang, self._max_steer_rad))
        self._node.pub_manual_cmd(twist)
        self._root.after(50, self._manual_tick)   # 20 Hz

    # ─────────────────────────────────────────────────────────────────────────
    # Apply methods  (always called on Tk thread via root.after)
    # ─────────────────────────────────────────────────────────────────────────
    def _apply_mode(self, mode: str):
        prev       = self._mode
        self._mode = mode
        color      = _MODE_COLOR.get(mode, FG)
        self._mode_lbl.config(text=mode, fg=color)
        if mode != prev:
            # If we left MANUAL while driving, stop the car
            if prev == 'MANUAL':
                self._release_all_dirs()
            tag = ('error' if mode == 'EMERGENCY_STOP' else
                   ('ok'   if mode == 'AUTO'            else 'warn'))
            self._add_event(f'Mode → {mode}', tag)
        self._refresh_controls()

    def _apply_status(self, data: str):
        kv = {k: v for k, v in
              (p.split(':', 1) for p in data.split('|') if ':' in p)}
        can_ok = kv.get('CAN', 'FAIL') == 'OK'
        self._can_lbl.config(
            text=f'CAN:  {"OK  ✔" if can_ok else "FAIL ✘"}',
            fg=GREEN if can_ok else RED)
        aeb = kv.get('AEB', 'CLEAR')
        if aeb != self._aeb_state:
            self._aeb_state = aeb

    def _apply_leds(self, data: str):
        kv = {k: v for k, v in
              (p.split(':', 1) for p in data.split('|') if ':' in p)}
        for key, (c, oval, color) in self._led_ovals.items():
            on = kv.get(key, '0') == '1'
            c.itemconfig(oval, fill=color if on else '#2a2a3a')

    def _apply_watchdog(self, data: str):
        kv = {k: v for k, v in
              (p.split(':', 1) for p in data.split('|') if ':' in p)}
        for name, (lbl, dot, oval) in self._wd_labels.items():
            ok  = kv.get(name, 'OK') == 'OK'
            col = GREEN if ok else RED
            lbl.config(text='OK' if ok else 'FAIL', fg=col)
            dot.itemconfig(oval, fill=col)

    def _apply_lidar(self, dist: float):
        self._aeb_dist = dist
        self._dist_lbl.config(text=f'Dist:  {dist:.2f} m')
        color = _AEB_COLOR.get(self._aeb_state, GREEN)
        self._aeb_lbl.config(text=f'AEB:  {self._aeb_state}', fg=color)
        self._draw_dist_bar(dist, color)

    def _draw_dist_bar(self, dist: float, color: str):
        c = self._dist_bar
        c.update_idletasks()
        w = c.winfo_width() or 300
        h = 30
        c.delete('all')
        c.create_rectangle(0, 0, w, h, fill=BG4, outline='')
        fill_w = max(int(min(dist / 0.65, 1.0) * w), 4)
        c.create_rectangle(2, 3, fill_w, h - 3, fill=color, outline='')
        c.create_text(w // 2, h // 2, text=f'{dist * 100:.1f} cm',
                      fill=WHITE, font=self._font(9, True))

    def _apply_speed(self, speed_ms: float):
        self._speed_ms = speed_ms
        mms = speed_ms * 1000.0
        self._speed_lbl.config(text=f'{mms:.1f} mm/s')
        c = self._speed_bar
        c.update_idletasks()
        w = c.winfo_width() or 200
        h = 22
        c.delete('all')
        c.create_rectangle(0, 0, w, h, fill=BG4, outline='')
        fill_w = max(int(min(abs(speed_ms) / 0.5, 1.0) * w), 2)
        c.create_rectangle(2, 3, fill_w, h - 3,
                           fill=GREEN if speed_ms >= 0 else ORANGE,
                           outline='')

    def _apply_steer(self, steer_rad: float):
        self._steer_rad = steer_rad
        self._steer_lbl.config(text=f'{steer_rad:+.3f} rad')
        c = self._steer_bar
        c.update_idletasks()
        w   = c.winfo_width() or 200
        h   = 22
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

    def _apply_image(self, pil_img):
        if not _IMG_OK:
            return
        photo = ImageTk.PhotoImage(pil_img)
        self._cam.delete('all')
        self._cam.create_image(0, 0, anchor='nw', image=photo)
        self._photo = photo   # prevent GC

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
    # Periodic redraw  (10 Hz)
    # ─────────────────────────────────────────────────────────────────────────
    def _tick(self):
        self._draw_dist_bar(self._aeb_dist,
                             _AEB_COLOR.get(self._aeb_state, GREEN))
        self._apply_speed(self._speed_ms)
        self._apply_steer(self._steer_rad)
        self._root.after(100, self._tick)


# ─────────────────────────────────────────────────────────────────────────────
# ROS2 node  (spins on background thread, never touches Tk directly)
# ─────────────────────────────────────────────────────────────────────────────
class _LazyRosNode(Node):
    """
    Publishers created immediately; subscriptions wired in late_init() once
    the Tk root is ready so root.after() is safe to call.
    """

    def __init__(self):
        super().__init__('dashboard_v3_node')
        self._app: DashboardApp | None = None

        rel = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                         history=HistoryPolicy.KEEP_LAST, depth=10)

        self._pub_auto       = self.create_publisher(Bool,  '/switch/autonomous',      rel)
        self._pub_acc        = self.create_publisher(Bool,  '/switch/acc',             rel)
        self._pub_lka        = self.create_publisher(Bool,  '/switch/lka',             rel)
        self._pub_manual_sw  = self.create_publisher(Bool,  '/switch/manual_override', rel)
        self._pub_manual_cmd = self.create_publisher(Twist, '/adas/manual_cmd',        rel)

    # ── Publish helpers ───────────────────────────────────────────────────────
    def pub(self, key: str, value: bool):
        msg = Bool(data=value)
        {'auto':   self._pub_auto,
         'acc':    self._pub_acc,
         'lka':    self._pub_lka,
         'manual': self._pub_manual_sw}[key].publish(msg)

    def pub_manual_cmd(self, twist: Twist):
        self._pub_manual_cmd.publish(twist)

    # ── Wire subscriptions once Tk is ready ───────────────────────────────────
    def late_init(self, app: DashboardApp):
        self._app = app
        be  = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                         history=HistoryPolicy.KEEP_LAST, depth=1)
        rel = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                         history=HistoryPolicy.KEEP_LAST, depth=10)

        def _ui(fn, *a):
            app._root.after(0, fn, *a)

        self.create_subscription(String, '/system/mode',
            lambda m: _ui(app._apply_mode,     m.data), rel)
        self.create_subscription(String, '/system/status',
            lambda m: _ui(app._apply_status,   m.data), rel)
        self.create_subscription(String, '/led/states',
            lambda m: _ui(app._apply_leds,     m.data), rel)
        self.create_subscription(String, '/system/watchdog',
            lambda m: _ui(app._apply_watchdog, m.data), rel)
        self.create_subscription(Range, '/sensor/lidar_range',
            lambda m: _ui(app._apply_lidar, float(m.range)), be)
        self.create_subscription(Twist, '/vehicle/steer_feedback',
            lambda m: _ui(app._apply_steer, m.angular.z), be)
        self.create_subscription(String, '/vehicle/rpm',
            lambda m: self._on_rpm(m, app), be)
        self.create_subscription(Image, '/lane/debug_image',
            lambda m: self._on_image(m, app), be)

    def _on_rpm(self, msg: String, app: DashboardApp):
        try:
            v = float(msg.data.split('|')[0])
            app._root.after(0, app._apply_speed, v)
        except (ValueError, IndexError):
            pass

    def _on_image(self, msg: Image, app: DashboardApp):
        if not _IMG_OK:
            return
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
        ros_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
