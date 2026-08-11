'use client';

import { ExternalLink, Flag, MapPin, Phone, Ruler, Layers } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { Association, Water } from '@/types/data';

interface WaterDetailCardProps {
  water: Water;
  association: Association | null;
  /** All waters sharing the same river (multiple contracts per river). */
  relatedWaters?: Water[];
}

/**
 * Normalize a water name to a group key: the first significant word,
 * diacritic-free. "Râul Buzău", "Râul Buzăul superior", "Pârâu Buzăul Mijlociu",
 * "Valea Buzăului inferior" all → "buzau(lui)" — grouped by 5-char prefix.
 */
function waterKey(name: string): string {
  const lower = name.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  return lower
    .replace(/^(raul|paraul|parau|valea|lacul|balta|acumularea|acumulare)\s+/, '')
    .replace(/[()]/g, '')
    .trim()
    .split(/\s+/)[0] ?? '';
}

/** True when two water keys name the same river (shared 5-char prefix). */
function sameRiver(a: string, b: string): boolean {
  if (!a || !b) return false;
  return a.slice(0, 5) === b.slice(0, 5);
}

/**
 * Pure presentational card (component_structure_plan.md §3.12).
 * Shows name, subtype + county badges, sector (limite), size (dimensiune),
 * association contact, legal reference. Missing fields simply don't render
 * (no "—"/"N/A" placeholders). "Raportează o problemă" is a placeholder.
 */
export function WaterDetailCard({
  water,
  association,
  relatedWaters = [],
}: WaterDetailCardProps) {
  const isLake = water.subtype === 'lac';
  const telefon = association?.telefon ?? water.asociatie?.telefon;
  const adresa = association?.adresa ?? water.asociatie?.adresa;
  const siteUrl = association?.siteUrl ?? water.asociatie?.siteUrl;

  // Group contracts for the same river: this water + all others sharing its key
  const key = waterKey(water.name);
  const contracts = relatedWaters.filter(
    (w) => sameRiver(key, waterKey(w.name)) && w.slug !== water.slug,
  );
  const showContracts = contracts.length > 0;

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

      {/* Multiple contracts on the same river — show all sectors */}
      {showContracts && (
        <div className="border-t pt-3">
          <h3 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            <Layers className="h-3.5 w-3.5" />
            {contracts.length} sectoare contractate
          </h3>
          <ul className="flex flex-col gap-2">
            {contracts.map((c) => (
              <li
                key={c.slug}
                className={cn(
                  'rounded-md border px-3 py-2 text-xs',
                  c.slug === water.slug
                    ? 'border-primary/40 bg-primary/5'
                    : 'border-border',
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium">{c.asociatie?.name ?? '—'}</span>
                  <Badge variant="outline" className="text-[10px] uppercase tracking-wide">
                    {c.judet}
                  </Badge>
                </div>
                {c.limite && <p className="mt-1 text-muted-foreground">{c.limite}</p>}
                {c.dimensiune && (
                  <p className="mt-0.5 text-muted-foreground">{c.dimensiune}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

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
