"use client";

import { useState, useEffect, useRef } from "react";
import SpeechRecognition, {
  useSpeechRecognition,
} from "react-speech-recognition";
import { sendPrompt } from "../../actions/sendPrompt";
import ScreenStream from "@/components/ScreenStream";

export default function PromptInput() {
  const [inputValue, setInputValue] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const autoSubmitTimerRef = useRef<NodeJS.Timeout | null>(null);
  const previousTranscriptRef = useRef("");

  const SILENCE_DELAY = 2000;

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition,
  } = useSpeechRecognition();

  useEffect(() => {
    if (transcript) {
      setInputValue(transcript);
    }
  }, [transcript]);

  useEffect(() => {
    if (listening && transcript) {
      if (autoSubmitTimerRef.current) {
        clearTimeout(autoSubmitTimerRef.current);
      }

      if (transcript !== previousTranscriptRef.current) {
        previousTranscriptRef.current = transcript;

        autoSubmitTimerRef.current = setTimeout(() => {
          SpeechRecognition.stopListening();
          setTimeout(() => {
            handleSubmit();
          }, 100);
        }, SILENCE_DELAY);
      }
    } else if (!listening) {
      if (autoSubmitTimerRef.current) {
        clearTimeout(autoSubmitTimerRef.current);
        autoSubmitTimerRef.current = null;
      }
      previousTranscriptRef.current = "";
    }

    return () => {
      if (autoSubmitTimerRef.current) {
        clearTimeout(autoSubmitTimerRef.current);
      }
    };
  }, [listening, transcript]);

  const playAudio = (base64Audio: string) => {
    try {
      const byteCharacters = atob(base64Audio);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: "audio/mpeg" });

      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      audio.play();

      audio.onended = () => URL.revokeObjectURL(audioUrl);
    } catch (err) {
      console.error("Error playing audio:", err);
    }
  };

  const handleSubmit = async () => {
    if (!inputValue.trim()) return;
    console.log("Submitted:", inputValue);
    setIsSubmitting(true);
    try {
      console.log("Sending to FastAPI:", inputValue);
      const result = await sendPrompt(inputValue);

      if (result.assistant_audio_base64) {
        playAudio(result.assistant_audio_base64);
      }

      setInputValue(""); 
      resetTranscript(); 
    } catch (err) {
      console.error("Error sending prompt:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

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
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-background p-2 sm:p-4">
      <div className="w-full max-w-5xl flex flex-col gap-3 sm:gap-6 py-4">
        <div className="w-full aspect-video max-h-[50vh] sm:max-h-[60vh] mx-auto">
          <ScreenStream />
        </div>

        <div className="relative flex-shrink-0">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Send message or command..."
            className="w-full rounded-full border-2 border-border bg-background px-4 sm:px-6 py-3 sm:py-4 pr-20 sm:pr-28 text-sm sm:text-lg outline-none transition-all focus:border-primary focus:ring-2 focus:ring-primary/20"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSubmit();
              }
            }}
          />

          {browserSupportsSpeechRecognition && (
            <button
              onClick={toggleListening}
              className={`absolute right-12 sm:right-16 top-1/2 -translate-y-1/2 rounded-full p-2 sm:p-3 transition-all ${
                listening
                  ? "bg-primary text-primary-foreground hover:bg-primary/90 animate-pulse"
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              }`}
              aria-label={listening ? "Stop recording" : "Start recording"}
              title={listening ? "Stop recording" : "Start recording"}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="h-4 w-4 sm:h-5 sm:w-5"
              >
                <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                <path d="M19 10v1a7 7 0 0 1-14 0v-1a1 1 0 0 0-2 0v1a9 9 0 0 0 8 8.94V21H8a1 1 0 1 0 0 2h8a1 1 0 1 0 0-2h-3v-1.06A9 9 0 0 0 21 11v-1a1 1 0 1 0-2 0Z" />
              </svg>
            </button>
          )}

          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className={`absolute right-2 top-1/2 -translate-y-1/2 rounded-full p-2 sm:p-3 transition-all ${
              isSubmitting
                ? "bg-primary text-primary-foreground animate-pulse"
                : "bg-primary text-primary-foreground hover:bg-primary/90"
            }`}
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
              className="h-4 w-4 sm:h-5 sm:w-5"
            >
              <path d="M5 12h14" />
              <path d="m12 5 7 7-7 7" />
            </svg>
          </button>
        </div>

        {!browserSupportsSpeechRecognition && (
          <div className="text-center text-xs sm:text-sm text-muted-foreground flex-shrink-0">
            Speech recognition is not supported in your browser. Please use
            Chrome for the best experience.
          </div>
        )}
      </div>
    </div>
  );
}
