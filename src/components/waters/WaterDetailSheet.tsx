'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Drawer } from 'vaul';
import { CheckCircle2, Flag, X } from 'lucide-react';
import { useMapStore } from '@/stores/map-store';
import { useMediaQuery } from '@/hooks/use-media-query';
import { useI18n } from '@/i18n/provider';
import { WaterDetailCard } from '@/components/waters/WaterDetailCard';
import { SheetGrabber } from '@/components/ui/sheet-grabber';
import { ReportForm } from '@/components/verification/ReportForm';
import { cn } from '@/lib/utils';
import type { Association, ReportReason } from '@/types/data';

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
  const waterSheetOpen = useMapStore((s) => s.waterSheetOpen);
  const waters = useMapStore((s) => s.waters);
  const uncontracted = useMapStore((s) => s.uncontracted);
  const associations = useMapStore((s) => s.associations);
  const closeWaterSheet = useMapStore((s) => s.closeWaterSheet);
  const { t } = useI18n();

  const isCompact = useMediaQuery('(max-width: 1023px)');
  const [snap, setSnap] = useState<number | string | null>(0.35);

  // F3 (t_5b1250b3): report dialog lives HERE (shared by the inline card
  // buttons and the mobile fixed bottom action bar) so the report action is
  // always reachable regardless of sheet snap/scoll (t_d9e8196e).
  const [report, setReport] = useState<{ open: boolean; reason: ReportReason | null }>({
    open: false,
    reason: null,
  });
  const openReport = (reason: ReportReason | null) => setReport({ open: true, reason });

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

  // ESC dismiss (works in any sheet state, mobile + desktop). t_21d2f68d:
  // closing the sheet must NOT clear the selection — the orange click focus
  // stays on the map (the reported bug: closing the card before using the
  // filters wiped every highlight).
  useEffect(() => {
    if (!water) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeWaterSheet();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [water, closeWaterSheet]);

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

  // Sync the CSS var on open / snap change / close. t_21d2f68d: the sheet can
  // now close while `water` stays selected (orange focus persists), so the var
  // resets on `waterSheetOpen` — not on the selection — or the legend/locate
  // button would keep floating at the sheet's last height.
  useEffect(() => {
    const vh = water && waterSheetOpen ? (typeof snap === 'number' ? Math.round(snap * 100) : 35) : 0;
    document.documentElement.style.setProperty('--sheet-snap-h', `${vh}vh`);
  }, [water, waterSheetOpen, snap]);

  const backdropOpacity = snap === 0.1 ? 0 : snap === 0.35 ? 0.2 : 0.5;
  const backdropIntercepts = snap === 0.65;

  return (
    <>
      {/* ── Bottom sheet (mobile + tablet, <1024px) ───────────────────── */}
      {isCompact && (
        <Drawer.Root
          open={waterSheetOpen && !!water}
          onOpenChange={(open) => {
            if (!open) closeWaterSheet();
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
                    onClick={closeWaterSheet}
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
                  className="h-[calc(65dvh-44px)] shrink-0 overflow-y-auto px-4 pb-[calc(env(safe-area-inset-bottom)+72px)] animate-in fade-in-0 duration-200"
                >
                  <WaterDetailCard
                    water={water}
                    association={association}
                    onReport={openReport}
                    compact={isCompact}
                  />
                </div>
              )}
            </Drawer.Content>

            {/* t_d9e8196e: fixed bottom action bar — a SIBLING of
                Drawer.Content, because vaul TRANSLATES Drawer.Content down at
                low snaps (a transformed ancestor would capture `fixed`/`absolute`
                descendants and push them off-screen). Rendered inside the portal
                (→ body, untransformed) so `fixed bottom-0` anchors to the real
                viewport: the report entry is always in view, for any snap/scroll.
                Hidden while the report dialog is open (z-[1250] would otherwise
                float above the z-50 dialog overlay). */}
            {water && !report.open && (
              <div className="pointer-events-auto fixed inset-x-0 bottom-0 z-[1250] border-t bg-background px-4 pt-2 pb-[max(env(safe-area-inset-bottom),0.625rem)] shadow-[0_-4px_12px_rgba(0,0,0,0.08)]">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => openReport('data_correct')}
                    data-testid="report-positive-fixed"
                    className="inline-flex items-center gap-1.5 rounded-md border border-green-600/40 bg-green-50 px-3 py-1.5 text-xs font-medium text-green-800 transition-colors hover:bg-green-100 dark:border-green-500/40 dark:bg-green-950/40 dark:text-green-300 dark:hover:bg-green-950/70"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    {t('card.dataCorrect')}
                  </button>
                  <button
                    type="button"
                    onClick={() => openReport(null)}
                    data-testid="report-flag-fixed"
                    className="inline-flex items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                  >
                    <Flag className="h-3.5 w-3.5" />
                    {t('card.reportProblem')}
                  </button>
                </div>
              </div>
            )}
          </Drawer.Portal>
        </Drawer.Root>
      )}

      {/* ── Desktop (≥1024px): right side panel ──────────────────────── */}
      {!isCompact && water && waterSheetOpen && (
        <aside className="flex h-full w-[380px] shrink-0 flex-col border-l bg-background">
          <div className="flex h-12 shrink-0 items-center justify-between border-b px-4">
            <h2 className="text-sm font-semibold">{t('detailSheet.detailsWater')}</h2>
            <button
              type="button"
              onClick={closeWaterSheet}
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
              onReport={openReport}
            />
          </div>
        </aside>
      )}

      {/* F3: the report dialog — owned here so both the inline card buttons
          and the mobile fixed bottom action bar share one dialog (t_d9e8196e). */}
      <ReportForm
        open={report.open}
        onOpenChange={(o) => setReport((r) => ({ ...r, open: o }))}
        waterSlug={water?.slug}
        waterName={water?.name}
        initialReason={report.reason}
      />
    </>
  );
}
