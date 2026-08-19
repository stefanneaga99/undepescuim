'use client';

import Link from 'next/link';
import { CheckCircle2, ExternalLink, Flag, MapPin, Phone, Ruler, ScrollText, ShieldCheck, Ticket } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useI18n } from '@/i18n/provider';
import { NATIONAL_PERMIT_URL } from '@/lib/permit';
import { safeEmail, safeExternalUrl, safeTelephone } from '@/lib/safe-url';
import type { Association, PermitIssuer, ReportReason, Water } from '@/types/data';

interface WaterDetailCardProps {
  water: Water;
  association: Association | null;
  /** Opens the report dialog with an optional pre-selected reason (F3). */
  onReport?: (reason: ReportReason | null) => void;
  /** Hide the inline report buttons (mobile uses the fixed bottom action bar). */
  compact?: boolean;
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
export function WaterDetailCard({ water, association, onReport, compact = false }: WaterDetailCardProps) {
  const { t } = useI18n();
  const isLake = water.subtype === 'lac';
  const isUncontracted = water.uncontracted === true;
  const telefon = association?.telefon ?? water.asociatie?.telefon;
  const adresa = association?.adresa ?? water.asociatie?.adresa;
  const siteUrl = safeExternalUrl(association?.siteUrl ?? water.asociatie?.siteUrl);
  // F1a: permit info — association record first, water's embedded block as fallback.
  const permitUrl = safeExternalUrl(association?.permitUrl ?? water.asociatie?.permitUrl);
  const permitIssuer: PermitIssuer | undefined =
    association?.permitIssuer ?? water.asociatie?.permitIssuer;

  return (
    <div data-testid="water-card" className="flex flex-col gap-3">
      {/* Header: name + badges */}
      <div className="flex flex-wrap items-center gap-1.5 pr-8">
        <h2 className="mr-auto text-base font-bold leading-tight">{water.name}</h2>
        <Badge
          variant="secondary"
          className={cn(
            'text-[10px] uppercase tracking-wide',
            isLake
              ? 'bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300'
              : 'bg-teal-100 text-teal-700 dark:bg-teal-950/60 dark:text-teal-300',
          )}
        >
          {isLake ? t('card.lake') : t('card.river')}
        </Badge>
        <Badge variant="outline" className="text-[10px] uppercase tracking-wide">
          {water.judet}
        </Badge>
        {isUncontracted && (
          <Badge variant="outline" className="bg-slate-100 text-[10px] uppercase tracking-wide text-slate-600 dark:bg-slate-800 dark:text-slate-300">
            {isLake ? t('card.privateUncontracted') : t('card.uncontracted')}
          </Badge>
        )}
        {water.pescuit_interzis && (
          <Badge variant="destructive" className="text-[10px] uppercase tracking-wide">
            {t('card.fishingBanned')}
          </Badge>
        )}
      </div>

      {/* Uncontracted notice (t_471dad64): no permit on this site covers it */}
      {isUncontracted && (
        <div className="rounded-md border border-teal-200 bg-teal-50 px-3 py-2.5 text-sm text-teal-900 dark:border-teal-900 dark:bg-teal-950/40 dark:text-teal-100">
          <p className="font-medium">{t('card.uncontractedTitle')}</p>
          <p className="mt-0.5 text-xs leading-relaxed opacity-90">
            {t('card.uncontractedBody')}
          </p>
          <Link
            href="/permis"
            className="mt-1 inline-flex items-center gap-1 text-xs font-semibold text-teal-800 underline-offset-2 hover:underline dark:text-teal-200"
          >
            {t('card.seePermitGuide')}
          </Link>
        </div>
      )}

      {/* Sector + size */}
      <dl className="flex flex-col gap-2 text-sm">
        {water.limite && (
          <div className="flex items-start gap-2">
            <Ruler className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <div>
              <dt className="text-xs font-medium text-muted-foreground">{t('card.sector')}</dt>
              <dd>{water.limite}</dd>
            </div>
          </div>
        )}
        {water.dimensiune && (
          <div className="flex items-start gap-2">
            <span className="mt-0.5 inline-block h-3.5 w-3.5 shrink-0 rounded-sm bg-primary/20" />
            <div>
              <dt className="text-xs font-medium text-muted-foreground">{t('card.size')}</dt>
              <dd>{water.dimensiune}</dd>
            </div>
          </div>
        )}
      </dl>

      {/* Association (the resolved one for this clicked sector) */}
      {!isUncontracted && (
        <div className="border-t pt-3">
          <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t('card.association')}
          </h3>
          {association ? (
            <div className="flex flex-col gap-1.5 text-sm">
              <p className="font-medium">{association.name}</p>
              {safeTelephone(telefon) && (
                <a
                  href={safeTelephone(telefon)!}
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
              {association.locations && association.locations.length > 0 && (
                <div className="mt-1 border-t pt-2" data-testid="water-card-association-locations">
                  <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Locații și contacte publice
                  </h4>
                  <div className="flex flex-col gap-2">
                    {association.locations.map((location) => {
                      const phone = location.contacts?.find((contact) => contact.kind === 'phone')?.value;
                      const email = location.contacts?.find((contact) => contact.kind === 'email')?.value;
                      const url = location.contacts?.find((contact) => contact.kind === 'url')?.value;
                      const source = location.sources[0];
                      return (
                        <div key={location.id} className="rounded-md border px-2.5 py-2 text-xs">
                          <p className="font-medium">{location.label ?? location.type}</p>
                          <p className="text-muted-foreground">{location.locality}, {location.county}</p>
                          <p className="flex items-start gap-1.5 text-muted-foreground">
                            <MapPin className="mt-0.5 h-3 w-3 shrink-0" />
                            {location.address}
                          </p>
                          {safeTelephone(phone) && <a href={safeTelephone(phone)!} className="flex items-center gap-1.5 text-primary hover:underline"><Phone className="h-3 w-3" />{phone}</a>}
                          {safeEmail(email) && <a href={safeEmail(email)!} className="text-primary hover:underline">{email}</a>}
                          {safeExternalUrl(url) && <a href={safeExternalUrl(url)!} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Site contact</a>}
                          <div className="mt-1 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
                            <span>{location.freshness === 'needs_confirmation' ? 'Necesită reconfirmare' : location.freshness === 'historical' ? 'Istoric' : 'Verificat la sursă'}</span>
                            {safeExternalUrl(source?.url) && <a href={safeExternalUrl(source.url)!} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Sursa oficială</a>}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {/* F1a: permit block — national permit (required on EVERY
                  contracted water) + the association's own permit store when
                  known. The issuer label tells the two regimes apart. */}
              <div className="mt-1 flex flex-col gap-1.5 border-t pt-2 text-sm">
                <a
                  href={NATIONAL_PERMIT_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  data-testid="permit-row"
                  className="flex items-center gap-2 text-primary hover:underline"
                >
                  <ShieldCheck className="h-3.5 w-3.5 shrink-0" />
                  {t('card.nationalPermitLabel')}
                </a>
                {permitUrl ? (
                  <a
                    href={permitUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    data-testid="permit-row"
                    className="flex items-center gap-2 text-primary hover:underline"
                  >
                    <Ticket className="h-3.5 w-3.5 shrink-0" />
                    {permitIssuer === 'anadspa'
                      ? t('card.permitAnadspa')
                      : permitIssuer === 'romsilva'
                        ? t('card.permitRomsilva')
                        : t('card.buyPermitOnline')}
                  </a>
                ) : (
                  <p className="flex items-start gap-2 text-xs text-muted-foreground">
                    <Ticket className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                    {t('card.permitCheckAssociation')}
                  </p>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t('card.noAssociation')}</p>
          )}
          {/* F2a: explicit permit-validity framing for THIS sector — the map
              already resolved the contract, so the association's permit covers
              this water (docs/f2a-permit-validity.md §4 step 7). */}
          {association && (
            <p className="mt-1 border-t pt-2 text-xs text-muted-foreground">
              {t('card.permitValidOnSector', { name: association.name })}
            </p>
          )}
        </div>
      )}

      {/* Legal reference (permit-note stand-in) */}
      {water.referinta && (
        <div className="border-t pt-3">
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t('card.reference')}
          </h3>
          <p className="text-xs leading-relaxed text-muted-foreground">{water.referinta}</p>
        </div>
      )}

      {/* F3 (t_5b1250b3): report entry points — positive-signal quick tap + full form.
          Hidden on compact (mobile) — the fixed bottom action bar (t_d9e8196e)
          replaces them so the report action is never duplicated below/inside the sheet. */}
      {!compact && (
      <div className="mt-1 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => onReport?.('data_correct')}
          data-testid="report-positive"
          className="inline-flex items-center gap-1.5 rounded-md border border-green-600/40 bg-green-50 px-3 py-1.5 text-xs font-medium text-green-800 transition-colors hover:bg-green-100 dark:border-green-500/40 dark:bg-green-950/40 dark:text-green-300 dark:hover:bg-green-950/70"
        >
          <CheckCircle2 className="h-3.5 w-3.5" />
          {t('card.dataCorrect')}
        </button>
        <button
          type="button"
          onClick={() => onReport?.(null)}
          data-testid="report-flag"
          className="inline-flex items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <Flag className="h-3.5 w-3.5" />
          {t('card.reportProblem')}
        </button>
      </div>
      )}
      <div className="mt-1 flex flex-wrap items-center gap-2">
        <Link
          href="/permis"
          className="inline-flex w-fit items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <ScrollText className="h-3.5 w-3.5" />
          {t('card.permisLink')}
        </Link>
        <Link
          href="/specii"
          className="inline-flex w-fit items-center gap-2 rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-accent hover:text-foreground"
        >
          <Ruler className="h-3.5 w-3.5" />
          {t('card.retentionLink')}
        </Link>
      </div>
    </div>
  );
}
