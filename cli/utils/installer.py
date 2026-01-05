import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import shutil
from pathlib import Path
from cli.utils.logger import Logger


class DependencyInstaller:
    """Automatically install required dependencies"""
    
    @staticmethod
    def is_windows():
        return platform.system() == "Windows"
    
    @staticmethod
    def is_mac():
        return platform.system() == "Darwin"
    
    @staticmethod
    def is_linux():
        return platform.system() == "Linux"
    
    @staticmethod
    def check_command(command):
        """Check if a command exists"""
        # On Windows, try multiple approaches since PATH might not be fully available
        if DependencyInstaller.is_windows():
            # Special handling for Tesseract - check common installation paths first
            if command == "tesseract":
                common_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                ]
                # Also try with username
                username = os.getenv('USERNAME', '')
                if username:
                    common_paths.append(
                        rf'C:\Users\{username}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
                    )
                
                for path in common_paths:
                    if Path(path).exists():
                        # Verify it works
                        try:
                            result = subprocess.run(
                                [path, "--version"],
                                capture_output=True,
                                text=True,
                                check=True,
                                timeout=5
                            )
                            if result.returncode == 0 or (result.stdout and "tesseract" in result.stdout.lower()):
                                return True
                        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                            continue
            
            # Try different variations: lowercase, uppercase first letter, with .exe
            variations = [command, command.capitalize(), f"{command}.exe"]
            version_flags = ["-version", "--version"]
            
            for cmd_var in variations:
                for version_flag in version_flags:
                    # First try: Use shutil.which (checks PATH)
                    exe_path = shutil.which(cmd_var)
                    if exe_path:
                        # Found in PATH, verify it works
                        try:
                            result = subprocess.run(
                                f"{cmd_var} {version_flag}",
                                shell=True,
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            # Check if it succeeded or if output contains version info
                            if result.returncode == 0 or (result.stdout and "version" in result.stdout.lower()):
                                return True
                        except (FileNotFoundError, subprocess.TimeoutExpired):
                            pass
                        except subprocess.CalledProcessError:
                            # Even if return code is non-zero, check if we got version output
                            pass
            
            # Final try: Direct execution with shell=True (uses cmd.exe PATH)
            # Don't use check=True, check return code and output manually
            for version_flag in version_flags:
                try:
                    result = subprocess.run(
                        f"{command} {version_flag}",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    # Success if return code is 0 OR if we got version output
                    if result.returncode == 0 or (result.stdout and "version" in result.stdout.lower()):
                        return True
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    pass
                except subprocess.CalledProcessError as e:
                    # Check if we got version output despite error code
                    if e.stdout and "version" in e.stdout.lower():
                        return True
            
            return False
        else:
            # On Unix-like systems, use shutil.which first
            if shutil.which(command) is None:
                return False
            
            # Verify it actually works
            try:
                result = subprocess.run([command, "--version"], 
                             capture_output=True, 
                             text=True,
                             check=True,
                             timeout=5)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                return False
    
    @staticmethod
    def download_file(url, destination):
        """Download a file with progress"""
        Logger.info(f"Downloading from {url}...")
        try:
            urllib.request.urlretrieve(url, destination)
            Logger.success(f"Downloaded to {destination}")
            return True
        except Exception as e:
            Logger.error(f"Download failed: {e}")
            return False
    
    @staticmethod
    def extract_zip(zip_path, extract_to):
        """Extract a zip file"""
        Logger.info(f"Extracting {zip_path}...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            Logger.success(f"Extracted to {extract_to}")
            return True
        except Exception as e:
            Logger.error(f"Extraction failed: {e}")
            return False
    
    @staticmethod
    def add_to_path_windows(directory):
        """Add directory to Windows PATH"""
        try:
            # Get current PATH
            result = subprocess.run(
                ['powershell', '-Command', '[Environment]::GetEnvironmentVariable("Path", "User")'],
                capture_output=True,
                text=True,
                check=True
            )
            current_path = result.stdout.strip()
            
            # Check if already in PATH
            if directory in current_path:
                Logger.info(f"{directory} already in PATH")
                return True
            
            # Add to PATH
            new_path = f"{current_path};{directory}"
            subprocess.run(
                ['powershell', '-Command', f'[Environment]::SetEnvironmentVariable("Path", "{new_path}", "User")'],
                check=True
            )
            
            Logger.success(f"Added {directory} to PATH")
            return True
        except Exception as e:
            Logger.error(f"Failed to add to PATH: {e}")
            return False
    
    @staticmethod
    def install_cloudflared_windows():
        """Install Cloudflared on Windows"""
        install_dir = Path.home() / ".remoto" / "bin"
        install_dir.mkdir(parents=True, exist_ok=True)
        
        exe_path = install_dir / "cloudflared.exe"
        
        # Download
        url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        
        if not DependencyInstaller.download_file(url, exe_path):
            return False
        
        # Add to PATH
        if not DependencyInstaller.add_to_path_windows(str(install_dir)):
            return False
        
        Logger.success("Cloudflared installed successfully")
        return True
    
    @staticmethod
    def install_ffmpeg_windows():
        """Install FFmpeg on Windows"""
        install_dir = Path.home() / ".remoto" / "ffmpeg"
        install_dir.mkdir(parents=True, exist_ok=True)
        
        zip_path = install_dir / "ffmpeg.zip"
        
        # Download essentials build
        url = "https://github.com/GyanD/codexffmpeg/releases/download/8.0.1/ffmpeg-8.0.1-essentials_build.zip"
        
        if not DependencyInstaller.download_file(url, zip_path):
            return False
        
        # Extract
        if not DependencyInstaller.extract_zip(zip_path, install_dir):
            return False
        
        # Find bin directory
        bin_dir = install_dir / "ffmpeg-8.0.1-essentials_build" / "bin"
        
        if not bin_dir.exists():
            Logger.error("FFmpeg bin directory not found after extraction")
            return False
        
        # Add to PATH
        if not DependencyInstaller.add_to_path_windows(str(bin_dir)):
            return False
        
        # Clean up zip
        zip_path.unlink()
        
        Logger.success("FFmpeg installed successfully")
        return True
    
    @staticmethod
    def install_mediamtx_windows():
        """Install MediaMTX on Windows"""
        install_dir = Path.home() / ".remoto" / "mediamtx"
        install_dir.mkdir(parents=True, exist_ok=True)
        
        zip_path = install_dir / "mediamtx.zip"
        
        # Download
        url = "https://github.com/bluenviron/mediamtx/releases/download/v1.15.0/mediamtx_v1.15.0_windows_amd64.zip"
        
        if not DependencyInstaller.download_file(url, zip_path):
            return False
        
        # Extract
        if not DependencyInstaller.extract_zip(zip_path, install_dir):
            return False
        
        # Add to PATH
        if not DependencyInstaller.add_to_path_windows(str(install_dir)):
            return False
        
        # Clean up zip
        zip_path.unlink()
        
        Logger.success("MediaMTX installed successfully")
        return True
    
    @staticmethod
    def install_cloudflared():
        """Install Cloudflared"""
        Logger.info("Installing Cloudflared...")
        
        if DependencyInstaller.is_windows():
            return DependencyInstaller.install_cloudflared_windows()
        
        elif DependencyInstaller.is_mac():
            try:
                subprocess.run(["brew", "install", "cloudflared"], check=True)
                Logger.success("Cloudflared installed via brew")
                return True
            except:
                Logger.error("Failed to install Cloudflared via brew")
                Logger.info("Please install manually: brew install cloudflared")
                return False
        
        else:  # Linux
            Logger.info("Please install manually:")
            Logger.info("wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb")
            Logger.info("sudo dpkg -i cloudflared-linux-amd64.deb")
            return False
    
    @staticmethod
    def install_ffmpeg():
        """Install FFmpeg"""
        Logger.info("Installing FFmpeg...")
        
        if DependencyInstaller.is_windows():
            return DependencyInstaller.install_ffmpeg_windows()
        
        elif DependencyInstaller.is_mac():
            try:
                subprocess.run(["brew", "install", "ffmpeg"], check=True)
                Logger.success("FFmpeg installed via brew")
                return True
            except:
                Logger.error("Failed to install FFmpeg via brew")
                Logger.info("Please install manually: brew install ffmpeg")
                return False
        
        else:  # Linux
            try:
                subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=True)
                Logger.success("FFmpeg installed via apt")
                return True
            except:
                Logger.error("Failed to install FFmpeg")
                Logger.info("Please install manually: sudo apt-get install ffmpeg")
                return False
    
    @staticmethod
    def install_mediamtx():
        """Install MediaMTX"""
        Logger.info("Installing MediaMTX...")
        
        if DependencyInstaller.is_windows():
            return DependencyInstaller.install_mediamtx_windows()
        
        elif DependencyInstaller.is_mac():
            try:
                subprocess.run(["brew", "install", "mediamtx"], check=True)
                Logger.success("MediaMTX installed via brew")
                return True
            except:
                Logger.error("Failed to install MediaMTX via brew")
                Logger.info("Please install manually: brew install mediamtx")
                return False
        
        else:  # Linux
            Logger.info("Please install MediaMTX manually:")
            Logger.info("Download from https://github.com/bluenviron/mediamtx/releases")
            return False
    
    @staticmethod
    def install_tesseract_windows():
        """Install Tesseract OCR on Windows"""
        Logger.info("Installing Tesseract OCR...")
        try:
            # Try using winget (without silent to see output)
            Logger.info("Running: winget install --id UB-Mannheim.TesseractOCR")
            result = subprocess.run(
                ["winget", "install", "--id", "UB-Mannheim.TesseractOCR", "--accept-package-agreements", "--accept-source-agreements"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Check output for success indicators
            output_lower = (result.stdout + result.stderr).lower()
            if result.returncode == 0 or "successfully installed" in output_lower or "installed" in output_lower:
                Logger.success("Tesseract OCR installed via winget")
                Logger.warning("Please close and reopen your terminal for PATH to update")
                return True
            else:
                # Show the actual error
                if result.stderr:
                    error_msg = result.stderr[:300]
                    Logger.warning(f"winget error: {error_msg}")
                if result.stdout:
                    output_msg = result.stdout[:300]
                    Logger.info(f"winget output: {output_msg}")
                
                # Check if it's an elevation issue
                if "administrator" in output_lower or "elevation" in output_lower or "access denied" in output_lower:
                    Logger.warning("Administrator rights may be required")
                    Logger.info("Try running PowerShell as Administrator, then run:")
                    Logger.info("winget install --id UB-Mannheim.TesseractOCR")
                
                Logger.info("You can also download from: https://github.com/UB-Mannheim/tesseract/wiki")
                return False
        except FileNotFoundError:
            Logger.error("winget not found. Please install winget first or install Tesseract manually")
            Logger.info("Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
            return False
        except subprocess.TimeoutExpired:
            Logger.error("Installation timed out")
            Logger.info("Please install Tesseract OCR manually:")
            Logger.info("Run: winget install --id UB-Mannheim.TesseractOCR")
            return False
        except Exception as e:
            Logger.warning(f"Installation error: {e}")
            Logger.info("Please install Tesseract OCR manually:")
            Logger.info("Run: winget install --id UB-Mannheim.TesseractOCR")
            Logger.info("Or download from: https://github.com/UB-Mannheim/tesseract/wiki")
            return False
    
    @staticmethod
    def install_tesseract():
        """Install Tesseract OCR"""
        Logger.info("Installing Tesseract OCR...")
        
        if DependencyInstaller.is_windows():
            return DependencyInstaller.install_tesseract_windows()
        
        elif DependencyInstaller.is_mac():
            try:
                subprocess.run(["brew", "install", "tesseract"], check=True)
                Logger.success("Tesseract OCR installed via brew")
                return True
            except:
                Logger.error("Failed to install Tesseract OCR via brew")
                Logger.info("Please install manually: brew install tesseract")
                return False
        
        else:  # Linux
            try:
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", "tesseract-ocr"], check=True)
                Logger.success("Tesseract OCR installed via apt")
                return True
            except:
                Logger.error("Failed to install Tesseract OCR")
                Logger.info("Please install manually: sudo apt-get install tesseract-ocr")
                return False
    
    @staticmethod
    def check_and_install_all():
        """Check and install all dependencies"""
        missing = []
        
        print("")
        Logger.info("Checking dependencies...")
        print("")
        
        # Check Cloudflared
        if not DependencyInstaller.check_command("cloudflared"):
            Logger.warning("Cloudflared not found")
            missing.append("cloudflared")
        else:
            Logger.success("Cloudflared found")
        
        # Check FFmpeg
        if not DependencyInstaller.check_command("ffmpeg"):
            Logger.warning("FFmpeg not found")
            missing.append("ffmpeg")
        else:
            Logger.success("FFmpeg found")
        
        # Check MediaMTX
        if not DependencyInstaller.check_command("mediamtx"):
            Logger.warning("MediaMTX not found")
            missing.append("mediamtx")
        else:
            Logger.success("MediaMTX found")
        
        # Check Tesseract OCR
        if not DependencyInstaller.check_command("tesseract"):
            Logger.warning("Tesseract OCR not found")
            missing.append("tesseract")
        else:
            Logger.success("Tesseract OCR found")
        
        if not missing:
            print("")
            Logger.success("All dependencies installed!")
            print("")
            return True
        
        # Ask user if they want to auto-install
        print("\nMissing dependencies:", ", ".join(missing))
        response = input("\nAttempt auto-install? (y/n): ")
        if response.lower() != 'y':
            Logger.info("Please install manually and try again")
            return False
        
        print("")
        
        # Try to install missing
        installed_any = False
        
        if "cloudflared" in missing:
            if DependencyInstaller.install_cloudflared():
                installed_any = True
            print("")
        
        if "ffmpeg" in missing:
            if DependencyInstaller.install_ffmpeg():
                installed_any = True
            print("")
        
        if "mediamtx" in missing:
            if DependencyInstaller.install_mediamtx():
                installed_any = True
            print("")
        
        if "tesseract" in missing:
            if DependencyInstaller.install_tesseract():
                installed_any = True
            print("")
        
        if installed_any:
            Logger.warning("Installation complete!")
            Logger.warning("IMPORTANT: Close this terminal and open a new one")
            Logger.warning("Then run 'remoto start' again")
            print("")
            sys.exit(0)
        
        return False