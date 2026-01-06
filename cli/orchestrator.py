import os
import sys
import time
from pathlib import Path

from cli.services.mediamtx import MediaMTXManager
from cli.services.ffmpeg import FFmpegManager
from cli.services.tunnel import TunnelManager
from cli.services.backend import BackendManager
from cli.utils.security import SecurityUtils
from cli.utils.logger import Logger
from cli.utils.installer import DependencyInstaller
from cli.config import Config


class Orchestrator:
    """Orchestrates all Remote AI services"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = Path.home() / ".remoto" / "data"
        self.logs_dir = Path.home() / ".remoto" / "logs"
        
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize config
        self.config = Config()
        
        # Initialize service managers
        self.mediamtx = MediaMTXManager(self.logs_dir, self.data_dir)
        self.ffmpeg = FFmpegManager(self.logs_dir, self.data_dir)
        self.api_tunnel = TunnelManager(self.logs_dir, self.data_dir, port=8000, name="api_tunnel")
        self.stream_tunnel = TunnelManager(self.logs_dir, self.data_dir, port=8888, name="stream_tunnel")
        self.backend = BackendManager(self.base_dir / "server", self.logs_dir, self.data_dir)
    
    def start(self, start_frontend=True, skip_dependency_check=False):
        """Start all services"""
        try:
            # Check dependencies first (unless skipped)
            if not skip_dependency_check:
                if not DependencyInstaller.check_and_install_all():
                    Logger.error("Missing dependencies. Please install them and try again.")
                    sys.exit(1)
            else:
                Logger.info("Skipping dependency check...")
                print("")
            
            Logger.info("Starting Remote AI...")
            print("")
            
            # Generate session password
            session_password = os.getenv("REMOTE_AI_PASSWORD") or SecurityUtils.generate_password()
            password_file = self.data_dir / "session_password.txt"
            with open(password_file, 'w') as f:
                f.write(session_password)
            
            # 1. Start MediaMTX
            Logger.info("Starting MediaMTX...")
            self.mediamtx.start()
            Logger.success("MediaMTX started")
            print("")
            
            # 2. Start FFmpeg
            Logger.info("Starting FFmpeg...")
            self.ffmpeg.start()
            Logger.success("FFmpeg streaming")
            print("")
            
            # 3. Start Cloudflare tunnels
            Logger.info("Starting Cloudflare tunnel for API...")
            api_tunnel_url = self.api_tunnel.start()
            Logger.success(f"API Tunnel URL: {api_tunnel_url}")
            print("")
            
            Logger.info("Starting Cloudflare tunnel for MediaMTX stream...")
            stream_tunnel_url = self.stream_tunnel.start()
            Logger.success(f"Stream Tunnel URL: {stream_tunnel_url}")
            print("")
            
            # 4. Start backend (use stream tunnel URL for STREAM_URL)
            Logger.info("Starting FastAPI backend...")
            self.backend.start(stream_tunnel_url, session_password)
            Logger.success("Backend started")
            print("")
            
            # Display access info
            self._display_access_info(api_tunnel_url, stream_tunnel_url, session_password)
            
            # Keep running
            Logger.info("Press Ctrl+C to stop all services...")
            print("")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n")
                Logger.info("Stopping services...")
                self.stop()
                
        except Exception as e:
            Logger.error(f"Error: {e}")
            self.stop()
            sys.exit(1)
    
    def stop(self):
        """Stop all services"""
        Logger.info("Stopping backend...")
        self.backend.stop()
        
        Logger.info("Stopping API tunnel...")
        self.api_tunnel.stop()
        
        Logger.info("Stopping stream tunnel...")
        self.stream_tunnel.stop()
        
        Logger.info("Stopping FFmpeg...")
        self.ffmpeg.stop()
        
        Logger.info("Stopping MediaMTX...")
        self.mediamtx.stop()
        
        print("")
        Logger.success("All services stopped")
        print("")
    
    def status(self):
        """Show status of all services"""
        print("")
        print("=" * 60)
        print("REMOTE AI STATUS")
        print("=" * 60)
        
        services = [
            ("MediaMTX", self.mediamtx.is_running()),
            ("FFmpeg", self.ffmpeg.is_running()),
            ("API Tunnel", self.api_tunnel.is_running()),
            ("Stream Tunnel", self.stream_tunnel.is_running()),
            ("Backend", self.backend.is_running()),
        ]
        
        for name, running in services:
            status = "RUNNING" if running else "STOPPED"
            print(f"{name:20} {status}")
        
        print("=" * 60)
        print("")
        
        # Show URLs if available
        api_tunnel_url = self.api_tunnel.get_url()
        stream_tunnel_url = self.stream_tunnel.get_url()
        if api_tunnel_url:
            print(f"API URL: {api_tunnel_url}")
        if stream_tunnel_url:
            print(f"Stream URL: {stream_tunnel_url}/screen")
        
        # Show password if available
        password_file = self.data_dir / "session_password.txt"
        if password_file.exists():
            with open(password_file) as f:
                password = f.read().strip()
            print(f"Password: {password}")
        
        print("")
    
    def _display_access_info(self, api_tunnel_url: str, stream_tunnel_url: str, password: str):
        """Display access information"""
        print("=" * 60)
        print("REMOTE AI READY")
        print("=" * 60)
        print("")
        print(f"API URL: {api_tunnel_url}")
        print(f"Stream URL: {stream_tunnel_url}/screen")
        print(f"Session Password: {password}")
        print("")
        print("Access from your phone:")
        print(f"1. Open: {api_tunnel_url}")
        print(f"2. Enter password when prompted")
        print("")
        print("Logs directory: " + str(self.logs_dir))
        print("=" * 60)
        print("")