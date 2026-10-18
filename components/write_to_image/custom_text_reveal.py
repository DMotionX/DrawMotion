import cv2
import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
import math

class CustomTextRevealAlgorithm:
    """
    Custom optimized version of SolidReveal tailored strictly for Text.
    Uses a much larger grid size for a fatter brush, reducing the path density 
    and allowing the hand to move extremely fast and smoothly.
    Also aggressively connects Arabic diacritics to prevent jumping.
    """
    
    def _get_ink_mask(self, qimage: QImage) -> np.ndarray:
        w, h = qimage.width(), qimage.height()
        ptr = qimage.constBits()
        arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 4))
        
        alpha = arr[:, :, 3]
        _, mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
        return mask

    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        
        mask = self._get_ink_mask(qimage)
        h, w = mask.shape
        
        if not np.any(mask):
            return []
            
        segments = []
        
        # 1. Connect letters horizontally into islands
        if rtl:
            # Arabic: cursive, connect letters and dots into words
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        else:
            # English: keep letters separate to draw them individually
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            
        dilated = cv2.dilate(mask, kernel, iterations=1)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated, connectivity=8)
        
        islands = []
        for i in range(1, num_labels):
            x, y, cw, ch, area = stats[i]
            if area > 10:
                islands.append({
                    "rect": (x, y, cw, ch),
                    "centroid": centroids[i]
                })
                
        # 2. Sort islands: Top to Bottom (by clustered Y lines), then LTR or RTL
        from core.drawing_engine.algorithms.base_algorithm import BaseDrawingAlgorithm
        islands = BaseDrawingAlgorithm.cluster_islands_into_lines(
            islands, rtl=rtl, sort_mode="right_to_left" if rtl else "left_to_right"
        )
            
        # Brush size defines how thick the scrub is
        grid_size = 25
        
        # 3. Generate organic TSP path for each island
        for island in islands:
            x, y, cw, ch = island["rect"]
            
            blocks = []
            for r in range(y, y + ch, grid_size):
                for c in range(x, x + cw, grid_size):
                    r_end = min(r + grid_size, h)
                    c_end = min(c + grid_size, w)
                    # Use raw mask to only draw actual ink
                    if np.any(mask[r:r_end, c:c_end]):
                        blocks.append((c + grid_size//2, r + grid_size//2))
                        
            if not blocks:
                continue
                
            # Nearest Neighbor TSP to organically trace the ink
            path = []
            if rtl:
                # Start at top-right for Arabic
                start_idx = max(range(len(blocks)), key=lambda i: blocks[i][0] - blocks[i][1])
            else:
                # Start at top-left for English
                start_idx = min(range(len(blocks)), key=lambda i: blocks[i][0] + blocks[i][1])
                
            path.append(blocks.pop(start_idx))
            
            while blocks:
                curr = path[-1]
                blocks_arr = np.array(blocks)
                dists = (blocks_arr[:, 0] - curr[0])**2 + (blocks_arr[:, 1] - curr[1])**2
                min_idx = int(np.argmin(dists))
                path.append(blocks.pop(min_idx))
                
            pts = [QPointF(float(p[0]), float(p[1])) for p in path]
            
            if len(pts) == 1:
                pts.append(QPointF(pts[0].x() + 1, pts[0].y()))
                
            length = self._calculate_length(pts)
            segments.append({
                "type": "stroke",
                "points": pts,
                "length": length,
                "width": grid_size * 2.5, # Overlap nicely to ensure solid coverage
                "opacity": 1.0
            })
            
        # 4. Assign timestamps
        total_length = sum(seg["length"] for seg in segments) or 1.0
        accumulated_time = 0.0
        
        timed_segments = []
        for seg in segments:
            seg_share = seg["length"] / total_length
            seg_duration = duration * seg_share
            
            timed_segments.append({
                "type": seg["type"],
                "points": seg["points"],
                "duration": seg_duration,
                "start_time": accumulated_time,
                "end_time": accumulated_time + seg_duration,
                "width": seg["width"],
                "opacity": seg["opacity"]
            })
            accumulated_time += seg_duration
            
        return timed_segments

    def _calculate_length(self, points: List[QPointF]) -> float:
        length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x() - points[i-1].x()
            dy = points[i].y() - points[i-1].y()
            length += math.hypot(dx, dy)
        return length
