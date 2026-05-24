/**
 * Next.js edge middleware — session refresh + route protection.
 *
 * Two responsibilities:
 *  1. Refresh the Supabase Auth session on every request so the cookie
 *     stays valid (Supabase access tokens expire after 1 hour).
 *  2. Redirect unauthenticated users away from protected routes to /login.
 *
 * Protected routes (require a valid session):
 *   /report/*       — scanner report with history + AI intelligence
 *   /findings/*     — aggregated findings view
 *   /compliance     — compliance mapping view
 *   /scan/*         — live scan terminal
 */
import { NextResponse, type NextRequest } from "next/server";
import { createServerClient } from "@supabase/ssr";

const PROTECTED = ["/report", "/findings", "/compliance", "/scan"];

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          // Write refreshed tokens back to both the request and response
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          );
          response = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  // Refresh session — MUST be called before checking user
  const { data: { user } } = await supabase.auth.getUser();

  const pathname = request.nextUrl.pathname;
  const isProtected = PROTECTED.some(p => pathname.startsWith(p));

  if (isProtected && !user) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirectTo", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect signed-in users away from /login back to home
  if (pathname === "/login" && user) {
    const redirectTo = request.nextUrl.searchParams.get("redirectTo") ?? "/";
    return NextResponse.redirect(new URL(redirectTo, request.url));
  }

  return response;
}

export const config = {
  matcher: [
    // Run on all paths except Next.js internals and static assets
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
