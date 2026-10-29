"""
Realistic Hybrid Handwriting Algorithm.
Integrates the Two-Thirds Power Law, Minimum-Jerk kinematic motor control,
and stroke segmentation for authentic human handwriting dynamics.
"""

import numpy as np
from ..base_algorithm import BaseWritingAlgorithm


def _gaussian_smooth_1d(arr: np.ndarray, sigma: float = 1.8) -> np.ndarray:
    """Applies edge-padded 1D Gaussian smoothing to filter discrete rasterization noise."""
    if len(arr) < 3:
        return arr.copy()
    radius = int(np.ceil(2.5 * sigma))
    if radius * 2 + 1 > len(arr):
        radius = max(1, (len(arr) - 1) // 2)
    x = np.arange(-radius, radius + 1)
    kernel = np.exp(-0.5 * (x / sigma) ** 2)
    kernel /= np.sum(kernel)
    pad_left = np.full(radius, arr[0])
    pad_right = np.full(radius, arr[-1])
    padded = np.concatenate([pad_left, arr, pad_right])
    return np.convolve(padded, kernel, mode='valid')


class RealisticHybridAlgorithm(BaseWritingAlgorithm):
    """
    Biological Motor Control Kinematic Model.
    - Two-Thirds Power Law: Slows dynamically at sharp turns, loops, and dots; accelerates on straight stems.
    - Minimum-Jerk Velocity Envelope: Natural bell-shaped acceleration and deceleration per stroke.
    - Ballistic Inter-Stroke Jumps: Rapid pen transitions between letters/words with micro-pauses at dots.
    """

    @property
    def style(self) -> str:
        return "realistic_hybrid"

    def generate_times(self, seeds: list, is_rtl: bool) -> np.ndarray:
        if not seeds:
            return np.array([], dtype=float)

        N = len(seeds)
        if N == 1:
            return np.array([0.0], dtype=float)
        if N == 2:
            return np.array([0.0, 1.0], dtype=float)

        seeds_arr = np.array(seeds, dtype=float)

        # 1. Detect stroke boundaries based on spatial jump distance (airborne pen lifts)
        dists = np.sqrt(np.sum((seeds_arr[1:] - seeds_arr[:-1]) ** 2, axis=1))
        jump_threshold = 8.0  # Pixels in skeleton space
        jump_indices = np.where(dists > jump_threshold)[0]

        # Partition seeds into discrete strokes
        strokes = []
        start_idx = 0
        for j_idx in jump_indices:
            strokes.append((start_idx, j_idx + 1))
            start_idx = j_idx + 1
        strokes.append((start_idx, N))

        # 2. Compute time increments (dt) for each point
        dt_full = np.zeros(N, dtype=float)

        for stroke_idx, (s_start, s_end) in enumerate(strokes):
            stroke_len = s_end - s_start
            stroke_pts = seeds_arr[s_start:s_end]

            if stroke_len <= 2:
                # Isolated dot or micro-accent (Tashkeel / Nuqat)
                dt_full[s_start:s_end] = 0.05
            else:
                # Continuous stroke: Gaussian smoothing on spatial coordinates suppresses discrete raster staircase noise
                smoothed_x = _gaussian_smooth_1d(stroke_pts[:, 0], sigma=1.8)
                smoothed_y = _gaussian_smooth_1d(stroke_pts[:, 1], sigma=1.8)

                # Spatial velocity and acceleration vectors
                dx = np.gradient(smoothed_x)
                dy = np.gradient(smoothed_y)
                ddx = np.gradient(dx)
                ddy = np.gradient(dy)

                # Spatial curvature Kappa
                speed_sq = dx ** 2 + dy ** 2
                speed_sq[speed_sq < 1e-4] = 1e-4
                kappa = np.abs(dx * ddy - dy * ddx) / (speed_sq ** 1.5)
                kappa_clamped = np.clip(kappa, 0.02, 3.5)

                # Two-Thirds Power Law: V ~ kappa^(-1/3)
                v_curv = kappa_clamped ** (-1.0 / 3.0)

                # Minimum-Jerk bell curve envelope across normalized stroke progress u in [0, 1]
                u = np.linspace(0.0, 1.0, stroke_len)
                v_jerk = 0.60 + 0.40 * (16.0 * (u ** 2) * ((1.0 - u) ** 2))

                # Combined physical speed with low-pass damping to eliminate acceleration oscillations
                v_raw = np.clip(v_curv * v_jerk, 0.4, 2.5)
                v_total = _gaussian_smooth_1d(v_raw, sigma=1.2)
                v_total = np.clip(v_total, 0.4, 2.5)

                # Segment distances along the stroke
                s_dists = np.sqrt(np.sum((stroke_pts[1:] - stroke_pts[:-1]) ** 2, axis=1))
                s_dists = np.concatenate(([1.0], s_dists))

                dt_full[s_start:s_end] = s_dists / v_total

            # For the point right after a jump, add ballistic transition penalty
            if stroke_idx > 0:
                jump_dist = dists[s_start - 1]
                # High-speed ballistic travel time + subtle micro-pause (settle)
                dt_full[s_start] += (jump_dist / 15.0) + 0.04

        # 3. Cumulative integration and normalization to [0.0, 1.0]
        times = np.cumsum(dt_full)
        t_span = times[-1] - times[0]
        if t_span > 1e-7:
            times = (times - times[0]) / t_span
        else:
            times = np.linspace(0.0, 1.0, N)

        return times
