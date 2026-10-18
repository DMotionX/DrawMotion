import cv2
import numpy as np
from PySide6.QtCore import QPointF
from typing import List, Dict, Any

try:
    import cv2.ximgproc
    HAS_XIMGPROC = True
except (ImportError, AttributeError):
    HAS_XIMGPROC = False

def generate_line_art_paths(ink_mask: np.ndarray, gray: np.ndarray, scale: float) -> List[Dict[str, Any]]:
    """
    Coloring Book Line Art Generator:
    - 1. Extracts crisp Canny edges and boundary contours for the black inking pen pass.
    - 2. Generates smooth interior cell-fill sweeps for solid bodies, eliminating white hollow spots.
    - 3. Strictly preserves authentic Coloring Book character (inking first, then color reveal).
    """
    h, w = ink_mask.shape
    max_dim = 1500.0
    map_scale = 1.0
    work_ink = ink_mask.copy()
    work_gray = gray.copy()
    
    if w > max_dim or h > max_dim:
        map_scale = min(max_dim / w, max_dim / h)
        work_w = int(w * map_scale)
        work_h = int(h * map_scale)
        work_ink = cv2.resize(ink_mask, (work_w, work_h), interpolation=cv2.INTER_NEAREST)
        work_gray = cv2.resize(gray, (work_w, work_h), interpolation=cv2.INTER_AREA)
        
    _, work_ink = cv2.threshold(work_ink, 127, 255, cv2.THRESH_BINARY)
    
    # 1. Canny edges on grayscale
    high_thresh, _ = cv2.threshold(work_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    low_thresh = 0.5 * high_thresh
    edges = cv2.Canny(work_gray, low_thresh, high_thresh)
    
    # Draw outer boundary onto edges to ensure complete outline
    contours, _ = cv2.findContours(work_ink, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(edges, contours, -1, 255, 1)
    edges = cv2.bitwise_and(edges, work_ink)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    edges = cv2.dilate(edges, kernel, iterations=1)
    
    def map_to_original(mx, my):
        return (mx / map_scale) / scale, (my / map_scale) / scale

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(work_ink, connectivity=8)
    islands = []
    
    for lbl in range(1, num_labels):
        x, y, cw, ch, area = stats[lbl]
        cx, cy = centroids[lbl]
        comp_mask = (labels == lbl).astype(np.uint8) * 255
        
        edge_paths = []
        fill_paths = []
        
        # 1. Component boundary contours (crisp inking pen pass)
        cnts, _ = cv2.findContours(comp_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in cnts:
            arc_len = cv2.arcLength(cnt, True)
            if arc_len >= 4:
                approx = cv2.approxPolyDP(cnt, 0.5, True)
                p = [QPointF(*map_to_original(pt[0][0], pt[0][1])) for pt in approx]
                if len(p) >= 2:
                    p.append(p[0])
                    edge_paths.append(p)
            else:
                p1 = QPointF(*map_to_original(cx - 1.5, cy))
                p2 = QPointF(*map_to_original(cx + 1.5, cy))
                edge_paths.append([p1, p2])
                
        # 2. Internal Canny edge lines (internal details & skeleton)
        comp_edges = cv2.bitwise_and(edges, comp_mask)
        edge_cnts, _ = cv2.findContours(comp_edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in edge_cnts:
            arc_len = cv2.arcLength(cnt, True)
            if arc_len >= 8:
                approx = cv2.approxPolyDP(cnt, 1.0, False)
                p = [QPointF(*map_to_original(pt[0][0], pt[0][1])) for pt in approx]
                if len(p) >= 2:
                    edge_paths.append(p)
                    
        # 3. Smooth interior cell-fill sweeps (for solid bodies)
        y_indices, _ = np.where(comp_mask > 0)
        if len(y_indices) > 0:
            y_min, y_max = int(np.min(y_indices)), int(np.max(y_indices))
            step = max(3, int(5.0 * map_scale))
            y_targets = list(range(y_min, y_max + 1, step))
            if y_targets and y_targets[-1] != y_max:
                y_targets.append(y_max)
            if y_targets and y_targets[0] != y_min:
                y_targets.insert(0, y_min)
                
            going_right = True
            for sy in y_targets:
                row = comp_mask[sy, :]
                diff = np.diff(np.pad((row > 0).astype(np.int8), (1, 1), 'constant'))
                starts = np.where(diff == 1)[0]
                ends = np.where(diff == -1)[0] - 1
                row_segs = []
                for s, e in zip(starts, ends):
                    if e >= s:
                        s_ext = max(0.0, float(s) - 1.5)
                        e_ext = min(float(work_ink.shape[1] - 1), float(e) + 1.5)
                        p1 = QPointF(*map_to_original(s_ext, sy))
                        p2 = QPointF(*map_to_original(e_ext, sy))
                        if p1 == p2:
                            p2 = QPointF(*map_to_original(min(work_ink.shape[1] - 1, s + 1), sy))
                        row_segs.append([p1, p2])
                if not going_right:
                    row_segs.reverse()
                    for seg in row_segs:
                        seg.reverse()
                for seg in row_segs:
                    fill_paths.append(seg)
                going_right = not going_right
                
        all_paths = edge_paths + fill_paths
        if not all_paths:
            p1 = QPointF(*map_to_original(cx - 1.5, cy))
            p2 = QPointF(*map_to_original(cx + 1.5, cy))
            all_paths = [[p1, p2]]
            
        islands.append({
            "edge_paths": edge_paths,
            "fill_paths": fill_paths,
            "paths": all_paths,
            "centroid": (x / scale + cw / (2.0 * scale), y / scale + ch / (2.0 * scale)),
            "rect": (x / scale, y / scale, cw / scale, ch / scale),
            "area": float(area)
        })
        
    return islands
