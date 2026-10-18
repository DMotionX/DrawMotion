from dataclasses import dataclass, field
from models.item_models import BaseItemModel
from typing import Dict, Any, List

@dataclass
class MindMapNodeModel(BaseItemModel):
    shape_type: str = "rect" # rect, circle, ellipse
    text: str = "Idea"
    fill_color: str = "#ffffff"
    stroke_color: str = "#2A322E"
    text_color: str = "#000000"
    font_size: int = 16
    
    # Store dimensions because it can be resized
    width: float = 120.0
    height: float = 60.0
    
    def __post_init__(self):
        self.item_type = "mind_map_node"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "shape_type": self.shape_type,
            "text": self.text,
            "fill_color": self.fill_color,
            "stroke_color": self.stroke_color,
            "text_color": self.text_color,
            "font_size": self.font_size,
            "width": self.width,
            "height": self.height
        })
        return data

@dataclass
class MindMapLinkModel(BaseItemModel):
    source_node_id: str = ""
    target_node_id: str = ""
    color: str = "#2A322E"
    thickness: float = 2.0
    
    def __post_init__(self):
        self.item_type = "mind_map_link"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "color": self.color,
            "thickness": self.thickness
        })
        return data
