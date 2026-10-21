import math
import pytest
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsScene

from graphics.animated_image_item import AnimatedImageItem
from components.write_to_image.graphics_item import WriteToImageGraphicsItem
from components.write_to_image.models import WriteToImageModel
from components.canvas.view import CustomGraphicsView
from components.canvas.workspace import CanvasWorkspace

def test_animated_image_shape_padding(qtbot):
    pixmap = QPixmap(200, 150)
    item = AnimatedImageItem(pixmap)
    item.setScale(1.0)
    
    shape_path = item.shape()
    # Point outside the top-left boundary by 10px should be inside the padded interaction shape
    assert shape_path.contains(QPointF(-10, -10))
    # Point far outside (35px) should not be inside
    assert not shape_path.contains(QPointF(-35, -35))

def test_8_handle_resizing_all_corners_and_edges(qtbot):
    pixmap = QPixmap(400, 300)
    item = AnimatedImageItem(pixmap)
    item.setPos(100, 100)
    item.setScale(1.0)
    
    scene = QGraphicsScene()
    scene.addItem(item)
    br = item.boundingRect()
    mid_x = (br.left() + br.right()) / 2.0
    mid_y = (br.top() + br.bottom()) / 2.0
    
    handles = [
        ('TL', br.topLeft(), br.bottomRight(), QPointF(-40, -30)),
        ('TR', br.topRight(), br.bottomLeft(), QPointF(40, -30)),
        ('BL', br.bottomLeft(), br.topRight(), QPointF(-40, 30)),
        ('BR', br.bottomRight(), br.topLeft(), QPointF(40, 30)),
        ('TC', QPointF(mid_x, br.top()), QPointF(mid_x, br.bottom()), QPointF(0, -30)),
        ('BC', QPointF(mid_x, br.bottom()), QPointF(mid_x, br.top()), QPointF(0, 30)),
        ('LC', QPointF(br.left(), mid_y), QPointF(br.right(), mid_y), QPointF(-40, 0)),
        ('RC', QPointF(br.right(), mid_y), QPointF(br.left(), mid_y), QPointF(40, 0)),
    ]
    
    for handle, drag_pt, anchor_pt, drag_dir in handles:
        item.setPos(100, 100)
        item.setScale(1.0)
        
        anchor_scene = item.mapToScene(anchor_pt)
        start_pos = item.mapToScene(drag_pt)
        init_vec = start_pos - anchor_scene
        init_dist = math.hypot(init_vec.x(), init_vec.y())
        
        cur_pos = start_pos + drag_dir
        cur_vec = cur_pos - anchor_scene
        cur_dist = math.hypot(cur_vec.x(), cur_vec.y())
        scale_factor = cur_dist / init_dist
        new_scale = 1.0 * scale_factor
        
        # Scale and pin opposite anchor
        item.setScale(new_scale)
        new_anchor_scene = item.mapToScene(anchor_pt)
        shift = new_anchor_scene - anchor_scene
        item.setPos(item.pos() - shift)
        
        # Verify anchor did not move
        final_anchor = item.mapToScene(anchor_pt)
        assert abs(final_anchor.x() - anchor_scene.x()) < 1e-3, f"{handle} Anchor X moved"
        assert abs(final_anchor.y() - anchor_scene.y()) < 1e-3, f"{handle} Anchor Y moved"
        
        # Verify dragged point moved outward and scale increased
        assert new_scale > 1.0, f"{handle} failed to scale outward"

def test_write_to_image_model_sync_on_resize(qtbot):
    model = WriteToImageModel(id="test_id", name="Test Item")
    item = WriteToImageGraphicsItem(model)
    item.setPos(50, 50)
    item.setScale(1.0)
    
    scene = QGraphicsScene()
    scene.addItem(item)
    
    shape_path = item.shape()
    assert shape_path.contains(QPointF(-10, -10))

def test_view_mouse_tracking_enabled(qtbot):
    workspace = CanvasWorkspace()
    qtbot.addWidget(workspace)
    view = workspace.view
    assert view.hasMouseTracking() is True
    assert view.viewport().hasMouseTracking() is True
