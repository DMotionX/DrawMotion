import pytest
from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QApplication

from graphics.artboard_item import SceneArtboardItem
from components.canvas.workspace import CanvasWorkspace


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


def test_artboard_initial_duration(qapp):
    """Artboard must be created with default duration of 2.0s, not 8.0s or 0.5s."""
    board = SceneArtboardItem(QRectF(0, 0, 1920, 1080))
    assert board.duration == 2.0
    assert board.user_defined_duration is None


def test_scene_duration_restore_to_2s_after_item_deletion(qapp):
    """
    Core bug fix verification:
    Adding an item expands scene duration.
    Deleting the item must restore scene duration to 2.0s, never shrinking to 0.5s!
    """
    workspace = CanvasWorkspace()
    assert len(workspace.artboards) >= 1
    board = workspace.artboards[0]
    
    # 1. Fresh scene must be 2.0s
    assert board.duration == 2.0
    
    # 2. Mock animated item with 8.0s duration
    class MockAnimItem:
        def __init__(self, parent):
            self._parent = parent
            self._anim_duration = 8.0
            self.anim_duration = 8.0
            self.anim_delay = 0.0
            self.zValue = lambda: 0

        def parentItem(self):
            return self._parent

    mock_item = MockAnimItem(board)
    workspace.user_items.append(mock_item)
    
    # Distribute time with item present
    workspace.distribute_global_time(respect_board_duration=False)
    assert board.duration == 8.0
    
    # 3. Delete item (simulate user pressing Delete key)
    workspace.user_items.remove(mock_item)
    workspace.distribute_global_time(respect_board_duration=False)
    
    # Must restore to 2.0s, NOT 0.5s!
    assert board.duration == 2.0, f"Expected 2.0s, but got {board.duration}s (corrupted shrinkage bug!)"


def test_user_defined_duration_preserved_on_deletion(qapp):
    """
    If user manually set custom scene duration (e.g. 10.0s),
    deleting items should respect the user-defined duration.
    """
    workspace = CanvasWorkspace()
    board = workspace.artboards[0]
    
    # User customizes duration to 10.0s
    workspace.set_scene_duration_and_scale(board, 10.0)
    assert board.duration == 10.0
    assert board.user_defined_duration == 10.0
    
    # Distribute time with no items
    workspace.distribute_global_time(respect_board_duration=False)
    assert board.duration == 10.0


def test_timeline_panel_total_project_duration_and_clamping(qapp):
    """
    Timeline panel compute_total_project_duration must correctly return
    at least 2.0s for empty scenes and clamp playhead progress properly.
    """
    from components.timeline.panel import TimelinePanel
    workspace = CanvasWorkspace()
    panel = TimelinePanel()
    panel.set_workspace(workspace)
    
    # For empty workspace with 1 board (2.0s), total project duration is 2.0s
    total = panel.compute_total_project_duration()
    assert total == 2.0
    
    # Set playhead at 8.0s
    panel.set_playhead_progress(8.0)
    assert panel._last_progress_time == 8.0
    
    # Calling update_timeline must clamp playhead back to 0.0 (or total project duration)
    panel.update_timeline()
    assert panel._last_progress_time <= 2.0
