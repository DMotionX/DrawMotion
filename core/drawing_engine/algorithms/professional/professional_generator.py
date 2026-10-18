import cv2
import numpy as np
from PySide6.QtCore import QPointF
from typing import List, Dict, Any

def generate_serpentine_fill(mask: np.ndarray, step: int = 14, map_scale: float = 1.0, scale: float = 1.0) -> List[List[QPointF]]:
    """
    Generates a relaxed, fluid back-and-forth serpentine hatching sweep with rounded U-turns.
    Calibrated step (14px) calms hand speed while maintaining 100% solid coverage.
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

    # Connect scanlines in a continuous alternating zigzag sweep with rounded U-turns
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

            # Insert an organic rounded wrist arc for smooth U-turns instead of sharp 90-degree corners
            if last_pt is not None:
                y_mid = (last_pt[1] + p_start[1]) / 2.0
                turn_rad = min(6.0, abs(p_start[1] - last_pt[1]) * 0.5)
                if not going_right:
                    # Turning on the right edge
                    x_arc = max(last_pt[0], p_start[0]) + turn_rad
                else:
                    # Turning on the left edge
                    x_arc = min(last_pt[0], p_start[0]) - turn_rad
                
                continuous_path.append(QPointF(*map_pt(x_arc, y_mid)))

            continuous_path.append(QPointF(*map_pt(p_start[0], p_start[1])))
            continuous_path.append(QPointF(*map_pt(p_end[0], p_end[1])))
            last_pt = p_end

        going_right = not going_right

    if len(continuous_path) >= 2:
        return [continuous_path]
    return []

def generate_professional_paths(mask: np.ndarray, scale: float = 1.0) -> List[Dict[str, Any]]:
    """
    Professional Vector Drawing (Human Whiteboard Inker & Relaxed Highlighter Flow):
    - 1. Crisp vector inking of outer outlines and text strokes first.
    - 2. Relaxed serpentine sweeps for wide solid fills (zero concentric pinching blotches).
    - 3. 100% complete coverage: every pixel revealed organically during animation.
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
    heal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    work_mask = cv2.morphologyEx(work_mask, cv2.MORPH_CLOSE, heal_kernel)
    
    def map_pt(px, py):
        return (px / map_scale) / scale, (py / map_scale) / scale

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(work_mask, connectivity=8)
    
    islands = []
    # Erode step of 5px ensures medium and thick letters/shapes get solid serpentine fills
    erode_step = max(3, int(5.0 * map_scale))
    erode_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (erode_step, erode_step))
    # Fill scan step of 14px guarantees 6-10px solid overlap with 22-26px marker (calm hand speed)
    fill_scan_step = max(6, int(14.0 * map_scale))
    
    for label_idx in range(1, num_labels):
        x, y, cw, ch, area = stats[label_idx]
        cx, cy = centroids[label_idx]
        
        # Micro-accents or small dots: preserve as dedicated point dab with full width coverage
        if area < 16:
            half_w = max(2.0, cw / 2.0)
            p1 = QPointF(*map_pt(max(0, cx - half_w), cy))
            p2 = QPointF(*map_pt(min(work_mask.shape[1] - 1, cx + half_w), cy))
            islands.append({
                "paths": [[p1, p2]],
                "rect": (x / scale, y / scale, cw / scale, ch / scale),
                "centroid": (cx / scale, cy / scale),
                "area": float(area),
                "is_dot": True
            })
            continue
            
        island_mask = (labels == label_idx).astype(np.uint8) * 255
        
        # 1. Primary Contours (Outer outlines and internal hole borders like 'o', 'e', 'a')
        contours, hierarchy = cv2.findContours(island_mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        island_paths = []
        
        for contour in contours:
            arc_len = cv2.arcLength(contour, True)
            if arc_len >= 6:
                epsilon = 0.002 * arc_len
                approx = cv2.approxPolyDP(contour, epsilon, True)
                if len(approx) >= 3:
                    pts = [QPointF(*map_pt(pt[0][0], pt[0][1])) for pt in approx]
                    pts.append(pts[0])
                    island_paths.append(pts)
                else:
                    pts = [QPointF(*map_pt(pt[0][0], pt[0][1])) for pt in contour]
                    if len(pts) >= 2:
                        pts.append(pts[0])
                        island_paths.append(pts)
            else:
                p1 = QPointF(*map_pt(cx - 1.5, cy))
                p2 = QPointF(*map_pt(cx + 1.5, cy))
                island_paths.append([p1, p2])

        # 2. Interior Fill (Serpentine sweeping for solid areas + pocket dabs)
        inner_mask = cv2.erode(island_mask, erode_kernel, iterations=1)
        if cv2.countNonZero(inner_mask) > 0:
            n_inner, l_inner, s_inner, c_inner = cv2.connectedComponentsWithStats(inner_mask, connectivity=8)
            for inner_lbl in range(1, n_inner):
                sub_mask = (l_inner == inner_lbl).astype(np.uint8) * 255
                sweep_paths = generate_serpentine_fill(sub_mask, step=fill_scan_step, map_scale=map_scale, scale=scale)
                if sweep_paths:
                    island_paths.extend(sweep_paths)
                else:
                    # Small inner pocket: place a solid centerline dab to prevent hollow cores
                    icx, icy = c_inner[inner_lbl]
                    p1 = QPointF(*map_pt(max(0, icx - 2.5), icy))
                    p2 = QPointF(*map_pt(min(work_mask.shape[1] - 1, icx + 2.5), icy))
                    island_paths.append([p1, p2])
                
        if not island_paths:
            p1 = QPointF(*map_pt(cx - 1.5, cy))
            p2 = QPointF(*map_pt(cx + 1.5, cy))
            island_paths = [[p1, p2]]
            
        # Outlines first, followed by smooth relaxed serpentine fills
        islands.append({
            "paths": island_paths,
            "rect": (x / scale, y / scale, cw / scale, ch / scale),
            "centroid": (cx / scale, cy / scale),
            "area": float(area),
            "is_dot": False
        })
        
    return islands
