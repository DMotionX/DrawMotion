from typing import List, Dict, Any
from PySide6.QtCore import QPointF

from ..cache.cache_manager import drawing_cache
from ..engines.path_optimizer import PathOptimizer
from ..engines.timing_engine import TimingEngine
from ..engines.stroke_engine import Stroke
from ..styles.base_style import BaseStyle

class DrawingPipeline:
    """
    Central Coordinator for the Drawing Engine.
    Executes the rendering pipeline: Input -> Direction -> Segment -> Style -> Render
    """
    
    @staticmethod
    def process_path(points: List[QPointF], style: BaseStyle, zoom_level: float = 1.0, object_type: str = "default") -> Dict[str, Any]:
        """
        Takes raw points and pushes them through the advanced drawing pipeline.
        Returns a dictionary containing the optimized strokes and timings.
        """
        if not points:
            return {"strokes": [], "durations": []}
            
        # 1. Caching Check
        # Convert points to a simple string representation for the hash key
        path_str = f"pts_{len(points)}_{points[0].x() if points else 0}"
        style_name = style.__class__.__name__
        cache_key = drawing_cache.generate_key(path_str, style_name, zoom_level)
        
        cached_result = drawing_cache.get(cache_key)
        if cached_result:
            return cached_result
            
        # 2. Smart Direction Engine (Path Analysis)
        optimized_points = PathOptimizer.find_best_direction(points)
        
        # 3. Adaptive Humanization Tuning
        # Inform the style to adapt based on zoom and object type
        from ..humanization_profile import HumanizationProfile
        style.profile = HumanizationProfile.create_adaptive(
            base_intensity=style.profile.jitter_amount, 
            zoom_level=zoom_level, 
            object_type=object_type
        )
        
        # 4. Style Application & Stroke Generation
        # The style handles applying jitter and calling StrokeEngine
        final_strokes = style.apply(optimized_points)
        
        # 5. Timing Engine (Variable speed based on curvature/length)
        # We calculate timing based on the original optimized points (ignoring jitter noise for speed calculations)
        durations = TimingEngine.calculate_durations(optimized_points)
        
        # 6. Final Result Assembly
        result = {
            "strokes": final_strokes,
            "durations": durations
        }
        
        # 7. Store in Cache
        drawing_cache.set(cache_key, result)
        
        return result
