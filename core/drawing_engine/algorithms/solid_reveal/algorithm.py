# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later

import cv2
import numpy as np
import math
import copy
from typing import List, Dict, Any
from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
from ..base_algorithm import BaseDrawingAlgorithm

_SOLID_CACHE = {}

class SolidRevealAlgorithm(BaseDrawingAlgorithm):
    """
    Solid Reveal Drawing Algorithm.
    Strictly follows the human whiteboarding principle: 
    «Draw one discrete visual piece, complete it 100%, then lift the hand and enter the next piece».
    
    Key Mechanics:
      1. Island Isolation: Large standalone objects (e.g. Laptop, Arduino, LED) remain strictly
         independent islands; small features (dots, accents, keys) fuse into their parent island.
      2. Line & Direction Sorting: Islands are clustered into visual lines and sorted strictly
         according to reading direction (RTL / LTR).
      3. Organic Continuous Sweep: Each island is shaded completely in a smooth nearest-neighbor
         organic sweep with zero mechanical horizontal slab slicing (no fax/printer vertical scans).
      4. In-Air Travel Flights: Explicit in-air travel flights with width=0.0 and opacity=0.0
         are emitted when lifting the hand between distinct islands or distant sub-features.
      5. Calibrated Velocity: Smooth, calm, natural hand velocity across the full duration.
    """

    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        duration = max(0.5, float(duration or 8.0))
        cache_key = (id(qimage), rtl, duration)

        if cache_key in _SOLID_CACHE:
            return copy.deepcopy(_SOLID_CACHE[cache_key])

        w, h = qimage.width(), qimage.height()
        if w <= 0 or h <= 0:
            return []

        ptr = qimage.constBits()
        arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 4)).copy()

        # Quick validation: check alpha channel
        alpha = arr[:, :, 3]
        if not np.any(alpha > 10):
            return []

        mask = self._get_ink_mask(qimage)
        if cv2.countNonZero(mask) == 0:
            return []

        h, w = mask.shape

        # 1. Connect anti-aliased pixels to form solid islands
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(mask, kernel, iterations=1)

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilated, connectivity=8)
        if num_labels <= 1:
            return []

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

        # 2. Containment & Proximity Fusion (Union-Find)
        # Allows small inner features/dots to fuse with their parent, while large standalone
        # objects (> 8000px) remain STRICTLY isolated components so they are drawn one by one.
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

            # Large standalone objects are NEVER merged together into a mega-block
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

                # Check spatial containment or immediate proximity (e.g. face details / dots / keys)
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

        # 3. Sort islands naturally into visual reading lines (RTL / LTR)
        islands = BaseDrawingAlgorithm.cluster_islands_into_lines(
            merged_islands, rtl=rtl, sort_mode="right_to_left" if rtl else "left_to_right"
        )

        grid_size = 15
        brush_w = grid_size * 2.2
        raw_island_units = []

        # 4. Generate continuous organic scribble path for each island INDEPENDENTLY
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

            # Start point determined strictly by reading direction corner
            if rtl:
                start_idx = max(range(len(blocks)), key=lambda i: blocks[i][0] - blocks[i][1])
            else:
                start_idx = min(range(len(blocks)), key=lambda i: blocks[i][0] + blocks[i][1])

            # Continuous organic nearest-neighbor TSP path across the entire island
            # Eliminates 100px horizontal slab slicing (no vertical fax machine scans)
            path = [blocks.pop(start_idx)]
            while blocks:
                curr = path[-1]
                arr = np.array(blocks)
                dists = (arr[:, 0] - curr[0])**2 + (arr[:, 1] - curr[1])**2
                min_idx = np.argmin(dists)
                path.append(blocks.pop(min_idx))

            pts = [QPointF(float(p[0]), float(p[1])) for p in path]
            if len(pts) == 1:
                pts.append(QPointF(pts[0].x() + 1.0, pts[0].y()))

            # Check for sub-jumps within this island (e.g. disjoint features inside the fused island)
            sub_strokes = []
            cur_sub = [pts[0]]
            for i in range(1, len(pts)):
                d = math.hypot(pts[i].x() - pts[i-1].x(), pts[i].y() - pts[i-1].y())
                if d > 45.0:
                    if len(cur_sub) == 1:
                        cur_sub.append(QPointF(cur_sub[0].x() + 1.0, cur_sub[0].y()))
                    sub_strokes.append({"type": "stroke", "points": cur_sub})
                    sub_strokes.append({"type": "travel", "points": [cur_sub[-1], pts[i]]})
                    cur_sub = [pts[i]]
                else:
                    cur_sub.append(pts[i])

            if len(cur_sub) == 1:
                cur_sub.append(QPointF(cur_sub[0].x() + 1.0, cur_sub[0].y()))
            sub_strokes.append({"type": "stroke", "points": cur_sub})

            raw_island_units.append({
                "island": island,
                "sub_strokes": sub_strokes
            })

        if not raw_island_units:
            return []

        # 5. Calculate physical lengths and assemble sequential timed plan
        total_stroke_len = 0.0
        for unit in raw_island_units:
            for s in unit["sub_strokes"]:
                s["length"] = max(1.0, self._calculate_length(s["points"]))
                if s["type"] == "stroke":
                    total_stroke_len += s["length"]

        total_stroke_len = max(1.0, total_stroke_len)
        timed_segments: List[Dict[str, Any]] = []
        cur_time = 0.0

        for unit in raw_island_units:
            sub_strokes = unit["sub_strokes"]

            # In-air travel flight between distinct islands
            if timed_segments:
                last_pt = timed_segments[-1]["points"][-1]
                next_pt = sub_strokes[0]["points"][0]
                dist = math.hypot(next_pt.x() - last_pt.x(), next_pt.y() - last_pt.y())
                if dist > 8.0:
                    flight_dur = min(0.18, max(0.04, dist / 2400.0))
                    timed_segments.append({
                        "type": "travel",
                        "points": [last_pt, next_pt],
                        "duration": flight_dur,
                        "start_time": cur_time,
                        "end_time": cur_time + flight_dur,
                        "width": 0.0,
                        "opacity": 0.0
                    })
                    cur_time += flight_dur

            # Draw all strokes of this island COMPLETELY before ever leaving it
            for s in sub_strokes:
                if s["type"] == "travel":
                    p0, p1 = s["points"][0], s["points"][1]
                    dist = math.hypot(p1.x() - p0.x(), p1.y() - p0.y())
                    dur = min(0.12, max(0.03, dist / 2400.0))
                    timed_segments.append({
                        "type": "travel",
                        "points": s["points"],
                        "duration": dur,
                        "start_time": cur_time,
                        "end_time": cur_time + dur,
                        "width": 0.0,
                        "opacity": 0.0
                    })
                    cur_time += dur
                else:
                    seg_dur = duration * (s["length"] / total_stroke_len)
                    timed_segments.append({
                        "type": "stroke",
                        "points": s["points"],
                        "duration": seg_dur,
                        "start_time": cur_time,
                        "end_time": cur_time + seg_dur,
                        "width": brush_w,
                        "opacity": 1.0
                    })
                    cur_time += seg_dur

        # Final timeline synchronization to exactly match duration
        if timed_segments and cur_time > 0:
            scale_time = duration / cur_time
            t = 0.0
            for seg in timed_segments:
                seg["duration"] *= scale_time
                seg["start_time"] = t
                t += seg["duration"]
                seg["end_time"] = t

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

