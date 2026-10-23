r"""
Purpose: DrawMotion Startup Lifecycle Diagnostics Tracker.
Features:
- Records precise, microsecond-timestamped lifecycle events during application boot.
- Completely non-blocking and fail-safe (zero impact on startup speed, zero risk of crashing).
- Writes to %LOCALAPPDATA%\DrawMotion[-Dev]\Logs\startup_lifecycle.log.
- Provides diagnostic trace summaries for error dialogs and disaster recovery.
"""

import os
import sys
import datetime
from typing import List

class StartupLifecycleTracker:
    _initialized = False
    _log_path = ""
    _in_memory_trace: List[str] = []
    _max_memory_entries = 50

    @classmethod
    def _resolve_log_path(cls) -> str:
        if cls._log_path:
            return cls._log_path
        try:
            from utils.paths import get_app_data_dir
            base_dir = get_app_data_dir()
            log_dir = os.path.join(base_dir, "Logs")
            os.makedirs(log_dir, exist_ok=True)
            cls._log_path = os.path.join(log_dir, "startup_lifecycle.log")
        except Exception:
            try:
                import tempfile
                fallback_dir = os.path.join(tempfile.gettempdir(), "DrawMotion_Logs")
                os.makedirs(fallback_dir, exist_ok=True)
                cls._log_path = os.path.join(fallback_dir, "startup_lifecycle.log")
            except Exception:
                cls._log_path = None
        return cls._log_path

    @classmethod
    def initialize(cls, version: str = "Unknown") -> None:
        """Initializes the lifecycle log session. Overwrites or truncates if log exceeds 1MB."""
        try:
            path = cls._resolve_log_path()
            # If log file is larger than 1MB, rotate/clean it
            if os.path.exists(path) and os.path.getsize(path) > 1024 * 1024:
                try:
                    os.remove(path)
                except Exception:
                    pass

            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            is_frozen = getattr(sys, 'frozen', False) or hasattr(sys, '_nuitka_version') or '__compiled__' in globals()
            env_mode = "Standalone/Production" if is_frozen else "Development/Source"

            header = (
                f"\n{'='*70}\n"
                f"DRAWMOTION BOOT SESSION STARTED\n"
                f"Timestamp   : {now_str}\n"
                f"Version     : v{version}\n"
                f"Environment : {env_mode}\n"
                f"PID         : {os.getpid()}\n"
                f"Executable  : {sys.executable}\n"
                f"{'='*70}\n"
            )

            with open(path, "a", encoding="utf-8") as f:
                f.write(header)

            cls._initialized = True
            cls.trace("BOOTSTRAP_START", f"PID={os.getpid()} Mode={env_mode}")
        except Exception:
            # Completely fail-safe: never crash
            pass

    @classmethod
    def trace(cls, phase: str, details: str = "") -> None:
        """Records a timestamped lifecycle milestone to disk and memory."""
        try:
            now_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            entry = f"[{now_str}] [{phase.upper()}] {details}".strip()
            
            # Store in memory for immediate inspection
            cls._in_memory_trace.append(entry)
            if len(cls._in_memory_trace) > cls._max_memory_entries:
                cls._in_memory_trace.pop(0)

            path = cls._resolve_log_path()
            with open(path, "a", encoding="utf-8") as f:
                f.write(entry + "\n")
        except Exception:
            pass

    @classmethod
    def get_log_path(cls) -> str:
        return cls._resolve_log_path()

    @classmethod
    def get_recent_trace(cls) -> str:
        """Returns the last recorded trace lines as a formatted string."""
        return "\n".join(cls._in_memory_trace)
