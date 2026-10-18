import cv2
import numpy as np
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
from ..base_algorithm import BaseDrawingAlgorithm
from .smart_education_generator import generate_smart_educational_paths

class HatchShadingAlgorithm(BaseDrawingAlgorithm):
    """
    Smart Educational (Solid Chisel-Tip Whiteboard Educator Flow):
    - 1. Pedagogical Top-to-Bottom Entry: Teacher begins with the Header / Main Lesson Title at the top.
    - 2. Crisp Technical Boundaries + Solid Chisel-Tip Marker Fills with 100% solid reveal coverage.
    - 3. Strict Concept Completion: Completes each educational block 100% before moving to the next.
    - 4. Zero erratic jumping, completely eliminates thin, flimsy skeleton wireframes.
    """
    
    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        mask = self._get_ink_mask(qimage)
        scale = 1.0
        
        islands = generate_smart_educational_paths(mask, scale)
        if not islands:
            return []
            
        # Natural Pedagogical Whiteboard Order:
        # Strictly clusters into reading lines (Top-to-Bottom).
        # In RTL (Arabic): draws from Right to Left, finishing each word completely with its dots
        # before moving to the next word. Eliminates all random jumping!
        ordered_islands = self._cluster_islands_pedagogical(islands, rtl=rtl)
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
                # Eliminates sudden hand sprints over long lines so the pen tip tracks ink with 100% precision
                uniform_pts = self._resample_path_uniform(pts, step_dist=8.0)
                length = self._calculate_length(uniform_pts)
                if length > 0 or island.get("is_dot", False):
                    path_data.append({"pts": uniform_pts, "length": max(2.0, length)})
                    
            if not path_data:
                continue
                
            # Strict Concept Completion: Boundary outlines first, then chisel marker sweeps
            if len(path_data) > 1:
                primary = path_data.pop(0)
                remaining = path_data
                sorted_paths = [primary]
                while remaining:
                    last_pt = sorted_paths[-1]["pts"][-1]
                    best_idx, best_dist, best_rev = 0, float('inf'), False
                    for i, item in enumerate(remaining):
                        st, en = item["pts"][0], item["pts"][-1]
                        d_st = (st.x() - last_pt.x())**2 + (st.y() - last_pt.y())**2
                        d_en = (en.x() - last_pt.x())**2 + (en.y() - last_pt.y())**2
                        if d_st < best_dist: best_dist, best_idx, best_rev = d_st, i, False
                        if d_en < best_dist: best_dist, best_idx, best_rev = d_en, i, True
                    nx = remaining.pop(best_idx)
                    if best_rev: nx["pts"].reverse()
                    sorted_paths.append(nx)
                path_data = sorted_paths
                
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

                # Solid Chisel-Tip Marker width (22-28px) for 100% solid reveal coverage with calm sweeps
                dynamic_width = max(22.0, min(28.0, 22.0 + item["length"] / 120.0))
                
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

    def _cluster_islands_pedagogical(self, islands: List[Dict[str, Any]], rtl: bool = False) -> List[Dict[str, Any]]:
        """
        Groups islands strictly into pedagogical whiteboard reading lines and concepts:
        - 1. Identifies and binds Arabic dots and diacritics immediately to their base words.
        - 2. Uses anti-avalanche line span bounds to prevent lines from ballooning into lower regions.
        - 3. Orders lines Top-to-Bottom, and strokes strictly along the reading direction (RTL / LTR).
        - 4. Completes each word and its dots 100% locally before proceeding. Eliminates erratic jumps!
        """
        if not islands or len(islands) <= 1:
            return list(islands)

        parsed = []
        for it in islands:
            if "rect" in it and len(it["rect"]) == 4:
                x, y, w, h = it["rect"]
            else:
                cx, cy = it.get("centroid", (0, 0))
                x, y, w, h = cx - 10.0, cy - 10.0, 20.0, 20.0
            cx = it["centroid"][0] if "centroid" in it else x + w / 2.0
            cy = it["centroid"][1] if "centroid" in it else y + h / 2.0
            parsed.append({
                "item": it, "x": float(x), "y": float(y),
                "w": float(max(1.0, w)), "h": float(max(1.0, h)),
                "cx": float(cx), "cy": float(cy),
                "y2": float(y + h), "x2": float(x + w),
                "area": float(it.get("area", w * h))
            })

        # Step 1: Associate dots and diacritics directly with their base letters/words
        children_map = {}
        child_to_parent = {}

        for i, c in enumerate(parsed):
            if c["area"] > 120.0:
                continue
            best_parent = None
            best_dist = float("inf")
            for j, p in enumerate(parsed):
                if i == j or p["area"] < 150.0:
                    continue
                ov_x = max(0.0, min(c["x2"], p["x2"]) - max(c["x"], p["x"]))
                gap_y = max(0.0, max(c["y"], p["y"]) - min(c["y2"], p["y2"]))
                cen_dx = abs(c["cx"] - p["cx"])
                if (ov_x >= 0.3 * c["w"] or cen_dx <= 20.0) and gap_y <= 22.0:
                    d = gap_y + 0.5 * cen_dx
                    if d < best_dist:
                        best_dist = d
                        best_parent = j

            if best_parent is not None:
                child_to_parent[i] = best_parent
                if best_parent not in children_map:
                    children_map[best_parent] = []
                children_map[best_parent].append(c)

        # Step 2: Form visual lines from top-level parents
        top_level = [p for i, p in enumerate(parsed) if i not in child_to_parent]
        top_level.sort(key=lambda p: (p["y"], p["x"]))

        heights = [p["h"] for p in top_level if p["h"] >= 8.0]
        median_h = float(np.median(heights)) if heights else 30.0
        max_line_span = max(50.0, 1.8 * median_h)

        lines = []
        for p in top_level:
            matched_idx = -1
            best_score = -1.0

            for idx, line in enumerate(lines):
                l_y1 = line["y1"]
                l_y2 = line["y2"]
                l_h = max(1.0, l_y2 - l_y1)

                # Anti-avalanche guard: prevents lines from swelling and swallowing distant shapes!
                new_y1 = min(l_y1, p["y"])
                new_y2 = max(l_y2, p["y2"])
                if (new_y2 - new_y1) > max_line_span:
                    continue

                overlap = max(0.0, min(p["y2"], l_y2) - max(p["y"], l_y1))
                min_h = max(1.0, min(p["h"], l_h))
                overlap_ratio = overlap / min_h

                tolerance = 0.30 * l_h
                centroid_in_line = (l_y1 - tolerance) <= p["cy"] <= (l_y2 + tolerance)

                if overlap_ratio > 0.25 or centroid_in_line:
                    score = overlap if overlap > 0 else (1.0 - abs(p["cy"] - (l_y1 + l_y2) / 2.0) / l_h)
                    if score > best_score:
                        best_score = score
                        matched_idx = idx

            if matched_idx >= 0:
                target_line = lines[matched_idx]
                target_line["items"].append(p)
                target_line["y1"] = min(target_line["y1"], p["y"])
                target_line["y2"] = max(target_line["y2"], p["y2"])
            else:
                lines.append({
                    "y1": p["y"],
                    "y2": p["y2"],
                    "items": [p]
                })

        # Sort lines strictly Top-to-Bottom
        lines.sort(key=lambda l: (l["y1"] + l["y2"]) / 2.0)

        # Step 3: Emit items strictly in reading order
        result = []
        emitted_ids = set()

        for line in lines:
            line_items = line["items"]
            if rtl:
                line_items.sort(key=lambda p: -p["x2"])
            else:
                line_items.sort(key=lambda p: p["x"])

            for p in line_items:
                if id(p["item"]) not in emitted_ids:
                    result.append(p["item"])
                    emitted_ids.add(id(p["item"]))

                # Emit dots/diacritics belonging to this parent immediately!
                p_idx = parsed.index(p) if p in parsed else -1
                if p_idx in children_map:
                    dots = children_map[p_idx]
                    if rtl:
                        dots.sort(key=lambda d: -d["x2"])
                    else:
                        dots.sort(key=lambda d: d["x"])
                    for d in dots:
                        if id(d["item"]) not in emitted_ids:
                            result.append(d["item"])
                            emitted_ids.add(id(d["item"]))

        # Leftover safety net
        for p in parsed:
            if id(p["item"]) not in emitted_ids:
                result.append(p["item"])
                emitted_ids.add(id(p["item"]))

        return result

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
        Eliminates hand acceleration spikes across long lines, ensuring the chisel marker tip glides
        calmly and tracks ink generation with 100% precision.
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
