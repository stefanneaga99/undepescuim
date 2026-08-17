"use client";

import { useEffect, useState } from "react";
import { CalendarClock, WifiOff } from "lucide-react";
import { useMapStore } from "@/stores/map-store";

/**
 * F6 PWA light (docs/offline-pwa-feasibility.md §4 + §6):
 * - "Date actualizate" chip — data freshness, from /data/meta.json
 *   (scripts/gen-meta.mjs at build time) via the map store.
 * - Offline banner — visible whenever the browser reports no connectivity,
 *   showing the data date so the user knows what they're looking at.
 *
 * Detection: `navigator.onLine` + online/offline events. The chip is hidden
 * on the smallest screens (header is dense there); the offline pill renders on
 * every viewport.
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

export function PwaStatusBar() {
  const dataUpdatedAt = useMapStore((s) => s.dataUpdatedAt);
  const [online, setOnline] = useState(true);

  useEffect(() => {
    // SSR-safe initial read; the event listeners keep it live afterwards.
    setOnline(typeof navigator === "undefined" ? true : navigator.onLine);
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

  const dateLabel = dataUpdatedAt ? formatDate(dataUpdatedAt) : null;

  return (
    <>
      {dateLabel && (
        <span
          data-testid="last-updated"
          className="hidden shrink-0 items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-medium text-muted-foreground sm:inline-flex"
          title="Ultima actualizare a datelor de pescuit"
        >
          <CalendarClock className="h-3 w-3" />
          Date actualizate: {dateLabel}
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
