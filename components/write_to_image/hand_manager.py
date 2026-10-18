from PySide6.QtWidgets import QGraphicsPixmapItem
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QPointF
import os
from core.settings_manager import SettingsManager

class TextHandManager:
    """
    Completely isolated hand manager specifically for the Text Writing Engine.
    This ensures no interference with the core animator_engine.py.
    """
    def __init__(self, scene):
        self.scene = scene
        self.hand_item = QGraphicsPixmapItem()
        self.hand_item.setZValue(9999) # Always on top
        self.hand_item.hide()
        
        if self.scene:
            self.scene.addItem(self.hand_item)
            
        self._load_hand()
        self.is_active = False

    def _load_hand(self):
        settings = SettingsManager()
        hand_style = settings.get("hand_style", "default")
        
        if hand_style == "none":
            self.hand_item.hide()
            return
            
        # Use absolute path to guarantee the image is found
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        hand_image_path = os.path.join(base_dir, "assets", "hend_right.png")
        
        if not os.path.exists(hand_image_path):
            hand_image_path = os.path.join(base_dir, "assets", "hand_right.png")
            
        if os.path.exists(hand_image_path):
            pixmap = QPixmap(hand_image_path)
            self.hand_item.setPixmap(pixmap)
            
            anchor = QPointF(20, pixmap.height() - 20) 
            anchor_str = settings.get("hand_anchor", "0,1")
            try:
                parts = anchor_str.split(',')
                ax = float(parts[0]) * pixmap.width()
                ay = float(parts[1]) * pixmap.height()
                anchor = QPointF(ax, ay)
            except:
                pass
                
            self.hand_item.setOffset(-anchor.x(), -anchor.y())
            
        # Strict hand size from settings, decoupled from text dimensions.
        try:
            hand_size = float(settings.get("hand_size", 3.0))
        except (ValueError, TypeError):
            hand_size = 3.0
            
        # The core engine used to multiply by item scale, causing huge hands.
        # We just use hand_size directly for Text.
        self.hand_item.setScale(hand_size)

    def update_position(self, scene_pos: QPointF, is_drawing: bool):
        settings = SettingsManager()
        if settings.get("hand_style", "default") == "none":
            self.hand_item.hide()
            return
            
        self.hand_item.setPos(scene_pos)
        
        if is_drawing and not self.is_active:
            self.hand_item.show()
            self.is_active = True
        elif not is_drawing and self.is_active:
            self.hand_item.hide()
            self.is_active = False
            
        # Debugging visibility
        print(f"[HandManager LOG] is_drawing={is_drawing}, pos=({scene_pos.x():.1f}, {scene_pos.y():.1f}), active={self.is_active}, visible={self.hand_item.isVisible()}, pixmap_null={self.hand_item.pixmap().isNull()}")

    def remove(self):
        if self.scene and self.hand_item in self.scene.items():
            self.scene.removeItem(self.hand_item)
