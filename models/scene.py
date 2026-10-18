"""
Purpose: Defines the Scene data model.
Features: Contains a list of layers, scene duration, and background properties.
Usage Summary: The top-level data structure for a specific animation sequence.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from models.layer import LayerModel

@dataclass
class SceneModel:
    id: str
    name: str
    layers: List[LayerModel] = field(default_factory=list)
    duration: float = 10.0 # Total duration in seconds
    bg_color: str = "#FAFAF8"
    transition_type: str = None
    transition_duration: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "duration": self.duration,
            "bg_color": self.bg_color,
            "transition_type": self.transition_type,
            "transition_duration": self.transition_duration,
            "layers": [layer.to_dict() for layer in self.layers]
        }
