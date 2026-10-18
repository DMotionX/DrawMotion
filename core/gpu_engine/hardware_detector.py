import subprocess
import os

class GPUHardwareDetector:
    @staticmethod
    def detect_best_gpu():
        """
        Runs a wmic command to get all VideoController names.
        Prioritizes NVIDIA or AMD dedicated GPUs over Intel integrated ones.
        """
        if os.name != 'nt':
            return "Unknown GPU"
            
        try:
            # Using wmic to get GPU names
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"], 
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            output = result.stdout.strip().split('\n')
            gpus = [line.strip() for line in output if line.strip() and line.strip().lower() != 'name']
            
            if not gpus:
                return "Unknown GPU"
                
            best_gpu = gpus[0]
            # Prioritize dedicated GPUs
            for gpu in gpus:
                gpu_lower = gpu.lower()
                if "nvidia" in gpu_lower or "geforce" in gpu_lower or "amd" in gpu_lower or "radeon" in gpu_lower:
                    if "intel" not in gpu_lower:
                        best_gpu = gpu
                        break
                        
            return best_gpu
        except Exception as e:
            return "Unknown GPU"
            
    @staticmethod
    def is_gpu_supported(gpu_name):
        if not gpu_name or gpu_name == "Unknown GPU":
            return False
            
        gpu_lower = gpu_name.lower()
        if "intel" in gpu_lower or "amd" in gpu_lower or "radeon" in gpu_lower or "nvidia" in gpu_lower or "geforce" in gpu_lower or "apple" in gpu_lower:
            return True
        return False
