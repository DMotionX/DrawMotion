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
    algorithm_style: str = "linear"
    # Selected text effect
    text_effect: str = "none"
    
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
            "text_effect": self.text_effect
        })
        return data
