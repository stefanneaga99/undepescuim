import type { NextConfig } from "next";

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
  /* config options here */
};

export default nextConfig;
