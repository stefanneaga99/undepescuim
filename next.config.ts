import type { NextConfig } from "next";
// F6 (t_0618943a): PWA light — service worker via Serwist (offline-pwa-feasibility.md §3).
// swSrc is compiled to public/sw.js at build time (gitignored — generated artifact).
// NOTE: Serwist's webpack plugin only runs under a webpack build, so the `build`
// script uses `next build --webpack` (package.json) — Turbopack skips the hook.
import withSerwistInit from "@serwist/next";
const withSerwist = withSerwistInit({
  swSrc: "src/app/sw.ts",
  swDest: "public/sw.js",
  // Data JSONs are ~45MB total — they must NOT be precached at install
  // (offline-pwa-feasibility.md §3: data tier is runtime NetworkFirst via the
  // app-data cache; precaching them makes SW install crawl/hang). Default
  // globPublicPatterns is ["**/*"] → exclude the whole /data dir, keep only
  // shell assets (icons, SVG logos) in the precache.
  globPublicPatterns: ["**/*", "!data/**"],
  // serverless build: the precache manifest comes from the Next build
  // manifest. No globDirectory/globPatterns (that was the static-export path).
});

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
      "img-src 'self' data: blob: https://tile.openstreetmap.org https://*.tile.openstreetmap.org",
      "font-src 'self' data:",
      "connect-src 'self' https://tile.openstreetmap.org https://*.tile.openstreetmap.org",
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
    const swHeaders = [
      // F6 (t_0618943a): sw.js must NEVER be cached client-side — a stale
      // service worker is the "stale-cache trap" (offline-pwa-feasibility.md
      // §2 risk 2). Registration uses updateViaCache:"none"; this header is
      // the server-side guarantee (self-hosted next start; vercel.json has
      // the matching rule for the Vercel edge).
      { key: "Cache-Control", value: "no-cache" },
      // Allow the SW to control the whole origin (default scope would be
      // /sw.js's dir "/" anyway — explicit is safer).
      { key: "Service-Worker-Allowed", value: "/" },
    ];
    return [
      { source: "/sw.js", headers: swHeaders },
      { source: "/(.*)", headers: securityHeaders },
    ];
  },
  /* config options here */
};

// Perf budget tooling (t_fbbc943b, docs/performance-test-plan.md §5.4):
// `ANALYZE=true npm run build` produces the @next/bundle-analyzer interactive
// chunk report used for the M10 initial-JS budget. Builds without the env var
// are untouched (the analyzer wrapper is a no-op when disabled).
import withBundleAnalyzer from "@next/bundle-analyzer";
const analyzer = withBundleAnalyzer({ enabled: process.env.ANALYZE === "true" });

// F6 (t_0618943a): Serwist wraps the (optionally analyzer-wrapped) config so
// the build emits public/sw.js + precache manifest from the Next build output.
export default withSerwist(analyzer(nextConfig));