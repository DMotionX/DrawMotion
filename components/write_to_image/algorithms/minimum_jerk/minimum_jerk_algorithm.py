"""
Minimum-Jerk Handwriting Algorithm (Smooth Academic).
Based on Flash & Hogan (1985) motor control model of human coordinate movements.
Minimizes the third derivative of position (jerk = d3x/dt3), yielding maximally smooth,
graceful, and non-fatiguing hand trajectories without abrupt starts or stops.
"""

import numpy as np
from ..base_algorithm import BaseWritingAlgorithm


class MinimumJerkAlgorithm(BaseWritingAlgorithm):
    """
    Flash & Hogan Minimum-Jerk Kinematic Model.
    - Applies segment-wise 5th-order minimum jerk polynomials per stroke.
    - Produces extraordinarily smooth, balanced, and steady academic handwriting.
    - Naturally adapts across both Arabic calligraphy and Latin letterforms.
    """

    @property
    def style(self) -> str:
        return "minimum_jerk"

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

        # Precompute lookup for Flash & Hogan 5th order polynomial
        # s(u) = 10*u^3 - 15*u^4 + 6*u^5
        u_lookup = np.linspace(0.0, 1.0, 1000)
        s_lookup = 10.0 * (u_lookup ** 3) - 15.0 * (u_lookup ** 4) + 6.0 * (u_lookup ** 5)

        # 2. Process each stroke with minimum-jerk kinematics
        for stroke_idx, (s_start, s_end) in enumerate(strokes):
            stroke_len = s_end - s_start
            stroke_pts = seeds_arr[s_start:s_end]

            if stroke_len <= 2:
                dt_full[s_start:s_end] = 0.05
            else:
                # Cumulative arc length along the stroke
                seg_dists = np.sqrt(np.sum((stroke_pts[1:] - stroke_pts[:-1]) ** 2, axis=1))
                arc_lens = np.concatenate(([0.0], np.cumsum(seg_dists)))
                total_len = arc_lens[-1]

                if total_len > 1e-4:
                    s_norm = arc_lens / total_len
                    # Map normalized arc length to minimum jerk time parameter u
                    u_pts = np.interp(s_norm, s_lookup, u_lookup)
                    # Instantaneous minimum-jerk velocity: 30 * u^2 * (1 - u)^2
                    # Added baseline floor (0.35) to prevent infinite dt at boundaries
                    v_profile = 0.35 + 0.65 * (30.0 * (u_pts ** 2) * ((1.0 - u_pts) ** 2) / 1.875)
                else:
                    v_profile = np.ones(stroke_len, dtype=float)

                s_step_dists = np.concatenate(([1.0], seg_dists))
                dt_full[s_start:s_end] = s_step_dists / np.clip(v_profile, 0.25, 4.0)

            # Settle pause for pen lift
            if stroke_idx > 0:
                jump_dist = dists[s_start - 1]
                dt_full[s_start] += (jump_dist / 16.0) + 0.035

        # 3. Cumulative integration and normalization
        times = np.cumsum(dt_full)
        t_span = times[-1] - times[0]
        if t_span > 1e-7:
            times = (times - times[0]) / t_span
        else:
            times = np.linspace(0.0, 1.0, N)

        return times
