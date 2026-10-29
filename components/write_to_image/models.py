from dataclasses import dataclass
from models.item_models import BaseItemModel
from typing import Dict, Any

@dataclass
class WriteToImageModel(BaseItemModel):
    text: str = ""
    font_family: str = "Arial"
    font_size: int = 24
    color: str = "#2A322E"
    is_bold: bool = False
    is_italic: bool = False
    is_underline: bool = False
    
    # SVG Original Dimensions
    width: float = 0.0
    height: float = 0.0
    
    # Path to the cached rasterized text
    image_path: str = ""
    
    # Selected drawing algorithm
    algorithm_style: str = "realistic_hybrid"
    writing_algorithm: str = "realistic_hybrid"
    # Selected text effect
    text_effect: str = "none"
    
    # Selected writing hand configuration
    writing_hand_type: str = "right"
    writing_hand_style: str = "default"
    writing_hand_size: float = 1.0

    # Alignment: "auto", "left", "center", "right"
    text_align: str = "auto"
    
    def __post_init__(self):
        self.item_type = "write_to_image"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "text": self.text,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "color": self.color,
            "is_bold": self.is_bold,
            "is_italic": self.is_italic,
            "is_underline": self.is_underline,
            "width": self.width,
            "height": self.height,
            "image_path": self.image_path,
            "algorithm_style": self.algorithm_style,
            "writing_algorithm": self.writing_algorithm,
            "text_effect": self.text_effect,
            "writing_hand_type": self.writing_hand_type,
            "writing_hand_style": self.writing_hand_style,
            "writing_hand_size": self.writing_hand_size,
            "text_align": self.text_align
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WriteToImageModel":
        flat_data = {k: v for k, v in data.items() if k not in ['transform', 'appearance', 'timing', 'type']}
        if 'transform' in data:
            flat_data['pos_x'] = data['transform'].get('x', 0.0)
            flat_data['pos_y'] = data['transform'].get('y', 0.0)
            flat_data['scale_w'] = data['transform'].get('scale_w', 1.0)
            flat_data['scale_h'] = data['transform'].get('scale_h', 1.0)
            flat_data['rotation'] = data['transform'].get('rotation', 0.0)
        if 'appearance' in data:
            flat_data['opacity'] = data['appearance'].get('opacity', 1.0)
            flat_data['blend_mode'] = data['appearance'].get('blend_mode', 'normal')
        if 'timing' in data:
            flat_data['start_time'] = data['timing'].get('start', 0.0)
            flat_data['duration'] = data['timing'].get('duration', 1.0)
            flat_data['delay'] = data['timing'].get('delay', 0.0)
        return cls(**flat_data)


