import cv2
import numpy as np
import math
from PySide6.QtCore import QPointF
from typing import List, Dict, Any

def generate_clean_diagonal_shades(pocket_mask: np.ndarray, step: int = 12, map_scale: float = 1.0, scale: float = 1.0) -> List[List[QPointF]]:
    """
    Generates authentic +45° diagonal pencil shading strokes strictly within the solid pocket mask.
    Each stroke is an independent segment to prevent dragging across empty canvas space.
    """
    def map_pt(px, py):
        return (px / map_scale) / scale, (py / map_scale) / scale

    h, w = pocket_mask.shape
    y_indices, x_indices = np.where(pocket_mask > 0)
    if len(y_indices) == 0:
        return []

    d_vals = y_indices.astype(np.int32) - x_indices.astype(np.int32)
    d_min = int(np.min(d_vals))
    d_max = int(np.max(d_vals))

    paths = []
    going_forward = True

    for d in range(d_min + max(2, step // 2), d_max + 1, step):
        x_start = max(0, -d)
        x_end = min(w - 1, h - 1 - d)
        if x_start > x_end:
            continue

        xs = np.arange(x_start, x_end + 1)
        ys = xs + d
        diag_pixels = pocket_mask[ys, xs] > 0

        diff = np.diff(np.pad(diag_pixels.astype(np.int8), (1, 1), 'constant'))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0] - 1

        segs = []
        for st_idx, en_idx in zip(starts, ends):
            if en_idx >= st_idx:
                p1 = (int(xs[st_idx]), int(ys[st_idx]))
                p2 = (int(xs[en_idx]), int(ys[en_idx]))
                if p1 == p2:
                    p2 = (min(w - 1, p1[0] + 1), min(h - 1, p1[1] + 1))
                segs.append((p1, p2))

        if not going_forward:
            segs.reverse()

        for (p_a, p_b) in segs:
            p_start = p_a if going_forward else p_b
            p_end = p_b if going_forward else p_a
            paths.append([QPointF(*map_pt(p_start[0], p_start[1])), QPointF(*map_pt(p_end[0], p_end[1]))])

        going_forward = not going_forward

    return paths

def generate_scribble_islands(mask: np.ndarray, scale: float = 1.0) -> List[Dict[str, Any]]:
    """
    Organic Sketch (Freehand Artist Simulation):
    - Phase 1: Gestural Perspective Rough-in (15% duration) -> dynamic guide curves.
    - Phase 2: Organic Freehand Contours (45% duration) -> expressive silhouettes & line-work.
    - Phase 3: Slanted 45° Pencil Shading (40% duration) -> localized cross-hatching on shadows.
    - Zero blanket sweeps over empty space.
    - Zero early completion, finishes smoothly at duration.
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

    y_indices, x_indices = np.where(work_mask > 0)
    if len(y_indices) == 0:
        return []
        
    x_min, x_max = float(np.min(x_indices)), float(np.max(x_indices))
    y_min, y_max = float(np.min(y_indices)), float(np.max(y_indices))
    cx, cy = (x_min + x_max) / 2.0, (y_min + y_max) / 2.0
    
    # 1. Phase 1: Gestural Perspective Rough-in Guide Curves
    gestural_paths = []
    # Primary perspective diagonal axis
    p1 = QPointF(*map_pt(x_min + 15.0, y_min + 15.0))
    mid1 = QPointF(*map_pt(cx - 10.0, cy + 10.0))
    p2 = QPointF(*map_pt(x_max - 15.0, y_max - 15.0))
    gestural_paths.append([p1, mid1, p2])
    
    # Counter perspective axis
    p3 = QPointF(*map_pt(x_max - 20.0, y_min + 20.0))
    mid2 = QPointF(*map_pt(cx + 10.0, cy - 10.0))
    p4 = QPointF(*map_pt(x_min + 20.0, y_max - 20.0))
    gestural_paths.append([p3, mid2, p4])
    
    # 2. Phase 2: Organic Freehand Contours
    contours, hierarchy = cv2.findContours(work_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    contour_paths = []
    contour_cnts = []
    
    if contours:
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
                icx = float(np.mean(c[:, 0, 0]))
                icy = float(np.mean(c[:, 0, 1]))
                pts = [QPointF(*map_pt(icx - 1.5, icy)), QPointF(*map_pt(icx + 1.5, icy))]
                
            if pts:
                contour_paths.append(pts)
                contour_cnts.append(c)
                
    # 3. Phase 3: Slanted 45° Pencil Cross-Hatching for Solid/Shadow Pockets
    canvas = np.zeros_like(work_mask)
    if contour_cnts:
        cv2.drawContours(canvas, contour_cnts, -1, 255, max(8, int(14 * map_scale)))
        
    unrevealed = (work_mask > 0) & (canvas == 0)
    n_u, l_u, s_u, _ = cv2.connectedComponentsWithStats(unrevealed.astype(np.uint8) * 255)
    
    hatch_step = max(8, int(12.0 * map_scale))
    hatch_paths = []
    for u in range(1, n_u):
        if s_u[u, cv2.CC_STAT_AREA] >= 25:
            pocket = (l_u == u).astype(np.uint8) * 255
            diag_shades = generate_clean_diagonal_shades(pocket, step=hatch_step, map_scale=map_scale, scale=scale)
            hatch_paths.extend(diag_shades)

    from ..base_algorithm import BaseDrawingAlgorithm
    filter_w = 14.0 * map_scale
    clean_contours = BaseDrawingAlgorithm.filter_non_overlapping_strokes(
        contour_paths, work_mask, stroke_width=filter_w, max_overlap_ratio=0.88
    ) if contour_paths else []
    
    clean_hatches = BaseDrawingAlgorithm.filter_non_overlapping_strokes(
        hatch_paths, work_mask, stroke_width=filter_w, max_overlap_ratio=0.88
    ) if hatch_paths else []

    islands = [
        {
            "name": "Phase 1: Gestural Rough-in",
            "paths": gestural_paths,
            "weight": 0.15,
            "stroke_width": 10.0,
            "phase": 1,
            "rect": (x_min / (map_scale * scale), y_min / (map_scale * scale), (x_max - x_min) / (map_scale * scale), (y_max - y_min) / (map_scale * scale)),
            "centroid": (cx / (map_scale * scale), cy / (map_scale * scale)),
            "area": float((x_max - x_min) * (y_max - y_min)),
            "is_dot": False
        },
        {
            "name": "Phase 2: Freehand Contours",
            "paths": clean_contours,
            "weight": 0.45,
            "stroke_width": 14.0,
            "phase": 2,
            "rect": (x_min / (map_scale * scale), y_min / (map_scale * scale), (x_max - x_min) / (map_scale * scale), (y_max - y_min) / (map_scale * scale)),
            "centroid": (cx / (map_scale * scale), cy / (map_scale * scale)),
            "area": float(len(clean_contours) * 100),
            "is_dot": False
        },
        {
            "name": "Phase 3: Slanted Pencil Shading",
            "paths": clean_hatches,
            "weight": 0.40,
            "stroke_width": 12.0,
            "phase": 3,
            "rect": (x_min / (map_scale * scale), y_min / (map_scale * scale), (x_max - x_min) / (map_scale * scale), (y_max - y_min) / (map_scale * scale)),
            "centroid": (cx / (map_scale * scale), cy / (map_scale * scale)),
            "area": float(len(clean_hatches) * 100),
            "is_dot": False
        }
    ]
    
    return [isl for isl in islands if isl["paths"]]
