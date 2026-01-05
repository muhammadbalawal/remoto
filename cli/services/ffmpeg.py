import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from cli.utils.process import ProcessManager
from cli.utils.logger import Logger


class FFmpegManager:
    """Manages FFmpeg streaming service"""
    
    def __init__(self, logs_dir: Path, data_dir: Path):
        self.logs_dir = logs_dir
        self.data_dir = data_dir
        self.log_file = logs_dir / "ffmpeg.log"
        self.pid_file = data_dir / "ffmpeg.pid"
        self.process = None
    
    def _detect_gpu(self) -> str:
        """Detect GPU type"""
        # Try NVIDIA
        try:
            subprocess.run(["nvidia-smi"], 
                         capture_output=True, 
                         check=True,
                         timeout=5)
            return "nvidia"
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try AMD (Windows)
        if sys.platform == 'win32':
            try:
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "name"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "AMD" in result.stdout or "Radeon" in result.stdout:
                    return "amd"
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        return "cpu"
    
    def _get_ffmpeg_command(self) -> list:
        """Get FFmpeg command based on OS and GPU"""
        gpu = self._detect_gpu()
        
        if sys.platform == 'win32':
            # Windows
            if gpu == "nvidia":
                return [
                    "ffmpeg",
                    "-f", "gdigrab",
                    "-framerate", "30",
                    "-i", "desktop",
                    "-vf", "fps=30",
                    "-c:v", "h264_nvenc",
                    "-preset", "p1",
                    "-tune", "ll",
                    "-b:v", "3M",
                    "-g", "60",
                    "-keyint_min", "60",
                    "-f", "rtsp",
                    "-rtsp_transport", "tcp",
                    "rtsp://127.0.0.1:8554/screen"
                ]
            elif gpu == "amd":
                return [
                    "ffmpeg",
                    "-f", "gdigrab",
                    "-framerate", "30",
                    "-i", "desktop",
                    "-vf", "fps=30",
                    "-c:v", "h264_amf",
                    "-quality", "speed",
                    "-b:v", "3M",
                    "-g", "60",
                    "-keyint_min", "60",
                    "-f", "rtsp",
                    "-rtsp_transport", "tcp",
                    "rtsp://127.0.0.1:8554/screen"
                ]
            else:
                return [
                    "ffmpeg",
                    "-f", "gdigrab",
                    "-framerate", "30",
                    "-i", "desktop",
                    "-vf", "fps=30",
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-tune", "zerolatency",
                    "-b:v", "3M",
                    "-g", "60",
                    "-keyint_min", "60",
                    "-f", "rtsp",
                    "-rtsp_transport", "tcp",
                    "rtsp://127.0.0.1:8554/screen"
                ]
        
        elif sys.platform == 'darwin':
            # macOS
            return [
                "ffmpeg",
                "-f", "avfoundation",
                "-pixel_format", "nv12",
                "-framerate", "30",
                "-i", "1",  # Screen capture device
                "-vf", "fps=30",
                "-vsync", "1",
                "-c:v", "h264_videotoolbox",
                "-b:v", "3M",
                "-g", "60",
                "-keyint_min", "60",
                "-f", "rtsp",
                "-rtsp_transport", "tcp",
                "rtsp://127.0.0.1:8554/screen"
            ]
        
        else:
            # Linux
            return [
                "ffmpeg",
                "-f", "x11grab",
                "-framerate", "30",
                "-i", ":0.0",
                "-vf", "fps=30",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-tune", "zerolatency",
                "-b:v", "3M",
                "-g", "60",
                "-keyint_min", "60",
                "-f", "rtsp",
                "-rtsp_transport", "tcp",
                "rtsp://127.0.0.1:8554/screen"
            ]
    
    def start(self):
        """Start FFmpeg streaming"""
        # Check if already running
        if self.is_running():
            Logger.warning("FFmpeg is already running")
            return
        
        # Check if ffmpeg is installed
        try:
            subprocess.run(["ffmpeg", "-version"], 
                         capture_output=True, 
                         check=True,
                         timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            Logger.error("FFmpeg not found. Please install it first.")
            Logger.error("Windows: Download from https://ffmpeg.org/")
            Logger.error("Mac: brew install ffmpeg")
            sys.exit(1)
        
        # Get command
        cmd = self._get_ffmpeg_command()
        gpu = self._detect_gpu()
        Logger.info(f"Using {gpu.upper()} encoder")
        
        # Start FFmpeg
        self.process = ProcessManager.start_process(cmd, self.log_file)
        ProcessManager.save_pid(self.pid_file, self.process.pid)
        
        # Wait for streaming to start
        time.sleep(3)
        
        # Verify it's running
        if not self.is_running():
            Logger.error("FFmpeg failed to start")
            sys.exit(1)
    
    def stop(self):
        """Stop FFmpeg"""
        pid = ProcessManager.load_pid(self.pid_file)
        if pid:
            ProcessManager.kill_process(pid, force=True)
            ProcessManager.delete_pid(self.pid_file)
            time.sleep(1)
    
    def is_running(self) -> bool:
        """Check if FFmpeg is running"""
        pid = ProcessManager.load_pid(self.pid_file)
        if pid and ProcessManager.is_process_running(pid):
            return True
        return False