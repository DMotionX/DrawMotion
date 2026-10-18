import cv2
import numpy as np
import math
from PySide6.QtCore import QPointF
from typing import List, Dict, Any

def _generate_chisel_marker_fill(mask: np.ndarray, step: int = 14, map_scale: float = 1.0, scale: float = 1.0) -> List[List[QPointF]]:
    """
    Generates broad, solid whiteboard chisel-tip marker sweeps with smooth U-turns.
    Guarantees 100% solid ink reveal coverage for educational diagrams and text.
    """
    def map_pt(px, py):
        return (px / map_scale) / scale, (py / map_scale) / scale

    h, w = mask.shape
    y_indices, _ = np.where(mask > 0)
    if len(y_indices) == 0:
        return []

    y_min, y_max = int(np.min(y_indices)), int(np.max(y_indices))
    scan_lines = []
    y_targets = []
    cur_y = y_min + min(step // 2, max(0, (y_max - y_min) // 2))
    while cur_y <= y_max:
        y_targets.append(cur_y)
        cur_y += step
    if y_targets and (y_max - y_targets[-1]) >= max(2, step // 3):
        y_targets.append(y_max)
    if y_targets and (y_targets[0] - y_min) >= max(2, step // 3):
        y_targets.insert(0, y_min)

    for y in y_targets:
        row = mask[y, :]
        diff = np.diff(np.pad((row > 0).astype(np.int8), (1, 1), 'constant'))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0] - 1
        
        row_segs = []
        for st, en in zip(starts, ends):
            if en >= st:
                row_segs.append((int(st), int(max(st + 2, en)), y))
        if row_segs:
            scan_lines.append(row_segs)

    if not scan_lines:
        return []

    continuous_path = []
    going_right = True
    last_pt = None

    for line_idx, row_segs in enumerate(scan_lines):
        sorted_segs = sorted(row_segs, key=lambda s: s[0])
        if not going_right:
            sorted_segs.reverse()

        for seg_idx, (st, en, cur_y) in enumerate(sorted_segs):
            if going_right:
                p_start = (st, cur_y)
                p_end = (en, cur_y)
            else:
                p_start = (en, cur_y)
                p_end = (st, cur_y)

            # Smooth whiteboard wrist U-turn between adjacent marker passes
            if last_pt is not None:
                y_mid = (last_pt[1] + p_start[1]) / 2.0
                turn_rad = min(6.0, abs(p_start[1] - last_pt[1]) * 0.5)
                if not going_right:
                    x_arc = max(last_pt[0], p_start[0]) + turn_rad
                else:
                    x_arc = min(last_pt[0], p_start[0]) - turn_rad
                continuous_path.append(QPointF(*map_pt(x_arc, y_mid)))

            continuous_path.append(QPointF(*map_pt(p_start[0], p_start[1])))
            continuous_path.append(QPointF(*map_pt(p_end[0], p_end[1])))
            last_pt = p_end

        going_right = not going_right

    if len(continuous_path) >= 2:
        return [continuous_path]
    return []

def generate_smart_educational_paths(mask: np.ndarray, scale: float) -> List[Dict[str, Any]]:
    """
    Smart Educational (Solid Chisel-Tip Whiteboard Educator Flow):
    - 1. Crisp technical contours defining diagrams, headers, and illustrations.
    - 2. Solid, broad chisel-tip marker sweeps with 100% solid reveal coverage.
    - 3. Completely replaces thin, flimsy skeleton wireframes with convincing whiteboard marker ink.
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
    erode_step = max(3, int(5.0 * map_scale))
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (erode_step, erode_step))
    fill_scan_step = max(6, int(14.0 * map_scale))
    
    for label_idx in range(1, num_labels):
        x, y, cw, ch, area = stats[label_idx]
        cx, cy = centroids[label_idx]
        
        if area < 16:
            half_w = max(2.0, cw / 2.0)
            p1 = QPointF(*map_to_original(max(0, cx - half_w), cy))
            p2 = QPointF(*map_to_original(min(work_mask.shape[1] - 1, cx + half_w), cy))
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
        
        # 1. Crisp technical contours (Both outer boundaries and inner loops/holes)
        contours, hierarchy = cv2.findContours(comp_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            arc_len = cv2.arcLength(cnt, True)
            if arc_len >= 8:
                epsilon = 0.0025 * arc_len
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
                
        # 2. Solid chisel-tip marker sweeps for medium & solid areas
        inner_mask = cv2.erode(comp_mask, erode_kernel, iterations=1)
        if cv2.countNonZero(inner_mask) > 0:
            n_inner, l_inner, s_inner, c_inner = cv2.connectedComponentsWithStats(inner_mask, connectivity=8)
            for inner_lbl in range(1, n_inner):
                sub_mask = (l_inner == inner_lbl).astype(np.uint8) * 255
                sweep_paths = _generate_chisel_marker_fill(sub_mask, step=fill_scan_step, map_scale=map_scale, scale=scale)
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
