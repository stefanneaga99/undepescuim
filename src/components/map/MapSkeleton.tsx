'use client';

/** Loading state while /data/*.json is fetched (map-state-data-flow §7.1). */
export function MapSkeleton() {
  return (
    <div className="flex h-full w-full animate-pulse items-center justify-center bg-muted/40">
      <span className="text-sm text-muted-foreground">Se încarcă harta…</span>
    </div>
  );
}
