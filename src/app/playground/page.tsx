"use client";

import { useState, useRef, useEffect } from "react";
import Hls from "hls.js";

export default function PlaygroundPage() {
  const [inputValue, setInputValue] = useState("");
  const [isPlaying, setIsPlaying] = useState(false);
  const [isVisible, setIsVisible] = useState(true);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [errorMessage, setErrorMessage] = useState("");
  const videoRef = useRef<HTMLVideoElement>(null);

  // Fixed screen ID - change this to your actual IP
  const FIXED_SCREEN_ID = "10.121.229.107";
  const streamUrl = `http://${FIXED_SCREEN_ID}:8888/screen/index.m3u8`;

  const handleSubmit = () => {
    if (!inputValue.trim()) return;
    console.log("Submitted:", inputValue);
    setInputValue("");
  };

  // Test if the stream URL is accessible
  const testStreamConnection = async (url: string): Promise<boolean> => {
    try {
      const response = await fetch(url, {
        method: "HEAD",
        mode: "no-cors", // We can't read the response but we can see if it fails
      });
      return true;
    } catch (error) {
      return false;
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
    let hls: Hls | null = null;
    let retryCount = 0;
    const maxRetries = 3;

    const playVideo = () => {
      video
        .play()
        .then(() => {
          setIsPlaying(true);
          setStreamStatus("live");
          setErrorMessage("");
          retryCount = 0; // Reset retry count on success
        })
        .catch((error) => {
          console.log("Auto-play failed:", error.message);
          setStreamStatus("error");
          setErrorMessage(`Playback failed: ${error.message}`);
        });
    };

    const handleHlsError = (event: string, data: any) => {
      console.error("HLS error event:", event, "data:", data);
      retryCount++;

      // Default error message for empty error objects
      let errorMsg =
        "Cannot connect to stream server. Common issues:\n• Server is not running\n• Wrong IP address\n• CORS restrictions\n• Network firewall";

      // Try to extract meaningful information from the error
      if (data && data.details) {
        errorMsg = `Stream error: ${data.details}`;
      } else if (data && data.type) {
        errorMsg = `Stream error: ${data.type}`;
      } else if (data && data.response) {
        errorMsg = `HTTP ${data.response.code}: ${
          data.response.text || "Server error"
        }`;
      }

      setErrorMessage(errorMsg);
      setStreamStatus("error");

      // Only attempt recovery for network errors, not for fatal errors
      if (data && data.fatal) {
        switch (data.type) {
          case Hls.ErrorTypes.NETWORK_ERROR:
            if (retryCount <= maxRetries) {
              console.log(`Network error - retry ${retryCount}/${maxRetries}`);
              setErrorMessage(
                `Network error - retrying... (${retryCount}/${maxRetries})`
              );
              setTimeout(() => {
                hls?.startLoad();
              }, 2000 * retryCount); // Exponential backoff
            } else {
              setErrorMessage(
                "Network error - failed after multiple retries. Check server connection."
              );
            }
            break;
          case Hls.ErrorTypes.MEDIA_ERROR:
            console.log("Media error, recovering...");
            hls?.recoverMediaError();
            break;
          default:
            console.log("Fatal error, cannot recover");
            setErrorMessage(
              "Fatal stream error. Please verify:\n1. Server is running\n2. Correct IP address\n3. Port 8888 is accessible"
            );
            break;
        }
      }
    };

    const initializeHls = async () => {
      // First, test if the stream URL is accessible
      setStreamStatus("connecting");
      setErrorMessage("Testing connection to stream server...");

      if (Hls.isSupported()) {
        console.log("Initializing HLS.js with URL:", streamUrl);

        hls = new Hls({
          enableWorker: false,
          lowLatencyMode: true,
          backBufferLength: 90,
          debug: false,
          maxMaxBufferLength: 30,
          liveSyncDurationCount: 3,
        });

        // Add all event listeners for debugging
        hls.on(Hls.Events.MEDIA_ATTACHED, () => {
          console.log("HLS media attached");
        });

        hls.on(Hls.Events.MANIFEST_LOADING, () => {
          console.log("HLS manifest loading");
        });

        hls.on(Hls.Events.MANIFEST_LOADED, () => {
          console.log("HLS manifest loaded successfully");
          setErrorMessage("");
        });

        hls.on(Hls.Events.LEVEL_LOADED, () => {
          console.log("HLS level loaded");
        });

        hls.on(Hls.Events.ERROR, handleHlsError);

        try {
          console.log("Loading HLS source...");
          hls.loadSource(streamUrl);
          hls.attachMedia(video);
        } catch (error) {
          console.error("HLS initialization error:", error);
          setStreamStatus("error");
          setErrorMessage(`HLS initialization failed: ${error}`);
        }
      } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        // Native HLS support (Safari)
        console.log("Using native HLS support");
        video.src = streamUrl;

        video.addEventListener("loadeddata", () => {
          console.log("Native HLS data loaded");
          if (isVisible) {
            playVideo();
          }
        });

        video.addEventListener("error", (e) => {
          console.error("Native video error:", e);
          setStreamStatus("error");
          setErrorMessage(
            "Native video error - check stream URL and CORS settings"
          );
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
      if (hls) {
        hls.destroy();
      }
    };
  }, [isVisible, streamUrl]);

  // Resume playback when clicking on the video container
  const handleVideoClick = () => {
    if (videoRef.current && !isPlaying) {
      videoRef.current
        .play()
        .then(() => {
          setIsPlaying(true);
          setStreamStatus("live");
          setErrorMessage("");
        })
        .catch((error) => {
          setStreamStatus("error");
          setErrorMessage(`Playback failed: ${error.message}`);
        });
    }
  };

  // Retry connection
  const handleRetry = () => {
    console.log("Manual retry requested");
    setStreamStatus("connecting");
    setErrorMessage("Reconnecting...");

    if (videoRef.current) {
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
              }}
              onPause={() => setIsPlaying(false)}
              onError={(e) => {
                console.error("Video error event:", e);
                setStreamStatus("error");
                setErrorMessage(
                  "Video element error - check console for details"
                );
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
                    : "CONNECTING"}
                </span>
                <span className="text-xs text-muted-foreground max-w-md">
                  {streamStatus === "live"
                    ? "Stream is live and running"
                    : streamStatus === "paused"
                    ? "Stream paused - tab in background"
                    : streamStatus === "error"
                    ? errorMessage
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
                      : "Connecting"}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {streamStatus === "error" && (
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

        {/* Input Field */}
        <div className="relative">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Send message or command..."
            className="w-full rounded-full border-2 border-border bg-background px-6 py-4 pr-16 text-lg outline-none transition-all focus:border-primary focus:ring-2 focus:ring-primary/20"
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                handleSubmit();
              }
            }}
          />
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
      </div>
    </div>
  );
}
