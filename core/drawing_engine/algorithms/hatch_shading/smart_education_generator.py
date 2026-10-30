# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
import cv2
import numpy as np
from PySide6.QtCore import QPointF
from typing import List, Dict, Any

def generate_clean_chisel_fills(pocket_mask: np.ndarray, step: int = 14, map_scale: float = 1.0, scale: float = 1.0) -> List[List[QPointF]]:
    """
    Generates bold chisel-tip marker hatch sweeps ONLY within the target pocket mask.
    Disconnected segments are strictly isolated as separate strokes.
    """
    def map_pt(px, py):
        return (px / map_scale) / scale, (py / map_scale) / scale

    y_indices, _ = np.where(pocket_mask > 0)
    if len(y_indices) == 0:
        return []

    y_min, y_max = int(np.min(y_indices)), int(np.max(y_indices))
    paths = []
    going_right = True

    for cur_y in range(y_min + max(2, step // 2), y_max + 1, step):
        row = pocket_mask[cur_y, :]
        diff = np.diff(np.pad((row > 0).astype(np.int8), (1, 1), 'constant'))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0] - 1

        segs = []
        for st, en in zip(starts, ends):
            if en >= st:
                segs.append((int(st), int(en)))

        if not going_right:
            segs.reverse()

        for st, en in segs:
            if going_right:
                p1 = QPointF(*map_pt(st, cur_y))
                p2 = QPointF(*map_pt(en, cur_y))
            else:
                p1 = QPointF(*map_pt(en, cur_y))
                p2 = QPointF(*map_pt(st, cur_y))
            paths.append([p1, p2])

        going_right = not going_right

    return paths

def generate_smart_educational_paths(mask: np.ndarray, scale: float = 1.0, rtl: bool = False) -> List[Dict[str, Any]]:
    """
    Smart Educational Flow (Semantic Component-First Whiteboard Flow):
    - Identifies discrete semantic modules (e.g. Arduino board, sensors, ICs, diagram boxes, characters)
      and isolates interconnecting wire/bus networks.
    - Eliminates arbitrary horizontal Y-band slicing.
    - Each module is drawn completely: Outer Frame -> Internal Features -> Solid Chisel Fills
      before lifting the pen in a deliberate in-air travel flight to the next module.
    - Interconnecting wires, arrows, and final annotations are drawn in the finale to link the modules.
    - Zero blanket sweeps across empty white space.
    - Zero pop-in, 100% steady progressive reveal.
    """
    h, w = mask.shape
    max_dim = 1500.0
    map_scale = 1.0
    work_mask = mask.copy()
    
    if w > max_dim or h > max_dim:
        map_scale = min(max_dim / w, max_dim / h)
        work_w = int(w * map_scale)
        work_h = int(h * map_scale)
        work_mask = cv2.resize(mask, (work_w, work_h), interpolation=cv2.INTER_NEAREST)
        
    _, work_mask = cv2.threshold(work_mask, 127, 255, cv2.THRESH_BINARY)
    heal_k = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    work_mask = cv2.morphologyEx(work_mask, cv2.MORPH_CLOSE, heal_k)
    
    def map_pt(px, py):
        return (px / map_scale) / scale, (py / map_scale) / scale

    y_indices, _ = np.where(work_mask > 0)
    if len(y_indices) == 0:
        return []

    from ..base_algorithm import BaseDrawingAlgorithm
    filter_w = 14.0 * map_scale
    fill_step = max(8, int(14.0 * map_scale))

    # 1. Separate Macro-Bodies from Thin Interconnecting Wires (e.g. 1-3px wires connecting modules)
    body_k = cv2.getStructuringElement(cv2.MORPH_RECT, (4, 4))
    opened_bodies = cv2.morphologyEx(work_mask, cv2.MORPH_OPEN, body_k)
    
    total_ink = cv2.countNonZero(work_mask)
    opened_ink = cv2.countNonZero(opened_bodies)
    
    # If opening destroyed almost everything (e.g. pure single-pixel line art), fallback to work_mask directly
    if opened_ink < total_ink * 0.15:
        working_bodies = work_mask
        wires_mask = np.zeros_like(work_mask)
    else:
        working_bodies = opened_bodies
        wires_mask = cv2.bitwise_and(work_mask, cv2.bitwise_not(opened_bodies))

    # 2. Connected Component Analysis on working_bodies
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(working_bodies, connectivity=8)
    
    raw_bodies = []
    for i in range(1, n_labels):
        bx, by, bw, bh, area = stats[i]
        if area >= 25:
            raw_bodies.append({
                "id": i,
                "rect": (bx, by, bw, bh),
                "area": area,
                "centroid": (float(centroids[i][0]), float(centroids[i][1])),
                "mask": (labels == i)
            })

    if not raw_bodies:
        raw_bodies.append({
            "id": 1,
            "rect": (0, 0, work_mask.shape[1], work_mask.shape[0]),
            "area": total_ink,
            "centroid": (work_mask.shape[1] / 2.0, work_mask.shape[0] / 2.0),
            "mask": (work_mask > 0)
        })

    # 3. Spatial Proximity & Containment Fusion (Union-Find)
    # Merges chips, pins, inner features, and closely clustered sub-elements into semantic modules
    n = len(raw_bodies)
    parent = list(range(n))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        bi = raw_bodies[i]["rect"]
        for j in range(i + 1, n):
            bj = raw_bodies[j]["rect"]
            # Two bodies belong to same module if their bounding boxes are within 18px of each other
            margin = 18
            ov_x = max(0, min(bi[0] + bi[2] + margin, bj[0] + bj[2] + margin) - max(bi[0] - margin, bj[0] - margin))
            ov_y = max(0, min(bi[1] + bi[3] + margin, bj[1] + bj[3] + margin) - max(bi[1] - margin, bj[1] - margin))
            if ov_x > 0 and ov_y > 0:
                union(i, j)

    groups = {}
    for i in range(n):
        r = find(i)
        if r not in groups:
            groups[r] = []
        groups[r].append(raw_bodies[i])

    # 4. Build Modules and Extract Hierarchical Strokes
    modules = []
    
    for mod_idx, (r, body_list) in enumerate(groups.items()):
        mod_mask = np.zeros_like(work_mask)
        min_x = min(b["rect"][0] for b in body_list)
        min_y = min(b["rect"][1] for b in body_list)
        max_x = max(b["rect"][0] + b["rect"][2] for b in body_list)
        max_y = max(b["rect"][1] + b["rect"][3] for b in body_list)
        
        # Include original ink pixels in the module bounding box (captures inner text/labels)
        pad = 4
        px1, py1 = max(0, min_x - pad), max(0, min_y - pad)
        px2, py2 = min(work_mask.shape[1], max_x + pad), min(work_mask.shape[0], max_y + pad)
        
        for b in body_list:
            mod_mask[b["mask"]] = 255
        mod_mask[py1:py2, px1:px2] = cv2.bitwise_or(mod_mask[py1:py2, px1:px2], work_mask[py1:py2, px1:px2])
        
        # Prevent stealing pixels from disjoint modules
        for other_r, other_bodies in groups.items():
            if other_r != r:
                for ob in other_bodies:
                    ox, oy, ow, oh = ob["rect"]
                    if ox > max_x + 12 or ox + ow < min_x - 12 or oy > max_y + 12 or oy + oh < min_y - 12:
                        mod_mask[ob["mask"]] = 0

        # Hierarchical Path Generation for this Module:
        # Layer 1: Outlines (top-level contours)
        # Layer 2: Internal Details (nested contours)
        # Layer 3: Chisel Pocket Fills
        contours, hierarchy = cv2.findContours(mod_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        outer_paths = []
        inner_paths = []
        mod_cnts = []
        
        for i, c in enumerate(contours):
            arc = cv2.arcLength(c, True)
            if arc >= 6:
                approx = cv2.approxPolyDP(c, 0.002 * arc, True)
                if len(approx) >= 3:
                    pts = [QPointF(*map_pt(pt[0][0], pt[0][1])) for pt in approx]
                    pts.append(pts[0])
                else:
                    pts = [QPointF(*map_pt(pt[0][0], pt[0][1])) for pt in c]
                    if len(pts) >= 2:
                        pts.append(pts[0])
            else:
                cx = float(np.mean(c[:, 0, 0]))
                cy = float(np.mean(c[:, 0, 1]))
                pts = [QPointF(*map_pt(cx - 1.5, cy)), QPointF(*map_pt(cx + 1.5, cy))]
                
            if pts:
                is_outer = (hierarchy is not None and hierarchy[0][i][3] == -1)
                if is_outer:
                    outer_paths.append(pts)
                else:
                    inner_paths.append(pts)
                mod_cnts.append(c)

        # Chisel Pocket Fills
        fill_paths = []
        canvas_mod = np.zeros_like(mod_mask)
        if mod_cnts:
            cv2.drawContours(canvas_mod, mod_cnts, -1, 255, max(8, int(14 * map_scale)))
            
        unrev_mod = (mod_mask > 0) & (canvas_mod == 0)
        n_u, l_u, s_u, _ = cv2.connectedComponentsWithStats(unrev_mod.astype(np.uint8) * 255)
        for u in range(1, n_u):
            if s_u[u, cv2.CC_STAT_AREA] >= 25:
                pocket = (l_u == u).astype(np.uint8) * 255
                pocket_fills = generate_clean_chisel_fills(pocket, step=fill_step, map_scale=map_scale, scale=scale)
                fill_paths.extend(pocket_fills)

        # Combine hierarchically: Outlines -> Inner details -> Chisel fills
        all_mod_paths = outer_paths + inner_paths + fill_paths
        clean_paths = BaseDrawingAlgorithm.filter_non_overlapping_strokes(
            all_mod_paths, mod_mask, stroke_width=filter_w, max_overlap_ratio=0.88
        ) if all_mod_paths else []

        if clean_paths:
            total_mod_area = sum(b["area"] for b in body_list)
            modules.append({
                "name": f"Module {mod_idx + 1}",
                "paths": clean_paths,
                "stroke_width": 16.0,
                "rect": (min_x / (map_scale * scale), min_y / (map_scale * scale),
                         (max_x - min_x) / (map_scale * scale), (max_y - min_y) / (map_scale * scale)),
                "centroid": ((min_x + max_x) / (2 * map_scale * scale), (min_y + max_y) / (2 * map_scale * scale)),
                "area": float(total_mod_area),
                "is_wires": False
            })

    # 5. Extract Interconnecting Wires & Lines (Lines linking different modules)
    if cv2.countNonZero(wires_mask) > 40:
        wires_clean = wires_mask.copy()
        for m in modules:
            rx, ry, rw, rh = m["rect"]
            mx1, my1 = int(rx * map_scale * scale), int(ry * map_scale * scale)
            mx2, my2 = int((rx + rw) * map_scale * scale), int((ry + rh) * map_scale * scale)
            wires_clean[my1:my2, mx1:mx2] = 0

        if cv2.countNonZero(wires_clean) >= 30:
            wire_cnts, _ = cv2.findContours(wires_clean, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            wire_paths = []
            for c in wire_cnts:
                if cv2.arcLength(c, False) >= 8:
                    pts = [QPointF(*map_pt(pt[0][0], pt[0][1])) for pt in c]
                    wire_paths.append(pts)
            if wire_paths:
                modules.append({
                    "name": "Interconnecting Wires & Links",
                    "paths": wire_paths,
                    "stroke_width": 12.0,
                    "rect": (0, 0, w / scale, h / scale),
                    "centroid": (w / (2 * scale), h / (2 * scale)),
                    "area": float(cv2.countNonZero(wires_clean)),
                    "is_wires": True
                })

    # 6. Pedagogical Ordering of Modules:
    # Separate wire module (to always draw last) from main bodies
    main_modules = [m for m in modules if not m.get("is_wires", False)]
    wire_modules = [m for m in modules if m.get("is_wires", False)]

    # Sort main modules along reading flow (RTL / LTR)
    if rtl:
        main_modules.sort(key=lambda m: -m["rect"][0])
    else:
        main_modules.sort(key=lambda m: m["rect"][0])

    return main_modules + wire_modules
