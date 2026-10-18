from dataclasses import dataclass
from typing import List
from PySide6.QtCore import QPointF

@dataclass
class Stroke:
    """
    Represents a single continuous line segment with styling properties.
    Moves beyond simple QPointF to support pressure simulation.
    """
    points: List[QPointF]
    width: float = 2.0
    opacity: float = 1.0
    color: str = "#000000"
    
class StrokeEngine:
    """
    Converts raw points into detailed Strokes, applying thickness and opacity variations.
    """
    
    @staticmethod
    def generate_strokes(points: List[QPointF], base_width: float, base_opacity: float, simulate_pressure: bool = False) -> List[Stroke]:
        """
        Creates Stroke objects from points.
        If simulate_pressure is True, it tapers the ends of the stroke.
        """
        if not points:
            return []
            
        # In a very advanced implementation, we would split a long list of points into
        # multiple Strokes if there's a pen lift. Assuming points here are one continuous segment.
        
        stroke = Stroke(points=points, width=base_width, opacity=base_opacity)
        
        if simulate_pressure and len(points) > 10:
            # We can't easily taper a single QGraphicsPathItem with standard Qt without
            # doing complex polygon generation. 
            # But we CAN vary opacity. Let's simulate a slight fade in/out at the tips.
            # This data will be used by the renderer later.
            stroke.opacity = base_opacity * 0.9 # Just a placeholder for the logic
            
        return [stroke]
