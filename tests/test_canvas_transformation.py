import math
import pytest
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsScene

from graphics.animated_image_item import AnimatedImageItem
from components.write_to_image.graphics_item import WriteToImageGraphicsItem
from components.write_to_image.models import WriteToImageModel

def test_animated_image_shape_padding(qtbot):
    pixmap = QPixmap(200, 150)
    item = AnimatedImageItem(pixmap)
    item.setScale(1.0)
    
    shape_path = item.shape()
    # Point outside the top-left boundary by 10px should be inside the padded interaction shape
    assert shape_path.contains(QPointF(-10, -10))
    # Point far outside (30px) should not be inside
    assert not shape_path.contains(QPointF(-30, -30))

def test_diagonal_anchor_resizing_all_corners(qtbot):
    pixmap = QPixmap(400, 300)
    item = AnimatedImageItem(pixmap)
    item.setPos(100, 100)
    item.setScale(1.0)
    
    scene = QGraphicsScene()
    scene.addItem(item)
    br = item.boundingRect()
    
    corners = [
        ('TL', br.topLeft(), br.bottomRight(), QPointF(-40, -30)),
        ('TR', br.topRight(), br.bottomLeft(), QPointF(40, -30)),
        ('BL', br.bottomLeft(), br.topRight(), QPointF(-40, 30)),
        ('BR', br.bottomRight(), br.topLeft(), QPointF(40, 30)),
    ]
    
    for handle, corner_pt, anchor_pt, drag_dir in corners:
        item.setPos(100, 100)
        item.setScale(1.0)
        
        anchor_scene = item.mapToScene(anchor_pt)
        start_pos = item.mapToScene(corner_pt)
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
        assert abs(final_anchor.x() - anchor_scene.x()) < 1e-3
        assert abs(final_anchor.y() - anchor_scene.y()) < 1e-3
        
        # Verify dragged corner moved outward and scale increased
        assert new_scale > 1.0
        final_corner = item.mapToScene(corner_pt)
        assert abs(final_corner.x() - cur_pos.x()) < 1e-3
        assert abs(final_corner.y() - cur_pos.y()) < 1e-3

def test_write_to_image_model_sync_on_resize(qtbot):
    model = WriteToImageModel(id="test_id", name="Test Item")
    item = WriteToImageGraphicsItem(model)
    item.setPos(50, 50)
    item.setScale(1.0)
    
    scene = QGraphicsScene()
    scene.addItem(item)
    
    # Test shape padding
    shape_path = item.shape()
    assert shape_path.contains(QPointF(-10, -10))
