import re
import cv2
import numpy as np
from PySide6.QtGui import QImage
from typing import Optional

def is_arabic_text(text: str) -> bool:
    """
    Checks if a text string is predominantly Arabic/Hebrew script.
    """
    if not text:
        return False
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\u0590-\u05FF]')
    latin_pattern = re.compile(r'[a-zA-Z]')
    
    arabic_count = len(arabic_pattern.findall(text))
    latin_count = len(latin_pattern.findall(text))
    
    if arabic_count > latin_count:
        return True
    return False


def detect_script_direction(qimage: QImage, source_text: Optional[str] = None) -> str:
    """
    Smart script detector:
    Determines if content should be drawn Right-to-Left (Arabic/Hebrew) or Left-to-Right (Latin/Generic).
    
    First checks explicit source text if available.
    If not, analyzes topological and morphological visual features of the QImage:
    - Horizontal cursive ligature ratio (Arabic letters connect horizontally on the baseline).
    - Nuqat / diacritic density (Arabic script has high density of small isolated dots).
    
    Returns:
        'rtl' or 'ltr'
    """
    # 1. Check explicit source text if provided
    if source_text and isinstance(source_text, str) and source_text.strip():
        return "rtl" if is_arabic_text(source_text) else "ltr"
        
    # 2. Visual analysis on QImage
    if qimage is None or qimage.isNull():
        return "ltr"
        
    w, h = qimage.width(), qimage.height()
    if w < 10 or h < 10:
        return "ltr"
        
    try:
        ptr = qimage.constBits()
        arr = np.frombuffer(ptr, np.uint8).reshape((h, w, 4))
        alpha = arr[:, :, 3]
        
        _, mask = cv2.threshold(alpha, 10, 255, cv2.THRESH_BINARY)
        non_zero = cv2.countNonZero(mask)
        total_pixels = w * h
        
        # If image has white background or opaque alpha, use Otsu on grayscale
        if non_zero > total_pixels * 0.95:
            gray = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
            _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            non_zero = cv2.countNonZero(mask)
            
        if non_zero < 50:
            return "ltr"
            
        # Fast downscale for morphological analysis if image is large (guarantees < 5ms analysis)
        max_dim = 400
        if w > max_dim or h > max_dim:
            scale = min(max_dim / w, max_dim / h)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            mask_small = cv2.resize(mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
        else:
            mask_small = mask
            
        _, binary = cv2.threshold(mask_small, 30, 255, cv2.THRESH_BINARY)
        
        # Direct connected components analysis on raw ink mask
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_small, connectivity=8)
        
        if num_labels <= 2:
            # Single icon or very few components: default safely to LTR
            return "ltr"
            
        valid_components = 0
        diacritic_count = 0
        wide_cursive_count = 0
        non_dot_aspects = []
        
        for i in range(1, num_labels):
            cw, ch, area = stats[i][2], stats[i][3], stats[i][4]
            if area < 6:
                continue
            valid_components += 1
            
            aspect_ratio = float(cw) / max(1.0, float(ch))
            
            # Diacritics/Nuqat: small, compact components
            if 6 <= area <= 120 and 0.5 <= aspect_ratio <= 1.8:
                diacritic_count += 1
            else:
                non_dot_aspects.append(aspect_ratio)
                
            # Wide cursive ligatures: letters connected along the horizontal baseline
            if aspect_ratio >= 1.5 and area >= 30:
                wide_cursive_count += 1
                
        if valid_components < 3:
            return "ltr"
            
        dot_ratio = diacritic_count / max(1, valid_components)
        wide_ratio = wide_cursive_count / max(1, valid_components)
        avg_aspect = (sum(non_dot_aspects) / max(1, len(non_dot_aspects))) if non_dot_aspects else 0.0
        
        # Decision metric:
        # Arabic cursive text has significant horizontal ligatures (wide_ratio >= 0.10) 
        # and a high density of floating diacritics/nuqat (dot_ratio >= 0.22).
        # Latin print text has zero wide ligatures (wide_ratio = 0.0) and few dots (dot_ratio <= 0.16).
        is_arabic = False
        if dot_ratio >= 0.22 and wide_ratio >= 0.10:
            is_arabic = True
        elif wide_ratio >= 0.18:
            is_arabic = True
        elif dot_ratio >= 0.28 and wide_cursive_count >= 1:
            is_arabic = True
        elif avg_aspect >= 1.05 and wide_ratio >= 0.12:
            is_arabic = True
            
        return "rtl" if is_arabic else "ltr"
        
    except Exception as e:
        # Failsafe fallback to standard LTR on any unexpected error
        return "ltr"
