"use client";

import { useState, useEffect } from "react";
import { createClientSupabase } from "@/lib/supabase/client";
import { Input } from "@/components/ui/genericInput";
import { Button } from "@/components/ui/genericButton";
import { Card, CardContent } from "@/components/ui/card";
import { useRouter } from "next/navigation";

export default function ConfigPage() {
  const supabase = createClientSupabase();
  const router = useRouter();

  const [streamURL, setStreamURL] = useState("");
  const [backendURL, setBackendURL] = useState("");
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

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

    const { error } = await supabase.from("UserConfig").upsert({
      id: user.id,
      json: jsonData,
    });

    setLoading(false);

    if (error) {
      setErrorMsg(error.message);
    } else {
      router.push("/dashboard/playground");
    }
  };

  return (
    <main className="h-full w-full overflow-hidden flex justify-center items-center p-4">
      <div className="relative w-full max-w-lg">
        <div className="absolute inset-0 rounded-2xl overflow-hidden">
          <div className="absolute inset-0 animate-gradient-rotate">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 blur-xl opacity-75"></div>
          </div>
        </div>

        <div className="relative p-[2px]">
          <Card className="w-full p-4 sm:p-6 rounded-2xl shadow-lg bg-background">
            <CardContent className="flex flex-col gap-4 sm:gap-6">
              <h1 className="text-xl sm:text-2xl font-bold text-center">
                User Configuration
              </h1>

              <div className="flex flex-col gap-2 sm:gap-3">
                <label className="font-medium text-sm sm:text-base">
                  Screen Share URL
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
                  AI Model URL
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
                <p className="text-green-500 text-xs sm:text-sm">
                  {successMsg}
                </p>
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
    </main>
  );
}
