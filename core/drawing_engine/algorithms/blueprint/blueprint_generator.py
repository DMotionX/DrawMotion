import cv2
import numpy as np
from PySide6.QtCore import QPointF
from typing import List, Dict, Any

def generate_blueprint_paths(ink_mask: np.ndarray, gray: np.ndarray, scale: float) -> Dict[str, Any]:
    """
    Blueprint Drafting Generator:
    - Phase 1: Architectural construction datum lines & corner drafting crosshairs.
    - Phase 2: Outer structural chassis & major framing contours.
    - Phase 3: Medium functional component boundaries.
    - Phase 4: Precision interior details, pins, and silkscreen labels.
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

    # 1. Technical Construction Guidelines
    y_idxs, x_idxs = np.where(work_ink > 0)
    guide_paths = []
    if len(y_idxs) > 0 and len(x_idxs) > 0:
        bx1, bx2 = int(np.min(x_idxs)), int(np.max(x_idxs))
        by1, by2 = int(np.min(y_idxs)), int(np.max(y_idxs))
        bw, bh = bx2 - bx1, by2 - by1
        cx, cy = (bx1 + bx2) / 2.0, (by1 + by2) / 2.0
        cross_len = max(15.0, min(bw, bh) * 0.08)
        
        # 4 Corner drafting crosshairs
        corners = [(bx1, by1), (bx2, by1), (bx1, by2), (bx2, by2)]
        for cx_c, cy_c in corners:
            guide_paths.append([
                QPointF(*map_to_original(cx_c - cross_len, cy_c)),
                QPointF(*map_to_original(cx_c + cross_len, cy_c))
            ])
            guide_paths.append([
                QPointF(*map_to_original(cx_c, cy_c - cross_len)),
                QPointF(*map_to_original(cx_c, cy_c + cross_len))
            ])
            
        # Center datum axis lines
        guide_paths.append([
            QPointF(*map_to_original(bx1 - cross_len, cy)),
            QPointF(*map_to_original(bx2 + cross_len, cy))
        ])
        guide_paths.append([
            QPointF(*map_to_original(cx, by1 - cross_len)),
            QPointF(*map_to_original(cx, by2 + cross_len))
        ])

    # 2. Multi-tier structural decomposition
    chassis_paths = []
    component_paths = []
    fine_cnt_paths = []
    
    contours, hierarchy = cv2.findContours(work_ink, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        arc = cv2.arcLength(cnt, True)
        if arc < 6.0:
            continue
        approx = cv2.approxPolyDP(cnt, 0.7, True)
        pts = [QPointF(*map_to_original(pt[0][0], pt[0][1])) for pt in approx]
        if len(pts) >= 2:
            pts.append(pts[0])
            if arc >= 100.0:
                chassis_paths.append(pts)
            elif arc >= 25.0:
                component_paths.append(pts)
            else:
                fine_cnt_paths.append(pts)

    # 3. Precision Internal Details (Canny edge details)
    detail_paths = list(fine_cnt_paths)
    high_thresh, _ = cv2.threshold(work_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    edges = cv2.Canny(work_gray, 0.5 * high_thresh, high_thresh)
    edges = cv2.bitwise_and(edges, work_ink)
    
    edge_cnts, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in edge_cnts:
        arc = cv2.arcLength(cnt, False)
        if 8.0 <= arc <= 400.0:
            approx = cv2.approxPolyDP(cnt, 0.9, False)
            pts = [QPointF(*map_to_original(pt[0][0], pt[0][1])) for pt in approx]
            if len(pts) >= 2:
                detail_paths.append(pts)

    return {
        "guide_paths": guide_paths,
        "chassis_paths": chassis_paths,
        "component_paths": component_paths,
        "detail_paths": detail_paths
    }
