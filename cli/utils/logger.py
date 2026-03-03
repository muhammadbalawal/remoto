"""
Simple timestamped logger for CLI output.

Provides static methods for info, success, warning, and error messages
printed to stdout, plus a file-logging helper for persistent logs.
"""

import sys
from datetime import datetime
from pathlib import Path


class Logger:
    """Timestamped console logger with level-prefixed output."""
    
    @staticmethod
    def log(message: str, level: str = "INFO"):
        """Print a timestamped log message to the console.

        Args:
            message: The message text to display.
            level: Log level label (INFO, SUCCESS, WARNING, ERROR).
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    @staticmethod
    def info(message: str):
        """Log info message"""
        Logger.log(message, "INFO")
    
    @staticmethod
    def success(message: str):
        """Log success message"""
        Logger.log(message, "SUCCESS")
    
    @staticmethod
    def warning(message: str):
        """Log warning message"""
        Logger.log(message, "WARNING")
    
    @staticmethod
    def error(message: str):
        """Log error message"""
        Logger.log(message, "ERROR")
    
    @staticmethod
    def write_log(log_file: Path, message: str):
        """Append a timestamped message to a log file on disk.

        Creates parent directories if they don't exist.

        Args:
            log_file: Path to the log file.
            message: Message text to write.
        """
        log_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")