import sys
sys.path.insert(0, '.')
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPointF
from core.drawing_engine.algorithms.clean_outline.algorithm import CleanOutlineAlgorithm

app = QApplication([])
img = QImage('assets/library/ChatGPT Image Aug 3, 2026, 08_15_34 AM.png')
scaled = img.scaled(1080, 607, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
pixmap = QPixmap.fromImage(scaled)
qimage = pixmap.scaled(400, 224, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation).toImage()

algo = CleanOutlineAlgorithm()
plan = algo.generate_plan(qimage, 8.0)

inv_scale = 1080/400.0
img_out = QImage(1080, 607, QImage.Format_ARGB32_Premultiplied)
img_out.fill(Qt.GlobalColor.white)
painter = QPainter(img_out)
painter.setPen(QPen(QColor('black'), 15.0))

last_time = 7.5
current_time = 8.0

for segment in plan:
    pts = [QPointF(p.x()*inv_scale, p.y()*inv_scale) for p in segment['points']]
    
    seg_dur = max(0.001, segment["duration"])
    local_end = min(seg_dur, current_time - segment["start_time"])
    seg_start = max(0.0, last_time - segment["start_time"])
    
    p_end = local_end / seg_dur
    p_start = seg_start / seg_dur
    
    idx_end = int(p_end * (len(pts) - 1))
    idx_start = int(p_start * (len(pts) - 1))

    if idx_end > idx_start:
        painter.drawPolyline(pts[idx_start:idx_end + 1])

painter.end()
img_out.save('test_scribble_pyside6.png')
print('Saved test_scribble_pyside6.png')
