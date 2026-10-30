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
    Modern Component-First Solid Reveal Algorithm.
    Divides visual artwork into discrete semantic ink components and reveals each 
    component completely with human hand drawing mechanics:
      1. Structural Outer Silhouette & Inner Cutout Contours first (instant recognizability).
      2. Contour-Guided Inward Concentric Shading Rings (100% solid, rich coverage without
         machine-like horizontal slab scanning or vertical fax wipes).
      3. Clean in-air travel flights between strokes and between components.
      4. Fully synchronized timing matching the requested duration with RTL/LTR reading awareness.
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

        # Downscale for very large assets while preserving crisp geometry
        max_dim = 1600.0
        scale = 1.0
        work_mask = mask.copy()

        if w > max_dim or h > max_dim:
            scale = max_dim / max(w, h)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            work_mask = cv2.resize(mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST)

        _, work_mask = cv2.threshold(work_mask, 127, 255, cv2.THRESH_BINARY)
        heal_k = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        work_mask = cv2.morphologyEx(work_mask, cv2.MORPH_CLOSE, heal_k)

        def map_pt(px: float, py: float) -> QPointF:
            return QPointF(float(px / scale), float(py / scale))

        # 1. Connected components analysis
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(work_mask, connectivity=8)
        if num_labels <= 1:
            return []

        raw_islands = []
        for lbl in range(1, num_labels):
            x, y, cw, ch, area = stats[lbl]
            if area >= 10:
                raw_islands.append({
                    "label": int(lbl),
                    "rect": (int(x), int(y), int(cw), int(ch)),
                    "area": float(area),
                    "centroid": (float(centroids[lbl][0]), float(centroids[lbl][1]))
                })

        if not raw_islands:
            return []

        # 2. Transitive Proximity & Containment Fusion (Union-Find)
        # Prevents fragmentation of adjacent features, diacritics, and sub-elements
        n = len(raw_islands)
        parent = list(range(n))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def union(i: int, j: int):
            ri, rj = find(i), find(j)
            if ri != rj:
                parent[ri] = rj

        margin = 16
        for i in range(n):
            bi = raw_islands[i]["rect"]
            for j in range(i + 1, n):
                bj = raw_islands[j]["rect"]
                ov_x = max(0, min(bi[0] + bi[2] + margin, bj[0] + bj[2] + margin) - max(bi[0] - margin, bj[0] - margin))
                ov_y = max(0, min(bi[1] + bi[3] + margin, bj[1] + bj[3] + margin) - max(bi[1] - margin, bj[1] - margin))
                if ov_x > 0 and ov_y > 0:
                    union(i, j)

        groups: Dict[int, List[Dict[str, Any]]] = {}
        for i in range(n):
            r = find(i)
            if r not in groups:
                groups[r] = []
            groups[r].append(raw_islands[i])

        # 3. Generate Structural Contours + Concentric Infill per component
        components = []
        fill_step = 8
        brush_w = max(18.0, 22.0 / scale)
        erosion_k = cv2.getStructuringElement(cv2.MORPH_RECT, (fill_step, fill_step))

        for comp_idx, (r, body_list) in enumerate(groups.items()):
            min_x = min(b["rect"][0] for b in body_list)
            min_y = min(b["rect"][1] for b in body_list)
            max_x = max(b["rect"][0] + b["rect"][2] for b in body_list)
            max_y = max(b["rect"][1] + b["rect"][3] for b in body_list)

            comp_mask = np.zeros_like(work_mask)
            for b in body_list:
                comp_mask[labels == b["label"]] = 255

            # Extract contours: separate external boundaries and inner cutouts
            contours, hierarchy = cv2.findContours(comp_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

            ext_contours = []
            hole_contours = []
            if hierarchy is not None:
                for i, c in enumerate(contours):
                    is_hole = hierarchy[0][i][3] != -1
                    if is_hole:
                        hole_contours.append(c)
                    else:
                        ext_contours.append(c)
            else:
                ext_contours = list(contours)

            # Sort external boundaries by area descending for confident stroke placement
            ext_contours.sort(key=lambda c: cv2.contourArea(c), reverse=True)

            outline_paths = []
            for c in (ext_contours + hole_contours):
                arc = cv2.arcLength(c, True)
                if arc >= 6:
                    approx = cv2.approxPolyDP(c, 0.002 * arc, True)
                    if len(approx) >= 3:
                        pts = [map_pt(pt[0][0], pt[0][1]) for pt in approx]
                        pts.append(pts[0])
                    else:
                        pts = [map_pt(pt[0][0], pt[0][1]) for pt in c]
                        if len(pts) >= 2:
                            pts.append(pts[0])
                else:
                    cx_c = float(np.mean(c[:, 0, 0]))
                    cy_c = float(np.mean(c[:, 0, 1]))
                    pts = [map_pt(cx_c - 1.5, cy_c), map_pt(cx_c + 1.5, cy_c)]
                if pts:
                    outline_paths.append(pts)

            # Concentric Inward Infill: iterative erosion rings
            infill_paths = []
            sub_mask = cv2.erode(comp_mask, erosion_k, iterations=1)
            max_rings = 45

            while cv2.countNonZero(sub_mask) > 0 and max_rings > 0:
                max_rings -= 1
                ring_cnts, _ = cv2.findContours(sub_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                if not ring_cnts:
                    break

                for rc in ring_cnts:
                    rc_arc = cv2.arcLength(rc, True)
                    if rc_arc >= 6:
                        approx = cv2.approxPolyDP(rc, 0.003 * rc_arc, True)
                        if len(approx) >= 3:
                            r_pts = [map_pt(pt[0][0], pt[0][1]) for pt in approx]
                            r_pts.append(r_pts[0])
                        else:
                            r_pts = [map_pt(pt[0][0], pt[0][1]) for pt in rc]
                            if len(r_pts) >= 2:
                                r_pts.append(r_pts[0])
                    else:
                        rcx = float(np.mean(rc[:, 0, 0]))
                        rcy = float(np.mean(rc[:, 0, 1]))
                        r_pts = [map_pt(rcx - 1.0, rcy), map_pt(rcx + 1.0, rcy)]
                    if r_pts:
                        infill_paths.append(r_pts)

                prev_nz = cv2.countNonZero(sub_mask)
                sub_mask = cv2.erode(sub_mask, erosion_k, iterations=1)
                if cv2.countNonZero(sub_mask) == prev_nz:
                    # Centroid core cap
                    M = cv2.moments(sub_mask)
                    if M['m00'] > 0:
                        cx_core = float(M['m10'] / M['m00'])
                        cy_core = float(M['m01'] / M['m00'])
                        infill_paths.append([map_pt(cx_core - 1.0, cy_core), map_pt(cx_core + 1.0, cy_core)])
                    break

            all_comp_paths = outline_paths + infill_paths
            if all_comp_paths:
                total_area = sum(b["area"] for b in body_list)
                components.append({
                    "name": f"Component {comp_idx + 1}",
                    "paths": all_comp_paths,
                    "stroke_width": brush_w,
                    "rect": (min_x / scale, min_y / scale, (max_x - min_x) / scale, (max_y - min_y) / scale),
                    "centroid": ((min_x + max_x) / (2 * scale), (min_y + max_y) / (2 * scale)),
                    "area": float(total_area)
                })

        if not components:
            return []

        # 4. Sort components naturally along reading direction (RTL / LTR)
        row_band = 60.0
        if rtl:
            components.sort(key=lambda c: (round(c["rect"][1] / row_band), -c["rect"][0]))
        else:
            components.sort(key=lambda c: (round(c["rect"][1] / row_band), c["rect"][0]))

        # 5. Pack strokes, calculate lengths, and generate timed segments with in-air travels
        for comp in components:
            comp["total_length"] = sum(
                self._calculate_length(pts) for pts in comp["paths"] if pts
            ) or 1.0

        total_all_length = sum(comp["total_length"] for comp in components) or 1.0
        timed_segments: List[Dict[str, Any]] = []
        current_time = 0.0

        for comp in components:
            target_comp_duration = max(0.05, duration * (comp["total_length"] / total_all_length))
            paths = comp["paths"]

            comp_segments: List[Dict[str, Any]] = []
            comp_accum = 0.0
            stroke_w = comp["stroke_width"]

            path_data = []
            for pts in paths:
                if not pts:
                    continue
                uniform_pts = self._resample_path_uniform(pts, step_dist=8.0)
                length = self._calculate_length(uniform_pts)
                if length > 0:
                    path_data.append({"pts": uniform_pts, "length": max(2.0, length)})

            if not path_data:
                continue

            total_comp_len = sum(item["length"] for item in path_data) or 1.0

            for item in path_data:
                seg_dur = max(0.005, target_comp_duration * (item["length"] / total_comp_len))

                # In-air travel flight between disconnected strokes or components
                if comp_segments or timed_segments:
                    last_pt = comp_segments[-1]["points"][-1] if comp_segments else timed_segments[-1]["points"][-1]
                    st_pt = item["pts"][0]
                    dist = math.hypot(st_pt.x() - last_pt.x(), st_pt.y() - last_pt.y())
                    if dist > 8.0:
                        travel_dur = min(0.12, max(0.035, dist / 2200.0))
                        comp_segments.append({
                            "type": "travel",
                            "points": [last_pt, st_pt],
                            "duration": travel_dur,
                            "start_time": comp_accum,
                            "end_time": comp_accum + travel_dur,
                            "width": 0.0,
                            "opacity": 0.0
                        })
                        comp_accum += travel_dur

                comp_segments.append({
                    "type": "stroke",
                    "points": item["pts"],
                    "duration": seg_dur,
                    "start_time": comp_accum,
                    "end_time": comp_accum + seg_dur,
                    "width": stroke_w,
                    "opacity": 1.0
                })
                comp_accum += seg_dur

            if comp_segments and comp_accum > 0:
                scale_f = target_comp_duration / comp_accum
                for seg in comp_segments:
                    seg["duration"] *= scale_f
                    seg["start_time"] = current_time
                    current_time += seg["duration"]
                    seg["end_time"] = current_time
                    timed_segments.append(seg)

        # Final timeline synchronization to exactly match duration
        if timed_segments and current_time > 0:
            scale_time = duration / current_time
            cur_t = 0.0
            for seg in timed_segments:
                seg["duration"] *= scale_time
                seg["start_time"] = cur_t
                cur_t += seg["duration"]
                seg["end_time"] = cur_t

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

