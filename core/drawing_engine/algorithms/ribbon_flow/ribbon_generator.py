import cv2
import numpy as np
from PySide6.QtCore import QPointF
from typing import List, Dict, Any
import math

def generate_ribbon_paths(ink_mask: np.ndarray, gray: np.ndarray, scale: float, rtl: bool = False) -> List[List[QPointF]]:
    """
    Continuous Single-Line Ribbon Flow Generator:
    - Extracts all structural outlines and interior detail paths.
    - Chains all elements into a single uninterrupted, flowing path with smooth connecting arcs.
    - Pen never leaves the paper — fluid, elegant, organic single-stroke drawing.
    """
    h, w = ink_mask.shape
    max_dim = 1000.0
    map_scale = 1.0
    work_ink = ink_mask.copy()
    work_gray = gray.copy()
    
    if w > max_dim or h > max_dim:
        map_scale = min(max_dim / w, max_dim / h)
        work_w = max(1, int(w * map_scale))
        work_h = max(1, int(h * map_scale))
        work_ink = cv2.resize(ink_mask, (work_w, work_h), interpolation=cv2.INTER_NEAREST)
        work_gray = cv2.resize(gray, (work_w, work_h), interpolation=cv2.INTER_AREA)
        
    _, work_ink = cv2.threshold(work_ink, 127, 255, cv2.THRESH_BINARY)
    
    def map_to_original(mx, my):
        return (mx / map_scale) / scale, (my / map_scale) / scale

    raw_strokes = []
    
    # 1. Contours
    cnts, _ = cv2.findContours(work_ink, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in cnts:
        arc = cv2.arcLength(cnt, True)
        if arc >= 5.0:
            approx = cv2.approxPolyDP(cnt, 0.8, True)
            pts = [QPointF(*map_to_original(pt[0][0], pt[0][1])) for pt in approx]
            if len(pts) >= 2:
                pts.append(pts[0])
                raw_strokes.append(pts)

    # 2. Canny edges
    high_thresh, _ = cv2.threshold(work_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    edges = cv2.Canny(work_gray, 0.5 * high_thresh, high_thresh)
    edges = cv2.bitwise_and(edges, work_ink)
    edge_cnts, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in edge_cnts:
        arc = cv2.arcLength(cnt, False)
        if arc >= 8.0:
            approx = cv2.approxPolyDP(cnt, 1.0, False)
            pts = [QPointF(*map_to_original(pt[0][0], pt[0][1])) for pt in approx]
            if len(pts) >= 2:
                raw_strokes.append(pts)

    if not raw_strokes:
        return []

    # Sort initial pool top-to-bottom (or RTL if requested)
    if rtl:
        raw_strokes.sort(key=lambda s: (min(p.y() for p in s), -max(p.x() for p in s)))
    else:
        raw_strokes.sort(key=lambda s: (min(p.y() for p in s), min(p.x() for p in s)))

    # Continuous Chaining: Stitch every stroke into one continuous flow
    remaining = list(raw_strokes)
    flowing_path = list(remaining.pop(0))
    
    while remaining:
        last_pt = flowing_path[-1]
        best_idx, best_dist, best_rev = 0, float('inf'), False
        limit = min(len(remaining), 35)
        for i in range(limit):
            st, en = remaining[i][0], remaining[i][-1]
            d_st = (st.x() - last_pt.x())**2 + (st.y() - last_pt.y())**2
            d_en = (en.x() - last_pt.x())**2 + (en.y() - last_pt.y())**2
            if d_st < best_dist: best_dist, best_idx, best_rev = d_st, i, False
            if d_en < best_dist: best_dist, best_idx, best_rev = d_en, i, True
            
        next_stroke = list(remaining.pop(best_idx))
        if best_rev:
            next_stroke.reverse()
            
        target_pt = next_stroke[0]
        gap_dist = math.hypot(target_pt.x() - last_pt.x(), target_pt.y() - last_pt.y())
        
        # If there is a gap, bridge it with an organic curved connector
        if gap_dist > 4.0:
            # Curved bridge to keep fluid ribbon appearance
            mid_x = (last_pt.x() + target_pt.x()) / 2.0
            mid_y = (last_pt.y() + target_pt.y()) / 2.0
            # Slight perpendicular offset for smooth ribbon curvature
            dx = target_pt.x() - last_pt.x()
            dy = target_pt.y() - last_pt.y()
            perp_x = -dy * 0.15
            perp_y = dx * 0.15
            ctrl_pt = QPointF(mid_x + perp_x, mid_y + perp_y)
            # Quadratic Bezier interpolation points
            bridge = []
            for t in [0.25, 0.5, 0.75]:
                bx = (1-t)**2 * last_pt.x() + 2*(1-t)*t * ctrl_pt.x() + t**2 * target_pt.x()
                by = (1-t)**2 * last_pt.y() + 2*(1-t)*t * ctrl_pt.y() + t**2 * target_pt.y()
                bridge.append(QPointF(bx, by))
            flowing_path.extend(bridge)
            
        flowing_path.extend(next_stroke)

    return [flowing_path]
