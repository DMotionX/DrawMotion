import math
from PySide6.QtCore import QPointF

class TransitionSystem:
    """
    Subsystem: Transition Intelligence
    Ensures smooth, cinematic transitions between different actions (e.g., from drawing to writing).
    """
    
    @staticmethod
    def create_smooth_transition(start_pos: QPointF, end_pos: QPointF, speed: float = 400.0) -> dict:
        """
        Generates a timed motion segment for the hand to travel smoothly without drawing.
        """
        if start_pos is None or end_pos is None:
            return None
            
        distance = math.hypot(end_pos.x() - start_pos.x(), end_pos.y() - start_pos.y())
        
        # If they are practically in the same spot, no transition needed
        if distance < 5:
            return None
            
        duration = distance / max(1.0, speed)
        
        # We can add an extra "lift" and "drop" time buffer
        lift_buffer = 0.1
        drop_buffer = 0.1
        total_duration = duration + lift_buffer + drop_buffer
        
        return {
            "type": "move-hand",
            "from_pos": start_pos,
            "to_pos": end_pos,
            "duration": total_duration,
            "distance": distance
        }
