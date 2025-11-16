"use client";

import { useState, useEffect } from "react";
import { createClientSupabase } from "@/lib/supabase/client";
import { Input } from "@/components/ui/genericInput";
import { Button } from "@/components/ui/genericButton";
import { Card, CardContent } from "@/components/ui/card";

export default function ConfigPage() {
  const supabase = createClientSupabase();

  const [streamURL, setStreamURL] = useState("");
  const [backendURL, setBackendURL] = useState("");
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  // Load user config if exists
  useEffect(() => {
    const loadConfig = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) return;

      const { data, error } = await supabase
        .from("UserConfig")
        .select("json")
        .eq("id", user.id)
        .single();

      if (error) return;

      if (data?.json) {
        setStreamURL(data.json.streamURL || "");
        setBackendURL(data.json.backendURL || "");
      }
    };

    loadConfig();
  }, []);

  const handleSave = async () => {
    setLoading(true);
    setSuccessMsg("");
    setErrorMsg("");

    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      setErrorMsg("Not logged in.");
      setLoading(false);
      return;
    }

    const jsonData = {
      streamURL,
      backendURL,
    };

    // Insert or update
    const { error } = await supabase.from("UserConfig").upsert({
      id: user.id,
      json: jsonData,
    });

    setLoading(false);

    if (error) {
      setErrorMsg(error.message);
    } else {
      setSuccessMsg("Configuration saved!");
    }
  };

  return (
    <main className="h-full w-full overflow-hidden flex justify-center items-center p-4">
      <Card className="w-full max-w-lg p-4 sm:p-6 rounded-2xl shadow-lg">
        <CardContent className="flex flex-col gap-4 sm:gap-6">
          <h1 className="text-xl sm:text-2xl font-bold text-center">
            User Configuration
          </h1>

          <div className="flex flex-col gap-2 sm:gap-3">
            <label className="font-medium text-sm sm:text-base">
              Stream URL
            </label>
            <Input
              placeholder="rtsp://your-stream-url"
              value={streamURL}
              onChange={(e) => setStreamURL(e.target.value)}
              className="text-sm sm:text-base"
            />
          </div>

          <div className="flex flex-col gap-2 sm:gap-3">
            <label className="font-medium text-sm sm:text-base">
              Backend URL
            </label>
            <Input
              placeholder="https://your-backend-api.com"
              value={backendURL}
              onChange={(e) => setBackendURL(e.target.value)}
              className="text-sm sm:text-base"
            />
          </div>

          {errorMsg && (
            <p className="text-red-500 text-xs sm:text-sm">{errorMsg}</p>
          )}
          {successMsg && (
            <p className="text-green-500 text-xs sm:text-sm">{successMsg}</p>
          )}

          <Button
            onClick={handleSave}
            disabled={loading}
            className="w-full text-sm sm:text-base"
          >
            {loading ? "Saving..." : "Save Configuration"}
          </Button>
        </CardContent>
      </Card>
    </main>
  );
}
