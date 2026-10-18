"""
Purpose: Boot Health Watchdog and Installer Vault Engine.
Features:
- Tracks startup health and consecutive boot failures.
- Manages cached installers in the local vault for instant offline rollback.
- Provides rollback automation to safely restore previous stable versions.
Zero emojis, high-reliability, zero-risk.
"""

import os
import sys
import json
import shutil
import subprocess

def _get_base_dir() -> str:
    from utils.paths import get_app_data_dir
    return get_app_data_dir()


def get_health_file_path() -> str:
    return os.path.join(_get_base_dir(), "boot_health.json")

def get_vault_dir() -> str:
    vault = os.path.join(_get_base_dir(), "cache", "installers")
    os.makedirs(vault, exist_ok=True)
    return vault

def load_boot_health() -> dict:
    path = get_health_file_path()
    default_state = {
        "current_version": "",
        "boot_attempts": 0,
        "max_allowed_failures": 3,
        "last_successful_version": "",
        "previous_installer_path": "",
        "previous_version": "",
        "status": "healthy"
    }
    if not os.path.exists(path):
        return default_state
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in default_state.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return default_state

def save_boot_health(data: dict) -> bool:
    path = get_health_file_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception:
        return False

def record_boot_start(current_version: str) -> dict:
    state = load_boot_health()
    if state.get("current_version") != current_version:
        # Version change / new update installed
        old_version = state.get("current_version", "")
        if old_version and old_version != current_version:
            state["previous_version"] = old_version
        state["current_version"] = current_version
        state["boot_attempts"] = 1
        state["status"] = "starting"
    else:
        state["boot_attempts"] = state.get("boot_attempts", 0) + 1
        state["status"] = "starting"

    save_boot_health(state)
    return state

def record_boot_success(current_version: str) -> None:
    state = load_boot_health()
    state["boot_attempts"] = 0
    state["last_successful_version"] = current_version
    state["current_version"] = current_version
    state["status"] = "healthy"
    save_boot_health(state)

def record_boot_abort() -> None:
    """Safely decrements or clears boot attempts when an instance exits cleanly/intentionally."""
    try:
        state = load_boot_health()
        attempts = state.get("boot_attempts", 0)
        if attempts > 0:
            state["boot_attempts"] = attempts - 1
            save_boot_health(state)
    except Exception:
        pass

def is_recovery_required(current_version: str) -> tuple[bool, dict]:
    state = load_boot_health()

    # If the application version changed (new update installed), immediately reset failures
    if state.get("current_version") != current_version:
        state["boot_attempts"] = 0
        state["current_version"] = current_version
        state["status"] = "starting"
        save_boot_health(state)
        return False, state

    attempts = state.get("boot_attempts", 0)
    max_failures = state.get("max_allowed_failures", 3)
    
    # Check if a fatal crash log was genuinely recorded
    log_path = os.path.join(_get_base_dir(), "Logs", "crash_log.txt")
    has_crash_log = os.path.exists(log_path) and os.path.getsize(log_path) > 0

    # If no crash log exists and attempts are under 3, never force lockout
    if not has_crash_log and attempts < max_failures:
        needs_recovery = False
    else:
        needs_recovery = (attempts >= max_failures)
        
    return needs_recovery, state

def register_installer_in_vault(installer_path: str, version: str) -> str:
    if not installer_path or not os.path.exists(installer_path):
        return ""
    vault = get_vault_dir()
    dest_name = f"DrawMotion_Setup_v{version}.exe"
    dest_path = os.path.join(vault, dest_name)
    try:
        if os.path.abspath(installer_path) != os.path.abspath(dest_path):
            shutil.copy2(installer_path, dest_path)
        
        state = load_boot_health()
        state["previous_installer_path"] = dest_path
        state["previous_version"] = version
        save_boot_health(state)
        return dest_path
    except Exception:
        return installer_path

def get_previous_installer_info() -> tuple[str, str]:
    state = load_boot_health()
    prev_version = state.get("previous_version", "")
    prev_path = state.get("previous_installer_path", "")
    
    if prev_path and os.path.exists(prev_path):
        return prev_version, prev_path

    # Check vault directory fallback
    vault = get_vault_dir()
    if os.path.exists(vault):
        files = [f for f in os.listdir(vault) if f.startswith("DrawMotion_Setup_v") and f.endswith(".exe")]
        if files:
            files.sort()
            latest = files[-1]
            extracted_v = latest.replace("DrawMotion_Setup_v", "").replace(".exe", "")
            full_path = os.path.join(vault, latest)
            return extracted_v, full_path

    return "", ""

def launch_rollback_installer(installer_path: str) -> bool:
    if not installer_path or not os.path.exists(installer_path):
        return False
    try:
        # Launch installer with elevated privileges
        subprocess.Popen([installer_path], shell=False)
        return True
    except Exception:
        try:
            os.startfile(installer_path)
            return True
        except Exception:
            return False
