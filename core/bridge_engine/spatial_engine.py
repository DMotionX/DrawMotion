from PySide6.QtCore import QPointF, QRectF
from .scene_context import SceneObject, SceneContext

class SpatialEngine:
    """
    Subsystem: Spatial Intelligence Engine
    Responsible for Layout Awareness, avoiding overlaps, and language-aware placement.
    """
    
    @staticmethod
    def find_best_label_position(target_obj: SceneObject, context: SceneContext, lang: str = "EN") -> QPointF:
        """
        Finds the best empty space around an object to place a label.
        Takes language direction into account.
        """
        bbox = target_obj.bbox
        
        # Simple heuristic:
        # English (LTR): Place label on the right side or bottom right.
        # Arabic (RTL): Place label on the left side or bottom left (because text flows to the left).
        
        offset_x = 20
        offset_y = 20
        
        if lang == "AR":
            # Place to the left of the bounding box
            x = bbox.left() - offset_x
            y = bbox.bottom() + offset_y
        else:
            # Place to the right
            x = bbox.right() + offset_x
            y = bbox.bottom() + offset_y
            
        candidate_pos = QPointF(x, y)
        
        # Collision detection (Error Recovery)
        # If the candidate position is inside another object's bounding box, move it down.
        collision = True
        while collision:
            collision = False
            for obj in context.objects:
                if obj.id != target_obj.id and obj.bbox.contains(candidate_pos):
                    collision = True
                    candidate_pos.setY(candidate_pos.y() + 30) # move down
                    break
                    
        return candidate_pos
