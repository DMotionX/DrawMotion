import os
import subprocess
import logging

class SecurityEngine:
    """
    Decoupled Security Interface.
    Communicates with the external standalone Blackbox (scanner.exe)
    to validate user inputs against malicious injections.
    """
    _instance = None
    
    def __init__(self):
        self.logger = logging.getLogger("SecurityEngine")
        self._scanner_path = self._resolve_scanner_path()
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SecurityEngine()
        return cls._instance

    def _resolve_scanner_path(self):
        """
        Dynamically resolves the path to scanner.exe.
        Works seamlessly in both Dev Mode and Nuitka Build Mode.
        """
        # Base directory of this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Look for the binary in the expected bin/ directory
        scanner_exe = os.path.join(base_dir, "bin", "scanner.exe")
        
        if os.path.exists(scanner_exe):
            return scanner_exe
            
        self.logger.warning(f"Security Scanner not found at {scanner_exe}. System is operating using Fallback protection.")
        return None

    def is_safe_input(self, user_input: str) -> bool:
        """
        Validates the input string.
        Returns True if safe, False if potentially malicious.
        """
        if not user_input or not user_input.strip():
            return False

        # Phase 1: Call external Rust/C# scanner if available
        if self._scanner_path:
            try:
                # We pass the input securely via args.
                # Avoid shell=True to prevent shell injection vulnerabilities.
                kwargs = {}
                if os.name == 'nt':
                    kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                    
                result = subprocess.run(
                    [self._scanner_path, user_input],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                    **kwargs
                )
                
                # Assume scanner returns exit code 0 for safe, non-zero for threat
                if result.returncode == 0:
                    return True
                else:
                    self.logger.warning(f"Security Engine blocked malicious input: {user_input}")
                    return False
                    
            except subprocess.TimeoutExpired:
                self.logger.error("Security Scanner timed out.")
                return False
            except Exception as e:
                self.logger.error(f"Security Scanner execution failed: {e}")
                # Fail-safe: Block if scanner crashes to prevent bypass
                return False
                
        # Phase 2: Fallback (Basic Regex/Filter) if scanner.exe is missing
        # This guarantees the app doesn't crash but still provides minimal protection
        # Block common shell injection characters
        forbidden_chars = [';', '&', '|', '>', '<', '`', '$', '(', ')', '{', '}', '\\', 'rm -rf']
        for char in forbidden_chars:
            if char in user_input:
                self.logger.warning(f"Fallback Security blocked malicious input: {user_input}")
                return False
                
        return True
