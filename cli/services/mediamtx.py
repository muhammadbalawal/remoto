import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional

from cli.utils.process import ProcessManager
from cli.utils.logger import Logger
from cli.utils.installer import DependencyInstaller


class MediaMTXManager:
    """Manages MediaMTX service"""
    
    def __init__(self, logs_dir: Path, data_dir: Path):
        self.logs_dir = logs_dir
        self.data_dir = data_dir
        self.log_file = logs_dir / "mediamtx.log"
        self.pid_file = data_dir / "mediamtx.pid"
        self.process = None
        self.config_content = """logLevel: info
logDestinations: [stdout]

# Global timeouts
readTimeout: 3600s
writeTimeout: 3600s

# RTSP Server
rtsp: yes
rtspAddress: :8554
rtspTransports: [tcp]
rtspEncryption: "no"

# HLS Server
hls: yes
hlsAddress: :8888
hlsEncryption: no
hlsAllowOrigin: '*'
hlsAlwaysRemux: yes
hlsVariant: lowLatency
hlsSegmentCount: 7
hlsSegmentDuration: 1s
hlsPartDuration: 200ms
hlsMuxerCloseAfter: 3600s

# Disable unused
rtmp: no
webrtc: no
srt: no
api: no
metrics: no
pprof: no
playback: no

# Paths
pathDefaults:
  source: publisher

paths:
  screen:
    source: publisher
"""
    
    def _ensure_config(self):
        """Ensure mediamtx.yml exists"""
        # Look for config in common locations
        possible_configs = [
            Path.cwd() / "mediamtx.yml",
            Path.home() / ".remoto" / "mediamtx.yml",
        ]
        
        # Check if config already exists
        for config_path in possible_configs:
            if config_path.exists():
                return
        
        # Create config in .remoto directory
        config_path = Path.home() / ".remoto" / "mediamtx.yml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            f.write(self.config_content)
        
        Logger.info(f"Created MediaMTX config at {config_path}")
    
    def start(self):
        """Start MediaMTX"""
        # Check if already running
        if self.is_running():
            Logger.warning("MediaMTX is already running")
            return
        
        # Ensure config exists
        self._ensure_config()
        
        # Find mediamtx path (checks Homebrew paths on macOS)
        mediamtx_path = DependencyInstaller.find_command_path("mediamtx")
        if mediamtx_path is None:
            Logger.error("MediaMTX not found. Please install it first.")
            Logger.error("Windows: Download from https://mediamtx.org/")
            Logger.error("Mac: brew install mediamtx")
            sys.exit(1)
        
        # Check if mediamtx works
        try:
            subprocess.run([mediamtx_path, "--version"], 
                         capture_output=True, 
                         check=True,
                         timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            Logger.error("MediaMTX found but failed to execute. Please check installation.")
            sys.exit(1)
        
        # Find config file
        config_path = None
        possible_configs = [
            Path.cwd() / "mediamtx.yml",
            Path.home() / ".remoto" / "mediamtx.yml",
        ]
        
        for path in possible_configs:
            if path.exists():
                config_path = path
                break
        
        # Start MediaMTX
        cmd = [mediamtx_path]
        if config_path:
            cmd.append(str(config_path))
        
        self.process = ProcessManager.start_process(cmd, self.log_file)
        ProcessManager.save_pid(self.pid_file, self.process.pid)
        
        # Wait for it to start
        time.sleep(2)
        
        # Verify it's running
        if not ProcessManager.is_port_open(8888):
            Logger.error("MediaMTX failed to start")
            sys.exit(1)
    
    def stop(self):
        """Stop MediaMTX"""
        pid = ProcessManager.load_pid(self.pid_file)
        if pid:
            ProcessManager.kill_process(pid)
            ProcessManager.delete_pid(self.pid_file)
            time.sleep(1)
    
    def is_running(self) -> bool:
        """Check if MediaMTX is running"""
        pid = ProcessManager.load_pid(self.pid_file)
        if pid and ProcessManager.is_process_running(pid):
            return True
        return ProcessManager.is_port_open(8888)