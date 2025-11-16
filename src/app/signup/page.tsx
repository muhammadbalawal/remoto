"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createBrowserClient } from "@supabase/ssr";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function SignupPage() {
  const router = useRouter();

  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    const { error } = await supabase.auth.signUp({
      email,
      password,
    });

    setLoading(false);

    if (error) {
      setErrorMsg(error.message);
      return;
    }

    // 🚀 Redirect user straight to login page after signup
    router.push("/login");
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-sm p-6 shadow-xl rounded-2xl">
        <CardContent className="flex flex-col gap-4">
          <h1 className="text-2xl font-bold text-center mb-2">Create Account</h1>

          <form onSubmit={handleSignup} className="flex flex-col gap-4">
            <Input
              type="email"
              placeholder="Email"
              required
              onChange={(e) => setEmail(e.target.value)}
            />

            <Input
              type="password"
              placeholder="Password (min 6 chars)"
              required
              onChange={(e) => setPassword(e.target.value)}
            />

            {errorMsg && (
              <p className="text-red-500 text-sm">{errorMsg}</p>
            )}

            <Button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Sign Up"}
            </Button>
          </form>

          <div className="text-center mt-2">
            <p className="text-sm text-muted-foreground">
              Already have an account?
            </p>
            <Button
              variant="outline"
              className="w-full mt-2"
              onClick={() => router.push("/login")}
            >
              Back to Login
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
