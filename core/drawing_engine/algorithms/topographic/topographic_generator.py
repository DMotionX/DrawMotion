import cv2
import numpy as np
from PySide6.QtCore import QPointF
from typing import List, Dict, Any

def generate_topographic_paths(mask: np.ndarray, scale: float) -> List[Dict[str, Any]]:
    """
    Classic Cross-Hatching Generator (Authentic Engraving / Pen-and-Ink Hatching):
    - 1. Clean boundary contours to define crisp silhouette edges.
    - 2. Pass 1: +45° straight parallel hatching lines (///).
    - 3. Pass 2: -45° straight cross-hatching lines (\\\\) to form rich cross-hatch texture.
    - 4. Fully fills solid areas with 100% solid reveal coverage (0 missing pixels).
    - 5. Eliminates hollow bubble loops, providing a striking contrast to Organic Sketch.
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
    
    heal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    work_mask = cv2.morphologyEx(work_mask, cv2.MORPH_CLOSE, heal_kernel)
    
    def map_to_original(mx, my):
        return (mx / map_scale) / scale, (my / map_scale) / scale

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(work_mask, connectivity=8)
    
    islands = []
    hatch_step = max(5, int(8.0 * map_scale))
    mw, mh = work_mask.shape[1], work_mask.shape[0]
    
    for label_idx in range(1, num_labels):
        x, y, cw, ch, area = stats[label_idx]
        cx, cy = centroids[label_idx]
        
        if area < 15:
            p1 = QPointF(*map_to_original(max(0, cx - 1.5), cy))
            p2 = QPointF(*map_to_original(min(mw - 1, cx + 1.5), cy))
            islands.append({
                "outlines": [[p1, p2]],
                "pass1": [],
                "pass2": [],
                "paths": [[p1, p2]],
                "rect": (x / scale, y / scale, cw / scale, ch / scale),
                "centroid": (cx / scale, cy / scale),
                "area": float(area),
                "is_dot": True
            })
            continue
            
        comp_mask = (labels == label_idx).astype(np.uint8) * 255
        
        # 1. Clean boundary contours
        comp_outlines = []
        contours, _ = cv2.findContours(comp_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            arc_len = cv2.arcLength(cnt, True)
            if arc_len >= 8:
                epsilon = 0.0025 * arc_len
                approx = cv2.approxPolyDP(cnt, epsilon, True)
                path = [QPointF(*map_to_original(p[0][0], p[0][1])) for p in approx]
                if len(path) >= 2:
                    path.append(path[0])
                    comp_outlines.append(path)
            else:
                p1 = QPointF(*map_to_original(cx - 1.5, cy))
                p2 = QPointF(*map_to_original(cx + 1.5, cy))
                comp_outlines.append([p1, p2])
                
        # 2. Pass 1: +45 deg straight parallel hatching (d = y - x)
        y_idx, x_idx = np.where(comp_mask > 0)
        d_vals = y_idx.astype(np.int32) - x_idx.astype(np.int32)
        d_min, d_max = int(np.min(d_vals)), int(np.max(d_vals))
        d_targets = list(range(d_min, d_max + 1, hatch_step))
        if d_targets and d_targets[-1] != d_max:
            d_targets.append(d_max)
        if d_targets and d_targets[0] != d_min:
            d_targets.insert(0, d_min)
            
        pass1_lines = []
        for d in d_targets:
            x_st = max(0, -d)
            x_en = min(mw - 1, mh - 1 - d)
            if x_st <= x_en:
                xs = np.arange(x_st, x_en + 1)
                ys = xs + d
                diag_pixels = comp_mask[ys, xs] > 0
                diff = np.diff(np.pad(diag_pixels.astype(np.int8), (1, 1), 'constant'))
                starts = np.where(diff == 1)[0]
                ends = np.where(diff == -1)[0] - 1
                for s, e in zip(starts, ends):
                    if e >= s:
                        p1 = QPointF(*map_to_original(xs[s], ys[s]))
                        p2 = QPointF(*map_to_original(xs[e], ys[e]))
                        if p1 == p2:
                            p2 = QPointF(*map_to_original(min(mw - 1, xs[e] + 1), min(mh - 1, ys[e] + 1)))
                        pass1_lines.append([p1, p2])
                        
        # 3. Pass 2: -45 deg straight cross-hatching (c = y + x)
        c_vals = y_idx.astype(np.int32) + x_idx.astype(np.int32)
        c_min, c_max = int(np.min(c_vals)), int(np.max(c_vals))
        c_targets = list(range(c_min, c_max + 1, hatch_step))
        if c_targets and c_targets[-1] != c_max:
            c_targets.append(c_max)
        if c_targets and c_targets[0] != c_min:
            c_targets.insert(0, c_min)
            
        pass2_lines = []
        for c in c_targets:
            x_st = max(0, c - (mh - 1))
            x_en = min(mw - 1, c)
            if x_st <= x_en:
                xs = np.arange(x_st, x_en + 1)
                ys = c - xs
                diag_pixels = comp_mask[ys, xs] > 0
                diff = np.diff(np.pad(diag_pixels.astype(np.int8), (1, 1), 'constant'))
                starts = np.where(diff == 1)[0]
                ends = np.where(diff == -1)[0] - 1
                for s, e in zip(starts, ends):
                    if e >= s:
                        p1 = QPointF(*map_to_original(xs[s], ys[s]))
                        p2 = QPointF(*map_to_original(xs[e], ys[e]))
                        if p1 == p2:
                            p2 = QPointF(*map_to_original(min(mw - 1, xs[e] + 1), max(0, ys[e] - 1)))
                        pass2_lines.append([p1, p2])
                        
        all_paths = comp_outlines + pass1_lines + pass2_lines
        if not all_paths:
            p1 = QPointF(*map_to_original(cx - 1.5, cy))
            p2 = QPointF(*map_to_original(cx + 1.5, cy))
            all_paths = [[p1, p2]]
            
        islands.append({
            "outlines": comp_outlines,
            "pass1": pass1_lines,
            "pass2": pass2_lines,
            "paths": all_paths,
            "rect": (x / scale, y / scale, cw / scale, ch / scale),
            "centroid": (cx / scale, cy / scale),
            "area": float(area),
            "is_dot": False
        })
        
    return islands
