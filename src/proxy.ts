import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const WWW_HOST = "www.unde-pescuim.ro";
const APEX_HOST = "unde-pescuim.ro";

function requestHost(request: NextRequest): string {
  // Vercel and Cloudflare route using Host. Keep this intentionally limited to
  // the configured www hostname so preview/rollback domains are untouched.
  return (request.headers.get("host") ?? "")
    .split(",", 1)[0]
    .trim()
    .toLowerCase()
    .replace(/:(?:443|80)$/, "");
}

export function proxy(request: NextRequest) {
  if (requestHost(request) !== WWW_HOST) {
    return NextResponse.next();
  }

  const destination = request.nextUrl.clone();
  destination.protocol = "https:";
  destination.hostname = APEX_HOST;
  destination.port = "";

  return NextResponse.redirect(destination, 308);
}

export const config = {
  matcher: "/:path*",
};
