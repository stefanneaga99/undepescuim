import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // react-leaflet v5 is ESM-only; transpile it for SSR compatibility.
  // Map components must additionally be loaded client-side:
  //   const MapView = dynamic(() => import("@/components/map/map-view"), { ssr: false })
  transpilePackages: ["react-leaflet"],
  // Dev-only: allow the local browserless container (Docker bridge gateway)
  // to fetch chunks — Next blocks cross-origin dev requests by default.
  allowedDevOrigins: ["172.17.0.1", "*.172.17.0.1"],
  /* config options here */
};

export default nextConfig;
