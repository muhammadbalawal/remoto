"""
Process lifecycle utilities for the Remoto CLI.

Provides helpers to start background processes, track them via PID files,
check if they are alive, and kill them gracefully or forcefully.
"""

import os
import sys
import subprocess
import psutil
import time
import signal
from pathlib import Path
from typing import Optional, List


class ProcessManager:
    """Static utility class for managing background system processes via PID files."""
    
    @staticmethod
    def start_process(cmd: List[str], log_file: Path, cwd: Optional[Path] = None) -> subprocess.Popen:
        """Start a background process with stdout/stderr redirected to a log file.

        On Windows, creates the process in a new process group so it can be
        killed independently of the parent shell.

        Args:
            cmd: Command and arguments to execute.
            log_file: Path to the log file (created/truncated on start).
            cwd: Working directory for the subprocess.

        Returns:
            The started Popen instance.
        """
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
        
        return process
    
    @staticmethod
    def start_process_capture(cmd: List[str], log_file: Path, cwd: Optional[Path] = None) -> subprocess.Popen:
        """Start a background process with stdout/stderr captured via PIPE.

        Used when the caller needs to read process output (e.g. to parse
        the Cloudflare tunnel URL from stderr).

        Args:
            cmd: Command and arguments to execute.
            log_file: Path for the log file (directory is created if needed).
            cwd: Working directory for the subprocess.

        Returns:
            The started Popen instance with accessible stdout/stderr pipes.
        """
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )
        
        return process
    
    @staticmethod
    def kill_process(pid: int, force: bool = False):
        """Terminate or kill a process by PID.

        On Windows or when ``force=True``, sends SIGKILL immediately.
        Otherwise sends SIGTERM and waits up to 5 seconds before escalating.

        Args:
            pid: Process ID to terminate.
            force: If True, skip graceful termination and kill immediately.
        """
        try:
            process = psutil.Process(pid)
            
            if force or sys.platform == 'win32':
                process.kill()
            else:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    process.kill()
        except psutil.NoSuchProcess:
            pass
    
    @staticmethod
    def is_process_running(pid: int) -> bool:
        """Check if process is running"""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
    
    @staticmethod
    def is_port_open(port: int) -> bool:
        """Check if a TCP port is in LISTEN state on this machine.

        Args:
            port: Port number to check.

        Returns:
            True if the port is listening.
        """
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return True
        return False
    
    @staticmethod
    def save_pid(pid_file: Path, pid: int):
        """Save PID to file"""
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pid_file, 'w') as f:
            f.write(str(pid))
    
    @staticmethod
    def load_pid(pid_file: Path) -> Optional[int]:
        """Load PID from file"""
        if not pid_file.exists():
            return None
        try:
            with open(pid_file) as f:
                return int(f.read().strip())
        except (ValueError, FileNotFoundError):
            return None
    
    @staticmethod
    def delete_pid(pid_file: Path):
        """Delete PID file"""
        if pid_file.exists():
            pid_file.unlink()