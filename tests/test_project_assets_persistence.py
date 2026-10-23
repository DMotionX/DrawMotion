import os
import sys
import shutil
import tempfile
import zipfile
import json
import pytest
from PySide6.QtGui import QPixmap, QColor, QPainter
from PySide6.QtCore import QPointF, QRectF
from core.project_engine.project_manager import ProjectManager
from graphics.animated_image_item import AnimatedImageItem
from utils.paths import get_app_data_dir

def _create_test_pixmap(width=100, height=100, color=QColor(255, 0, 0)):
    pix = QPixmap(width, height)
    pix.fill(color)
    p = QPainter(pix)
    p.setPen(QColor(0, 255, 0))
    p.drawRect(10, 10, 80, 80)
    p.end()
    return pix

class DummyWorkspace:
    def __init__(self):
        self.user_items = []
        self.audio_items = []
        self.artboards = []
        self.current_scene_index = 0
        from PySide6.QtWidgets import QGraphicsScene
        self.scene = QGraphicsScene()
        
        class DummySignal:
            def emit(self, *args): pass
            def connect(self, *args): pass
            def disconnect(self, *args): pass
            
        class DummyEngine:
            def __init__(self):
                self.queue = []
            def sync_queue(self, items, force_recompile=False):
                self.queue = list(items)
            def seek(self, t): pass
            def add_track(self, *args): pass
            def update_track_fx(self, *args): pass

        self.items_changed = DummySignal()
        self.audio_items_changed = DummySignal()
        self.animator_engine = DummyEngine()
        self.audio_engine = DummyEngine()
        
    def clear_all(self):
        self.user_items.clear()
        self.audio_items.clear()
        self.artboards.clear()
        self.scene.clear()
        
    def add_item_to_scene(self, item):
        self.user_items.append(item)
        self.scene.addItem(item)
        
    def update_scene_indices(self):
        pass
        
    def distribute_global_time(self, respect_board_duration=True):
        pass
        
    def focus_on_artboard(self, idx):
        pass
        
    def reset_zoom(self):
        pass
        
    def _on_item_plan_started(self):
        pass
        
    def _on_item_plan_ready(self):
        pass

def test_pack_and_save_direct_file(tmp_path, qapp):
    """Level 1: Image exists directly on disk."""
    ws = DummyWorkspace()
    pm = ProjectManager()
    pm.set_workspace(ws)
    
    # Create image file on disk
    src_img = tmp_path / "sample_disk.png"
    pix = _create_test_pixmap()
    pix.save(str(src_img), "PNG")
    
    # Create item
    item = AnimatedImageItem(pix)
    item.image_path = str(src_img)
    ws.add_item_to_scene(item)
    
    target_wip = str(tmp_path / "project_direct.wip")
    ok = pm.save_project_to_path(target_wip)
    assert ok is True
    assert os.path.exists(target_wip)
    
    # Verify ZIP contents
    with zipfile.ZipFile(target_wip, 'r') as zf:
        namelist = zf.namelist()
        assert "manifest.json" in namelist
        assert "project.json" in namelist
        
        asset_files = [n for n in namelist if n.startswith("assets/") and n.endswith(".png")]
        assert len(asset_files) == 1
        
        proj_data = json.loads(zf.read("project.json"))
        saved_items = proj_data.get("items", [])
        assert len(saved_items) == 1
        assert saved_items[0]["image_path"] == asset_files[0]
        
        manifest_data = json.loads(zf.read("manifest.json"))
        base_asset = os.path.basename(asset_files[0])
        assert base_asset in manifest_data["asset_hashes"]
        assert len(manifest_data["asset_hashes"][base_asset]) == 64

def test_pack_and_save_library_subfolder_fallback(tmp_path, qapp, monkeypatch):
    """Level 2: Image disk path is dead, but exists in library subfolder (e.g. task2)."""
    ws = DummyWorkspace()
    pm = ProjectManager()
    pm.set_workspace(ws)
    
    fake_lib = tmp_path / "assets" / "library"
    task2_dir = fake_lib / "task2"
    task2_dir.mkdir(parents=True)
    
    lib_img = task2_dir / "moved_to_task2.png"
    pix = _create_test_pixmap()
    pix.save(str(lib_img), "PNG")
    
    # Point item to non-existent path
    dead_path = str(tmp_path / "non_existent_folder" / "moved_to_task2.png")
    item = AnimatedImageItem(pix)
    item.image_path = dead_path
    ws.add_item_to_scene(item)
    
    # Mock get_app_data_dir to return tmp_path so it scans fake_lib
    import utils.paths
    monkeypatch.setattr(utils.paths, "get_app_data_dir", lambda: str(tmp_path))
    
    target_wip = str(tmp_path / "project_lib_fallback.wip")
    ok = pm.save_project_to_path(target_wip)
    assert ok is True
    
    with zipfile.ZipFile(target_wip, 'r') as zf:
        asset_files = [n for n in zf.namelist() if n.startswith("assets/") and "moved_to_task2.png" in n]
        assert len(asset_files) == 1

def test_pack_and_save_in_memory_pixmap_fallback(tmp_path, qapp):
    """Level 3: Image is deleted everywhere from disk, extracted live from RAM."""
    ws = DummyWorkspace()
    pm = ProjectManager()
    pm.set_workspace(ws)
    
    dead_path = str(tmp_path / "completely_deleted.png")
    assert not os.path.exists(dead_path)
    
    pix = _create_test_pixmap(120, 80, QColor(0, 0, 255))
    item = AnimatedImageItem(pix)
    item.image_path = dead_path
    ws.add_item_to_scene(item)
    
    target_wip = str(tmp_path / "project_ram_fallback.wip")
    ok = pm.save_project_to_path(target_wip)
    assert ok is True
    
    with zipfile.ZipFile(target_wip, 'r') as zf:
        asset_files = [n for n in zf.namelist() if n.startswith("assets/") and "completely_deleted.png" in n]
        assert len(asset_files) == 1
        
        # Verify extracted image from RAM is valid PNG
        extracted_bytes = zf.read(asset_files[0])
        restored_pix = QPixmap()
        restored_pix.loadFromData(extracted_bytes, "PNG")
        assert not restored_pix.isNull()
        assert restored_pix.width() == 120
        assert restored_pix.height() == 80

def test_load_project_file_smart_resolver_and_instant_visibility(tmp_path, qapp):
    """Load project restores images, ensures valid pixmap, triggers async plan, and sets progress 1.0."""
    ws = DummyWorkspace()
    pm = ProjectManager()
    pm.set_workspace(ws)
    
    src_img = tmp_path / "test_load_item.png"
    pix = _create_test_pixmap(150, 150)
    pix.save(str(src_img), "PNG")
    
    item = AnimatedImageItem(pix)
    item.image_path = str(src_img)
    ws.add_item_to_scene(item)
    
    target_wip = str(tmp_path / "project_roundtrip.wip")
    pm.save_project_to_path(target_wip)
    
    # Clear workspace
    ws.clear_all()
    assert len(ws.user_items) == 0
    
    # Load back
    errs = []
    pm.project_error.connect(lambda msg: errs.append(msg))
    ok = pm.load_project_file(target_wip)
    assert ok is True, f"Failed with errors: {errs}"
    assert len(ws.user_items) == 1
    
    loaded_item = ws.user_items[0]
    assert loaded_item._pixmap is not None
    assert not loaded_item._pixmap.isNull()
    assert loaded_item._progress == 1.0  # Instant visual rendering, no blank screen!


def test_self_healing_loader_for_moved_library_assets(tmp_path, qapp, monkeypatch):
    """
    Directly tests that if an old project references an asset that was moved
    to a subfolder (like task2/), load_project_file self-heals and locates the asset.
    """
    ws = DummyWorkspace()
    pm = ProjectManager()
    pm.set_workspace(ws)
    
    # Setup library with subfolder task2
    fake_lib = tmp_path / "assets" / "library"
    task2_dir = fake_lib / "task2"
    task2_dir.mkdir(parents=True)
    
    img_name = "01_welcome_fekra_code.png"
    real_disk_path = task2_dir / img_name
    pix = _create_test_pixmap(200, 200, QColor(255, 128, 0))
    pix.save(str(real_disk_path), "PNG")
    
    # Mock get_app_data_dir to point to tmp_path
    import utils.paths
    monkeypatch.setattr(utils.paths, "get_app_data_dir", lambda: str(tmp_path))
    
    # Manually craft a project WIP mimicking test.wip where asset was moved
    wip_path = str(tmp_path / "legacy_test.wip")
    old_dead_path = str(fake_lib / img_name) # File does not exist here directly!
    assert not os.path.exists(old_dead_path)
    
    project_data = {
        "canvas": {"width": 1920, "height": 1080, "background_color": "#ffffff"},
        "artboards": [{"width": 1920, "height": 1080, "x": 0, "y": 0}],
        "items": [
            {
                "type": "AnimatedImageItem",
                "image_path": old_dead_path,
                "x": 100,
                "y": 100,
                "scale": 1.0,
                "rotation": 0,
                "opacity": 1.0
            }
        ],
        "audio": []
    }
    manifest_data = {
        "schema_version": 1,
        "app_version": "1.7.11",
        "project_name": "legacy_test",
        "asset_hashes": {}
    }
    
    with zipfile.ZipFile(wip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.json", json.dumps(project_data))
        zf.writestr("manifest.json", json.dumps(manifest_data))
        
    # Now load legacy_test.wip
    ok = pm.load_project_file(wip_path)
    assert ok is True
    assert len(ws.user_items) == 1
    
    recovered_item = ws.user_items[0]
    assert recovered_item._pixmap is not None
    assert not recovered_item._pixmap.isNull()
    assert recovered_item._pixmap.width() == 200
    assert recovered_item.image_path == os.path.normpath(str(real_disk_path))

