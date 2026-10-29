"""
Linear Interpolation Handwriting Algorithm (Steady Uniform).
Produces constant arc-length speed across the entire skeleton path.
Serves as an objective baseline and ideal choice for uniform tickers or mechanical reveal effects.
"""

import numpy as np
from ..base_algorithm import BaseWritingAlgorithm


class LinearInterpolationAlgorithm(BaseWritingAlgorithm):
    """
    Uniform Arc-Length Kinematic Model.
    - Constant Cartesian pen speed (uniform pixels per second).
    - Unvarying reveal flow from start to finish.
    """

    @property
    def style(self) -> str:
        return "linear_interpolation"

    def generate_times(self, seeds: list, is_rtl: bool) -> np.ndarray:
        if not seeds:
            return np.array([], dtype=float)

        N = len(seeds)
        if N <= 2:
            return np.linspace(0.0, 1.0, N)

        seeds_arr = np.array(seeds, dtype=float)

        # Compute cumulative Euclidean arc lengths
        dists = np.sqrt(np.sum((seeds_arr[1:] - seeds_arr[:-1]) ** 2, axis=1))
        arc_lengths = np.concatenate(([0.0], np.cumsum(dists)))

        total_length = arc_lengths[-1]
        if total_length > 1e-6:
            return arc_lengths / total_length

        return np.linspace(0.0, 1.0, N)
