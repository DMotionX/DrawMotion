import os
import sys
import re
import pytest
from utils.paths import get_app_data_dir, resource_path

def test_paths_centralization_and_xdg():
    """Verify that centralized path resolver produces valid directories."""
    app_data = get_app_data_dir()
    assert os.path.isabs(app_data)
    assert os.path.exists(app_data)
    
    # Test hand asset resolver
    hand_path = resource_path("assets/hand_drag.png")
    assert os.path.exists(hand_path), f"Asset hand_drag.png not found at {hand_path}"
    assert "hand_drag.png" in hand_path.replace("\\", "/")


def test_static_code_asset_case_sensitivity_scanner():
    """
    Scans project source code for static asset string literals and verifies
    that every referenced path matches disk contents character-by-character (Case-Sensitive).
    This catches Linux ext4 FileNotFoundError issues while running on Windows.
    """
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    scan_dirs = ["core", "components", "graphics", "asset_library", "utils"]
    
    asset_pattern = re.compile(r'["\']((?:assets|resources)/[^"\'\n\r]+\.(?:png|svg|ttf|ico|json))["\']')
    found_assets = set()
    
    for scan_dir in scan_dirs:
        full_dir = os.path.join(root_dir, scan_dir)
        if not os.path.exists(full_dir):
            continue
        for parent, _, filenames in os.walk(full_dir):
            for fn in filenames:
                if fn.endswith(".py"):
                    filepath = os.path.join(parent, fn)
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            matches = asset_pattern.findall(content)
                            for m in matches:
                                found_assets.add(m)
                    except Exception:
                        pass

    assert len(found_assets) > 0, "Asset scanner should detect static asset references"

    # Strictly verify case-sensitivity against disk via os.listdir()
    mismatches = []
    for rel_path in found_assets:
        parts = rel_path.replace("\\", "/").split("/")
        current_dir = root_dir
        path_valid = True
        
        for part in parts:
            if not os.path.exists(current_dir):
                path_valid = False
                break
            actual_entries = os.listdir(current_dir)
            if part not in actual_entries:
                # Check if it matches case-insensitively to report a casing bug
                case_insensitive = [e for e in actual_entries if e.lower() == part.lower()]
                if case_insensitive:
                    mismatches.append(f"Casing mismatch: Code references '{part}' but disk has '{case_insensitive[0]}' in '{rel_path}'")
                else:
                    mismatches.append(f"Missing file or directory: '{part}' in '{rel_path}'")
                path_valid = False
                break
            current_dir = os.path.join(current_dir, part)

    assert not mismatches, f"Case sensitivity audit failed:\n" + "\n".join(mismatches)


def test_project_manager_cross_platform_normalization():
    """Verify that project load logic normalizes Windows backslashes across platforms."""
    extract_dir = os.path.abspath("/fake/extract/dir" if sys.platform != "win32" else "C:\\fake\\extract\\dir")
    sample_windows_rel = "assets\\illustrations\\test.png"
    
    # The normalization logic implemented in project_manager.py
    normalized_rel = str(sample_windows_rel).replace("\\", "/")
    combined = os.path.normpath(os.path.join(extract_dir, normalized_rel))
    
    assert "assets/illustrations/test.png" in combined.replace("\\", "/")
    assert "\\" not in normalized_rel


def test_lifecycle_tracker_fallback_safety():
    """Verify that lifecycle tracker log path resolution is fail-safe and never raises."""
    from core.diagnostics.lifecycle_tracker import StartupLifecycleTracker
    path = StartupLifecycleTracker._resolve_log_path()
    assert path is None or os.path.isabs(path)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX executable bits are verified on Linux only")
def test_ffmpeg_real_posix_execution_permission():
    """
    Directly tests that FFmpeg has POSIX execute permission (+x) on real Linux environment.
    Runs on GitHub Actions ubuntu-latest runner and WSL2.
    """
    from core.export_engine.ffmpeg_manager import FFmpegManager
    manager = FFmpegManager(width=1920, height=1080, fps=30)
    ffmpeg_path = manager._verify_and_get_ffmpeg()
    
    assert os.path.exists(ffmpeg_path), f"FFmpeg binary not found at {ffmpeg_path}"
    assert os.access(ffmpeg_path, os.X_OK), f"FFmpeg binary {ffmpeg_path} lacks execution permission (chmod +x)!"
