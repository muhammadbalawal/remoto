# Test Mode - Testing Without Anthropic API Key

## Overview

Test Mode allows you to test the entire Remoto application without needing an Anthropic API key. This is useful for:

- Testing the UI and functionality
- Development and debugging
- Demos without API costs
- Understanding how the system works

## How to Enable Test Mode

### Option 1: Environment Variable

Set `TEST_MODE=true` in your `.env` file:

```bash
# server/.env
TEST_MODE=true
STREAM_URL=http://localhost:8888/screen
REMOTE_AI_PASSWORD=your-password
```

### Option 2: Command Line

```bash
TEST_MODE=true remoto start
```

## What Test Mode Does

When `TEST_MODE=true`:

- ✅ The backend starts normally
- ✅ The API runs without requiring an Anthropic API key
- ✅ Mock responses are generated based on keywords in your voice commands
- ✅ You can test the full UI and interaction flow
- ✅ No API costs

## Mock Response Behavior

The mock responses recognize these commands:

### Click/Button Commands

User says: "Click the button" or "Press that"

- Mock response: "I'll click on that for you now."
- Executes: `pyautogui.click(500, 300)`

### Type/Text Commands

User says: "Type your password" or "Enter the text"

- Mock response: "Let me type that for you."
- Executes: `pyautogui.typewrite('test input')`

### Scroll Commands

User says: "Scroll down" or "Scroll up"

- Mock response: "I'll scroll for you."
- Executes: `pyautogui.scroll(-3)`

### Greeting Commands

User says: "Hello" or "How are you?"

- Mock response: Provides helpful information about test mode
- Executes: Nothing (no code)

### Other Commands

Any other input gets a response acknowledging the request and noting that test mode is enabled.

## Switching to Real API

When you have an Anthropic API key and want to use the real Claude AI:

1. Update `.env`:

```bash
TEST_MODE=false
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

2. Restart the server:

```bash
remoto start
```

The system will now use real Claude responses with full capabilities.

## Development Tips

- Mock mode uses simple pattern matching - it's not AI
- For testing UI responsiveness, this is perfect
- For testing the code execution pipeline, mock mode works great
- For testing actual AI intelligence, you'll need the real API key

## Current Configuration

Your current `.env` has:

- `TEST_MODE=true` (enabled)
- `STREAM_URL=http://localhost:8888/screen`

You can now run `remoto start` and test the full system!
