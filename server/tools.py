"""
Custom Tools for Remoto AI - Backboard Integration
Defines and executes custom tools for computer control
"""

import pyautogui
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Tool definitions for Backboard
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "launch_app",
            "description": "Open a Windows application using Start menu search",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Application name (e.g., 'chrome', 'vscode', 'notepad')"
                    }
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "navigate_url",
            "description": "Open browser and navigate to a URL",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Website URL to visit"
                    },
                    "new_tab": {
                        "type": "boolean",
                        "description": "Whether to open in new tab (default: false)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_and_click",
            "description": "Find UI element by text using OCR data and click it",
            "parameters": {
                "type": "object",
                "properties": {
                    "element_text": {
                        "type": "string",
                        "description": "Text on button/link to find and click"
                    },
                    "click_type": {
                        "type": "string",
                        "description": "Type of click: 'single', 'double', or 'right' (default: 'single')",
                        "enum": ["single", "double", "right"]
                    }
                },
                "required": ["element_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_workflow",
            "description": "Create and save a new multi-step workflow for future use",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_name": {
                        "type": "string",
                        "description": "Name for this workflow (e.g., 'work_mode', 'study_mode')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what this workflow does"
                    },
                    "steps": {
                        "type": "array",
                        "description": "List of steps to execute",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tool": {
                                    "type": "string",
                                    "description": "Tool name to execute"
                                },
                                "args": {
                                    "type": "object",
                                    "description": "Arguments for the tool"
                                }
                            }
                        }
                    }
                },
                "required": ["workflow_name", "steps"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_workflow",
            "description": "Execute a saved multi-step workflow by name",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_name": {
                        "type": "string",
                        "description": "Name of the workflow to execute (e.g., 'work_mode', 'gaming_mode')"
                    }
                },
                "required": ["workflow_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_workflows",
            "description": "List all available saved workflows",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_learned_shortcut",
            "description": "Save a newly discovered keyboard shortcut to memory for future use",
            "parameters": {
                "type": "object",
                "properties": {
                    "app": {
                        "type": "string",
                        "description": "Application name"
                    },
                    "action": {
                        "type": "string",
                        "description": "Action description"
                    },
                    "shortcut": {
                        "type": "string",
                        "description": "Keyboard shortcut (e.g., 'Ctrl+N', 'Alt+F4')"
                    }
                },
                "required": ["app", "action", "shortcut"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text on the keyboard",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to type"
                    },
                    "interval": {
                        "type": "number",
                        "description": "Seconds between each keystroke (default: 0.05)"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a single key (enter, tab, esc, backspace, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key name (e.g., 'enter', 'tab', 'esc', 'space', 'backspace')"
                    }
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_hotkey",
            "description": "Press a keyboard shortcut (key combination)",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keys to press together (e.g., ['ctrl', 'c'] for copy, ['alt', 'tab'] for switch apps)"
                    }
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_position",
            "description": "Click at specific screen coordinates",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {
                        "type": "number",
                        "description": "X coordinate from OCR data"
                    },
                    "y": {
                        "type": "number",
                        "description": "Y coordinate from OCR data"
                    },
                    "clicks": {
                        "type": "number",
                        "description": "Number of clicks (1 for single, 2 for double, default: 1)"
                    },
                    "button": {
                        "type": "string",
                        "description": "Mouse button ('left' or 'right', default: 'left')"
                    }
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scroll_page",
            "description": "Scroll up or down on the page",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Scroll amount (positive for up, negative for down, e.g., 3 for up, -5 for down)"
                    }
                },
                "required": ["amount"]
            }
        }
    }
]


class ToolExecutor:
    """Executes custom tools for Remoto AI"""
    
    def __init__(self):
        self.workflows = {}  # Will be populated from memory
        self.ocr_data = None  # Set by main.py before tool execution
        self.scale_factor = 1.0  # Set by main.py for coordinate scaling
        self.backboard_client = None  # Set by main.py
        self.assistant_id = None  # Set by main.py
    
    def set_ocr_context(self, ocr_data: str, scale_factor: float):
        """Set current OCR data and scale factor for find_and_click"""
        self.ocr_data = ocr_data
        self.scale_factor = scale_factor
    
    def set_backboard_client(self, client, assistant_id: str):
        """Set Backboard client for memory operations"""
        self.backboard_client = client
        self.assistant_id = assistant_id
    
    async def load_workflows_from_memory(self):
        """Load workflows from Backboard memory"""
        if not self.backboard_client or not self.assistant_id:
            return
        
        try:
            # Get all memories for this assistant
            memories_response = await self.backboard_client.get_memories(assistant_id=self.assistant_id)
            memories = getattr(memories_response, 'memories', [])
            
            for memory in memories:
                metadata = getattr(memory, 'metadata', {})
                if metadata.get('type') == 'workflow':
                    content = getattr(memory, 'content', '{}')
                    workflow_data = json.loads(content)
                    workflow_name = workflow_data.get('workflow_name')
                    if workflow_name:
                        self.workflows[workflow_name] = workflow_data
            
            print(f"Loaded {len(self.workflows)} workflows from memory")
        except Exception as e:
            print(f"Warning: Could not load workflows from memory: {e}")
    
    async def save_workflow_to_memory(self, workflow_name: str, workflow_data: Dict):
        """Save workflow to Backboard memory"""
        if not self.backboard_client or not self.assistant_id:
            # Fallback to in-memory only
            self.workflows[workflow_name] = workflow_data
            return True
        
        try:
            await self.backboard_client.add_memory(
                assistant_id=self.assistant_id,
                content=json.dumps(workflow_data),
                metadata={"type": "workflow", "name": workflow_name}
            )
            self.workflows[workflow_name] = workflow_data
            print(f"Workflow '{workflow_name}' saved to Backboard memory")
            return True
        except Exception as e:
            print(f"Error saving workflow to memory: {e}")
            # Fallback to in-memory
            self.workflows[workflow_name] = workflow_data
            return True
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name with given arguments"""
        try:
            if tool_name == "launch_app":
                return self.launch_app(**arguments)
            elif tool_name == "navigate_url":
                return self.navigate_url(**arguments)
            elif tool_name == "find_and_click":
                return self.find_and_click(**arguments)
            elif tool_name == "create_workflow":
                return await self.create_workflow(**arguments)
            elif tool_name == "execute_workflow":
                return await self.execute_workflow_async(**arguments)
            elif tool_name == "list_workflows":
                return self.list_workflows()
            elif tool_name == "save_learned_shortcut":
                return await self.save_learned_shortcut(**arguments)
            elif tool_name == "type_text":
                return self.type_text(**arguments)
            elif tool_name == "press_key":
                return self.press_key(**arguments)
            elif tool_name == "press_hotkey":
                return self.press_hotkey(**arguments)
            elif tool_name == "click_position":
                return self.click_position(**arguments)
            elif tool_name == "scroll_page":
                return self.scroll_page(**arguments)
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def launch_app(self, app_name: str) -> Dict[str, Any]:
        """Launch Windows application via Start menu"""
        try:
            pyautogui.press('win')
            time.sleep(0.5)
            pyautogui.write(app_name, interval=0.05)
            time.sleep(0.3)
            pyautogui.press('enter')
            time.sleep(2)
            
            return {
                "success": True,
                "app_name": app_name,
                "message": f"Launched {app_name}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def navigate_url(self, url: str, new_tab: bool = False) -> Dict[str, Any]:
        """Navigate to URL in browser"""
        try:
            # Add https:// if not present
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Open new tab if requested
            if new_tab:
                pyautogui.hotkey('ctrl', 't')
                time.sleep(0.3)
            
            # Focus address bar
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.3)
            
            # Type URL
            pyautogui.write(url, interval=0.05)
            pyautogui.press('enter')
            time.sleep(1.5)
            
            return {
                "success": True,
                "url": url,
                "message": f"Navigated to {url}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def find_and_click(self, element_text: str, click_type: str = "single") -> Dict[str, Any]:
        """Find UI element by text and click it"""
        try:
            if not self.ocr_data:
                return {"success": False, "error": "No OCR data available"}
            
            # Parse OCR data to find element
            # Format: "text" at (x, y)
            lines = self.ocr_data.split('\n')
            for line in lines:
                if element_text.lower() in line.lower():
                    # Extract coordinates
                    import re
                    match = re.search(r'\((\d+),\s*(\d+)\)', line)
                    if match:
                        x = int(match.group(1))
                        y = int(match.group(2))
                        
                        # Scale coordinates to actual screen resolution
                        scaled_x = int(x * self.scale_factor)
                        scaled_y = int(y * self.scale_factor)
                        
                        # Move and click
                        pyautogui.moveTo(scaled_x, scaled_y, duration=0.3)
                        
                        if click_type == "double":
                            pyautogui.click(clicks=2)
                        elif click_type == "right":
                            pyautogui.rightClick()
                        else:
                            pyautogui.click()
                        
                        time.sleep(0.5)
                        
                        return {
                            "success": True,
                            "element": element_text,
                            "coordinates": (scaled_x, scaled_y),
                            "message": f"Clicked '{element_text}' at ({scaled_x}, {scaled_y})"
                        }
            
            return {
                "success": False,
                "error": f"Could not find '{element_text}' on screen"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_workflow_async(self, workflow_name: str) -> Dict[str, Any]:
        """Execute a saved workflow (async version)"""
        try:
            if workflow_name not in self.workflows:
                return {
                    "success": False,
                    "error": f"Workflow '{workflow_name}' not found. Available workflows: {list(self.workflows.keys())}"
                }
            
            workflow = self.workflows[workflow_name]
            results = []
            
            for step in workflow.get('steps', []):
                tool_name = step.get('tool')
                args = step.get('args', {})
                
                # Execute the step
                result = await self.execute(tool_name, args)
                results.append(result)
                
                # Stop if any step fails
                if not result.get('success'):
                    return {
                        "success": False,
                        "workflow": workflow_name,
                        "error": f"Step failed: {result.get('error')}",
                        "completed_steps": len(results) - 1
                    }
                
                # Brief pause between steps
                time.sleep(0.5)
            
            return {
                "success": True,
                "workflow": workflow_name,
                "steps_completed": len(results),
                "message": f"Executed workflow '{workflow_name}' with {len(results)} steps"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_workflows(self) -> Dict[str, Any]:
        """List all available workflows"""
        try:
            workflows_info = []
            for name, workflow in self.workflows.items():
                workflows_info.append({
                    "name": name,
                    "description": workflow.get('description', ''),
                    "steps_count": len(workflow.get('steps', []))
                })
            
            return {
                "success": True,
                "workflows": workflows_info,
                "count": len(workflows_info),
                "message": f"Found {len(workflows_info)} workflows"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_workflow(self, workflow_name: str, steps: list, description: str = "") -> Dict[str, Any]:
        """Create and save a new workflow"""
        try:
            workflow_data = {
                "workflow_name": workflow_name,
                "description": description,
                "steps": steps,
                "created_at": time.time()
            }
            
            # Save to Backboard memory
            success = await self.save_workflow_to_memory(workflow_name, workflow_data)
            
            if success:
                return {
                    "success": True,
                    "workflow_name": workflow_name,
                    "steps_count": len(steps),
                    "message": f"Workflow '{workflow_name}' created with {len(steps)} steps"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to save workflow to memory"
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def save_learned_shortcut(self, app: str, action: str, shortcut: str) -> Dict[str, Any]:
        """Save a newly learned shortcut to Backboard memory"""
        if not self.backboard_client or not self.assistant_id:
            return {"success": False, "error": "Backboard client not initialized"}
        
        try:
            shortcut_data = {
                "app": app,
                "action": action,
                "shortcut": shortcut,
                "learned_at": time.time()
            }
            
            await self.backboard_client.add_memory(
                assistant_id=self.assistant_id,
                content=json.dumps(shortcut_data),
                metadata={"type": "learned_shortcut", "app": app, "action": action}
            )
            
            print(f"Shortcut learned and saved: {app} {action} = {shortcut}")
            return {
                "success": True,
                "message": f"Learned and saved: {app} {action} = {shortcut}"
            }
        except Exception as e:
            print(f"Error saving learned shortcut: {e}")
            return {"success": False, "error": str(e)}
    
    def type_text(self, text: str, interval: float = 0.05) -> Dict[str, Any]:
        """Type text on the keyboard"""
        try:
            pyautogui.write(text, interval=interval)
            return {
                "success": True,
                "text": text,
                "message": f"Typed: {text[:50]}{'...' if len(text) > 50 else ''}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def press_key(self, key: str) -> Dict[str, Any]:
        """Press a single key"""
        try:
            pyautogui.press(key)
            return {
                "success": True,
                "key": key,
                "message": f"Pressed key: {key}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def press_hotkey(self, keys: list) -> Dict[str, Any]:
        """Press a keyboard shortcut (key combination)"""
        try:
            pyautogui.hotkey(*keys)
            keys_str = '+'.join(keys)
            return {
                "success": True,
                "keys": keys,
                "message": f"Pressed: {keys_str}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def click_position(self, x: int, y: int, clicks: int = 1, button: str = 'left') -> Dict[str, Any]:
        """Click at specific screen coordinates"""
        try:
            # Scale coordinates using the scale factor
            scaled_x = int(x * self.scale_factor)
            scaled_y = int(y * self.scale_factor)
            
            if button == 'right':
                pyautogui.rightClick(scaled_x, scaled_y)
                action = "Right-clicked"
            elif clicks == 2:
                pyautogui.click(scaled_x, scaled_y, clicks=2)
                action = "Double-clicked"
            else:
                pyautogui.click(scaled_x, scaled_y)
                action = "Clicked"
            
            return {
                "success": True,
                "x": scaled_x,
                "y": scaled_y,
                "message": f"{action} at ({scaled_x}, {scaled_y})"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def scroll_page(self, amount: int) -> Dict[str, Any]:
        """Scroll up or down"""
        try:
            pyautogui.scroll(amount)
            direction = "up" if amount > 0 else "down"
            return {
                "success": True,
                "amount": amount,
                "message": f"Scrolled {direction} by {abs(amount)}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
