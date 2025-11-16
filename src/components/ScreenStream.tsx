"use client";

import { useEffect, useState } from "react";

export default function ScreenStream() {
  const [mounted, setMounted] = useState(false);

  const streamBaseUrl = "https://means-heating-whom-sunday.trycloudflare.com/screen";

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="w-full h-screen bg-black">
      {mounted && (
        <iframe
          src={streamBaseUrl}
          className="w-full h-full border-0"
          allow="autoplay; fullscreen; picture-in-picture"
          allowFullScreen
          title="Screen Stream"
        />
      )}
    </div>
  );
}