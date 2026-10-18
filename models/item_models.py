"""
Purpose: Defines the core data structures (Models) for all animatable items.
Features: Base Item class, specialized classes (Text, Image, SVG) with properties independent of UI.
Usage Summary: Instantiate these data classes to represent elements in a layer. They will be serialized for saving/loading.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class AnimationCurve:
    name: str = "linear" # linear, ease-in, ease-out, ease-in-out
    # Additional curve parameters if needed

@dataclass
class BaseItemModel:
    id: str
    name: str
    item_type: str = "base"
    start_time: float = 0.0
    duration: float = 2.0
    delay: float = 0.0
    
    # Transform
    pos_x: float = 0.0
    pos_y: float = 0.0
    scale_w: float = 1.0
    scale_h: float = 1.0
    rotation: float = 0.0
    
    # Appearance
    opacity: float = 1.0
    blend_mode: str = "normal"
    
    # Animation specific
    draw_progress: float = 1.0 # 0.0 to 1.0
    animation_curve: AnimationCurve = field(default_factory=AnimationCurve)
    
    # SFX
    sfx_name: str = "None"
    sfx_volume: int = 100
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.item_type,
            "sfx_name": self.sfx_name,
            "sfx_volume": self.sfx_volume,
            "transform": {
                "x": self.pos_x,
                "y": self.pos_y,
                "scale_w": self.scale_w,
                "scale_h": self.scale_h,
                "rotation": self.rotation
            },
            "appearance": {
                "opacity": self.opacity,
                "blend_mode": self.blend_mode
            },
            "timing": {
                "start": self.start_time,
                "duration": self.duration,
                "delay": self.delay
            }
        }

@dataclass
class TextItemModel(BaseItemModel):
    text: str = ""
    font_family: str = "Arial"
    font_size: int = 48
    fill_color: str = "#000000"
    stroke_color: str = "#000000"
    stroke_width: float = 1.0
    
    def __post_init__(self):
        self.item_type = "text"
        
@dataclass
class ImageItemModel(BaseItemModel):
    file_path: str = ""
    is_traced: bool = False # If True, it acts like SVG strokes
    
    def __post_init__(self):
        self.item_type = "image"

@dataclass
class SvgItemModel(BaseItemModel):
    file_path: str = ""
    stroke_color: Optional[str] = None # Override if needed
    
    def __post_init__(self):
        self.item_type = "svg"
