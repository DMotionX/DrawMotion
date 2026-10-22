"""
Purpose: Bottom timeline panel.

Layout:
┌──────────────────────────┬───────────────────────────────────────────────┐
│  LAYERS  (fixed 200px)   │  Ruler + 4 track rows  (stretch)               │
│  ─────────────────────── │  ─────────────────────────────────────────────  │
│  [img] Image             │  ████████████  ████████████                     │
│  [T]   Text              │  ████ ████                                      │
│  [mic] Voice             │                                                 │
│  [sfx] SFX               │                                                 │
└──────────────────────────┴───────────────────────────────────────────────┘

Key: label_widget() stays in left column, track_widget() stays in right column.
"""
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPolygonF, QPen
from PySide6.QtCore import QPointF
from utils.theme import THEME_COLORS
from utils.icons import get_icon
from .ruler import TimeRuler

PIXELS_PER_SECOND = 50
LABEL_WIDTH       = 200    # fixed left column width (px)
TRACK_HEIGHT      = 36     # must match base_layer_row.TRACK_HEIGHT
TRACK_SPACING     = 4


# ─────────────────────────────────────────────────────────────────────────────
class PlayheadWidget(QWidget):
    time_seek = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(14)
        self.setCursor(Qt.CursorShape.SizeHorCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("red"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(QPolygonF([QPointF(0, 0), QPointF(14, 0), QPointF(7, 10)]))
        pen = QPen(QColor("red")); pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(7, 10, 7, self.height())
        painter.drawLine(7, 10, 7, self.height())

    def mousePressEvent(self, event):
        from PySide6.QtCore import Qt
        if event.button() == Qt.MouseButton.LeftButton:
            self._emit_seek(event.globalPosition().x())

    def mouseMoveEvent(self, event):
        from PySide6.QtCore import Qt
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._emit_seek(event.globalPosition().x())

    def _emit_seek(self, global_x):
        from PySide6.QtCore import QPoint
        parent_pos = self.parentWidget().mapFromGlobal(QPoint(int(global_x), 0))
        time_sec = max(0.0, parent_pos.x() / PIXELS_PER_SECOND)
        self.time_seek.emit(time_sec)

# ─────────────────────────────────────────────────────────────────────────────
class TimelineResizeHandle(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TimelineResizeHandle")
        self.setFixedHeight(8)
        self.setCursor(Qt.CursorShape.SplitVCursor)
        self.setToolTip("Drag vertically to resize timeline | Double-click to reset")
        self._is_dragging = False
        self._drag_start_y = 0
        self._drag_start_height = 0
        self.setStyleSheet(f"""
            #TimelineResizeHandle {{
                background-color: {THEME_COLORS['bg_main']};
                border-top: 1px solid {THEME_COLORS['divider']};
            }}
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pill_w = 40
        pill_h = 4
        pill_x = int((self.width() - pill_w) / 2)
        pill_y = int((self.height() - pill_h) / 2)
        
        is_active = self.underMouse() or self._is_dragging
        color = QColor(THEME_COLORS['primary_green']) if is_active else QColor(255, 255, 255, 60)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(pill_x, pill_y, pill_w, pill_h, 2, 2)

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_y = event.globalPosition().y()
            parent = self.parentWidget()
            if parent:
                self._drag_start_height = parent.height()
            self.update()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            delta_y = event.globalPosition().y() - self._drag_start_y
            parent = self.parentWidget()
            if parent and hasattr(parent, 'set_timeline_height'):
                new_h = int(self._drag_start_height - delta_y)
                parent.set_timeline_height(new_h)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            self.update()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            parent = self.parentWidget()
            if parent and hasattr(parent, 'set_timeline_height'):
                parent.set_timeline_height(180)
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

# ─────────────────────────────────────────────────────────────────────────────
class TimelinePanel(QFrame):
    delete_item_requested = Signal(object)
    time_seek = Signal(float)

    def __init__(self):
        super().__init__()
        self.setObjectName("BottomPanel")
        self._custom_height = 180
        self.setFixedHeight(180)
        self.workspace     = None
        self._layer_rows   = []   # list of BaseLayerRow instances
        self._init_ui()

    def set_timeline_height(self, h: int):
        min_h = 76
        window = self.window()
        max_h = int(window.height() * 0.45) if window else 350
        max_h = max(250, min(max_h, 450))
        clamped_h = max(min_h, min(max_h, h))
        self.setFixedHeight(clamped_h)
        self._custom_height = clamped_h

    # ─────────────────────────────────────────────────────────────
    # UI build
    # ─────────────────────────────────────────────────────────────
    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        
        # 1. Resizable split handle at the very top of the timeline
        self.resize_handle = TimelineResizeHandle(self)
        root.addWidget(self.resize_handle)

        # 2. Timeline Toolbar
        from components.timeline.toolbar import TimelineToolbar
        self.toolbar = TimelineToolbar(self)
        
        # Wire toolbar events safely
        def open_recorder():
            from PySide6.QtWidgets import QApplication
            for widget in QApplication.topLevelWidgets():
                if widget.__class__.__name__ == "WhiteInkMainWindow":
                    widget.left_panel._open_voice_recorder()
                    break
        self.toolbar.record_requested.connect(open_recorder)
        self.toolbar.focus_mode_toggled.connect(self._on_focus_mode_toggled)
        
        root.addWidget(self.toolbar)

        self.content_widget = QWidget()
        content_layout = QHBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # ══ LEFT COLUMN: fixed-width LAYERS panel ═════════════════
        self._left_col = QFrame()
        self._left_col.setFixedWidth(LABEL_WIDTH)
        self._left_col.setStyleSheet(
            f"background-color: {THEME_COLORS['bg_main']};"
            f"border-radius: 8px 0 0 8px;"
        )
        self._left_main_layout = QVBoxLayout(self._left_col)
        self._left_main_layout.setContentsMargins(0, 0, 0, 0)
        self._left_main_layout.setSpacing(0)

        # "LAYERS" header inside left column (fixed at top)
        header_frame = QFrame()
        header_frame.setFixedHeight(28)
        header_frame.setStyleSheet("background: transparent; border: none;")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(12, 0, 12, 0)
        title_lbl = QLabel("LAYERS")
        title_lbl.setStyleSheet(
            f"color: {THEME_COLORS['text_primary']}; font-weight: bold;"
            f"font-size: 11px; letter-spacing: 1px; background: transparent;"
        )
        icon_lbl = QLabel()
        try:
            icon_lbl.setPixmap(get_icon("layers", THEME_COLORS['text_secondary']).pixmap(16, 16))
        except Exception:
            pass
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        h_layout.addWidget(icon_lbl)
        self._left_main_layout.addWidget(header_frame)
        
        # Scrollable left layers container
        self._left_scroll = QScrollArea()
        self._left_scroll.setWidgetResizable(True)
        self._left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._left_scroll.setStyleSheet("border: none; background: transparent;")
        
        self._left_scroll_container = QWidget()
        self._left_scroll_container.setStyleSheet("background: transparent;")
        self._left_layout = QVBoxLayout(self._left_scroll_container)
        self._left_layout.setContentsMargins(0, TRACK_SPACING, 0, TRACK_SPACING)
        self._left_layout.setSpacing(TRACK_SPACING)

        # Label rows will be inserted here (stretch at the end)
        self._left_layout.addStretch()
        
        self._left_scroll.setWidget(self._left_scroll_container)
        self._left_main_layout.addWidget(self._left_scroll)

        content_layout.addWidget(self._left_col)

        # ══ RIGHT COLUMN: ruler + track rows ══════════════════════
        self._right_col = QFrame()
        self._right_col.setStyleSheet(
            f"background-color: {THEME_COLORS['bg_secondary']};"
            f"border-radius: 0 8px 8px 0;"
        )
        self._right_layout = QVBoxLayout(self._right_col)
        self._right_layout.setContentsMargins(0, 0, 0, 0)
        self._right_layout.setSpacing(0)

        # Time ruler (26px tall header, aligns with left "LAYERS" header)
        ruler_container = QFrame()
        ruler_container.setFixedHeight(28)
        ruler_container.setStyleSheet("background: transparent;")
        rc_layout = QHBoxLayout(ruler_container)
        rc_layout.setContentsMargins(0, 0, 0, 0)
        self.ruler = TimeRuler(pixels_per_second=PIXELS_PER_SECOND)
        self.ruler.time_seek.connect(self.time_seek.emit)
        rc_layout.addWidget(self.ruler)
        self._right_layout.addWidget(ruler_container)

        # Scrollable track-rows container
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.2);
                min-height: 20px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.4);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self._tracks_container = QWidget()
        self._tracks_container.setStyleSheet("background: transparent;")
        self._tracks_layout = QVBoxLayout(self._tracks_container)
        self._tracks_layout.setContentsMargins(0, TRACK_SPACING, 0, TRACK_SPACING)
        self._tracks_layout.setSpacing(TRACK_SPACING)
        self._tracks_layout.addStretch()

        self._scroll.setWidget(self._tracks_container)
        self._right_layout.addWidget(self._scroll, stretch=1)
        
        # Link scroll bars for perfect vertical sync
        self._scroll.verticalScrollBar().valueChanged.connect(self._left_scroll.verticalScrollBar().setValue)
        self._left_scroll.verticalScrollBar().valueChanged.connect(self._scroll.verticalScrollBar().setValue)

        content_layout.addWidget(self._right_col, stretch=1)
        root.addWidget(self.content_widget, stretch=1)

        # Playhead (absolute, lives inside tracks_container)
        self.playhead_line = PlayheadWidget(self._tracks_container)
        self.playhead_line.time_seek.connect(self.time_seek.emit)
        self.playhead_line.move(0, 0)
        self.playhead_line.raise_()

    def _on_focus_mode_toggled(self, is_focused):
        """Collapses the entire track area, leaving only the toolbar visible."""
        handle_h = self.resize_handle.height() if hasattr(self, 'resize_handle') else 0
        if is_focused:
            self.content_widget.hide()
            self.setFixedHeight(36 + handle_h)
        else:
            self.content_widget.show()
            restored_h = getattr(self, '_custom_height', 180)
            self.setFixedHeight(restored_h)

    # ─────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────
    def set_workspace(self, workspace):
        self.workspace = workspace

    def set_playhead_progress(self, current_time_sec):
        x_pos = int(current_time_sec * PIXELS_PER_SECOND)
        self.playhead_line.move(x_pos, 0)
        self.playhead_line.setFixedHeight(self._tracks_container.height())
        self.playhead_line.raise_()
        
        # Update Digital Timer
        total_time = 0.0
        if self.workspace and hasattr(self.workspace, 'animator_engine'):
            schedule = self.workspace.animator_engine.schedule
            if schedule:
                total_time = max(a['end'] for a in schedule)
        
        def fmt(t):
            m = int(t // 60)
            s = int(t % 60)
            ms = int((t * 10) % 10)
            return f"{m:02d}:{s:02d}.{ms}"
            
        self.toolbar.timer_lbl.setText(f"{fmt(current_time_sec)} / {fmt(total_time)}")

    def update_timeline(self, items=None):
        """Rebuild both columns using current workspace data."""
        if not self.workspace:
            return

        from components.timeline.layers import (
            ScenesLayerRow, TextLayerRow, VoiceLayerRow
        )
        
        # Save scroll state
        h_scroll = 0
        v_scroll = 0
        if hasattr(self, '_scroll') and self._scroll:
            h_scroll = self._scroll.horizontalScrollBar().value()
            v_scroll = self._scroll.verticalScrollBar().value()

        # ── Clear existing layer rows ──────────────────────────────
        for row in self._layer_rows:
            lw = row.label_widget()
            if lw:
                self._left_layout.removeWidget(lw)
                lw.deleteLater()
            
            tw = row.track_widget()
            if tw:
                self._tracks_layout.removeWidget(tw)
                tw.deleteLater()
                
        self._layer_rows.clear()

        # ── Build rows ────────────────────────────────────────
        # [PHASE 2 FIX]: Restore TextLayerRow (Elements Layer)
        row_classes = [ScenesLayerRow, TextLayerRow, VoiceLayerRow]
        for cls in row_classes:
            row = cls(self.workspace, PIXELS_PER_SECOND)
            self._layer_rows.append(row)

            # Label → LEFT column (before the final stretch)
            insert_idx = self._left_layout.count() - 1  # before addStretch
            self._left_layout.insertWidget(insert_idx, row.label_widget())



            # Track → RIGHT column (before the final stretch)
            t_idx = self._tracks_layout.count() - 1
            self._tracks_layout.insertWidget(t_idx, row.track_widget())

        # Keep playhead on top
        if hasattr(self, 'playhead_line'):
            self.playhead_line.raise_()
            
        self._left_layout.invalidate()
        self._tracks_layout.invalidate()
        self.update()
        
        # Restore scroll state (use QTimer to allow layout to compute new sizes)
        if hasattr(self, '_scroll') and self._scroll:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, lambda h=h_scroll, v=v_scroll: (
                self._scroll.horizontalScrollBar().setValue(h),
                self._scroll.verticalScrollBar().setValue(v)
            ))
