'use client';

import { ExternalLink, Flag, MapPin, Phone, Ruler } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { Association, Water } from '@/types/data';

interface WaterDetailCardProps {
  water: Water;
  association: Association | null;
}

/**
 * Pure presentational card (component_structure_plan.md §3.12).
 * Shows name, subtype + county badges, sector (limite), size (dimensiune),
 * association contact, legal reference. Missing fields simply don't render
 * (no "—"/"N/A" placeholders). "Raportează o problemă" is a placeholder.
 */
export function WaterDetailCard({ water, association }: WaterDetailCardProps) {
  const isLake = water.subtype === 'lac';
  const telefon = association?.telefon ?? water.asociatie?.telefon;
  const adresa = association?.adresa ?? water.asociatie?.adresa;
  const siteUrl = association?.siteUrl ?? water.asociatie?.siteUrl;

  return (
    <div className="flex flex-col gap-3">
      {/* Header: name + badges */}
      <div className="flex flex-wrap items-center gap-1.5 pr-8">
        <h2 className="mr-auto text-base font-bold leading-tight">{water.name}</h2>
        <Badge
          variant="secondary"
          className={cn(
            'text-[10px] uppercase tracking-wide',
            isLake ? 'bg-sky-100 text-sky-700' : 'bg-teal-100 text-teal-700',
          )}
        >
          {isLake ? 'Lac' : 'Râu'}
        </Badge>
        <Badge variant="outline" className="text-[10px] uppercase tracking-wide">
          {water.judet}
        </Badge>
        {water.pescuit_interzis && (
          <Badge variant="destructive" className="text-[10px] uppercase tracking-wide">
            Pescuit interzis
          </Badge>
        )}
      </div>

      {/* Sector + size */}
      <dl className="flex flex-col gap-2 text-sm">
        {water.limite && (
          <div className="flex items-start gap-2">
            <Ruler className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <div>
              <dt className="text-xs font-medium text-muted-foreground">Sector</dt>
              <dd>{water.limite}</dd>
            </div>
          </div>
        )}
        {water.dimensiune && (
          <div className="flex items-start gap-2">
            <span className="mt-0.5 inline-block h-3.5 w-3.5 shrink-0 rounded-sm bg-primary/20" />
            <div>
              <dt className="text-xs font-medium text-muted-foreground">Dimensiune</dt>
              <dd>{water.dimensiune}</dd>
            </div>
          </div>
        )}
      </dl>

      {/* Association */}
      <div className="border-t pt-3">
        <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Asociație
        </h3>
        {association ? (
          <div className="flex flex-col gap-1.5 text-sm">
            <p className="font-medium">{association.name}</p>
            {telefon && (
              <a
                href={`tel:${telefon.replace(/\s+/g, '')}`}
                className="flex items-center gap-2 text-primary hover:underline"
              >
                <Phone className="h-3.5 w-3.5 shrink-0" />
                {telefon}
              </a>
            )}
            {adresa && (
              <p className="flex items-start gap-2 text-muted-foreground">
                <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                {adresa}
              </p>
            )}
            {siteUrl && (
              <a
                href={siteUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-primary hover:underline"
              >
                <ExternalLink className="h-3.5 w-3.5 shrink-0" />
                {siteUrl.replace(/^https?:\/\//, '').replace(/\/$/, '')}
              </a>
            )}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Fără asociație</p>
        )}
      </div>

      {/* Legal reference (permit-note stand-in) */}
      {water.referinta && (
        <div className="border-t pt-3">
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Referință
          </h3>
          <p className="text-xs leading-relaxed text-muted-foreground">{water.referinta}</p>
        </div>
      )}

      {/* Report placeholder — out of scope this milestone */}
      <button
        type="button"
        title="În curând"
        className="mt-1 inline-flex w-fit items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground"
      >
        <Flag className="h-3.5 w-3.5" />
        Raportează o problemă
      </button>
    </div>
  );
}
