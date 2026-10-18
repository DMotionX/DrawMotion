import cv2
import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
import math
from ..base_algorithm import BaseDrawingAlgorithm

class IconSketchAlgorithm(BaseDrawingAlgorithm):
    """
    Icon Sketch: Simplifies details, traces connected main lines (pencil style) 
    with no random hatching.
    """
    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        import cv2
        import numpy as np
        import random
        
        mask = self._get_ink_mask(qimage)
        scale = 1.0
        max_dim = 1000
        h, w = mask.shape
        if w > max_dim or h > max_dim:
            scale = min(max_dim / w, max_dim / h)
            mask = cv2.resize(mask, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_NEAREST)
            h, w = mask.shape
            
        # [NEW CONCEPT]: The Passionate Scribble
        # Instead of contours, we sample random points inside the mask and connect them into a single chaotic stroke!
        
        y_idx, x_idx = np.where(mask > 0)
        total_ink_pixels = len(x_idx)
        
        if total_ink_pixels == 0:
            return []
            
        # Sample points based on shape size to ensure coverage (max 300 points for speed)
        num_points = min(300, total_ink_pixels // 100)
        if num_points < 10: num_points = 10
        
        # Randomly pick indices
        random.seed(42) # Deterministic
        sample_indices = random.sample(range(total_ink_pixels), num_points)
        
        points = []
        for idx in sample_indices:
            points.append(QPointF(float(x_idx[idx]) / scale, float(y_idx[idx]) / scale))
            
        # TSP (Nearest Neighbor) to connect them into a single continuous scribble
        if not points: return []
        
        # Start at the highest point (top of the shape)
        points.sort(key=lambda p: p.y())
        scribble_path = [points.pop(0)]
        
        while points:
            last_p = scribble_path[-1]
            best_idx = 0
            best_dist = float('inf')
            for i, p in enumerate(points):
                dist = (p.x() - last_p.x())**2 + (p.y() - last_p.y())**2
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i
            scribble_path.append(points.pop(best_idx))
            
        # Calculate length
        length = self._calculate_length(scribble_path)
        
        timed_segments = [{
            "type": "stroke",
            "points": scribble_path,
            "duration": duration,
            "start_time": 0.0,
            "end_time": duration,
            "width": 60.0, # Massive brush because the scribble points are sparse! This covers the whole shape.
            "opacity": 1.0
        }]
            
        return timed_segments

    def _calculate_length(self, points: List[QPointF]) -> float:
        import math
        length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x() - points[i-1].x()
            dy = points[i].y() - points[i-1].y()
            length += math.hypot(dx, dy)
        return length
