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
    Organic Sketch (Freehand Charcoal / Pencil Artist Flow):
    - 3 Artistic Construction Phases:
      1. Phase 1: Gestural Perspective Rough-in (15% duration) -> rapid axis guide curves.
      2. Phase 2: Organic Freehand Contours (45% duration) -> expressive silhouettes & line-work.
      3. Phase 3: Slanted 45° Pencil Cross-Hatching (40% duration) -> localized shading on shadows.
    - Zero Retrace & Zero Blanket Sweeps: No rubbing over white background.
    - Zero Early Completion: Ink reveals steadily from 0.0s until 8.0s.
    """
    
    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        mask = self._get_ink_mask(qimage)
        scale = 1.0
        
        islands = generate_scribble_islands(mask, scale)
        if not islands:
            return []
            
        is_phased = any("phase" in isl for isl in islands)
        if is_phased:
            timed_segments = []
            current_time = 0.0
            
            for isl in islands:
                target_phase_duration = duration * isl.get("weight", 0.33)
                paths = isl.get("paths", [])
                if not paths:
                    continue
                    
                phase_segments = []
                phase_accum = 0.0
                
                ordered_paths = self._sort_paths_continuous(paths)
                
                path_data = []
                for pts in ordered_paths:
                    if not pts:
                        continue
                    uniform_pts = self._resample_path_uniform(pts, step_dist=8.0)
                    length = self._calculate_length(uniform_pts)
                    if length > 0 or isl.get("is_dot", False):
                        path_data.append({"pts": uniform_pts, "length": max(2.0, length)})
                        
                if not path_data:
                    continue
                    
                total_phase_length = sum(item["length"] for item in path_data) or 1.0
                stroke_w = isl.get("stroke_width", 14.0)
                
                for item in path_data:
                    seg_dur = max(0.005, target_phase_duration * (item["length"] / total_phase_length))
                    
                    if phase_segments or timed_segments:
                        last_pt = phase_segments[-1]["points"][-1] if phase_segments else timed_segments[-1]["points"][-1]
                        st_pt = item["pts"][0]
                        dist = math.hypot(st_pt.x() - last_pt.x(), st_pt.y() - last_pt.y())
                        if dist > 8.0:
                            travel_dur = min(0.08, max(0.02, dist / 2200.0))
                            phase_segments.append({
                                "type": "travel",
                                "points": [last_pt, st_pt],
                                "duration": travel_dur,
                                "start_time": phase_accum,
                                "end_time": phase_accum + travel_dur,
                                "width": 0.0,
                                "opacity": 0.0
                            })
                            phase_accum += travel_dur
                            
                    phase_segments.append({
                        "type": "stroke",
                        "points": item["pts"],
                        "duration": seg_dur,
                        "start_time": phase_accum,
                        "end_time": phase_accum + seg_dur,
                        "width": stroke_w,
                        "opacity": 1.0
                    })
                    phase_accum += seg_dur
                    
                if phase_segments and phase_accum > 0:
                    scale_f = target_phase_duration / phase_accum
                    for seg in phase_segments:
                        seg["duration"] *= scale_f
                        seg["start_time"] = current_time
                        current_time += seg["duration"]
                        seg["end_time"] = current_time
                        timed_segments.append(seg)
                        
            return timed_segments

        # Fallback ordering
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
                uniform_pts = self._resample_path_uniform(pts, step_dist=8.0)
                length = self._calculate_length(uniform_pts)
                if length > 0 or island.get("is_dot", False):
                    path_data.append({"pts": uniform_pts, "length": max(2.0, length)})
                    
            if not path_data:
                continue
                
            total_island_length = sum(item["length"] for item in path_data) or 1.0
            
            for item in path_data:
                seg_share = item["length"] / total_island_length
                seg_duration = max(0.015, island_duration * seg_share)
                
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

                dynamic_width = max(18.0, min(24.0, 18.0 + item["length"] / 100.0))
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
                
        if timed_segments and accumulated_time > 0:
            scale_time = duration / accumulated_time
            cur_t = 0.0
            for seg in timed_segments:
                seg["duration"] *= scale_time
                seg["start_time"] = cur_t
                cur_t += seg["duration"]
                seg["end_time"] = cur_t
                
        return timed_segments

    def _sort_paths_continuous(self, paths: List[List[QPointF]]) -> List[List[QPointF]]:
        if len(paths) <= 1:
            return paths
        remaining = list(paths)
        sorted_p = [remaining.pop(0)]
        while remaining:
            last_pt = sorted_p[-1][-1]
            best_idx, best_dist, best_rev = 0, float('inf'), False
            for i, p in enumerate(remaining):
                st, en = p[0], p[-1]
                d_st = (st.x() - last_pt.x())**2 + (st.y() - last_pt.y())**2
                d_en = (en.x() - last_pt.x())**2 + (en.y() - last_pt.y())**2
                if d_st < best_dist:
                    best_dist, best_idx, best_rev = d_st, i, False
                if d_en < best_dist:
                    best_dist, best_idx, best_rev = d_en, i, True
            nx = remaining.pop(best_idx)
            if best_rev:
                nx = list(reversed(nx))
            sorted_p.append(nx)
        return sorted_p

    def _order_islands_artistic_flow(self, islands: List[Dict[str, Any]], rtl: bool = False) -> List[Dict[str, Any]]:
        return list(islands)

    def _calculate_length(self, points: List[QPointF]) -> float:
        length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x() - points[i-1].x()
            dy = points[i].y() - points[i-1].y()
            length += math.hypot(dx, dy)
        return length

    def _resample_path_uniform(self, points: List[QPointF], step_dist: float = 8.0) -> List[QPointF]:
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
