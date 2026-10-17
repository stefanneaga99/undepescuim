'use client';

/**
 * Explicit attribution kept above Leaflet's attribution control so it remains
 * legible on small screens and while the map is loading or filtered.
 */
export function MapAttribution() {
  return (
    <div
      className="pointer-events-auto absolute bottom-1 left-1 z-[1000] rounded bg-white/90 px-1.5 py-0.5 text-[11px] leading-4 text-neutral-800 shadow-sm dark:bg-neutral-900/90 dark:text-neutral-100"
      data-testid="map-attribution"
    >
      <span>© OpenStreetMap contributors — </span>
      <a
        className="underline underline-offset-2"
        href="https://www.openstreetmap.org/copyright"
        target="_blank"
        rel="noreferrer"
      >
        OpenStreetMap copyright
      </a>
      {/* River geometry v2: some pre-cut sectors use the ANAR cadastral network (CC BY 4.0). */}
      <span> · </span>
      <a
        className="underline underline-offset-2"
        href="https://data.gov.ro/dataset/hidrografie"
        target="_blank"
        rel="noreferrer"
      >
        Hidrografie © ANAR (CC BY 4.0)
      </a>
    </div>
  );
}
