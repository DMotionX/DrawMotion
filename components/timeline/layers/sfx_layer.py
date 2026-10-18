"""
SFX Layer Row — placeholder for sound-effects track.
Icon: double musical note (drawn with QPainter).
Accent: purple #6A1B9A.
"""
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRectF, QPointF
from components.timeline.layers.base_layer_row import BaseLayerRow


class SfxLayerRow(BaseLayerRow):
    LABEL_TEXT   = "SFX"
    ACCENT_COLOR = "#6A1B9A"

    def draw_icon(self, painter: QPainter, rect):
        c = QColor(self.ACCENT_COLOR)
        pen = QPen(c, 1.4); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        w, h = rect.width(), rect.height()

        # Two note stems
        painter.drawLine(QPointF(w*0.3, 3), QPointF(w*0.3, h*0.72))
        painter.drawLine(QPointF(w*0.65, 1), QPointF(w*0.65, h*0.62))
        # Beam
        painter.drawLine(QPointF(w*0.3, 3), QPointF(w*0.65, 1))

        # Note heads
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(c.red(), c.green(), c.blue(), 220))
        painter.drawEllipse(QRectF(w*0.15, h*0.65, 6, 4))
        painter.drawEllipse(QRectF(w*0.5,  h*0.55, 6, 4))

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
            
        btn = QPushButton(" + Add SFX ")
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
            path, _ = QFileDialog.getOpenFileName(None, "Select SFX Audio", "", "Audio Files (*.mp3 *.wav *.ogg)")
            if path:
                node = self._workspace.add_audio_node(path, self.LABEL_TEXT)
                self._workspace.audio_engine.add_track(path, getattr(node, 'anim_delay', 0.0))
                
        btn.clicked.connect(add_audio)
        self._track_layout.addWidget(btn)
        self._track_layout.addStretch()
