import os
import sys
import subprocess
import psutil
import time
import signal
from pathlib import Path
from typing import Optional, List


class ProcessManager:
    """Manages system processes"""
    
    @staticmethod
    def start_process(cmd: List[str], log_file: Path, cwd: Optional[Path] = None) -> subprocess.Popen:
        """Start a process and redirect output to log file"""
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
        """Start process and capture output (for parsing)"""
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
        """Kill a process by PID"""
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
        """Check if a port is open/listening"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return True
        return False
    
    @staticmethod
    def find_process_by_name(name: str) -> Optional[int]:
        """Find process PID by name"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if name.lower() in proc.info['name'].lower():
                    return proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return None
    
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