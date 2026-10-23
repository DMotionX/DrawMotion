import cv2
import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
import math

from ..base_algorithm import BaseDrawingAlgorithm
from .ribbon_generator import generate_ribbon_paths

class RibbonFlowAlgorithm(BaseDrawingAlgorithm):
    """
    Continuous Ribbon Flow Style:
    - Entire artwork is drawn as one unbroken, fluid, elegant ribbon path.
    - Zero in-air pen lifts. Hand glides in an organic continuous flow.
    - Guaranteed full timeline synchronization: drawing progresses steadily from 0.0s to 100% of duration.
    """

    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        duration = max(0.5, float(duration or 8.0))
        
        mask = self._get_ink_mask(qimage)
        h, w = mask.shape
        
        ptr = qimage.constBits()
        arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 4))
        gray = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
        
        ribbon_paths = generate_ribbon_paths(mask, gray, scale=1.0, rtl=rtl)
        if not ribbon_paths or not ribbon_paths[0]:
            return []
            
        full_path = ribbon_paths[0]
        uniform_pts = self._resample_path_uniform(full_path, step_dist=6.0)
        total_length = self._calculate_length(uniform_pts)
        if total_length <= 0:
            return []
            
        chunk_size = 30
        timed_segments = []
        accumulated_time = 0.0
        
        for i in range(0, len(uniform_pts) - 1, chunk_size - 1):
            sub_pts = uniform_pts[i:i + chunk_size]
            if len(sub_pts) < 2:
                continue
            sub_len = self._calculate_length(sub_pts)
            seg_dur = duration * (sub_len / total_length)
            
            timed_segments.append({
                "type": "stroke",
                "points": sub_pts,
                "duration": seg_dur,
                "start_time": accumulated_time,
                "end_time": accumulated_time + seg_dur,
                "width": 6.0,
                "opacity": 1.0
            })
            accumulated_time += seg_dur

        # Smoothly normalize all timestamps to end at PRECISELY duration
        if timed_segments and accumulated_time > 0:
            scale_time = duration / accumulated_time
            cur_t = 0.0
            for seg in timed_segments:
                seg["duration"] *= scale_time
                seg["start_time"] = cur_t
                cur_t += seg["duration"]
                seg["end_time"] = cur_t

        return timed_segments

    def _calculate_length(self, points: List[QPointF]) -> float:
        l = 0.0
        for i in range(1, len(points)):
            l += math.hypot(points[i].x() - points[i-1].x(), points[i].y() - points[i-1].y())
        return l

    def _resample_path_uniform(self, points: List[QPointF], step_dist: float = 6.0) -> List[QPointF]:
        if len(points) < 2: return points
        new_pts = [points[0]]
        accum = 0.0
        for i in range(1, len(points)):
            p1, p2 = points[i-1], points[i]
            d = math.hypot(p2.x() - p1.x(), p2.y() - p1.y())
            if d == 0: continue
            while accum + d >= step_dist:
                rem = step_dist - accum
                ratio = rem / d
                nx = p1.x() + (p2.x() - p1.x()) * ratio
                ny = p1.y() + (p2.y() - p1.y()) * ratio
                mid = QPointF(nx, ny)
                new_pts.append(mid)
                p1 = mid
                d = math.hypot(p2.x() - p1.x(), p2.y() - p1.y())
                accum = 0.0
            accum += d
        if len(new_pts) < 2: new_pts.append(points[-1])
        return new_pts
