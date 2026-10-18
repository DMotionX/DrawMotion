"""
DrawingPathGenerator -- Core image-to-path conversion engine.
Produces clean ordered path segments for the Drawing Engine.
Jitter/style effects are applied ONLY by the Style layer, NOT here.
"""
import cv2
import numpy as np
import math
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import QPointF

_SCIPY_AVAILABLE = False


class DrawingPathGenerator:

    @staticmethod
    def qimage_to_cv2(image: QImage):
        image = image.convertToFormat(QImage.Format.Format_RGBA8888)
        w, h = image.width(), image.height()
        ptr = image.bits()
        arr = np.array(ptr).reshape((h, w, 4))
        alpha = arr[:, :, 3]
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        gray[alpha == 0] = 255
        return gray

    @staticmethod
    def extract_edges(gray_img, complexity: str = "MEDIUM"):
        max_contours   = {"LOW": 40,    "MEDIUM": 80,    "HIGH": 150  }.get(complexity, 80)
        epsilon_factor = {"LOW": 0.010, "MEDIUM": 0.005, "HIGH": 0.002}.get(complexity, 0.005)
        t1, t2         = {"LOW": (50,150), "MEDIUM": (40,120), "HIGH": (30,100)}.get(complexity, (40,120))

        blurred = cv2.GaussianBlur(gray_img, (5, 5), 0)
        edges   = cv2.Canny(blurred, t1, t2)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=lambda c: cv2.arcLength(c, False), reverse=True)[:max_contours]

        optimized = []
        for cnt in contours:
            eps    = epsilon_factor * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, eps, False)
            if len(approx) >= 2:
                optimized.append(approx)
        return optimized

    @staticmethod
    def smooth_path(points):
        if len(points) < 4:
            return points
        if _SCIPY_AVAILABLE and len(points) >= 6:
            x = [p.x() for p in points]
            y = [p.y() for p in points]
            try:
                perim = sum(math.hypot(x[i]-x[i-1], y[i]-y[i-1]) for i in range(1, len(x)))
                s_val = max(1.0, perim * 0.05)
                tck, _ = splprep([x, y], s=s_val, quiet=True)
                n_out  = min(len(points) * 2, 200)
                u      = np.linspace(0, 1, n_out)
                nx, ny = splev(u, tck)
                return [QPointF(float(a), float(b)) for a, b in zip(nx, ny)]
            except Exception:
                pass
        smoothed = [points[0]]
        for i in range(1, len(points) - 1):
            sx = (points[i-1].x() + points[i].x() + points[i+1].x()) / 3.0
            sy = (points[i-1].y() + points[i].y() + points[i+1].y()) / 3.0
            smoothed.append(QPointF(sx, sy))
        smoothed.append(points[-1])
        return smoothed

    @staticmethod
    def calculate_path_length(points) -> float:
        total = 0.0
        for i in range(1, len(points)):
            total += math.hypot(points[i].x()-points[i-1].x(), points[i].y()-points[i-1].y())
        return total

    @staticmethod
    def get_ink_mask(qimage: QImage):
        image = qimage.convertToFormat(QImage.Format.Format_RGBA8888)
        w, h = image.width(), image.height()
        ptr = image.bits()
        arr = np.array(ptr).reshape((h, w, 4))
        alpha = arr[:, :, 3]
        
        # If image is mostly opaque (like a JPG), use grayscale threshold
        if np.mean(alpha == 255) > 0.90:
            bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            # Anything significantly darker than white is ink
            _, mask = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY_INV)
        else:
            # Use alpha channel directly
            _, mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
            
        return mask

    @staticmethod
    def build_drawing_plan(qimage: QImage, duration: float = 2.0):
        # 1. Smart-Eye Ink Detection
        mask = DrawingPathGenerator.get_ink_mask(qimage)
        
        # 2. Group adjacent elements using morphological dilation
        # This helps group letters into words, and sketch parts into coherent shapes
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
        dilated = cv2.dilate(mask, kernel, iterations=1)
        
        # 3. Find connected components (Chunks/Regions)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        rects = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            # Filter out tiny noise dots
            if w > 5 and h > 5:
                rects.append((x, y, w, h))
                
        # 4. Sort chunks: Top to Bottom, Left to Right
        # Group by 50px rows to read lines properly
        rects.sort(key=lambda r: (r[1] // 50, r[0]))
        
        segments = []
        grid_size = 15 # The thickness of our "virtual marker"
        
        # 5. Generate Organic Grid-Based Path for each chunk
        for rect in rects:
            x, y, w, h = rect
            blocks = []
            
            # Scan the chunk area and collect grids that actually contain ink
            for r in range(y, y + h, grid_size):
                for c in range(x, x + w, grid_size):
                    block = mask[r:min(r+grid_size, mask.shape[0]), c:min(c+grid_size, mask.shape[1])]
                    if np.any(block):
                        blocks.append((c + grid_size//2, r + grid_size//2))
                        
            if not blocks:
                continue
                
            # Nearest Neighbor Path (TSP approximation)
            path = [blocks.pop(0)]
            while blocks:
                curr = path[-1]
                blocks_arr = np.array(blocks)
                dists = (blocks_arr[:, 0] - curr[0])**2 + (blocks_arr[:, 1] - curr[1])**2
                
                # Add slight random noise to distances to prevent perfect horizontal raster scans
                # This makes the drawing look more organic like a hand scribbling
                noise = np.random.uniform(0, 0.5 * (grid_size**2), size=dists.shape)
                dists = dists + noise
                
                min_idx = np.argmin(dists)
                path.append(blocks.pop(min_idx))
                
            # Convert to QPointF
            pts = [QPointF(float(p[0]), float(p[1])) for p in path]
            
            # Ensure at least 2 points
            if len(pts) == 1:
                pts.append(QPointF(pts[0].x() + 1, pts[0].y()))
                
            # Calculate length
            length = DrawingPathGenerator.calculate_path_length(pts)
            
            segments.append({
                "type": "mask_reveal", 
                "intent": "draw", 
                "points": pts, 
                "length": length,
                "importance": 1.0,
                "width": grid_size * 1.5 # Overshoot slightly to ensure full coverage
            })
            
        # Compute timings based on length
        total_len = sum(s["length"] for s in segments)
        current_t = 0.0
        for s in segments:
            frac = s["length"] / max(1.0, total_len)
            s["duration"] = frac * duration
            s["start_time"] = current_t
            s["end_time"] = current_t + s["duration"]
            current_t = s["end_time"]
            
        return segments
