"use client";

import { useSyncExternalStore } from "react";
import { CalendarClock, WifiOff } from "lucide-react";
import { useMapStore } from "@/stores/map-store";

/**
 * F6 PWA light (docs/offline-pwa-feasibility.md §4 + §6):
 * - "Date actualizate" chip — data freshness, from /data/meta.json
 *   (scripts/gen-meta.mjs at build time) via the map store.
 * - Offline banner — visible whenever the browser reports no connectivity,
 *   showing the data date so the user knows what they're looking at.
 *
 * Connectivity is a browser-global, so it's read with useSyncExternalStore
 * (server snapshot = online; no effect/setState cascade).
 */
function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat("ro-RO", {
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(new Date(iso));
  } catch {
    return iso.slice(0, 10);
  }
}

function subscribeOnline(callback: () => void): () => void {
  window.addEventListener("online", callback);
  window.addEventListener("offline", callback);
  return () => {
    window.removeEventListener("online", callback);
    window.removeEventListener("offline", callback);
  };
}

const getOnlineSnapshot = () => navigator.onLine;
const getOnlineServerSnapshot = () => true;

export function PwaStatusBar() {
  const dataUpdatedAt = useMapStore((s) => s.dataUpdatedAt);
  // Server render = online (no banner in SSR HTML); client subscribes to
  // online/offline so the banner appears the moment connectivity drops.
  const online = useSyncExternalStore(
    subscribeOnline,
    getOnlineSnapshot,
    getOnlineServerSnapshot,
  );

  const dateLabel = dataUpdatedAt ? formatDate(dataUpdatedAt) : null;

  return (
    <>
      {dateLabel && (
        <span
          data-testid="last-updated"
          className="inline-flex shrink-0 items-center gap-1 whitespace-nowrap rounded-md border px-2 py-0.5 text-[11px] font-medium text-muted-foreground"
          title="Ultima actualizare a datelor de pescuit"
        >
          <CalendarClock className="h-3 w-3" />
          <span className="hidden sm:inline">Date actualizate: </span>
          {dateLabel}
        </span>
      )}
      {!online && (
        <div
          data-testid="offline-banner"
          role="status"
          className="fixed bottom-3 left-3 z-[1300] flex max-w-[calc(100vw-1.5rem)] items-center gap-2 rounded-lg border border-amber-500/40 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-900 shadow-lg dark:border-amber-400/30 dark:bg-amber-950/90 dark:text-amber-200"
        >
          <WifiOff className="h-4 w-4 shrink-0" />
          <span>
            Fără conexiune
            {dateLabel ? ` — date din ${dateLabel}` : ""}
          </span>
        </div>
      )}
    </>
  );
}
