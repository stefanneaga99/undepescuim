import type { MetadataRoute } from "next";

/**
 * PWA install manifest (docs/offline-pwa-feasibility.md §5). Served at
 * /manifest.webmanifest via Next's typed MetadataRoute.Manifest route.
 *
 * theme_color matches the app's actual --primary (#171717, globals.css) and
 * the Header logo tile — the same value as viewport.themeColor in layout.tsx.
 */
export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "UndePescuim.ro",
    short_name: "UndePescuim.ro",
    description: "Harta apelor de pescuit din România — Romanian fishing waters map",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#ffffff",
    theme_color: "#171717",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      {
        src: "/icons/icon-512-maskable.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
  };
}
