import cv2
import numpy as np
import random
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
from ..base_algorithm import BaseDrawingAlgorithm

from .scribble_generator import generate_scribble_islands

class OrganicSketchAlgorithm(BaseDrawingAlgorithm):
    """
    Organic Sketch (Solid Artistic Charcoal / Bold Pencil Flow):
    - 1. Focal-First Entry: Artist begins with the primary visual subject (Character / Focal Center).
    - 2. Bold Expressive Contours + Solid Serpentine Shading with 100% solid reveal coverage.
    - 3. Strict Locality: Completely completes the current subject before moving to the next.
    - 4. Zero erratic jumping, zero flimsy wireframe scratches.
    """
    
    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        mask = self._get_ink_mask(qimage)
        scale = 1.0
        
        islands = generate_scribble_islands(mask, scale)
        if not islands:
            return []
            
        ordered_islands = self._order_islands_artistic_flow(islands, rtl=rtl)
        if not ordered_islands:
            return []

        for isl in ordered_islands:
            isl["total_length"] = sum(
                self._calculate_length(pts) for pts in isl["paths"] if pts
            ) or 1.0

        total_all_length = sum(isl["total_length"] for isl in ordered_islands) or 1.0

        timed_segments = []
        accumulated_time = 0.0
        
        for island in ordered_islands:
            island_length = island["total_length"]
            island_duration = duration * (island_length / total_all_length)
            
            path_data = []
            for pts in island["paths"]:
                if not pts:
                    continue
                # Resample path points to uniform human-speed steps (8px)
                # Eliminates sudden hand sprints over long lines so the pen tip tracks charcoal/pencil ink accurately
                uniform_pts = self._resample_path_uniform(pts, step_dist=8.0)
                length = self._calculate_length(uniform_pts)
                if length > 0 or island.get("is_dot", False):
                    path_data.append({"pts": uniform_pts, "length": max(2.0, length)})
                    
            if not path_data:
                continue
                
            # Authentic Freehand Sketch Artist Ordering:
            # 1. Expressive structural contours first (outlines) to capture the silhouette
            # 2. Energetic 45° diagonal pencil shading sweeps second to render the volume
            outlines = [item for item in path_data if len(item["pts"]) > 2]
            shades = [item for item in path_data if len(item["pts"]) <= 2]
            
            # Sort outlines continuously (longest primary contour first, then nearest neighbor)
            sorted_outlines = []
            if outlines:
                outlines.sort(key=lambda item: -item["length"])
                sorted_outlines = [outlines.pop(0)]
                while outlines:
                    last_pt = sorted_outlines[-1]["pts"][-1]
                    best_idx, best_dist, best_rev = 0, float('inf'), False
                    for i, item in enumerate(outlines):
                        st, en = item["pts"][0], item["pts"][-1]
                        d_st = (st.x() - last_pt.x())**2 + (st.y() - last_pt.y())**2
                        d_en = (en.x() - last_pt.x())**2 + (en.y() - last_pt.y())**2
                        if d_st < best_dist: best_dist, best_idx, best_rev = d_st, i, False
                        if d_en < best_dist: best_dist, best_idx, best_rev = d_en, i, True
                    nx = outlines.pop(best_idx)
                    if best_rev: nx["pts"].reverse()
                    sorted_outlines.append(nx)
                    
            # Sort shading strokes starting directly from where the outlines ended
            sorted_shades = []
            if shades:
                if sorted_outlines:
                    last_pt = sorted_outlines[-1]["pts"][-1]
                else:
                    last_pt = shades[0]["pts"][0]
                    
                while shades:
                    best_idx, best_dist, best_rev = 0, float('inf'), False
                    for i, item in enumerate(shades):
                        st, en = item["pts"][0], item["pts"][-1]
                        d_st = (st.x() - last_pt.x())**2 + (st.y() - last_pt.y())**2
                        d_en = (en.x() - last_pt.x())**2 + (en.y() - last_pt.y())**2
                        if d_st < best_dist: best_dist, best_idx, best_rev = d_st, i, False
                        if d_en < best_dist: best_dist, best_idx, best_rev = d_en, i, True
                    nx = shades.pop(best_idx)
                    if best_rev: nx["pts"].reverse()
                    sorted_shades.append(nx)
                    last_pt = sorted_shades[-1]["pts"][-1]
                    
            path_data = sorted_outlines + sorted_shades
                
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

                # Bold Solid Charcoal / Pencil width (20-26px) for 100% solid reveal coverage
                dynamic_width = max(20.0, min(26.0, 20.0 + item["length"] / 100.0))
                
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

    def _order_islands_artistic_flow(self, islands: List[Dict[str, Any]], rtl: bool = False) -> List[Dict[str, Any]]:
        """
        Orders islands using authentic human sketch artist flow:
        - Starts at the most prominent visual subject (or top-right for RTL / top-left for LTR).
        - Flows continuously to the nearest neighboring element (Continuous Spatial Proximity)
          with a natural progressive sweep, eliminating erratic jumping without forcing
          rigid horizontal notebook lines across illustrations.
        """
        if not islands or len(islands) <= 1:
            return list(islands)
            
        remaining = list(islands)
        
        # 1. Natural artistic entry point:
        # A sketcher naturally begins at the primary focal element (large area) near the top,
        # or at top-right (for RTL) / top-left (for LTR).
        def entry_score(it):
            cx, cy = it.get("centroid", (0, 0))
            area = it.get("area", 100.0)
            area_weight = min(4.0, math.sqrt(max(1.0, area)) / 40.0)
            if rtl:
                return cy * 1.5 - cx * 0.8 - area_weight * 25.0
            else:
                return cy * 1.5 + cx * 0.8 - area_weight * 25.0
                
        remaining.sort(key=entry_score)
        ordered = [remaining.pop(0)]
        
        # 2. Continuous Proximity Flow (Nearest Neighbor with smooth directional sweep)
        while remaining:
            curr_cx, curr_cy = ordered[-1].get("centroid", (0, 0))
            best_idx = 0
            best_cost = float("inf")
            
            for i, cand in enumerate(remaining):
                cand_cx, cand_cy = cand.get("centroid", (0, 0))
                dx = cand_cx - curr_cx
                dy = cand_cy - curr_cy
                dist = math.hypot(dx, dy)
                
                # Directional bias: gentle penalty for backtracking
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
        Eliminates hand acceleration spikes across long lines, ensuring the charcoal / pencil tip
        tracks the drawn strokes smoothly with 100% precision.
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
