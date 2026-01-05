# Remote AI - Remote Computer Control System

## Project Overview

Remote AI enables secure remote access and control of home computer through voice commands from anywhere in the world. The system combines speech recognition, AI agent processing, and real-time streaming to allow users to interact with their remote computers from any location. Users authenticate via Supabase and communicate through a React-based interface that translates voice commands into executable actions on the target machine.

![Alt text](./public/Remoto.png)

## System Architecture

### Frontend Interface

Built with React and react-speech-recognition for speech-to-text conversion. The interface handles user authentication through Supabase and provides real-time video streaming from the remote computer.

### Backend Services

A Python service runs persistently on the local computer, managing authentication, command execution, and media streaming.

### AI Agent Core

The custom AI agent processes user commands through multiple stages:

-   Receives transcribed text from speech input
-   Captures screen content using OpenCV for image processing
-   Extracts textual context using Tesseract OCR
-   Analyzes screen state and user intent to generate executable commands
-   Executes actions via pyautogui for keyboard and mouse control
-   Provides audio confirmation through Google Text-to-Speech

### Media Streaming Pipeline

Live screen content is streamed using MediaMTX and FFmpeg for encoding, with global delivery handled through Cloudflare. This ensures low-latency visual feedback to users during remote sessions.

## Workflow Process

1. **Authentication & Connection**
   Users securely login through Supabase authentication, establishing a connection to their home computer running the Python backend service.

2. **Voice Command Processing**
   Speech input is captured via the React interface and converted to text using speech recognition libraries.

3. **Screen Analysis & Command Generation**
   The AI agent captures the current screen state, resizes images using OpenCV, and extracts UI context with Tesseract OCR. This contextual information combined with the user's command enables the agent to generate precise keyboard and mouse actions.

4. **Action Execution**
   Generated commands are executed on the remote computer using pyautogui, performing the requested operations with screen-relative precision.

5. **User Feedback**
   Upon task completion, the system provides audio confirmation via Google Text-to-Speech, informing users of successful command execution while the live stream displays the updated screen state.

## Technical Implementation

The system integrates multiple technologies including React for the user interface, Python for backend services, OpenCV and Tesseract for computer vision tasks, pyautogui for system control, and MediaMTX with Cloudflare for streaming delivery. Speech processing handles both input transcription and output audio responses, creating a seamless voice-controlled remote access experience.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/remoto.git
cd remoto

# Install the package
pip install -e .
```

### First Run

```bash
# Check and install dependencies
remoto setup

# Start all services
remoto start
```

## CLI Commands

```bash
remoto start          # Start all services
remoto stop           # Stop all services
remoto restart        # Restart all services
remoto status         # Show status of all services (includes URLs)
remoto setup          # Check and install dependencies
remoto password       # Show current session password
remoto password show  # Show current session password (explicit)
remoto password set   # Set a new session password
```

### Password Management

Manage your session password with the `password` command:

```bash
# Show current password
remoto password
# or
remoto password show

# Generate a random password
remoto password set --generate
# or
remoto password set -g

# Set a specific password
remoto password set --new-password "MySecurePass123"
# or
remoto password set -p "MySecurePass123"

# Interactive prompt (press Enter to generate random)
remoto password set
```

**Note:** If the backend is running when you change the password, it will automatically restart with the new password.

### Command Options

```bash
remoto start --no-frontend   # Start backend only (no web UI)
```

## Security Notes

-   **Session Passwords**: Passwords are auto-generated for each session and stored locally in `~/.remoto/data/session_password.txt`
-   **Password Management**: Use `remoto password set` to change your password at any time
-   **Password Requirements**: Passwords must be at least 8 characters long
-   **Secure Communication**: All communication goes through Cloudflare tunnels (HTTPS)
-   **HTTP Basic Auth**: API endpoints are protected with HTTP Basic Authentication
-   **Environment Variables**: Never commit `.env` files or session passwords to version control
-   **API Keys**: Store your `ANTHROPIC_API_KEY` in a `.env` file (not committed to git)

## Troubleshooting

### Services won't start

```bash
# Check dependencies
remoto setup

# Check service status
remoto status

# View logs (stored in ~/.remoto/logs/)
```

### Password issues

```bash
# View current password
remoto password

# Change password
remoto password set --generate

# If backend needs restart after password change
remoto restart
```

### FFmpeg encoding issues

-   Ensure your GPU drivers are up to date
-   Check that hardware encoding is supported: `ffmpeg -encoders | grep nvenc`
-   The CLI will automatically fall back to CPU encoding if needed

### Cloudflare tunnel issues

-   Ensure Cloudflared is installed and in PATH
-   Check firewall settings
-   Try restarting: `remoto restart`
