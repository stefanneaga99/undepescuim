'use client';

import { useMemo } from 'react';
import { Drawer } from 'vaul';
import { ChevronRight, LocateFixed, X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { SheetGrabber } from '@/components/ui/sheet-grabber';
import { useMapStore } from '@/stores/map-store';
import { useMediaQuery } from '@/hooks/use-media-query';
import { cn } from '@/lib/utils';
import type { PermitIssuer } from '@/types/data';

/**
 * "Nearby waters" list — geolocation MVP (docs/geolocation-feasibility.md
 * §7.1 `NearbyWatersSheet`, AC3/5/7).
 *
 * Shows the N nearest CONTRACTED waters within the adaptive radius (the
 * association/permit data lives on the contracted pool; uncontracted OSM
 * rivers are explicitly out of scope per feasibility §4). Each row: name,
 * distance (km, 1 decimal), county, association name, permit-issuer badge.
 * Tapping a row calls the existing selectWater(slug) → the existing
 * WaterDetailCard opens (mobile vaul drawer / desktop side panel) — no new
 * detail UI.
 *
 * Honest framing (AC7): the position is live, the coverage data is ANNUAL —
 * the header carries the "date 2026" label and never implies live
 * availability.
 *
 * Layout: mobile/tablet <1024px = non-modal vaul bottom sheet (z-[1050],
 * BELOW the water card drawer z-[1200] + its backdrop z-[1100] so the detail
 * card takes over cleanly, and the sheet stays when the card closes);
 * desktop ≥1024px = floating panel above the map's bottom-left (clear of the
 * top-left filter panel and the bottom-right legend).
 */

function issuerBadge(issuer: PermitIssuer | undefined) {
  if (issuer === 'anadspa') {
    return (
      <Badge variant="secondary" className="bg-blue-100 text-[10px] uppercase tracking-wide text-blue-700">
        ANADSPA
      </Badge>
    );
  }
  if (issuer === 'romsilva') {
    return (
      <Badge variant="secondary" className="bg-emerald-100 text-[10px] uppercase tracking-wide text-emerald-700">
        Romsilva
      </Badge>
    );
  }
  return (
    <Badge variant="secondary" className="bg-amber-100 text-[10px] uppercase tracking-wide text-amber-700">
      Asociație
    </Badge>
  );
}

export function NearbyWatersSheet() {
  const userPosition = useMapStore((s) => s.userPosition);
  const nearbyWaters = useMapStore((s) => s.nearbyWaters);
  const nearbyRadiusKm = useMapStore((s) => s.nearbyRadiusKm);
  const waters = useMapStore((s) => s.waters);
  const selectWater = useMapStore((s) => s.selectWater);
  const clearUserPosition = useMapStore((s) => s.clearUserPosition);

  const isCompact = useMediaQuery('(max-width: 1023px)');
  const open = userPosition !== null && nearbyWaters.length > 0;

  // Join slugs → full water records (all contracted, so asociatie exists).
  const rows = useMemo(
    () =>
      nearbyWaters
        .map((n) => ({ n, water: waters.find((w) => w.slug === n.slug) }))
        .filter((r): r is { n: (typeof nearbyWaters)[number]; water: NonNullable<(typeof waters)[number]> } => !!r.water),
    [nearbyWaters, waters],
  );

  const header = (
    <div className="flex items-center justify-between gap-2">
      <h2 className="text-sm font-semibold">Ape în apropiere</h2>
      <button
        type="button"
        onClick={clearUserPosition}
        className="map-touch flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-accent"
        aria-label="Închide lista"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );

  const freshness = (
    <p className="flex items-center gap-1.5 text-[11px] leading-snug text-muted-foreground">
      <LocateFixed className="h-3 w-3 shrink-0" />
      Poziția ta este live; datele despre ape sunt anuale (date 2026).
      {nearbyRadiusKm > 0 && ` Rază: ${nearbyRadiusKm} km.`}
    </p>
  );

  const list = (
    <ul className="flex flex-col gap-1.5">
      {rows.map(({ n, water }) => (
        <li key={n.slug}>
          <button
            type="button"
            onClick={() => selectWater(n.slug)}
            className="flex w-full items-center gap-2 rounded-lg border bg-card p-2.5 text-left transition-colors hover:bg-accent"
          >
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1.5">
                <span className="truncate text-sm font-medium">{water.name}</span>
                {issuerBadge(water.asociatie?.permitIssuer)}
              </div>
              <p className="mt-0.5 truncate text-xs text-muted-foreground">
                {water.judet} · {water.asociatie?.name ?? 'Fără asociație'}
              </p>
            </div>
            <span className="shrink-0 rounded-md bg-muted px-1.5 py-0.5 text-xs font-medium tabular-nums text-muted-foreground">
              {n.km < 1 ? `${Math.round(n.km * 1000)} m` : `${n.km.toFixed(1)} km`}
            </span>
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          </button>
        </li>
      ))}
    </ul>
  );

  if (!open) return null;

  // ── Mobile / tablet (<1024px): non-modal vaul bottom sheet ────────────
  if (isCompact) {
    return (
      <Drawer.Root
        open={open}
        onOpenChange={(o) => {
          if (!o) clearUserPosition();
        }}
        snapPoints={[0.15, 0.45, 0.85]}
        modal={false}
        noBodyStyles
      >
        <Drawer.Portal>
          <Drawer.Content
            aria-label="Ape în apropiere"
            data-nearby-sheet=""
            className="fixed inset-x-0 bottom-0 z-[1050] flex h-[100dvh] flex-col rounded-t-2xl border-t bg-background shadow-xl outline-none"
          >
            <SheetGrabber />
            <div className="flex flex-col gap-1.5 px-4 pb-2">
              {header}
              {freshness}
            </div>
            <div className="min-h-0 max-h-[calc(85dvh-44px-64px)] flex-1 overflow-y-auto px-4 pb-[calc(env(safe-area-inset-bottom)+16px)]">
              {list}
            </div>
          </Drawer.Content>
        </Drawer.Portal>
      </Drawer.Root>
    );
  }

  // ── Desktop (≥1024px): floating panel over the map ────────────────────
  return (
    <div
      data-nearby-sheet=""
      className="absolute bottom-[calc(var(--sheet-snap-h,0vh)+88px)] left-3 z-[1000] flex w-[360px] max-w-[calc(100vw-24px)] flex-col gap-1.5 rounded-xl border bg-background/95 p-3 shadow-md backdrop-blur"
    >
      {header}
      {freshness}
      <div className="max-h-[45dvh] overflow-y-auto">{list}</div>
      <p className={cn('text-[11px] text-muted-foreground')}>
        Doar apele contractate sunt listate aici — pentru râuri/bălți necontractate folosește filtrul „Necontractate”.
      </p>
    </div>
  );
}
