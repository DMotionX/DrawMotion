import os
import json
import urllib.request
import urllib.error
from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt, QThread, Signal, QObject
from utils.theme import THEME_COLORS

# Current application version
CURRENT_VERSION = "1.7.8"

# Official public open-source repository
GITHUB_REPO = "DMotionX/DrawMotion"

def is_newer_version(latest: str, current: str) -> bool:
    """Performs semantic comparison between version strings."""
    try:
        l_parts = [int(p) for p in latest.strip().lstrip('v').split('.') if p.isdigit()]
        c_parts = [int(p) for p in current.strip().lstrip('v').split('.') if p.isdigit()]
        return l_parts > c_parts
    except Exception:
        return latest != current

class UpdateCheckerThread(QThread):
    update_available = Signal(dict)
    no_update = Signal()
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("UpdateCheckerThread")
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def shutdown(self):
        self.cancel()
        try:
            if self.isRunning():
                self.quit()
                self.wait(500)
        except Exception:
            pass

    def run(self):
        if self._is_cancelled:
            return
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'DrawMotion-Updater'})
            with urllib.request.urlopen(req, timeout=5) as response:
                if self._is_cancelled:
                    return
                data = json.loads(response.read().decode())
                
                latest_version = data.get("tag_name", "").replace("v", "")
                if latest_version and is_newer_version(latest_version, CURRENT_VERSION):
                    self.update_available.emit({
                        "version": latest_version,
                        "changelog": data.get("body", "No changelog provided."),
                        "assets": data.get("assets", [])
                    })
                else:
                    self.no_update.emit()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # Repository doesn't exist yet, simulate no update available
                self.no_update.emit()
            else:
                self.error.emit(str(e))
        except Exception as e:
            self.error.emit(str(e))


class UpdaterDialog(QDialog):
    """
    Unified high-speed updater UI delegating to the 8-stream FastUpdateDialog.
    Zero emojis, high-speed parallel downloads.
    """
    def __new__(cls, update_info, parent=None):
        from core.update_engine.ui import FastUpdateDialog
        return FastUpdateDialog(update_info, parent)
