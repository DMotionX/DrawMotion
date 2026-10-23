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

def generate_smart_educational_paths(mask: np.ndarray, scale: float = 1.0) -> List[Dict[str, Any]]:
    """
    Smart Educational Flow (Pedagogical Concept Zoning):
    - Divides visual space into 3 Pedagogical Concept Zones (Top, Center, Bottom).
    - Teaches and draws each zone completely (outlines + bold chisel-tip marker fills)
      before lifting the pen in a deliberate in-air travel flight to the next concept zone.
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
    y_min, y_max = int(np.min(y_indices)), int(np.max(y_indices))
    total_h = max(1, y_max - y_min)
    
    z1_y = y_min + int(0.35 * total_h)
    z2_y = y_min + int(0.70 * total_h)
    
    zone_defs = [
        ("Zone 1: Header & Power Unit", y_min, z1_y, 0.30, 16.0),
        ("Zone 2: Core Processing & Logic", z1_y, z2_y, 0.45, 16.0),
        ("Zone 3: Interface & Peripheral Ports", z2_y, y_max + 1, 0.25, 14.0)
    ]
    
    from ..base_algorithm import BaseDrawingAlgorithm
    filter_w = 14.0 * map_scale
    fill_step = max(8, int(14.0 * map_scale))
    
    islands = []
    
    for z_idx, (z_name, z_start_y, z_end_y, z_weight, stroke_w) in enumerate(zone_defs):
        z_mask = np.zeros_like(work_mask)
        z_mask[z_start_y:z_end_y, :] = work_mask[z_start_y:z_end_y, :]
        if cv2.countNonZero(z_mask) == 0:
            continue
            
        contours, hierarchy = cv2.findContours(z_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        z_paths = []
        z_cnts = []
        
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
                z_paths.append(pts)
                z_cnts.append(c)
                
        # Localized solid pocket fills within this concept zone
        canvas_z = np.zeros_like(z_mask)
        if z_cnts:
            cv2.drawContours(canvas_z, z_cnts, -1, 255, max(8, int(14 * map_scale)))
            
        unrev_z = (z_mask > 0) & (canvas_z == 0)
        n_u, l_u, s_u, _ = cv2.connectedComponentsWithStats(unrev_z.astype(np.uint8) * 255)
        for u in range(1, n_u):
            if s_u[u, cv2.CC_STAT_AREA] >= 25:
                pocket = (l_u == u).astype(np.uint8) * 255
                pocket_fills = generate_clean_chisel_fills(pocket, step=fill_step, map_scale=map_scale, scale=scale)
                z_paths.extend(pocket_fills)
                
        clean_paths = BaseDrawingAlgorithm.filter_non_overlapping_strokes(
            z_paths, z_mask, stroke_width=filter_w, max_overlap_ratio=0.88
        ) if z_paths else []
        
        if clean_paths:
            islands.append({
                "name": z_name,
                "paths": clean_paths,
                "weight": z_weight,
                "stroke_width": stroke_w,
                "zone": z_idx + 1,
                "rect": (0, z_start_y / (map_scale * scale), w / scale, (z_end_y - z_start_y) / (map_scale * scale)),
                "centroid": (w / (2 * scale), (z_start_y + z_end_y) / (2 * map_scale * scale)),
                "area": float(len(clean_paths) * 100),
                "is_dot": False
            })
            
    return islands
