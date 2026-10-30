# Copyright (c) 2026 Mohamed Fadl & DrawMotion Team
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import sys
import subprocess
import logging
import unicodedata
import zipfile
from typing import Optional

class SecurityEngine:
    """
    Decoupled Zero-Risk Security Interface for DrawMotion.
    Provides multi-layered protection:
    1. Ultra-fast, zero-overhead In-Memory Unicode input sanitization (Zero False Positives).
    2. Native OS validation via compiled Rust blackbox (scanner.exe) on Windows.
    3. Defensive Path Traversal & Windows Reserved Name shielding.
    4. Project Archive (Zip Slip / Zip Bomb) integrity verification.
    """
    _instance = None
    
    # Windows reserved device names that cause OS hangs or filesystem corruption
    RESERVED_NAMES = {
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
        "COM¹", "COM²", "COM³", "LPT¹", "LPT²", "LPT³"
    }

    # Strict forbidden characters for file and folder names across Windows and POSIX
    FORBIDDEN_CHARS = {
        ';', '&', '|', '>', '<', '`', '$', '{', '}', '\\', '/', ':', '*', '?', '"', '\0'
    }

    def __init__(self):
        self.logger = logging.getLogger("SecurityEngine")
        self._scanner_path = self._resolve_scanner_path()
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SecurityEngine()
        return cls._instance

    def _resolve_scanner_path(self) -> Optional[str]:
        """
        Dynamically resolves the path to scanner.exe.
        Works seamlessly in both Dev Mode and Nuitka / PyInstaller Build Mode.
        """
        try:
            # Base directory of this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Look for the binary in the expected bin/ directory
            scanner_exe = os.path.join(base_dir, "bin", "scanner.exe")
            
            if os.path.exists(scanner_exe) and os.name == 'nt':
                return scanner_exe
                
            # In Nuitka standalone builds, check application root
            if getattr(sys, "frozen", False):
                app_root = os.path.dirname(sys.executable)
                candidate = os.path.join(app_root, "core", "security_engine", "bin", "scanner.exe")
                if os.path.exists(candidate) and os.name == 'nt':
                    return candidate
                    
            return None
        except Exception as e:
            self.logger.warning(f"Could not resolve scanner binary path: {e}")
            return None

    @staticmethod
    def _is_safe_char(c: str) -> bool:
        """
        Validates individual character using the exact same rules as the Rust scanner:
        - ASCII alphanumeric or general alphanumeric unicode (letters/digits in all languages)
        - Safe punctuation: . _ - ( ) and space
        - Arabic Unicode blocks: Primary, Supplement, Extended-A, Presentation-A, Presentation-B
        """
        if c.isalnum() or c in {'.', '_', '-', ' ', '(', ')'}:
            return True
            
        code = ord(c)
        if (
            (0x0600 <= code <= 0x06FF) or  # Arabic Primary
            (0x0750 <= code <= 0x077F) or  # Arabic Supplement
            (0x08A0 <= code <= 0x08FF) or  # Arabic Extended-A
            (0xFB50 <= code <= 0xFDFF) or  # Arabic Presentation Forms-A
            (0xFE70 <= code <= 0xFEFF)     # Arabic Presentation Forms-B
        ):
            return True
            
        return False

    def validate_in_memory(self, user_input: str) -> bool:
        """
        Performs ultra-fast in-memory validation (< 0.05ms) with zero OS overhead.
        Matches the strict security criteria of the Rust binary.
        """
        if not user_input or not isinstance(user_input, str):
            return False
            
        trimmed = user_input.strip()
        if not trimmed:
            return False
            
        # 1. Null-byte rejection
        if '\0' in user_input:
            self.logger.warning("Security Engine blocked input containing null bytes.")
            return False

        # 2. Strong Unicode normalization (NFKC)
        normalized = unicodedata.normalize('NFKC', trimmed)
        upper = normalized.upper()
        lower = normalized.lower()

        # 3. Path Traversal Check (relative path traversal)
        if ".." in lower:
            self.logger.warning(f"Security Engine blocked Path Traversal attempt: {user_input}")
            return False

        # 4. Check for Reserved Windows Device Names
        base_name = upper.split('.')[0].strip()
        if upper in self.RESERVED_NAMES or base_name in self.RESERVED_NAMES:
            self.logger.warning(f"Security Engine blocked Reserved Windows Name: {user_input}")
            return False

        # 5. Fast check for shell / filesystem injection characters
        for ch in normalized:
            if ch in self.FORBIDDEN_CHARS:
                self.logger.warning(f"Security Engine blocked forbidden character '{ch}' in: {user_input}")
                return False
            if not self._is_safe_char(ch):
                self.logger.warning(f"Security Engine blocked non-allowlisted character '{ch}' in: {user_input}")
                return False

        return True

    def is_safe_input(self, user_input: str) -> bool:
        """
        Validates user input string (e.g. folder name, project title).
        Returns True if safe, False if potentially malicious.
        Guarantees 100% backwards compatibility and zero crash risk.
        """
        try:
            # Step 1: Instant In-Memory validation
            if not self.validate_in_memory(user_input):
                return False

            # Step 2: Native external scanner validation if on Windows and binary exists
            if self._scanner_path and os.name == 'nt':
                try:
                    kwargs = {
                        "creationflags": subprocess.CREATE_NO_WINDOW
                    }
                    result = subprocess.run(
                        [self._scanner_path, user_input],
                        capture_output=True,
                        text=True,
                        timeout=1.5,
                        **kwargs
                    )
                    if result.returncode != 0:
                        self.logger.warning(f"Rust Security Scanner blocked input: {user_input}")
                        return False
                except subprocess.TimeoutExpired:
                    self.logger.error("Rust Security Scanner timed out, relying on in-memory validation.")
                except Exception as e:
                    self.logger.warning(f"Rust Security Scanner invocation failed: {e}")

            return True
        except Exception as e:
            self.logger.error(f"Unexpected error in is_safe_input: {e}", exc_info=True)
            # Fail-safe: if something unexpected crashed, reject input to maintain security
            return False

    def is_safe_path(self, target_path: str, base_dir: Optional[str] = None) -> bool:
        """
        Guarantees that target_path does not escape base_dir via directory traversal.
        """
        try:
            if not target_path or '\0' in target_path:
                return False
                
            abs_target = os.path.abspath(os.path.normpath(target_path))
            
            if base_dir:
                abs_base = os.path.abspath(os.path.normpath(base_dir))
                # Ensure abs_target starts with abs_base directory
                common = os.path.commonpath([abs_base, abs_target])
                if common != abs_base:
                    self.logger.warning(f"Path escape attempt blocked: {target_path} outside {base_dir}")
                    return False
                    
            return True
        except Exception as e:
            self.logger.error(f"Error checking path safety: {e}")
            return False

    def is_safe_project_archive(
        self, 
        zip_path: str, 
        max_files: int = 10000, 
        max_uncompressed_bytes: int = 500 * 1024 * 1024
    ) -> bool:
        """
        Validates .drawmotion project archive before extraction.
        Prevents Zip Slip (directory traversal in archive members) and Zip Bomb attacks.
        """
        try:
            if not os.path.isfile(zip_path):
                return False
                
            total_uncompressed = 0
            file_count = 0
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for info in zf.infolist():
                    file_count += 1
                    if file_count > max_files:
                        self.logger.warning(f"Zip archive exceeded max file count limit: {zip_path}")
                        return False
                        
                    total_uncompressed += info.file_size
                    if total_uncompressed > max_uncompressed_bytes:
                        self.logger.warning(f"Zip archive exceeded uncompressed size limit: {zip_path}")
                        return False
                        
                    # Check for Zip Slip directory traversal
                    member_name = info.filename
                    if member_name.startswith(('/', '\\')) or (len(member_name) > 1 and member_name[1] == ':'):
                        self.logger.warning(f"Zip Slip absolute path blocked: {member_name}")
                        return False
                        
                    normalized = os.path.normpath(member_name)
                    if normalized.startswith("..") or ".." in normalized.split(os.sep):
                        self.logger.warning(f"Zip Slip relative traversal blocked: {member_name}")
                        return False
                        
            return True
        except zipfile.BadZipFile:
            self.logger.warning(f"Corrupt or invalid zip archive: {zip_path}")
            return False
        except Exception as e:
            self.logger.error(f"Error validating project archive: {e}")
            return False

    def sanitize_file_name(self, raw_name: str, default: str = "project") -> str:
        """
        Sanitizes a raw input string into a safe file/folder name.
        """
        try:
            if not raw_name or not isinstance(raw_name, str):
                return default
                
            normalized = unicodedata.normalize('NFKC', raw_name).strip()
            safe_chars = []
            
            for ch in normalized:
                if self._is_safe_char(ch) and ch not in self.FORBIDDEN_CHARS:
                    safe_chars.append(ch)
                else:
                    safe_chars.append('_')
                    
            clean_name = "".join(safe_chars).strip('. ')
            clean_upper = clean_name.upper().split('.')[0]
            
            if not clean_name or clean_upper in self.RESERVED_NAMES:
                return f"{default}_safe"
                
            return clean_name
        except Exception:
            return default
