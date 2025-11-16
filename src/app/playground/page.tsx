"use client";

import { useState, useEffect } from "react";
import SpeechRecognition, {
  useSpeechRecognition,
} from "react-speech-recognition";
import { sendPrompt } from "../actions/sendPrompt";
import ScreenStream from "@/components/ScreenStream";

export default function PromptInput() {
  const [inputValue, setInputValue] = useState("");

  // Speech recognition hook
  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition,
  } = useSpeechRecognition();

  // Update input field with speech transcript
  useEffect(() => {
    if (transcript) {
      setInputValue(transcript);
    }
  }, [transcript]);

  const handleSubmit = async () => {
    if (!inputValue.trim()) return;
    console.log("Submitted:", inputValue);
    try {
      console.log("Sending to FastAPI:", inputValue);
      await sendPrompt(inputValue);
      setInputValue(""); // clear input
      resetTranscript(); // clear speech transcript
    } catch (err) {
      console.error("Error sending prompt:", err);
    }
  };

  // Toggle microphone listening
  const toggleListening = () => {
    if (listening) {
      SpeechRecognition.stopListening();
    } else {
      resetTranscript();
      setInputValue("");
      SpeechRecognition.startListening({
        continuous: true,
        language: "en-US",
      });
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      <div className="w-full max-w-5xl space-y-6">

        <ScreenStream />
        {/* Input Field with Microphone and Send buttons */}
        <div className="relative">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Send message or command..."
            className="w-full rounded-full border-2 border-border bg-background px-6 py-4 pr-28 text-lg outline-none transition-all focus:border-primary focus:ring-2 focus:ring-primary/20"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSubmit();
              }
            }}
          />

          {/* Microphone Button */}
          {browserSupportsSpeechRecognition && (
            <button
              onClick={toggleListening}
              className={`absolute right-16 top-1/2 -translate-y-1/2 rounded-full p-3 transition-all ${
                listening
                  ? "bg-red-500 text-white hover:bg-red-600 animate-pulse"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
              aria-label={listening ? "Stop recording" : "Start recording"}
              title={listening ? "Stop recording" : "Start recording"}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="h-5 w-5"
              >
                <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                <path d="M19 10v1a7 7 0 0 1-14 0v-1a1 1 0 0 0-2 0v1a9 9 0 0 0 8 8.94V21H8a1 1 0 1 0 0 2h8a1 1 0 1 0 0-2h-3v-1.06A9 9 0 0 0 21 11v-1a1 1 0 1 0-2 0Z" />
              </svg>
            </button>
          )}

          {/* Send Button */}
          <button
            onClick={handleSubmit}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-primary p-3 text-primary-foreground transition-all hover:bg-primary/90"
            aria-label="Send"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="h-5 w-5"
            >
              <path d="M5 12h14" />
              <path d="m12 5 7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* Browser support warning */}
        {!browserSupportsSpeechRecognition && (
          <div className="text-center text-sm text-muted-foreground">
            Speech recognition is not supported in your browser. Please use
            Chrome for the best experience.
          </div>
        )}
      </div>
    </div>
  );
}