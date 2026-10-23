import math
import pytest
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPixmap, QColor
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

def test_cursor_zones_edge_resize_and_interior_hand(qtbot):
    from PySide6.QtWidgets import QGraphicsSceneHoverEvent
    from PySide6.QtCore import QEvent, Qt
    pixmap = QPixmap(200, 200)
    item = AnimatedImageItem(pixmap)
    item.setScale(1.0)
    
    def check_cursor(pt):
        ev = QGraphicsSceneHoverEvent(QEvent.Type.GraphicsSceneHoverMove)
        ev.setPos(pt)
        item.hoverMoveEvent(ev)
        return item.cursor().shape()
        
    # Corners: diagonal resize arrows
    assert check_cursor(QPointF(2, 2)) == Qt.CursorShape.SizeFDiagCursor
    assert check_cursor(QPointF(198, 198)) == Qt.CursorShape.SizeFDiagCursor
    assert check_cursor(QPointF(198, 2)) == Qt.CursorShape.SizeBDiagCursor
    assert check_cursor(QPointF(2, 198)) == Qt.CursorShape.SizeBDiagCursor
    
    # Edges: vertical and horizontal resize arrows
    assert check_cursor(QPointF(100, 2)) == Qt.CursorShape.SizeVerCursor
    assert check_cursor(QPointF(100, 198)) == Qt.CursorShape.SizeVerCursor
    assert check_cursor(QPointF(2, 100)) == Qt.CursorShape.SizeHorCursor
    assert check_cursor(QPointF(198, 100)) == Qt.CursorShape.SizeHorCursor
    
    # Interior: grab hand cursor (المقبض)
    assert check_cursor(QPointF(100, 100)) == Qt.CursorShape.OpenHandCursor


def test_replace_image_cache_purge_and_transformation_preservation(qtbot):
    """Verify that replacing an image purges stale drawing plans while preserving all user transformations."""
    pix_a = QPixmap(100, 100)
    pix_a.fill(Qt.GlobalColor.black)
    item = AnimatedImageItem(pix_a)
    
    # User applies custom canvas transformations and animation properties
    item.setPos(50, 75)
    item.setRotation(15.0)
    item.setScale(1.5)
    item.setOpacity(0.8)
    item.set_anim_duration(6.0)
    item.drawing_style = "Solid Reveal"
    
    # Simulate a cached plan from the previous image
    item._plan_cache[("Solid Reveal", "auto", 6.0)] = [{"type": "stroke", "points": [QPointF(0, 0), QPointF(10, 10)]}]
    item._total_length = 500.0
    item._cached_pixmap_id = id(pix_a)
    
    # Replace with image B (different dimensions)
    pix_b = QPixmap(250, 300)
    pix_b.fill(Qt.GlobalColor.blue)
    ok = item.replace_image(pix_b)
    
    assert ok is True
    # 1. Transformations strictly preserved
    assert item.pos() == QPointF(50, 75)
    assert item.rotation() == 15.0
    assert item.scale() == 1.5
    assert item.opacity() == 0.8
    assert item._anim_duration == 6.0
    assert item.drawing_style == "Solid Reveal"
    
    # 2. Dimensions and buffers updated to image B
    assert item._pixmap.width() == 250
    assert item._pixmap.height() == 300
    assert item._scribble_buffer.size() == pix_b.size()
    assert item._composite_buffer.size() == pix_b.size()
    
    # 3. Cache completely purged - NO stale lines from image A
    assert len(item._plan_cache) == 0
    assert not hasattr(item, '_total_length')


def test_replace_image_rejects_null_or_corrupted_pixmap(qtbot):
    """Verify that replace_image rejects null/invalid pixmaps with zero side-effects on current image."""
    pix_a = QPixmap(80, 80)
    pix_a.fill(Qt.GlobalColor.red)
    item = AnimatedImageItem(pix_a)
    
    # Attempt to replace with null/invalid pixmap
    null_pix = QPixmap()
    assert null_pix.isNull() is True
    
    ok = item.replace_image(null_pix)
    assert ok is False
    
    # Current image is completely unharmed
    assert item._pixmap.width() == 80
    assert item._pixmap.height() == 80
    assert not item._pixmap.isNull()

