"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createBrowserClient } from "@supabase/ssr";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/genericInput";
import { Button } from "@/components/ui/genericButton";

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

    router.push("/login");
  }

  return (
    <main className="h-screen w-screen overflow-hidden flex items-center justify-center p-4">
      <div className="relative w-full max-w-sm">
        <div className="absolute inset-0 rounded-2xl overflow-hidden">
          <div className="absolute inset-0 animate-gradient-rotate">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 blur-xl opacity-75"></div>
          </div>
        </div>

        <div className="relative p-[2px]">
          <Card className="w-full p-4 sm:p-6 shadow-xl rounded-2xl bg-background">
            <CardContent className="flex flex-col gap-3 sm:gap-4">
              <h1 className="text-xl sm:text-2xl font-bold text-center mb-2">
                Create Account
              </h1>

              <form
                onSubmit={handleSignup}
                className="flex flex-col gap-3 sm:gap-4"
              >
                <Input
                  type="email"
                  placeholder="Email"
                  required
                  onChange={(e) => setEmail(e.target.value)}
                  className="text-sm sm:text-base"
                />

                <Input
                  type="password"
                  placeholder="Password (min 6 character's)"
                  required
                  onChange={(e) => setPassword(e.target.value)}
                  className="text-sm sm:text-base"
                />

                {errorMsg && (
                  <p className="text-red-500 text-xs sm:text-sm">{errorMsg}</p>
                )}

                <Button
                  type="submit"
                  disabled={loading}
                  className="text-sm sm:text-base"
                >
                  {loading ? "Creating..." : "Sign Up"}
                </Button>
              </form>

              <div className="text-center mt-2">
                <p className="text-xs sm:text-sm text-muted-foreground">
                  Already have an account?
                </p>
                <Button
                  variant="outline"
                  className="w-full mt-2 text-xs sm:text-sm"
                  onClick={() => router.push("/login")}
                >
                  Back to Login
                </Button>
              </div>
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
