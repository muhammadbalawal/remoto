import pyautogui
import io
import os
import time
import base64
import re
import secrets
from PIL import Image
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import anthropic
import uvicorn
from typing import List, Optional, Tuple
import tempfile
from gtts import gTTS
import pytesseract
import cv2
import numpy as np
import sys
import shutil
from pathlib import Path

load_dotenv()

# Configure Tesseract path if needed (Windows)
if sys.platform == 'win32':
    # First check if tesseract is in PATH
    tesseract_found = shutil.which('tesseract') or shutil.which('tesseract.exe')
    
    if not tesseract_found:
        # Try common installation paths
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME', '')),
        ]
        for path in possible_paths:
            if Path(path).exists():
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"Found Tesseract at: {path}")
                break
        else:
            print("WARNING: Tesseract OCR not found. OCR functionality will not work.")
            print("Please install Tesseract: winget install --id UB-Mannheim.TesseractOCR")
    else:
        print(f"Found Tesseract in PATH: {tesseract_found}")

# ============= SECURITY =============
# Session password (generated on startup or from env)
SESSION_PASSWORD = os.getenv("REMOTE_AI_PASSWORD") or secrets.token_urlsafe(16)
security = HTTPBasic()

def verify_password(credentials: HTTPBasicCredentials = Depends(security)):
    """Simple password authentication"""
    correct_password = secrets.compare_digest(credentials.password, SESSION_PASSWORD)
    if not correct_password:
        raise HTTPException(
            status_code=401,
            detail="Invalid password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

# ============= FASTAPI APP =============
app = FastAPI(title="Remote AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= SERVE STATIC FILES =============
app.mount("/static", StaticFiles(directory="server/static"), name="static")

@app.get("/")
async def home(authenticated: bool = Depends(verify_password)):
    """Serve the main HTML page"""
    return FileResponse("server/static/index.html")

# ============= CONFIG ENDPOINT =============
@app.get("/config")
async def get_config(authenticated: bool = Depends(verify_password)):
    """Provide configuration to frontend (requires authentication)"""
    return JSONResponse({
        "streamUrl": os.getenv("STREAM_URL", ""),
        "apiUrl": "http://localhost:8000",
        "passwordRequired": True,
        "password": SESSION_PASSWORD  # Safe to return since user is already authenticated
    })

# ============= HEALTH CHECK =============
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "remote-ai-backend"}

# ============= MODELS =============
class ChatMessage(BaseModel):
    role: str
    content: str

class VoiceRequest(BaseModel):
    text: str
    history: Optional[List[ChatMessage]] = []

class VoiceResponse(BaseModel):
    assistant_message: str
    assistant_audio_base64: Optional[str] = None
    code_executed: Optional[str] = None
    execution_result: str
    screenshot_base64: str
    success: bool

# ============= SYSTEM PROMPT =============
SYSTEM_PROMPT = """You are a voice-controlled computer assistant. The user is remotely accessing their computer via voice commands on their phone.

Your job: Execute EXACTLY what the user asks. You can combine multiple RELATED steps into one response, but don't do unrelated tasks together.

CONVERSATION AWARENESS:
- You have access to recent conversation history
- Use context from previous exchanges to understand references like "it", "that file", "the same folder"
- If user provides information in response to your question, USE IT immediately
- Don't ask for information you already have from conversation history
- If you asked "what should I name the file?" and user says "test.js", just create/save it as test.js

AVAILABLE COMMANDS:

KEYBOARD:
pyautogui.press('key') - Press a single key
pyautogui.hotkey('key1', 'key2', ...) - Press multiple keys together  
pyautogui.write('text', interval=0.05) - Type text (use for all text input)
time.sleep(seconds) - Wait (use 0.5-2.0 seconds between actions)

MOUSE:
pyautogui.click(x, y) - Click at coordinates (x, y)
pyautogui.click(x, y, clicks=2) - Double click at coordinates
pyautogui.rightClick(x, y) - Right click at coordinates
pyautogui.moveTo(x, y, duration=0.5) - Move mouse smoothly to position (with tweening)
pyautogui.dragTo(x, y, duration=0.5) - Drag to position
pyautogui.scroll(clicks) - Scroll up (positive) or down (negative)

TEXT DETECTION:
You will receive OCR text extracted from the screenshot showing:
- Detected text and their approximate positions
- Use this to find buttons, links, menu items, etc.
- Combine OCR positions with click commands

CRITICAL COORDINATE INFORMATION:
- The screenshot you see is 1280x720 resolution
- OCR coordinates are provided in this 1280x720 space
- The system will automatically scale your coordinates to the actual screen resolution
- Just use the coordinates from the OCR data directly - no scaling needed on your end
- Example: If OCR shows "Compose" at (79, 183), use pyautogui.click(79, 183)

MULTI-STEP EXECUTION RULES:
✅ COMBINE these related actions:
- Opening app + navigating to URL (e.g., "open chrome and go to gmail.com")
- Opening app + opening file (e.g., "open vscode and open homework folder")
- Clicking + typing (e.g., "click search bar and type hello")
- Navigation sequences (e.g., "go to desktop and open homework folder")
- Saving files - DON'T ask for filename, use a default like "document.txt" or infer from context

❌ DON'T combine unrelated actions:
- Different applications (e.g., don't open Chrome AND VSCode together)
- Actions requiring user verification (e.g., don't send email without confirmation)
- Complex multi-stage workflows across different contexts

❌ NEVER ASK FOR:
- Filenames (use defaults: "document.txt", "file.js", "note.md", etc.)
- Confirmation for simple actions (clicking, typing, opening apps)
- Information you already have from conversation history

OPENING APPLICATIONS (Windows Search - PREFERRED):
pyautogui.press('win'); time.sleep(0.5); pyautogui.write('app_name', interval=0.05); time.sleep(0.3); pyautogui.press('enter'); time.sleep(2)

Common apps: vscode, notepad, chrome, firefox, edge, powershell, git bash, cmd, file explorer (write 'explorer')

BROWSER WORKFLOW:
To open browser and navigate:
pyautogui.press('win'); time.sleep(0.5); pyautogui.write('chrome', interval=0.05); time.sleep(0.3); pyautogui.press('enter'); time.sleep(2.5); pyautogui.hotkey('ctrl', 'l'); time.sleep(0.3); pyautogui.write('gmail.com', interval=0.05); pyautogui.press('enter'); time.sleep(2)

SAVING FILES:
When user asks to save:
1. Check if they mentioned a filename - use it
2. If not, use a sensible default based on context
3. Press Ctrl+S, wait, type filename, press Enter
Example: pyautogui.hotkey('ctrl', 's'); time.sleep(0.5); pyautogui.write('document.txt', interval=0.05); pyautogui.press('enter')

NAVIGATING FILE EXPLORER:
- Open: pyautogui.hotkey('win', 'e'); time.sleep(1)
- Type path in address bar: pyautogui.hotkey('alt', 'd'); time.sleep(0.3); pyautogui.write('path', interval=0.05); pyautogui.press('enter')
- Desktop: pyautogui.hotkey('alt', 'd'); pyautogui.write('Desktop', interval=0.05); pyautogui.press('enter')

COMMON SHORTCUTS:
- Copy: Ctrl+C
- Paste: Ctrl+V
- Save: Ctrl+S
- Select all: Ctrl+A
- Find: Ctrl+F
- Close tab: Ctrl+W
- Close window: Alt+F4
- Switch apps: Alt+Tab
- Show desktop: Win+D
- Address bar (browser): Ctrl+L
- New tab (browser): Ctrl+T

CLICKING STRATEGY:
1. Look for the text/button in the OCR results
2. Use the position (x, y) to click it
3. If OCR doesn't detect it, use keyboard shortcuts as fallback
4. Use moveTo with duration for smooth, visible mouse movement
5. Always wait (time.sleep) after clicks for UI to respond

VOICE INTERACTION RULES:
1. Be conversational and natural - this is VOICE, not text chat
2. Keep responses SHORT (1-2 sentences max) - user is listening, not reading
3. Confirm actions: "Opening Chrome and going to Gmail" or "Saving as document.txt"
4. If you see an error or something unexpected, briefly explain: "I don't see that button"
5. RARELY ask for clarification - use context and make reasonable assumptions
6. You can execute multiple related steps without asking - be efficient
7. After action, briefly describe result: "Done" or "Gmail is loading"
8. Be helpful but concise - remember they're on their phone
9. If you just asked a question and user answered it, ACT on that answer immediately

RESPONSE FORMAT:
You MUST respond with BOTH parts:
1. <voice> tag: What you'll say to the user (keep it SHORT)
2. <code> tag: Python code to execute (can be multiple lines for related actions)

Format:
<voice>Your brief spoken response</voice>
<code>
pyautogui.click(500, 300)
time.sleep(0.5)
pyautogui.write('hello', interval=0.05)
</code>

If no action needed (just clarifying/responding), only use <voice> tag.

Examples:

User: "Open Chrome and go to Gmail"
<voice>Opening Chrome and going to Gmail</voice>
<code>
pyautogui.press('win')
time.sleep(0.5)
pyautogui.write('chrome', interval=0.05)
time.sleep(0.3)
pyautogui.press('enter')
time.sleep(2.5)
pyautogui.hotkey('ctrl', 'l')
time.sleep(0.3)
pyautogui.write('gmail.com', interval=0.05)
pyautogui.press('enter')
time.sleep(2)
</code>

User: "Save this file"
<voice>Saving as document.txt</voice>
<code>
pyautogui.hotkey('ctrl', 's')
time.sleep(0.5)
pyautogui.write('document.txt', interval=0.05)
pyautogui.press('enter')
time.sleep(0.5)
</code>

User (after being asked): "test.js"
<voice>Saving as test.js</voice>
<code>
pyautogui.write('test.js', interval=0.05)
pyautogui.press('enter')
time.sleep(0.5)
</code>

User: "Click the submit button"
<voice>Clicking submit</voice>
<code>
pyautogui.moveTo(850, 600, duration=0.3)
pyautogui.click()
time.sleep(0.5)
</code>

User: "Open notepad and type hello world"
<voice>Opening Notepad and typing hello world</voice>
<code>
pyautogui.press('win')
time.sleep(0.5)
pyautogui.write('notepad', interval=0.05)
time.sleep(0.3)
pyautogui.press('enter')
time.sleep(2)
pyautogui.write('hello world', interval=0.05)
time.sleep(0.3)
</code>

User: "Scroll down"
<voice>Scrolling down</voice>
<code>
pyautogui.scroll(-3)
time.sleep(0.3)
</code>

User: "Search for python tutorials on Google"
<voice>Searching Google for python tutorials</voice>
<code>
pyautogui.press('win')
time.sleep(0.5)
pyautogui.write('chrome', interval=0.05)
time.sleep(0.3)
pyautogui.press('enter')
time.sleep(2.5)
pyautogui.hotkey('ctrl', 'l')
time.sleep(0.3)
pyautogui.write('google.com', interval=0.05)
pyautogui.press('enter')
time.sleep(2)
pyautogui.write('python tutorials', interval=0.05)
pyautogui.press('enter')
time.sleep(1.5)
</code>

Remember: 
- Use conversation history to understand context
- Don't ask unnecessary questions
- Combine RELATED steps for efficiency
- Keep voice responses BRIEF and NATURAL
- Use appropriate wait times between actions (longer for apps to load)
- User is on their phone listening, so be concise
- Make reasonable assumptions rather than asking for clarification"""

def get_screenshot_with_ocr() -> Tuple[str, str, float]:
    """
    Capture screenshot and extract text with OCR
    Returns: (screenshot_base64, ocr_text_with_positions, scale_factor)
    """
    # Capture full resolution screenshot
    screenshot = pyautogui.screenshot()
    original_width, original_height = screenshot.size
    
    # Target size for transmission
    target_width = 1280
    target_height = 720
    
    # Resize screenshot for transmission
    screenshot_resized = screenshot.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # Run OCR on the resized image so coordinates match what Claude sees
    screenshot_cv = cv2.cvtColor(np.array(screenshot_resized), cv2.COLOR_RGB2BGR)
    
    # Perform OCR with position data
    ocr_data = pytesseract.image_to_data(screenshot_cv, output_type=pytesseract.Output.DICT)
    
    # Build OCR text with positions
    ocr_info = []
    n_boxes = len(ocr_data['text'])
    for i in range(n_boxes):
        text = ocr_data['text'][i].strip()
        if text:
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w = ocr_data['width'][i]
            h = ocr_data['height'][i]
            conf = ocr_data['conf'][i]
            
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Only include text with reasonable confidence
            if conf > 30:
                ocr_info.append(f'"{text}" at ({center_x}, {center_y})')
    
    ocr_text = "\n".join(ocr_info) if ocr_info else "No text detected"
    
    buffered = io.BytesIO()
    screenshot_resized.save(buffered, format="PNG", optimize=True, quality=85)
    screenshot_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    # Calculate reverse scale factor (resized coords -> actual screen coords)
    scale_factor = original_width / target_width
    
    return screenshot_base64, ocr_text, scale_factor

def text_to_speech(text: str) -> Optional[str]:
    """Convert text to speech using gTTS (free, no API key needed)"""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
            temp_path = temp_audio.name
        
        tts.save(temp_path)
        
        with open(temp_path, 'rb') as f:
            audio_bytes = f.read()
        
        os.unlink(temp_path)
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        return audio_base64
        
    except Exception as e:
        print(f"TTS error: {e}")
        return None

def ask_claude_voice(user_message: str, screenshot_b64: str, ocr_text: str, conversation_history: Optional[List[ChatMessage]] = None) -> tuple[str, str, str]:
    """
    Ask Claude to execute a voice instruction with OCR data
    Returns: (voice_response, code_to_execute, full_response)
    """
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    messages = []
    
    # Build conversation context string for better awareness
    conversation_context = ""
    if conversation_history and len(conversation_history) > 0:
        conversation_context = "\n\nRECENT CONVERSATION:\n"
        # Show last 6 messages for context
        recent = conversation_history[-6:]
        for msg in recent:
            role_label = "User" if msg.role == "user" else "You"
            conversation_context += f"{role_label}: {msg.content}\n"
        conversation_context += "\n"
    
    # Add conversation history as actual messages
    if conversation_history:
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
    
    # Build the context text with conversation awareness
    context_text = f"[Current screenshot attached]\n\nDetected text on screen:\n{ocr_text}{conversation_context}Current user request: \"{user_message}\""
    
    messages.append({
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": screenshot_b64,
                },
            },
            {
                "type": "text",
                "text": context_text
            }
        ],
    })
    
    response = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        max_tokens=1000,
        temperature=0.0,
        system=SYSTEM_PROMPT,
        messages=messages
    )
    
    full_response = response.content[0].text
    
    voice_match = re.search(r'<voice>(.*?)</voice>', full_response, re.DOTALL)
    code_match = re.search(r'<code>(.*?)</code>', full_response, re.DOTALL)
    
    voice_response = voice_match.group(1).strip() if voice_match else full_response
    code = code_match.group(1).strip() if code_match else ""
    
    voice_response = re.sub(r'<[^>]+>', '', voice_response).strip()
    
    return voice_response, code, full_response

def parse_and_clean_code(code: str, scale_factor: float = 1.0) -> str:
    """
    Clean up code for execution and scale mouse coordinates
    """
    code = code.replace("```python", "").replace("```", "").strip()
    
    lines = []
    for line in code.split('\n'):
        line = line.strip()
        if line and (
            'pyautogui' in line or 
            'time.sleep' in line or 
            line.startswith('import')
        ):
            # Scale mouse coordinates if scale_factor != 1.0
            if scale_factor != 1.0 and any(fn in line for fn in ['click', 'moveTo', 'dragTo', 'rightClick']):
                # Extract coordinates and scale them
                # Match patterns like: pyautogui.click(100, 200)
                coord_pattern = r'(\d+),\s*(\d+)'
                match = re.search(coord_pattern, line)
                if match:
                    x = int(match.group(1))
                    y = int(match.group(2))
                    
                    # Scale to actual screen coordinates
                    scaled_x = int(x * scale_factor)
                    scaled_y = int(y * scale_factor)
                    
                    # Replace coordinates in the line
                    line = re.sub(coord_pattern, f'{scaled_x}, {scaled_y}', line, count=1)
            
            lines.append(line)
    
    return '\n'.join(lines)

@app.post("/voice", response_model=VoiceResponse)
async def voice_command(request: VoiceRequest):
    """
    Main voice command endpoint with OCR and mouse support
    """
    print("\n" + "=" * 60)
    print(f"USER SAID: {request.text}")
    print("=" * 60 + "\n")
    
    print("Capturing screenshot and running OCR...")
    screenshot_b64, ocr_text, scale_factor = get_screenshot_with_ocr()
    print(f"OCR detected {len(ocr_text.split(chr(10)))} text elements")
    print(f"Scale factor: {scale_factor:.2f}x (resized -> actual screen)\n")
    
    try:
        voice_response, code, full_response = ask_claude_voice(
            request.text,
            screenshot_b64,
            ocr_text,
            request.history
        )
        
        print(f"ASSISTANT SAYS: \"{voice_response}\"")
        if code:
            print(f"\nCODE TO EXECUTE (before scaling):\n{code}\n")
        
        execution_result = "No action needed"
        cleaned_code = None
        
        if code:
            cleaned_code = parse_and_clean_code(code, scale_factor)
            print(f"EXECUTING CODE (after scaling):\n{cleaned_code}\n")
            
            try:
                exec(cleaned_code)
                execution_result = "Executed successfully"
                print(execution_result)
            except Exception as e:
                execution_result = f"Execution error: {str(e)}"
                print(execution_result)
                voice_response = f"I tried but got an error. {voice_response}"
        
        print("Generating speech response...")
        audio_base64 = text_to_speech(voice_response)
        
        if cleaned_code:
            time.sleep(1.2)
        
        # Get new screenshot after action
        new_screenshot_b64, _, _ = get_screenshot_with_ocr()
        
        print("Request completed\n")
        
        return VoiceResponse(
            assistant_message=voice_response,
            assistant_audio_base64=audio_base64,
            code_executed=cleaned_code,
            execution_result=execution_result,
            screenshot_base64=new_screenshot_b64,
            success=True
        )
        
    except Exception as e:
        error_msg = "Sorry, something went wrong on my end"
        print(f"ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
        
        return VoiceResponse(
            assistant_message=error_msg,
            assistant_audio_base64=text_to_speech(error_msg),
            code_executed=None,
            execution_result=f"Error: {str(e)}",
            screenshot_base64=screenshot_b64,
            success=False
        )

# ============= STARTUP MESSAGE =============
@app.on_event("startup")
async def startup_event():
    """Display startup information"""
    print("\n" + "=" * 60)
    print("REMOTE AI BACKEND STARTED")
    print("=" * 60)
    print(f"Session Password: {SESSION_PASSWORD}")
    print(f"API URL: http://localhost:8000")
    print(f"Stream URL: {os.getenv('STREAM_URL', 'Not set yet')}")
    print("=" * 60 + "\n")

if __name__ == "__main__":    
    uvicorn.run(app, host="0.0.0.0", port=8000)
