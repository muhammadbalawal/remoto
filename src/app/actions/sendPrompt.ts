"use server";

export async function sendPrompt(text: string): Promise<string> {
  const res = await fetch("http://localhost:8000/improve", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
    cache: "no-store", 
  });

  if (!res.ok) {
    throw new Error("Failed to fetch improved prompt");
  }

  const data: { improved_prompt: string } = await res.json();
  return data.improved_prompt;
}
