import os
import sys
import time
import platform
import subprocess
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
        self.logs_dir = Path("/Users/marcolipari/remoto/logs")
        
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
        
        # For macOS streaming process
        self.remoto_process = None
        self.macos_stream_url = None
    
    def start(self, start_frontend=True, skip_dependency_check=False):
        """Start all services"""
        try:
            # Check if running on macOS
            is_macos = platform.system() == "Darwin"
            
            # Check dependencies first (unless skipped)
            if not skip_dependency_check:
                if not DependencyInstaller.check_and_install_all(is_macos=is_macos):
                    if is_macos:
                        Logger.error("Remoto streaming setup not installed on macOS.")
                        sys.exit(1)
                    else:
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
            
            # On macOS, use remoto-start script to manage MediaMTX, FFmpeg, and stream tunnel
            if is_macos:
                Logger.info("Starting streaming services via remoto-start...")
                self._start_macos_streaming()
                Logger.success("Streaming services started")
                print("")
                
                # Use the captured stream URL from remoto-start
                if not self.macos_stream_url:
                    Logger.warning("Could not capture stream URL from remoto-start, using localhost fallback")
                    stream_url = "http://localhost:8888/screen"
                else:
                    stream_url = self.macos_stream_url
            else:
                # On other platforms, manually start individual services
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
                
                # 3. Start Cloudflare tunnel for stream
                Logger.info("Starting Cloudflare tunnel for MediaMTX stream...")
                stream_tunnel_url = self.stream_tunnel.start()
                Logger.success(f"Stream Tunnel URL: {stream_tunnel_url}")
                print("")
            
            # 4. Start API Cloudflare tunnel (same on all platforms)
            Logger.info("Starting Cloudflare tunnel for API...")
            api_tunnel_url = self.api_tunnel.start()
            Logger.success(f"API Tunnel URL: {api_tunnel_url}")
            print("")
            
            # 5. Start backend (use stream tunnel URL for STREAM_URL)
            if not is_macos:
                stream_url = self.stream_tunnel.get_url() + "/screen"
            
            Logger.info("Starting FastAPI backend...")
            self.backend.start(stream_url, session_password)
            Logger.success("Backend started")
            print("")
            
            # Display access info
            self._display_access_info(api_tunnel_url, stream_url, session_password)
            
            # Keep running
            Logger.info("Press Ctrl+C to stop all services...")
            print("")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n")
                Logger.info("Stopping services...")
                self.stop(is_macos=is_macos)
                
        except Exception as e:
            Logger.error(f"Error: {e}")
            self.stop()
            sys.exit(1)
    
    def stop(self, is_macos=None):
        """Stop all services"""
        if is_macos is None:
            is_macos = platform.system() == "Darwin"
        
        Logger.info("Stopping backend...")
        self.backend.stop()
        
        Logger.info("Stopping API tunnel...")
        self.api_tunnel.stop()
        
        if is_macos:
            Logger.info("Stopping macOS streaming services...")
            self._stop_macos_streaming()
        else:
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
    
    def _start_macos_streaming(self):
        """Start streaming services on macOS using remoto-start script"""
        try:
            remoto_script = Path.home() / ".remoto" / "start.sh"
            
            if not remoto_script.exists():
                raise RuntimeError(f"remoto-start script not found at {remoto_script}")
            
            # Start remoto-start script in background
            # The script will handle MediaMTX, FFmpeg, and Cloudflare tunnel
            # We capture output to extract the stream URL
            self.remoto_process = subprocess.Popen(
                ["bash", str(remoto_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Read output to find the stream URL
            self.macos_stream_url = None
            import re
            while True:
                line = self.remoto_process.stdout.readline()
                if not line:
                    break
                print(line, end='')  # Print to console
                
                # Look for the stream URL in output (pattern: https://xxx.trycloudflare.com/screen)
                match = re.search(r'(https://[^\s]+\.trycloudflare\.com/screen)', line)
                if match:
                    self.macos_stream_url = match.group(1)
                    Logger.success(f"Captured stream URL: {self.macos_stream_url}")
                    break
            
            # Check if process is still running (would have exited with error if failed)
            if self.remoto_process.poll() is not None:
                # Process exited, read remaining output to see what went wrong
                remaining_output, _ = self.remoto_process.communicate()
                if remaining_output:
                    print(remaining_output, end='')
                raise RuntimeError(f"remoto-start script exited unexpectedly")
            
            # Continue reading output in background
            import threading
            threading.Thread(target=self._read_remoto_output, daemon=True).start()
                
        except FileNotFoundError:
            raise RuntimeError("remoto-start script not found. Please ensure Homebrew installation completed successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to start macOS streaming services: {e}")
    
    def _read_remoto_output(self):
        """Read remaining output from remoto process"""
        try:
            while True:
                line = self.remoto_process.stdout.readline()
                if not line:
                    break
                print(line, end='')
        except:
            pass
    
    def _stop_macos_streaming(self):
        """Stop streaming services on macOS"""
        try:
            # If remoto process is still running, terminate it
            if self.remoto_process and self.remoto_process.poll() is None:
                self.remoto_process.terminate()
                try:
                    self.remoto_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.remoto_process.kill()
            
            remoto_stop_script = Path.home() / ".remoto" / "stop.sh"
            
            # Also try calling remoto-stop script directly if it exists
            if remoto_stop_script.exists():
                subprocess.run(
                    ["bash", str(remoto_stop_script)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
        except Exception as e:
            Logger.warning(f"Could not cleanly stop macOS streaming services: {e}")
            # Try direct pkill as fallback
            try:
                subprocess.run(["pkill", "-f", "ffmpeg.*rtsp"], capture_output=True)
                subprocess.run(["pkill", "cloudflared"], capture_output=True)
                subprocess.run(["brew", "services", "stop", "mediamtx"], capture_output=True)
            except Exception as fallback_error:
                Logger.warning(f"Fallback stop also failed: {fallback_error}")
    
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