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
- Receives transcribed text from speech input
- Captures screen content using OpenCV for image processing
- Extracts textual context using Tesseract OCR
- Analyzes screen state and user intent to generate executable commands
- Executes actions via pyautogui for keyboard and mouse control
- Provides audio confirmation through Google Text-to-Speech

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





## Install guide for windows

### Streaming Flow
   
   1. **MediaMtx** Install the lastest version and the path to your environment variable make sure the ymal file is in the same place as .exe : [https://mediamtx.org/](https://mediamtx.org/)
   2. **FFmpeg** Install the lastest version and the path to your environment variable : [https://ffmpeg.org/](https://ffmpeg.org/)
   3. **Cloudflare** I found it eazier to use `winget install Cloudflare.Cloudflared` to install Cloudflared.
      
   -   To stream your screen:
       -  Setup .yml file first before you run MediaMtx
         ```
            logLevel: info
            logDestinations: [stdout]
            
            # Global timeouts
            readTimeout: 3600s
            writeTimeout: 3600s
            
            # RTSP Server
            rtsp: yes
            rtspAddress: :8554
            rtspTransports: [tcp]
            rtspEncryption: "no"
            
            # HLS Server
            hls: yes
            hlsAddress: :8888
            hlsEncryption: no
            hlsAllowOrigin: '*'
            hlsAlwaysRemux: yes
            hlsVariant: lowLatency
            hlsSegmentCount: 7
            hlsSegmentDuration: 1s
            hlsPartDuration: 200ms
            hlsMuxerCloseAfter: 3600s
            
            # Disable unused
            rtmp: no
            webrtc: no
            srt: no
            api: no
            metrics: no
            pprof: no
            playback: no
            
            # Paths
            pathDefaults:
              source: publisher
            
            paths:
              screen:
                source: publisher
         ```
       -  Run FFmpeg with options see all on [documentaion](https://ffmpeg.org/documentation.html)

            ```
            ONLY WORKS FOR COMPUTERS WITH NVIDIA GPUS
            ffmpeg -f gdigrab -framerate 30 -i desktop \
                 -vf fps=30 \
                 -c:v h264_nvenc -preset p1 -tune ll \
                 -b:v 3M -g 60 -keyint_min 60 \
                 -f rtsp -rtsp_transport tcp \
                 rtsp://127.0.0.1:8554/screen
            
            THIS IS FOR ANY WINDOWS COMPUTER (INCREDIBLY SLOW)
            ffmpeg -f gdigrab -framerate 30 -i desktop \
              -vf fps=30 \
              -c:v libx264 -preset ultrafast -tune zerolatency \
              -b:v 3M -g 60 -keyint_min 60 \
              -f rtsp -rtsp_transport tcp \
              rtsp://127.0.0.1:8554/screen
            
            AMD GPUS
            ffmpeg -f gdigrab -framerate 30 -i desktop \
              -vf fps=30 \
              -c:v h264_amf -quality speed \
              -b:v 3M -g 60 -keyint_min 60 \
              -f rtsp -rtsp_transport tcp \
              rtsp://127.0.0.1:8554/screen
            ```
       -  Use Cloudflare to open a port
            ```cloudflared tunnel --url http://localhost:8888```

### FrontEnd

   1. Clone this repo.
   2. Add a `.env.local` file that contains your Supabase credentials:
   
      ```env
      NEXT_PUBLIC_SUPABASE_URL=
      NEXT_PUBLIC_SUPABASE_ANON_KEY=
      ```   

### BackEnd
   [github](https://github.com/aleburrascano/remoto-backend)

## Install guide for MACOS


      ## RemotoMacQuickInstall
      ```
      #!/bin/bash
      set -e  
      if [[ "$OSTYPE" != "darwin"* ]]; then
          exit 1
      fi
      
      if ! command -v brew &> /dev/null; then
          /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
          if [[ $(uname -m) == "arm64" ]]; then
              echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
              eval "$(/opt/homebrew/bin/brew shellenv)"
          fi
      fi
      
      if ! brew list mediamtx &> /dev/null; then
          brew install mediamtx
      fi
      
      if ! brew list ffmpeg &> /dev/null; then
          brew install ffmpeg
      fi
      
      if ! brew list cloudflared &> /dev/null; then
          brew install cloudflare/cloudflare/cloudflared
      fi
      
      CONFIG_DIR="/opt/homebrew/etc/mediamtx"
      mkdir -p "$CONFIG_DIR"
      
      if [ -f "$CONFIG_DIR/mediamtx.yml" ]; then
          cp "$CONFIG_DIR/mediamtx.yml" "$CONFIG_DIR/mediamtx.yml.backup.$(date +%s)"
      fi
      
      cat > "$CONFIG_DIR/mediamtx.yml" << 'EOF'
      logLevel: info
      logDestinations: [stdout]
      readTimeout: 10s
      writeTimeout: 10s
      writeQueueSize: 512
      udpMaxPayloadSize: 1472
      
      authMethod: internal
      authInternalUsers:
      - user: any
        pass:
        ips: []
        permissions:
        - action: publish
        - action: read
        - action: playback
      
      rtsp: yes
      rtspAddress: :8554
      rtspTransports: [tcp]
      rtspEncryption: "no"
      
      hls: yes
      hlsAddress: :8888
      hlsEncryption: no
      hlsAllowOrigin: '*'
      hlsAlwaysRemux: yes
      hlsVariant: lowLatency
      hlsSegmentCount: 7
      hlsSegmentDuration: 1s
      hlsPartDuration: 200ms
      hlsSegmentMaxSize: 50M
      hlsDirectory: ''
      
      rtmp: no
      webrtc: no
      srt: no
      api: no
      metrics: no
      pprof: no
      playback: no
      
      pathDefaults:
        source: publisher
        record: no
      
      paths:
        screen:
          source: publisher
      EOF
      
      SCRIPTS_DIR="$HOME/.screen-streaming"
      mkdir -p "$SCRIPTS_DIR"
      
      cat > "$SCRIPTS_DIR/start-streaming.sh" << 'STARTEOF'
      #!/bin/bash
      
      brew services start mediamtx
      sleep 3
      
      ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep "AVFoundation video devices" -A 20 | grep "\[AVFoundation"
      
      read -p "Enter display number (usually 0, 1, 2, or 3): " DISPLAY_NUM
      
      ffmpeg -f avfoundation -pixel_format nv12 -framerate 30 -i "$DISPLAY_NUM" \
        -vf fps=30 \
        -vsync 1 \
        -c:v h264_videotoolbox -b:v 5M \
        -g 30 -keyint_min 30 \
        -f rtsp rtsp://127.0.0.1:8554/screen &
      
      FFMPEG_PID=$!
      sleep 3
      
      cloudflared tunnel --url http://localhost:8888
      
      trap "kill $FFMPEG_PID 2>/dev/null; brew services stop mediamtx" EXIT
      STARTEOF
      
      chmod +x "$SCRIPTS_DIR/start-streaming.sh"
      
      cat > "$SCRIPTS_DIR/stop-streaming.sh" << 'STOPEOF'
      #!/bin/bash
      
      pkill -f "ffmpeg.*rtsp://127.0.0.1:8554/screen"
      pkill cloudflared
      brew services stop mediamtx
      STOPEOF
      
      chmod +x "$SCRIPTS_DIR/stop-streaming.sh"
      
      cat > "$SCRIPTS_DIR/status.sh" << 'STATUSEOF'
      #!/bin/bash
      
      brew services list | grep mediamtx
      
      if pgrep -f "ffmpeg.*rtsp://127.0.0.1:8554/screen" > /dev/null; then
          pgrep -f "ffmpeg.*rtsp://127.0.0.1:8554/screen"
      fi
      
      if pgrep cloudflared > /dev/null; then
          pgrep cloudflared
      fi
      STATUSEOF
      
      chmod +x "$SCRIPTS_DIR/status.sh"
      
      if [[ ":$PATH:" != *":$SCRIPTS_DIR:"* ]]; then
          echo "export PATH=\"\$PATH:$SCRIPTS_DIR\"" >> ~/.zshrc
      fi
      
      ```

      ## REMOOOTO MAC REQUIREMENTS

      mediamtx v1.15.3
      
      ffmpeg version 8.0
      
      cloudflared version 2025.11.1
      
      QUICK START GUIDE:
      
      Run RemotoMacQuickInstall to install all dependencies.
      
      Then in three separate terminal windows run:

      1. brew services start mediamtx
      2. ffmpeg -f avfoundation -pixel_format nv12 -framerate 30 -i "3" -vf fps=30 -c:v h264_videotoolbox -b:v 3M -g 60 -keyint_min 60 -f rtsp -rtsp_transport tcp rtsp://127.0.0.1:8554/screen
      3. cloudflared tunnel --url http://localhost:8888

      Copy paste the link that looks like this, https://[your-tunnel-name].trycloudflare.com, add /screen to the end, and paste it into
      livestream url in config.



