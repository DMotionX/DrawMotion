import os
import sys

def is_frozen_build() -> bool:
    """Detects whether running as a compiled standalone binary (Nuitka/PyInstaller) or raw Python dev."""
    return (
        getattr(sys, 'frozen', False) or 
        hasattr(sys, '_nuitka_version') or 
        '__compiled__' in globals()
    )

def get_app_data_dir() -> str:
    r"""
    Returns isolated application data directory:
    - Production Build (Installer): %LOCALAPPDATA%\DrawMotion
    - Development Source (Python) : %LOCALAPPDATA%\DrawMotion-Dev
    Creates the directory if it doesn't exist.
    """
    if sys.platform == "win32":
        base_dir = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        app_name = "DrawMotion" if is_frozen_build() else "DrawMotion-Dev"
        app_dir = os.path.join(base_dir, app_name)
    else:
        app_name = ".drawmotion" if is_frozen_build() else ".drawmotion-dev"
        app_dir = os.path.join(os.path.expanduser("~"), app_name)
        
    if not os.path.exists(app_dir):
        os.makedirs(app_dir, exist_ok=True)
        
    return app_dir


def resource_path(relative_path: str) -> str:
    """
    Universal asset path resolver.
    Works correctly in all 3 environments:
    - Development   : uses project root via __file__
    - PyInstaller   : uses sys._MEIPASS temp extraction folder
    - Nuitka        : uses sys.executable directory (assets are next to .exe in .dist)
    """
    # Case 1: PyInstaller — injects _MEIPASS into sys
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS

    # Case 2: Nuitka standalone / frozen binary
    elif '__compiled__' in globals() or getattr(sys, 'frozen', False) or hasattr(sys, '_nuitka_version'):
        base_path = os.path.dirname(os.path.abspath(sys.executable))

    # Case 3: Normal development
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.join(base_path, relative_path)
