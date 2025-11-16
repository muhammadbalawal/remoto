"use server";

import { createServerSupabase } from "@/lib/supabase/server";

export async function sendPrompt(text: string): Promise<string> {
    // Use server-side client
    const supabase = await createServerSupabase();

    const {
        data: { user },
        error: userError,
    } = await supabase.auth.getUser();

    if (userError || !user) {
        throw new Error("Not authenticated");
    }

    // Rest of your code remains the same...
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