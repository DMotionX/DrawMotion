import cv2
import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
import math
from ..base_algorithm import BaseDrawingAlgorithm

class SmartBlueprintAlgorithm(BaseDrawingAlgorithm):
    """
    Smart Blueprint: Draws the main outer silhouette slowly, 
    then fills the inner complex details with a fast solid sweep.
    """
    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        import cv2
        import numpy as np
        
        mask = self._get_ink_mask(qimage)
        scale = 1.0
        max_dim = 1000
        h, w = mask.shape
        if w > max_dim or h > max_dim:
            scale = min(max_dim / w, max_dim / h)
            mask = cv2.resize(mask, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_NEAREST)
            h, w = mask.shape
            
        # [NEW CONCEPT]: The Architect's Cross-Hatch
        # Draws a technical cross-hatch (X-pattern) across the bounding box, masked by the image.
        
        y_idx, x_idx = np.where(mask > 0)
        if len(x_idx) == 0: return []
        
        min_x, max_x = np.min(x_idx), np.max(x_idx)
        min_y, max_y = np.min(y_idx), np.max(y_idx)
        
        path_data = []
        spacing = 35 # Wide spacing, thick brush
        
        # 1. Diagonal from Top-Left to Bottom-Right
        for offset in range(-h, w, spacing):
            pts = []
            for y in range(min_y, max_y, 5):
                x = y + offset
                if min_x <= x <= max_x and mask[y, x] > 0:
                    pts.append(QPointF(float(x)/scale, float(y)/scale))
                else:
                    if len(pts) > 1:
                        path_data.append({"pts": pts, "length": self._calculate_length(pts)})
                    pts = []
            if len(pts) > 1:
                path_data.append({"pts": pts, "length": self._calculate_length(pts)})
                
        # 2. Diagonal from Top-Right to Bottom-Left
        for offset in range(0, w + h, spacing):
            pts = []
            for y in range(min_y, max_y, 5):
                x = offset - y
                if min_x <= x <= max_x and mask[y, x] > 0:
                    pts.append(QPointF(float(x)/scale, float(y)/scale))
                else:
                    if len(pts) > 1:
                        path_data.append({"pts": pts, "length": self._calculate_length(pts)})
                    pts = []
            if len(pts) > 1:
                path_data.append({"pts": pts, "length": self._calculate_length(pts)})
                
        if not path_data: return []
        
        # Sort paths top-to-bottom for smooth hand flow
        path_data.sort(key=lambda item: item["pts"][0].y())
        
        timed_segments = []
        accumulated_time = 0.0
        total_length = sum(item["length"] for item in path_data) or 1.0
        
        for item in path_data:
            seg_duration = duration * (item["length"] / total_length)
            timed_segments.append({
                "type": "stroke",
                "points": item["pts"],
                "duration": seg_duration,
                "start_time": accumulated_time,
                "end_time": accumulated_time + seg_duration,
                "width": 50.0, # Massive brush to guarantee 100% ink coverage
                "opacity": 1.0
            })
            accumulated_time += seg_duration
            
        return timed_segments

    def _calculate_length(self, points: List[QPointF]) -> float:
        import math
        length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x() - points[i-1].x()
            dy = points[i].y() - points[i-1].y()
            length += math.hypot(dx, dy)
        return length
