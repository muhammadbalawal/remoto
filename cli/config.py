import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Configuration management"""
    
    DEFAULT_CONFIG = {
        "streaming": {
            "resolution": "1280x720",
            "framerate": 30,
            "bitrate": "3M"
        },
        "mediamtx": {
            "rtsp_port": 8554,
            "hls_port": 8888
        },
        "backend": {
            "port": 8000,
            "host": "0.0.0.0"
        },
        "logging": {
            "level": "INFO",
            "keep_days": 7
        }
    }
    
    def __init__(self):
        self.config = self.DEFAULT_CONFIG.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot notation key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default