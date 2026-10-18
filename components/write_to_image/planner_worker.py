"""
TextPlannerWorker: Background thread worker that generates the timed segment
plan for WriteToImageGraphicsItem.

v4: We completely dropped text_reveal_algorithm.py.
Instead, we treat the text image as a regular image and use the core AlgorithmFactory.
"""
from PySide6.QtCore import QObject, Signal, QPointF


class TextPlannerWorker(QObject):
    finished = Signal(list)

    def __init__(self, qimage, duration: float, is_rtl: bool = False, inv_scale: float = 1.0):
        super().__init__()
        self.qimage = qimage
        self.duration = duration
        self.is_rtl = is_rtl
        self.inv_scale = inv_scale
        self.style_name = "Solid Reveal"  # Default clean wiping style

    def run(self):
        try:
            from .custom_text_reveal import CustomTextRevealAlgorithm
            algorithm = CustomTextRevealAlgorithm()
            
            timed_segments = algorithm.generate_plan(self.qimage, self.duration, rtl=self.is_rtl)
            
            # Apply inverse scale if the image was downscaled for analysis
            for segment in timed_segments:
                scaled_pts = []
                for p in segment["points"]:
                    scaled_pts.append(QPointF(p.x() * self.inv_scale, p.y() * self.inv_scale))
                segment["points"] = scaled_pts
                segment["width"] = segment.get("width", 1.0) * self.inv_scale
                
            self.finished.emit(timed_segments)
        except Exception as e:
            import traceback
            print(f"[TextPlannerWorker] Error: {e}")
            traceback.print_exc()
            self.finished.emit([])
