"""
Purpose: Represents the graphical Hand asset used during animation drawing.
Features: Loads hand images (left or right) and provides methods to position the pen tip accurately on the canvas.
"""
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsEllipseItem, QGraphicsDropShadowEffect
from PySide6.QtGui import QPixmap, QColor, QBrush, QPen
from PySide6.QtCore import Qt, QTimer, QPointF
from utils.paths import resource_path
import random

class HandItem(QGraphicsPixmapItem):
    def __init__(self):
        super().__init__()
        self.setZValue(9999) # Always on top of everything
        
        # Ink System state
        self.ink_color = QColor(0, 0, 0)
        self.is_ink_active = False
        self.particles = []
        self.particle_timer = QTimer()
        self.particle_timer.timeout.connect(self._update_particles)
        self.particle_timer.start(30) # ~33 FPS
        
        # Glowing Dot System
        self.ink_dot = QGraphicsEllipseItem(-4, -4, 8, 8, self)
        self.ink_dot.setPen(Qt.PenStyle.NoPen)
        self.ink_dot.setBrush(QBrush(self.ink_color))
        self.ink_dot.setFlags(QGraphicsEllipseItem.GraphicsItemFlag.ItemStacksBehindParent)
        self.ink_dot.setZValue(-1) # Behind the hand
        self.ink_dot.hide()
        
        self.glow_effect = QGraphicsDropShadowEffect()
        self.glow_effect.setBlurRadius(15)
        self.glow_effect.setOffset(0, 0)
        self.glow_effect.setColor(self.ink_color)
        self.ink_dot.setGraphicsEffect(self.glow_effect)
        
        self.right_pixmap = None
        self.left_pixmap = None
        self.current_type = "right"
        self.current_style = "default"
        
        from core.settings_manager import SettingsManager
        self._sm = SettingsManager()
        style = self._sm.get("hand_style", "default")
        self.set_hand_style(style)
        
        # Live update: react immediately when user changes hand style in Settings
        self._sm.settings_changed.connect(self._on_setting_changed)
        
    def _on_setting_changed(self, key: str, value):
        if key == "hand_style":
            self.set_hand_style(value)
        
    def set_hand_style(self, style: str):
        self.current_style = style
        if style == "young_man":
            right_hand_path = "assets/hands/young_man_hand.png"
            left_hand_path = "assets/hand_lift.png" # Fallback for left
        elif style == "old_man":
            right_hand_path = "assets/hands/old_man_hand.png"
            left_hand_path = "assets/hand_lift.png"
        elif style == "woman":
            right_hand_path = "assets/hands/woman_hand.png"
            left_hand_path = "assets/hand_lift.png"
        else:
            right_hand_path = "assets/hend_right.png"
            left_hand_path = "assets/hand_lift.png"
            
        self._load_hands(right_hand_path, left_hand_path)
        self.set_hand_type(self.current_type)
            
    def _load_hands(self, right_path: str, left_path: str):
        pix_r = QPixmap(resource_path(right_path))
        if not pix_r.isNull():
            self.right_pixmap = pix_r.scaledToWidth(500, Qt.TransformationMode.SmoothTransformation)
            
        pix_l = QPixmap(resource_path(left_path))
        if not pix_l.isNull():
            self.left_pixmap = pix_l.scaledToWidth(500, Qt.TransformationMode.SmoothTransformation)
            
    def set_hand_type(self, hand_type: str):
        """Switch between 'left', 'right', and 'none' hand."""
        self.current_type = hand_type
        
        if hand_type == "none":
            self.setPixmap(QPixmap()) # Hide the hand completely
            return
            
        if hand_type == "left" and self.left_pixmap:
            self.setPixmap(self.left_pixmap)
            self.setOffset(-460, -40) 
        elif self.right_pixmap:
            self.setPixmap(self.right_pixmap)
            # Adjust offset based on the style to accurately align the pen tip
            if self.current_style == "young_man":
                self.setOffset(-85, -60) # Accurately aligned to pen tip
            elif self.current_style == "old_man":
                self.setOffset(-105, -70)
            elif self.current_style == "woman":
                self.setOffset(-115, -90)
            else:
                self.setOffset(-40, -40) # Default offset

    def set_ink_color(self, color):
        if not isinstance(color, QColor):
            color = QColor(color)
        if color.isValid():
            self.ink_color = color
            self.ink_dot.setBrush(QBrush(self.ink_color))
            self.glow_effect.setColor(self.ink_color)
            
    def set_ink_active(self, active: bool):
        self.is_ink_active = active
        
        effect_type = self._sm.get("ink_effect_type", "dot")
        
        if self.is_ink_active and effect_type == "dot":
            self.ink_dot.show()
        else:
            self.ink_dot.hide()
        
    def _update_particles(self):
        effect_type = self._sm.get("ink_effect_type", "dot")
        if self.is_ink_active and self.scene() and effect_type == "particles":
            # Spawn new particles
            for _ in range(2): # 2 particles per tick
                size = random.uniform(2, 5)
                p = QGraphicsEllipseItem(-size/2, -size/2, size, size)
                p.setBrush(QBrush(self.ink_color))
                p.setPen(Qt.PenStyle.NoPen)
                
                # Hand tip is always aligned with the item's pos() because of the offset
                tip_pos = self.scenePos()
                scatter_x = random.uniform(-4, 4)
                scatter_y = random.uniform(-4, 4)
                p.setPos(tip_pos.x() + scatter_x, tip_pos.y() + scatter_y)
                p.setZValue(9998) # Behind the hand, but above canvas
                
                # Custom properties for movement
                p.vx = random.uniform(-1.5, 1.5)
                p.vy = random.uniform(-1.5, 1.5)
                p.life = 1.0
                
                self.scene().addItem(p)
                self.particles.append(p)
                
        # Update existing particles
        active_particles = []
        for p in self.particles:
            p.life -= 0.08 # Fades out relatively fast
            if p.life <= 0:
                if p.scene():
                    p.scene().removeItem(p)
            else:
                p.setPos(p.pos().x() + p.vx, p.pos().y() + p.vy)
                p.setOpacity(p.life)
                active_particles.append(p)
                
        self.particles = active_particles
