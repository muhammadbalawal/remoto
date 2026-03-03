"""
Centralized configuration defaults for the Remoto CLI.

Provides streaming resolution, port assignments, and logging settings
used across all service managers.
"""

import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Holds default configuration values and provides dot-notation access."""
    
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
        """Retrieve a configuration value using dot-notation.

        Args:
            key: Dot-separated path (e.g. 'streaming.resolution' or 'backend.port').
            default: Value returned if the key path does not exist.

        Returns:
            The configuration value, or *default* if not found.
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default