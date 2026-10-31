# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later

import cv2
import numpy as np
import math
import copy
from typing import List, Dict, Any
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QImage
from ..base_algorithm import BaseDrawingAlgorithm

_CLEAN_OUTLINE_CACHE = {}

class CleanOutlineAlgorithm(BaseDrawingAlgorithm):
    """
    Clean Outline Drawing Algorithm.
    Reveals crisp vector outline contours and concentric architectural fills strictly
    piece-by-piece: each discrete object (e.g. Laptop, Arduino, LED) is 100% completed 
    before the hand lifts in the air to draw the next piece.
    """

    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        duration = max(0.5, float(duration or 8.0))
        cache_key = (id(qimage), rtl, duration)

        if cache_key in _CLEAN_OUTLINE_CACHE:
            return copy.deepcopy(_CLEAN_OUTLINE_CACHE[cache_key])

        w_orig, h_orig = qimage.width(), qimage.height()
        if w_orig <= 0 or h_orig <= 0:
            return []

        # Safe pre-scale for very large images to prevent RAM pressure
        max_dim = 1600.0
        scale = 1.0
        if w_orig > max_dim or h_orig > max_dim:
            scale = max_dim / max(w_orig, h_orig)
            w_scaled = int(w_orig * scale)
            h_scaled = int(h_orig * scale)
            work_qimg = qimage.scaled(w_scaled, h_scaled, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            work_qimg = qimage

        mask = self._get_ink_mask(work_qimg)
        if cv2.countNonZero(mask) == 0:
            return []

        h, w = mask.shape
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

        # 1. Spatial Proximity & Containment Fusion (Union-Find)
        # Keeps large standalone objects (> 8000 scaled px) strictly isolated as separate pieces
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

            # Geometric containment: if child is strictly inside another island's bounding box,
            # it is part of that same piece (e.g. screen inside laptop, IC inside circuit board)
            contained_in = None
            min_enclosing_area = float('inf')
            for i, p_candidate in enumerate(raw_islands):
                if i == j:
                    continue
                p_x, p_y, p_w, p_h = p_candidate["rect"]
                p_area = p_candidate["area"]
                if (p_x - 8 <= c_x and p_y - 8 <= c_y and
                    c_x + c_w <= p_x + p_w + 8 and c_y + c_h <= p_y + p_h + 8):
                    if p_area < min_enclosing_area:
                        min_enclosing_area = p_area
                        contained_in = i

            if contained_in is not None:
                union_uf(j, contained_in)
                continue

            if c_area > 8000.0 * (scale ** 2):
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

        # 2. Sort islands naturally into visual reading lines (RTL / LTR)
        islands = BaseDrawingAlgorithm.cluster_islands_into_lines(
            merged_islands, rtl=rtl, sort_mode="right_to_left" if rtl else "left_to_right"
        )

        erosion_k = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        step_canvas = 3.0 / scale
        pen_width = max(20.0, step_canvas * 2.5)

        raw_units = []
        # 3. Process each island: generate clean outline & concentric contour paths
        for island in islands:
            target_labels = island.get("fused_labels", [island["label"]])
            bx, by, bw, bh = island["rect"]
            sub_labels = labels[by:by+bh, bx:bx+bw]
            sub_mask = np.isin(sub_labels, target_labels).astype(np.uint8) * 255

            fill_paths = []
            max_iter = 80
            while cv2.countNonZero(sub_mask) > 0 and max_iter > 0:
                max_iter -= 1
                contours, _ = cv2.findContours(sub_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                if not contours:
                    break

                for contour in contours:
                    if len(contour) < 3:
                        px = float(contour[0][0][0] + bx) / scale
                        py = float(contour[0][0][1] + by) / scale
                        fill_paths.append([QPointF(px, py), QPointF(px + 1.0, py)])
                        continue

                    epsilon = 0.003 * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    if len(approx) < 3:
                        approx = contour

                    ring_pts = [QPointF(float(pt[0][0] + bx) / scale, float(pt[0][1] + by) / scale) for pt in approx]
                    if ring_pts:
                        ring_pts.append(ring_pts[0])
                        fill_paths.append(ring_pts)

                prev_nz = cv2.countNonZero(sub_mask)
                sub_mask = cv2.erode(sub_mask, erosion_k, iterations=1)
                if cv2.countNonZero(sub_mask) == prev_nz:
                    M = cv2.moments(sub_mask)
                    if M["m00"] > 0:
                        cx_sub = float(M["m10"] / M["m00"] + bx) / scale
                        cy_sub = float(M["m01"] / M["m00"] + by) / scale
                        fill_paths.append([QPointF(cx_sub, cy_sub), QPointF(cx_sub + 1.0, cy_sub)])
                    break

            if not fill_paths:
                continue

            # Sort paths within this island: longest outline first, then nearest-neighbor inner rings
            path_data = [{"pts": p, "length": max(1.0, self._calculate_length(p))} for p in fill_paths]
            path_data.sort(key=lambda it: -it["length"])
            sorted_paths = [path_data.pop(0)]

            while path_data:
                last_pt = sorted_paths[-1]["pts"][-1]
                best_idx = 0
                best_dist = float("inf")
                best_needs_rev = False

                for idx, item in enumerate(path_data):
                    p_st = item["pts"][0]
                    p_en = item["pts"][-1]
                    d_st = (p_st.x() - last_pt.x())**2 + (p_st.y() - last_pt.y())**2
                    d_en = (p_en.x() - last_pt.x())**2 + (p_en.y() - last_pt.y())**2
                    if d_st < best_dist:
                        best_dist = d_st
                        best_idx = idx
                        best_needs_rev = False
                    if d_en < best_dist:
                        best_dist = d_en
                        best_idx = idx
                        best_needs_rev = True

                next_it = path_data.pop(best_idx)
                if best_needs_rev:
                    next_it["pts"].reverse()
                sorted_paths.append(next_it)

            # Sub-strokes with in-air travels inside this piece
            sub_strokes = []
            for item in sorted_paths:
                if sub_strokes:
                    last_p = sub_strokes[-1]["points"][-1]
                    first_p = item["pts"][0]
                    dist = math.hypot(first_p.x() - last_p.x(), first_p.y() - last_p.y())
                    if dist > 15.0:
                        sub_strokes.append({"type": "travel", "points": [last_p, first_p]})
                sub_strokes.append({"type": "stroke", "points": item["pts"]})

            raw_units.append({
                "island": island,
                "sub_strokes": sub_strokes
            })

        if not raw_units:
            return []

        # 4. Assemble timed segments with in-air travels between distinct pieces
        total_stroke_len = sum(
            sum(self._calculate_length(s["points"]) for s in u["sub_strokes"] if s["type"] == "stroke")
            for u in raw_units
        ) or 1.0

        timed_segments: List[Dict[str, Any]] = []
        cur_time = 0.0

        for u in raw_units:
            sub_strokes = u["sub_strokes"]

            # In-air travel flight between distinct pieces
            if timed_segments:
                last_p = timed_segments[-1]["points"][-1]
                first_p = sub_strokes[0]["points"][0]
                dist = math.hypot(first_p.x() - last_p.x(), first_p.y() - last_p.y())
                if dist > 8.0:
                    flight_dur = min(0.18, max(0.04, dist / 2400.0))
                    timed_segments.append({
                        "type": "travel",
                        "points": [last_p, first_p],
                        "duration": flight_dur,
                        "start_time": cur_time,
                        "end_time": cur_time + flight_dur,
                        "width": 0.0,
                        "opacity": 0.0
                    })
                    cur_time += flight_dur

            # Draw all strokes of this piece COMPLETELY before ever leaving it
            for s in sub_strokes:
                length = self._calculate_length(s["points"])
                if s["type"] == "travel":
                    dur = min(0.12, max(0.02, length / 2400.0))
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
                    seg_dur = duration * (length / total_stroke_len)
                    timed_segments.append({
                        "type": "stroke",
                        "points": s["points"],
                        "duration": seg_dur,
                        "start_time": cur_time,
                        "end_time": cur_time + seg_dur,
                        "width": pen_width,
                        "opacity": 1.0
                    })
                    cur_time += seg_dur

        # 5. Timeline normalization to match duration strictly
        if timed_segments and cur_time > 0:
            scale_t = duration / cur_time
            t = 0.0
            for s in timed_segments:
                s["duration"] *= scale_t
                s["start_time"] = t
                t += s["duration"]
                s["end_time"] = t

        _CLEAN_OUTLINE_CACHE[cache_key] = copy.deepcopy(timed_segments)
        return timed_segments

    def _calculate_length(self, points: List[QPointF]) -> float:
        length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x() - points[i-1].x()
            dy = points[i].y() - points[i-1].y()
            length += math.hypot(dx, dy)
        return length

