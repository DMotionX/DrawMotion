"""
Purpose: Backend service for processing raster images using OpenCV.
Features: Converts normal JPG/PNG images into vector paths (Edge Detection) so the AnimatorEngine can draw them as sketches.
"""
import cv2
import numpy as np
from PySide6.QtGui import QPainterPath
from PySide6.QtCore import QPointF

class ImageProcessingService:
    @staticmethod
    def trace_image_to_path(image_path: str, threshold1: int = 100, threshold2: int = 200) -> QPainterPath:
        """
        Uses OpenCV Canny Edge Detection to find outlines in an image and 
        converts those outlines into a drawable QPainterPath.
        """
        # Read image in grayscale
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"[Error] Could not load image: {image_path}")
            return QPainterPath()
            
        # Apply Canny Edge Detection
        edges = cv2.Canny(img, threshold1, threshold2)
        
        # Find contours from the edges
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        path = QPainterPath()
        
        for contour in contours:
            if len(contour) < 2: continue
            
            # contour shape is (N, 1, 2)
            first_point = contour[0][0]
            path.moveTo(QPointF(float(first_point[0]), float(first_point[1])))
            
            for pt in contour[1:]:
                p = pt[0]
                path.lineTo(QPointF(float(p[0]), float(p[1])))
                
        return path.simplified()
