import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // react-leaflet v5 is ESM-only; transpile it for SSR compatibility.
  // Map components must additionally be loaded client-side:
  //   const MapView = dynamic(() => import("@/components/map/map-view"), { ssr: false })
  transpilePackages: ["react-leaflet"],
  /* config options here */
};

export default nextConfig;
