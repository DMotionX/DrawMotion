"""
Images Layer Row — one block per scene that has content.
Icon: landscape photo (rectangle + mountain + sun circle).
Accent: green #2E8B57.
"""
from PySide6.QtGui import QPainter, QColor, QPen, QPolygonF
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtWidgets import QWidget
from components.timeline.layers.base_layer_row import BaseLayerRow
from PySide6.QtWidgets import QPushButton, QMenu
from PySide6.QtGui import QIcon, QCursor
from components.widgets.timeline_track import DraggableBlock, TransitionBlock


class SceneDraggableBlock(DraggableBlock):
    """DraggableBlock that also focuses the artboard when clicked (not dragged)."""
    def __init__(self, data, pixels_per_second, workspace, scene_index, is_last_scene=False, parent=None):
        super().__init__(data, pixels_per_second, parent)
        self._workspace = workspace
        self._scene_index = scene_index

    def mouseReleaseEvent(self, event):
        # Capture the state BEFORE super() clears it
        was_resizing = getattr(self, '_resizing', False)
        
        # Let DraggableBlock handle resize and workspace notifications first
        super().mouseReleaseEvent(event)
        
        # Then focus on this scene (only if not resizing)
        if not was_resizing and self._workspace:
            try:
                self._workspace.focus_on_artboard(self._scene_index)
                
                # Jump the timeline to the end of the scene to reveal all its items
                if hasattr(self._workspace, 'animator_engine') and self.data:
                    # Seek just slightly before the end to avoid triggering the next scene's focus
                    end_time = self.data['start'] + self.data['duration'] - 0.01
                    self._workspace.animator_engine.seek(end_time)
            except Exception:
                pass

class ScenesLayerRow(BaseLayerRow):
    LABEL_TEXT   = "Scene"
    ACCENT_COLOR = "#2E8B57"

    # ── Icon ─────────────────────────────────────────────────────
    def draw_icon(self, painter: QPainter, rect):
        c = QColor(self.ACCENT_COLOR)
        painter.setPen(QPen(c, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(1, 1, rect.width()-2, rect.height()-2), 2, 2)

        # Mountain
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(c.red(), c.green(), c.blue(), 180))
        w, h = rect.width(), rect.height()
        painter.drawPolygon(QPolygonF([
            QPointF(2, h-3), QPointF(w/2, h/2), QPointF(w-2, h-3),
        ]))
        # Sun
        painter.setBrush(QColor(c.red(), c.green(), c.blue(), 220))
        painter.drawEllipse(QRectF(w*0.6, 3, 4, 4))

    # ── Track ─────────────────────────────────────────────────────
    def _populate_track(self):
        self._clear_track()
        if not self._workspace:
            self._track_layout.addStretch()
            return

        blocks = []
        current_time = 0.0
        for i, board in enumerate(self._workspace.artboards):
            if current_time > 0 and i > 0:
                prev_board = self._workspace.artboards[i - 1]
                t_type = getattr(prev_board, 'transition_type', None)
                t_dur = 0.2
                if t_type and t_type != "None":
                    t_dur = getattr(prev_board, 'transition_duration', 1.0)
                current_time += t_dur
            base_dur = getattr(board, 'duration', 8.0)
            items = [i for i in self._workspace.user_items if i.parentItem() == board]
            
            # Find the actual compiled end time for this scene from the scheduler
            max_item_dur = 0.0
            if items and hasattr(self._workspace, 'animator_engine') and self._workspace.animator_engine.schedule:
                # Find the last action in the schedule belonging to an item in this scene
                scene_end_times = [
                    action['end'] for action in self._workspace.animator_engine.schedule 
                    if action.get('type') == 'draw' and action.get('item') in items
                ]
                if scene_end_times:
                    # The duration is the final end time minus the scene's start time
                    max_item_dur = max(scene_end_times) - current_time

            if items:
                # Dynamically stretch the scene duration to fit all items
                dur = max(base_dur, max_item_dur)
            else:
                dur = base_dur
                
            is_active = (i == self._workspace.current_scene_index) if self._workspace else False
            blocks.append({'start': current_time, 'duration': dur,
                           'color': self.ACCENT_COLOR,
                           'label': f'Scene', 'item': board, 'is_scene_block': True,
                           'is_active': is_active})
                
            current_time += dur

        rendered = 0.0
        prev = None
        for i, data in enumerate(blocks):
            if prev:
                prev_board = prev.get('item')
                t_type = getattr(prev_board, 'transition_type', None) if prev_board else None
                t_dur = 0.2
                if t_type and t_type != "None":
                    t_dur = getattr(prev_board, 'transition_duration', 1.0)
                self._track_layout.addWidget(
                    TransitionBlock(prev_board, t_type if t_type else "None", t_dur, self._pps))
                rendered += t_dur
                
            if data['start'] > rendered:
                sp = QWidget(); sp.setFixedWidth(int((data['start']-rendered)*self._pps))
                self._track_layout.addWidget(sp)
                rendered = data['start']
                
            is_last = (i == len(blocks) - 1)
            scene_block = SceneDraggableBlock(data, self._pps, self._workspace, i, is_last)
            
            self._track_layout.addWidget(scene_block)
            rendered += data['duration']
            prev = data
        self._track_layout.addStretch()
