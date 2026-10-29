"""
Algorithms package for the DrawMotion Text Handwriting Engine.
Provides access to physics-based and kinematic handwriting models.
"""

from typing import Dict, Type
from .base_algorithm import BaseWritingAlgorithm
from .realistic_hybrid import RealisticHybridAlgorithm
from .minimum_jerk.minimum_jerk_algorithm import MinimumJerkAlgorithm
from .two_thirds_power_law.power_law_algorithm import TwoThirdsPowerLawAlgorithm
from .stop_and_go.stop_and_go_algorithm import StopAndGoAlgorithm
from .ou_noise.ou_noise_algorithm import OrnsteinUhlenbeckNoiseAlgorithm
from .linear_interpolation.linear_algorithm import LinearInterpolationAlgorithm
from core.settings_manager import SettingsManager

ALGORITHM_REGISTRY: Dict[str, Type[BaseWritingAlgorithm]] = {
    "realistic_hybrid": RealisticHybridAlgorithm,
    "minimum_jerk": MinimumJerkAlgorithm,
    "two_thirds_power_law": TwoThirdsPowerLawAlgorithm,
    "stop_and_go": StopAndGoAlgorithm,
    "ou_noise": OrnsteinUhlenbeckNoiseAlgorithm,
    "linear": LinearInterpolationAlgorithm,
}

DEFAULT_ALGORITHM = "realistic_hybrid"


def get_writing_algorithm(name: str = None) -> BaseWritingAlgorithm:
    """
    Returns an instantiated handwriting algorithm based on the requested name or user settings.
    Falls back gracefully to RealisticHybridAlgorithm.
    """
    if not name or not isinstance(name, str):
        name = SettingsManager().get("writing_algorithm", DEFAULT_ALGORITHM)

    norm_name = str(name).lower().strip()
    
    # Normalize aliases
    if norm_name in ("hybrid", "default", "realistic"):
        norm_name = "realistic_hybrid"
    elif norm_name in ("jerk", "min_jerk"):
        norm_name = "minimum_jerk"
    elif norm_name in ("power_law", "power", "2/3_power_law"):
        norm_name = "two_thirds_power_law"
    elif norm_name in ("flat", "linear_interpolation"):
        norm_name = "linear"

    algo_class = ALGORITHM_REGISTRY.get(norm_name, RealisticHybridAlgorithm)
    return algo_class()


__all__ = [
    'BaseWritingAlgorithm',
    'RealisticHybridAlgorithm',
    'MinimumJerkAlgorithm',
    'TwoThirdsPowerLawAlgorithm',
    'StopAndGoAlgorithm',
    'OrnsteinUhlenbeckNoiseAlgorithm',
    'LinearInterpolationAlgorithm',
    'ALGORITHM_REGISTRY',
    'get_writing_algorithm',
    'DEFAULT_ALGORITHM',
]
