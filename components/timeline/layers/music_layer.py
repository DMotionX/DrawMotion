"""
Music Layer Row — for background music tracks.
Icon: music note.
Accent: green #388E3C.
"""
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtWidgets import QLabel
from components.timeline.layers.base_layer_row import BaseLayerRow


class MusicLayerRow(BaseLayerRow):
    LABEL_TEXT   = "Music"
    ACCENT_COLOR = "#388E3C"

    def draw_icon(self, painter: QPainter, rect):
        c = QColor(self.ACCENT_COLOR)
        pen = QPen(c, 1.5); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush)
        w, h = rect.width(), rect.height(); cx = w / 2
        
        # Music Note (eighth note)
        painter.drawEllipse(QRectF(cx-4, h/2+2, 4, 3))
        painter.drawLine(QPointF(cx, h/2+3), QPointF(cx, 3))
        painter.drawArc(QRectF(cx, 3, 5, 5), 90 * 16, -180 * 16)

    def _populate_track(self):
        self._clear_track()
        
        if not self._workspace:
            self._track_layout.addStretch()
            return
            
        items = sorted([i for i in self._workspace.audio_items if i.layer_name == self.LABEL_TEXT], key=lambda x: getattr(x, 'anim_delay', 0.0))
        
        from components.widgets.timeline_track import TimelineTrack
        from PySide6.QtWidgets import QPushButton, QFileDialog, QWidget
        
        rendered = 0.0
        for item in items:
            delay = getattr(item, 'anim_delay', 0.0)
            if delay > rendered:
                sp = QWidget()
                sp.setFixedWidth(int((delay - rendered) * self._pps))
                self._track_layout.addWidget(sp)
            
            track_w = TimelineTrack(item, self._pps)
            self._track_layout.addWidget(track_w)
            rendered = delay + getattr(item, 'anim_duration', 0.0)
            
        btn = QPushButton(" + Add Music ")
        btn.setStyleSheet(f"""
            QPushButton {{
                color: #A0A0A0; 
                background: rgba(255, 255, 255, 0.03); 
                border: 1px dashed rgba(255, 255, 255, 0.2); 
                border-radius: 6px; 
                padding: 4px 12px;
                font-size: 11px;
                margin-left: 8px;
            }}
            QPushButton:hover {{
                color: white;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid {self.ACCENT_COLOR};
            }}
        """)
        btn.setFixedSize(100, 26)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        def add_audio():
            path, _ = QFileDialog.getOpenFileName(None, "Select Music Audio", "", "Audio Files (*.mp3 *.wav *.ogg)")
            if path:
                node = self._workspace.add_audio_node(path, self.LABEL_TEXT)
                self._workspace.audio_engine.add_track(path, getattr(node, 'anim_delay', 0.0))
                
        btn.clicked.connect(add_audio)
        self._track_layout.addWidget(btn)
        self._track_layout.addStretch()
