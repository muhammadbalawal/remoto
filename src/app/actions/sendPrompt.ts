"use server";

import { createServerSupabase } from "@/lib/supabase/server";

interface VoiceResponse {
  assistant_message: string;
  assistant_audio_base64: string | null;
  code_executed: string | null;
  execution_result: string;
  screenshot_base64: string;
  success: boolean;
}

export async function sendPrompt(text: string): Promise<VoiceResponse> {
  const supabase = await createServerSupabase();

  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user) {
    throw new Error("Not authenticated");
  }

  const { data, error: configError } = await supabase
    .from("UserConfig")
    .select("json")
    .eq("id", user.id)
    .single();

  if (configError) {
    throw new Error("Error fetching user config");
  }

  const backendURL = data?.json?.backendURL;

  if (!backendURL) {
    throw new Error("Backend URL not configured for this user");
  }

  const res = await fetch(`${backendURL}voice`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      history: [],
    }),
    cache: "no-store",
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Backend error: ${res.status} - ${errorText}`);
  }

  const payload: VoiceResponse = await res.json();

  if (!payload.success) {
    throw new Error(`Command failed: ${payload.execution_result}`);
  }

  return payload;
}
