'use client';

import Link from 'next/link';
import { ExternalLink, Flag, MapPin, Phone, Ruler, ScrollText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { Association, Water } from '@/types/data';

interface WaterDetailCardProps {
  water: Water;
  association: Association | null;
}

/**
 * Pure presentational card (component_structure_plan.md §3.12).
 * Shows the SINGLE resolved contract for the clicked sector: name, subtype +
 * county badges, sector (limite), size (dimensiune), association contact,
 * legal reference. The map click already resolves which contract owns the
 * clicked fraction of the river (contractAtFraction), so only that contract
 * is shown — never the full list of contracts on the river.
 * Missing fields simply don't render (no "—"/"N/A" placeholders).
 * "Raportează o problemă" is a placeholder.
 */
export function WaterDetailCard({ water, association }: WaterDetailCardProps) {
  const isLake = water.subtype === 'lac';
  const isUncontracted = water.uncontracted === true;
  const telefon = association?.telefon ?? water.asociatie?.telefon;
  const adresa = association?.adresa ?? water.asociatie?.adresa;
  const siteUrl = association?.siteUrl ?? water.asociatie?.siteUrl;
  // F1a: permit info — association record first, water's embedded block as fallback.
  const permitUrl = association?.permitUrl ?? water.asociatie?.permitUrl;
  const permitIssuer: PermitIssuer | undefined =
    association?.permitIssuer ?? water.asociatie?.permitIssuer;
  const [reportOpen, setReportOpen] = useState(false);
  const [reportReason, setReportReason] = useState<ReportReason | null>(null);
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
        {isUncontracted && (
          <Badge variant="outline" className="bg-slate-100 text-[10px] uppercase tracking-wide text-slate-600">
            {isLake ? 'Privat / Necontractat' : 'Necontractat'}
          </Badge>
        )}
        {water.pescuit_interzis && (
          <Badge variant="destructive" className="text-[10px] uppercase tracking-wide">
            Pescuit interzis
          </Badge>
        )}
      </div>

      {/* Uncontracted notice (t_471dad64): no permit on this site covers it */}
      {isUncontracted && (
        <div className="rounded-md border border-teal-200 bg-teal-50 px-3 py-2.5 text-sm text-teal-900 dark:border-teal-900 dark:bg-teal-950/40 dark:text-teal-100">
          <p className="font-medium">Apă necontractată</p>
          <p className="mt-0.5 text-xs leading-relaxed opacity-90">
            Pescuitul aici <strong>nu este acoperit</strong> de niciun permis afișat pe acest site.
            Verifică legislația locală înainte de a pescui.
          </p>
          <Link
            href="/permis"
            className="mt-1 inline-flex items-center gap-1 text-xs font-semibold text-teal-800 underline-offset-2 hover:underline dark:text-teal-200"
          >
            Vezi ghidul „Permis &amp; Reguli 2026&rdquo; →
          </Link>
        </div>
      )}

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

      {/* Association (the resolved one for this clicked sector) */}
      {!isUncontracted && (
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
          {/* F2a: explicit permit-validity framing for THIS sector — the map
              already resolved the contract, so the association's permit covers
              this water (docs/f2a-permit-validity.md §4 step 7). */}
          {association && (
            <p className="mt-1 border-t pt-2 text-xs text-muted-foreground">
              Permisul {association.name} este valabil pe acest sector.
            </p>
          )}
        </div>
      )}

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
      <Link
        href="/permis"
        className="mt-1 inline-flex w-fit items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-accent hover:text-foreground"
      >
        <ScrollText className="h-3.5 w-3.5" />
        Permis &amp; Reguli 2026
      </Link>
    </div>
  );
}
