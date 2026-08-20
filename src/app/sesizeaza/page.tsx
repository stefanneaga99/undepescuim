'use client';

import Link from 'next/link';
import { useState } from 'react';
import { AlertTriangle, ArrowLeft, ExternalLink, Mail, Phone, ShieldAlert, Siren } from 'lucide-react';
import { useI18n } from '@/i18n/provider';
import type { MessageKey } from '@/i18n/messages';
import { INCIDENT_ROUTES, OFFICIAL_CONTACTS, INCIDENT_VERIFIED_AT, type IncidentKind, type IncidentRoute } from '@/content/incident-routing';
import { safeEmail, safeExternalUrl, safeTelephone } from '@/lib/safe-url';

const KIND_KEYS: Record<IncidentKind, { title: MessageKey; body: MessageKey }> = {
  poaching: { title: 'incidentRouting.poachingTitle', body: 'incidentRouting.poachingBody' },
  pollution: { title: 'incidentRouting.pollutionTitle', body: 'incidentRouting.pollutionBody' },
  illegal_gear_or_sale: { title: 'incidentRouting.gearTitle', body: 'incidentRouting.gearBody' },
};

type Translate = (key: MessageKey, params?: Record<string, string | number>) => string;
function Contact({ id, sourceLabel }: { id: string; sourceLabel: string }) {
  const c = OFFICIAL_CONTACTS[id];
  const tel = safeTelephone(c.phone);
  const email = safeEmail(c.email);
  const url = safeExternalUrl(c.url);
  return <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
    <strong>{c.label}</strong>
    {tel && <a className="inline-flex items-center gap-1 text-primary hover:underline" href={tel}><Phone className="h-3.5 w-3.5" />{c.phone}</a>}
    {email && <a className="inline-flex items-center gap-1 text-primary hover:underline" href={email}><Mail className="h-3.5 w-3.5" />{c.email}</a>}
    {url && <a className="inline-flex items-center gap-1 text-primary hover:underline" href={url} target="_blank" rel="noopener noreferrer" data-testid={id === 'gnmDirectory' ? 'incident-gnm-directory' : undefined}><ExternalLink className="h-3.5 w-3.5" />{sourceLabel}</a>}
  </div>;
}

function RouteCard({ route, t }: { route: IncidentRoute; t: Translate }) {
  const keys = KIND_KEYS[route.kind];
  const emergency = route.urgency === 'active_emergency';
  return <section data-testid={emergency ? 'incident-emergency-route' : `incident-route-${route.kind}`} className="rounded-lg border p-4">
    <h2 className="flex items-center gap-2 text-base font-bold"><Siren className="h-4 w-4 text-primary" />{t(keys.title)}</h2>
    <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{t(keys.body)}</p>
    <div className="mt-3 flex flex-col gap-2">{route.contactIds.map((id) => <Contact key={id} id={id} sourceLabel={t('incidentRouting.openOfficialSource')} />)}</div>
    <p className="mt-3 rounded-md bg-muted/50 px-3 py-2 text-xs leading-relaxed">{t('incidentRouting.whatToSay')}</p>
  </section>;
}

export default function SesizeazaPage() {
  const { t } = useI18n();
  const [activeSelected, setActiveSelected] = useState(false);
  const emergency = INCIDENT_ROUTES.find((r) => r.kind === 'poaching' && r.urgency === 'active_emergency')!;
  const nonUrgent = INCIDENT_ROUTES.filter((r) => r.urgency === 'non_urgent');
  return <main className="mx-auto flex w-full max-w-3xl flex-col gap-5 px-4 py-6 md:py-10">
    <Link href="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="h-4 w-4" />{t('incidentRouting.backToMap')}</Link>
    <div>
      <h1 className="text-2xl font-bold tracking-tight md:text-3xl">{t('incidentRouting.title')}</h1>
      <p className="mt-2 text-sm leading-relaxed">{t('incidentRouting.intro')}</p>
    </div>
    <div className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
      <p className="flex items-center gap-2 font-semibold"><ShieldAlert className="h-4 w-4" />{t('incidentRouting.safetyTitle')}</p>
      <p className="mt-1 leading-relaxed">{t('incidentRouting.safetyBody')}</p>
    </div>
    <section className="rounded-lg border border-red-300 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950/30">
      <h2 className="flex items-center gap-2 text-base font-bold"><AlertTriangle className="h-4 w-4 text-red-600" />{t('incidentRouting.activeTitle')}</h2>
      <p className="mt-1 text-sm leading-relaxed">{t('incidentRouting.activeBody')}</p>
      {!activeSelected && <button type="button" onClick={() => setActiveSelected(true)} className="mt-3 rounded-md border border-red-600 px-4 py-2 text-sm font-bold text-red-700 hover:bg-red-100 dark:text-red-300">{t('incidentRouting.activeChoice')}</button>}
      {activeSelected && <a href={safeTelephone(OFFICIAL_CONTACTS[emergency.contactIds[0]].phone) ?? '#'} data-testid="incident-emergency-112" className="mt-3 inline-flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-bold text-white hover:bg-red-700"><Phone className="h-4 w-4" />112</a>}
    </section>
    <div className="flex flex-col gap-3">{nonUrgent.map((r) => <RouteCard key={`${r.kind}-${r.urgency}`} route={r} t={t} />)}</div>
    <section className="rounded-lg border p-4"><h2 className="text-base font-bold">{t('incidentRouting.checklistTitle')}</h2><ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-relaxed">{(['location','facts','time','risk','safeDetails'] as const).map((k) => <li key={k}>{t(`incidentRouting.checklist.${k}` as MessageKey)}</li>)}</ul></section>
    <p className="text-xs text-muted-foreground">{t('incidentRouting.sourcesFooter', { date: INCIDENT_VERIFIED_AT })}</p>
  </main>;
}
