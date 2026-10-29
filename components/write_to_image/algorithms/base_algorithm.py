import numpy as np
from abc import ABC, abstractmethod

class BaseWritingAlgorithm(ABC):
    """
    Architectural base class for handwriting trajectory algorithms.
    All algorithms must inherit this class and implement generate_times.
    """
    
    @property
    @abstractmethod
    def style(self) -> str:
        """Returns the algorithm style identifier."""
        pass

    @property
    def name(self) -> str:
        """Alias for algorithm style identifier."""
        return self.style
        
    @abstractmethod
    def generate_times(self, seeds: list, is_rtl: bool) -> np.ndarray:
        """
        Generates a normalized timestamp array (from 0.0 to 1.0) for every seed.
        """
        pass

