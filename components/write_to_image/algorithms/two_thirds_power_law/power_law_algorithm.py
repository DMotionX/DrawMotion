"""
Two-Thirds Power Law Handwriting Algorithm (Energetic Sculptor).
Based on Viviani & Terzuolo (1982) biological motor control law:
velocity is inversely proportional to the cube root of trajectory curvature (v ~ kappa^(-1/3)).
Produces highly dynamic, energetic strokes with rapid acceleration on straight segments
and decisive deceleration at corners and loops.
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


class TwoThirdsPowerLawAlgorithm(BaseWritingAlgorithm):
    """
    Biological Two-Thirds Power Law Kinematic Model.
    - Curvature Velocity Coupling: v ~ kappa^(-1/3)
    - Strong contrast between high-speed straight strokes and deep corner braking.
    - Preserves distinct dynamic rhythm for both Arabic and Latin scripts.
    """

    @property
    def style(self) -> str:
        return "two_thirds_power_law"

    def generate_times(self, seeds: list, is_rtl: bool) -> np.ndarray:
        if not seeds:
            return np.array([], dtype=float)

        N = len(seeds)
        if N == 1:
            return np.array([0.0], dtype=float)
        if N == 2:
            return np.array([0.0, 1.0], dtype=float)

        seeds_arr = np.array(seeds, dtype=float)

        # 1. Segment into strokes via airborne jump detection
        dists = np.sqrt(np.sum((seeds_arr[1:] - seeds_arr[:-1]) ** 2, axis=1))
        jump_threshold = 8.0
        jump_indices = np.where(dists > jump_threshold)[0]

        strokes = []
        start_idx = 0
        for j_idx in jump_indices:
            strokes.append((start_idx, j_idx + 1))
            start_idx = j_idx + 1
        strokes.append((start_idx, N))

        dt_full = np.zeros(N, dtype=float)

        # 2. Process each stroke with pure Power Law dynamics
        for stroke_idx, (s_start, s_end) in enumerate(strokes):
            stroke_len = s_end - s_start
            stroke_pts = seeds_arr[s_start:s_end]

            if stroke_len <= 2:
                # Fast tap for micro-dots and accents
                dt_full[s_start:s_end] = 0.04
            else:
                # Gaussian smoothing to suppress discrete rasterization staircase noise
                smoothed_x = _gaussian_smooth_1d(stroke_pts[:, 0], sigma=1.8)
                smoothed_y = _gaussian_smooth_1d(stroke_pts[:, 1], sigma=1.8)

                # Spatial velocity and acceleration vectors
                dx = np.gradient(smoothed_x)
                dy = np.gradient(smoothed_y)
                ddx = np.gradient(dx)
                ddy = np.gradient(dy)

                # Curvature Kappa calculation: |dx*ddy - dy*ddx| / (dx^2 + dy^2)^(3/2)
                speed_sq = dx ** 2 + dy ** 2
                speed_sq[speed_sq < 1e-4] = 1e-4
                kappa = np.abs(dx * ddy - dy * ddx) / (speed_sq ** 1.5)
                kappa_clamped = np.clip(kappa, 0.02, 3.5)

                # Two-Thirds Power Law: v ~ kappa^(-1/3) with low-pass damping
                v_power = kappa_clamped ** (-1.0 / 3.0)
                v_raw = np.clip(v_power, 0.4, 2.8)
                velocity = _gaussian_smooth_1d(v_raw, sigma=1.2)
                velocity = np.clip(velocity, 0.4, 2.8)

                # Differential time: dt = ds / v
                s_dists = np.sqrt(np.sum((stroke_pts[1:] - stroke_pts[:-1]) ** 2, axis=1))
                s_dists = np.concatenate(([1.0], s_dists))
                dt_full[s_start:s_end] = s_dists / velocity

            # Airborne ballistic penalty between disjoint strokes
            if stroke_idx > 0:
                jump_dist = dists[s_start - 1]
                dt_full[s_start] += (jump_dist / 18.0) + 0.03

        # 3. Cumulative integration and normalization
        times = np.cumsum(dt_full)
        t_span = times[-1] - times[0]
        if t_span > 1e-7:
            times = (times - times[0]) / t_span
        else:
            times = np.linspace(0.0, 1.0, N)

        return times
