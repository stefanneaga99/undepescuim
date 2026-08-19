"use client";
import { useEffect } from "react";

/**
 * F6 (t_0618943a): PWA light — client-side service worker registration
 * (docs/offline-pwa-feasibility.md §3 "SW registration (client)").
 *
 * Registers the Serwist-generated /sw.js (produced at build time from
 * src/app/sw.ts). updateViaCache: "none" forces the browser to revalidate
 * sw.js itself so a new deploy's worker is picked up (the stale-cache trap,
 * feasibility doc §2 risk 2 — server headers on /sw.js guarantee the same).
 *
 * Production only: in dev there is no built sw.js and HMR would fight a
 * worker; next dev users get no offline behavior, which is fine.
 */
export function ServiceWorkerRegister() {
  useEffect(() => {
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      void navigator.serviceWorker
        .register("/sw.js", { updateViaCache: "none" })
        .catch(() => {
          // A blocked/failed SW must never make the interactive app fail.
        });
    }
  }, []);
  return null;
}
