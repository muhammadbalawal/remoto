# Quick Start with Test Mode

## Test the application without Anthropic API key

The easiest way to get started testing is to use Test Mode, which provides mock AI responses.

### Step 1: Verify Test Mode is Enabled

```bash
cat server/.env | grep TEST_MODE
```

Should show: `TEST_MODE=true`

### Step 2: Start the Application

```bash
remoto start
```

The terminal will show:

```
============================================================
⚠️  TEST MODE ENABLED - Using mock Claude responses
Set TEST_MODE=false and provide ANTHROPIC_API_KEY to use real API
============================================================
```

### Step 3: Access the Web Interface

Open your browser and navigate to: `http://localhost:8000`

### Step 4: Test Voice Commands

Try these voice commands in the web interface:

- "Click the button"
- "Type something"
- "Scroll down"
- "Hello"

You'll get instant mock responses without any API calls or costs!

## Switching to Real Claude AI

When you have an Anthropic API key:

1. Update `.env`:

```bash
TEST_MODE=false
ANTHROPIC_API_KEY=your-api-key-here
```

2. Restart:

```bash
remoto start
```

See [TEST_MODE.md](TEST_MODE.md) for more details.
