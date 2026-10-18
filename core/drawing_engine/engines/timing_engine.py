from typing import List
from PySide6.QtCore import QPointF
import math

class TimingEngine:
    """
    Stroke Timing Engine:
    Calculates dynamic drawing speeds based on path geometry.
    Slows down on sharp curves, speeds up on long straight lines.
    """
    
    @staticmethod
    def calculate_durations(points: List[QPointF], base_speed: float = 200.0) -> List[float]:
        """
        Returns a list of durations (in seconds) for each segment.
        """
        if len(points) < 2:
            return []
            
        durations = []
        for i in range(1, len(points)):
            p1 = points[i-1]
            p2 = points[i]
            
            dist = math.hypot(p2.x() - p1.x(), p2.y() - p1.y())
            
            # Default time based on distance / speed
            time = dist / max(1.0, base_speed)
            
            # Simple curvature estimation (if we had 3 points, we'd check the angle)
            # For now, we simulate slowing down on very short, dense segments (typical of curves)
            if dist < 5.0:
                time *= 1.5 # Slow down
            elif dist > 50.0:
                time *= 0.8 # Speed up on long straights
                
            durations.append(time)
            
        return durations
