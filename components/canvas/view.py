from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt

class CustomGraphicsView(QGraphicsView):
    def __init__(self, workspace, scene, parent=None):
        super().__init__(scene, parent)
        self.workspace = workspace
        self.setAcceptDrops(True)
        
        # Enable real-time mouse tracking so hover events on handles and canvas fire instantly at 60 FPS
        self.setMouseTracking(True)
        if self.viewport():
            self.viewport().setMouseTracking(True)
            
        # Enable high-quality rendering to prevent pixelation on small screens
        from PySide6.QtGui import QPainter
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        
    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        
        from core.settings_manager import SettingsManager
        if SettingsManager().get("show_fps", False):
            import time
            if not hasattr(self, '_fps_time'):
                self._fps_time = time.time()
                self._fps_frames = 0
                self._current_fps = 0
                
            self._fps_frames += 1
            now = time.time()
            if now - self._fps_time >= 1.0:
                self._current_fps = int(self._fps_frames / (now - self._fps_time))
                self._fps_time = now
                self._fps_frames = 0
                
            painter.save()
            painter.resetTransform()
            from PySide6.QtGui import QColor, QFont
            if self._current_fps < 30:
                painter.setPen(QColor("#F56565"))
            elif self._current_fps < 50:
                painter.setPen(QColor("#ECC94B"))
            else:
                painter.setPen(QColor("#48BB78"))
                
            font = QFont("Arial", 12, QFont.Weight.Bold)
            painter.setFont(font)
            # Add a dark background rect for readability
            bg_rect = painter.fontMetrics().boundingRect(f"FPS: {self._current_fps}")
            bg_rect.adjust(-5, -5, 5, 5)
            bg_rect.translate(10, 10 - painter.fontMetrics().ascent())
            painter.fillRect(bg_rect, QColor(0, 0, 0, 150))
            painter.drawText(10, 10, f"FPS: {self._current_fps}")
            painter.restore()
        
    def keyPressEvent(self, event):
        from PySide6.QtWidgets import QTextEdit, QLineEdit
        focus_widget = self.window().focusWidget()
        if focus_widget and isinstance(focus_widget, (QTextEdit, QLineEdit)):
            super().keyPressEvent(event)
            return

        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            self.workspace.delete_selected_items()
            
        modifiers = event.modifiers()
        if modifiers == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_C:
                selected = self.scene().selectedItems()
                if selected:
                    self.workspace.clipboard.copy(selected[0])
            elif event.key() == Qt.Key.Key_X:
                selected = self.scene().selectedItems()
                if selected:
                    self.workspace.clipboard.cut(selected[0])
            elif event.key() == Qt.Key.Key_V:
                self.workspace.clipboard.paste()
            elif event.key() == Qt.Key.Key_D:
                selected = self.scene().selectedItems()
                if selected:
                    self.workspace.clipboard.duplicate(selected[0])
                    
        super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("mind_map_template:"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("mind_map_template:"):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("mind_map_template:"):
            shape_type = event.mimeData().text().split(":")[1]
            # Call a workspace method to add the node
            self.workspace.add_mind_map_node(shape_type, event.position().toPoint())
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def contextMenuEvent(self, event):
        # Determine if we clicked on an item or empty space
        item = self.scene().itemAt(self.mapToScene(event.pos()), self.transform())
        
        # We want to show the menu if we clicked on empty space, OR if we clicked on an artboard directly
        from graphics.artboard_item import SceneArtboardItem
        from PySide6.QtWidgets import QMenu
        from PySide6.QtGui import QAction, QIcon
        from utils.theme import THEME_COLORS
        
        # Custom stylesheet for premium look
        menu_style = f"""
            QMenu {{
                background-color: {THEME_COLORS['bg_main']};
                color: {THEME_COLORS['text_primary']};
                border: 1px solid {THEME_COLORS['divider']};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 24px 8px 8px;
                border-radius: 4px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background-color: {THEME_COLORS['primary_green']};
                color: white;
            }}
            QMenu::item:disabled {{
                color: {THEME_COLORS['text_secondary']};
            }}
        """
        
        menu = QMenu(self)
        menu.setStyleSheet(menu_style)
        
        action_add_scene = QAction("Add New Scene", self)
        action_add_scene.triggered.connect(self.workspace.add_new_scene)
        menu.addAction(action_add_scene)
        
        # If we are on an artboard (or a child of it), we can offer to delete IT.
        # Otherwise, delete the currently focused scene.
        target_artboard = None
        if isinstance(item, SceneArtboardItem):
            target_artboard = item
        elif item and hasattr(item, 'parentItem') and isinstance(item.parentItem(), SceneArtboardItem):
            target_artboard = item.parentItem()
            
        self._context_item = item
        self._context_artboard = target_artboard

        if item and item != target_artboard:
            # We clicked on an actual item
            if type(item).__name__ == "AnimatedImageItem":
                act_replace = QAction("Replace Image", self)
                act_replace.triggered.connect(self._on_context_replace)
                menu.addAction(act_replace)
                menu.addSeparator()
                
            act_cut = QAction("Cut", self)
            act_cut.triggered.connect(self._on_context_cut)
            menu.addAction(act_cut)
            
            act_copy = QAction("Copy", self)
            act_copy.triggered.connect(self._on_context_copy)
            menu.addAction(act_copy)
            
            act_dup = QAction("Duplicate", self)
            act_dup.triggered.connect(self._on_context_duplicate)
            menu.addAction(act_dup)
            
            act_del = QAction("Delete", self)
            act_del.triggered.connect(self.workspace.delete_selected_items)
            menu.addAction(act_del)
            menu.addSeparator()
            
        act_paste = QAction("Paste", self)
        act_paste.triggered.connect(self.workspace.clipboard.paste)
        if not self.workspace.clipboard.has_content():
            act_paste.setEnabled(False)
        menu.addAction(act_paste)
        menu.addSeparator()
            
        # Transition menu removed for cleaner UI
        
        action_del_scene = QAction("Delete Scene", self)
        
        if target_artboard:
            # ── Scene Settings ───────────────────────────────────────────────
            ratio_menu = QMenu("Aspect Ratio", self)
            ratio_menu.setStyleSheet(menu_style)
            
            def add_ratio(title, w, h):
                act = QAction(title, self)
                act.setData((w, h))
                act.triggered.connect(self._on_context_ratio_triggered)
                ratio_menu.addAction(act)
                
            add_ratio("YouTube / Wide (16:9) - 1920x1080", 1920, 1080)
            add_ratio("Instagram Post (1:1) - 1080x1080", 1080, 1080)
            add_ratio("TikTok / Shorts (9:16) - 1080x1920", 1080, 1920)
            add_ratio("Standard (4:3) - 1024x768", 1024, 768)
            
            menu.addMenu(ratio_menu)
            menu.addSeparator()
            
            idx = self.workspace.artboards.index(target_artboard)
            action_del_scene.setData(idx)
            action_del_scene.triggered.connect(self._on_context_del_scene)
        else:
            idx = self.workspace.current_scene_index
            if 0 <= idx < len(self.workspace.artboards):
                action_del_scene.setData(idx)
                action_del_scene.triggered.connect(self._on_context_del_scene)
            else:
                action_del_scene.setEnabled(False)
                
        menu.addAction(action_del_scene)
        
        menu.exec_(event.globalPos())

    def _on_context_replace(self):
        if hasattr(self, '_context_item') and self._context_item:
            from PySide6.QtWidgets import QFileDialog
            from PySide6.QtGui import QPixmap
            path, _ = QFileDialog.getOpenFileName(self, "Replace Image", "", "Images (*.png *.jpg *.jpeg)")
            if path:
                self._context_item.replace_image(QPixmap(path))
                self._context_item.filepath = path
                self.workspace.items_changed.emit(self.workspace.user_items)

    def _on_context_cut(self):
        if hasattr(self, '_context_item') and self._context_item:
            self.workspace.clipboard.cut(self._context_item)

    def _on_context_copy(self):
        if hasattr(self, '_context_item') and self._context_item:
            self.workspace.clipboard.copy(self._context_item)

    def _on_context_duplicate(self):
        if hasattr(self, '_context_item') and self._context_item:
            self.workspace.clipboard.duplicate(self._context_item)

    def _on_context_ratio_triggered(self):
        act = self.sender()
        if act and hasattr(self, '_context_artboard') and self._context_artboard:
            data = act.data()
            if data:
                w, h = data
                self._context_artboard._set_aspect_ratio(w, h)

    def _on_context_del_scene(self):
        act = self.sender()
        if act:
            idx = act.data()
            if idx is not None:
                self.workspace.delete_scene(idx)

    def _assign_transition_to_scene(self, transition_id, artboard=None):
        """Assign or clear a transition on the artboard preceding this scene."""
        if artboard is None:
            # Fall back to the currently selected/focused artboard
            idx = self.workspace.current_scene_index
            if 0 <= idx < len(self.workspace.artboards):
                artboard = self.workspace.artboards[idx]
        if artboard:
            artboard.transition_type = transition_id
            # Trigger timeline refresh so the TransitionBlock appears/disappears
            self.workspace.items_changed.emit(self.workspace.user_items)


# Zero-Risk Dual Compatibility Alias:
# Guarantees that any caller importing CanvasView or CustomGraphicsView succeeds 100%
CanvasView = CustomGraphicsView

