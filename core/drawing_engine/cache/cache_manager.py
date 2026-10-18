import hashlib
from typing import Any, Optional

class CacheManager:
    """
    Central caching system for the Drawing Engine.
    Prevents redundant heavy computations (e.g., path jittering, smoothing).
    """
    def __init__(self):
        self._cache = {}
        
    def generate_key(self, path_data: str, style_name: str, zoom_level: float) -> str:
        """
        Creates a unique hash key based on the path, the applied style, and zoom level.
        """
        raw_key = f"{path_data}_{style_name}_{zoom_level}"
        return hashlib.md5(raw_key.encode('utf-8')).hexdigest()
        
    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
        
    def set(self, key: str, data: Any):
        self._cache[key] = data
        
    def clear(self):
        self._cache.clear()

# Global Singleton for ease of use across the engine
drawing_cache = CacheManager()
