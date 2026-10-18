import os
import xml.etree.ElementTree as ET

class SVGAnalyzer:
    """
    Adaptive Engine (Phase 4): 
    Analyzes SVG complexity to decide whether to draw it as vectors or fallback to Raster Sweep.
    """
    @staticmethod
    def is_complex(file_path: str) -> bool:
        # 1. Quick check: File size
        # If an SVG is larger than 1MB, it's definitely an AI-generated or highly complex shape.
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > 1.0:
                return True
        except Exception:
            pass

        # 2. Deep check: Number of paths/nodes
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Count elements that require drawing algorithms
            path_count = 0
            for tag in ['{http://www.w3.org/2000/svg}path', 
                        '{http://www.w3.org/2000/svg}polygon', 
                        '{http://www.w3.org/2000/svg}polyline',
                        '{http://www.w3.org/2000/svg}rect',
                        '{http://www.w3.org/2000/svg}circle']:
                path_count += len(root.findall(f".//{tag}"))
            
            # If it has more than 500 paths, it will cause heavy lag in the vector drawing engine
            if path_count > 500:
                return True
                
        except Exception:
            # If we fail to parse (e.g., malformed XML), treat as complex to be safe
            return True

        return False
