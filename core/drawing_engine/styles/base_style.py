from abc import ABC, abstractmethod
from typing import List
from PySide6.QtCore import QPointF
from ..engines.stroke_engine import Stroke
from ..humanization_profile import HumanizationProfile
import random

class BaseStyle(ABC):
    """
    Base class for all drawing styles.
    """
    def __init__(self, profile: HumanizationProfile = None):
        self.profile = profile or HumanizationProfile()
        
    @abstractmethod
    def apply(self, points: List[QPointF]) -> List[Stroke]:
        """
        Takes raw optimized points, applies the style (jitter, multiple passes), 
        and returns a list of detailed Strokes.
        """
        pass
        
    def _apply_jitter(self, points: List[QPointF]) -> List[QPointF]:
        """Applies humanization noise if enabled."""
        if not self.profile.allow_humanization or self.profile.jitter_amount <= 0:
            return points
            
        jittered = []
        jitter = self.profile.jitter_amount
        for p in points:
            nx = p.x() + random.uniform(-jitter, jitter)
            ny = p.y() + random.uniform(-jitter, jitter)
            jittered.append(QPointF(nx, ny))
            
        return jittered

class ProfessionalStyle(BaseStyle):
    """
    Clean, smooth, Bézier style rendering. Figma/AfterEffects style.
    No jitter, one pass.
    """
    def apply(self, points: List[QPointF]) -> List[Stroke]:
        # Force no humanization for professional style
        self.profile.allow_humanization = False 
        
        clean_points = self._apply_jitter(points)
        
        from ..engines.stroke_engine import StrokeEngine
        return StrokeEngine.generate_strokes(clean_points, base_width=3.0, base_opacity=1.0)

class SketchStyle(BaseStyle):
    """
    Messy, human-like sketch style. 
    Applies jitter and multiple overlay passes.
    """
    def apply(self, points: List[QPointF]) -> List[Stroke]:
        strokes = []
        from ..engines.stroke_engine import StrokeEngine
        
        passes = self.profile.sketch_passes
        
        for i in range(passes):
            # Each pass gets a different random jitter
            pass_points = self._apply_jitter(points)
            
            # Lower opacity for multiple passes to create a pencil effect
            opacity = 1.0 if passes == 1 else 0.4
            
            pass_strokes = StrokeEngine.generate_strokes(
                pass_points, 
                base_width=2.0, 
                base_opacity=opacity,
                simulate_pressure=True
            )
            strokes.extend(pass_strokes)
            
        return strokes

class EducationalStyle(BaseStyle):
    """
    Clean, pedagogical style. Slightly thicker lines, no jitter, clear paths.
    """
    def apply(self, points: List[QPointF]) -> List[Stroke]:
        self.profile.allow_humanization = False 
        
        from ..engines.stroke_engine import StrokeEngine
        return StrokeEngine.generate_strokes(points, base_width=4.0, base_opacity=1.0)
