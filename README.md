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


## Install guide for MACOS



