import sys
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
@click.option('--no-browser', is_flag=True, help="Don't open browser automatically")
@click.option('--no-frontend', is_flag=True, help="Don't start frontend (backend only)")
def start(no_browser, no_frontend):
    """Start all Remote AI services"""
    orchestrator = Orchestrator()
    orchestrator.start(open_browser=not no_browser, start_frontend=not no_frontend)


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


@main.command()
def password():
    """Show current session password"""
    data_dir = Path.home() / ".remoto" / "data"
    password_file = data_dir / "session_password.txt"
    
    if password_file.exists():
        with open(password_file) as f:
            pwd = f.read().strip()
        print(f"\nCurrent Session Password: {pwd}\n")
    else:
        print("\nNo active session\n")


@main.command()
def url():
    """Show current tunnel URL"""
    data_dir = Path.home() / ".remoto" / "data"
    url_file = data_dir / "tunnel_url.txt"
    
    if url_file.exists():
        with open(url_file) as f:
            tunnel_url = f.read().strip()
        print(f"\nTunnel URL: {tunnel_url}")
        print(f"Stream URL: {tunnel_url}/screen\n")
    else:
        print("\nNo active tunnel\n")


@main.command()
def restart():
    """Restart all services"""
    orchestrator = Orchestrator()
    orchestrator.stop()
    import time
    time.sleep(2)
    orchestrator.start()


if __name__ == '__main__':
    main()