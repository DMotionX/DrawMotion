"""
Stop-and-Go Handwriting Algorithm (Thoughtful / Block Writer).
Simulates deliberate, contemplative handwriting characterized by distinct pauses
between morphological word chunks and disconnected letter components (syllabic chunking).
Applies bell-shaped sinusoidal speed curves per stroke with explicit resting pauses.
"""

import numpy as np
from ..base_algorithm import BaseWritingAlgorithm


class StopAndGoAlgorithm(BaseWritingAlgorithm):
    """
    Syllabic Chunking & Pausing Kinematic Model.
    - Partitions writing into distinct morphological segments.
    - Smooth sinusoidal velocity within each stroke segment.
    - Prominent, deliberate inter-stroke pauses between disconnected glyphs.
    - Ideal for printed block letters, diagrams, and deliberate annotations.
    """

    @property
    def style(self) -> str:
        return "stop_and_go"

    def generate_times(self, seeds: list, is_rtl: bool) -> np.ndarray:
        if not seeds:
            return np.array([], dtype=float)

        N = len(seeds)
        if N == 1:
            return np.array([0.0], dtype=float)
        if N == 2:
            return np.array([0.0, 1.0], dtype=float)

        seeds_arr = np.array(seeds, dtype=float)

        # 1. Detect disconnected stroke jumps
        dists = np.sqrt(np.sum((seeds_arr[1:] - seeds_arr[:-1]) ** 2, axis=1))
        jump_threshold = 6.0
        jump_indices = np.where(dists > jump_threshold)[0]

        strokes = []
        start_idx = 0
        for j_idx in jump_indices:
            strokes.append((start_idx, j_idx + 1))
            start_idx = j_idx + 1
        strokes.append((start_idx, N))

        dt_full = np.zeros(N, dtype=float)

        # 2. Process each stroke with contemplative pause cadence
        for stroke_idx, (s_start, s_end) in enumerate(strokes):
            stroke_len = s_end - s_start
            stroke_pts = seeds_arr[s_start:s_end]

            if stroke_len <= 2:
                dt_full[s_start:s_end] = 0.06
            else:
                # Sinusoidal velocity profile: slow entry and exit, peak in center
                s_norm = np.linspace(0.08, 0.92, stroke_len)
                v_profile = np.sin(np.pi * s_norm)
                v_clamped = np.clip(v_profile, 0.25, 1.0)

                s_step_dists = np.sqrt(np.sum((stroke_pts[1:] - stroke_pts[:-1]) ** 2, axis=1))
                s_step_dists = np.concatenate(([1.0], s_step_dists))
                dt_full[s_start:s_end] = s_step_dists / v_clamped

            # Explicit contemplative pause between separate glyphs/words
            if stroke_idx > 0:
                jump_dist = dists[s_start - 1]
                # Definite, visible pause (0.08 time weight + distance travel)
                dt_full[s_start] += (jump_dist / 14.0) + 0.08

        # 3. Cumulative integration and normalization
        times = np.cumsum(dt_full)
        t_span = times[-1] - times[0]
        if t_span > 1e-7:
            times = (times - times[0]) / t_span
        else:
            times = np.linspace(0.0, 1.0, N)

        return times
