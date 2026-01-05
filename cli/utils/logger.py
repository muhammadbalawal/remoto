import sys
from datetime import datetime
from pathlib import Path


class Logger:
    """logger for CLI"""
    
    @staticmethod
    def log(message: str, level: str = "INFO"):
        """Log a message to console"""
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
        """Write to log file"""
        log_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")