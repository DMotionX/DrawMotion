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
from .professional_generator import generate_clean_localized_fills

_PROFESSIONAL_CACHE = {}

class ProfessionalAlgorithm(BaseDrawingAlgorithm):
    """
    Professional Vector Drawing (CAD Structural Hierarchy & Whiteboard Flow):
    Strictly follows the human whiteboarding principle:
    «Draw one discrete visual piece, complete it 100% via 4-tier CAD structural assembly,
      then lift the hand in an in-air travel flight and enter the next piece».

    4-Tier CAD Structural Assembly (Executed Per-Piece):
      1. Tier 1: External Chassis & Primary Silhouette (Board outline, outer frames)
      2. Tier 2: Major Functional Units & IC Bodies (Chips, ports + localized solid pocket fills)
      3. Tier 3: Discrete Components & Pins (Headers, capacitors, resistors + small fills)
      4. Tier 4: Fine Details & Silkscreen (Copper traces, vias, text labels)

    Key Invariants:
      - Strictly Piece-by-Piece: Discrete semantic objects (e.g. Laptop, Arduino, LED)
        are never drawn concurrently; each piece reaches 100% completion before moving on.
      - Zero Retrace & Zero Blanket Sweeps: Localized fills only in unrevealed solid pockets.
      - Natural Hand Velocity & Exact Duration: Smooth progress from 0.0s to duration.
    """

    def generate_plan(self, qimage: QImage, duration: float, **kwargs) -> List[Dict[str, Any]]:
        rtl = kwargs.get("rtl", False)
        duration = max(0.5, float(duration or 8.0))
        cache_key = (id(qimage), rtl, duration)

        if cache_key in _PROFESSIONAL_CACHE:
            return copy.deepcopy(_PROFESSIONAL_CACHE[cache_key])

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

        # 1. Containment & Spatial Fusion (Union-Find)
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

        raw_piece_units = []
        # 3. For each piece: generate 4-tier CAD structural paths
        for island in islands:
            target_labels = island.get("fused_labels", [island["label"]])
            bx, by, bw, bh = island["rect"]
            sub_labels = labels[by:by+bh, bx:bx+bw]
            sub_mask = np.isin(sub_labels, target_labels).astype(np.uint8) * 255

            if cv2.countNonZero(sub_mask) == 0:
                continue

            contours, hierarchy = cv2.findContours(sub_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            t1_paths, t2_paths, t3_paths, t4_paths = [], [], [], []
            t1_cnts, t2_cnts, t3_cnts, t4_cnts = [], [], [], []

            if contours:
                for i, c in enumerate(contours):
                    arc = cv2.arcLength(c, True)
                    c_area = cv2.contourArea(c)
                    parent = hierarchy[0][i][3] if hierarchy is not None else -1

                    if arc >= 6:
                        epsilon = 0.002 * arc
                        approx = cv2.approxPolyDP(c, epsilon, True)
                        if len(approx) >= 3:
                            pts = [QPointF(float(pt[0][0] + bx) / scale, float(pt[0][1] + by) / scale) for pt in approx]
                            pts.append(pts[0])
                        else:
                            pts = [QPointF(float(pt[0][0] + bx) / scale, float(pt[0][1] + by) / scale) for pt in c]
                            if len(pts) >= 2:
                                pts.append(pts[0])
                    else:
                        cx = float(np.mean(c[:, 0, 0]))
                        cy = float(np.mean(c[:, 0, 1]))
                        p1 = QPointF(float(cx - 1.5 + bx) / scale, float(cy + by) / scale)
                        p2 = QPointF(float(cx + 1.5 + bx) / scale, float(cy + by) / scale)
                        pts = [p1, p2]

                    if not pts:
                        continue

                    # Tier Classification
                    if arc >= 140 or (parent == -1 and c_area >= 400):
                        t1_paths.append(pts)
                        t1_cnts.append(c)
                    elif arc >= 40 or c_area >= 60:
                        t2_paths.append(pts)
                        t2_cnts.append(c)
                    elif arc >= 16 or c_area >= 15:
                        t3_paths.append(pts)
                        t3_cnts.append(c)
                    else:
                        t4_paths.append(pts)
                        t4_cnts.append(c)

                # Ensure at least one primary contour in Tier 1 if available
                if not t1_paths and t2_paths:
                    t1_paths.append(t2_paths.pop(0))

            # Localized solid pocket fills within this piece
            canvas_sub = np.zeros(sub_mask.shape, dtype=np.uint8)
            all_cnts = t1_cnts + t2_cnts + t3_cnts + t4_cnts
            if all_cnts:
                cv2.drawContours(canvas_sub, all_cnts, -1, 255, 12)

            unrevealed = (sub_mask > 0) & (canvas_sub == 0)
            n_u, l_u, s_u, _ = cv2.connectedComponentsWithStats(unrevealed.astype(np.uint8) * 255)
            fill_step = max(6, int(12.0 * scale))
            for u in range(1, n_u):
                u_area = s_u[u, cv2.CC_STAT_AREA]
                if u_area < 25:
                    continue
                pocket = (l_u == u).astype(np.uint8) * 255
                pocket_fills = generate_clean_localized_fills(pocket, step=fill_step, map_scale=1.0, scale=scale)
                offset_fills = []
                for stroke in pocket_fills:
                    offset_fills.append([QPointF(p.x() + float(bx) / scale, p.y() + float(by) / scale) for p in stroke])
                if u_area >= 500:
                    t2_paths.extend(offset_fills)
                else:
                    t3_paths.extend(offset_fills)

            # Build ordered sub-strokes for this piece following 4-tier CAD order
            piece_sub_strokes = []
            tiers = [
                ("Tier 1: Chassis", t1_paths, 14.0),
                ("Tier 2: ICs & Pockets", t2_paths, 13.0),
                ("Tier 3: Pins & Elements", t3_paths, 10.0),
                ("Tier 4: Details & Traces", t4_paths, 8.0),
            ]

            for tier_name, tier_paths, stroke_w in tiers:
                if not tier_paths:
                    continue
                start_pt = piece_sub_strokes[-1]["points"][-1] if piece_sub_strokes else None
                ordered = self._sort_paths_continuous(tier_paths, rtl=rtl, start_near=start_pt)
                for pts in ordered:
                    if piece_sub_strokes:
                        last_p = piece_sub_strokes[-1]["points"][-1]
                        first_p = pts[0]
                        dist = math.hypot(first_p.x() - last_p.x(), first_p.y() - last_p.y())
                        if dist > 15.0:
                            piece_sub_strokes.append({
                                "type": "travel",
                                "points": [last_p, first_p]
                            })
                    piece_sub_strokes.append({
                        "type": "stroke",
                        "points": pts,
                        "width": stroke_w
                    })

            if piece_sub_strokes:
                raw_piece_units.append({
                    "island": island,
                    "sub_strokes": piece_sub_strokes
                })

        if not raw_piece_units:
            return []

        # 4. Assemble timed segments with in-air travels between distinct pieces
        total_stroke_len = sum(
            sum(self._calculate_length(s["points"]) for s in u["sub_strokes"] if s["type"] == "stroke")
            for u in raw_piece_units
        ) or 1.0

        timed_segments: List[Dict[str, Any]] = []
        cur_time = 0.0

        for u in raw_piece_units:
            sub_strokes = u["sub_strokes"]

            # In-air travel flight between distinct pieces
            if timed_segments:
                last_p = timed_segments[-1]["points"][-1]
                first_p = sub_strokes[0]["points"][0]
                dist = math.hypot(first_p.x() - last_p.x(), first_p.y() - last_p.y())
                if dist > 8.0:
                    flight_dur = min(0.20, max(0.04, dist / 2400.0))
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
                        "width": s.get("width", 14.0),
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

        _PROFESSIONAL_CACHE[cache_key] = copy.deepcopy(timed_segments)
        return timed_segments

    def _sort_paths_continuous(self, paths: List[List[QPointF]], rtl: bool = False, start_near: QPointF = None) -> List[List[QPointF]]:
        if len(paths) <= 1:
            return paths
        remaining = list(paths)
        if start_near is not None:
            best_init_idx = min(range(len(remaining)), key=lambda i: min(
                (p.x() - start_near.x())**2 + (p.y() - start_near.y())**2 for p in remaining[i]
            ))
        elif rtl:
            best_init_idx = max(range(len(remaining)), key=lambda i: max(p.x() for p in remaining[i]))
        else:
            best_init_idx = min(range(len(remaining)), key=lambda i: min(p.x() for p in remaining[i]))

        sorted_p = [remaining.pop(best_init_idx)]
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

    def _calculate_length(self, points: List[QPointF]) -> float:
        length = 0.0
        for i in range(1, len(points)):
            dx = points[i].x() - points[i-1].x()
            dy = points[i].y() - points[i-1].y()
            length += math.hypot(dx, dy)
        return length
