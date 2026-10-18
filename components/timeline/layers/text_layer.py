"""
Text Layer Row — one block per EditableTextNode item.
Icon: bold 'T' inside rounded rectangle.
Accent: dark red #B71C1C.
"""
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QRectF
from PySide6.QtWidgets import QWidget, QFrame
from components.timeline.layers.base_layer_row import BaseLayerRow
from components.widgets.timeline_track import DraggableBlock


class TextLayerRow(BaseLayerRow):
    LABEL_TEXT   = "Elements"
    ACCENT_COLOR = "#B71C1C"

    def draw_icon(self, painter: QPainter, rect):
        c = QColor(self.ACCENT_COLOR)
        painter.setPen(QPen(c, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(1, 1, rect.width()-2, rect.height()-2), 3, 3)
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.setPen(c)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "E")

    def _build_track_frame(self) -> QFrame:
        # Override to use absolute positioning instead of QHBoxLayout
        frame = QFrame()
        frame.setFixedHeight(36) # TRACK_HEIGHT
        from utils.theme import THEME_COLORS
        frame.setStyleSheet(f"background-color: {THEME_COLORS['bg_secondary']}; border: none;")
        return frame

    def _clear_track(self):
        # Delete all child widgets (DraggableBlocks)
        for child in self._track_frame.children():
            if isinstance(child, QWidget):
                child.deleteLater()

    def _populate_track(self):
        self._clear_track()
        if not self._workspace:
            return

        # Include all animatable items
        anim_items = [
            i for i in self._workspace.user_items
            if hasattr(i, 'anim_duration') or hasattr(i, '_anim_duration')
        ]
        
        blocks = []
        for item in anim_items:
            # anim_delay is absolute time (calculated by distribute_global_time)
            start  = getattr(item, 'anim_delay', 0.0)
            dur    = getattr(item, 'anim_duration', getattr(item, '_anim_duration', 2.0))
            
            class_name = item.__class__.__name__
            
            if class_name == "AnimatedImageItem":
                color = "#FB8C00" # Orange for Images
                label = "Image"
            elif "WriteToAnimatedImageItem" in class_name or "WriteToImageGraphicsItem" in class_name:
                color = "#E53935" # Red for Text
                label = "Text"
            elif "AnimatedStrokeItem" in class_name:
                color = "#8E24AA" # Purple for Shape
                label = "Shape"
            elif "MindMap" in class_name or "SVGCanvasItem" in class_name:
                color = "#3949AB" # Indigo for Template
                label = "Template"
            else:
                color = self.ACCENT_COLOR
                label = "Element"
                
            blocks.append({'start': start, 'duration': dur,
                           'color': color, 'label': label, 'item': item})
                           
        blocks.sort(key=lambda x: x['start'])

        # Create blocks using absolute positioning with static frame height (Cascading Overlap)
        rows = [] # list of end_times for each row
        
        for data in blocks:
            start_px = int(data['start'] * self._pps)
            width_px = max(10, int(data['duration'] * self._pps))
            end_px = start_px + width_px
            
            # Find an available row (with a minimum 10px natural horizontal gap)
            row_idx = -1
            for i, row_end in enumerate(rows):
                if start_px >= row_end + 10:
                    row_idx = i
                    rows[i] = end_px
                    break
                    
            if row_idx == -1:
                row_idx = len(rows)
                rows.append(end_px)
                
            block = DraggableBlock(data, self._pps)
            block.setParent(self._track_frame)
            
            # Cascading offset: shift down by 4px for each overlap level to a max of 3 levels
            # The height of the block is 30px, and track is 36px, so up to y=6 fits perfectly!
            visual_row = min(row_idx, 3) 
            y_pos = 1 + (visual_row * 2)  # 1, 3, 5, 7
            block.move(start_px, y_pos)
            block.show()

