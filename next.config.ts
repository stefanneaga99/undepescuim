import type { NextConfig } from "next";

// REM-7: hardening headers (docs/security-test-plan.md). Applied to every
// Next-served route (pages + /api/*). The CSP starts permissive on purpose:
// Next injects inline bootstrap scripts (script-src 'unsafe-inline') and the
// Leaflet app needs tile images + inline styles. Tighten once the live domain
// behavior is confirmed (report-only mode first — see the plan §8).
const securityHeaders = [
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob: https://*.tile.openstreetmap.org",
      "font-src 'self' data:",
      "connect-src 'self' https://*.tile.openstreetmap.org",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "frame-ancestors 'none'",
    ].join("; "),
  },
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
  // Legacy guard; frame-ancestors 'none' in the CSP is the modern equivalent.
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    // NOTE: geolocation is deliberately NOT blocked — the "În apropiere"
    // feature uses it. Block everything else this app never needs.
    value:
      "camera=(), microphone=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()",
  },
];

const nextConfig: NextConfig = {
  // react-leaflet v5 is ESM-only; transpile it for SSR compatibility.
  // Map components must additionally be loaded client-side:
  //   const MapView = dynamic(() => import("@/components/map/map-view"), { ssr: false })
  transpilePackages: ["react-leaflet"],
  // Dev-only: allow the local browserless container (Docker bridge gateway)
  // to fetch chunks — Next blocks cross-origin dev requests by default.
  allowedDevOrigins: ["172.17.0.1", "*.172.17.0.1"],
  // F3 (t_5b1250b3): DO NOT add `output: "export"` here. The report flow needs
  // the serverless POST /api/report route (src/app/api/report/route.ts) to
  // create GitHub issues; a static export silently removes it. If serverless is
  // ever dropped, swap ReportForm's submit handler to the Google-Form fallback
  // (t_c21762e3) instead of exporting statically.
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
  /* config options here */
};

// Perf budget tooling (t_fbbc943b, docs/performance-test-plan.md §5.4):
// `ANALYZE=true npm run build` produces the @next/bundle-analyzer interactive
// chunk report used for the M10 initial-JS budget. Builds without the env var
// are untouched (the analyzer wrapper is a no-op when disabled).
import withBundleAnalyzer from "@next/bundle-analyzer";
const analyzer = withBundleAnalyzer({ enabled: process.env.ANALYZE === "true" });

export default analyzer(nextConfig);