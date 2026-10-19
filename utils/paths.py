import os
import sys

def is_frozen_build() -> bool:
    """
    Detects whether running as a compiled standalone binary (Nuitka/PyInstaller) or raw Python dev.
    Checks sys.frozen, builtins.__compiled__, sys.__nuitka_version__, and executable filename.
    """
    import builtins

    if getattr(sys, 'frozen', False):
        return True

    if hasattr(builtins, '__compiled__') or hasattr(sys, '__nuitka_version__') or hasattr(sys, '_nuitka_version'):
        return True

    exe_name = os.path.basename(sys.executable).lower()
    if not (exe_name.startswith('python') or exe_name.startswith('pytest')):
        return True

    return False

def get_app_data_dir() -> str:
    r"""
    Returns isolated application data directory:
    - Windows Production (Installed/Compiled): %LOCALAPPDATA%\DrawMotion
    - Windows Development (Python Source)   : %LOCALAPPDATA%\DrawMotion-Dev
    - Linux Production                     : ~/.local/share/drawmotion
    - Linux Development                    : ~/.local/share/drawmotion-dev
    Creates the directory if it doesn't exist.
    """
    is_prod = is_frozen_build()

    if sys.platform == "win32":
        base_dir = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        app_name = "DrawMotion" if is_prod else "DrawMotion-Dev"
        app_dir = os.path.join(base_dir, app_name)
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
        app_name = "drawmotion" if is_prod else "drawmotion-dev"
        app_dir = os.path.join(xdg_data, app_name)

    if not os.path.exists(app_dir):
        os.makedirs(app_dir, exist_ok=True)

    return app_dir


def resource_path(relative_path: str) -> str:
    """
    Universal asset path resolver.
    Works correctly in all environments:
    - PyInstaller   : uses sys._MEIPASS temp extraction folder
    - Standalone bin: uses directory containing sys.executable
    - Development   : uses project root via __file__
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    elif is_frozen_build():
        base_path = os.path.dirname(os.path.abspath(sys.executable))
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    return os.path.normpath(os.path.join(base_path, relative_path))
