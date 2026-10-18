import json
import urllib.request
from PySide6.QtCore import QObject, Signal, QThread
from core.updater import CURRENT_VERSION, GITHUB_REPO, is_newer_version

class SilentUpdateChecker(QThread):
    """
    Checks for updates asynchronously in the background without freezing the UI.
    Emits full release details if a newer version is available.
    """
    update_found = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SilentUpdateCheckerThread")
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
            if not url.startswith("https://"):
                raise ValueError("Insecure update URL scheme")
            req = urllib.request.Request(url, headers={'User-Agent': 'DrawMotion-AutoNotifier/1.0'})
            with urllib.request.urlopen(req, timeout=4) as response:  # nosec B310
                if self._is_cancelled:
                    return
                data = json.loads(response.read().decode())
                if self._is_cancelled:
                    return
                
                latest_version = data.get("tag_name", "").replace("v", "")
                if latest_version and is_newer_version(latest_version, CURRENT_VERSION):
                    assets = data.get("assets", [])
                    download_url = ""
                    for asset in assets:
                        if asset.get("name", "").endswith(".exe"):
                            download_url = asset.get("browser_download_url", "")
                            break
                            
                    if download_url and not self._is_cancelled:
                        self.update_found.emit({
                            "version": latest_version,
                            "changelog": data.get("body", "Stability improvements and new features."),
                            "url": download_url,
                            "assets": assets
                        })
        except Exception:
            # Silent fail for background check
            pass
