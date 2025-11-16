"use server";

import { createClientSupabase } from "@/lib/supabase/client";

export async function sendPrompt(text: string): Promise<string> {
  // 1. Create supabase client
  const supabase = createClientSupabase();

  // 2. Get current user
  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user) {
    throw new Error("Not authenticated");
  }

  // 3. Fetch user's config
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

  // 4. Send request to the user's backend
  const res = await fetch(`${backendURL}/voice`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error("Failed to fetch improved prompt");
  }

  const payload: { improved_prompt: string } = await res.json();
  return payload.improved_prompt;
}
