/**
 * Remoto AI -- Frontend Application
 *
 * Handles text commands, authentication, live video stream configuration,
 * chat history rendering, and the analysis panel (model info, complexity,
 * tool calls).
 */

/** @type {Array<{role: string, content: string}>} Rolling conversation history (max 10) */
let conversationHistory = [];

/** @type {string|null} Session password used for HTTP Basic Auth */
let sessionPassword = null;

/** @type {string|null} Backboard thread ID for persistent conversation memory */
let threadId = localStorage.getItem('remoto_thread_id') || null;

const textInput = document.getElementById("textInput");
const sendBtn = document.getElementById("sendBtn");
const errorDiv = document.getElementById("error");
const streamElement = document.getElementById("stream");
const commandNotification = document.getElementById("commandNotification");
const commandText = document.getElementById("commandText");

// Analysis panel elements
const modelInfo = document.getElementById("modelInfo");
const complexityInfo = document.getElementById("complexityInfo");
const toolCalls = document.getElementById("toolCalls");

// Chat history element
const chatHistory = document.getElementById("chatHistory");

/**
 * Build HTTP Basic Auth headers using the session password.
 * @returns {Object} Headers object with Authorization header, or empty if no password.
 */
function getAuthHeaders() {
    if (!sessionPassword) {
        return {};
    }
    const credentials = btoa(`user:${sessionPassword}`);
    return {
        'Authorization': `Basic ${credentials}`
    };
}

/**
 * Fetch the session password from the /config endpoint.
 * Called on page load and before sending commands if no password is cached.
 * @returns {Promise<boolean>} True if authentication was successful.
 */
async function initializeAuth() {
    try {
        const response = await fetch("/config", {
            credentials: 'include'
        });
        
        if (response.ok) {
            const config = await response.json();
            if (config.password) {
                sessionPassword = config.password;
                return true;
            }
        }
        return false;
    } catch (error) {
        console.error("Auth error:", error);
        return false;
    }
}

/**
 * Configure the video stream iframe with the HLS URL from the backend.
 * Fetches the stream URL from /config and sets it as the iframe src.
 */
async function initializeStream() {
    try {
        if (!sessionPassword) {
            await initializeAuth();
        }

        const response = await fetch("/config", {
            headers: getAuthHeaders()
        });
        
        if (response.ok) {
            const config = await response.json();
            if (config.password) {
                sessionPassword = config.password;
            }
            if (config.streamUrl) {
                let streamUrl = config.streamUrl;
                if (!streamUrl.endsWith('/screen')) {
                    streamUrl = streamUrl.endsWith('/') 
                        ? streamUrl + 'screen' 
                        : streamUrl + '/screen';
                }
                streamElement.src = streamUrl;
            }
        }
    } catch (error) {
        console.error("Stream config error:", error);
    }
}

/**
 * Append a message bubble to the chat history panel.
 * @param {string} role - Either 'user' or 'assistant'.
 * @param {string} content - The message text to display.
 */
function addChatMessage(role, content) {
    // Remove empty state if present
    const emptyState = chatHistory.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = content;
    
    const timestamp = document.createElement('div');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.appendChild(bubble);
    messageDiv.appendChild(timestamp);
    chatHistory.appendChild(messageDiv);
    
    // Scroll to bottom
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

/**
 * Update the analysis panel with the selected model and task complexity.
 * @param {string|null} model - Model identifier (e.g. "openai/gpt-4.1").
 * @param {string|null} complexity - Task complexity ("simple", "medium", or "complex").
 */
function updateModelInfo(model, complexity) {
    modelInfo.innerHTML = `<span class="info-badge">${model || 'N/A'}</span>`;
    
    let complexityClass = '';
    if (complexity) {
        const c = complexity.toLowerCase();
        if (c === 'simple') complexityClass = 'success';
        else if (c === 'medium') complexityClass = 'warning';
        else if (c === 'complex') complexityClass = 'error';
    }
    
    complexityInfo.innerHTML = `<span class="info-badge ${complexityClass}">${complexity || '-'}</span>`;
}

/**
 * Add a tool call entry to the analysis panel's tool calls list.
 * Keeps only the 10 most recent entries and auto-scrolls to the bottom.
 * @param {string} toolName - Name of the executed tool.
 * @param {Object} args - Arguments passed to the tool.
 * @param {{success: boolean, message?: string, error?: string}|null} result - Execution result.
 */
function addToolCall(toolName, args, result) {
    // Remove empty state if present
    const emptyState = toolCalls.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }

    const toolItem = document.createElement('div');
    toolItem.className = 'tool-call-item';
    
    const toolNameDiv = document.createElement('div');
    toolNameDiv.className = 'tool-call-name';
    toolNameDiv.textContent = toolName;
    
    const toolArgsDiv = document.createElement('div');
    toolArgsDiv.className = 'tool-call-args';
    toolArgsDiv.textContent = JSON.stringify(args, null, 2);
    
    toolItem.appendChild(toolNameDiv);
    toolItem.appendChild(toolArgsDiv);
    
    if (result) {
        const resultDiv = document.createElement('div');
        resultDiv.className = `tool-call-result ${result.success ? 'success' : 'error'}`;
        resultDiv.textContent = result.success ? (result.message || 'Success') : (result.error || 'Failed');
        toolItem.appendChild(resultDiv);
    }
    
    toolCalls.appendChild(toolItem);
    
    // Keep only last 10 tool calls
    const toolItems = toolCalls.querySelectorAll('.tool-call-item');
    if (toolItems.length > 10) {
        toolItems[0].remove();
    }
    
    // Scroll to bottom
    toolCalls.scrollTop = toolCalls.scrollHeight;
}

/** Remove all tool call entries from the analysis panel. */
function clearToolCalls() {
    toolCalls.innerHTML = '';
}

/** Reset the entire analysis panel (model info, complexity, and tool calls). */
function clearAnalysisPanel() {
    modelInfo.innerHTML = '';
    complexityInfo.innerHTML = '';
    toolCalls.innerHTML = '';
}

/**
 * Show the "Processing" notification banner at the top of the screen.
 * @param {string} text - The command text being processed.
 */
function showCommandNotification(text) {
    commandText.textContent = text;
    commandNotification.classList.add("show");
}

/** Hide the processing notification banner. */
function hideCommandNotification() {
    commandNotification.classList.remove("show");
}

/**
 * Send a voice/text command to the backend /voice endpoint.
 * Updates the chat history, analysis panel, and plays the audio response.
 * @param {string} text - The command text to send.
 */
async function sendCommand(text) {
    showCommandNotification(text);
    
    // Add user message to chat
    addChatMessage('user', text);
    
    // Clear analysis panel for new command
    clearAnalysisPanel();
    
    try {
        if (!sessionPassword) {
            await initializeAuth();
        }

        const response = await fetch("/command", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                text: text,
                thread_id: threadId,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        // Store thread ID for persistent memory
        if (result.thread_id) {
            threadId = result.thread_id;
            localStorage.setItem('remoto_thread_id', threadId);
            console.log("Thread ID:", threadId);
        }
        
        conversationHistory.push({
            role: "user",
            content: text,
        });
        conversationHistory.push({
            role: "assistant",
            content: result.assistant_message,
        });

        if (conversationHistory.length > 10) {
            conversationHistory = conversationHistory.slice(-10);
        }

        // Add assistant message to chat
        addChatMessage('assistant', result.assistant_message);
        
        // Update analysis panel from response
        if (result.analysis) {
            updateModelInfo(result.analysis.model, result.analysis.complexity);
            
            if (result.analysis.tool_calls) {
                result.analysis.tool_calls.forEach(tc => {
                    addToolCall(tc.tool, tc.args, tc.result);
                });
            }
        }

        // Hide notification after command completes
        setTimeout(() => {
            hideCommandNotification();
        }, 300);
    } catch (error) {
        console.error("Command error:", error);
        showError("Failed to send command. Please try again.");
        hideCommandNotification();
        
        // Reset analysis panel
        clearAnalysisPanel();
    }
}

/**
 * Read the text input field, clear it, and send the command.
 * Shows an error if the input is empty.
 */
async function sendTextCommand() {
    const text = textInput.value.trim();
    if (!text) {
        showError("Please enter a command");
        return;
    }

    textInput.value = "";
    await sendCommand(text);
}

/**
 * Display an error message that auto-dismisses after 5 seconds.
 * @param {string} message - Error text to show.
 */
function showError(message) {
    errorDiv.textContent = message;
    errorDiv.classList.add("show");
    setTimeout(() => {
        errorDiv.classList.remove("show");
    }, 5000);
}

sendBtn.addEventListener("click", sendTextCommand);

textInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        sendTextCommand();
    }
});

window.addEventListener("load", async () => {
    await initializeAuth();
    initializeStream();
});
