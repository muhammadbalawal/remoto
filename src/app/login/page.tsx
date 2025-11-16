"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClientSupabase } from "@/lib/supabase/client";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const router = useRouter();
  const supabase = createClientSupabase();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleLogin = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    setLoading(false);

    if (error) {
      setErrorMsg(error.message);
      return;
    }

    router.push("/dashboard/config");
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-sm p-6 shadow-xl rounded-2xl">
        <CardContent className="flex flex-col gap-4">
          <h1 className="text-2xl font-bold text-center mb-2">Welcome Back</h1>

          <form onSubmit={handleLogin} className="flex flex-col gap-4">
            <Input
              type="email"
              placeholder="Email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <Input
              type="password"
              placeholder="Password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            {errorMsg && (
              <p className="text-red-500 text-sm">{errorMsg}</p>
            )}

            <Button type="submit" disabled={loading}>
              {loading ? "Signing in…" : "Sign In"}
            </Button>
          </form>

          <div className="text-center mt-2">
            <p className="text-sm text-muted-foreground">
              Don’t have an account?
            </p>
            <Button
              variant="outline"
              className="w-full mt-2"
              onClick={() => router.push("/signup")}
            >
              Create Account
            </Button>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
