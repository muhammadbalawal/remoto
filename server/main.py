import pyautogui
import io
import os
import time
import base64
import re
import secrets
import json
import asyncio
from PIL import Image
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from typing import List, Optional, Tuple, Dict, Any
import tempfile
from gtts import gTTS
import pytesseract
import cv2
import numpy as np
import sys
import shutil
from pathlib import Path
from backboard import BackboardClient
from server.tools import TOOL_DEFINITIONS, ToolExecutor

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

# ============= BACKBOARD INITIALIZATION =============
backboard_client = None
assistant = None
tool_executor = ToolExecutor()

# ============= FASTAPI APP =============
app = FastAPI(title="Remoto AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Map frontend thread_ids to Backboard thread_ids (for persistent memory)
thread_id_mapping: Dict[str, str] = {}  # frontend_id -> backboard_id

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

# ============= SSE ENDPOINT =============
# ============= MODELS =============
class ChatMessage(BaseModel):
    role: str
    content: str

class VoiceRequest(BaseModel):
    text: str
    thread_id: Optional[str] = None
    history: Optional[List[ChatMessage]] = []  # Kept for backward compatibility

class AnalysisData(BaseModel):
    model: Optional[str] = None
    complexity: Optional[str] = None
    tool_calls: Optional[List[dict]] = []

class VoiceResponse(BaseModel):
    assistant_message: str
    assistant_audio_base64: Optional[str] = None
    screenshot_base64: str
    thread_id: str
    success: bool
    analysis: Optional[AnalysisData] = None

# ============= SYSTEM PROMPT =============
SYSTEM_PROMPT = """You are Remoto AI - a voice-controlled computer assistant. The user is remotely controlling their computer via voice commands on their phone.

CORE BEHAVIOR:
- Execute exactly what the user asks
- Be conversational and concise (they're listening, not reading)
- Keep voice responses to 1-2 sentences maximum
- Use conversation history to understand context ("it", "that file", etc.)
- Make smart assumptions rather than asking for clarification
- Combine related steps, but not unrelated tasks

AVAILABLE TOOLS:
You have these tools for ALL operations:

Basic Actions:
- type_text: Type text on keyboard
- press_key: Press single key (enter, tab, esc, etc.)
- press_hotkey: Press key combos (ctrl+c, alt+tab, etc.)
- click_position: Click at coordinates from OCR
- scroll_page: Scroll up (positive) or down (negative)

Application Control:
- launch_app: Open Windows applications
- navigate_url: Open URLs in browser
- find_and_click: Find text/visual elements and click (OCR + vision fallback)

Workflows & Memory:
- create_workflow/execute_workflow: Save and replay multi-step sequences
- save_learned_shortcut: Remember new shortcuts user teaches you

CRITICAL TOOL USAGE RULES:
YOU MUST USE TOOLS FOR ALL ACTIONS
- NEVER just describe what should happen - EXECUTE IT with tools
- When user says "open X" → CALL launch_app tool immediately
- When user says "type Y" → CALL type_text tool immediately
- When user says "click Z" → CALL find_and_click first, if returns success=False then CALL click_position with OCR coordinates
- Combine multiple tool calls for complex sequences (including retries!)
- When a tool returns success=False → Try alternative approach, don't give up
- When a tool returns success=True → TRUST IT - the action succeeded
- Only provide voice confirmation after tool execution

OCR & COORDINATES:
- You receive OCR text with positions from screenshot (1280x720)
- Use OCR coordinates with click_position tool - system auto-scales to actual resolution
- Example: OCR shows "Submit" at (850, 600) ? call click_position(x=850, y=600)

VISUAL FEEDBACK AFTER TOOL EXECUTION:
- After you execute tools, you will receive a NEW screenshot showing the result
- Use this screenshot to verify if your actions succeeded
- Check if dialogs opened, text appeared, buttons were clicked, etc.
- If the action didn't work as expected, try alternative approaches
- If the user's request is complete, provide voice confirmation
- If more steps are needed, continue with additional tool calls

CLICKING STRATEGY (CRITICAL - for ANY element):
When user asks to click something:
1. ALWAYS use find_and_click("element name") first
   - This tool now has DUAL capability:
     a) First tries OCR text matching (fast, for text-based elements)
     b) If OCR fails → Automatically uses vision model to locate element visually
   - Works for: text buttons, icon buttons, images, any visible element
   - The tool handles the fallback automatically - you just call it once!

2. Example usage:
   User: "click send button"
   → Call find_and_click("send")
   → Tool tries OCR first, if fails, vision locates it automatically
   → Success!
   
3. For elements not found by name:
   - If find_and_click fails for a named element
   - Look at OCR data and use click_position(x, y) with specific coordinates
   - Or describe the element's position: "click the blue button in bottom right"

4. Vision model can find:
   - Icon buttons (no text)
   - Styled text OCR can't read
   - Images, logos, graphics
   - Any visible clickable element

QUICK PATTERNS:
- Open app: Use launch_app tool
- Type text: Use type_text tool
- Press keys: Use press_key or press_hotkey tools
- Click: Use find_and_click or click_position tools

RESPONSE FORMAT:
Only use <voice> tags for spoken confirmation:
<voice>Brief spoken confirmation of what you did</voice>

REMEMBER:
- User is on phone listening - be BRIEF
- Don't ask for filenames - use sensible defaults
- MUST execute actions using tools, not describe them
- Combine related tool calls for efficiency"""

def get_screenshot_with_ocr() -> Tuple[str, str, float]:
    """
    Capture screenshot and extract text with OCR
    Returns: (screenshot_base64, ocr_text_with_positions, scale_factor)
    """
    screenshot = pyautogui.screenshot()
    original_width, original_height = screenshot.size
    
    target_width = 1280
    target_height = 720
    
    screenshot_resized = screenshot.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    screenshot_cv = cv2.cvtColor(np.array(screenshot_resized), cv2.COLOR_RGB2BGR)
    
    ocr_data = pytesseract.image_to_data(screenshot_cv, output_type=pytesseract.Output.DICT)
    
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
            
            if conf > 30:
                ocr_info.append(f'"{text}" at ({center_x}, {center_y})')
    
    ocr_text = "\n".join(ocr_info) if ocr_info else "No text detected"
    
    buffered = io.BytesIO()
    screenshot_resized.save(buffered, format="PNG", optimize=True, quality=85)
    screenshot_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
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

async def classify_task_complexity(user_message: str, backboard_client, assistant) -> dict:
    """
    Use a fast LLM to analyze task complexity and recommend appropriate model.
    Pure LLM analysis - no keyword matching!
    
    Returns: {
        "complexity": "simple|medium|complex",
        "reasoning": "why this classification",
        "recommended_model": ("provider", "model_name")
    }
    """
    classification_prompt = f"""Analyze the following user request and classify its complexity for a voice-controlled computer assistant.

User Request: "{user_message}"

Evaluate based on:
1. Number of steps required (1 step = simple, 2-3 = medium, 4+ = complex)
2. Reasoning depth needed (basic action vs planning/problem-solving)
3. Tool/API calls required (single action vs coordinated sequence)
4. Error handling complexity (straightforward vs requires judgment)

Classify as:
- "simple": Single straightforward action (open app, click button, type text)
- "medium": 2-3 coordinated actions or simple navigation sequences
- "complex": Multi-step workflows, planning required, or complex reasoning

Respond ONLY with valid JSON in this exact format:
{{"complexity": "simple", "reasoning": "Single action to launch application", "steps": 1}}

JSON response:"""

    try:
        temp_thread = await backboard_client.create_thread(assistant_id=assistant.assistant_id)
        
        response = await backboard_client.add_message(
            thread_id=str(temp_thread.thread_id),
            content=classification_prompt,
            llm_provider="google",
            model_name="gemini-2.5-flash-lite",
            memory="off",
            stream=False
        )
        
        import json
        import re
        
        content = response.content.strip()
        
        json_match = re.search(r'\{[^}]+\}', content)
        if json_match:
            content = json_match.group(0)
        
        classification = json.loads(content)
        
        model_map = {
            "simple": ("google", "gemini-2.5-flash-lite"),
            "medium": ("openai", "gpt-4.1"),
            "complex": ("anthropic", "claude-sonnet-4-20250514")
        }
        
        complexity = classification.get("complexity", "medium")
        classification["recommended_model"] = model_map.get(complexity, ("openai", "gpt-4o"))
        
        return classification
        
    except Exception as e:
        print(f"Classification error: {e}")
        print(f"Response was: {response.content if 'response' in locals() else 'No response'}")
        return {
            "complexity": "simple",
            "reasoning": "Classification failed, defaulting to simple model",
            "recommended_model": ("google", "gemini-2.5-flash-lite")
        }

async def ask_backboard_voice(user_message: str, screenshot_b64: str, ocr_text: str, thread_id: str, scale_factor: float) -> tuple[str, str, str, dict]:
    """
    Ask Backboard AI to execute a voice instruction with OCR data
    Returns: (voice_response, full_response, thread_id, analysis_data)
    """
    global backboard_client, assistant, tool_executor, thread_id_mapping
    
    context_text = f"[Current screenshot attached]\n\nDetected text on screen:\n{ocr_text}\n\nCurrent user request: \"{user_message}\""
    
    frontend_thread_id = thread_id
    backboard_thread_id = None
    
    if not frontend_thread_id:
        thread = await backboard_client.create_thread(assistant_id=assistant.assistant_id)
        backboard_thread_id = str(thread.thread_id)
        frontend_thread_id = backboard_thread_id
        thread_id_mapping[frontend_thread_id] = backboard_thread_id
    else:
        if frontend_thread_id in thread_id_mapping:
            backboard_thread_id = thread_id_mapping[frontend_thread_id]
        else:
            thread = await backboard_client.create_thread(assistant_id=assistant.assistant_id)
            backboard_thread_id = str(thread.thread_id)
            thread_id_mapping[frontend_thread_id] = backboard_thread_id
    
    thread_id = frontend_thread_id
    
    tool_executor.set_ocr_context(ocr_text, scale_factor)
    tool_executor.set_vision_context(screenshot_b64, backboard_thread_id)

    classification = await classify_task_complexity(user_message, backboard_client, assistant)
    llm_provider, model_name = classification["recommended_model"]
    
    print(f"\n{'='*60}")
    print(f"TASK CLASSIFICATION")
    print(f"{'='*60}")
    print(f"Complexity: {classification['complexity'].upper()}")
    print(f"Reasoning: {classification['reasoning']}")
    print(f"Selected Model: {llm_provider}/{model_name}")
    print(f"{'='*60}\n")
    
    response = await backboard_client.add_message(
        thread_id=backboard_thread_id,
        content=context_text,
        llm_provider=llm_provider,
        model_name=model_name,
        memory="Auto",
        stream=False
    )
    
    max_iterations = 10
    iteration = 0
    all_tool_results = []
    full_response = ""
    
    while response.status == 'REQUIRES_ACTION' and response.tool_calls and iteration < max_iterations:
        iteration += 1
        if iteration > 1:
            print(f"\n--- Tool Execution Step {iteration} ---")
        
        tool_outputs = []
        
        for tool_call in response.tool_calls:
            try:
                if isinstance(tool_call, dict):
                    tool_call_id = tool_call['id']
                    function_name = tool_call['function']['name']
                    function_args = tool_call['function'].get('parsed_arguments') or tool_call['function'].get('arguments', {})
                    
                    if isinstance(function_args, str):
                        try:
                            function_args = json.loads(function_args)
                        except json.JSONDecodeError:
                            print(f"Error parsing arguments: {function_args}")
                            function_args = {}
                else:
                    tool_call_id = tool_call.id
                    function_name = tool_call.function.name
                    
                    function_args = getattr(tool_call.function, 'parsed_arguments', None)
                    
                    if function_args is None:
                        arguments_str = getattr(tool_call.function, 'arguments', '{}')
                        try:
                            function_args = json.loads(arguments_str) if isinstance(arguments_str, str) else arguments_str
                        except json.JSONDecodeError:
                            print(f"Error parsing arguments: {arguments_str}")
                            function_args = {}
            except Exception as e:
                print(f"ERROR parsing tool call: {e}")
                print(f"Tool call type: {type(tool_call)}, content: {tool_call}")
                continue
            
            print(f"Executing tool: {function_name} with args: {function_args}")
            
            result = await tool_executor.execute(function_name, function_args)
            print(f"Tool result: {result}")
            
            all_tool_results.append({
                "tool": function_name,
                "args": function_args,
                "result": result
            })
            
            tool_outputs.append({
                "tool_call_id": tool_call_id,
                "output": json.dumps(result)
            })
        
        try:
            response = await backboard_client.submit_tool_outputs(
                thread_id=backboard_thread_id,
                run_id=response.run_id,
                tool_outputs=tool_outputs
            )
            
            if response.status == 'REQUIRES_ACTION':
                pass
            elif response.status != 'REQUIRES_ACTION':
                try:
                    thread = await backboard_client.get_thread(thread_id=backboard_thread_id)
                    if hasattr(thread, 'messages') and thread.messages:
                        for message in reversed(thread.messages):
                            if hasattr(message, 'role') and message.role == 'assistant':
                                if hasattr(message, 'content') and message.content:
                                    full_response = message.content
                                    break
                        else:
                            full_response = ""
                    else:
                        full_response = ""
                except Exception as e:
                    print(f"Warning: Failed to fetch thread messages: {e}")
                    if hasattr(response, 'content') and response.content:
                        full_response = response.content
                    else:
                        full_response = ""
                break
                
        except Exception as e:
            print(f"Warning: submit_tool_outputs failed: {e}")
            print("Generating fallback response from tool results...")
            full_response = ""
            break
    
    if iteration >= max_iterations:
        print(f"WARNING: Reached max tool execution iterations ({max_iterations})")
        full_response = f"<voice>I completed {len(all_tool_results)} actions but had to stop</voice>"
    elif not full_response:
        if hasattr(response, 'content') and response.content:
            full_response = response.content or ""
        elif hasattr(response, 'latest_message') and response.latest_message:
            full_response = response.latest_message.content or ""
        elif hasattr(response, 'message') and response.message:
            full_response = response.message or ""
        else:
            full_response = str(response)
    
    if not full_response or full_response == "None":
        if all_tool_results:
            successful_count = sum(1 for tr in all_tool_results if tr["result"].get("success"))
            if successful_count == len(all_tool_results):
                full_response = f"<voice>Completed {len(all_tool_results)} actions successfully</voice>"
            else:
                full_response = f"<voice>Completed {successful_count} out of {len(all_tool_results)} actions</voice>"
        else:
            full_response = f"<voice>Done</voice>"
    
    if iteration > 0:
        print(f"Final response after {iteration} tool execution step(s): {full_response[:200]}...")
    
    if iteration > 0 and all_tool_results:
        try:
            await asyncio.sleep(0.5)
            final_screenshot_b64, final_ocr_text, _ = get_screenshot_with_ocr()
            
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as temp_file:
                temp_file.write(base64.b64decode(final_screenshot_b64))
                temp_screenshot_path = temp_file.name
            
            executed_tools = [f"{r['tool']}({json.dumps(r['args'])})" for r in all_tool_results]
            verification_message = f"FINAL SCREENSHOT - TASK VERIFICATION:\n\nI completed these actions: {', '.join(executed_tools)}\n\nHere's the final state of the screen:\n\nDetected text on screen:\n{final_ocr_text}\n\nPlease verify if the user's request was completed successfully by looking at this screenshot."
            
            await backboard_client.add_message(
                thread_id=backboard_thread_id,
                content=verification_message,
                files=[temp_screenshot_path],
                llm_provider=llm_provider,
                model_name=model_name,
                memory="off",
                stream=False
            )
            
            try:
                os.unlink(temp_screenshot_path)
            except:
                pass
        except Exception as e:
            print(f"Warning: Failed to send final verification screenshot: {e}")
    
    voice_match = re.search(r'<voice>(.*?)</voice>', full_response, re.DOTALL)
    voice_response = voice_match.group(1).strip() if voice_match else full_response
    voice_response = re.sub(r'<[^>]+>', '', voice_response).strip()
    analysis_data = {
        "model": f"{llm_provider}/{model_name}",
        "complexity": classification['complexity'],
        "tool_calls": all_tool_results
    }
    
    return voice_response, full_response, thread_id, analysis_data
@app.post("/voice", response_model=VoiceResponse)
async def voice_command(request: VoiceRequest):
    """
    Main voice command endpoint with OCR, custom tools, and Backboard integration
    """
    print("\n" + "=" * 60)
    print(f"USER SAID: {request.text}")
    print(f"THREAD ID: {request.thread_id or 'NEW'}")
    print("=" * 60 + "\n")
    
    print("Capturing screenshot and running OCR...")
    screenshot_b64, ocr_text, scale_factor = get_screenshot_with_ocr()
    print(f"OCR detected {len(ocr_text.split(chr(10)))} text elements")
    print(f"Scale factor: {scale_factor:.2f}x (resized -> actual screen)")
    print(f"\nOCR Text Preview (first 500 chars):\n{ocr_text[:500]}\n")
    
    try:
        voice_response, full_response, thread_id, analysis_data = await ask_backboard_voice(
            request.text,
            screenshot_b64,
            ocr_text,
            request.thread_id,
            scale_factor
        )
        
        print(f"ASSISTANT SAYS: \"{voice_response}\"")
        
        print("Generating speech response...")
        audio_base64 = text_to_speech(voice_response)
        
        time.sleep(0.8)
        time.sleep(0.5)
        
        new_screenshot_b64, _, _ = get_screenshot_with_ocr()
        
        print(f"Request completed. Thread: {thread_id}\n")
        
        return VoiceResponse(
            assistant_message=voice_response,
            assistant_audio_base64=audio_base64,
            screenshot_base64=new_screenshot_b64,
            thread_id=str(thread_id),
            success=True,
            analysis=AnalysisData(**analysis_data)
        )
        
    except Exception as e:
        error_msg = "Sorry, something went wrong on my end"
        error_str = str(e)
        if "502" in error_str or "Bad Gateway" in error_str:
            print(f"ERROR: Backboard API temporarily unavailable (502 Bad Gateway)\n")
        else:
            print(f"ERROR: {error_str[:200]}\n")
        
        if os.getenv("DEBUG"):
            import traceback
            traceback.print_exc()
        
        return VoiceResponse(
            assistant_message=error_msg,
            assistant_audio_base64=text_to_speech(error_msg),
            screenshot_base64=screenshot_b64,
            thread_id=str(request.thread_id) if request.thread_id else "",
            success=False
        )

# ============= STARTUP MESSAGE =============
@app.on_event("startup")
async def startup_event():
    """Initialize Backboard and display startup information"""
    global backboard_client, assistant, tool_executor
    
    print("\n" + "=" * 60)
    print("REMOTO AI BACKEND STARTING...")
    print("=" * 60)
    
    backboard_api_key = os.getenv("BACKBOARD_API_KEY")
    if not backboard_api_key:
        print("WARNING: BACKBOARD_API_KEY not set in environment!")
        print("Please set BACKBOARD_API_KEY in your .env file")
    else:
        try:
            backboard_client = BackboardClient(api_key=backboard_api_key)
            print("[OK] Backboard client initialized")
            
            assistant = await backboard_client.create_assistant(
                name="Remoto AI",
                description=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS
            )
            print(f"[OK] Assistant created: {assistant.assistant_id}")
            
            tool_executor.set_backboard_client(backboard_client, assistant.assistant_id)
            
            shortcuts_path = "server/shortcuts.json"
            if os.path.exists(shortcuts_path):
                try:
                    document = await backboard_client.upload_document_to_assistant(
                        assistant_id=assistant.assistant_id,
                        file_path=shortcuts_path
                    )
                    print(f"[OK] Shortcuts database uploaded to RAG: {getattr(document, 'id', 'uploaded')}")
                except Exception as e:
                    print(f"[WARNING] Could not upload shortcuts to RAG: {e}")
            
            await tool_executor.load_workflows_from_memory()
            print(f"[OK] Tool executor initialized with memory")
            
        except Exception as e:
            print(f"[ERROR] Backboard initialization failed: {e}")
            print("The app will not work without Backboard integration")
    
    print("=" * 60)
    print("REMOTO AI BACKEND READY")
    print("=" * 60)
    print(f"Session Password: {SESSION_PASSWORD}")
    print(f"API URL: http://localhost:8000")
    print(f"Stream URL: {os.getenv('STREAM_URL', 'Not set yet')}")
    print("=" * 60 + "\n")

if __name__ == "__main__":    
    uvicorn.run(app, host="0.0.0.0", port=8000)
