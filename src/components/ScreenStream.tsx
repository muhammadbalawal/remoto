"use client";

import { useEffect, useState } from "react";
import { createClientSupabase } from "@/lib/supabase/client";

export default function ScreenStream() {
  const supabase = createClientSupabase();

  const [mounted, setMounted] = useState(false);
  const [streamURL, setStreamURL] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
    fetchStreamURL();
  }, []);

  async function fetchStreamURL() {
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) return;

    const { data, error } = await supabase
      .from("UserConfig")
      .select("json")
      .eq("id", user.id)
      .single();

    if (error || !data?.json?.streamURL) {
      console.warn("No stream URL found in UserConfig");
      return;
    }

    setStreamURL(data.json.streamURL);
  }

  return (
    <div className="relative w-full h-full">
      {/* Animated gradient border wrapper */}
      <div className="absolute inset-0 rounded-lg sm:rounded-xl overflow-hidden">
        <div className="absolute inset-0 animate-gradient-rotate">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 blur-xl opacity-75"></div>
        </div>

        {/* Inner container with padding to show border */}
        <div className="relative w-full h-full p-0.5 sm:p-1">
          <div className="w-full h-full bg-black rounded-md sm:rounded-lg overflow-hidden">
            {mounted && streamURL ? (
              <iframe
                src={streamURL}
                className="w-full h-full border-0"
                allow="autoplay; fullscreen; picture-in-picture"
                allowFullScreen
                title="Screen Stream"
              />
            ) : (
              <p className="text-center text-gray-500 p-2 sm:p-4 flex items-center justify-center h-full text-xs sm:text-sm">
                {mounted ? "Loading stream…" : "Preparing…"}
              </p>
            )}
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes gradient-rotate {
          0% {
            transform: rotate(0deg) scale(1.5);
          }
          100% {
            transform: rotate(360deg) scale(1.5);
          }
        }

        .animate-gradient-rotate {
          animation: gradient-rotate 8s linear infinite;
        }
      `}</style>
    </div>
  );
}
