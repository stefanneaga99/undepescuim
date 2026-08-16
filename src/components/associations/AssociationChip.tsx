'use client';

import { Building2, ChevronRight } from 'lucide-react';
import { useMapStore } from '@/stores/map-store';

/**
 * Persistent association chip (F2a, docs/f2a-permit-validity.md §4 step 5-6).
 *
 * Rendered on the map (top-center, below the FilterBar) whenever an
 * association is selected. Shows the association name + water count; tapping
 * opens the association detail sheet (the validity statement). Pure derived
 * view of the store — selection/clear flows through store.selectAssociation,
 * no store change needed for the chip itself.
 */
export function AssociationChip() {
  const slug = useMapStore((s) => s.selectedAssociationSlug);
  const associations = useMapStore((s) => s.associations);
  const openAssociationSheet = useMapStore((s) => s.openAssociationSheet);

  if (!slug) return null;
  const association = associations.find((a) => a.slug === slug);
  if (!association) return null;

  return (
    <div className="pointer-events-none absolute inset-x-0 top-3 z-[900] flex justify-center px-3">
      <button
        type="button"
        onClick={openAssociationSheet}
        className="map-touch pointer-events-auto flex max-w-full items-center gap-2 rounded-full border bg-background/95 py-1.5 pl-2 pr-2.5 text-sm shadow-md backdrop-blur transition-colors hover:bg-accent"
        aria-label={`Detalii ${association.name}`}
        data-testid="assoc-chip"
      >
        <Building2 className="h-4 w-4 shrink-0 text-primary" />
        <span className="truncate font-medium">{association.name}</span>
        <span className="shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-[10px] font-medium tabular-nums text-muted-foreground">
          {association.ape ?? 0}
        </span>
        <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
      </button>
    </div>
  );
}
