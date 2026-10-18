"""
Transition Manager: Orchestrates transition playback as an independent overlay
on top of the canvas view, without stopping the animation engine.
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from core.transitions.effects import TRANSITION_REGISTRY, TRANSITION_METADATA


class TransitionManager:
    """
    Manages and plays scene transition effects on the canvas view.
    The transition overlay is completely independent of the drawing engine
    — the hand continues drawing while the transition plays visually.
    """

    DEFAULT_TRANSITION_COLOR = "#000000"  # Black
    DEFAULT_TRANSITION_TYPE = None        # No transition by default

    def __init__(self, view_widget: QWidget):
        """
        Args:
            view_widget: The CustomGraphicsView widget that the overlay will be parented to.
        """
        self._view = view_widget
        self._active_overlay: QWidget | None = None
        self._active_transition = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def play_transition(self, transition_type: str, color: str = None, duration_sec: float = 1.0,
                        on_scene_start=None, on_finished=None):
        """
        Play a named transition effect as a widget overlay on the canvas view.

        Args:
            transition_type: Key from TRANSITION_REGISTRY (e.g. 'fade', 'slide').
            color: Hex color string for the overlay (defaults to black).
            duration_sec: Duration of the transition in seconds.
            on_scene_start: Callable — invoked at the midpoint of the transition,
                            i.e. when the overlay fully covers the screen.
                            Use this to pan the camera to the next scene.
            on_finished: Callable — invoked when the transition animation is complete
                         and the overlay has been removed.
        """
        if transition_type not in TRANSITION_REGISTRY:
            # No-op: if type is unknown, just call callbacks immediately
            if on_scene_start:
                on_scene_start()
            if on_finished:
                on_finished()
            return

        # Kill any currently running transition
        self._cleanup_overlay()

        cls = TRANSITION_REGISTRY[transition_type]
        transition = cls(color=color or self.DEFAULT_TRANSITION_COLOR, duration_ms=int(duration_sec * 1000))
        self._active_transition = transition

        # Create overlay containing a snapshot of the CURRENT scene
        overlay = self._create_overlay()

        # Optimize viewport during transition to prevent audio stutter
        from PySide6.QtWidgets import QGraphicsView
        original_mode = self._view.viewportUpdateMode()
        self._view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)

        # IMPORTANT: Immediately move the camera to the NEXT scene,
        # so it's ready behind our snapshot overlay!
        if on_scene_start:
            on_scene_start()

        def _on_midpoint():
            pass # No longer needed, camera already moved!

        def _on_done():
            self._view.setViewportUpdateMode(original_mode)
            self._cleanup_overlay()
            if on_finished:
                on_finished()

        # The transition effect now only needs to animate the snapshot OUT
        transition.play(overlay, on_midpoint=_on_midpoint, on_finished=_on_done)

    @staticmethod
    def get_metadata():
        """Returns the list of transition metadata dicts for building the UI picker."""
        return TRANSITION_METADATA

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_overlay(self) -> QWidget:
        """Creates an overlay containing a snapshot of the current view."""
        from PySide6.QtWidgets import QLabel
        from PySide6.QtGui import QPixmap
        
        # Grab a snapshot of what the user is currently seeing (Scene 1)
        pixmap = self._view.grab()
        
        overlay = QLabel(self._view)
        overlay.setPixmap(pixmap)
        overlay.setScaledContents(True)
        
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        overlay.setGeometry(self._view.rect())
        overlay.raise_()
        overlay.show()
        
        self._active_overlay = overlay
        return overlay

    def _cleanup_overlay(self):
        """Hides and destroys the active overlay if it exists."""
        if self._active_overlay is not None:
            try:
                self._active_overlay.hide()
                self._active_overlay.deleteLater()
            except RuntimeError:
                pass
            self._active_overlay = None
        self._active_transition = None
