let isListening = false;
let conversationHistory = [];
let sessionPassword = null;
let currentTranscript = '';
let threadId = localStorage.getItem('remoto_thread_id') || null;

const voiceBtn = document.getElementById("voiceBtn");
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

function getAuthHeaders() {
    if (!sessionPassword) {
        return {};
    }
    const credentials = btoa(`user:${sessionPassword}`);
    return {
        'Authorization': `Basic ${credentials}`
    };
}

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

function initializeVoice() {
    if (!annyang) {
        showError("Voice recognition library failed to load. Please refresh the page.");
        voiceBtn.disabled = true;
        return;
    }

    annyang.addCallback('result', (phrases) => {
        if (phrases && phrases.length > 0) {
            currentTranscript = phrases[0];
            textInput.value = currentTranscript;
        }
    });

    annyang.addCallback('error', (error) => {
        console.error("Speech error:", error);
    });

    annyang.addCallback('start', () => {
        console.log("Speech started");
    });

    annyang.addCallback('end', () => {
        console.log("Speech ended");
        if (isListening) {
            setTimeout(() => {
                if (isListening) {
                    annyang.start({ autoRestart: false, continuous: false });
                }
            }, 100);
        }
    });

    annyang.setLanguage('en-US');
    console.log("Annyang initialized");
}

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

function clearToolCalls() {
    toolCalls.innerHTML = '';
}

function clearAnalysisPanel() {
    modelInfo.innerHTML = '';
    complexityInfo.innerHTML = '';
    toolCalls.innerHTML = '';
}

function showCommandNotification(text) {
    commandText.textContent = text;
    commandNotification.classList.add("show");
}

function hideCommandNotification() {
    commandNotification.classList.remove("show");
}

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

        const response = await fetch("/voice", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                text: text,
                thread_id: threadId,
                history: conversationHistory,
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

        if (result.assistant_audio_base64) {
            const audio = new Audio("data:audio/mp3;base64," + result.assistant_audio_base64);
            audio.play().catch(err => console.error("Audio error:", err));
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

async function sendTextCommand() {
    const text = textInput.value.trim();
    if (!text) {
        showError("Please enter a command");
        return;
    }

    textInput.value = "";
    await sendCommand(text);
}

function showError(message) {
    errorDiv.textContent = message;
    errorDiv.classList.add("show");
    setTimeout(() => {
        errorDiv.classList.remove("show");
    }, 5000);
}

voiceBtn.addEventListener("click", () => {
    if (!annyang) {
        showError("Voice recognition not available");
        return;
    }

    if (isListening) {
        isListening = false;
        annyang.abort();
        voiceBtn.classList.remove("listening");
        console.log("Stopped listening");
    } else {
        isListening = true;
        currentTranscript = '';
        voiceBtn.classList.add("listening");
        annyang.start({ autoRestart: false, continuous: false });
        console.log("Started listening");
    }
});

sendBtn.addEventListener("click", sendTextCommand);

textInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        sendTextCommand();
    }
});

window.addEventListener("load", async () => {
    await initializeAuth();
    initializeStream();
    initializeVoice();
});
