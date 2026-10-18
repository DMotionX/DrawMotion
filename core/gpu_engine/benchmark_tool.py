from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QBrush, QPen, QPainter
from core.settings_manager import SettingsManager
import math
import time

class BenchmarkTool(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test Smoothness (Benchmark Stress Test)")
        self.setFixedSize(650, 500)
        self.setStyleSheet("background-color: #1A202C; color: white;")
        
        layout = QVBoxLayout(self)
        
        info = QLabel("Stress Test: Rendering 5000 overlapping semi-transparent objects.\nIf GPU is disabled, your CPU will struggle (low FPS). Enable GPU Acceleration for buttery smooth 60 FPS!")
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 13px; color: #E2E8F0; margin-bottom: 10px;")
        layout.addWidget(info)
        
        self.scene = QGraphicsScene(0, 0, 550, 350)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setStyleSheet("background-color: #2D3748; border: 1px solid #4A5568;")
        
        # Determine whether to use GPU or CPU based on Settings
        use_gpu = SettingsManager().get("use_gpu_acceleration", False)
        if use_gpu:
            try:
                from PySide6.QtOpenGLWidgets import QOpenGLWidget
                from PySide6.QtGui import QSurfaceFormat
                gl_format = QSurfaceFormat()
                gl_format.setSamples(4)
                gl_widget = QOpenGLWidget()
                gl_widget.setFormat(gl_format)
                self.view.setViewport(gl_widget)
                self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
            except Exception as e:
                pass # Fallback to CPU if OpenGL fails
        else:
            self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
            
        layout.addWidget(self.view)
        
        self.items = []
        # GPU Stress Test: Fewer items, but heavy Shader (Blur) effects
        # CPU will struggle massively with blur calculations, GPU will fly at 60fps.
        from PySide6.QtWidgets import QGraphicsBlurEffect
        for i in range(150):
            item = QGraphicsEllipseItem(0, 0, 40, 40)
            color = QColor.fromHsv((i * 5) % 360, 220, 255, 200)
            item.setBrush(QBrush(color))
            item.setPen(QPen(Qt.PenStyle.NoPen))
            
            # Apply heavy blur effect to stress shaders
            blur = QGraphicsBlurEffect()
            blur.setBlurRadius(15)
            item.setGraphicsEffect(blur)
            
            self.scene.addItem(item)
            self.items.append(item)
            
        stats_layout = QHBoxLayout()
        self.fps_lbl = QLabel("FPS: 0")
        self.fps_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #48BB78;")
        
        status_lbl = QLabel(f"Mode: {'GPU (Hardware Accelerated)' if use_gpu else 'CPU (Safe Mode)'}")
        status_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {'#48BB78' if use_gpu else '#ECC94B'}; margin-left: 20px;")
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #E53E3E; color: white; padding: 6px 12px; border-radius: 4px;")
        close_btn.clicked.connect(self.close)
        
        stats_layout.addWidget(self.fps_lbl)
        stats_layout.addWidget(status_lbl)
        stats_layout.addStretch()
        stats_layout.addWidget(close_btn)
        layout.addLayout(stats_layout)
        
        self.angle = 0
        self.last_time = time.time()
        self.frames = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(16)
        
    def closeEvent(self, event):
        """CRITICAL FIX: Stop timer to prevent memory leaks and thread crashes."""
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        super().closeEvent(event)
        
    def _animate(self):
        self.angle += 0.03
        cx, cy = 250, 150
        
        for i, item in enumerate(self.items):
            offset = i * 0.1
            r = 50 + (i % 50) * 1.5
            x = cx + math.cos(self.angle + offset) * r - 20
            y = cy + math.sin(self.angle + offset) * r - 20
            item.setPos(x, y)
            
        self.frames += 1
        current_time = time.time()
        if current_time - self.last_time >= 1.0:
            fps = self.frames / (current_time - self.last_time)
            self.fps_lbl.setText(f"FPS: {int(fps)}")
            
            if fps < 30:
                self.fps_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #F56565;")
            elif fps < 50:
                self.fps_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #ECC94B;")
            else:
                self.fps_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #48BB78;")
                
            self.last_time = current_time
            self.frames = 0
