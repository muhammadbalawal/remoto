"""
Simple timestamped logger for CLI output.

Provides static methods for info, success, warning, and error messages
printed to stdout.
"""

from datetime import datetime


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