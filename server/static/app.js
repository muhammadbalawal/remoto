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

function showCommandNotification(text) {
    commandText.textContent = text;
    commandNotification.classList.add("show");
}

function hideCommandNotification() {
    commandNotification.classList.remove("show");
}

async function sendCommand(text) {
    showCommandNotification(text);
    
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
                history: conversationHistory,  // Kept for backward compatibility
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

