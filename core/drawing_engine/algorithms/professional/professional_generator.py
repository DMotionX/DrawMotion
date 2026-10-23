import cv2
import numpy as np
from PySide6.QtCore import QPointF
from typing import List, Dict, Any

def generate_clean_localized_fills(pocket_mask: np.ndarray, step: int = 14, map_scale: float = 1.0, scale: float = 1.0) -> List[List[QPointF]]:
    """
    Generates localized hatching strokes ONLY within the solid mask.
    Disconnected segments are returned as separate strokes, preventing the pen
    from ever dragging across empty space or unrelated components.
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

def generate_serpentine_fill(mask: np.ndarray, step: int = 14, map_scale: float = 1.0, scale: float = 1.0) -> List[List[QPointF]]:
    """
    Backward-compatible clean localized fill generator.
    """
    return generate_clean_localized_fills(mask, step=step, map_scale=map_scale, scale=scale)

def generate_professional_paths(mask: np.ndarray, scale: float = 1.0) -> List[Dict[str, Any]]:
    """
    Professional Vector Drawing (CAD Structural Hierarchy):
    - Tier 1: External Chassis & Primary Silhouettes (Board outline, outer frames).
    - Tier 2: Major Functional Units & IC Bodies (Chips, ports + localized solid fills).
    - Tier 3: Discrete Components & Pins (Headers, capacitors, resistors + fills).
    - Tier 4: Fine Details & Silkscreen (Copper traces, vias, text labels).
    - Zero blanket serpentine fills over white space.
    - Zero early completion: ink reveals steadily from 0.0s to 8.0s.
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
    
    # Morphological healing to connect small font antialiasing gaps
    heal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    work_mask = cv2.morphologyEx(work_mask, cv2.MORPH_CLOSE, heal_kernel)
    
    def map_pt(px, py):
        return (px / map_scale) / scale, (py / map_scale) / scale

    # 1. Structural multi-level contours
    contours, hierarchy = cv2.findContours(work_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
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
                    pts = [QPointF(*map_pt(pt[0][0], pt[0][1])) for pt in approx]
                    pts.append(pts[0])
                else:
                    pts = [QPointF(*map_pt(pt[0][0], pt[0][1])) for pt in c]
                    if len(pts) >= 2:
                        pts.append(pts[0])
            else:
                cx = float(np.mean(c[:, 0, 0]))
                cy = float(np.mean(c[:, 0, 1]))
                p1 = QPointF(*map_pt(cx - 1.5, cy))
                p2 = QPointF(*map_pt(cx + 1.5, cy))
                pts = [p1, p2]
                
            if not pts:
                continue
                
            if arc >= 160 or (parent == -1 and c_area >= 600):
                t1_paths.append(pts)
                t1_cnts.append(c)
            elif arc >= 45 or c_area >= 80:
                t2_paths.append(pts)
                t2_cnts.append(c)
            elif arc >= 18 or c_area >= 20:
                t3_paths.append(pts)
                t3_cnts.append(c)
            else:
                t4_paths.append(pts)
                t4_cnts.append(c)

    # 2. Localized solid pocket fills (strictly within unrevealed solid pockets)
    canvas = np.zeros(work_mask.shape, dtype=np.uint8)
    all_cnts = t1_cnts + t2_cnts + t3_cnts + t4_cnts
    if all_cnts:
        cv2.drawContours(canvas, all_cnts, -1, 255, max(8, int(14 * map_scale)))
    
    unrevealed = (work_mask > 0) & (canvas == 0)
    n_u, l_u, s_u, c_u = cv2.connectedComponentsWithStats(unrevealed.astype(np.uint8) * 255)
    
    fill_step = max(6, int(12.0 * map_scale))
    for u in range(1, n_u):
        u_area = s_u[u, cv2.CC_STAT_AREA]
        if u_area < 25:
            continue
        pocket = (l_u == u).astype(np.uint8) * 255
        pocket_fills = generate_clean_localized_fills(pocket, step=fill_step, map_scale=map_scale, scale=scale)
        if u_area >= 800:
            t2_paths.extend(pocket_fills)
        else:
            t3_paths.extend(pocket_fills)

    # 3. Non-overlapping Spatial Filter
    from ..base_algorithm import BaseDrawingAlgorithm
    filter_w = 14.0 * map_scale
    t1_clean = BaseDrawingAlgorithm.filter_non_overlapping_strokes(t1_paths, work_mask, stroke_width=filter_w, max_overlap_ratio=0.88) if t1_paths else []
    t2_clean = BaseDrawingAlgorithm.filter_non_overlapping_strokes(t2_paths, work_mask, stroke_width=filter_w, max_overlap_ratio=0.88) if t2_paths else []
    t3_clean = BaseDrawingAlgorithm.filter_non_overlapping_strokes(t3_paths, work_mask, stroke_width=filter_w, max_overlap_ratio=0.88) if t3_paths else []
    t4_clean = BaseDrawingAlgorithm.filter_non_overlapping_strokes(t4_paths, work_mask, stroke_width=filter_w, max_overlap_ratio=0.88) if t4_paths else []

    islands = []
    tiers = [
        ("Tier 1: Chassis & Silhouette", t1_clean, 0.25, 14.0, 1),
        ("Tier 2: Major ICs & Ports", t2_clean, 0.25, 14.0, 2),
        ("Tier 3: Pins & Components", t3_clean, 0.25, 10.0, 3),
        ("Tier 4: Traces & Silkscreen", t4_clean, 0.25, 8.0, 4)
    ]
    for name, paths, weight, stroke_w, tier_num in tiers:
        if paths:
            islands.append({
                "name": name,
                "paths": paths,
                "weight": weight,
                "stroke_width": stroke_w,
                "tier": tier_num,
                "rect": (0, 0, w / scale, h / scale),
                "centroid": (w / (2 * scale), h / (2 * scale)),
                "area": float(len(paths) * 100),
                "is_dot": False
            })

    return islands
