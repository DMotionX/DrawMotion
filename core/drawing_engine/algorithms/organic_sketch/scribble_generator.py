import cv2
import numpy as np
import random
import math
from PySide6.QtCore import QPointF
from typing import List, Dict, Any

def _generate_organic_serpentine_fill(mask: np.ndarray, step: int = 12, map_scale: float = 1.0, scale: float = 1.0) -> List[List[QPointF]]:
    """
    Generates authentic +45° diagonal serpentine shading sweeps.
    Simulates a human artist sketching with a natural slanted wrist angle (charcoal / 6B pencil).
    Guarantees 100% solid reveal coverage with zero flimsy wireframes.
    """
    def map_pt(px, py):
        return (px / map_scale) / scale, (py / map_scale) / scale

    h, w = mask.shape
    y_indices, x_indices = np.where(mask > 0)
    if len(y_indices) == 0:
        return []

    # Calculate diagonal bounds (d = y - x)
    d_vals = y_indices.astype(np.int32) - x_indices.astype(np.int32)
    d_min = int(np.min(d_vals))
    d_max = int(np.max(d_vals))

    d_targets = []
    cur_d = d_min + min(step // 2, max(0, (d_max - d_min) // 2))
    while cur_d <= d_max:
        d_targets.append(cur_d)
        cur_d += step
    if d_targets and (d_max - d_targets[-1]) >= max(2, step // 3):
        d_targets.append(d_max)
    if d_targets and (d_targets[0] - d_min) >= max(2, step // 3):
        d_targets.insert(0, d_min)

    diagonal_strips = []
    for d in d_targets:
        # For line y = x + d:
        # 0 <= x < w and 0 <= x + d < h ==> max(0, -d) <= x <= min(w - 1, h - 1 - d)
        x_start = max(0, -d)
        x_end = min(w - 1, h - 1 - d)

        if x_start <= x_end:
            xs = np.arange(x_start, x_end + 1)
            ys = xs + d
            diag_pixels = mask[ys, xs] > 0

            diff = np.diff(np.pad(diag_pixels.astype(np.int8), (1, 1), 'constant'))
            starts = np.where(diff == 1)[0]
            ends = np.where(diff == -1)[0] - 1

            strip_segs = []
            for st_idx, en_idx in zip(starts, ends):
                if en_idx >= st_idx:
                    p1 = (int(xs[st_idx]), int(ys[st_idx]))
                    p2 = (int(xs[en_idx]), int(ys[en_idx]))
                    if p1 == p2:
                        p2 = (min(w - 1, p1[0] + 1), min(h - 1, p1[1] + 1))
                    strip_segs.append((p1, p2))
            if strip_segs:
                diagonal_strips.append(strip_segs)

    if not diagonal_strips:
        return []

    continuous_path = []
    going_forward = True
    last_pt = None

    for strip in diagonal_strips:
        sorted_segs = sorted(strip, key=lambda s: s[0][0])
        if not going_forward:
            sorted_segs.reverse()

        for (p_a, p_b) in sorted_segs:
            p_start = p_a if going_forward else p_b
            p_end = p_b if going_forward else p_a

            # Smooth organic wrist turn between diagonal strips
            if last_pt is not None:
                mid_x = (last_pt[0] + p_start[0]) / 2.0
                mid_y = (last_pt[1] + p_start[1]) / 2.0
                turn_offset = min(6.0, math.hypot(p_start[0] - last_pt[0], p_start[1] - last_pt[1]) * 0.4)
                if going_forward:
                    continuous_path.append(QPointF(*map_pt(mid_x - turn_offset, mid_y + turn_offset)))
                else:
                    continuous_path.append(QPointF(*map_pt(mid_x + turn_offset, mid_y - turn_offset)))

            continuous_path.append(QPointF(*map_pt(p_start[0], p_start[1])))
            continuous_path.append(QPointF(*map_pt(p_end[0], p_end[1])))
            last_pt = p_end

        going_forward = not going_forward

    if len(continuous_path) >= 2:
        return [continuous_path]
    return []

def generate_scribble_islands(mask: np.ndarray, scale: float) -> List[Dict[str, Any]]:
    """
    Organic Sketch (Solid Artistic Charcoal / Bold Pencil Flow):
    - 1. Bold expressive structural contours.
    - 2. Solid, broad serpentine shading sweeps with 100% solid reveal coverage.
    - 3. Completely eliminates weak, flimsy wireframe scratches.
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
    
    # Heal micro-breaks
    heal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    work_mask = cv2.morphologyEx(work_mask, cv2.MORPH_CLOSE, heal_kernel)
    
    def map_to_original(mx, my):
        return (mx / map_scale) / scale, (my / map_scale) / scale

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(work_mask, connectivity=8)
    
    islands = []
    erode_step = max(3, int(6.0 * map_scale))
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (erode_step, erode_step))
    fill_scan_step = max(5, int(12.0 * map_scale))
    
    for label_idx in range(1, num_labels):
        x, y, cw, ch, area = stats[label_idx]
        cx, cy = centroids[label_idx]
        
        if area < 15:
            p1 = QPointF(*map_to_original(max(0, cx - 1.5), cy))
            p2 = QPointF(*map_to_original(min(work_mask.shape[1] - 1, cx + 1.5), cy))
            islands.append({
                "paths": [[p1, p2]],
                "rect": (x / scale, y / scale, cw / scale, ch / scale),
                "centroid": (cx / scale, cy / scale),
                "area": float(area),
                "is_dot": True
            })
            continue
            
        comp_mask = (labels == label_idx).astype(np.uint8) * 255
        comp_paths = []
        
        # 1. Bold expressive contours (both outer boundaries and inner loops/holes)
        contours, hierarchy = cv2.findContours(comp_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            arc_len = cv2.arcLength(cnt, True)
            if arc_len >= 8:
                epsilon = 0.003 * arc_len
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                path = []
                for p in approx:
                    px, py = map_to_original(p[0][0], p[0][1])
                    path.append(QPointF(px, py))
                if len(path) >= 2:
                    path.append(path[0])
                    comp_paths.append(path)
            else:
                p1 = QPointF(*map_to_original(cx - 1.5, cy))
                p2 = QPointF(*map_to_original(cx + 1.5, cy))
                comp_paths.append([p1, p2])
                
        # 2. Solid, broad serpentine shading sweeps for medium & solid areas
        inner_mask = cv2.erode(comp_mask, erode_kernel, iterations=1)
        if cv2.countNonZero(inner_mask) > 0:
            n_inner, l_inner, s_inner, c_inner = cv2.connectedComponentsWithStats(inner_mask, connectivity=8)
            for inner_lbl in range(1, n_inner):
                sub_mask = (l_inner == inner_lbl).astype(np.uint8) * 255
                sweep_paths = _generate_organic_serpentine_fill(sub_mask, step=fill_scan_step, map_scale=map_scale, scale=scale)
                if sweep_paths:
                    comp_paths.extend(sweep_paths)
                else:
                    # Small inner pocket: place a solid centerline dab to prevent hollow cores
                    icx, icy = c_inner[inner_lbl]
                    p1 = QPointF(*map_to_original(max(0, icx - 2.5), icy))
                    p2 = QPointF(*map_to_original(min(work_mask.shape[1] - 1, icx + 2.5), icy))
                    comp_paths.append([p1, p2])
                
        if not comp_paths:
            p1 = QPointF(*map_to_original(cx - 1.5, cy))
            p2 = QPointF(*map_to_original(cx + 1.5, cy))
            comp_paths = [[p1, p2]]
            
        islands.append({
            "paths": comp_paths,
            "rect": (x / scale, y / scale, cw / scale, ch / scale),
            "centroid": (cx / scale, cy / scale),
            "area": float(area),
            "is_dot": False
        })
        
    return islands
