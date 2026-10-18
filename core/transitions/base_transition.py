"""
Purpose: Abstract base class for all scene transition effects.
Every transition must implement the `play` method.
"""
from abc import ABC, abstractmethod


class BaseTransition(ABC):
    """
    Abstract base class defining the contract for all transition effects.
    Each effect must implement `play()` which animates an overlay widget.
    """

    # Default duration in milliseconds
    DEFAULT_DURATION_MS = 500

    def __init__(self, color: str = "#000000", duration_ms: int = None):
        """
        Args:
            color: The hex color of the transition overlay (e.g. '#000000' for black fade).
            duration_ms: Total duration of the transition in milliseconds.
        """
        self.color = color
        self.duration_ms = duration_ms or self.DEFAULT_DURATION_MS

    @abstractmethod
    def play(self, overlay_widget, on_midpoint=None, on_finished=None):
        """
        Animate the overlay widget.

        Args:
            overlay_widget: The QWidget overlay drawn on top of the canvas.
            on_midpoint: Callable — called at the midpoint of the transition
                         (when the screen is fully covered). Use this to move
                         the camera / start drawing the next scene.
            on_finished: Callable — called when the transition is fully done.
                         Use this to remove and destroy the overlay.
        """
        pass

    @property
    def half_duration_ms(self) -> int:
        return self.duration_ms // 2
