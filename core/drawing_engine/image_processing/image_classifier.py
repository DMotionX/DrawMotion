from PySide6.QtGui import QImage, QColor

class ImageClassifier:
    """
    Decision Engine for Hybrid Image System.
    Analyzes an image and decides if it should be rendered as a Raster (Photo), 
    Vector (Icon/SVG), or Hybrid (Diagram/Complex).
    """
    
    @staticmethod
    def classify(image_path: str) -> str:
        """
        Returns 'raster', 'vector', or 'hybrid'.
        """
        # Very simple heuristic based on extension first
        if image_path.lower().endswith('.svg'):
            return "vector"
            
        try:
            img = QImage(image_path)
            if img.isNull():
                return "raster" # Safe fallback
                
            # If the image is large, tracing it to vector is usually a bad idea.
            if img.width() * img.height() > 1000000: # 1 Megapixel
                return "raster"
                
            # A real implementation would sample pixels to look for high color variance
            # (which indicates a photo) vs solid blocks of color (which indicates an icon/diagram).
            
            # Simulated check: For now, default to raster reveal for high-quality photos
            return "raster"
            
        except Exception:
            return "raster"
