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
    // Get logged-in user
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) return;

    // Fetch config row
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
    <div className="w-full h-full">
      {mounted && streamURL ? (
        <iframe
          src={streamURL}
          className="w-full h-full border-0"
          allow="autoplay; fullscreen; picture-in-picture"
          allowFullScreen
          title="Screen Stream"
        />
      ) : (
        <p className="text-center text-gray-500 p-4">
          {mounted ? "Loading stream…" : "Preparing…"}
        </p>
      )}
    </div>
  );
}
