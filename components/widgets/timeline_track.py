from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QPainter, QColor, QPen
import math
from utils.theme import THEME_COLORS

class WaveformFrame(QFrame):
    def __init__(self, parent=None, base_color="#1565C0"):
        super().__init__(parent)
        self.base_color = base_color
        self.setStyleSheet("background-color: transparent; border-radius: 4px;")
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Darken the background color slightly for contrast
        bg_color = QColor(self.base_color)
        bg_color = bg_color.darker(150)
        bg_color.setAlpha(180)
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Visual separation: leave 1px empty on the right side
        # This creates a "cut" line between adjacent clips without changing their true width
        draw_rect = self.rect().adjusted(0, 0, -1, 0)
        painter.drawRoundedRect(draw_rect, 4, 4)
        
        w = self.width()
        h = self.height()
        
        # Make the waveform wave color white/light-gray for high visibility
        wave_color = QColor(255, 255, 255, 200)
        pen = QPen(wave_color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        from PySide6.QtCore import QLineF
        # Increase step size to avoid scrunching
        step = 6
        mid_y = h / 2.0
        for x in range(4, int(w) - 4, step):
            # Slow down the frequency to spread out the waves
            noise = (math.sin(x * 0.1) + math.cos(x * 0.05) + math.sin(x * 0.3)) / 3.0
            amp = (abs(noise) * 0.7 + 0.3) * (h / 2.0 - 6.0)
            painter.drawLine(QLineF(x, mid_y - amp, x, mid_y + amp))

class TimelineTrack(QFrame):
    def __init__(self, item, pixels_per_second=50):
        super().__init__()
        self.item = item
        self.pixels_per_second = pixels_per_second
        self.setFixedHeight(40)
        self.setStyleSheet(f"background-color: {THEME_COLORS['bg_main']}; border-radius: 4px; margin-bottom: 4px;")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self._init_ui()

    def _init_ui(self):
        # Determine color and text
        layer_name = getattr(self.item, 'layer_name', 'Unknown')
        is_text = "Text" in layer_name
        is_image = "AnimatedImageItem" in self.item.__class__.__name__
        is_audio = layer_name in ["Voice", "SFX", "Music"] or hasattr(self.item, 'file_path')
        
        if is_text:
            bg_color = "#E53935" # Red for Text
        elif is_image:
            bg_color = "#1976D2" # Blue for Image
        elif layer_name == "Voice":
            bg_color = "#1565C0"
        elif layer_name == "SFX":
            bg_color = "#6A1B9A"
        elif layer_name == "Music":
            bg_color = "#2E7D32"
        else:
            bg_color = "#455A64"
            
        if is_audio:
            self.block = WaveformFrame(self, base_color=bg_color)
            if hasattr(self.item, 'is_selected') and self.item.is_selected:
                self.block.setStyleSheet(f"background-color: transparent; border-radius: 4px; border: 2px solid white;")
            else:
                self.block.setStyleSheet(f"background-color: transparent; border-radius: 4px;")
        else:
            self.block = QFrame(self)
            if hasattr(self.item, 'is_selected') and self.item.is_selected:
                self.block.setStyleSheet(f"background-color: {bg_color}; border-radius: 4px; border: 2px solid white;")
            else:
                self.block.setStyleSheet(f"background-color: {bg_color}; border-radius: 4px;")
            
        self.block.setFixedHeight(30)
        
        # Calculate width based on duration
        duration = getattr(self.item, 'anim_duration', 2.0)
        
        # Add label inside the block
        block_layout = QHBoxLayout(self.block)
        block_layout.setContentsMargins(4, 0, 4, 0)
        
        if is_audio:
            del_btn = QPushButton("X")
            del_btn.setFixedSize(20, 20)
            del_btn.setStyleSheet("""
                QPushButton { 
                    background-color: transparent; 
                    color: #FFCDD2; 
                    border: none; 
                    font-weight: bold; 
                    font-size: 12px; 
                    padding: 0px;
                    margin: 0px;
                } 
                QPushButton:hover { 
                    color: white; 
                    background-color: #E53935;
                    border-radius: 10px;
                }
            """)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            def on_delete():
                panel = self
                while panel and not hasattr(panel, 'delete_item_requested'):
                    panel = panel.parentWidget()
                if panel:
                    panel.delete_item_requested.emit(self.item)
                    
            del_btn.clicked.connect(on_delete)
            block_layout.addWidget(del_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
            
        name_label = QLabel(f"{layer_name} ({duration:.1f}s)")
        name_label.setObjectName("timeLabel")
        name_label.setStyleSheet("color: white; font-size: 10px; background: transparent;")
        block_layout.addWidget(name_label)
        block_layout.addStretch()
        
        width = int(duration * self.pixels_per_second)
        self.block.setFixedWidth(max(10, width))
        
        self.layout.addWidget(self.block)
        
        # Set absolute fixed width for the entire track to prevent layout shrinking
        self.setFixedWidth(max(10, width))

    def mousePressEvent(self, event: QMouseEvent):
        self.setFocus()
        panel = self
        while panel and not hasattr(panel, 'delete_item_requested'):
            panel = panel.parentWidget()
        if panel and hasattr(panel, 'workspace') and panel.workspace and self.item:
            panel.workspace.item_selected.emit(self.item)

    def mouseMoveEvent(self, event: QMouseEvent):
        pass

    def mouseReleaseEvent(self, event: QMouseEvent):
        pass
            
    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #222A27; color: white; border: 1px solid #2E8B57; } QMenu::item:selected { background-color: #F44336; }")
        
        delete_action = menu.addAction("Delete Item")
        action = menu.exec_(event.globalPos())
        
        if action == delete_action:
            panel = self
            while panel and not hasattr(panel, 'delete_item_requested'):
                panel = panel.parentWidget()
            if panel:
                panel.delete_item_requested.emit(self.item)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            panel = self
            while panel and not hasattr(panel, 'delete_item_requested'):
                panel = panel.parentWidget()
class DraggableBlock(QFrame):
    def __init__(self, data, pixels_per_second, parent=None):
        super().__init__(parent)
        self.data = data
        self.pixels_per_second = pixels_per_second
        self.item = data.get('item', None)
        self.duration = data.get('duration', 2.0)
        
        self.block_color = data.get('color', THEME_COLORS['primary_green'])
        
        self.setObjectName("DragBlock")
        if data.get('is_scene_block') and data.get('is_active'):
            self.setStyleSheet(f"#DragBlock {{ background-color: {self.block_color}; border-radius: 4px; border: 2px solid white; }}")
        else:
            self.setStyleSheet(f"#DragBlock {{ background-color: {self.block_color}; border-radius: 4px; border: none; }}")
        self.setFixedHeight(30)
        
        base_label = data.get('label', '')
        
        # [PHASE 2 FIX]: Differentiate items by analyzing the item type
        if self.item and not data.get('is_scene_block', False):
            class_name = self.item.__class__.__name__
            if "WriteToAnimatedImageItem" in class_name or "WriteToImageGraphicsItem" in class_name:
                base_label = f"[Text] {base_label}"
            elif "AnimatedStrokeItem" in class_name:
                base_label = f"[Shape] {base_label}"
            elif "MindMap" in class_name:
                base_label = f"[Template] {base_label}"
            elif "SVGCanvasItem" in class_name or "AnimatedImageItem" in class_name:
                base_label = f"[Image] {base_label}"
                
        self.lbl = QLabel(f"{base_label} ({self.duration:.1f}s)")
        self.lbl.setStyleSheet("color: white; font-size: 10px; background: transparent;")
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.addWidget(self.lbl)
        
        self._update_width()
        self.setMouseTracking(True)
        self._resizing = False
        self._drag_start_x = 0
        self._original_width = 0

    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #222A27; color: white; border: 1px solid #2E8B57; } QMenu::item:selected { background-color: #F44336; }")
        
        is_scene = self.data.get('is_scene_block', False)
        
        if is_scene:
            add_action = menu.addAction("Add Scene")
            delete_action = menu.addAction("Delete Scene")
            menu.addSeparator()
            trans_menu = menu.addMenu("Transition Effect")
            t_fade = trans_menu.addAction("Fade")
            t_slide = trans_menu.addAction("Slide")
            t_wipe = trans_menu.addAction("Wipe")
            t_zoom = trans_menu.addAction("Zoom")
            t_iris = trans_menu.addAction("Iris")
            t_none = trans_menu.addAction("None")
            
            action = menu.exec_(event.globalPos())
            
            # Find the panel to get to the workspace
            panel = self
            while panel and panel.__class__.__name__ != "TimelinePanel":
                panel = panel.parentWidget()
                
            if action == add_action:
                if panel and panel.workspace:
                    panel.workspace.add_new_scene()
            elif action == delete_action:
                if panel and panel.workspace and self.item:
                    panel.workspace.delete_scene(self.item.scene_index - 1)
            elif action in (t_fade, t_slide, t_wipe, t_zoom, t_iris, t_none):
                if self.item:
                    val = action.text().lower()
                    if val == "none":
                        self.item.transition_type = None
                    else:
                        self.item.transition_type = val
                    if panel and panel.workspace:
                        panel.workspace.items_changed.emit(panel.workspace.user_items)
        else:
            delete_action = menu.addAction("Delete Item")
            action = menu.exec_(event.globalPos())
            
            if action == delete_action:
                panel = self
                while panel and not hasattr(panel, 'delete_item_requested'):
                    panel = panel.parentWidget()
                if panel:
                    panel.delete_item_requested.emit(self.item)

    def _update_width(self):
        self.setFixedWidth(max(10, int(self.duration * self.pixels_per_second)))
        self.lbl.setText(f"{self.data.get('label', '')} ({self.duration:.1f}s)")

    def mouseMoveEvent(self, event: QMouseEvent):
        if not getattr(self, '_resizing', False) and not getattr(self, '_dragging_block', False):
            if event.position().x() > self.width() - 10:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.SizeAllCursor) # Cursor for moving
        elif getattr(self, '_resizing', False):
            dx = event.globalPosition().x() - self._drag_start_x
            new_width = max(10, self._original_width + dx)
            new_duration = new_width / self.pixels_per_second
            self.duration = new_duration
            self._update_width()
            
            # Update the item if possible
            if self.item:
                if hasattr(self.item, 'duration'):
                    self.item.duration = new_duration
                elif hasattr(self.item, 'anim_duration'):
                    self.item.anim_duration = new_duration
        elif getattr(self, '_dragging_block', False):
            self._was_dragged = True
            dx = event.globalPosition().x() - self._drag_start_x
            new_x = max(0, self._original_x + dx)
            self.move(int(new_x), self.y())
            new_delay = new_x / self.pixels_per_second
            
            if self.item:
                self.item.anim_delay = new_delay

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.position().x() > self.width() - 10:
                self._resizing = True
                self._drag_start_x = event.globalPosition().x()
                self._original_width = self.width()
                event.accept()
            else:
                if not self.data.get('is_scene_block', False):
                    self._dragging_block = True
                    self._drag_start_x = event.globalPosition().x()
                    self._original_x = self.x()
                self._was_dragged = False
                event.accept()
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        if getattr(self, '_resizing', False) or (getattr(self, '_dragging_block', False) and getattr(self, '_was_dragged', False)):
            self._resizing = False
            self._dragging_block = False
            self._was_dragged = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
            # Find TimelinePanel to notify workspace of the new duration/delay
            panel = self
            while panel and not hasattr(panel, 'delete_item_requested'):
                panel = panel.parentWidget()
            
            if panel and hasattr(panel, 'workspace') and panel.workspace:
                is_scene = self.data.get('is_scene_block', False)
                if is_scene and self.item:
                    # set_scene_duration_and_scale internally calls distribute_global_time(respect_board_duration=True)
                    panel.workspace.set_scene_duration_and_scale(self.item, self.duration)
                else:
                    # Item changed, recalculate board from items total
                    panel.workspace.distribute_global_time(respect_board_duration=False)
                    
                if hasattr(panel.workspace, 'items_changed'):
                    panel.workspace.items_changed.emit(panel.workspace.user_items)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            # Select item on simple click
            panel = self
            while panel and not hasattr(panel, 'delete_item_requested'):
                panel = panel.parentWidget()
            if panel and hasattr(panel, 'workspace') and panel.workspace and self.item:
                panel.workspace.item_selected.emit(self.item)
            
            # If clicked without resizing/dragging, and it's a scene block, focus on the scene
            if self.data.get('is_scene_block', False):
                panel = self
                while panel and panel.__class__.__name__ != "TimelinePanel":
                    panel = panel.parentWidget()
                if panel and hasattr(panel, 'workspace') and panel.workspace and self.item:
                    try:
                        idx = panel.workspace.artboards.index(self.item)
                        panel.workspace.focus_on_artboard(idx)
                    except ValueError:
                        pass


class TransitionBlock(QFrame):
    """
    A purple/color pill rendered on the timeline track between two scene blocks
    to indicate a transition effect is assigned between those scenes.
    Supports right-click to change or remove the transition.
    """
    TRANSITION_COLORS = {
        'fade':  '#7C3AED',
        'slide': '#2563EB',
        'wipe':  '#059669',
        'zoom':  '#D97706',
        'iris':  '#DB2777',
    }
    DEFAULT_COLOR = '#4A1D96'

    def __init__(self, artboard, transition_type: str, duration_sec: float = 0.5,
                 pixels_per_second: int = 50, parent=None):
        super().__init__(parent)
        self.artboard = artboard          # The artboard BEFORE this transition
        self.transition_type = transition_type
        self.duration_sec = duration_sec
        self.pixels_per_second = pixels_per_second
        self.is_empty = (transition_type == "None" or not transition_type)

        if self.is_empty:
            self.setStyleSheet("""
                QFrame {
                    background-color: transparent;
                }
                QFrame:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)
            self.setToolTip("Add Transition")
        else:
            accent = self.TRANSITION_COLORS.get(transition_type, self.DEFAULT_COLOR)
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {accent}CC;
                    border: 1px solid {accent};
                    border-radius: 3px;
                }}
            """)
            self.setToolTip(f"Transition: {transition_type.title()}\nRight-click to change or remove\nDrag edges to resize")
            
        self.setFixedHeight(30)
        self.setFixedWidth(max(16, int(duration_sec * pixels_per_second)))
        
        # Resizing support
        self.setMouseTracking(True)
        self._resizing = False
        self._drag_start_x = 0
        self._original_width = 0

    def _update_width(self):
        self.setFixedWidth(max(10, int(self.duration_sec * self.pixels_per_second)))

    def mouseMoveEvent(self, event):
        from PySide6.QtCore import Qt
        if not self._resizing:
            if event.position().x() > self.width() - 10:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            dx = event.globalPosition().x() - self._drag_start_x
            new_width = max(10, self._original_width + dx)
            new_duration = new_width / self.pixels_per_second
            self.duration_sec = new_duration
            self._update_width()
            
            # Update the item
            if self.artboard:
                self.artboard.transition_duration = new_duration

    def mousePressEvent(self, event):
        from PySide6.QtCore import Qt
        if getattr(self, 'is_empty', False):
            if event.button() == Qt.MouseButton.LeftButton:
                self.contextMenuEvent(event)
                event.accept()
            return
            
        if event.button() == Qt.MouseButton.LeftButton and event.position().x() > self.width() - 10:
            self._resizing = True
            self._drag_start_x = event.globalPosition().x()
            self._original_width = self.width()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        from PySide6.QtCore import Qt
        if event.button() == Qt.MouseButton.LeftButton and self._resizing:
            self._resizing = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
            # Re-compile global time
            panel = self
            while panel and panel.__class__.__name__ != "TimelinePanel":
                panel = panel.parentWidget()
            if panel and panel.workspace:
                panel.workspace.distribute_global_time()
                
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        from PySide6.QtGui import QPainter, QColor, QPen
        from PySide6.QtCore import QPointF, Qt
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        if getattr(self, 'is_empty', False):
            # Draw a subtle separator line
            pen = QPen(QColor(255, 255, 255, 50), 1)
            painter.setPen(pen)
            painter.drawLine(int(cx), 2, int(cx), int(h-2))
            
            # Draw + icon
            pen = QPen(QColor(255, 255, 255, 200), 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(cx - 3, cy), QPointF(cx + 3, cy))
            painter.drawLine(QPointF(cx, cy - 3), QPointF(cx, cy + 3))
        else:
            # Draw a small 4-pointed star icon in the center
            r_outer, r_inner = 5.0, 2.5
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(255, 255, 255, 200))
            import math
            points = []
            for i in range(8):
                angle = math.radians(i * 45 - 90)
                r = r_outer if i % 2 == 0 else r_inner
                points.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))
            from PySide6.QtGui import QPolygonF
            painter.drawPolygon(QPolygonF(points))
            
        painter.end()

    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QMenu, QWidgetAction, QWidget, QGridLayout, QPushButton
        from PySide6.QtGui import QAction, QColor, QPainter
        from PySide6.QtCore import Qt
        from core.transitions.effects import TRANSITION_METADATA
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1A1D1A; color: white;
                    border: 1px solid #4A1D96; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 20px 6px 8px; border-radius: 4px; margin: 2px; }
            QMenu::item:selected { background-color: #7C3AED; }
        """)

        # Custom Grid for transitions
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)
        grid_layout.setContentsMargins(10, 10, 10, 10)
        
        row, col = 0, 0
        for meta in TRANSITION_METADATA:
            btn = QPushButton(meta['label'])
            btn.setFixedSize(80, 80)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            is_active = (meta['id'] == getattr(self, 'transition_type', None) and not getattr(self, 'is_empty', False))
            accent = meta['color']
            bg_color = f"{accent}80" if is_active else "#2A2D2A"
            border = f"2px solid {accent}" if is_active else "1px solid #444"
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    border: {border};
                    border-radius: 12px;
                    color: white;
                    font-size: 13px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {accent};
                    border: 2px solid white;
                }}
            """)
            
            t_id = meta['id']
            btn.setProperty("transition_id", t_id)
            btn.setProperty("parent_menu", menu)
            btn.clicked.connect(self._on_transition_btn_clicked)
            grid_layout.addWidget(btn, row, col)
            
            col += 1
            if col > 3:  # 4 columns for a better grid look
                col = 0
                row += 1
                
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(grid_widget)
        scroll_area.setMaximumHeight(220) # Prevent overflowing screen
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: rgba(0, 0, 0, 0.2);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #7C3AED;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        grid_action = QWidgetAction(menu)
        grid_action.setDefaultWidget(scroll_area)
        menu.addAction(grid_action)
        
        if not getattr(self, 'is_empty', False):
            menu.addSeparator()
            remove_act = QAction("🚫 Remove Transition", self)
            remove_act.triggered.connect(self._remove_transition)
            menu.addAction(remove_act)

        menu.exec_(event.globalPos())

    def _on_transition_btn_clicked(self):
        sender = self.sender()
        if sender:
            tid = sender.property("transition_id")
            menu = sender.property("parent_menu")
            if tid is not None:
                self._set_transition(tid)
            if menu:
                menu.close()

    def _set_transition(self, transition_id: str):
        self.artboard.transition_type = transition_id
        
        # Fix shrink bug: Default to 1.0s if empty or very short
        if getattr(self, 'is_empty', False) or self.duration_sec < 0.2:
            self.duration_sec = 1.0
            self.artboard.transition_duration = 1.0
            self.is_empty = False
            self._update_width()

        accent = self.TRANSITION_COLORS.get(transition_id, self.DEFAULT_COLOR)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {accent}CC;
                border: 1px solid {accent};
                border-radius: 3px;
            }}
        """)
        self.transition_type = transition_id
        self.update()
        
        # Trigger re-layout so timeline expands smoothly
        panel = self
        while panel and panel.__class__.__name__ != "TimelinePanel":
            panel = panel.parentWidget()
        if panel and hasattr(panel, 'workspace') and panel.workspace:
            panel.workspace.distribute_global_time()

    def _remove_transition(self):
        self.artboard.transition_type = None
        self.artboard.transition_duration = 1.0
        
        # Trigger re-layout
        panel = self
        while panel and panel.__class__.__name__ != "TimelinePanel":
            panel = panel.parentWidget()
        if panel and panel.workspace:
            panel.workspace.distribute_global_time()
            
        self.hide()
        self.deleteLater()


class MultiBlockTrack(QFrame):
    def __init__(self, pixels_per_second=50):
        super().__init__()
        self.pixels_per_second = pixels_per_second
        self.setFixedHeight(40)
        self.setStyleSheet(f"background-color: transparent; border-radius: 4px; margin-bottom: 4px;")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
    def set_blocks(self, blocks_data):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        blocks_data = sorted(blocks_data, key=lambda x: x.get('start', 0))
        current_time = 0.0
        prev_block_data = None
        
        for data in blocks_data:
            start_time = data.get('start', 0.0)
            duration = data.get('duration', 2.0)
            
            # Check if the PREVIOUS block's artboard has a transition assigned
            if prev_block_data is not None:
                prev_artboard = prev_block_data.get('item', None)
                t_type = getattr(prev_artboard, 'transition_type', None) if prev_artboard else None
                
                if t_type:
                    # Insert the transition block between the two scene blocks
                    t_block = TransitionBlock(
                        artboard=prev_artboard,
                        transition_type=t_type,
                        duration_sec=0.5,
                        pixels_per_second=self.pixels_per_second,
                    )
                    self.layout.addWidget(t_block)
                    current_time += 0.5
            
            if start_time > current_time:
                gap = start_time - current_time
                spacer = QWidget()
                spacer.setFixedWidth(int(gap * self.pixels_per_second))
                self.layout.addWidget(spacer)
                current_time = start_time
                
            block = DraggableBlock(data, self.pixels_per_second)
            self.layout.addWidget(block)
            current_time += duration
            prev_block_data = data
            
        self.layout.addStretch()

