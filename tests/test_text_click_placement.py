import sys
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QMouseEvent, QPixmap
from components.canvas.workspace import CanvasWorkspace, ToolMode
from components.write_to_image.text_editor import TextEditorWidget
from components.write_to_image.models import WriteToImageModel

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

@pytest.fixture
def workspace(qapp):
    ws = CanvasWorkspace()
    ws.resize(1000, 800)
    ws.focus_on_artboard(0)
    qapp.processEvents()
    yield ws
    try:
        ws.animator_engine.shutdown()
        ws.audio_engine.cleanup()
    except Exception:
        pass
    ws.close()
    ws.deleteLater()
    qapp.processEvents()

def test_text_editor_widget_respects_click_coordinates(qapp):
    """Verify that TextEditorWidget with center_in_view=False places at (x, y)."""
    model = WriteToImageModel(id="test_model", name="Text", text="Hello Click Placement")
    editor = TextEditorWidget(x=150, y=250, existing_model=model, center_in_view=False)
    
    assert editor.x() == 150
    assert editor.y() == 250
    editor.close()
    editor.deleteLater()

def test_text_editor_widget_clamps_to_viewport_boundary(qapp, workspace):
    """Verify that TextEditorWidget clamps inside parent viewport if clicked near bottom-right edge."""
    vp_w = workspace.view.viewport().width()
    vp_h = workspace.view.viewport().height()
    
    # Click near extreme bottom-right edge: (vp_w - 5, vp_h - 5)
    model = WriteToImageModel(id="test_clamp", name="Clamp", text="Edge Click")
    editor = TextEditorWidget(x=vp_w - 5, y=vp_h - 5, existing_model=model, parent=workspace.view, center_in_view=False)
    
    # Editor must be clamped so its right and bottom edges don't overflow
    assert editor.x() + editor.width() <= vp_w
    assert editor.y() + editor.height() <= vp_h
    editor.close()
    editor.deleteLater()

def test_workspace_trigger_write_to_image_at_view_pos(qapp, workspace):
    """Verify that triggering text at view_pos creates editor and places final item at click position."""
    target_board = workspace.artboards[0]
    board_rect = target_board.boundingRect()
    
    # Click point strictly inside the visible viewport and well within max_x
    view_click_pos = QPoint(100, 100)
    
    # Trigger write to image at this position
    workspace.trigger_write_to_image_at_view_pos(view_click_pos)
    
    # Find active TextEditorWidget among workspace.view children
    editors = workspace.view.findChildren(TextEditorWidget)
    assert len(editors) >= 1
    editor = editors[-1]
    
    # Editor x, y should match view_click_pos
    assert abs(editor.x() - view_click_pos.x()) <= 5
    assert abs(editor.y() - view_click_pos.y()) <= 5
    
    # Simulate finishing editing with a dummy image path
    editor.model.image_path = "tests/test_dummy_click.png"
    editor.editing_finished.emit(editor.model)
    qapp.processEvents()
    
    # The new WriteToImageGraphicsItem should exist in user_items
    created_item = workspace.user_items[-1]
    assert created_item.parentItem() is target_board
    
    # Item position should match the click position on the board, NOT the dead center!
    local_center = board_rect.center()
    item_pos = created_item.pos()
    
    # Verify it is significantly distant from the dead center
    center_dist = (item_pos - local_center).manhattanLength()
    assert center_dist > 50, f"Text item placed at {item_pos} which is too close to dead center {local_center}"

def test_image_placement_remains_100_percent_untouched(qapp, workspace, tmp_path):
    """
    CRITICAL USER REQUIREMENT:
    Verify that image addition via add_image_from_path remains 100% UNTOUCHED
    and continues its standard, expected centering on the artboard.
    """
    target_board = workspace.artboards[0]
    board_rect = target_board.boundingRect()
    
    # Create a temporary test image
    test_img_path = str(tmp_path / "test_image.png")
    pix = QPixmap(200, 150)
    pix.fill(Qt.GlobalColor.blue)
    pix.save(test_img_path)
    
    # Add image
    workspace.add_image_from_path(test_img_path)
    qapp.processEvents()
    
    added_image = workspace.user_items[-1]
    assert added_image.parentItem() is target_board
    
    # Image must be centered in target_board as standard
    img_rect = added_image.boundingRect()
    img_scale = added_image.scale()
    expected_center_x = board_rect.center().x() - ((img_rect.width() * img_scale) / 2)
    expected_center_y = board_rect.center().y() - ((img_rect.height() * img_scale) / 2)
    
    assert abs(added_image.pos().x() - expected_center_x) < 2.0
    assert abs(added_image.pos().y() - expected_center_y) < 2.0
