# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Purpose: Project management engine.
Features: Handles saving and loading of DrawMotion project files (.wip ZIP archives containing project.json, assets, and fonts).
Usage Summary: Instantiate ProjectManager and call save_project() or load_project() with the desired path.
"""
import json
import zipfile
import os
import shutil
import tempfile
from typing import Dict, Any, Optional
from models.scene import SceneModel
from utils.paths import get_app_data_dir

class ProjectManager:
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = project_path
        self.project_data: Dict[str, Any] = {
            "version": "1.0",
            "scenes": []
        }
        self.scenes: list[SceneModel] = []
        
    def add_scene(self, scene: SceneModel):
        self.scenes.append(scene)

    def save_project(self, save_path: str):
        """Saves the project state and assets to a .wip (DrawMotion Project) ZIP archive."""
        self.project_path = save_path
        
        # Serialize scenes
        self.project_data["scenes"] = [scene.to_dict() for scene in self.scenes]
        
        # Create a temporary directory in AppData for organizing files before zipping
        app_data_dir = get_app_data_dir()
        temp_dir = os.path.join(app_data_dir, "temp_project_build")
        
        # Clean up existing temp dir if any
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Write project.json
            with open(os.path.join(temp_dir, "project.json"), "w", encoding="utf-8") as f:
                json.dump(self.project_data, f, ensure_ascii=False, indent=4)
                
            # Create required standard directories
            os.makedirs(os.path.join(temp_dir, "assets"), exist_ok=True)
            os.makedirs(os.path.join(temp_dir, "fonts"), exist_ok=True)
            
            # Zip the directory contents
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
        except Exception as e:
            print(f"Error saving project: {e}")
            raise
        finally:
            # Always cleanup the temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def load_project(self, load_path: str) -> bool:
        """Loads a .wip (DrawMotion Project) file and extracts its data."""
        if not os.path.exists(load_path) or not zipfile.is_zipfile(load_path):
            return False
            
        self.project_path = load_path
        temp_dir = tempfile.mkdtemp(dir=get_app_data_dir(), prefix="project_extract_")
        
        try:
            with zipfile.ZipFile(load_path, 'r') as zipf:
                zipf.extractall(temp_dir)
                
            json_path = os.path.join(temp_dir, "project.json")
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    self.project_data = json.load(f)
                    
            # TODO: Load assets and reconstruct models from self.project_data
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
        return True
