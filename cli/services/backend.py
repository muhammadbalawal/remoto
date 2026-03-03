import os
import sys
import time
import subprocess
import requests
from pathlib import Path
from typing import Optional

from cli.utils.process import ProcessManager
from cli.utils.logger import Logger


class BackendManager:
    """Manages the FastAPI backend server process.

    Handles starting/stopping Uvicorn, updating the ``.env`` file with
    runtime values (stream URL, session password), and health-checking
    the ``/health`` endpoint to verify the backend is responsive.

    Args:
        backend_dir: Path to the ``server/`` directory containing main.py.
        logs_dir: Directory for log files (``~/.remoto/logs/``).
        data_dir: Directory for PID files (``~/.remoto/data/``).
    """
    
    def __init__(self, backend_dir: Path, logs_dir: Path, data_dir: Path):
        self.backend_dir = backend_dir
        self.logs_dir = logs_dir
        self.data_dir = data_dir
        self.log_file = logs_dir / "backend.log"
        self.pid_file = data_dir / "backend.pid"
        self.env_file = backend_dir / ".env"
        self.process = None
    
    def _update_env(self, stream_url: str, password: str):
        """Merge runtime values into the backend ``.env`` file.

        Preserves any existing keys (like BACKBOARD_API_KEY) while replacing
        STREAM_URL and REMOTE_AI_PASSWORD with the current session values.

        Args:
            stream_url: Public Cloudflare tunnel URL for the HLS stream.
            password: Current session password.
        """
        env_content = []
        
        # Read existing .env if it exists
        if self.env_file.exists():
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    # Skip STREAM_URL and REMOTE_AI_PASSWORD lines
                    if not line.startswith("STREAM_URL=") and not line.startswith("REMOTE_AI_PASSWORD="):
                        env_content.append(line)
        
        # Add new values
        env_content.append(f"STREAM_URL={stream_url}")
        env_content.append(f"REMOTE_AI_PASSWORD={password}")
        
        # Write back
        with open(self.env_file, 'w') as f:
            f.write("\n".join(env_content) + "\n")
        
        Logger.info("Updated backend .env file")
    
    def start(self, stream_url: str, password: str):
        """Launch the FastAPI backend via Uvicorn as a background process.

        Updates the ``.env`` file, starts Uvicorn on port 8000, waits 3 seconds,
        and verifies the process is alive and the ``/health`` endpoint responds.

        Args:
            stream_url: Public Cloudflare tunnel URL for the HLS stream.
            password: Session password to inject into the environment.
        """
        # Check if already running
        if self.is_running():
            Logger.warning("Backend is already running")
            return
        
        # Update .env
        self._update_env(stream_url, password)
        
        # Check if uvicorn is available
        try:
            import uvicorn
        except ImportError:
            Logger.error("Uvicorn not found. Installing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        # Start backend
        cmd = [
            sys.executable,
            "-m", "uvicorn",
            "server.main:app",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]
        
        self.process = ProcessManager.start_process(cmd, self.log_file, cwd=self.backend_dir.parent)
        ProcessManager.save_pid(self.pid_file, self.process.pid)
        
        # Wait for it to start
        time.sleep(3)
        
        # Verify it's running
        if not self.is_running():
            Logger.error("Backend failed to start")
            sys.exit(1)
    
    def stop(self):
        """Stop backend"""
        pid = ProcessManager.load_pid(self.pid_file)
        if pid:
            ProcessManager.kill_process(pid, force=True)
            ProcessManager.delete_pid(self.pid_file)
            time.sleep(1)
    
    def is_running(self) -> bool:
        """Check if the backend process is alive and the /health endpoint responds 200."""
        # Check process
        pid = ProcessManager.load_pid(self.pid_file)
        if not pid or not ProcessManager.is_process_running(pid):
            return False
        
        # Check health endpoint
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False