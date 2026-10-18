"""
Purpose: Defines the Layer data model.
Features: Contains a list of item models, handles layer visibility, locking, and naming.
Usage Summary: Used within a Scene model to group and order items.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from models.item_models import BaseItemModel

@dataclass
class LayerModel:
    id: str
    name: str
    items: List[BaseItemModel] = field(default_factory=list)
    is_visible: bool = True
    is_locked: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "is_visible": self.is_visible,
            "is_locked": self.is_locked,
            "items": [item.to_dict() for item in self.items]
        }
