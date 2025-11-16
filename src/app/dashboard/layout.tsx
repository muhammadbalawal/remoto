"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClientSupabase } from "@/lib/supabase/client";
import { Button } from "@/components/ui/button";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const supabase = createClientSupabase();

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push("/"); // go back to main page
  };

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white p-6 flex flex-col">
        <h1 className="text-xl font-bold mb-6">Dashboard</h1>

        <nav className="flex flex-col gap-3 flex-1">
          <Link
            href="/dashboard/playground"
            className="hover:bg-gray-700 p-2 rounded"
          >
            Playground
          </Link>

          <Link
            href="/dashboard/config"
            className="hover:bg-gray-700 p-2 rounded"
          >
            Config
          </Link>
        </nav>

        {/* Sign Out Button (bottom) */}
        <div className="mt-auto pt-6">
          <Button
            variant="destructive"
            className="w-full"
            onClick={handleSignOut}
          >
            Sign Out
          </Button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-8 bg-gray-50">
        {children}
      </main>
    </div>
  );
}
