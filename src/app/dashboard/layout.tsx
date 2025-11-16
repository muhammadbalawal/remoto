"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClientSupabase } from "@/lib/supabase/client";
import { Button } from "@/components/ui/genericButton";
import { buttonVariants } from "@/components/ui/genericButton";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const supabase = createClientSupabase();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push("/");
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Hamburger Button - INVISIBLE BACKGROUND */}
      <div
        className="fixed left-0 top-0 z-50 cursor-pointer p-3"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        {/* Pure white icon, no background */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          strokeWidth={2.8}
          className={`w-7 h-7 transition-transform duration-300 ${
            sidebarOpen ? "rotate-180" : ""
          }`}
          fill="none"
        >
          <defs>
            <linearGradient
              id="hamburgerGradient"
              gradientUnits="userSpaceOnUse"
            >
              <stop offset="0%" stopColor="#3b82f6" /> {/* blue-500 */}
              <stop offset="50%" stopColor="#a855f7" /> {/* purple-500 */}
              <stop offset="100%" stopColor="#ec4899" /> {/* pink-500 */}
            </linearGradient>
          </defs>

          <g className="animate-gradient-rotate origin-center">
            <path
              stroke="url(#hamburgerGradient)"
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
            />
          </g>
        </svg>
      </div>

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 h-screen
          w-64 
          bg-black           /* jet black */
          text-white 
          p-6 
          flex flex-col
          z-40
          transition-transform duration-300 ease-in-out
          shadow-2xl border-r border-white/10
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        <div className="flex items-center justify-center mb-6"></div>

        {/* NAV ITEMS with button-style hover */}
        <nav className="flex flex-col gap-2 flex-1">
          <Link
            href="/dashboard/playground"
            className={`
              px-3 py-2 rounded-md transition-all
              text-white bg-transparent
              hover:bg-primary hover:text-primary-foreground
            `}
            onClick={() => setSidebarOpen(false)}
          >
            Playground
          </Link>

          <Link
            href="/dashboard/config"
            className={`
              px-3 py-2 rounded-md transition-all
              text-white bg-transparent
              hover:bg-primary hover:text-primary-foreground
            `}
            onClick={() => setSidebarOpen(false)}
          >
            Config
          </Link>

          {/* Moved Sign Out Button under Config */}
          <Button
            variant="default"
            className="w-full mt-2"
            onClick={handleSignOut}
          >
            Sign Out
          </Button>
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 bg-background h-screen overflow-hidden">
        {children}
      </main>
    </div>
  );

  <style jsx>{`
    @keyframes gradient-rotate {
      0% {
        transform: rotate(0deg);
      }
      100% {
        transform: rotate(360deg);
      }
    }

    .animate-gradient-rotate {
      animation: gradient-rotate 2s linear infinite;
    }
  `}</style>;
}
