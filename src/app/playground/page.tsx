"use client";

import { useState, useRef, useEffect } from "react";
import Hls from "hls.js";
import SpeechRecognition, {
  useSpeechRecognition,
} from "react-speech-recognition";

export default function PlaygroundPage() {
  const [inputValue, setInputValue] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [errorMessage, setErrorMessage] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastUpdateRef = useRef<number>(Date.now());

  // Speech recognition hook
  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition,
  } = useSpeechRecognition();

  // Fixed screen ID - change this to your actual IP
  const FIXED_SCREEN_ID = "10.121.229.107";
  //const streamUrl = `http://${FIXED_SCREEN_ID}:8888/screen/index.m3u8`;
  const streamUrl = `https://myers-horizon-dispatch-thinkpad.trycloudflare.com/screen/`;

  // Update input field with speech transcript
  useEffect(() => {
    if (transcript) {
      setInputValue(transcript);
    }
  }, [transcript]);

  const handleSubmit = () => {
    if (!inputValue.trim()) return;
    console.log("Submitted:", inputValue);
    setInputValue("");
    resetTranscript(); // Clear the transcript after submission
  };

  // Toggle microphone listening
  const toggleListening = () => {
    if (listening) {
      SpeechRecognition.stopListening();
    } else {
      resetTranscript();
      setInputValue("");
      SpeechRecognition.startListening({
        continuous: true, // Stop when user stops talking
        language: "en-US",
      });
    }
  };

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      const visible = document.visibilityState === "visible";
      setIsVisible(visible);

      if (visible && videoRef.current && !isPlaying) {
        setStreamStatus("connecting");
        setTimeout(() => {
          videoRef.current?.play().catch(console.error);
        }, 100);
      } else if (!visible) {
        setStreamStatus("paused");
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [isPlaying]);

  // Initialize HLS stream on component mount
  useEffect(() => {
    if (!videoRef.current) return;

    const video = videoRef.current;

    const playVideo = () => {
      video
        .play()
        .then(() => {
          setIsPlaying(true);
          setStreamStatus("live");
          setErrorMessage("");
          lastUpdateRef.current = Date.now();
        })
        .catch((error) => {
          console.log("Auto-play failed:", error.message);
          // Don't set error status for autoplay failures
          setStreamStatus("waiting");
        });
    };

    const handleHlsError = (event: string, data: any) => {
      console.log("HLS event:", event, "data:", data);

      // Only handle fatal errors, ignore non-fatal ones
      if (!data.fatal) {
        console.log("Non-fatal error, continuing...");
        return;
      }

      const errorType = data.type;
      const errorDetails = data.details;

      console.log(`Fatal error - Type: ${errorType}, Details: ${errorDetails}`);

      // Handle different types of fatal errors
      if (errorType === Hls.ErrorTypes.NETWORK_ERROR) {
        console.log("Network error - will retry automatically");
        setStreamStatus("waiting");
        setErrorMessage("Waiting for connection...");

        // Clear any existing retry timeout
        if (retryTimeoutRef.current) {
          clearTimeout(retryTimeoutRef.current);
        }

        // Try to recover after a delay
        retryTimeoutRef.current = setTimeout(() => {
          console.log("Attempting to recover from network error");
          if (hlsRef.current) {
            hlsRef.current.startLoad();
          }
        }, 3000);
      } else if (errorType === Hls.ErrorTypes.MEDIA_ERROR) {
        console.log("Media error - attempting recovery");
        setStreamStatus("waiting");
        if (hlsRef.current) {
          hlsRef.current.recoverMediaError();
        }
      } else {
        // For other fatal errors, just wait - don't show big error
        console.log("Other error type, waiting for stream to resume");
        setStreamStatus("waiting");
        setErrorMessage("Waiting for stream...");
      }
    };

    const initializeHls = () => {
      setStreamStatus("connecting");

      if (Hls.isSupported()) {
        console.log("Initializing HLS.js with URL:", streamUrl);

        const hls = new Hls({
          enableWorker: false,
          lowLatencyMode: true, // Enable low latency
          backBufferLength: 0, // No buffer behind
          debug: false,
          maxMaxBufferLength: 0.5, // Minimal buffer (0.5 seconds)
          maxBufferSize: 500 * 1000, // 500KB buffer
          maxBufferLength: 0.5, // Buffer only 0.5 seconds ahead
          liveSyncDurationCount: 0, // Stay exactly at live edge
          liveMaxLatencyDurationCount: 1, // Jump to live immediately if behind
          liveDurationInfinity: true,
          manifestLoadingTimeOut: 10000,
          manifestLoadingMaxRetry: 10,
          manifestLoadingRetryDelay: 500,
          levelLoadingTimeOut: 10000,
          levelLoadingMaxRetry: 10,
          levelLoadingRetryDelay: 500,
          fragLoadingTimeOut: 10000,
          fragLoadingMaxRetry: 6,
          fragLoadingRetryDelay: 500,
          highBufferWatchdogPeriod: 1,
          nudgeOffset: 0.1, // Minimal offset
          nudgeMaxRetry: 10, // Keep trying to stay at edge
        });

        hlsRef.current = hls;

        // Track successful data loading
        hls.on(Hls.Events.FRAG_LOADED, () => {
          console.log("Fragment loaded");
          lastUpdateRef.current = Date.now();
          if (streamStatus !== "live" && isPlaying) {
            setStreamStatus("live");
            setErrorMessage("");
          }
        });

        hls.on(Hls.Events.MEDIA_ATTACHED, () => {
          console.log("HLS media attached");
        });

        hls.on(Hls.Events.MANIFEST_LOADING, () => {
          console.log("HLS manifest loading");
          setStreamStatus("connecting");
        });

        hls.on(Hls.Events.MANIFEST_LOADED, () => {
          console.log("HLS manifest loaded successfully");
          setErrorMessage("");
          lastUpdateRef.current = Date.now();
        });

        hls.on(Hls.Events.LEVEL_LOADED, () => {
          console.log("HLS level loaded");
          lastUpdateRef.current = Date.now();
        });

        // Only log errors, don't crash on them
        hls.on(Hls.Events.ERROR, handleHlsError);

        try {
          console.log("Loading HLS source...");
          hls.loadSource(streamUrl);
          hls.attachMedia(video);

          // Try to play after a short delay
          setTimeout(() => {
            if (isVisible) {
              playVideo();
            }
          }, 1000);
        } catch (error) {
          console.error("HLS initialization error:", error);
          setStreamStatus("waiting");
          setErrorMessage("Waiting for stream...");
        }
      } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        // Native HLS support (Safari)
        console.log("Using native HLS support");
        video.src = streamUrl;

        video.addEventListener("loadeddata", () => {
          console.log("Native HLS data loaded");
          lastUpdateRef.current = Date.now();
          if (isVisible) {
            playVideo();
          }
        });

        video.addEventListener("error", (e) => {
          console.log("Native video error (will retry):", e);
          setStreamStatus("waiting");
          setErrorMessage("Waiting for stream...");
        });
      } else {
        setStreamStatus("error");
        setErrorMessage("HLS not supported in this browser");
      }
    };

    initializeHls();

    // Cleanup function
    return () => {
      console.log("Cleaning up HLS instance");
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      if (hlsRef.current) {
        hlsRef.current.destroy();
        hlsRef.current = null;
      }
    };
  }, [isVisible, streamUrl]);

  // Monitor stream health
  useEffect(() => {
    const checkInterval = setInterval(() => {
      const timeSinceUpdate = Date.now() - lastUpdateRef.current;

      // If no update in 8 seconds and we think we're live, switch to waiting
      if (timeSinceUpdate > 8000 && streamStatus === "live") {
        console.log("No updates for 8 seconds, switching to waiting status");
        setStreamStatus("waiting");
        setErrorMessage("Waiting for stream data...");
      }
    }, 2000); // Check every 2 seconds

    return () => clearInterval(checkInterval);
  }, [streamStatus]);

  // Resume playback when clicking on the video container
  const handleVideoClick = () => {
    if (videoRef.current && !isPlaying) {
      videoRef.current
        .play()
        .then(() => {
          setIsPlaying(true);
          setStreamStatus("live");
          setErrorMessage("");
          lastUpdateRef.current = Date.now();
        })
        .catch((error) => {
          console.log("Playback failed:", error.message);
          setStreamStatus("waiting");
        });
    }
  };

  // Retry connection
  const handleRetry = () => {
    console.log("Manual retry requested");
    setStreamStatus("connecting");
    setErrorMessage("Reconnecting...");

    if (hlsRef.current) {
      hlsRef.current.stopLoad();
      setTimeout(() => {
        hlsRef.current?.startLoad();
        videoRef.current?.play().catch(console.error);
      }, 500);
    } else if (videoRef.current) {
      videoRef.current.load();
      setTimeout(() => {
        videoRef.current?.play().catch(console.error);
      }, 1000);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      <div className="w-full max-w-5xl space-y-6">
        {/* Video/Remote Screen Area */}
        <div
          className="relative w-full overflow-hidden rounded-lg border-2 border-border bg-muted"
          onClick={handleVideoClick}
        >
          <div className="aspect-video flex items-center justify-center bg-black">
            <video
              ref={videoRef}
              controls
              autoPlay
              muted
              playsInline
              className="w-full h-full object-contain"
              onPlay={() => {
                setIsPlaying(true);
                setStreamStatus("live");
                setErrorMessage("");
                lastUpdateRef.current = Date.now();
              }}
              onPause={() => setIsPlaying(false)}
              onError={(e) => {
                console.log("Video error event:", e);
                // Don't show error, just wait
                setStreamStatus("waiting");
              }}
            >
              Your browser does not support the video tag.
            </video>

            {/* Overlay messages */}
            {!isVisible && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/70">
                <div className="text-center text-white p-4">
                  <p className="text-lg font-medium">Stream Paused</p>
                  <p className="text-sm">Return to this tab to resume</p>
                </div>
              </div>
            )}

            {streamStatus === "waiting" && (
              <div className="absolute top-4 right-4 bg-black/80 text-white px-4 py-2 rounded-lg text-sm">
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Waiting for stream data...</span>
                </div>
              </div>
            )}

            {streamStatus === "error" && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/70">
                <div className="text-center text-white p-4 max-w-md">
                  <p className="text-lg font-medium mb-2">
                    Stream Connection Error
                  </p>
                  <p className="text-sm mb-4 whitespace-pre-line">
                    {errorMessage}
                  </p>
                  <div className="flex gap-2 justify-center">
                    <button
                      onClick={handleRetry}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                    >
                      Retry Connection
                    </button>
                    <button
                      onClick={() => window.location.reload()}
                      className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                    >
                      Reload Page
                    </button>
                  </div>
                </div>
              </div>
            )}

            {streamStatus === "connecting" && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                <div className="text-center text-white p-4">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
                  <p className="text-sm">Connecting to stream...</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Enhanced Stream Status */}
        <div className="flex items-center justify-between rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className={`relative flex items-center justify-center`}>
                <div
                  className={`w-3 h-3 rounded-full ${
                    streamStatus === "live"
                      ? "bg-green-500 animate-pulse"
                      : streamStatus === "paused"
                      ? "bg-orange-500"
                      : streamStatus === "error"
                      ? "bg-red-500"
                      : "bg-yellow-500 animate-pulse"
                  }`}
                ></div>
                <div
                  className={`absolute inset-0 rounded-full ${
                    streamStatus === "live"
                      ? "bg-green-500 animate-ping"
                      : "hidden"
                  }`}
                  style={{ animationDuration: "2s" }}
                ></div>
              </div>

              <div className="flex flex-col">
                <span className="text-sm font-semibold">
                  {streamStatus === "live"
                    ? "LIVE"
                    : streamStatus === "paused"
                    ? "PAUSED"
                    : streamStatus === "error"
                    ? "CONNECTION ERROR"
                    : streamStatus === "waiting"
                    ? "BUFFERING"
                    : "CONNECTING"}
                </span>
                <span className="text-xs text-muted-foreground max-w-md">
                  {streamStatus === "live"
                    ? "Stream is live and running"
                    : streamStatus === "paused"
                    ? "Stream paused - tab in background"
                    : streamStatus === "error"
                    ? errorMessage
                    : streamStatus === "waiting"
                    ? "Waiting for stream data - weak connection detected"
                    : "Establishing connection to stream server..."}
                </span>
              </div>
            </div>

            {streamStatus !== "error" && (
              <div className="hidden sm:flex items-center gap-4 pl-4 border-l border-border">
                <div className="flex flex-col">
                  <span className="text-xs text-muted-foreground">Server</span>
                  <span className="text-sm font-medium">
                    {FIXED_SCREEN_ID}:8888
                  </span>
                </div>
                <div className="flex flex-col">
                  <span className="text-xs text-muted-foreground">Status</span>
                  <span className="text-sm font-medium">
                    {streamStatus === "live"
                      ? "Connected"
                      : streamStatus === "paused"
                      ? "Standby"
                      : streamStatus === "waiting"
                      ? "Buffering"
                      : "Connecting"}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {(streamStatus === "error" || streamStatus === "waiting") && (
              <button
                onClick={handleRetry}
                className="flex items-center gap-2 px-3 py-2 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                <svg
                  className="w-3 h-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                Retry
              </button>
            )}
          </div>
        </div>

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

        {/* Speech recognition status */}
        {listening && (
          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span>Listening... Speak now</span>
          </div>
        )}

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
