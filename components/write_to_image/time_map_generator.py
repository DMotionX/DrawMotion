import cv2
import numpy as np
from PySide6.QtGui import QImage

def qimage_to_mask(qimage: QImage) -> np.ndarray:
    """
    يستخرج قناة الشفافية (Alpha) من QImage ويحولها إلى مصفوفة NumPy ثنائية الأبعاد.
    """
    alpha_img = qimage.convertToFormat(QImage.Format_Alpha8)
    ptr = alpha_img.constBits()
    # نحول المؤشر إلى مصفوفة بايتات
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((alpha_img.height(), alpha_img.bytesPerLine()))
    # نقطع العرض الفعلي فقط (في حالة وجود Padding)
    mask = arr[:, :alpha_img.width()].copy()
    return mask

def generate_time_map(qimage: QImage, is_rtl: bool, char_map: list = None) -> np.ndarray:
    """
    يولد خريطة زمنية (Time-Map) لكل بكسل في الصورة.
    يعيد مصفوفة NumPy من نوع uint8 (0-255) تمثل وقت ظهور كل بكسل.
    """
    # 1. استخراج الـ Mask
    text_mask = qimage_to_mask(qimage)
    orig_h, orig_w = text_mask.shape

    # Fast Mode: Downscale before processing to speed up 25x
    scale_down_factor = 1.0
    MAX_DIM = 800
    if orig_w > MAX_DIM or orig_h > MAX_DIM:
        scale_down_factor = min(MAX_DIM / float(orig_w), MAX_DIM / float(orig_h))
        new_w = int(orig_w * scale_down_factor)
        new_h = int(orig_h * scale_down_factor)
        processing_mask = cv2.resize(text_mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
    else:
        processing_mask = text_mask
        new_w = orig_w
        new_h = orig_h
    
    # 2. تحويل الـ Mask إلى صورة ثنائية (0 و 255)
    _, binary = cv2.threshold(processing_mask, 1, 255, cv2.THRESH_BINARY)
    
    # 3. استخراج الهيكل العظمي (Skeleton)
    skel = cv2.ximgproc.thinning(binary, thinningType=cv2.ximgproc.THINNING_GUOHALL)
    
    # 4. العثور على البذور (Seeds) على مسار الهيكل
    y_coords, x_coords = np.nonzero(skel)
    seeds = list(zip(x_coords, y_coords))
    
    if not seeds:
        # إذا كانت الصورة فارغة، نعيد مصفوفة أصفار
        return np.zeros_like(text_mask)
        
    # --- New Logic: Use char_map to find the char_idx for each seed ---
    seeds_with_char_idx = []
    
    if char_map and len(char_map) > 0:
        # Check if line_idx is provided in char_map
        has_line_idx = all('line_idx' in ch for ch in char_map)
        if has_line_idx:
            # Sort by line_idx then horizontal position
            sorted_chars = []
            for i, ch in enumerate(char_map):
                cx = ch['x'] * scale_down_factor
                cw = ch['w'] * scale_down_factor
                l_idx = ch['line_idx']
                sorted_chars.append((i, l_idx, cx + cw / 2.0))
            if is_rtl:
                sorted_chars.sort(key=lambda p: (p[1], -p[2]))
            else:
                sorted_chars.sort(key=lambda p: (p[1], p[2]))
            visual_order_map = {orig_idx: visual_idx for visual_idx, (orig_idx, _, _) in enumerate(sorted_chars)}
        else:
            # Use line clustering based on bounding boxes
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
        
        # Create a 2D array for O(1) lookups
        char_idx_map = np.full((new_h, new_w), -1, dtype=np.int32)
        
        # Fill bounding boxes with their visual_order_idx
        for i, ch in enumerate(char_map):
            cx = int(ch['x'] * scale_down_factor)
            cy = int(ch['y'] * scale_down_factor)
            cw = int(ch['w'] * scale_down_factor)
            ch_h = int(ch['h'] * scale_down_factor)
            
            y1, y2 = max(0, cy), min(new_h, cy + ch_h)
            x1, x2 = max(0, cx), min(new_w, cx + cw)
            
            char_idx_map[y1:y2, x1:x2] = visual_order_map[i]
            
        for x, y in seeds:
            idx = char_idx_map[y, x]
            
            if idx == -1:
                # Fallback if seed is slightly outside bounding box
                best_idx = 0
                best_dist = float('inf')
                for i, ch in enumerate(char_map):
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
            
        # Sort seeds by visual char_idx, then by X depending on RTL
        if is_rtl:
            seeds_with_char_idx.sort(key=lambda p: (p[0], -p[1]))
        else:
            seeds_with_char_idx.sort(key=lambda p: (p[0], p[1]))
            
        seeds = [(p[1], p[2]) for p in seeds_with_char_idx]
    else:
        # Fallback if char_map is not available: cluster seeds into visual lines
        from core.drawing_engine.algorithms.base_algorithm import BaseDrawingAlgorithm
        seed_items = [{"orig_seed": (x, y), "centroid": (float(x), float(y)), "rect": (float(x)-5, float(y)-5, 10.0, 10.0)} for x, y in seeds]
        clustered_seeds = BaseDrawingAlgorithm.cluster_islands_into_lines(
            seed_items, rtl=is_rtl, sort_mode="right_to_left" if is_rtl else "left_to_right"
        )
        seeds = [it["orig_seed"] for it in clustered_seeds]
        
    # 7. تعيين وقت (t) من 0 إلى 1 لكل بذرة
    seed_times = np.linspace(0.0, 1.0, len(seeds))
    
    # 7. إنشاء قناع البذور (Seed Mask) لعملية Distance Transform
    h, w = binary.shape
    seed_mask = np.full((h, w), 255, dtype=np.uint8)
    for x, y in seeds:
        seed_mask[y, x] = 0
        
    # 8. حساب المسافات وربط كل بكسل بأقرب بذرة (Distance Transform with Labels)
    dist, labels = cv2.distanceTransformWithLabels(
        seed_mask, 
        cv2.DIST_L2, 
        cv2.DIST_MASK_5, 
        labelType=cv2.DIST_LABEL_PIXEL
    )
    
    # 9. بناء جدول تحويل (LUT) لربط الـ Label بالزمن الخاص بالبذرة
    # الـ Label رقم 0 هو الخلفية، والـ Labels تبدأ من 1.
    max_label = int(np.max(labels))
    lut = np.zeros(max_label + 1, dtype=np.uint8)
    
    # نحتاج لمعرفة أي Label يعود لأي بذرة
    for i, (x, y) in enumerate(seeds):
        lbl = labels[y, x]
        # نحول الزمن [0, 1] إلى قيمة لونية [0, 255]
        lut[lbl] = int(seed_times[i] * 255.0)
        
    # 10. إنشاء مصفوفة الزمن لكل بكسل (Time-Map Image)
    time_map_image = lut[labels]
    
    # 11. إخفاء البكسلات التي لا تنتمي للنص الأصلي (للتنظيف فقط)
    time_map_image[binary == 0] = 255
    
    # Upscale back to original size if it was downscaled
    if scale_down_factor != 1.0:
        time_map_image = cv2.resize(time_map_image, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
        
        # Re-apply the original high-res mask to ensure crisp edges
        _, orig_binary = cv2.threshold(text_mask, 1, 255, cv2.THRESH_BINARY)
        time_map_image[orig_binary == 0] = 255
    
    return time_map_image
