import os
import sys
import json
import shutil
import uuid
import zipfile
import tempfile
from PySide6.QtCore import QObject, Signal, QTimer, QSettings
from core.serialization.serializer import SerializerEngine
from core.settings_manager import SettingsManager

class ProjectManager(QObject):
    """
    Handles creating, saving, loading, and deleting project folders inside AppData.
    Implements Phase 3 (WIP Format, Atomic Save) and Phase 5 (Auto-Save, Crash Recovery).
    Operates without modifying existing drawing/writing engines.
    """
    project_saved = Signal(str)
    project_loaded = Signal(str)
    project_error = Signal(str)
    recovery_found = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.app_data_dir = self._get_app_data_dir()
        
        custom_path = SettingsManager().get("default_project_path", "")
        if custom_path and os.path.exists(custom_path):
            self.projects_dir = custom_path
        else:
            self.projects_dir = os.path.join(self.app_data_dir, "Projects")
            

        self.cache_dir = os.path.join(self.app_data_dir, "Cache")
        self.recovery_file = os.path.join(self.cache_dir, "recovery.wip")
        
        # Ensure directories exist
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.workspace = None
        self.current_project_filepath = None
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save_project)
        
        # Check for crash recovery on startup
        if os.path.exists(self.recovery_file):
            # Using QTimer.singleShot to allow UI to load before emitting
            QTimer.singleShot(1000, self.recovery_found.emit)

    def set_workspace(self, workspace):
        self.workspace = workspace
        self.update_auto_save_timer()
        # Listen to settings changes so auto-save updates instantly
        SettingsManager().settings_changed.connect(self._on_settings_changed)
        
    def _on_settings_changed(self, key, value):
        if key in ("auto_save_enabled", "auto_save_interval"):
            self.update_auto_save_timer()
        elif key == "default_project_path":
            custom_path = value
            if custom_path and os.path.exists(custom_path):
                self.projects_dir = custom_path
            else:
                self.projects_dir = os.path.join(self.app_data_dir, "Projects")
            os.makedirs(self.projects_dir, exist_ok=True)
        
    def update_auto_save_timer(self):
        settings = SettingsManager()
        is_enabled = settings.get("auto_save_enabled")
        
        if not is_enabled:
            self.auto_save_timer.stop()
            return
            
        # SettingsManager stores interval directly as minutes (e.g., 5)
        minutes = int(settings.get("auto_save_interval"))
        if minutes <= 0:
            minutes = 5
        self.auto_save_timer.start(minutes * 60 * 1000)

    def _get_app_data_dir(self):
        """Returns a safe, hidden AppData directory for the application."""
        app_name = "DrawMotion"
        if sys.platform == "win32":
            return os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), app_name)
        elif sys.platform == "darwin":
            return os.path.join(os.path.expanduser("~"), "Library", "Application Support", app_name)
        else:
            return os.path.join(os.path.expanduser("~"), ".local", "share", app_name)
    def get_cache_size(self):
        total_size = 0
        for dirpath, _, filenames in os.walk(self.cache_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    def get_projects_size(self):
        total_size = 0
        for dirpath, _, filenames in os.walk(self.projects_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    def clear_cache(self):
        """Deletes all files in the cache directory."""
        try:
            for item in os.listdir(self.cache_dir):
                item_path = os.path.join(self.cache_dir, item)
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            return True
        except Exception as e:
            self.project_error.emit(f"Failed to clear cache: {e}")
            return False
            
    def clear_all_projects(self):
        """Deletes all projects completely."""
        try:
            for item in os.listdir(self.projects_dir):
                item_path = os.path.join(self.projects_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                elif os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
            return True
        except Exception as e:
            self.project_error.emit(f"Failed to clear projects: {e}")
            return False
            
    def get_cache_size(self):
        """Returns the total cache size in bytes."""
        total_size = 0
        for dirpath, _, filenames in os.walk(self.cache_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size
        
    def get_projects_size(self):
        """Returns the total projects size in bytes."""
        total_size = 0
        for dirpath, _, filenames in os.walk(self.projects_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    def list_projects(self):
        """Returns a list of saved .wip projects metadata."""
        projects = []
        if not os.path.exists(self.projects_dir):
            return projects
            
        for d in os.listdir(self.projects_dir):
            if d.endswith(".wip"):
                wip_path = os.path.join(self.projects_dir, d)
                try:
                    with zipfile.ZipFile(wip_path, 'r') as zipf:
                        if 'manifest.json' in zipf.namelist():
                            with zipf.open('manifest.json') as mf:
                                manifest = json.load(mf)
                                projects.append({
                                    "id": d,
                                    "name": manifest.get("project_name", d),
                                    "path": wip_path,
                                    "created_at": manifest.get("created_at", "")
                                })
                except Exception:
                    pass # Ignore corrupted zips
        return projects

    def delete_project(self, project_id):
        proj_path = os.path.join(self.projects_dir, project_id)
        if os.path.exists(proj_path):
            try:
                os.remove(proj_path)
                return True
            except Exception as e:
                self.project_error.emit(f"Failed to delete project {project_id}: {e}")
                return False
        return False

    def _pack_and_save(self, target_filepath: str, project_name: str, is_auto_save: bool = False):
        """
        Internal method to serialize and create a .wip file with Atomic Save.
        """
        if not self.workspace: return False
        if not self.workspace.user_items and not self.workspace.audio_items:
            return False

        # Use a temporary directory to gather files
        with tempfile.TemporaryDirectory() as temp_dir:
            assets_dir = os.path.join(temp_dir, "assets")
            os.makedirs(assets_dir, exist_ok=True)
            
            # Extract state using Read-Only SerializerEngine
            bundle = SerializerEngine.bundle_project(self.workspace, project_name, temp_dir)
            project_data = bundle["project"]
            manifest_data = bundle["manifest"]
            
            def _get_safe_asset_name(src_path):
                base = os.path.basename(src_path)
                # Check if it already has a 32-char hex UUID prefix
                if len(base) > 33 and base[32] == '_' and all(c in '0123456789abcdefABCDEF' for c in base[:32]):
                    return base
                return f"{uuid.uuid4().hex}_{base}"

            # Process Asset Hashing and Copying safely
            for item in project_data.get("items", []):
                if 'image_path' in item and item['image_path'] and os.path.exists(item['image_path']):
                    src_path = item['image_path']
                    asset_name = _get_safe_asset_name(src_path)
                    dest_path = os.path.join(assets_dir, asset_name)
                    shutil.copy2(src_path, dest_path)
                    
                    item['image_path'] = f"assets/{asset_name}"
                    manifest_data["asset_hashes"][asset_name] = SerializerEngine.generate_hash(dest_path)

            for node in project_data.get("audio", []):
                if 'file_path' in node and node['file_path'] and os.path.exists(node['file_path']):
                    src_path = node['file_path']
                    asset_name = _get_safe_asset_name(src_path)
                    dest_path = os.path.join(assets_dir, asset_name)
                    shutil.copy2(src_path, dest_path)
                    
                    node['file_path'] = f"assets/{asset_name}"
                    manifest_data["asset_hashes"][asset_name] = SerializerEngine.generate_hash(dest_path)
            
            # Write JSON files to temp dir
            with open(os.path.join(temp_dir, "project.json"), 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=4)
                
            with open(os.path.join(temp_dir, "manifest.json"), 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=4)
                
            # Phase 3: Atomic Save Implementation
            temp_zip_path = target_filepath + ".tmp"
            
            try:
                # Zip the temp_dir into the .tmp file
                with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(temp_dir):
                        for file in files:
                            abs_path = os.path.join(root, file)
                            rel_path = os.path.relpath(abs_path, temp_dir)
                            zipf.write(abs_path, rel_path)
                            
                # Verify integrity
                if os.path.getsize(temp_zip_path) > 0:
                    # Rename securely (Atomic Replace)
                    if os.path.exists(target_filepath):
                        os.remove(target_filepath) # Windows requires explicit removal before rename sometimes
                    os.rename(temp_zip_path, target_filepath)
                    
                    if not is_auto_save:
                        self.project_saved.emit(project_name)
                    return True
            except Exception as e:
                if os.path.exists(temp_zip_path):
                    os.remove(temp_zip_path)
                if not is_auto_save:
                    self.project_error.emit(f"Failed to save project: {e}")
                return False

    def auto_save_project(self):
        """ Silent background save. """
        self._pack_and_save(self.recovery_file, "AutoSave Recovery", is_auto_save=True)

    def save_project(self, project_name):
        """ Explicit user save into the Projects directory (Fallback). """
        import datetime
        safe_name = "".join(c for c in project_name if c.isalnum() or c in " _-").strip()
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{safe_name}_{timestamp}.wip"
        target_path = os.path.join(self.projects_dir, filename)
        
        ok = self._pack_and_save(target_path, project_name)
        if ok:
            self.current_project_filepath = target_path
        return ok

    def save_project_to_path(self, target_filepath: str):
        """ Save project directly to a specific filepath chosen by the user. """
        project_name = os.path.splitext(os.path.basename(target_filepath))[0]
        ok = self._pack_and_save(target_filepath, project_name)
        if ok:
            self.current_project_filepath = target_filepath
        return ok

    def recover_crash(self):
        """ Load the crash recovery file if it exists. """
        if os.path.exists(self.recovery_file):
            res = self.load_project_file(self.recovery_file)
            if res:
                # Cleanup the recovery file after successful load
                os.remove(self.recovery_file)
            return res
        return False
        
    def discard_crash_recovery(self):
        """ Delete the crash recovery file if the user chooses not to restore. """
        self.cleanup_recovery()
        
    def cleanup_recovery(self):
        """ Silently remove the recovery file on normal graceful exit. """
        if os.path.exists(self.recovery_file):
            try:
                os.remove(self.recovery_file)
            except Exception as e:

                self.project_error.emit(f"Failed to delete recovery file: {e}")

    def load_project_file(self, wip_filepath: str):
        """
        Phase 2: Loads a `.wip` file, validates manifest, and restores objects to the Workspace.
        """
        if not os.path.exists(wip_filepath):
            self.project_error.emit("Project file not found.")
            return False
            
        try:
            # We extract it to Cache temporarily to load assets
            extract_dir = os.path.join(self.cache_dir, "ActiveProject")
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(wip_filepath, 'r') as zipf:
                zipf.extractall(extract_dir)
                
            manifest_path = os.path.join(extract_dir, "manifest.json")
            project_path = os.path.join(extract_dir, "project.json")
            
            if not os.path.exists(project_path) or not os.path.exists(manifest_path):
                raise Exception("Corrupt WIP file: missing JSON files.")
                
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
                
            with open(project_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Clear current workspace
            self.workspace.clear_all()
            
            # 1. Reconstruct Artboards FIRST (Fix Catastrophic Bug)
            for ab_data in data.get("artboards", []):
                from graphics.artboard_item import SceneArtboardItem
                from PySide6.QtCore import QRectF
                
                # Instantiate new artboard
                rect = QRectF(0, 0, ab_data.get("width", 1920), ab_data.get("height", 1080))
                ab = SceneArtboardItem(rect)
                ab.setPos(ab_data.get("x", 0), ab_data.get("y", 0))
                
                # Restore properties
                ab.transition_type     = ab_data.get("transition_type", None)
                ab.transition_duration = ab_data.get("transition_duration", 1.0)
                ab.transition_color    = ab_data.get("transition_color", "#000000")
                ab.duration            = ab_data.get("duration", 0.0)
                
                # Add to scene
                self.workspace.scene.addItem(ab)
                self.workspace.artboards.append(ab)
                
            self.workspace.update_scene_indices()
            
            # 2. Reconstruct items (Now safe because Artboards exist)
            for idata in data.get("items", []):
                item_type = idata.get("type")
                scene_idx = idata.get("scene_index", 0)
                
                # Temporarily switch active scene so add_item_to_scene places it correctly
                if scene_idx < len(self.workspace.artboards):
                    self.workspace.current_scene_index = scene_idx
                    
                if item_type == "AnimatedImageItem":
                    if 'image_path' in idata:
                        idata['image_path'] = os.path.join(extract_dir, idata['image_path'])
                    from graphics.animated_image_item import AnimatedImageItem
                    item = AnimatedImageItem.from_dict(idata)
                    self.workspace.add_item_to_scene(item)
                    
                    # EditableTextNode was deprecated and removed.
                elif item_type == "AnimatedStrokeItem":
                    from graphics.animated_stroke_item import AnimatedStrokeItem
                    item = AnimatedStrokeItem.from_dict(idata)
                    self.workspace.add_item_to_scene(item)
                    
                elif item_type == "WriteToImageGraphicsItem":
                    if 'image_path' in idata and idata['image_path']:
                        idata['image_path'] = os.path.join(extract_dir, idata['image_path'])
                    from components.write_to_image.graphics_item import WriteToImageGraphicsItem
                    item = WriteToImageGraphicsItem.from_dict(idata)
                    item.canvas_workspace = self.workspace
                    self.workspace.add_item_to_scene(item)
                    
                elif item_type == "SVGCanvasItem":
                    if 'svg_filepath' in idata and idata['svg_filepath']:
                        idata['svg_filepath'] = os.path.join(extract_dir, idata['svg_filepath'])
                    from asset_library.engine.svg_canvas_item import SVGCanvasItem
                    item = SVGCanvasItem.from_dict(idata)
                    self.workspace.add_item_to_scene(item)
                    
                elif item_type == "AnimatedRasterItem":
                    if 'image_path' in idata and idata['image_path']:
                        idata['image_path'] = os.path.join(extract_dir, idata['image_path'])
                    from core.drawing_engine.raster_engine.raster_item import AnimatedRasterItem
                    item = AnimatedRasterItem.from_dict(idata)
                    self.workspace.add_item_to_scene(item)
            
            # Reset active scene to the first one after loading
            self.workspace.current_scene_index = 0
            if self.workspace.artboards:
                self.workspace.focus_on_artboard(0)
                    
            # 3. Reconstruct audio
            for adata in data.get("audio", []):
                if 'file_path' in adata:
                    adata['file_path'] = os.path.join(extract_dir, adata['file_path'])
                from core.audio_engine.audio_node import AudioNodeModel
                node = AudioNodeModel.from_dict(adata)
                self.workspace.audio_items.append(node)
                if hasattr(self.workspace, 'audio_engine'):
                    # Audio Plugins Application
                    vol = 1.0
                    if hasattr(node, 'audio_fx_settings') and isinstance(node.audio_fx_settings, dict):
                        vol = node.audio_fx_settings.get("volume", 100) / 100.0
                    self.workspace.audio_engine.add_track(node.file_path, node.anim_delay, vol)
                    if hasattr(node, 'audio_fx_settings') and isinstance(node.audio_fx_settings, dict):
                        self.workspace.audio_engine.update_track_fx(node.file_path, node.audio_fx_settings)            
            self.workspace.items_changed.emit(self.workspace.user_items)
            self.workspace.audio_items_changed.emit(self.workspace.audio_items)
            
            # CRITICAL FIX: Distribute times so camera scene_windows are generated correctly
            # respect_board_duration=True ensures we don't accidentally shrink scenes below user's desired duration
            self.workspace.distribute_global_time(respect_board_duration=True)
            
            # Make all loaded items immediately visible safely without breaking the global timer
            self.workspace.animator_engine.sync_queue(self.workspace.user_items, force_recompile=True)
            self.workspace.animator_engine.seek(0.0) # Reset time to 0
            
            # Make elements visible
            for current_item in self.workspace.animator_engine.queue:
                is_image = "AnimatedImageItem" in current_item.__class__.__name__ or "SVGCanvasItem" in current_item.__class__.__name__ or "WriteToImageGraphicsItem" in current_item.__class__.__name__ or "MindMap" in current_item.__class__.__name__
                max_progress = 1.0 if is_image else 2.0
                current_item.set_progress(max_progress)
            
            self.project_loaded.emit(manifest.get("project_name", "Recovered Project"))
            
            self.workspace.reset_zoom()
            self.current_project_filepath = os.path.normpath(wip_filepath)
            return True
            
        except Exception as e:
            self.project_error.emit(f"Failed to load WIP project: {e}")
            return False
