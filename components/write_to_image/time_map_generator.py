import cv2
import numpy as np
from PySide6.QtGui import QImage

import math

def qimage_to_mask(qimage: QImage) -> np.ndarray:
    """
    Extracts the alpha channel from QImage and converts it to a 2D NumPy array.
    """
    alpha_img = qimage.convertToFormat(QImage.Format_Alpha8)
    ptr = alpha_img.constBits()
    # Convert pointer buffer to byte array
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((alpha_img.height(), alpha_img.bytesPerLine()))
    # Crop to actual image width (removing row stride padding if present)
    mask = arr[:, :alpha_img.width()].copy()
    return mask


def _topological_sort_seeds(seeds: list, is_rtl: bool) -> list:
    """
    Sorts a set of skeleton seeds using 8-connected graph traversal, momentum vector tracking,
    and vertical stem preservation. Eliminates disjoint temporal gaps (white holes) in cyclic characters (e.g. 'p', 'b', 'd', 'R').
    """
    if len(seeds) <= 2:
        return list(seeds)

    seed_set = set(seeds)
    neighbors = {p: [] for p in seeds}
    offsets = [(-1, -1), (0, -1), (1, -1),
               (-1,  0),          (1,  0),
               (-1,  1), (0,  1), (1,  1)]

    for x, y in seeds:
        for dx, dy in offsets:
            nbr = (x + dx, y + dy)
            if nbr in seed_set:
                neighbors[(x, y)].append(nbr)

    endpoints = [p for p in seeds if len(neighbors[p]) <= 1]
    unvisited = set(seeds)
    ordered = []

    def start_priority(p):
        x, y = p
        # For RTL (Arabic): top-right priority (smaller y, larger x)
        # For LTR (English): top-left priority (smaller y, smaller x)
        return (3.0 * y - x) if is_rtl else (3.0 * y + x)

    if endpoints:
        current = min(endpoints, key=start_priority)
    else:
        current = min(seeds, key=start_priority)

    # Momentum direction vector to smooth out 1-pixel raster zigzag noise
    dir_x, dir_y = (-1.0, 0.0) if is_rtl else (1.0, 0.0)
    has_momentum = False

    while unvisited:
        if current in unvisited:
            unvisited.remove(current)
            ordered.append(current)

        unvisited_nbrs = [n for n in neighbors[current] if n in unvisited]
        if unvisited_nbrs:
            best_nbr = None
            best_score = -999.0
            for nbr in unvisited_nbrs:
                ux = float(nbr[0] - current[0])
                uy = float(nbr[1] - current[1])
                u_mag = math.hypot(ux, uy)
                if u_mag > 1e-4:
                    ux /= u_mag
                    uy /= u_mag

                if has_momentum:
                    score = dir_x * ux + dir_y * uy
                else:
                    score = 0.0

                # Natural downward and reading-direction ergonomic handwriting bias
                score += 0.35 * uy
                if is_rtl:
                    score += -0.15 * ux
                else:
                    score += 0.15 * ux

                # If moving downwards in a vertical stroke/stem, heavily prioritize continuing downwards
                if has_momentum and dir_y > 0.4:
                    if uy > 0.4:
                        score += 0.5  # Crucial bonus to keep vertical stem contiguous and prevent cutting stems in half

                if score > best_score:
                    best_score = score
                    best_nbr = nbr

            # Update momentum with exponential moving average
            step_x = float(best_nbr[0] - current[0])
            step_y = float(best_nbr[1] - current[1])
            s_mag = math.hypot(step_x, step_y)
            if s_mag > 1e-4:
                step_x /= s_mag
                step_y /= s_mag
                if not has_momentum:
                    dir_x, dir_y = step_x, step_y
                    has_momentum = True
                else:
                    dir_x = 0.65 * dir_x + 0.35 * step_x
                    dir_y = 0.65 * dir_y + 0.35 * step_y
                    d_mag = math.hypot(dir_x, dir_y)
                    if d_mag > 1e-4:
                        dir_x /= d_mag
                        dir_y /= d_mag

            current = best_nbr
        else:
            if not unvisited:
                break
            # When stroke ends (e.g. reached descender endpoint), jump to next stroke start.
            curr_x, curr_y = current
            # Check nearby unvisited seeds within 3 pixels for small raster breaks
            nearby = [p for p in unvisited if max(abs(p[0] - curr_x), abs(p[1] - curr_y)) <= 3]
            if nearby:
                best_next = min(nearby, key=lambda p: (p[0] - curr_x)**2 + (p[1] - curr_y)**2)
            else:
                # Prioritize natural stroke beginnings (higher up / reading start) among unvisited endpoints or top seeds
                unvis_endpoints = [p for p in unvisited if len([n for n in neighbors[p] if n in unvisited]) <= 1]
                if unvis_endpoints:
                    best_next = min(unvis_endpoints, key=start_priority)
                else:
                    best_next = min(unvisited, key=start_priority)

            has_momentum = False
            current = best_next

    return ordered

def _is_rtl_char(c: str) -> bool:
    """Returns True if the character belongs to an RTL script (Arabic, Hebrew)."""
    if not c:
        return False
    code = ord(c[0])
    return (0x0600 <= code <= 0x06FF) or (0x0750 <= code <= 0x077F) or \
           (0x08A0 <= code <= 0x08FF) or (0xFB50 <= code <= 0xFDFF) or (0xFE70 <= code <= 0xFEFF)


def generate_time_map(qimage: QImage, is_rtl: bool, char_map: list = None, algorithm: str = None, return_trajectory: bool = False):
    """
    Generates a Time-Map matrix for every pixel using kinematic handwriting algorithms,
    and optionally returns the sub-pixel smooth skeleton trajectory for pen positioning.
    """
    # 1. Extract Mask
    text_mask = qimage_to_mask(qimage)
    orig_h, orig_w = text_mask.shape

    # Fast Mode: Downscale before processing to speed up 25x while preserving high fidelity
    scale_down_factor = 1.0
    MAX_DIM = 1200
    if orig_w > MAX_DIM or orig_h > MAX_DIM:
        scale_down_factor = min(MAX_DIM / float(orig_w), MAX_DIM / float(orig_h))
        new_w = int(orig_w * scale_down_factor)
        new_h = int(orig_h * scale_down_factor)
        processing_mask = cv2.resize(text_mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
    else:
        processing_mask = text_mask
        new_w = orig_w
        new_h = orig_h
    
    # 2. Binary Thresholding
    _, binary = cv2.threshold(processing_mask, 1, 255, cv2.THRESH_BINARY)
    
    # 3. Guo-Hall Thinning (Skeletonization)
    skel = cv2.ximgproc.thinning(binary, thinningType=cv2.ximgproc.THINNING_GUOHALL)
    
    # 4. Find ordered seeds along skeleton
    y_coords, x_coords = np.nonzero(skel)
    seeds = list(zip(x_coords, y_coords))
    
    if not seeds:
        empty_map = np.zeros_like(text_mask)
        if return_trajectory:
            from PySide6.QtCore import QPointF
            return empty_map, [QPointF(orig_w / 2.0, orig_h / 2.0)] * 512
        return empty_map
        
    # --- New Logic: Use char_map to find the char_idx for each seed ---
    seeds_with_char_idx = []
    
    if char_map and len(char_map) > 0:
        # Check if line_idx is provided in char_map
        has_line_idx = all('line_idx' in ch for ch in char_map)
        sorted_chars = []

        if has_line_idx:
            # Group chars by line_idx
            lines_dict = {}
            for i, ch in enumerate(char_map):
                lines_dict.setdefault(ch.get('line_idx', 0), []).append((i, ch))

            for l_idx in sorted(lines_dict.keys()):
                line_chars = lines_dict[l_idx]
                
                # Partition line into runs of same direction (Latin LTR vs Arabic RTL)
                runs = []
                curr_run = []
                curr_rtl = None
                
                for i, ch in line_chars:
                    c_rtl = _is_rtl_char(ch.get('char', ''))
                    if curr_rtl is None or c_rtl == curr_rtl:
                        curr_run.append((i, ch))
                        curr_rtl = c_rtl
                    else:
                        runs.append((curr_rtl, curr_run))
                        curr_run = [(i, ch)]
                        curr_rtl = c_rtl
                if curr_run:
                    runs.append((curr_rtl, curr_run))
                    
                # Order runs according to overall line direction:
                # If dominant line direction is RTL, runs flow from right to left
                # If dominant line direction is LTR, runs flow from left to right
                if is_rtl:
                    runs.sort(key=lambda r: -max((ch['x'] * scale_down_factor + (ch['w'] * scale_down_factor) / 2.0) for _, ch in r[1]))
                else:
                    runs.sort(key=lambda r: min((ch['x'] * scale_down_factor + (ch['w'] * scale_down_factor) / 2.0) for _, ch in r[1]))
                    
                # Within each run:
                # Latin/English runs are ALWAYS written Left-to-Right!
                # Arabic runs are ALWAYS written Right-to-Left!
                for run_rtl, run_chars in runs:
                    if run_rtl:
                        sorted_run = sorted(run_chars, key=lambda p: -(p[1]['x'] * scale_down_factor + (p[1]['w'] * scale_down_factor) / 2.0))
                    else:
                        sorted_run = sorted(run_chars, key=lambda p: (p[1]['x'] * scale_down_factor + (p[1]['w'] * scale_down_factor) / 2.0))
                    for orig_idx, _ in sorted_run:
                        sorted_chars.append(orig_idx)

            visual_order_map = {orig_idx: visual_idx for visual_idx, orig_idx in enumerate(sorted_chars)}
        else:
            # Fallback clustering
            char_items = []
            for i, ch in enumerate(char_map):
                cx = ch['x'] * scale_down_factor
                cy = ch['y'] * scale_down_factor
                cw = ch['w'] * scale_down_factor
                ch_h = ch['h'] * scale_down_factor
                char_items.append({
                    "orig_idx": i,
                    "rect": (cx, cy, cw, ch_h),
                    "centroid": (cx + cw / 2.0, cy + ch_h / 2.0)
                })
            from core.drawing_engine.algorithms.base_algorithm import BaseDrawingAlgorithm
            clustered = BaseDrawingAlgorithm.cluster_islands_into_lines(
                char_items, rtl=is_rtl, sort_mode="right_to_left" if is_rtl else "left_to_right"
            )
            visual_order_map = {it["orig_idx"]: visual_idx for visual_idx, it in enumerate(clustered)}
            sorted_chars = [it["orig_idx"] for it in clustered]
        
        # Create 2D arrays for O(1) lookups with overlap resolution
        char_idx_map = np.full((new_h, new_w), -1, dtype=np.int32)
        dist_map = np.full((new_h, new_w), 1e9, dtype=np.float32)
        
        # Fill bounding boxes with visual_order_idx, resolving overlaps via nearest centroid
        for i, ch in enumerate(char_map):
            cx = int(ch['x'] * scale_down_factor)
            cy = int(ch['y'] * scale_down_factor)
            cw = int(ch['w'] * scale_down_factor)
            ch_h = int(ch['h'] * scale_down_factor)
            
            y1, y2 = max(0, cy), min(new_h, cy + ch_h)
            x1, x2 = max(0, cx), min(new_w, cx + cw)
            
            if y2 > y1 and x2 > x1:
                center_x = cx + cw / 2.0
                center_y = cy + ch_h / 2.0
                y_idx, x_idx = np.ogrid[y1:y2, x1:x2]
                dists = (x_idx - center_x) ** 2 + (y_idx - center_y) ** 2
                
                closer_mask = dists < dist_map[y1:y2, x1:x2]
                char_idx_map[y1:y2, x1:x2][closer_mask] = visual_order_map[i]
                dist_map[y1:y2, x1:x2][closer_mask] = dists[closer_mask]
            
        # Pre-group char_map indices by line_idx if available
        chars_by_line = {}
        if has_line_idx:
            for i, ch in enumerate(char_map):
                chars_by_line.setdefault(ch.get('line_idx', 0), []).append(i)

        for x, y in seeds:
            idx = char_idx_map[y, x]
            
            if idx == -1:
                # Fallback if seed is slightly outside bounding box:
                # Constrain search to characters in the same vertical line band
                candidate_indices = None
                if has_line_idx and chars_by_line:
                    best_l_dist = float('inf')
                    best_line_idx = None
                    for l_idx, indices in chars_by_line.items():
                        l_min_y = min(char_map[ci]['y'] * scale_down_factor for ci in indices)
                        l_max_y = max((char_map[ci]['y'] + char_map[ci]['h']) * scale_down_factor for ci in indices)
                        if l_min_y <= y <= l_max_y:
                            best_line_idx = l_idx
                            break
                        dist_to_line = min(abs(y - l_min_y), abs(y - l_max_y))
                        if dist_to_line < best_l_dist:
                            best_l_dist = dist_to_line
                            best_line_idx = l_idx
                    if best_line_idx is not None:
                        candidate_indices = chars_by_line[best_line_idx]

                if not candidate_indices:
                    candidate_indices = range(len(char_map))

                best_idx = 0
                best_dist = float('inf')
                for i in candidate_indices:
                    ch = char_map[i]
                    cx = ch['x'] * scale_down_factor
                    cy = ch['y'] * scale_down_factor
                    cw = ch['w'] * scale_down_factor
                    ch_h = ch['h'] * scale_down_factor
                    center_x = cx + cw / 2.0
                    center_y = cy + ch_h / 2.0
                    dist = (x - center_x)**2 + (y - center_y)**2
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = visual_order_map[i]
                idx = best_idx
                        
            seeds_with_char_idx.append((idx, x, y))
            
        # Group seeds by visual char_idx, then sort each character's skeleton topologically
        char_seeds_dict = {}
        for idx, x, y in seeds_with_char_idx:
            char_seeds_dict.setdefault(idx, []).append((x, y))

        sorted_char_indices = sorted(char_seeds_dict.keys())
        seeds = []
        for c_idx in sorted_char_indices:
            char_pts = char_seeds_dict[c_idx]
            # Determine script direction for topological seed ordering
            char_is_rtl = is_rtl
            if c_idx < len(sorted_chars):
                orig_i = sorted_chars[c_idx]
                if orig_i < len(char_map):
                    char_is_rtl = _is_rtl_char(char_map[orig_i].get('char', ''))
            seeds.extend(_topological_sort_seeds(char_pts, is_rtl=char_is_rtl))
    else:
        # Fallback if char_map is not available: cluster seeds into visual lines
        from core.drawing_engine.algorithms.base_algorithm import BaseDrawingAlgorithm
        seed_items = [{"orig_seed": (x, y), "centroid": (float(x), float(y)), "rect": (float(x)-5, float(y)-5, 10.0, 10.0)} for x, y in seeds]
        clustered_seeds = BaseDrawingAlgorithm.cluster_islands_into_lines(
            seed_items, rtl=is_rtl, sort_mode="right_to_left" if is_rtl else "left_to_right"
        )
        seeds = _topological_sort_seeds([it["orig_seed"] for it in clustered_seeds], is_rtl=is_rtl)
        
    # 7. Apply physics/kinematic writing algorithm to assign time (t in [0.0, 1.0]) for each seed
    from .algorithms import get_writing_algorithm
    algo = get_writing_algorithm(algorithm)
    seed_times = algo.generate_times(seeds, is_rtl=is_rtl)
    if len(seed_times) != len(seeds) or not isinstance(seed_times, np.ndarray):
        seed_times = np.linspace(0.0, 1.0, len(seeds))
    
    # 8. Seed Mask for Distance Transform
    h, w = binary.shape
    seed_mask = np.full((h, w), 255, dtype=np.uint8)
    for x, y in seeds:
        seed_mask[y, x] = 0
        
    # 9. Distance Transform with Labels
    dist, labels = cv2.distanceTransformWithLabels(
        seed_mask, 
        cv2.DIST_L2, 
        cv2.DIST_MASK_5, 
        labelType=cv2.DIST_LABEL_PIXEL
    )
    
    # 10. Look-Up-Table (LUT) mapping each seed label to quantized timestamp [0..255]
    max_label = int(np.max(labels))
    lut = np.zeros(max_label + 1, dtype=np.uint8)
    
    for i, (x, y) in enumerate(seeds):
        lbl = labels[y, x]
        lut[lbl] = int(seed_times[i] * 255.0)
        
    # 11. Create Time-Map Image
    time_map_image = lut[labels]
    
    # Clean background pixels
    time_map_image[binary == 0] = 255
    
    # Upscale back to original size using INTER_NEAREST to prevent artificial gradient wave smears
    if scale_down_factor != 1.0:
        time_map_image = cv2.resize(time_map_image, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
        
        # Re-apply the original high-res mask to ensure crisp vector edges
        _, orig_binary = cv2.threshold(text_mask, 1, 255, cv2.THRESH_BINARY)
        time_map_image[orig_binary == 0] = 255
    
    if return_trajectory:
        from PySide6.QtCore import QPointF
        seeds_orig_x = np.array([float(p[0]) / scale_down_factor for p in seeds], dtype=float)
        seeds_orig_y = np.array([float(p[1]) / scale_down_factor for p in seeds], dtype=float)

        # Smooth spatial coordinates within continuous strokes to eliminate discrete 1-pixel raster staircase kinks
        if len(seeds_orig_x) >= 5:
            from .algorithms.realistic_hybrid.realistic_hybrid_algorithm import _gaussian_smooth_1d
            jump_dists = np.sqrt((seeds_orig_x[1:] - seeds_orig_x[:-1]) ** 2 + (seeds_orig_y[1:] - seeds_orig_y[:-1]) ** 2)
            j_indices = np.where(jump_dists > (8.0 / scale_down_factor))[0]
            seg_starts = [0] + [j + 1 for j in j_indices]
            seg_ends = [j + 1 for j in j_indices] + [len(seeds_orig_x)]
            
            for s0, s1 in zip(seg_starts, seg_ends):
                if s1 - s0 >= 5:
                    seeds_orig_x[s0:s1] = _gaussian_smooth_1d(seeds_orig_x[s0:s1], sigma=1.2)
                    seeds_orig_y[s0:s1] = _gaussian_smooth_1d(seeds_orig_y[s0:s1], sigma=1.2)

        NUM_TRAJ_POINTS = 512
        trajectory_points = []
        for k in range(NUM_TRAJ_POINTS):
            prog = k / float(NUM_TRAJ_POINTS - 1)
            tx = float(np.interp(prog, seed_times, seeds_orig_x))
            ty = float(np.interp(prog, seed_times, seeds_orig_y))
            trajectory_points.append(QPointF(tx, ty))
        return time_map_image, trajectory_points

    return time_map_image
