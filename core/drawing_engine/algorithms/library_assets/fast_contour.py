import cv2
import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
import math
from ..base_algorithm import BaseDrawingAlgorithm

class FastContourAlgorithm(BaseDrawingAlgorithm):
    """
    Fast Contour: Merges complex details into blobs to drastically reduce path count.
    """
    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        import cv2
        import numpy as np
        import math
        
        mask = self._get_ink_mask(qimage)
        scale = 1.0
        max_dim = 1000
        h, w = mask.shape
        if w > max_dim or h > max_dim:
            scale = min(max_dim / w, max_dim / h)
            mask = cv2.resize(mask, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_NEAREST)
            h, w = mask.shape
            
        # [NEW CONCEPT]: The Spiral Reveal
        # The hand draws a continuous expanding spiral from the center of the image.
        # It only draws where the mask is positive!
        
        y_idx, x_idx = np.where(mask > 0)
        if len(x_idx) == 0: return []
        
        # Center of ink
        cx = np.mean(x_idx)
        cy = np.mean(y_idx)
        
        # Max radius needed
        max_r = max(cx, w - cx, cy, h - cy) * 1.2
        
        # Generate spiral points
        spiral_spacing = 30.0 # Distance between loops (determines brush width needed)
        theta = 0.0
        theta_step = 0.2
        
        path_data = []
        current_segment = []
        
        while True:
            r = (spiral_spacing / (2 * math.pi)) * theta
            if r > max_r:
                break
                
            x = int(cx + r * math.cos(theta))
            y = int(cy + r * math.sin(theta))
            
            # Check if point is inside image and inside mask
            if 0 <= x < w and 0 <= y < h and mask[y, x] > 0:
                current_segment.append(QPointF(float(x) / scale, float(y) / scale))
            else:
                if len(current_segment) > 1:
                    length = self._calculate_length(current_segment)
                    path_data.append({"pts": current_segment, "length": length})
                current_segment = []
                
            # Decrease theta step as r increases to keep point density consistent
            theta_step = 3.0 / max(r, 1.0)
            theta += theta_step
            
        if len(current_segment) > 1:
            path_data.append({"pts": current_segment, "length": self._calculate_length(current_segment)})
            
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
                "width": spiral_spacing * 1.5, # Overlap to ensure 100% coverage
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
