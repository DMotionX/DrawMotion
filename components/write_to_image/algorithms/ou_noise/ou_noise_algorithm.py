"""
Ornstein-Uhlenbeck Noise Handwriting Algorithm (Organic Sketch & Tremor).
Simulates physiological human motor tremor and instantaneous muscular velocity fluctuations
via a mean-reverting stochastic Ornstein-Uhlenbeck process. Imbues handwriting with genuine
biological warmth and spontaneity without distorting letterform geometry.
"""

import numpy as np
from ..base_algorithm import BaseWritingAlgorithm


class OrnsteinUhlenbeckNoiseAlgorithm(BaseWritingAlgorithm):
    """
    Biological Neuromuscular Tremor Kinematic Model.
    - Stochastic mean-reverting velocity fluctuations: dv = theta*(mu - v)*dt + sigma*dW
    - Simulates human motor variability (8-12 Hz micro-tremor).
    - Preserves exact path fidelity while adding spontaneous organic personality.
    """

    @property
    def style(self) -> str:
        return "ou_noise"

    def generate_times(self, seeds: list, is_rtl: bool) -> np.ndarray:
        if not seeds:
            return np.array([], dtype=float)

        N = len(seeds)
        if N == 1:
            return np.array([0.0], dtype=float)
        if N == 2:
            return np.array([0.0, 1.0], dtype=float)

        seeds_arr = np.array(seeds, dtype=float)

        # 1. Stroke boundary detection
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

        # Fix RNG seed deterministically per seed count for stable and reproducible animations
        rng = np.random.RandomState(seed=N * 31 + 17)

        # Ornstein-Uhlenbeck parameters
        # mu = baseline velocity, theta = mean reversion speed, sigma = volatility
        mu = 1.0
        theta = 0.15
        sigma = 0.28

        # 2. Process each stroke
        for stroke_idx, (s_start, s_end) in enumerate(strokes):
            stroke_len = s_end - s_start
            stroke_pts = seeds_arr[s_start:s_end]

            if stroke_len <= 2:
                dt_full[s_start:s_end] = 0.05
            else:
                # Generate OU velocity series for this stroke
                v = np.ones(stroke_len, dtype=float)
                for i in range(1, stroke_len):
                    dw = rng.normal(0.0, 1.0)
                    dv = theta * (mu - v[i - 1]) + sigma * dw
                    v[i] = v[i - 1] + dv

                # Clamp velocity to prevent stalling or backwards motion
                v_clamped = np.clip(v, 0.25, 3.5)

                s_step_dists = np.sqrt(np.sum((stroke_pts[1:] - stroke_pts[:-1]) ** 2, axis=1))
                s_step_dists = np.concatenate(([1.0], s_step_dists))
                dt_full[s_start:s_end] = s_step_dists / v_clamped

            # Airborne ballistic travel time
            if stroke_idx > 0:
                jump_dist = dists[s_start - 1]
                dt_full[s_start] += (jump_dist / 16.0) + 0.04

        # 3. Cumulative integration and normalization
        times = np.cumsum(dt_full)
        t_span = times[-1] - times[0]
        if t_span > 1e-7:
            times = (times - times[0]) / t_span
        else:
            times = np.linspace(0.0, 1.0, N)

        return times
