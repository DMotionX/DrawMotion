from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
import math
from ..base_algorithm import BaseDrawingAlgorithm
from .professional_generator import generate_professional_paths

class ProfessionalAlgorithm(BaseDrawingAlgorithm):
    """
    Professional Vector Drawing (CAD Structural Hierarchy & Whiteboard Flow):
    - 4-Tier CAD Structural Assembly:
      1. Tier 1: External Chassis & Primary Silhouettes (25% duration)
      2. Tier 2: Major IC Units, Ports & Localized Solid Fills (25% duration)
      3. Tier 3: Discrete Components, Pins, & Sockets (25% duration)
      4. Tier 4: Fine Copper Traces, Vias, & Silkscreen Labels (25% duration)
    - Zero Retrace & Zero Blanket Sweeps: No rubbing over white background.
    - Zero Early Completion: Ink reveals steadily from 0.0s until 8.0s.
    """
    
    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        mask = self._get_ink_mask(qimage)
        scale = 1.0
        
        islands = generate_professional_paths(mask, scale)
        if not islands:
            return []
            
        # Check if islands are already structured into architectural tiers
        is_tiered = any("tier" in isl for isl in islands)
        if is_tiered:
            timed_segments = []
            current_time = 0.0
            
            for isl in islands:
                target_tier_duration = duration * isl.get("weight", 0.25)
                paths = isl.get("paths", [])
                if not paths:
                    continue
                    
                tier_segments = []
                tier_accum = 0.0
                
                # Order paths continuously using spatial nearest-neighbor
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
                    
                total_tier_length = sum(item["length"] for item in path_data) or 1.0
                stroke_w = isl.get("stroke_width", 14.0)
                
                for item in path_data:
                    seg_dur = max(0.005, target_tier_duration * (item["length"] / total_tier_length))
                    
                    # In-air travel flight
                    if tier_segments or timed_segments:
                        last_pt = tier_segments[-1]["points"][-1] if tier_segments else timed_segments[-1]["points"][-1]
                        st_pt = item["pts"][0]
                        dist = math.hypot(st_pt.x() - last_pt.x(), st_pt.y() - last_pt.y())
                        if dist > 8.0:
                            travel_dur = min(0.06, max(0.015, dist / 2500.0))
                            tier_segments.append({
                                "type": "travel",
                                "points": [last_pt, st_pt],
                                "duration": travel_dur,
                                "start_time": tier_accum,
                                "end_time": tier_accum + travel_dur,
                                "width": 0.0,
                                "opacity": 0.0
                            })
                            tier_accum += travel_dur
                            
                    tier_segments.append({
                        "type": "stroke",
                        "points": item["pts"],
                        "duration": seg_dur,
                        "start_time": tier_accum,
                        "end_time": tier_accum + seg_dur,
                        "width": stroke_w,
                        "opacity": 1.0
                    })
                    tier_accum += seg_dur
                    
                # Normalize THIS TIER to EXACTLY target_tier_duration!
                if tier_segments and tier_accum > 0:
                    scale_f = target_tier_duration / tier_accum
                    for seg in tier_segments:
                        seg["duration"] *= scale_f
                        seg["start_time"] = current_time
                        current_time += seg["duration"]
                        seg["end_time"] = current_time
                        timed_segments.append(seg)
                        
            return timed_segments
            
        # Fallback Semantic Clustering for non-tiered inputs
        cluster_objects = self._cluster_into_semantic_objects(islands, rtl=rtl)
        if not cluster_objects:
            return []
            
        num_blocks = len(cluster_objects)
        total_sqrt_area = sum(math.sqrt(max(100.0, obj["w"] * obj["h"])) for obj in cluster_objects) or 1.0
        
        for obj in cluster_objects:
            obj["total_length"] = sum(
                sum(self._calculate_length(pts) for pts in isl["paths"] if pts)
                for isl in obj["islands"]
            ) or 1.0
            
        total_all_length = sum(obj["total_length"] for obj in cluster_objects) or 1.0
        
        for obj in cluster_objects:
            area_factor = math.sqrt(max(100.0, obj["w"] * obj["h"])) / total_sqrt_area
            length_factor = obj["total_length"] / total_all_length
            uniform_factor = 1.0 / num_blocks
            weight = 0.40 * area_factor + 0.45 * length_factor + 0.15 * uniform_factor
            obj["duration"] = duration * weight
            
        timed_segments = []
        accumulated_time = 0.0
        
        for obj in cluster_objects:
            block_duration = obj["duration"]
            block_total_len = obj["total_length"]
            
            for island in obj["islands"]:
                island_length = sum(self._calculate_length(pts) for pts in island["paths"] if pts)
                island_duration = block_duration * (island_length / block_total_len)
                
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
                stroke_w = island.get("stroke_width", 14.0)
                
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

                    timed_segments.append({
                        "type": "stroke",
                        "points": item["pts"],
                        "duration": seg_duration,
                        "start_time": accumulated_time,
                        "end_time": accumulated_time + seg_duration,
                        "width": stroke_w,
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

    def _cluster_into_semantic_objects(self, islands: List[Dict[str, Any]], rtl: bool = False) -> List[Dict[str, Any]]:
        cluster_objects = BaseDrawingAlgorithm.cluster_into_semantic_objects(islands, rtl=rtl)
        text_blocks, heroes, accents = BaseDrawingAlgorithm.categorize_semantic_objects(cluster_objects, rtl=rtl)
        return heroes + accents + text_blocks

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
