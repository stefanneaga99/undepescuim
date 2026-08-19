"use client";

import { useSyncExternalStore } from "react";
import { CalendarClock, WifiOff, TriangleAlert } from "lucide-react";
import { useMapStore } from "@/stores/map-store";
import { useI18n } from "@/i18n/provider";

/**
 * F6 PWA light (docs/offline-pwa-feasibility.md §4 + §6):
 * - "Date actualizate" chip — data freshness, from /data/meta.json
 *   (scripts/gen-meta.mjs at build time) via the map store.
 * - Offline banner — visible whenever the browser reports no connectivity,
 *   showing the data date so the user knows what they're looking at.
 *
 * Connectivity is a browser-global, so it's read with useSyncExternalStore
 * (server snapshot = online; no effect/setState cascade).
 * Labels + date formatting are locale-aware (t_920a7b7b).
 */
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
  const dataStale = useMapStore((s) => s.dataStale);
  const { locale, t } = useI18n();
  // Server render = online (no banner in SSR HTML); client subscribes to
  // online/offline so the banner appears the moment connectivity drops.
  const online = useSyncExternalStore(
    subscribeOnline,
    getOnlineSnapshot,
    getOnlineServerSnapshot,
  );

  const dateLabel = dataUpdatedAt
    ? new Intl.DateTimeFormat(locale === "en" ? "en-GB" : "ro-RO", {
        day: "numeric",
        month: "short",
        year: "numeric",
      }).format(new Date(dataUpdatedAt))
    : null;

  return (
    <>
      {dateLabel && (
        <span
          data-testid="last-updated"
          role="status"
          className={`inline-flex shrink-0 items-center gap-1 whitespace-nowrap rounded-md border px-2 py-0.5 text-[11px] font-medium ${dataStale ? 'border-amber-500/50 text-amber-700 dark:text-amber-300' : 'text-muted-foreground'}`}
          title={dataStale ? t("pwa.staleTitle") : t("pwa.lastUpdatedTitle")}
        >
          {dataStale ? <TriangleAlert className="h-3 w-3" /> : <CalendarClock className="h-3 w-3" />}
          <span className="hidden sm:inline">{dataStale ? t("pwa.stale") : t("pwa.lastUpdatedLabel")}</span>
          {!dataStale && dateLabel}
        </span>
      )}
      {!online && (
        <div
          data-testid="offline-banner"
          role="status"
          aria-live="polite"
          className="fixed bottom-3 left-3 z-[1300] flex max-w-[calc(100vw-1.5rem)] items-center gap-2 rounded-lg border border-amber-500/40 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-900 shadow-lg dark:border-amber-400/30 dark:bg-amber-950/90 dark:text-amber-200"
        >
          <WifiOff className="h-4 w-4 shrink-0" />
          <span>
            {t("pwa.offline")}
            {dateLabel ? t("pwa.offlineFrom", { date: dateLabel }) : ""}
          </span>
        </div>
      )}
    </>
  );
}