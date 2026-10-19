import json
import os
import shutil
import uuid
import hashlib
from PySide6.QtGui import QPainterPath, QColor
from PySide6.QtCore import QPointF

SCHEMA_VERSION = 1
APP_VERSION = "1.7.11" # Current target version

class SerializerEngine:
    """
    Handles extracting the state from the application's engines and items, 
    and serializing it into the standard DrawMotion Project (WIP) format.
    This operates strictly as an observer (Read-Only).
    """
    
    @staticmethod
    def generate_hash(filepath: str) -> str:
        """ Generate SHA-256 hash for asset integrity. """
        hasher = hashlib.sha256()
        try:
            with open(filepath, 'rb') as afile:
                buf = afile.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = afile.read(65536)
            return hasher.hexdigest()
        except Exception:
            return ""

    @staticmethod
    def serialize_path(path: QPainterPath) -> list:
        """ Extract elements from a QPainterPath into a serializable JSON list. """
        elements = []
        for i in range(path.elementCount()):
            el = path.elementAt(i)
            el_type = int(el.type) # 0=MoveTo, 1=LineTo, 2=CurveTo, 3=CurveToData
            elements.append({
                "type": el_type,
                "x": el.x,
                "y": el.y
            })
        return elements

    @staticmethod
    def deserialize_path(elements: list) -> QPainterPath:
        """ Reconstruct a QPainterPath from a JSON list of elements. """
        path = QPainterPath()
        i = 0
        while i < len(elements):
            el = elements[i]
            etype = el["type"]
            if etype == 0:
                path.moveTo(el["x"], el["y"])
                i += 1
            elif etype == 1:
                path.lineTo(el["x"], el["y"])
                i += 1
            elif etype == 2: # CurveTo Element (Start of Cubic)
                # A cubic curve in Qt consists of 1 CurveToElement (CP1) + 2 CurveToDataElements (CP2, EP)
                if i + 2 < len(elements) and elements[i+1]["type"] == 3 and elements[i+2]["type"] == 3:
                    path.cubicTo(
                        el["x"], el["y"],
                        elements[i+1]["x"], elements[i+1]["y"],
                        elements[i+2]["x"], elements[i+2]["y"]
                    )
                    i += 3
                else:
                    path.lineTo(el["x"], el["y"])
                    i += 1
            else:
                i += 1
        return path

    @staticmethod
    def serialize_workspace(workspace) -> dict:
        """
        Extracts the state of the workspace without modifying it.
        Uses Read-Only inspection of `user_items` and `audio_items`.
        Returns the data structure ready to be wrapped in a manifest.
        """
        data = {
            "canvas": {
                "width": 1920, # Dynamic based on actual canvas size later
                "height": 1080,
                "background_color": "#ffffff"
            },
            "items": [],
            "audio": [],
            "artboards": []
        }
        
        # Serialize user items (Text, Image, Stroke)
        for item in getattr(workspace, 'user_items', []):
            if hasattr(item, 'to_dict'):
                item_dict = item.to_dict()
                parent_ab = item.parentItem()
                if parent_ab in getattr(workspace, 'artboards', []):
                    item_dict['scene_index'] = workspace.artboards.index(parent_ab)
                else:
                    item_dict['scene_index'] = 0
                data["items"].append(item_dict)
                
        # Serialize audio items
        for node in getattr(workspace, 'audio_items', []):
            if hasattr(node, 'to_dict'):
                data["audio"].append(node.to_dict())
                
        # Serialize Artboards
        for ab in getattr(workspace, 'artboards', []):
            data["artboards"].append({
                "width": ab.rect().width(),
                "height": ab.rect().height(),
                "x": ab.pos().x(),
                "y": ab.pos().y(),
                "duration":            getattr(ab, 'duration', 0.0),
                "transition_type":     getattr(ab, 'transition_type', None),
                "transition_duration": getattr(ab, 'transition_duration', 1.0),
                "transition_color":    getattr(ab, 'transition_color', '#000000')
            })

            
        return data

    @classmethod
    def bundle_project(cls, workspace, project_name: str, dest_dir: str):
        """
        Phase 3/4: Generates the .wip container logic.
        (This will be expanded to create a ZIP and copy assets, generating Manifest)
        """
        state = cls.serialize_workspace(workspace)
        
        from datetime import datetime
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "app_version": APP_VERSION,
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "asset_hashes": {}
        }
        
        return {"manifest": manifest, "project": state}
