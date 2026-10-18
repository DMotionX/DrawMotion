from PySide6.QtCore import QPointF
from typing import List, Dict, Any

class SceneObject:
    def __init__(self, id: str, obj_type: str, bbox: Any, metadata: Dict = None):
        self.id = id
        self.obj_type = obj_type  # e.g., 'image', 'text', 'shape'
        self.bbox = bbox          # Bounding box (QRectF)
        self.metadata = metadata or {}
        
class SceneContext:
    """
    Layer 0: Scene Context Engine
    Stateful memory for the Intelligent Presentation Engine.
    Keeps track of drawn objects, current hand position, and modes.
    """
    def __init__(self):
        self.objects: List[SceneObject] = []
        self.last_hand_position: QPointF = QPointF(0, 0)
        self.current_mode: str = "idle" # 'draw', 'write', 'annotate', 'idle'
        self.action_history: List[str] = []
        
    def add_object(self, obj: SceneObject):
        self.objects.append(obj)
        
    def update_hand_position(self, pos: QPointF):
        self.last_hand_position = pos
        
    def set_mode(self, mode: str):
        self.current_mode = mode
        self.action_history.append(mode)
        
    def get_last_action(self) -> str:
        if self.action_history:
            return self.action_history[-1]
        return "none"
        
    def clear(self):
        self.objects.clear()
        self.last_hand_position = QPointF(0, 0)
        self.current_mode = "idle"
        self.action_history.clear()
        
    def find_nearest_object(self, point: QPointF) -> SceneObject:
        """Finds the closest drawn object to a given point (useful for semantic grouping)."""
        if not self.objects:
            return None
            
        closest = None
        min_dist = float('inf')
        
        for obj in self.objects:
            center = obj.bbox.center()
            dist = (center.x() - point.x())**2 + (center.y() - point.y())**2
            if dist < min_dist:
                min_dist = dist
                closest = obj
                
        return closest
