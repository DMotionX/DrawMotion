import cv2
import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
import math
from ..base_algorithm import BaseDrawingAlgorithm
from .human_fill_generator import generate_human_islands

class CleanOutlineAlgorithm(BaseDrawingAlgorithm):
    """
    Professional style: Draws perfect centerlines with a thick, smooth brush to completely fill the ink.
    Longest paths are drawn first (like a professional architect).
    """
    
    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        mask = self._get_ink_mask(qimage)
        h, w = mask.shape
        max_dim = 1600.0
        scale = 1.0
        
        if w > max_dim or h > max_dim:
            scale = max_dim / max(w, h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            mask = cv2.resize(mask, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
        raw_islands = generate_human_islands(mask, scale)
        if not raw_islands:
            return []
            
        # 1. Spatial Proximity & Containment Fusion (Union-Find)
        # Guarantees inner details (eyes, nose, mouth, diacritics) are fused into their parent 
        # contour, completely eliminating blank facial patches and delayed pop-ins.
        n = len(raw_islands)
        parent_uf = list(range(n))
        
        def find_uf(k):
            while parent_uf[k] != k:
                parent_uf[k] = parent_uf[parent_uf[k]]
                k = parent_uf[k]
            return k

        def union_uf(a, b):
            ra, rb = find_uf(a), find_uf(b)
            if ra != rb:
                parent_uf[ra] = rb

        for j, child in enumerate(raw_islands):
            c_x, c_y, c_w, c_h = child["rect"]
            c_area = child["area"]
            c_cx, c_cy = child["centroid"]
            
            if c_area > 8000.0:
                continue
                
            best_parent_idx = None
            best_parent_area = float('inf')
            
            for i, p_candidate in enumerate(raw_islands):
                if i == j:
                    continue
                p_x, p_y, p_w, p_h = p_candidate["rect"]
                p_area = p_candidate["area"]
                if p_area < 1.8 * c_area:
                    continue
                    
                margin_x = 20.0
                margin_y = 26.0
                if (p_x - margin_x <= c_cx <= p_x + p_w + margin_x and
                    p_y - margin_y <= c_cy <= p_y + p_h + margin_y):
                    if p_area < best_parent_area:
                        best_parent_area = p_area
                        best_parent_idx = i
                        
            if best_parent_idx is not None:
                union_uf(j, best_parent_idx)

        groups = {}
        for j in range(n):
            r = find_uf(j)
            if r not in groups:
                groups[r] = []
            groups[r].append(raw_islands[j])

        merged_islands = []
        for r, group in groups.items():
            rep = max(group, key=lambda it: it["area"])
            all_x = [isl["rect"][0] for isl in group]
            all_y = [isl["rect"][1] for isl in group]
            all_x2 = [isl["rect"][0] + isl["rect"][2] for isl in group]
            all_y2 = [isl["rect"][1] + isl["rect"][3] for isl in group]
            bx, by = min(all_x), min(all_y)
            bw = max(all_x2) - bx
            bh = max(all_y2) - by
            
            all_paths = []
            for isl in group:
                all_paths.extend(isl["paths"])
                
            merged_islands.append({
                "rect": (bx, by, bw, bh),
                "label": rep["label"],
                "centroid": rep["centroid"],
                "area": sum(isl["area"] for isl in group),
                "paths": all_paths
            })

        # 2. Sort islands naturally into reading lines (RTL / LTR)
        islands = BaseDrawingAlgorithm.cluster_islands_into_lines(
            merged_islands, rtl=rtl, sort_mode="right_to_left" if rtl else "left_to_right"
        )
        
        timed_segments = []
        accumulated_time = 0.0
        total_area = sum(island["area"] for island in islands) or 1.0
        
        # Pen width guarantees 100% overlap between 5x5 kernel erosion concentric rings
        step_canvas = 3.0 / scale
        pen_width = max(24.0, step_canvas * 2.5)
        
        for island in islands:
            island_area = island["area"]
            island_duration = duration * (island_area / total_area)
            
            path_data = []
            for pts in island["paths"]:
                length = self._calculate_length(pts)
                path_data.append({"pts": pts, "length": max(1.0, length)})
                
            if not path_data:
                continue
                
            # Outermost ring / contour drawn first, followed by continuous nearest-neighbor inner rings
            if len(path_data) > 1:
                path_data.sort(key=lambda item: -item["length"])
                sorted_paths = [path_data.pop(0)]
                
                while path_data:
                    last_pt = sorted_paths[-1]["pts"][-1]
                    best_idx = 0
                    best_dist = float('inf')
                    best_needs_reverse = False
                    
                    for i, item in enumerate(path_data):
                        start_pt = item["pts"][0]
                        end_pt = item["pts"][-1]
                        d_start = (start_pt.x() - last_pt.x())**2 + (start_pt.y() - last_pt.y())**2
                        d_end = (end_pt.x() - last_pt.x())**2 + (end_pt.y() - last_pt.y())**2
                        
                        if d_start < best_dist:
                            best_dist = d_start
                            best_idx = i
                            best_needs_reverse = False
                            
                        if d_end < best_dist:
                            best_dist = d_end
                            best_idx = i
                            best_needs_reverse = True
                            
                    next_item = path_data.pop(best_idx)
                    if best_needs_reverse:
                        next_item["pts"].reverse()
                    sorted_paths.append(next_item)
                    
                path_data = sorted_paths
                    
            total_island_length = sum(item["length"] for item in path_data) or 1.0
            
            for item in path_data:
                seg_share = item["length"] / total_island_length
                seg_duration = island_duration * seg_share
                
                timed_segments.append({
                    "type": "stroke",
                    "points": item["pts"],
                    "duration": seg_duration,
                    "start_time": accumulated_time,
                    "end_time": accumulated_time + seg_duration,
                    "width": pen_width,
                    "opacity": 1.0
                })
                accumulated_time += seg_duration
                
        # Normalize timeline smoothly to requested duration
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
        length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x() - points[i-1].x()
            dy = points[i].y() - points[i-1].y()
            length += math.hypot(dx, dy)
        return length
