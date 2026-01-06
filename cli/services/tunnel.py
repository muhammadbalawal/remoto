import os
import sys
import time
import subprocess
import threading
from pathlib import Path
from typing import Optional

from cli.utils.process import ProcessManager
from cli.utils.logger import Logger
from cli.utils.installer import DependencyInstaller


class TunnelManager:
    """Manages Cloudflare tunnel service"""
    
    def __init__(self, logs_dir: Path, data_dir: Path, port: int = 8000, name: str = "tunnel"):
        self.logs_dir = logs_dir
        self.data_dir = data_dir
        self.port = port
        self.name = name
        self.log_file = logs_dir / f"{name}.log"
        self.pid_file = data_dir / f"{name}.pid"
        self.url_file = data_dir / f"{name}_url.txt"
        self.process = None
        self.tunnel_url = None
    
    def _capture_url(self, process: subprocess.Popen) -> Optional[str]:
        """Capture tunnel URL from stderr"""
        url = None
        
        try:
            for line in process.stderr:
                # Write to log
                with open(self.log_file, 'a') as f:
                    f.write(line)
                
                # Look for URL
                if "trycloudflare.com" in line:
                    # Extract URL
                    parts = line.split("https://")
                    if len(parts) > 1:
                        url_part = parts[1].split()[0]
                        url = f"https://{url_part}"
                        Logger.info(f"Tunnel URL captured: {url}")
                        
                        # Save URL
                        with open(self.url_file, 'w') as f:
                            f.write(url)
                        
                        return url
        except Exception as e:
            Logger.error(f"Error capturing URL: {e}")
        
        return url
    
    def start(self) -> str:
        """Start Cloudflare tunnel and return URL"""
        # Check if already running
        if self.is_running():
            Logger.warning("Tunnel is already running")
            # Try to load existing URL
            if self.url_file.exists():
                with open(self.url_file) as f:
                    return f.read().strip()
        
        # Find cloudflared path (checks Homebrew paths on macOS)
        cloudflared_path = DependencyInstaller.find_command_path("cloudflared")
        if cloudflared_path is None:
            Logger.error("Cloudflared not found. Please install it first.")
            Logger.error("Windows: winget install Cloudflare.Cloudflared")
            Logger.error("Mac: brew install cloudflared")
            sys.exit(1)
        
        # Check if cloudflared works
        try:
            subprocess.run([cloudflared_path, "--version"], 
                         capture_output=True, 
                         check=True,
                         timeout=5)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            Logger.error("Cloudflared found but failed to execute. Please check installation.")
            sys.exit(1)
        
        # Start tunnel for specified port
        cmd = [cloudflared_path, "tunnel", "--url", f"http://localhost:{self.port}"]
        self.process = ProcessManager.start_process_capture(cmd, self.log_file)
        ProcessManager.save_pid(self.pid_file, self.process.pid)
        
        # Capture URL from stderr (blocking until found)
        url = self._capture_url(self.process)
        
        if not url:
            Logger.error("Failed to capture tunnel URL")
            self.stop()
            sys.exit(1)
        
        self.tunnel_url = url
        return url
    
    def stop(self):
        """Stop Cloudflare tunnel"""
        pid = ProcessManager.load_pid(self.pid_file)
        if pid:
            ProcessManager.kill_process(pid, force=True)
            ProcessManager.delete_pid(self.pid_file)
            if self.url_file.exists():
                self.url_file.unlink()
            time.sleep(1)
    
    def is_running(self) -> bool:
        """Check if tunnel is running"""
        pid = ProcessManager.load_pid(self.pid_file)
        if pid and ProcessManager.is_process_running(pid):
            return True
        return False
    
    def get_url(self) -> Optional[str]:
        """Get current tunnel URL"""
        if self.url_file.exists():
            with open(self.url_file) as f:
                return f.read().strip()
        return None