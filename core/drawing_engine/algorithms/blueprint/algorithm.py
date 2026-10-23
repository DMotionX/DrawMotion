import cv2
import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
import math

from ..base_algorithm import BaseDrawingAlgorithm
from .blueprint_generator import generate_blueprint_paths

class BlueprintDraftingAlgorithm(BaseDrawingAlgorithm):
    """
    Blueprint Drafting Style:
    - Tier 1 (15% duration): Architectural construction datum lines & corner drafting crosshairs.
    - Tier 2 (35% duration): Outer structural chassis & major framing boundaries.
    - Tier 3 (25% duration): Medium functional components and connectors.
    - Tier 4 (25% duration): Fine internal details, pin marks, and silkscreen labels.
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
        
        paths_dict = generate_blueprint_paths(mask, gray, scale=1.0)
        
        guide_paths = paths_dict.get("guide_paths", [])
        chassis_paths = paths_dict.get("chassis_paths", [])
        component_paths = paths_dict.get("component_paths", [])
        detail_paths = paths_dict.get("detail_paths", [])
        
        all_drawing_paths = chassis_paths + component_paths + detail_paths
        if not guide_paths and not all_drawing_paths:
            return []
            
        clean_drawing_paths = self.filter_non_overlapping_strokes(
            all_drawing_paths, mask, stroke_width=10.0, max_overlap_ratio=0.85
        ) if all_drawing_paths else []
        if not clean_drawing_paths and all_drawing_paths:
            clean_drawing_paths = all_drawing_paths
            
        guide_budget = min(0.5, duration * 0.08) if guide_paths else 0.0
        draw_budget = duration - guide_budget
        
        timed_segments = []
        accumulated_time = 0.0
        
        def pack_and_sort(raw_paths, budget_dur, base_w, opacity_val):
            nonlocal accumulated_time
            if not raw_paths:
                return
            
            packed = []
            for pts in raw_paths:
                if not pts:
                    continue
                u_pts = self._resample_path_uniform(pts, step_dist=8.0)
                l = self._calculate_length(u_pts)
                if l > 0:
                    packed.append({"pts": u_pts, "length": l})
            if not packed:
                return
            
            total_l = sum(p["length"] for p in packed) or 1.0
            
            if rtl:
                packed.sort(key=lambda item: (min(p.y() for p in item["pts"]), -max(p.x() for p in item["pts"])))
            else:
                packed.sort(key=lambda item: (min(p.y() for p in item["pts"]), min(p.x() for p in item["pts"])))
                
            sorted_p = [packed.pop(0)]
            while packed:
                last_pt = sorted_p[-1]["pts"][-1]
                best_idx, best_dist, best_rev = 0, float('inf'), False
                limit = min(len(packed), 40)
                for i in range(limit):
                    st, en = packed[i]["pts"][0], packed[i]["pts"][-1]
                    d_st = (st.x() - last_pt.x())**2 + (st.y() - last_pt.y())**2
                    d_en = (en.x() - last_pt.x())**2 + (en.y() - last_pt.y())**2
                    if d_st < best_dist:
                        best_dist, best_idx, best_rev = d_st, i, False
                    if d_en < best_dist:
                        best_dist, best_idx, best_rev = d_en, i, True
                nx = packed.pop(best_idx)
                if best_rev:
                    nx["pts"].reverse()
                sorted_p.append(nx)
                
            for item in sorted_p:
                seg_dur = max(0.005, budget_dur * (item["length"] / total_l))
                if timed_segments:
                    prev_pt = timed_segments[-1]["points"][-1]
                    curr_st = item["pts"][0]
                    dist = math.hypot(curr_st.x() - prev_pt.x(), curr_st.y() - prev_pt.y())
                    if dist > 8.0:
                        travel_dur = min(0.04, max(0.01, dist / 2500.0))
                        timed_segments.append({
                            "type": "travel",
                            "points": [prev_pt, curr_st],
                            "duration": travel_dur,
                            "start_time": accumulated_time,
                            "end_time": accumulated_time + travel_dur,
                            "width": 0.0,
                            "opacity": 0.0
                        })
                        accumulated_time += travel_dur
                        
                timed_segments.append({
                    "type": "stroke",
                    "points": item["pts"],
                    "duration": seg_dur,
                    "start_time": accumulated_time,
                    "end_time": accumulated_time + seg_dur,
                    "width": base_w,
                    "opacity": opacity_val
                })
                accumulated_time += seg_dur

        # 1. Technical Guide Crosshairs & Datum Lines (snappy initial architectural layout)
        if guide_paths:
            pack_and_sort(guide_paths, guide_budget, base_w=3.0, opacity_val=0.5)
            
        # 2. Main Structural Blueprint Drafting (filtered, non-overlapping, steady reveal)
        if clean_drawing_paths:
            pack_and_sort(clean_drawing_paths, draw_budget, base_w=10.0, opacity_val=1.0)
        
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

    def _resample_path_uniform(self, points: List[QPointF], step_dist: float = 8.0) -> List[QPointF]:
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
