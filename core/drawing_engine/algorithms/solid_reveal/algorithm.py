import cv2
import numpy as np
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from typing import List, Dict, Any
from ..base_algorithm import BaseDrawingAlgorithm

import copy
_SOLID_CACHE = {}

class SolidRevealAlgorithm(BaseDrawingAlgorithm):
    """
    Algorithm for solid mask shading. 
    Divides the image into completely independent ink islands, 
    and shades them one by one using an organic grid path.
    """
    
    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        cache_key = (id(qimage), rtl, duration)
        
        if cache_key in _SOLID_CACHE:
            return copy.deepcopy(_SOLID_CACHE[cache_key])
            
        w, h = qimage.width(), qimage.height()
        ptr = qimage.constBits()
        arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 4)).copy()
        
        # Only process pixels with alpha > 10
        alpha = arr[:, :, 3]
        valid_mask = alpha > 10
        
        if not np.any(valid_mask):
            return []
            
        mask = self._get_ink_mask(qimage)
        h, w = mask.shape
        
        # 1. Connect anti-aliased pixels to form solid islands
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(mask, kernel, iterations=1)
        
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated, connectivity=8)
        
        raw_islands = []
        for i in range(1, num_labels):
            x, y, cw, ch, area = stats[i]
            if area > 10:
                raw_islands.append({
                    "rect": (int(x), int(y), int(cw), int(ch)),
                    "label": int(i),
                    "centroid": (float(centroids[i][0]), float(centroids[i][1])),
                    "area": float(area),
                    "fused_labels": [int(i)]
                })
                
        if not raw_islands:
            return []

        # 2. Transitive Spatial Proximity & Containment Fusion (Union-Find)
        # Prevents dropped child components when fusions are multi-level (A -> B -> C),
        # guaranteeing 100% complete ink coverage with zero missing facial features or word fragments.
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
            
            # Skip large standalone objects
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
                    
                # Check spatial containment or immediate proximity (e.g. face details / dots)
                margin_x = 18.0
                margin_y = 24.0
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
            all_labels = [it["label"] for it in group]
            
            all_x = [stats[lbl][0] for lbl in all_labels]
            all_y = [stats[lbl][1] for lbl in all_labels]
            all_x2 = [stats[lbl][0] + stats[lbl][2] for lbl in all_labels]
            all_y2 = [stats[lbl][1] + stats[lbl][3] for lbl in all_labels]
            bx, by = min(all_x), min(all_y)
            bw = max(all_x2) - bx
            bh = max(all_y2) - by
            
            merged_islands.append({
                "rect": (int(bx), int(by), int(bw), int(bh)),
                "label": int(rep["label"]),
                "centroid": (float(rep["centroid"][0]), float(rep["centroid"][1])),
                "area": float(sum(it["area"] for it in group)),
                "fused_labels": all_labels
            })

        # 3. Sort islands naturally into reading lines (RTL / LTR)
        islands = BaseDrawingAlgorithm.cluster_islands_into_lines(
            merged_islands, rtl=rtl, sort_mode="right_to_left" if rtl else "left_to_right"
        )
            
        grid_size = 15
        band_height = 100
        segments = []
        
        # 4. Generate smooth organic scribble path for each island
        for island in islands:
            target_labels = island.get("fused_labels", [island["label"]])
            bx, by, bw, bh = island["rect"]
            
            sub_labels = labels[by:by+bh, bx:bx+bw]
            sub_mask = np.isin(sub_labels, target_labels)
            
            blocks = []
            for r_rel in range(0, bh, grid_size):
                for c_rel in range(0, bw, grid_size):
                    r_end = min(r_rel + grid_size, bh)
                    c_end = min(c_rel + grid_size, bw)
                    if np.any(sub_mask[r_rel:r_end, c_rel:c_end]):
                        blocks.append((bx + c_rel + grid_size // 2, by + r_rel + grid_size // 2))
                        
            if not blocks:
                continue
                
            if bh <= 160:
                # Small or medium island: single continuous organic TSP sweep
                if rtl and blocks:
                    start_idx = max(range(len(blocks)), key=lambda i: blocks[i][0] - blocks[i][1])
                else:
                    start_idx = min(range(len(blocks)), key=lambda i: blocks[i][0] + blocks[i][1])
                    
                path = [blocks.pop(start_idx)]
                while blocks:
                    curr = path[-1]
                    arr = np.array(blocks)
                    dists = (arr[:, 0] - curr[0])**2 + (arr[:, 1] - curr[1])**2
                    min_idx = np.argmin(dists)
                    path.append(blocks.pop(min_idx))
            else:
                # Tall macro-island: Banded vertical sweep
                # Ensures face and upper features are 100% completed before descending down
                bands = []
                y_start = by
                while y_start < by + bh:
                    y_end = y_start + band_height
                    band_blocks = [b for b in blocks if y_start <= b[1] < y_end]
                    if band_blocks:
                        bands.append(band_blocks)
                    y_start = y_end
                    
                path = []
                last_pt = None
                for band in bands:
                    if not band:
                        continue
                    if last_pt is None:
                        if rtl:
                            start_idx = max(range(len(band)), key=lambda i: band[i][0] - band[i][1])
                        else:
                            start_idx = min(range(len(band)), key=lambda i: band[i][0] + band[i][1])
                        curr = band.pop(start_idx)
                    else:
                        arr = np.array(band)
                        dists = (arr[:, 0] - last_pt[0])**2 + (arr[:, 1] - last_pt[1])**2
                        min_idx = np.argmin(dists)
                        curr = band.pop(min_idx)
                        
                    path.append(curr)
                    while band:
                        curr = path[-1]
                        arr = np.array(band)
                        dists = (arr[:, 0] - curr[0])**2 + (arr[:, 1] - curr[1])**2
                        min_idx = np.argmin(dists)
                        path.append(band.pop(min_idx))
                    last_pt = path[-1]
                    
            pts = [QPointF(float(p[0]), float(p[1])) for p in path]
            if len(pts) == 1:
                pts.append(QPointF(pts[0].x() + 1.0, pts[0].y()))
                
            length = self._calculate_length(pts)
            segments.append({
                "type": "stroke",
                "points": pts,
                "length": length,
                "width": grid_size * 2.2,
                "opacity": 1.0
            })
            
        # 5. Assign timestamps
        total_length = sum(seg["length"] for seg in segments) or 1.0
        accumulated_time = 0.0
        
        timed_segments = []
        for seg in segments:
            seg_share = seg["length"] / total_length
            seg_duration = duration * seg_share
            
            timed_segments.append({
                "type": seg["type"],
                "points": seg["points"],
                "duration": seg_duration,
                "start_time": accumulated_time,
                "end_time": accumulated_time + seg_duration,
                "width": seg["width"],
                "opacity": seg["opacity"]
            })
            accumulated_time += seg_duration
            
        _SOLID_CACHE[cache_key] = copy.deepcopy(timed_segments)
        return timed_segments

    def _calculate_length(self, points: List[QPointF]) -> float:
        import math
        length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x() - points[i-1].x()
            dy = points[i].y() - points[i-1].y()
            length += math.hypot(dx, dy)
        return length
