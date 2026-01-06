import sys
import time
import click
from pathlib import Path

from cli.orchestrator import Orchestrator
from cli.utils.logger import Logger


@click.group()
@click.version_option(version="1.0.0")
def main():
    """
    Remote AI - Voice-controlled computer automation
    
    Control your computer from anywhere using just your voice.
    """
    pass


@main.command()
@click.option('--no-frontend', is_flag=True, help="Don't start frontend (backend only)")
@click.option('--skip-check', is_flag=True, help="Skip dependency check (use if you know dependencies are installed)")
def start(no_frontend, skip_check):
    """Start all Remote AI services"""
    orchestrator = Orchestrator()
    orchestrator.start(start_frontend=not no_frontend, skip_dependency_check=skip_check)


@main.command()
def stop():
    """Stop all Remote AI services"""
    orchestrator = Orchestrator()
    orchestrator.stop()


@main.command()
def status():
    """Show status of all services"""
    orchestrator = Orchestrator()
    orchestrator.status()


@main.command()
def setup():
    """Check and install required dependencies"""
    from cli.utils.installer import DependencyInstaller
    DependencyInstaller.check_and_install_all()


@main.group(invoke_without_command=True)
@click.pass_context
def password(ctx):
    """Manage session password"""
    # If no subcommand, show password (backward compatibility)
    if ctx.invoked_subcommand is None:
        data_dir = Path.home() / ".remoto" / "data"
        password_file = data_dir / "session_password.txt"
        
        if password_file.exists():
            with open(password_file) as f:
                pwd = f.read().strip()
            print(f"\nCurrent Session Password: {pwd}\n")
        else:
            print("\nNo active session\n")


@password.command()
def show():
    """Show current session password"""
    data_dir = Path.home() / ".remoto" / "data"
    password_file = data_dir / "session_password.txt"
    
    if password_file.exists():
        with open(password_file) as f:
            pwd = f.read().strip()
        print(f"\nCurrent Session Password: {pwd}\n")
    else:
        print("\nNo active session\n")


@password.command()
@click.option('--new-password', '-p', help='New password to set (if not provided, will prompt or generate)')
@click.option('--generate', '-g', is_flag=True, help='Generate a random password')
def set(new_password, generate):
    """Set a new session password"""
    from cli.utils.security import SecurityUtils
    from cli.orchestrator import Orchestrator
    
    data_dir = Path.home() / ".remoto" / "data"
    password_file = data_dir / "session_password.txt"
    
    # Determine new password
    if generate:
        new_pwd = SecurityUtils.generate_password()
        Logger.info("Generated new random password")
    elif new_password:
        new_pwd = new_password
    else:
        # Prompt for password
        import getpass
        new_pwd = getpass.getpass("Enter new password (or press Enter to generate random): ")
        if not new_pwd:
            new_pwd = SecurityUtils.generate_password()
            Logger.info("Generated new random password")
    
    # Validate password
    if len(new_pwd) < 8:
        Logger.error("Password must be at least 8 characters long")
        sys.exit(1)
    
    # Save new password
    password_file.parent.mkdir(parents=True, exist_ok=True)
    with open(password_file, 'w') as f:
        f.write(new_pwd)
    
    Logger.success(f"Password updated successfully")
    print(f"\nNew Session Password: {new_pwd}\n")
    
    # If backend is running, restart it with new password
    orchestrator = Orchestrator()
    if orchestrator.backend.is_running():
        Logger.info("Backend is running. Restarting with new password...")
        
        # Get current stream URL from stream tunnel
        stream_tunnel_url = orchestrator.stream_tunnel.get_url()
        if not stream_tunnel_url:
            Logger.warning("Could not get stream tunnel URL. Backend may need manual restart.")
            print("Please run 'remoto restart' to apply the new password.\n")
            return
        
        # Restart backend with new password
        orchestrator.backend.stop()
        time.sleep(2)
        orchestrator.backend.start(stream_tunnel_url, new_pwd)
        Logger.success("Backend restarted with new password")
        print("")


@main.command()
def restart():
    """Restart all services"""
    orchestrator = Orchestrator()
    orchestrator.stop()
    time.sleep(2)
    orchestrator.start(start_frontend=True)


if __name__ == '__main__':
    main()