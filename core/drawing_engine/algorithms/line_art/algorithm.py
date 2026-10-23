import cv2
import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
import math
from ..base_algorithm import BaseDrawingAlgorithm
from .line_art_generator import generate_line_art_paths

class LineArtAlgorithm(BaseDrawingAlgorithm):
    """
    Coloring Book style (Line Art): Extracts grayscale Canny edges to capture all internal 
    details of complex images (like Arduino) and draws them with a uniform thin pen.
    """
    
    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        w, h = qimage.width(), qimage.height()
        ptr = qimage.constBits()
        arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 4))
        
        # Convert to grayscale for detailed edge extraction
        gray = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
        
        # Otsu's thresholding to dynamically find optimal Canny thresholds
        high_thresh, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        low_thresh = 0.5 * high_thresh
        
        # Extract all edges
        edges = cv2.Canny(gray, low_thresh, high_thresh)
        
        # Get the reliable ink mask (handles white and transparent backgrounds perfectly)
        ink_mask = self._get_ink_mask(qimage)
        
        # Draw the true outer boundary onto the edges so we don't lose the main outline
        contours, _ = cv2.findContours(ink_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(edges, contours, -1, 255, 1)
        
        # Mask out any edges that fall outside the true drawing area (erases background noise)
        edges = cv2.bitwise_and(edges, ink_mask)
        
        # Dilate slightly to connect broken lines before tracing
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        scale = 1.0
        islands = generate_line_art_paths(ink_mask, gray, scale)
        if not islands:
            return []
        
        # Sort islands naturally into reading lines (RTL / LTR) - Preserved drawing system
        islands = BaseDrawingAlgorithm.cluster_islands_into_lines(
            islands, rtl=rtl, sort_mode="right_to_left" if rtl else "left_to_right"
        )
        
        for isl in islands:
            isl["total_length"] = sum(
                self._calculate_length(pts) for pts in isl.get("paths", []) if pts
            ) or 1.0

        total_length_all = sum(isl["total_length"] for isl in islands) or 1.0

        timed_segments = []
        accumulated_time = 0.0
        
        for island in islands:
            island_length = island["total_length"]
            island_duration = duration * (island_length / total_length_all)
            
            # Helper to resample and pack strokes
            def pack_strokes(raw_list, is_edge):
                packed = []
                for pts in raw_list:
                    if not pts: continue
                    u_pts = self._resample_path_uniform(pts, step_dist=8.0)
                    length = self._calculate_length(u_pts)
                    if length > 0 or island.get("is_dot", False):
                        packed.append({"pts": u_pts, "length": max(2.0, length), "is_edge": is_edge})
                return packed

            edge_data = pack_strokes(island.get("edge_paths", []), is_edge=True)
            fill_data = pack_strokes(island.get("fill_paths", []), is_edge=False)
            
            if not edge_data and not fill_data:
                edge_data = pack_strokes(island.get("paths", []), is_edge=True)

            # Preserve exact existing line art sorting system:
            # Progressive Structural Build (Zero-Risk)
            row_height = max(20.0, float(h) / 20.0)
            
            # 1. Sort Edge Inking Paths (Coloring Book Line Art)
            sorted_edges = []
            if edge_data:
                if rtl:
                    edge_data.sort(key=lambda item, rh=row_height: (min(p.y() for p in item["pts"]) // rh, -max(p.x() for p in item["pts"])))
                    for item in edge_data:
                        if len(item["pts"]) >= 2 and item["pts"][0].x() < item["pts"][-1].x():
                            item["pts"].reverse()
                else:
                    edge_data.sort(key=lambda item: min(p.y() for p in item["pts"]))
                    
                sorted_edges = [edge_data.pop(0)]
                while edge_data:
                    last_pt = sorted_edges[-1]["pts"][-1]
                    best_idx, best_dist, best_needs_reverse = 0, float('inf'), False
                    search_limit = min(len(edge_data), 35)
                    for i in range(search_limit):
                        item = edge_data[i]
                        st, en = item["pts"][0], item["pts"][-1]
                        d_st = (st.x() - last_pt.x())**2 + (st.y() - last_pt.y())**2
                        d_en = (en.x() - last_pt.x())**2 + (en.y() - last_pt.y())**2
                        if d_st < best_dist: best_dist, best_idx, best_needs_reverse = d_st, i, False
                        if d_en < best_dist: best_dist, best_idx, best_needs_reverse = d_en, i, True
                    nx = edge_data.pop(best_idx)
                    if best_needs_reverse: nx["pts"].reverse()
                    sorted_edges.append(nx)
                    
            # 2. Sort Fill Paths (Smooth cell coloring for solid reveal)
            sorted_fills = []
            if fill_data:
                last_pt = sorted_edges[-1]["pts"][-1] if sorted_edges else fill_data[0]["pts"][0]
                while fill_data:
                    best_idx, best_dist, best_needs_reverse = 0, float('inf'), False
                    search_limit = min(len(fill_data), 35)
                    for i in range(search_limit):
                        item = fill_data[i]
                        st, en = item["pts"][0], item["pts"][-1]
                        d_st = (st.x() - last_pt.x())**2 + (st.y() - last_pt.y())**2
                        d_en = (en.x() - last_pt.x())**2 + (en.y() - last_pt.y())**2
                        if d_st < best_dist: best_dist, best_idx, best_needs_reverse = d_st, i, False
                        if d_en < best_dist: best_dist, best_idx, best_needs_reverse = d_en, i, True
                    nx = fill_data.pop(best_idx)
                    if best_needs_reverse: nx["pts"].reverse()
                    sorted_fills.append(nx)
                    last_pt = sorted_fills[-1]["pts"][-1]

            path_data = sorted_edges + sorted_fills
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

                # Precise inking pen (4.0px) for edges, solid coloring brush (20-24px) for fills
                dynamic_width = 4.0 if item.get("is_edge", True) else max(20.0, min(24.0, 20.0 + item["length"] / 100.0))
                
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
        Eliminates sudden hand sprints over long curves so the inking pen tip tracks ink with 100% precision.
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
