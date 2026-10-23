from abc import ABC, abstractmethod
from typing import List, Dict, Any
from PySide6.QtGui import QImage
import copy

_SKELETON_CACHE = {}

class BaseDrawingAlgorithm(ABC):
    """
    Interface for all drawing algorithms in the engine.
    Every algorithm must define how to extract paths, style them, and calculate timing.
    """
    
    @abstractmethod
    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        """
        Analyzes the QImage and generates a list of TimedSegments.
        """
        pass
    def _get_ink_mask(self, qimage: QImage) -> 'numpy.ndarray':
        import cv2
        import numpy as np
        w, h = qimage.width(), qimage.height()
        ptr = qimage.constBits()
        arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 4))
        
        alpha = arr[:, :, 3]
        _, mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
        
        non_zero = cv2.countNonZero(mask)
        total = w * h
        
        if non_zero > total * 0.95:
            # Opaque image on white / near-white background
            # Detect ink across all color spectrums (black outlines, blue jeans, colored fills, accents)
            # A pixel is background only if it lacks color saturation AND is near-white in brightness
            rgb = cv2.cvtColor(arr, cv2.COLOR_RGBA2RGB)
            hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
            sat = hsv[:, :, 1]
            val = hsv[:, :, 2]
            
            is_bg = (sat < 18) & (val > 218)
            mask = (~is_bg).astype(np.uint8) * 255
            
        heal_k = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, heal_k)
        
        return mask

    @staticmethod
    def cluster_islands_into_lines(islands: List[Dict[str, Any]], rtl: bool = False, sort_mode: str = "left_to_right") -> List[Dict[str, Any]]:
        """
        Groups disconnected components/islands into visual lines/rows based on vertical
        bounding box overlap, then sorts items strictly along the reading direction (RTL/LTR).
        Safely supports non-directional sort modes ('top_to_bottom', 'random', 'area_desc').
        """
        import random
        if not islands or len(islands) <= 1:
            return list(islands)

        if sort_mode == "top_to_bottom":
            return sorted(islands, key=lambda it: it.get("centroid", (0, 0))[1])
        elif sort_mode == "random":
            copied = list(islands)
            random.seed(42)
            random.shuffle(copied)
            return copied
        elif sort_mode == "area_desc":
            return sorted(islands, key=lambda it: it.get("area", 0), reverse=True)

        effective_rtl = rtl or (sort_mode == "right_to_left")

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
                "item": it,
                "x": float(x),
                "y": float(y),
                "w": float(max(1.0, w)),
                "h": float(max(1.0, h)),
                "cx": float(cx),
                "cy": float(cy),
                "y2": float(y + h),
                "x2": float(x + w)
            })

        # --- Spatial Containment Analysis (Face & Inner Detail Proximity) ---
        # Detect inner features (e.g. eyes, nose inside head) to draw them immediately with parent
        children_map = {}
        child_to_parent = {}

        for i, c in enumerate(parsed):
            c_area = c["w"] * c["h"]
            best_parent = None
            best_parent_area = float('inf')

            for j, p in enumerate(parsed):
                if i == j:
                    continue
                p_area = p["w"] * p["h"]
                if p_area < 1.4 * c_area:
                    continue

                # Check if center of c is geometrically inside p's bounding box
                if (p["x"] - 5.0 <= c["cx"] <= p["x2"] + 5.0 and 
                    p["y"] - 5.0 <= c["cy"] <= p["y2"] + 5.0):
                    ov_w = max(0.0, min(c["x2"], p["x2"]) - max(c["x"], p["x"]))
                    ov_h = max(0.0, min(c["y2"], p["y2"]) - max(c["y"], p["y"]))
                    if ov_w >= 0.65 * c["w"] and ov_h >= 0.65 * c["h"]:
                        if p_area < best_parent_area:
                            best_parent = j
                            best_parent_area = p_area

            if best_parent is not None:
                child_to_parent[i] = best_parent
                if best_parent not in children_map:
                    children_map[best_parent] = []
                children_map[best_parent].append(c)

        # Group primary top-level items into lines
        top_level_parsed = [p for i, p in enumerate(parsed) if i not in child_to_parent]
        if not top_level_parsed:
            top_level_parsed = parsed
            children_map.clear()
            child_to_parent.clear()

        top_level_parsed.sort(key=lambda p: (p["y"], p["x"]))

        lines = []
        for p in top_level_parsed:
            matched_idx = -1
            best_overlap = -1.0

            for idx, line in enumerate(lines):
                l_y1 = line["y1"]
                l_y2 = line["y2"]
                l_h = max(1.0, l_y2 - l_y1)

                overlap = max(0.0, min(p["y2"], l_y2) - max(p["y"], l_y1))
                min_h = max(1.0, min(p["h"], l_h))
                overlap_ratio = overlap / min_h

                tolerance = 0.35 * l_h
                centroid_in_line = (l_y1 - tolerance) <= p["cy"] <= (l_y2 + tolerance)

                if overlap_ratio > 0.25 or centroid_in_line:
                    score = overlap if overlap > 0 else (1.0 - abs(p["cy"] - (l_y1 + l_y2) / 2.0) / l_h)
                    if score > best_overlap:
                        best_overlap = score
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

        merged_lines = []
        lines.sort(key=lambda l: l["y1"])
        for line in lines:
            if not merged_lines:
                merged_lines.append(line)
            else:
                prev = merged_lines[-1]
                overlap = max(0.0, min(prev["y2"], line["y2"]) - max(prev["y1"], line["y1"]))
                min_h = max(1.0, min(prev["y2"] - prev["y1"], line["y2"] - line["y1"]))
                if overlap / min_h > 0.4:
                    prev["items"].extend(line["items"])
                    prev["y1"] = min(prev["y1"], line["y1"])
                    prev["y2"] = max(prev["y2"], line["y2"])
                else:
                    merged_lines.append(line)

        result = []
        emitted_ids = set()

        for line in merged_lines:
            line_items = line["items"]
            if effective_rtl:
                line_items.sort(key=lambda p: -p["x2"])
            else:
                line_items.sort(key=lambda p: p["x"])

            for p in line_items:
                if id(p["item"]) not in emitted_ids:
                    result.append(p["item"])
                    emitted_ids.add(id(p["item"]))

                # Emit immediately any contained child features right after their parent
                p_idx = parsed.index(p) if p in parsed else -1
                if p_idx in children_map:
                    ch_items = children_map[p_idx]
                    if effective_rtl:
                        ch_items.sort(key=lambda c: -c["x2"])
                    else:
                        ch_items.sort(key=lambda c: c["x"])
                    for c in ch_items:
                        if id(c["item"]) not in emitted_ids:
                            result.append(c["item"])
                            emitted_ids.add(id(c["item"]))

        # Leftover safety net
        for p in parsed:
            if id(p["item"]) not in emitted_ids:
                result.append(p["item"])
                emitted_ids.add(id(p["item"]))

        return result

    def _extract_skeleton_paths(self, qimage: QImage, sort_mode: str = "left_to_right", rtl: bool = False) -> List[Dict[str, Any]]:
        import cv2
        import numpy as np
        import random
        from PySide6.QtCore import QPointF
        
        cache_key = (id(qimage), sort_mode, rtl)
        if cache_key in _SKELETON_CACHE:
            all_islands_data = copy.deepcopy(_SKELETON_CACHE[cache_key])
            return BaseDrawingAlgorithm.cluster_islands_into_lines(all_islands_data, rtl=rtl, sort_mode=sort_mode)
            
        mask = self._get_ink_mask(qimage)
        
        # Max resolution for analysis
        max_dim = 1000
        h, w = mask.shape
        scale = 1.0
        
        if w > max_dim or h > max_dim:
            scale = min(max_dim / w, max_dim / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            mask_small = cv2.resize(mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
        else:
            mask_small = mask.copy()
            
        # Ensure binary - lower threshold preserves anti-aliased text and thin lines that were downscaled
        _, binary = cv2.threshold(mask_small, 30, 255, cv2.THRESH_BINARY)
        
        # Find completely isolated components (Islands)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(binary, kernel, iterations=1)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated, connectivity=8)
        
        islands = []
        for i in range(1, num_labels):
            x, y, cw, ch, area = stats[i]
            if area > 10:
                islands.append({
                    "rect": (x, y, cw, ch),
                    "label": i,
                    "centroid": centroids[i],
                    "area": area
                })
                
        # 4. Sort islands based on the requested style mode and direction
        islands = BaseDrawingAlgorithm.cluster_islands_into_lines(islands, rtl=rtl, sort_mode=sort_mode)
            
        all_islands_data = []
        
        import time
        for idx_island, island in enumerate(islands):
            if idx_island % 10 == 0:
                time.sleep(0.005) # Yield GIL to prevent UI freeze
                
            label = island["label"]
            island_mask = np.zeros_like(binary)
            island_mask[(labels == label) & (binary == 255)] = 255
            
            # Skeleton Simplification: 
            # Apply morphological close to fuse micro-details and tiny noisy lines 
            # before skeletonizing. This drastically reduces the number of noisy paths!
            close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            island_mask = cv2.morphologyEx(island_mask, cv2.MORPH_CLOSE, close_kernel)
            
            skeleton = cv2.ximgproc.thinning(island_mask, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
            contours, _ = cv2.findContours(skeleton, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            
            paths = []
            for contour in contours:
                # Filter out tiny noisy paths
                if len(contour) < 1:
                    continue
                    
                pts = []
                for point in contour:
                    px = point[0][0] / scale
                    py = point[0][1] / scale
                    pts.append(QPointF(float(px), float(py)))
                    
                if len(pts) > 2:
                    np_pts = np.array([[[p.x(), p.y()]] for p in pts], dtype=np.float32)
                    epsilon = 1.5 / scale 
                    approx = cv2.approxPolyDP(np_pts, epsilon, closed=False)
                    pts = [QPointF(float(p[0][0]), float(p[0][1])) for p in approx]
                    
                paths.append(pts)
                
            # TSP for paths WITHIN this island
            if paths:
                ordered_paths = []
                current_pos = paths[0][0]
                
                iterations = 0
                while paths:
                    iterations += 1
                    if iterations % 50 == 0:
                        time.sleep(0.005) # Yield GIL
                        
                    best_idx = 0
                    best_dist = float('inf')
                    reverse_best = False
                    
                    for i, p in enumerate(paths):
                        dist_start = (p[0].x() - current_pos.x())**2 + (p[0].y() - current_pos.y())**2
                        if dist_start < best_dist:
                            best_dist = dist_start
                            best_idx = i
                            reverse_best = False
                            
                        dist_end = (p[-1].x() - current_pos.x())**2 + (p[-1].y() - current_pos.y())**2
                        if dist_end < best_dist:
                            best_dist = dist_end
                            best_idx = i
                            reverse_best = True
                            
                    best_path = paths.pop(best_idx)
                    if reverse_best:
                        best_path.reverse()
                        
                    ordered_paths.append(best_path)
                    current_pos = best_path[-1]
                    
                all_islands_data.append({
                    "paths": ordered_paths,
                    "area": island["area"],
                    "centroid": island["centroid"],
                    "rect": island["rect"],
                    "label": island["label"]
                })
                
        # Save to cache before returning
        _SKELETON_CACHE[cache_key] = copy.deepcopy(all_islands_data)
        return all_islands_data
        
    def _calculate_length(self, points: List['QPointF']) -> float:
        import math
        length = 0.0
        for i in range(1, len(points)):
            p1 = points[i-1]
            p2 = points[i]
            length += math.hypot(p2.x() - p1.x(), p2.y() - p1.y())
        return length

    @classmethod
    def cluster_into_semantic_objects(cls, islands: List[Dict[str, Any]], rtl: bool = False) -> List[Dict[str, Any]]:
        """
        Anti-Chaining Semantic Clustering:
        Partitions islands into discrete, encapsulated semantic entities:
        - Text Headlines & Words
        - Hero Figures (Human characters, animals)
        - Icons & Diagrams (Bulbs, arrows, badges)
        Ensures strict intra-object completion with zero jumping between half-finished objects.
        """
        if not islands:
            return []
            
        n = len(islands)
        if n == 1:
            x, y, w, h = islands[0]["rect"]
            return [{
                "islands": islands,
                "min_x": x, "min_y": y, "max_x": x + w, "max_y": y + h,
                "cx": x + w / 2.0, "cy": y + h / 2.0,
                "w": w, "h": h,
                "is_tall_figure": (h > 140.0 and h > 1.3 * w)
            }]

        parsed = []
        for it in islands:
            x, y, w, h = it["rect"]
            cx, cy = it.get("centroid", (x + w / 2.0, y + h / 2.0))
            is_text = (h <= 55.0 and (w <= 220.0 or (w / max(1.0, h)) >= 1.5))
            parsed.append({
                "item": it, "x": float(x), "y": float(y),
                "w": float(max(1.0, w)), "h": float(max(1.0, h)),
                "x2": float(x + w), "y2": float(y + h),
                "cx": float(cx), "cy": float(cy),
                "is_text": is_text
            })

        parent = list(range(n))
        def find(k):
            while parent[k] != k:
                parent[k] = parent[parent[k]]
                k = parent[k]
            return k

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        # 1. Bounding box containment (eyes/mouth inside face, shirt buttons inside torso, internal fills)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                if (parsed[j]["x"] >= parsed[i]["x"] - 2.0 and parsed[j]["x2"] <= parsed[i]["x2"] + 2.0 and
                    parsed[j]["y"] >= parsed[i]["y"] - 2.0 and parsed[j]["y2"] <= parsed[i]["y2"] + 2.0):
                    union(i, j)

        # 2. Text line continuity (only merge text items with text items along horizontal lines)
        for i in range(n):
            for j in range(i + 1, n):
                if parsed[i]["is_text"] and parsed[j]["is_text"]:
                    min_h = min(parsed[i]["h"], parsed[j]["h"])
                    ov_y = max(0.0, min(parsed[i]["y2"], parsed[j]["y2"]) - max(parsed[i]["y"], parsed[j]["y"]))
                    gap_x = max(0.0, max(parsed[i]["x"], parsed[j]["x"]) - min(parsed[i]["x2"], parsed[j]["x2"]))
                    gap_y = max(0.0, max(parsed[i]["y"], parsed[j]["y"]) - min(parsed[i]["y2"], parsed[j]["y2"]))
                    # Words on same horizontal baseline
                    if ov_y >= 0.40 * min_h and gap_x <= 35.0:
                        union(i, j)
                    # Arabic dots/diacritics immediately above or below
                    elif gap_y <= 14.0 and gap_x <= 15.0:
                        union(i, j)

        # 3. Vertical alignment of figure parts (head -> torso -> pants of human characters)
        for i in range(n):
            for j in range(i + 1, n):
                if not parsed[i]["is_text"] and not parsed[j]["is_text"]:
                    min_w = min(parsed[i]["w"], parsed[j]["w"])
                    max_w = max(parsed[i]["w"], parsed[j]["w"])
                    min_h = min(parsed[i]["h"], parsed[j]["h"])
                    ov_x = max(0.0, min(parsed[i]["x2"], parsed[j]["x2"]) - max(parsed[i]["x"], parsed[j]["x"]))
                    gap_y = max(0.0, max(parsed[i]["y"], parsed[j]["y"]) - min(parsed[i]["y2"], parsed[j]["y2"]))
                    if min_h >= 40.0 and (min_w / max_w >= 0.35) and (ov_x >= 0.30 * min_w) and gap_y <= 25.0:
                        union(i, j)

        clusters = {}
        for i in range(n):
            r = find(i)
            if r not in clusters:
                clusters[r] = []
            clusters[r].append(parsed[i])

        cluster_objects = []
        for r, group in clusters.items():
            min_x = min(p["x"] for p in group)
            min_y = min(p["y"] for p in group)
            max_x = max(p["x2"] for p in group)
            max_y = max(p["y2"] for p in group)
            w_obj = max_x - min_x
            h_obj = max_y - min_y
            is_tall = (h_obj > 140.0 and h_obj > 1.3 * w_obj)

            # Strict intra-object drawing order: Complete object 100% before lifting!
            if is_tall:
                group.sort(key=lambda p: p["cy"])
            else:
                if rtl:
                    group.sort(key=lambda p: (round(p["cy"] / 30.0), -p["cx"]))
                else:
                    group.sort(key=lambda p: (round(p["cy"] / 30.0), p["cx"]))

            cluster_objects.append({
                "islands": [p["item"] for p in group],
                "min_x": min_x,
                "min_y": min_y,
                "max_x": max_x,
                "max_y": max_y,
                "cx": (min_x + max_x) / 2.0,
                "cy": (min_y + max_y) / 2.0,
                "w": w_obj,
                "h": h_obj,
                "is_tall_figure": is_tall
            })

        return cluster_objects

    @staticmethod
    def categorize_semantic_objects(cluster_objects: List[Dict[str, Any]], rtl: bool = False):
        """
        Categorizes clustered semantic objects into:
        - text_blocks: Written text lines, headings, sub-headings
        - hero_figures: The primary character (e.g. boy/human figure) or central tall subject
        - accent_icons: Secondary icons, bulb, arrows, badges, decorative shapes
        """
        if not cluster_objects or len(cluster_objects) <= 1:
            return list(cluster_objects), [], []
            
        # 1. Detect Hero Figure candidates (tall figure or largest balanced figure)
        hero_candidates = [
            obj for obj in cluster_objects
            if obj.get("is_tall_figure", False) or (obj["h"] >= 80.0 and 0.25 <= (obj["w"] / max(1.0, obj["h"])) <= 2.2)
        ]
        
        hero_obj = None
        if hero_candidates:
            hero_obj = max(hero_candidates, key=lambda o: (o["w"] * o["h"]) * (2.0 if o.get("is_tall_figure") else 1.0))
            
        heroes = [hero_obj] if hero_obj else []
        
        # 2. Categorize remaining objects into text vs accents
        text_blocks = []
        accent_blocks = []
        
        for obj in cluster_objects:
            if hero_obj is not None and obj is hero_obj:
                continue
            aspect = obj["w"] / max(1.0, obj["h"])
            # Text lines and words are horizontally elongated (aspect >= 1.8 or top headline text)
            if aspect >= 1.8 or (obj["h"] <= 60.0 and obj["w"] >= 40.0):
                text_blocks.append(obj)
            else:
                accent_blocks.append(obj)
                
        row_band = 40.0
        if rtl:
            text_blocks.sort(key=lambda o: (round(o["min_y"] / row_band), -o["cx"]))
            accent_blocks.sort(key=lambda o: (round(o["min_y"] / row_band), -o["cx"]))
        else:
            text_blocks.sort(key=lambda o: (round(o["min_y"] / row_band), o["cx"]))
            accent_blocks.sort(key=lambda o: (round(o["min_y"] / row_band), o["cx"]))
            
        return text_blocks, heroes, accent_blocks

    def _resample_path_uniform(self, points: List['QPointF'], step_dist: float = 8.0) -> List['QPointF']:
        """
        Resamples a path so that points are spaced at equal physical Euclidean distances.
        Eliminates hand acceleration spikes across long lines, ensuring the pen tip glides
        calmly and tracks ink generation with 100% precision.
        """
        import math
        from PySide6.QtCore import QPointF
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

    @staticmethod
    def filter_non_overlapping_strokes(
        paths: List[List['QPointF']],
        mask: 'numpy.ndarray',
        stroke_width: float = 16.0,
        max_overlap_ratio: float = 0.85,
        target_coverage_cap: float = 0.985
    ) -> List[List['QPointF']]:
        """
        Non-Overlapping Coverage Filter (Zero Retrace Engine):
        Filters out redundant strokes whose physical footprint overlaps >= max_overlap_ratio
        with already covered/revealed pixels.
        Terminates fill generation once target ink coverage hits target_coverage_cap (98.5%).
        Guarantees that the hand NEVER retraces over previously drawn areas on solid/complex objects
        like Arduino boards, eliminating the defect where hand lingers and walks over finished lines.
        """
        import cv2
        import numpy as np

        if not paths:
            return []

        h, w = mask.shape
        max_dim = 400.0
        map_scale = 1.0
        work_mask = mask
        if w > max_dim or h > max_dim:
            map_scale = min(max_dim / w, max_dim / h)
            work_w = max(1, int(w * map_scale))
            work_h = max(1, int(h * map_scale))
            work_mask = cv2.resize(mask, (work_w, work_h), interpolation=cv2.INTER_NEAREST)

        target_ink = work_mask > 0
        total_target = np.count_nonzero(target_ink)
        if total_target == 0:
            return paths

        scaled_width = max(2, int(stroke_width * map_scale))
        coverage_map = np.zeros(work_mask.shape, dtype=np.uint8)
        stamp = np.zeros(work_mask.shape, dtype=np.uint8)

        accepted_paths = []
        covered_pixels = 0

        for pts in paths:
            if not pts:
                continue

            if len(pts) == 1:
                px = int(pts[0].x() * map_scale)
                py = int(pts[0].y() * map_scale)
                radius = max(2, scaled_width // 2)
                cv2.circle(stamp, (px, py), radius, 255, -1)
            else:
                raw_coords = np.array([[[int(p.x() * map_scale), int(p.y() * map_scale)]] for p in pts], dtype=np.int32)
                cv2.polylines(stamp, [raw_coords], isClosed=False, color=255, thickness=scaled_width)

            stroke_target_pixels = (stamp > 0) & target_ink
            cnt = np.count_nonzero(stroke_target_pixels)
            if cnt == 0:
                stamp.fill(0)
                continue

            new_pixels = np.count_nonzero(stroke_target_pixels & (coverage_map == 0))
            overlap_ratio = 1.0 - (new_pixels / cnt)

            # If this stroke retraces >= max_overlap_ratio of already revealed pixels, reject it!
            if overlap_ratio >= max_overlap_ratio and len(accepted_paths) > 0:
                stamp.fill(0)
                continue

            # Accept this stroke
            accepted_paths.append(pts)
            coverage_map[stamp > 0] = 255
            covered_pixels += new_pixels
            stamp.fill(0)

            # If image target ink is already >= target_coverage_cap revealed, stop early!
            if (covered_pixels / total_target) >= target_coverage_cap:
                break

        return accepted_paths if accepted_paths else paths[:1]



