'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Drawer } from 'vaul';
import { X } from 'lucide-react';
import { useMapStore } from '@/stores/map-store';
import { useMediaQuery } from '@/hooks/use-media-query';
import { useI18n } from '@/i18n/provider';
import { WaterDetailCard } from '@/components/waters/WaterDetailCard';
import { SheetGrabber } from '@/components/ui/sheet-grabber';
import { cn } from '@/lib/utils';
import type { Association } from '@/types/data';

/**
 * Water detail UI (component_structure_plan.md §3.11 + mobile-layout-spec §3,
 * as amended by user decisions in t_aace2685 comment #64).
 *
 * - <1024px (mobile + tablet): vaul bottom sheet, snap points [0.1, 0.35, 0.65]
 *   vh (Collapsed / Peek / Expanded). Backdrop: 0 / 0.20 / 0.50 opacity.
 *   Backdrop tap is a no-op at Peek (map stays tappable above the sheet),
 *   collapses to Peek at Expanded. Dismiss: drag past threshold from
 *   Collapsed, ×, ESC (R4).
 * - Desktop (≥1024px): persistent right panel, 380px.
 */
export function WaterDetailSheet() {
  const selectedWaterSlug = useMapStore((s) => s.selectedWaterSlug);
  const waters = useMapStore((s) => s.waters);
  const uncontracted = useMapStore((s) => s.uncontracted);
  const associations = useMapStore((s) => s.associations);
  const selectWater = useMapStore((s) => s.selectWater);
  const { t } = useI18n();

  const isCompact = useMediaQuery('(max-width: 1023px)');
  const [snap, setSnap] = useState<number | string | null>(0.35);

  // Contracted waters first, then uncontracted OSM rivers (t_471dad64).
  const water =
    waters.find((w) => w.slug === selectedWaterSlug) ??
    uncontracted.find((w) => w.slug === selectedWaterSlug) ??
    null;

  // Card association: prefer the canonical 82-association record; fall back to
  // the water's embedded asociatie object (same shape for the fields we need).
  const association = useMemo<Association | null>(() => {
    if (!water?.asociatie) return null;
    const found = associations.find((a) => a.slug === water.asociatie?.slug);
    if (found) return found;
    return {
      slug: water.asociatie.slug,
      name: water.asociatie.name,
      name_long: water.asociatie.name_long ?? water.asociatie.name,
      ape: 0,
      id: water.asociatie.slug,
      bbox: water.bbox,
      telefon: water.asociatie.telefon,
      adresa: water.asociatie.adresa,
      siteUrl: water.asociatie.siteUrl,
      // F1a: copy permit info so the card renders the permit rows even for
      // waters whose association is not in the 94-record directory.
      permitUrl: water.asociatie.permitUrl,
      permitIssuer: water.asociatie.permitIssuer,
      permitType: water.asociatie.permitType,
    };
  }, [water, associations]);

  // ESC dismiss (works in any sheet state, mobile + desktop).
  useEffect(() => {
    if (!water) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') selectWater(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [water, selectWater]);

  // Expose the current snap height to ColorLegend (mobile-layout-spec §8.3).
  const handleSnap = (s: number | string | null) => {
    setSnap(s);
    const vh = typeof s === 'number' ? Math.round(s * 100) : 0;
    document.documentElement.style.setProperty('--sheet-snap-h', `${vh}vh`);
  };

  // Fresh open → Peek (35vh); keep current height when switching waters.
  const prevWaterSlug = useRef<string | null>(null);
  useEffect(() => {
    const slug = water?.slug ?? null;
    if (slug && prevWaterSlug.current === null) handleSnap(0.35);
    prevWaterSlug.current = slug;
  }, [water?.slug]);

  // Sync the CSS var on open / snap change / close.
  useEffect(() => {
    const vh = water ? (typeof snap === 'number' ? Math.round(snap * 100) : 35) : 0;
    document.documentElement.style.setProperty('--sheet-snap-h', `${vh}vh`);
  }, [water, snap]);

  const backdropOpacity = snap === 0.1 ? 0 : snap === 0.35 ? 0.2 : 0.5;
  const backdropIntercepts = snap === 0.65;

  return (
    <>
      {/* ── Bottom sheet (mobile + tablet, <1024px) ───────────────────── */}
      {isCompact && (
        <Drawer.Root
          open={!!water}
          onOpenChange={(open) => {
            if (!open) selectWater(null);
          }}
          snapPoints={[0.1, 0.35, 0.65]}
          activeSnapPoint={snap}
          setActiveSnapPoint={handleSnap}
          modal={false}
          noBodyStyles
        >
          <Drawer.Portal>
            {water && (
              <div
                className={cn(
                  'fixed inset-0 z-[1100] bg-black transition-opacity duration-200',
                  backdropIntercepts ? 'cursor-pointer' : 'pointer-events-none',
                )}
                style={{ opacity: backdropOpacity }}
                onClick={() => backdropIntercepts && setSnap(0.35)}
                aria-hidden
              />
            )}
            <Drawer.Content
              aria-label={water ? t('detailSheet.detailsAria', { name: water.name }) : t('detailSheet.detailsWater')}
              className="fixed inset-x-0 bottom-0 z-[1200] flex h-[100dvh] flex-col rounded-t-2xl border-t bg-background shadow-xl outline-none"
            >
              {/* drag handle */}
              <SheetGrabber />

              {water && (
                <div className="absolute right-3 top-12">
                  <button
                    type="button"
                    onClick={() => selectWater(null)}
                    className="map-touch flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-accent"
                    aria-label={t('detailSheet.close')}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}

              {water && (
                <div
                  key={water.slug}
                  className="h-[calc(65dvh-44px)] shrink-0 overflow-y-auto px-4 pb-[calc(env(safe-area-inset-bottom)+16px)] animate-in fade-in-0 duration-200"
                >
                  <WaterDetailCard
                    water={water}
                    association={association}
                  />
                </div>
              )}
            </Drawer.Content>
          </Drawer.Portal>
        </Drawer.Root>
      )}

      {/* ── Desktop (≥1024px): right side panel ──────────────────────── */}
      {!isCompact && water && (
        <aside className="flex h-full w-[380px] shrink-0 flex-col border-l bg-background">
          <div className="flex h-12 shrink-0 items-center justify-between border-b px-4">
            <h2 className="text-sm font-semibold">{t('detailSheet.detailsWater')}</h2>
            <button
              type="button"
              onClick={() => selectWater(null)}
              className="map-touch flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-accent"
              aria-label={t('detailSheet.close')}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            <WaterDetailCard
              water={water}
              association={association}
            />
          </div>
        </aside>
      )}
    </>
  );
}
