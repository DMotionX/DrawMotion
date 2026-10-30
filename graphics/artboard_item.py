"""
Purpose: Defines the SceneArtboardItem which acts as a virtual camera/canvas for a single scene.
Features: Resizable, supports standard aspect ratios, acts as a container for scene elements.
"""
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem, QMenu
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPen, QBrush, QCursor, QAction

class SceneArtboardItem(QGraphicsRectItem):
    """
    Represents the main camera/scene frame in the workspace.
    It acts as a fixed canvas.
    """
    def __init__(self, rect: QRectF, parent=None):
        super().__init__(rect, parent)
        # Artboard should NOT be movable or selectable by default to avoid confusing the user.
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape, True)
        self.setAcceptHoverEvents(False)
        
        # Subtle gray border like a piece of paper
        pen = QPen(QColor("#333333")) 
        pen.setWidth(1)
        pen.setCosmetic(True)
        self.setPen(pen)
        
        # Solid white fill so it looks like a distinct "page" or "scene"
        self.setBrush(QBrush(QColor(255, 255, 255)))
        self.duration = 2.0 # Default scene duration in seconds (standard across DrawMotion)
        self.user_defined_duration = None # Preserves manual custom duration if set by user
        
        self.scene_index = 1
        self.total_scenes = 1
        self._is_exporting = False

    def paint(self, painter, option, widget=None):
        if self._is_exporting:
            # We must paint the white background, but hide the gray border!
            old_pen = self.pen()
            self.setPen(QPen(Qt.GlobalColor.transparent))
            super().paint(painter, option, widget)
            self.setPen(old_pen)
        else:
            super().paint(painter, option, widget)

    def shape(self):
        # Override shape to strictly return our own rect.
        # This prevents large scaled child items from expanding our shape
        # and intercepting mouse events when they spill over into other scenes.
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.addRect(self.rect())
        return path

    def contextMenuEvent(self, event):
        from PySide6.QtWidgets import QInputDialog
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #222A27; color: white; border: 1px solid #2E8B57; } QMenu::item:selected { background-color: #2E8B57; }")
        
        def add_ratio_action(title, w, h):
            action = menu.addAction(title)
            action.setData((w, h))
            action.triggered.connect(self._on_ratio_action_triggered)
            
        change_duration_action = menu.addAction(f"Set Scene Duration  ({self.duration}s)")
        menu.addSeparator()
        
        add_ratio_action("YouTube / Wide (16:9) - 1920x1080", 1920, 1080)
        add_ratio_action("Instagram Post (1:1) - 1080x1080", 1080, 1080)
        add_ratio_action("TikTok / Shorts (9:16) - 1080x1920", 1080, 1920)
        add_ratio_action("Standard (4:3) - 1024x768", 1024, 768)
        
        action = menu.exec_(event.screenPos())
        if action == change_duration_action:
            new_dur, ok = QInputDialog.getDouble(None, "Scene Duration", "Enter scene duration in seconds:", self.duration, 1.0, 3600.0, 1)
            if ok and new_dur != self.duration:
                if self.scene():
                    views = self.scene().views()
                    if views:
                        workspace = views[0].parent()
                        if hasattr(workspace, 'set_scene_duration_and_scale'):
                            workspace.set_scene_duration_and_scale(self, new_dur)
                            return
                
                # Fallback if workspace method not found
                self.duration = new_dur
                self.user_defined_duration = new_dur
                self._recalculate_scene_times()
                
    def _recalculate_scene_times(self):
        # Tell the workspace to re-distribute times
        if self.scene():
            views = self.scene().views()
            if views:
                workspace = views[0].parent()
                if hasattr(workspace, 'distribute_global_time'):
                    workspace.distribute_global_time(respect_board_duration=True)

    def _set_aspect_ratio(self, w, h):
        self.setRect(self.rect().x(), self.rect().y(), w, h)
        # Notify scene to update if needed
        self.update()

    def _on_ratio_action_triggered(self):
        action = self.sender()
        if action and hasattr(action, 'data'):
            data = action.data()
            if data:
                w, h = data
                self._set_aspect_ratio(w, h)
