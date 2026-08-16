'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Drawer } from 'vaul';
import { ExternalLink, MapPin, Phone, X } from 'lucide-react';
import { useMapStore } from '@/stores/map-store';
import { useMediaQuery } from '@/hooks/use-media-query';
import { AssociationValidity } from '@/components/associations/AssociationValidity';
import { SheetGrabber } from '@/components/ui/sheet-grabber';
import { cn } from '@/lib/utils';
import type { Association } from '@/types/data';

/**
 * Association detail sheet (F2a, docs/f2a-permit-validity.md §4 step 5).
 *
 * Shows the permit-validity statement ("Permisul X este valabil pe N ape în
 * județele: ..." + reciprocity note) plus contact info. Mirrors the
 * WaterDetailSheet UX exactly: vaul bottom sheet on mobile/tablet (<1024px,
 * snap points [0.1, 0.35, 0.65]) and a persistent right panel on desktop
 * (≥1024px). Opened from the AssociationChip; one-at-a-time with the water
 * sheet (opening it clears the selected water, selecting a water closes it).
 */
export function AssociationDetailSheet() {
  const slug = useMapStore((s) => s.selectedAssociationSlug);
  const associations = useMapStore((s) => s.associations);
  const open = useMapStore((s) => s.associationSheetOpen);
  const closeAssociationSheet = useMapStore((s) => s.closeAssociationSheet);

  const isCompact = useMediaQuery('(max-width: 1023px)');
  const [snap, setSnap] = useState<number | string | null>(0.35);

  const association = useMemo<Association | null>(
    () => associations.find((a) => a.slug === slug) ?? null,
    [associations, slug],
  );

  // ESC dismiss (works in any sheet state, mobile + desktop).
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeAssociationSheet();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, closeAssociationSheet]);

  // Expose the current snap height to ColorLegend (mobile-layout-spec §8.3).
  const handleSnap = (s: number | string | null) => {
    setSnap(s);
    const vh = typeof s === 'number' ? Math.round(s * 100) : 0;
    document.documentElement.style.setProperty('--sheet-snap-h', `${vh}vh`);
  };

  // Fresh open → Peek (35vh); keep current height when switching associations.
  const prevSlug = useRef<string | null>(null);
  useEffect(() => {
    const s = slug ?? null;
    if (s && prevSlug.current === null) handleSnap(0.35);
    prevSlug.current = s;
  }, [slug]);

  // Sync the CSS var on open / snap change / close.
  useEffect(() => {
    const vh = open ? (typeof snap === 'number' ? Math.round(snap * 100) : 35) : 0;
    document.documentElement.style.setProperty('--sheet-snap-h', `${vh}vh`);
  }, [open, snap]);

  const backdropOpacity = snap === 0.1 ? 0 : snap === 0.35 ? 0.2 : 0.5;
  const backdropIntercepts = snap === 0.65;

  return (
    <>
      {/* ── Bottom sheet (mobile + tablet, <1024px) ───────────────────── */}
      {isCompact && (
        <Drawer.Root
          open={open}
          onOpenChange={(o) => {
            if (!o) closeAssociationSheet();
          }}
          snapPoints={[0.1, 0.35, 0.65]}
          activeSnapPoint={snap}
          setActiveSnapPoint={handleSnap}
          modal={false}
          noBodyStyles
        >
          <Drawer.Portal>
            {open && (
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
              aria-label={association ? `Detalii: ${association.name}` : 'Detalii asociație'}
              data-testid="assoc-detail-sheet"
              className="fixed inset-x-0 bottom-0 z-[1200] flex h-[100dvh] flex-col rounded-t-2xl border-t bg-background shadow-xl outline-none"
            >
              {/* drag handle */}
              <SheetGrabber />

              {association && (
                <div className="absolute right-3 top-12">
                  <button
                    type="button"
                    onClick={closeAssociationSheet}
                    className="map-touch flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-accent"
                    aria-label="Închide"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}

              {association && (
                <div
                  key={association.slug}
                  className="h-[calc(65dvh-44px)] shrink-0 overflow-y-auto px-4 pb-[calc(env(safe-area-inset-bottom)+16px)] animate-in fade-in-0 duration-200"
                >
                  <AssociationDetailContent association={association} />
                </div>
              )}
            </Drawer.Content>
          </Drawer.Portal>
        </Drawer.Root>
      )}

      {/* ── Desktop (≥1024px): right side panel ──────────────────────── */}
      {!isCompact && open && association && (
        <aside
          data-testid="assoc-detail-sheet"
          className="flex h-full w-[380px] shrink-0 flex-col border-l bg-background"
        >
          <div className="flex h-12 shrink-0 items-center justify-between border-b px-4">
            <h2 className="text-sm font-semibold">Detalii asociație</h2>
            <button
              type="button"
              onClick={closeAssociationSheet}
              className="map-touch flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-accent"
              aria-label="Închide"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            <AssociationDetailContent association={association} />
          </div>
        </aside>
      )}
    </>
  );
}

/** Shared content for both the drawer and the desktop panel. */
function AssociationDetailContent({ association }: { association: Association }) {
  return (
    <div className="flex flex-col gap-3">
      <div>
        <h2 className="text-base font-bold leading-tight">{association.name}</h2>
        {association.name_long && association.name_long !== association.name && (
          <p className="mt-0.5 text-sm text-muted-foreground">{association.name_long}</p>
        )}
      </div>

      <AssociationValidity association={association} />

      {(association.telefon || association.adresa || association.siteUrl) && (
        <div className="border-t pt-3">
          <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Contact
          </h3>
          <div className="flex flex-col gap-1.5 text-sm">
            {association.telefon && (
              <a
                href={`tel:${association.telefon.replace(/\s+/g, '')}`}
                className="flex items-center gap-2 text-primary hover:underline"
              >
                <Phone className="h-3.5 w-3.5 shrink-0" />
                {association.telefon}
              </a>
            )}
            {association.adresa && (
              <p className="flex items-start gap-2 text-muted-foreground">
                <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {association.adresa}
              </p>
            )}
            {association.siteUrl && (
              <a
                href={association.siteUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-primary hover:underline"
              >
                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                {association.siteUrl.replace(/^https?:\/\//, '').replace(/\/$/, '')}
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
