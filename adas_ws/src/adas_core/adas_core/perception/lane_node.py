"""
lane_node.py — Full lane detection pipeline.

Pipeline:
  HSV white masking → IPM warp → sliding-window search →
  polynomial fit → recovery hierarchy → LaneData + debug image

Subscribes : /camera/image_raw     (sensor_msgs/Image)
Publishes  : /lane/data            (LaneData)
             /lane/debug_image     (sensor_msgs/Image)

IPM calibration loaded from:
  ~/adas_ws/src/adas_core/config/ipm_calibration.yaml
  (overridable via ROS2 parameter 'config_path')
"""

import os
import threading
from typing import Optional, Tuple

import cv2
import numpy as np
import yaml

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from cv_bridge import CvBridge
from sensor_msgs.msg import Image

from adas_msgs.msg import LaneData

# ──────────────────────────────────────────────────────────────────────────────
# Recovery mode constants
# ──────────────────────────────────────────────────────────────────────────────

MODE_BOTH_LANES    = 'BOTH_LANES'
MODE_PREDICT       = 'PREDICT'
MODE_SINGLE_LANE   = 'SINGLE_LANE'
MODE_EMERGENCY_STOP = 'EMERGENCY_STOP'

PREDICT_MAX_FRAMES = 10
MIN_POLY_POINTS    = 10
CONFIDENCE_PIXEL_NORM = 500.0

# ──────────────────────────────────────────────────────────────────────────────
# Default identity IPM (used when config file is missing)
# ──────────────────────────────────────────────────────────────────────────────

_DEFAULT_CONFIG = {
    'src_points':          [[0, 479], [639, 479], [639, 0], [0, 0]],
    'dst_points':          [[0, 799], [499, 799], [499, 0], [0, 0]],
    'output_size':         [500, 800],
    'metres_per_pixel_x':  0.00185,
    'metres_per_pixel_y':  0.00240,
    'car_centre_x':        250,
    'lane_width_m':        0.385,
}


# ──────────────────────────────────────────────────────────────────────────────
# Config loading
# ──────────────────────────────────────────────────────────────────────────────

def _load_ipm_config(config_path: str, logger) -> dict:
    """Load IPM calibration YAML; fall back to identity transform on error."""
    expanded = os.path.expanduser(config_path)
    if not os.path.isfile(expanded):
        logger.error(
            f'IPM calibration file not found at "{expanded}". '
            'Using identity transform — lane estimates will be unreliable.'
        )
        return dict(_DEFAULT_CONFIG)
    try:
        with open(expanded, 'r') as fh:
            data = yaml.safe_load(fh)
        # Validate required keys
        required = [
            'src_points', 'dst_points', 'output_size',
            'metres_per_pixel_x', 'metres_per_pixel_y',
            'car_centre_x', 'lane_width_m',
        ]
        for key in required:
            if key not in data:
                raise KeyError(f'Missing key "{key}" in calibration file.')
        logger.info(f'IPM calibration loaded from "{expanded}".')
        return data
    except Exception as exc:  # noqa: BLE001
        logger.error(
            f'Failed to parse IPM calibration file "{expanded}": {exc}. '
            'Falling back to identity transform.'
        )
        return dict(_DEFAULT_CONFIG)


# ──────────────────────────────────────────────────────────────────────────────
# Node
# ──────────────────────────────────────────────────────────────────────────────

class LaneNode(Node):
    """
    Lane detection node using IPM + sliding-window polynomial fitting.

    Architecture:
      - ROS callback stores the latest frame under a Lock.
      - A dedicated processing thread wakes on a threading.Event, runs the
        full pipeline, and publishes results.
      - A 30 Hz timer triggers LaneData re-publish from cached results if
        a new frame has not yet been processed (keeps downstream at rate).
    """

    def __init__(self) -> None:
        super().__init__('lane_node')

        # ── Parameters ────────────────────────────────────────────────────────
        default_cfg = os.path.expanduser(
            '~/adas_ws/src/adas_core/config/ipm_calibration.yaml'
        )
        self.declare_parameter('config_path', default_cfg)
        self.declare_parameter('debug_publish', True)

        config_path: str = (
            self.get_parameter('config_path').get_parameter_value().string_value
        )
        self._debug_publish: bool = (
            self.get_parameter('debug_publish').get_parameter_value().bool_value
        )

        # ── Load calibration ──────────────────────────────────────────────────
        cfg = _load_ipm_config(config_path, self.get_logger())

        src_pts = np.float32(cfg['src_points'])
        dst_pts = np.float32(cfg['dst_points'])
        self._ipm_M: np.ndarray = cv2.getPerspectiveTransform(src_pts, dst_pts)

        self._out_W: int = int(cfg['output_size'][0])
        self._out_H: int = int(cfg['output_size'][1])
        self._mppx: float  = float(cfg['metres_per_pixel_x'])
        self._mppy: float  = float(cfg['metres_per_pixel_y'])
        self._car_centre_x: float = float(cfg['car_centre_x'])
        self._lane_width_m: float = float(cfg['lane_width_m'])
        self._lane_width_px: float = self._lane_width_m / self._mppx

        self._mid: int = self._out_W // 2

        # Sliding-window params
        self._n_windows: int = 14
        self._win_h: int = self._out_H // self._n_windows
        self._margin: int = max(1, int(0.08 * self._out_W))  # 8 % → 40 px
        self._minpix: int = 5

        # ── Recovery state ────────────────────────────────────────────────────
        self._last_good_left_fit:  Optional[np.ndarray] = None
        self._last_good_right_fit: Optional[np.ndarray] = None
        self._predict_frame_count: int = 0
        self._last_lane_data:      Optional[LaneData] = None

        # ── CV bridge ─────────────────────────────────────────────────────────
        self._bridge = CvBridge()

        # ── Threading ─────────────────────────────────────────────────────────
        self._frame_lock = threading.Lock()
        self._latest_frame: Optional[np.ndarray] = None
        self._new_frame_event = threading.Event()
        self._shutdown_flag = threading.Event()
        self._result_lock = threading.Lock()

        self._processing_thread = threading.Thread(
            target=self._processing_loop,
            name='lane_processing',
            daemon=True,
        )

        # ── QoS ───────────────────────────────────────────────────────────────
        img_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # ── Subscribers ───────────────────────────────────────────────────────
        self._image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self._image_callback,
            img_qos,
        )

        # ── Publishers ────────────────────────────────────────────────────────
        self._lane_pub  = self.create_publisher(LaneData, '/lane/data', 10)
        self._debug_pub = self.create_publisher(Image, '/lane/debug_image', 10)

        # ── 30 Hz publish timer ───────────────────────────────────────────────
        self._publish_timer = self.create_timer(1.0 / 30.0, self._timer_publish_callback)

        # ── Start thread ──────────────────────────────────────────────────────
        self._processing_thread.start()
        self.get_logger().info(
            f'LaneNode ready — IPM {self._out_W}×{self._out_H}, '
            f'margin={self._margin}px, windows={self._n_windows}'
        )

    # ── ROS callback ──────────────────────────────────────────────────────────

    def _image_callback(self, msg: Image) -> None:
        """Store the latest frame and signal the processing thread."""
        try:
            frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warning(f'cv_bridge conversion failed: {exc}')
            return

        with self._frame_lock:
            self._latest_frame = frame
        self._new_frame_event.set()

    # ── Timer callback — re-publish cached LaneData at 30 Hz ─────────────────

    def _timer_publish_callback(self) -> None:
        with self._result_lock:
            cached = self._last_lane_data
        if cached is not None:
            # Refresh timestamp so downstream sees a live message
            cached.header.stamp = self.get_clock().now().to_msg()
            self._lane_pub.publish(cached)

    # ── Processing thread ─────────────────────────────────────────────────────

    def _processing_loop(self) -> None:
        while not self._shutdown_flag.is_set():
            triggered = self._new_frame_event.wait(timeout=0.5)
            if not triggered:
                continue
            self._new_frame_event.clear()

            with self._frame_lock:
                frame = self._latest_frame
                if frame is None:
                    continue
                frame = frame.copy()

            try:
                self._process_frame(frame)
            except Exception as exc:  # noqa: BLE001
                self.get_logger().error(f'Lane processing error: {exc}', throttle_duration_sec=2.0)

    # ══════════════════════════════════════════════════════════════════════════
    # PIPELINE
    # ══════════════════════════════════════════════════════════════════════════

    def _process_frame(self, frame: np.ndarray) -> None:
        img_h, img_w = frame.shape[:2]

        # ── Step 1: White mask ────────────────────────────────────────────────
        mask_binary = self._white_mask(frame, img_h, img_w)

        # ── Step 2: IPM warp ──────────────────────────────────────────────────
        warped = cv2.warpPerspective(
            mask_binary, self._ipm_M, (self._out_W, self._out_H)
        )

        # ── Step 3: Sliding window search ────────────────────────────────────
        leftx, lefty, rightx, righty = self._sliding_window_search(warped)

        # ── Step 4: Polynomial fit ────────────────────────────────────────────
        left_fit:  Optional[np.ndarray] = None
        right_fit: Optional[np.ndarray] = None

        if len(lefty) > MIN_POLY_POINTS:
            try:
                left_fit = np.polyfit(lefty, leftx, 2)
            except (np.linalg.LinAlgError, ValueError):
                left_fit = None

        if len(righty) > MIN_POLY_POINTS:
            try:
                right_fit = np.polyfit(righty, rightx, 2)
            except (np.linalg.LinAlgError, ValueError):
                right_fit = None

        # ── Step 5: Recovery hierarchy ────────────────────────────────────────
        left_fit, right_fit, recovery_mode, confidence = self._apply_recovery(
            left_fit, right_fit, len(lefty), len(righty)
        )

        if recovery_mode == MODE_EMERGENCY_STOP:
            lane_data = self._build_emergency_lane_data()
            with self._result_lock:
                self._last_lane_data = lane_data
            self._lane_pub.publish(lane_data)
            return

        # ── Step 6: Compute outputs ───────────────────────────────────────────
        H = self._out_H
        y_eval = float(H - 1)

        left_x  = self._eval_poly(left_fit,  y_eval)
        right_x = self._eval_poly(right_fit, y_eval)
        centre_x = (left_x + right_x) / 2.0

        lateral_error_m = (centre_x - self._car_centre_x) * self._mppx

        curvature = self._compute_curvature(left_fit, y_eval)

        # ── Step 7: Publish LaneData ──────────────────────────────────────────
        lane_data = LaneData()
        lane_data.header.stamp    = self.get_clock().now().to_msg()
        lane_data.header.frame_id = 'camera_link'
        lane_data.left_x          = float(left_x)
        lane_data.right_x         = float(right_x)
        lane_data.centre_x        = float(centre_x)
        lane_data.curvature       = float(curvature)
        lane_data.lateral_error_m = float(lateral_error_m)
        lane_data.confidence      = float(confidence)
        lane_data.recovery_mode   = recovery_mode

        with self._result_lock:
            self._last_lane_data = lane_data
        self._lane_pub.publish(lane_data)

        # ── Debug image ───────────────────────────────────────────────────────
        if self._debug_publish:
            debug_img = self._draw_debug(warped, left_fit, right_fit)
            try:
                debug_msg = self._bridge.cv2_to_imgmsg(debug_img, encoding='bgr8')
                debug_msg.header.stamp    = lane_data.header.stamp
                debug_msg.header.frame_id = 'camera_link'
                self._debug_pub.publish(debug_msg)
            except Exception as exc:  # noqa: BLE001
                self.get_logger().warning(f'Debug image publish failed: {exc}')

    # ── Step 1 impl ───────────────────────────────────────────────────────────

    def _white_mask(self, frame: np.ndarray, img_h: int, img_w: int) -> np.ndarray:
        """
        Return a binary mask (uint8, 0/255) of white pixels using adaptive
        thresholding in HSV.  ROI is the bottom half of the frame for stats,
        but the mask is applied to the full image.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        roi_v = hsv[img_h // 2:, :, 2].astype(np.float32)

        mean_v = float(roi_v.mean())
        std_v  = float(roi_v.std())
        v_thresh = max(80.0, mean_v + 1.2 * std_v)

        V = hsv[:, :, 2]
        S = hsv[:, :, 1]

        mask = np.zeros((img_h, img_w), dtype=np.uint8)
        condition = (V.astype(np.float32) > v_thresh) & (S < 40)
        mask[condition] = 255
        return mask

    # ── Step 3 impl ───────────────────────────────────────────────────────────

    def _sliding_window_search(
        self, warped: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Sliding-window search with hard centre-line boundaries.
        Returns (leftx, lefty, rightx, righty) arrays of pixel coordinates.
        """
        H, W = warped.shape[:2]
        mid  = self._mid

        # Histogram of bottom half
        hist_region = warped[H // 2:, :]
        histogram = np.sum(hist_region.astype(np.float32), axis=0)

        left_base  = int(np.argmax(histogram[:mid]))
        right_base = int(np.argmax(histogram[mid:])) + mid

        left_x_current  = left_base
        right_x_current = right_base

        nonzero   = warped.nonzero()
        nonzero_y = np.array(nonzero[0])
        nonzero_x = np.array(nonzero[1])

        left_inds:  list[np.ndarray] = []
        right_inds: list[np.ndarray] = []

        for win_idx in range(self._n_windows):
            # Window y bounds (scan top→bottom from bottom of image)
            win_y_high = H - win_idx * self._win_h
            win_y_low  = win_y_high - self._win_h

            # ── LEFT window — hard boundary: x_hi <= mid ─────────────────────
            lx_lo = max(0,   left_x_current  - self._margin)
            lx_hi = min(mid, left_x_current  + self._margin)

            # ── RIGHT window — hard boundary: x_lo >= mid ────────────────────
            rx_lo = max(mid, right_x_current - self._margin)
            rx_hi = min(W,   right_x_current + self._margin)

            # Collect pixels
            good_left = np.where(
                (nonzero_y >= win_y_low)  & (nonzero_y < win_y_high) &
                (nonzero_x >= lx_lo)      & (nonzero_x < lx_hi)
            )[0]
            good_right = np.where(
                (nonzero_y >= win_y_low)  & (nonzero_y < win_y_high) &
                (nonzero_x >= rx_lo)      & (nonzero_x < rx_hi)
            )[0]

            if len(good_left) > self._minpix:
                left_inds.append(good_left)
                left_x_current = int(np.mean(nonzero_x[good_left]))

            if len(good_right) > self._minpix:
                right_inds.append(good_right)
                right_x_current = int(np.mean(nonzero_x[good_right]))

        if left_inds:
            left_idx_all = np.concatenate(left_inds)
            leftx = nonzero_x[left_idx_all]
            lefty = nonzero_y[left_idx_all]
        else:
            leftx = np.array([], dtype=np.int32)
            lefty = np.array([], dtype=np.int32)

        if right_inds:
            right_idx_all = np.concatenate(right_inds)
            rightx = nonzero_x[right_idx_all]
            righty = nonzero_y[right_idx_all]
        else:
            rightx = np.array([], dtype=np.int32)
            righty = np.array([], dtype=np.int32)

        return leftx, lefty, rightx, righty

    # ── Step 5 impl ───────────────────────────────────────────────────────────

    def _apply_recovery(
        self,
        left_fit:  Optional[np.ndarray],
        right_fit: Optional[np.ndarray],
        n_left:    int,
        n_right:   int,
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], str, float]:
        """
        Apply recovery hierarchy and return
        (left_fit, right_fit, recovery_mode, confidence).
        """
        both_found = (left_fit is not None) and (right_fit is not None)
        any_found  = (left_fit is not None) or  (right_fit is not None)

        # ── BOTH_LANES ────────────────────────────────────────────────────────
        if both_found:
            self._last_good_left_fit  = left_fit.copy()
            self._last_good_right_fit = right_fit.copy()
            self._predict_frame_count = 0
            conf = min(1.0, (n_left + n_right) / CONFIDENCE_PIXEL_NORM)
            return left_fit, right_fit, MODE_BOTH_LANES, conf

        # ── PREDICT ───────────────────────────────────────────────────────────
        if self._predict_frame_count < PREDICT_MAX_FRAMES:
            self._predict_frame_count += 1

            # Fill missing lane from last known good fit
            if left_fit is None:
                left_fit = (
                    self._last_good_left_fit.copy()
                    if self._last_good_left_fit is not None
                    else None
                )
            if right_fit is None:
                right_fit = (
                    self._last_good_right_fit.copy()
                    if self._last_good_right_fit is not None
                    else None
                )

            if (left_fit is not None) and (right_fit is not None):
                return left_fit, right_fit, MODE_PREDICT, 0.6

        # ── SINGLE_LANE ───────────────────────────────────────────────────────
        if any_found:
            # Update the one we have
            if left_fit is not None:
                self._last_good_left_fit = left_fit.copy()
            elif self._last_good_left_fit is not None:
                left_fit = self._last_good_left_fit.copy()

            if right_fit is not None:
                self._last_good_right_fit = right_fit.copy()
            elif self._last_good_right_fit is not None:
                right_fit = self._last_good_right_fit.copy()

            # Mirror missing lane
            if left_fit is not None and right_fit is None:
                right_fit = np.array([
                    left_fit[0],
                    left_fit[1],
                    left_fit[2] + self._lane_width_px,
                ])
                self._last_good_right_fit = right_fit.copy()
            elif right_fit is not None and left_fit is None:
                left_fit = np.array([
                    right_fit[0],
                    right_fit[1],
                    right_fit[2] - self._lane_width_px,
                ])
                self._last_good_left_fit = left_fit.copy()

            if (left_fit is not None) and (right_fit is not None):
                return left_fit, right_fit, MODE_SINGLE_LANE, 0.4

        # ── EMERGENCY_STOP ────────────────────────────────────────────────────
        self._predict_frame_count += 1
        return None, None, MODE_EMERGENCY_STOP, 0.0

    # ── Step 6 helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _eval_poly(fit: np.ndarray, y: float) -> float:
        """Evaluate a 2nd-degree polynomial at y."""
        return float(fit[0] * y * y + fit[1] * y + fit[2])

    def _compute_curvature(self, left_fit: np.ndarray, y_eval: float) -> float:
        """
        Radius of curvature (metres) of the left lane polynomial at y_eval.
        Converts pixel-space polynomial to metres space before computing.
        """
        # Convert polynomial coefficients from pixel space to metre space
        A_m = left_fit[0] * (self._mppx / (self._mppy ** 2))
        B_m = left_fit[1] * (self._mppx / self._mppy)

        y_eval_m = y_eval * self._mppy
        numerator   = (1.0 + (2.0 * A_m * y_eval_m + B_m) ** 2) ** 1.5
        denominator = abs(2.0 * A_m) + 1e-6
        return float(numerator / denominator)

    # ── Debug image ───────────────────────────────────────────────────────────

    def _draw_debug(
        self,
        warped:    np.ndarray,
        left_fit:  Optional[np.ndarray],
        right_fit: Optional[np.ndarray],
    ) -> np.ndarray:
        """
        Draw both fitted lane curves onto a colour copy of the warped bird's-eye
        image.  Left lane = green, right lane = blue.
        """
        debug = cv2.cvtColor(warped, cv2.COLOR_GRAY2BGR)

        y_vals = np.linspace(0, self._out_H - 1, num=self._out_H)

        if left_fit is not None:
            lx = left_fit[0] * y_vals ** 2 + left_fit[1] * y_vals + left_fit[2]
            pts = np.column_stack([lx, y_vals]).astype(np.int32).reshape(-1, 1, 2)
            pts[:, 0, 0] = np.clip(pts[:, 0, 0], 0, self._out_W - 1)
            cv2.polylines(debug, [pts], isClosed=False, color=(0, 255, 0), thickness=3)

        if right_fit is not None:
            rx = right_fit[0] * y_vals ** 2 + right_fit[1] * y_vals + right_fit[2]
            pts = np.column_stack([rx, y_vals]).astype(np.int32).reshape(-1, 1, 2)
            pts[:, 0, 0] = np.clip(pts[:, 0, 0], 0, self._out_W - 1)
            cv2.polylines(debug, [pts], isClosed=False, color=(255, 0, 0), thickness=3)

        return debug

    # ── Emergency lane data ───────────────────────────────────────────────────

    def _build_emergency_lane_data(self) -> LaneData:
        ld = LaneData()
        ld.header.stamp    = self.get_clock().now().to_msg()
        ld.header.frame_id = 'camera_link'
        ld.left_x          = 0.0
        ld.right_x         = 0.0
        ld.centre_x        = 0.0
        ld.curvature       = 0.0
        ld.lateral_error_m = 0.0
        ld.confidence      = 0.0
        ld.recovery_mode   = MODE_EMERGENCY_STOP
        return ld

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def destroy_node(self) -> None:
        self.get_logger().info('LaneNode shutting down — stopping processing thread.')
        self._shutdown_flag.set()
        self._new_frame_event.set()
        self._processing_thread.join(timeout=3.0)
        super().destroy_node()


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main(args=None) -> None:
    rclpy.init(args=args)
    node = LaneNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
