import cv2
import numpy as np
from PySide6.QtCore import QPointF
from typing import List, Dict, Any

def generate_engraving_paths(ink_mask: np.ndarray, gray: np.ndarray, scale: float) -> Dict[str, Any]:
    """
    Classical Banknote / Woodcut Engraving Generator:
    - Phase 1: Crisp inking contours tracing outer and interior boundaries.
    - Phase 2: Tone-mapped 45-degree diagonal engraving hatching for midtones.
    - Phase 3: Intersecting 135-degree cross-hatching for deep shadow depth.
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

    # 1. Structural Outlines (Crisp Boundaries)
    outline_paths = []
    cnts, _ = cv2.findContours(work_ink, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in cnts:
        arc = cv2.arcLength(cnt, True)
        if arc >= 6.0:
            approx = cv2.approxPolyDP(cnt, 0.7, True)
            pts = [QPointF(*map_to_original(pt[0][0], pt[0][1])) for pt in approx]
            if len(pts) >= 2:
                pts.append(pts[0])
                outline_paths.append(pts)

    # Internal details (Canny)
    high_thresh, _ = cv2.threshold(work_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    edges = cv2.Canny(work_gray, 0.5 * high_thresh, high_thresh)
    edges = cv2.bitwise_and(edges, work_ink)
    edge_cnts, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in edge_cnts:
        arc = cv2.arcLength(cnt, False)
        if arc >= 8.0:
            approx = cv2.approxPolyDP(cnt, 0.8, False)
            pts = [QPointF(*map_to_original(pt[0][0], pt[0][1])) for pt in approx]
            if len(pts) >= 2:
                outline_paths.append(pts)

    # 2. Tone-Mapped Engraving Hatching (Cross-Hatch)
    # Highlights (> 220): left clean
    # Midtones (80 to 220): 45-degree diagonal lines
    # Deep shadows (< 80): 135-degree cross-hatching over the 45-degree lines
    hatch_paths = []
    step = 8 # Spacing between parallel hatch lines
    
    # Generate 45-degree parallel lines mask
    grid_45 = np.zeros_like(work_ink)
    diag_max = work_ink.shape[0] + work_ink.shape[1]
    for d in range(0, diag_max, step):
        pt1 = (max(0, d - work_ink.shape[0]), min(work_ink.shape[0] - 1, d))
        pt2 = (min(work_ink.shape[1] - 1, d), max(0, d - work_ink.shape[1]))
        cv2.line(grid_45, pt1, pt2, 255, 1)
        
    # Mask midtone + shadow lines strictly within ink mask
    tone_active = (work_gray < 220) & (work_ink > 0)
    lines_45 = cv2.bitwise_and(grid_45, tone_active.astype(np.uint8) * 255)
    
    lcnts_45, _ = cv2.findContours(lines_45, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in lcnts_45:
        arc = cv2.arcLength(cnt, False)
        if arc >= 4.0:
            approx = cv2.approxPolyDP(cnt, 0.6, False)
            pts = [QPointF(*map_to_original(pt[0][0], pt[0][1])) for pt in approx]
            if len(pts) >= 2:
                hatch_paths.append(pts)

    # Generate 135-degree cross-hatch lines only for deep shadows (< 90)
    shadow_active = (work_gray < 90) & (work_ink > 0)
    if np.any(shadow_active):
        grid_135 = np.zeros_like(work_ink)
        for d in range(-work_ink.shape[0], work_ink.shape[1], step):
            pt1 = (max(0, d), max(0, -d))
            pt2 = (min(work_ink.shape[1] - 1, d + work_ink.shape[0]), min(work_ink.shape[0] - 1, work_ink.shape[0] - 1))
            cv2.line(grid_135, pt1, pt2, 255, 1)
            
        lines_135 = cv2.bitwise_and(grid_135, shadow_active.astype(np.uint8) * 255)
        lcnts_135, _ = cv2.findContours(lines_135, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in lcnts_135:
            arc = cv2.arcLength(cnt, False)
            if arc >= 4.0:
                approx = cv2.approxPolyDP(cnt, 0.6, False)
                pts = [QPointF(*map_to_original(pt[0][0], pt[0][1])) for pt in approx]
                if len(pts) >= 2:
                    hatch_paths.append(pts)

    return {
        "outline_paths": outline_paths,
        "hatch_paths": hatch_paths
    }
