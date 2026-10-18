from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
import math
import numpy as np
from ..base_algorithm import BaseDrawingAlgorithm
from .topographic_generator import generate_topographic_paths

class TopographicShadingAlgorithm(BaseDrawingAlgorithm):
    """
    Topographic Hatch Shading (Solid 3D Elevation Contour Flow):
    - 1. Calculates distance transform per connected component to extract true 3D volume contours.
    - 2. Concentric inner rings climb smoothly from outer boundaries to inner peaks.
    - 3. Small central peaks and narrow tips are capped with center dabs to guarantee 100% solid coverage.
    - 4. Completely eliminates hollow white rings and faded translucent washes with 100% solid reveal coverage.
    """
    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        mask = self._get_ink_mask(qimage)
        scale = 1.0
        
        islands = generate_topographic_paths(mask, scale)
        if not islands:
            return []
            
        ordered_islands = self._order_islands_topographic_scan(islands, rtl=rtl)
        if not ordered_islands:
            return []

        for isl in ordered_islands:
            isl["total_length"] = sum(
                self._calculate_length(pts) for pts in isl["paths"] if pts
            ) or 1.0

        total_length_all = sum(isl["total_length"] for isl in ordered_islands) or 1.0
        
        timed_segments = []
        accumulated_time = 0.0
        
        for island in ordered_islands:
            island_length = island["total_length"]
            island_duration = duration * (island_length / total_length_all)
            
            # Helper to resample and pack strokes
            def pack_strokes(raw_list):
                packed = []
                for pts in raw_list:
                    if not pts:
                        continue
                    u_pts = self._resample_path_uniform(pts, step_dist=8.0)
                    length = self._calculate_length(u_pts)
                    if length > 0 or island.get("is_dot", False):
                        packed.append({"pts": u_pts, "length": max(2.0, length)})
                return packed

            raw_outlines = pack_strokes(island.get("outlines", []))
            raw_pass1 = pack_strokes(island.get("pass1", []))
            raw_pass2 = pack_strokes(island.get("pass2", []))
            
            # Fallback if island only has 'paths'
            if not raw_outlines and not raw_pass1 and not raw_pass2:
                all_packed = pack_strokes(island.get("paths", []))
                raw_outlines = [p for p in all_packed if len(p["pts"]) > 2]
                raw_pass1 = [p for p in all_packed if len(p["pts"]) <= 2]

            # 1. Sort Outlines continuously (longest perimeter first, then nearest neighbor)
            sorted_outlines = []
            if raw_outlines:
                raw_outlines.sort(key=lambda item: -item["length"])
                sorted_outlines = [raw_outlines.pop(0)]
                while raw_outlines:
                    last_pt = sorted_outlines[-1]["pts"][-1]
                    best_idx, best_dist, best_rev = 0, float('inf'), False
                    for i, item in enumerate(raw_outlines):
                        st, en = item["pts"][0], item["pts"][-1]
                        d_st = (st.x() - last_pt.x())**2 + (st.y() - last_pt.y())**2
                        d_en = (en.x() - last_pt.x())**2 + (en.y() - last_pt.y())**2
                        if d_st < best_dist: best_dist, best_idx, best_rev = d_st, i, False
                        if d_en < best_dist: best_dist, best_idx, best_rev = d_en, i, True
                    nx = raw_outlines.pop(best_idx)
                    if best_rev: nx["pts"].reverse()
                    sorted_outlines.append(nx)
                    
            # 2. Sort Pass 1 (+45° parallel hatching ///) starting from where outlines ended
            sorted_pass1 = []
            if raw_pass1:
                last_pt = sorted_outlines[-1]["pts"][-1] if sorted_outlines else raw_pass1[0]["pts"][0]
                while raw_pass1:
                    best_idx, best_dist, best_rev = 0, float('inf'), False
                    for i, item in enumerate(raw_pass1):
                        st, en = item["pts"][0], item["pts"][-1]
                        d_st = (st.x() - last_pt.x())**2 + (st.y() - last_pt.y())**2
                        d_en = (en.x() - last_pt.x())**2 + (en.y() - last_pt.y())**2
                        if d_st < best_dist: best_dist, best_idx, best_rev = d_st, i, False
                        if d_en < best_dist: best_dist, best_idx, best_rev = d_en, i, True
                    nx = raw_pass1.pop(best_idx)
                    if best_rev: nx["pts"].reverse()
                    sorted_pass1.append(nx)
                    last_pt = sorted_pass1[-1]["pts"][-1]
                    
            # 3. Sort Pass 2 (-45° cross-hatching \\\\) starting from where Pass 1 ended
            sorted_pass2 = []
            if raw_pass2:
                if sorted_pass1:
                    last_pt = sorted_pass1[-1]["pts"][-1]
                elif sorted_outlines:
                    last_pt = sorted_outlines[-1]["pts"][-1]
                else:
                    last_pt = raw_pass2[0]["pts"][0]
                while raw_pass2:
                    best_idx, best_dist, best_rev = 0, float('inf'), False
                    for i, item in enumerate(raw_pass2):
                        st, en = item["pts"][0], item["pts"][-1]
                        d_st = (st.x() - last_pt.x())**2 + (st.y() - last_pt.y())**2
                        d_en = (en.x() - last_pt.x())**2 + (en.y() - last_pt.y())**2
                        if d_st < best_dist: best_dist, best_idx, best_rev = d_st, i, False
                        if d_en < best_dist: best_dist, best_idx, best_rev = d_en, i, True
                    nx = raw_pass2.pop(best_idx)
                    if best_rev: nx["pts"].reverse()
                    sorted_pass2.append(nx)
                    last_pt = sorted_pass2[-1]["pts"][-1]

            path_data = sorted_outlines + sorted_pass1 + sorted_pass2
            if not path_data:
                continue
                
            total_island_length = sum(item["length"] for item in path_data) or 1.0
            
            for item in path_data:
                seg_share = item["length"] / total_island_length
                seg_duration = max(0.015, island_duration * seg_share)
                
                # In-air travel flight between strokes
                if timed_segments:
                    last_pt = timed_segments[-1]["points"][-1]
                    cur_start = item["pts"][0]
                    dx = cur_start.x() - last_pt.x()
                    dy = cur_start.y() - last_pt.y()
                    air_dist = math.hypot(dx, dy)
                    if air_dist > 12.0:
                        travel_dur = min(0.12, max(0.035, air_dist / 1400.0))
                        timed_segments.append({
                            "type": "travel",
                            "points": [last_pt, cur_start],
                            "duration": travel_dur,
                            "start_time": accumulated_time,
                            "end_time": accumulated_time + travel_dur,
                            "width": 0.0,
                            "opacity": 0.0
                        })
                        accumulated_time += travel_dur

                # Solid Classic Cross-Hatching width (12-14px) with opacity 1.0 for 100% solid reveal coverage
                dynamic_width = max(11.5, min(14.0, 11.5 + item["length"] / 120.0))
                
                timed_segments.append({
                    "type": "stroke",
                    "points": item["pts"],
                    "duration": seg_duration,
                    "start_time": accumulated_time,
                    "end_time": accumulated_time + seg_duration,
                    "width": dynamic_width, 
                    "opacity": 1.0
                })
                accumulated_time += seg_duration
                
        # Normalize timeline smoothly to duration
        if timed_segments and accumulated_time > 0:
            scale_time = duration / accumulated_time
            cur_t = 0.0
            for seg in timed_segments:
                seg["duration"] *= scale_time
                seg["start_time"] = cur_t
                cur_t += seg["duration"]
                seg["end_time"] = cur_t
                
        return timed_segments

    def _order_islands_topographic_scan(self, islands: List[Dict[str, Any]], rtl: bool = False) -> List[Dict[str, Any]]:
        """
        Orders islands using a smooth 3D topographic relief scan:
        - Sweeps across the canvas smoothly (respecting RTL / LTR).
        - Connects to adjacent terrain via spatial proximity, eliminating abrupt jumps.
        - Preserves 3D spatial integrity without slicing objects into text lines.
        """
        if not islands or len(islands) <= 1:
            return list(islands)
            
        remaining = list(islands)
        
        # Natural starting terrain: top-right for RTL / top-left for LTR
        def entry_score(it):
            cx, cy = it.get("centroid", (0, 0))
            if rtl:
                return cy * 1.5 - cx * 0.8
            else:
                return cy * 1.5 + cx * 0.8
                
        remaining.sort(key=entry_score)
        ordered = [remaining.pop(0)]
        
        while remaining:
            curr_cx, curr_cy = ordered[-1].get("centroid", (0, 0))
            best_idx = 0
            best_cost = float("inf")
            
            for i, cand in enumerate(remaining):
                cand_cx, cand_cy = cand.get("centroid", (0, 0))
                dx = cand_cx - curr_cx
                dy = cand_cy - curr_cy
                dist = math.hypot(dx, dy)
                
                # Smooth directional bias to guide terrain sweep
                backtrack_x = dx if rtl else -dx
                penalty_x = max(0.0, backtrack_x) * 0.5
                backtrack_y = -dy
                penalty_y = max(0.0, backtrack_y) * 0.3
                
                cost = dist + penalty_x + penalty_y
                if cost < best_cost:
                    best_cost = cost
                    best_idx = i
                    
            ordered.append(remaining.pop(best_idx))
            
        return ordered

    def _calculate_length(self, points: List[QPointF]) -> float:
        length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x() - points[i-1].x()
            dy = points[i].y() - points[i-1].y()
            length += math.hypot(dx, dy)
        return length

    def _resample_path_uniform(self, points: List[QPointF], step_dist: float = 8.0) -> List[QPointF]:
        """
        Resamples a path so that points are spaced at equal physical Euclidean distances.
        Eliminates hand acceleration spikes across long contour rings, ensuring the pen tip
        glides calmly and tracks ink generation with 100% precision.
        """
        if len(points) < 2:
            return points
        new_pts = [points[0]]
        accum_dist = 0.0
        for i in range(1, len(points)):
            p0 = points[i-1]
            p1 = points[i]
            dx = p1.x() - p0.x()
            dy = p1.y() - p0.y()
            seg_dist = math.hypot(dx, dy)
            if seg_dist < 1e-4:
                continue
            curr_p = p0
            while accum_dist + seg_dist >= step_dist:
                needed = step_dist - accum_dist
                t = needed / seg_dist
                new_p = QPointF(curr_p.x() + (p1.x() - curr_p.x()) * t,
                                curr_p.y() + (p1.y() - curr_p.y()) * t)
                new_pts.append(new_p)
                seg_dist -= needed
                curr_p = new_p
                accum_dist = 0.0
            accum_dist += seg_dist
        if math.hypot(points[-1].x() - new_pts[-1].x(), points[-1].y() - new_pts[-1].y()) > 1.0:
            new_pts.append(points[-1])
        return new_pts
