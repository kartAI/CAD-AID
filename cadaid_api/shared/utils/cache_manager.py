from typing import Optional
import hashlib
import json
import os
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
    def _get_file_hash(self, file_content: bytes) -> str:
        return hashlib.md5(file_content).hexdigest()
    
    def get_cached_result(self, file_content: bytes) -> Optional[dict]:
        file_hash = self._get_file_hash(file_content)
        cache_file = os.path.join(self.cache_dir, f"{file_hash}.json")
        
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                # Check if cache is still valid (24 hours)
                if datetime.fromisoformat(cached_data['timestamp']) > datetime.now() - timedelta(hours=24):
                    return cached_data['result']
        return None
    
    def cache_result(self, file_content: bytes, result: dict):
        file_hash = self._get_file_hash(file_content)
        cache_file = os.path.join(self.cache_dir, f"{file_hash}.json")
        
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'result': result
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f)
        