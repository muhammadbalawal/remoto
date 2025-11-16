// app/auth/logout/route.ts
import { NextResponse } from "next/server";
import { createServerSupabase } from "@/lib/supabase/server";

export async function POST() {
  const supabase = await createServerSupabase();
  await supabase.auth.signOut();
  // Redirect to login after logout
  return NextResponse.redirect("/login");
}
