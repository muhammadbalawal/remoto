// middleware.ts (root)
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";

export async function middleware(req: NextRequest) {
  // Only run on HTML navigation requests
  const pathname = req.nextUrl.pathname;

  // Protect /dashboard and any subpath
  const isProtected = pathname === "/dashboard" || pathname.startsWith("/dashboard/");

  if (!isProtected) {
    return NextResponse.next();
  }

  // Build a server-side supabase client that can read cookies
  const cookieStore = await cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value;
        },
      },
    }
  );

  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (isProtected && !session) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/dashboard"],
};
