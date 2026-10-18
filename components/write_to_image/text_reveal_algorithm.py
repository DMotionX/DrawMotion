"""
TextRevealAlgorithm: A standalone algorithm that generates timed segments 
for the Solid Reveal engine but strictly sequentially (line by line).

v5: Sequential Line Wipe
Instead of treating text like a random image painting, we scan for ink density 
horizontally to group ink into lines, then generate a simple, dense sweeping 
segment across each line sequentially from right to left (or left to right).
"""

from PySide6.QtCore import QPointF
from PySide6.QtGui import QImage
import math

def generate_text_reveal_plan(qimage: QImage, total_duration: float, is_rtl: bool = False) -> list:
    """
    Generates a list of timed segment dicts compatible with the Solid Reveal 
    engine, but forced into a sequential line-by-line order.
    """
    if qimage.isNull():
        return []

    w, h = qimage.width(), qimage.height()
    
    # 1. Analyze image to find lines of text (rows with ink)
    step_x = max(1, w // 100)
    row_density = [0] * h
    max_dens = 0
    
    for y in range(h):
        count = 0
        for x in range(0, w, step_x):
            # >> 24 gets the alpha channel for ARGB32
            if (qimage.pixel(x, y) >> 24) & 0xFF > 10:
                count += 1
        row_density[y] = count
        if count > max_dens: max_dens = count

    # 2. Group into contiguous horizontal bands (lines)
    thresh = max_dens * 0.05
    smoothed = [0] * h
    win = max(1, h // 100)
    for y in range(h):
        s = max(0, y - win)
        e = min(h, y + win + 1)
        smoothed[y] = sum(row_density[s:e]) / (e - s)

    raw_lines = []
    in_line = False
    start_y = 0
    for y in range(h):
        if smoothed[y] > thresh:
            if not in_line:
                start_y = y
                in_line = True
        else:
            if in_line:
                raw_lines.append([start_y, y])
                in_line = False
                
    if in_line:
        raw_lines.append([start_y, h - 1])

    if not raw_lines:
        raw_lines = [[0, h - 1]]
        
    # Merge lines that are very close to each other (e.g. Arabic dots and diacritics)
    lines = []
    for y1, y2 in raw_lines:
        if not lines:
            lines.append([y1, y2])
        else:
            prev_y1, prev_y2 = lines[-1]
            gap = y1 - prev_y2
            # If gap is less than 15% of image height, merge them!
            if gap < h * 0.15:
                lines[-1][1] = y2
            else:
                lines.append([y1, y2])
        
    # 3. Find accurate bounding box for each merged line
    final_lines = []
    for (y1, y2) in lines:
        line_h = y2 - y1
        min_x, max_x = w, 0
        
        step_y = max(1, line_h // 10)
        for y in range(y1, y2 + 1, step_y):
            for x in range(w):
                if (qimage.pixel(x, y) >> 24) & 0xFF > 10:
                    if x < min_x: min_x = x
                    if x > max_x: max_x = x
                    
        if min_x > max_x:
            min_x = int(w * 0.05)
            max_x = int(w * 0.95)
            
        final_lines.append((min_x, max_x, y1, y2))
            
    if not final_lines:
        final_lines = [(0, w, 0, h)]
        
    # 4. Generate points for each line
    segments = []
    current_time = 0.0
    
    total_width = sum(b[1] - b[0] for b in final_lines)
    if total_width <= 0:
        total_width = 1
        
    # Small gap between lines
    gap_time = (0.05 * total_duration) / max(1, len(final_lines))
    active_time = max(0.1, total_duration - gap_time * len(final_lines))

    for min_x, max_x, y1, y2 in final_lines:
        line_w = max_x - min_x
        line_h = y2 - y1
        cy = y1 + line_h / 2.0
        
        # Because we use FlatCap, we don't need any brush radius padding!
        # It starts exactly at the bounding box edge.
        start_x = max_x if is_rtl else min_x
        end_x = min_x if is_rtl else max_x
        
        dur = (line_w / total_width) * active_time
        dur = max(0.01, dur)
        
        num_points = max(10, int(line_w / 4))
        points = []
        
        for j in range(num_points):
            t = j / (num_points - 1)
            x = start_x + (end_x - start_x) * t
            y = cy # Strict flat sweep, no jitter needed for FlatCap wipe
            points.append(QPointF(x, y))
            
        length = abs(end_x - start_x)
        brush_width = line_h * 1.5
        
        seg = {
            "points": points,
            "start_time": current_time,
            "end_time": current_time + dur,
            "duration": dur,
            "active_duration": dur,
            "width": brush_width,
            "opacity": 1.0,
            "length": float(length),
        }
        segments.append(seg)
        current_time += dur + gap_time

    return segments
