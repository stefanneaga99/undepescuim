import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowLeft, AlertTriangle, ExternalLink, FileText, HelpCircle, Scale, ShieldCheck, Sparkles } from 'lucide-react';
import {
  PERMIS_LAST_UPDATED,
  PERMIS_PORTAL_URL,
  PERMIS_WHAT_CHANGED,
  PERMIS_GET_STATE,
  PERMIS_GET_ASSOCIATION,
  PERMIS_GET_DELTA,
  PERMIS_GOLDEN_RULE,
  PERMIS_RENEW,
  PERMIS_GOTCHAS,
  PERMIS_RULES,
  PERMIS_UPCOMING,
  PERMIS_FAQ,
  PERMIS_SOURCES,
} from '@/content/permis-2026';

export const metadata: Metadata = {
  title: 'Permis & Reguli 2026 — UndePescuim.ro',
  description:
    'Ghid 2026: tranziția ANPA→ANADSPA, cum obții și reînnoiești permisul de pescuit recreativ, capcane și reguli esențiale.',
};

function SectionHeading({
  icon,
  children,
}: {
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <h2 className="mt-8 flex items-center gap-2 text-lg font-bold tracking-tight">
      {icon}
      {children}
    </h2>
  );
}

function GotchaCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
      <p className="flex items-center gap-1.5 font-semibold">
        <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
        {title}
      </p>
      <p className="mt-0.5 text-xs leading-relaxed opacity-90">{body}</p>
    </div>
  );
}

export default function PermisPage() {
  return (
    <main className="mx-auto w-full max-w-3xl px-4 py-6 md:py-10">
      <Link
        href="/"
        className="mb-4 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Înapoi la hartă
      </Link>

      <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Permis &amp; Reguli 2026</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Ultima verificare a faptelor: {PERMIS_LAST_UPDATED}. Informațiile se pot schimba —
        verifică sursele oficiale (linkuri la finalul paginii) înainte de o decizie. Conținut
        sensibil la timp: se re-verifică trimestrial.
      </p>

      {/* §1 Ce s-a schimbat */}
      <SectionHeading icon={<ShieldCheck className="h-4 w-4 text-primary" />}>
        Ce s-a schimbat: ANPA → ANADSPA
      </SectionHeading>
      <p className="mt-2 text-sm leading-relaxed">{PERMIS_WHAT_CHANGED.lead}</p>
      <p className="mt-3 text-sm font-medium">Ce înseamnă asta pentru tine, ca pescar recreativ, practic:</p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        {PERMIS_WHAT_CHANGED.bullets.map((b) => (
          <li key={b}>{b}</li>
        ))}
      </ul>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{PERMIS_WHAT_CHANGED.unchanged}</p>

      {/* §2 Cum obții */}
      <SectionHeading icon={<FileText className="h-4 w-4 text-primary" />}>
        Cum obții permisul în 2026
      </SectionHeading>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        Există trei situații diferite, în funcție de unde pescuiești:
      </p>

      <h3 className="mt-4 text-sm font-bold">{PERMIS_GET_STATE.title}</h3>
      <p className="mt-1 text-sm leading-relaxed">{PERMIS_GET_STATE.intro}</p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        {PERMIS_GET_STATE.items.map((i) => (
          <li key={i}>{i}</li>
        ))}
      </ul>
      <p className="mt-2 text-sm leading-relaxed">
        <a
          href={PERMIS_PORTAL_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-primary hover:underline"
        >
          Deschide portalul de permise
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </p>

      <h3 className="mt-4 text-sm font-bold">{PERMIS_GET_ASSOCIATION.title}</h3>
      <p className="mt-1 text-sm leading-relaxed">{PERMIS_GET_ASSOCIATION.intro}</p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        {PERMIS_GET_ASSOCIATION.items.map((i) => (
          <li key={i}>{i}</li>
        ))}
      </ul>

      <h3 className="mt-4 text-sm font-bold">{PERMIS_GET_DELTA.title}</h3>
      <p className="mt-1 text-sm leading-relaxed">{PERMIS_GET_DELTA.intro}</p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        {PERMIS_GET_DELTA.items.map((i) => (
          <li key={i}>{i}</li>
        ))}
      </ul>

      <div className="mt-4 rounded-md border border-teal-200 bg-teal-50 px-3 py-2.5 text-sm text-teal-900 dark:border-teal-900 dark:bg-teal-950/40 dark:text-teal-100">
        <p className="font-medium">Regula de aur</p>
        <p className="mt-0.5 text-xs leading-relaxed opacity-90">{PERMIS_GOLDEN_RULE}</p>
      </div>

      {/* §3 Cum reînnoiești */}
      <SectionHeading icon={<Sparkles className="h-4 w-4 text-primary" />}>
        Cum reînnoiești permisul
      </SectionHeading>
      <p className="mt-2 text-sm leading-relaxed">{PERMIS_RENEW.intro}</p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        <li>{PERMIS_RENEW.currentRule}</li>
        <li>{PERMIS_RENEW.changing}</li>
      </ul>

      {/* §4 Capcane */}
      <SectionHeading icon={<AlertTriangle className="h-4 w-4 text-primary" />}>
        Capcane cunoscute (gotchas)
      </SectionHeading>
      <div className="mt-2 flex flex-col gap-2">
        {PERMIS_GOTCHAS.map((g) => (
          <GotchaCard key={g.title} title={g.title} body={g.body} />
        ))}
      </div>

      {/* §5 Reguli */}
      <SectionHeading icon={<Scale className="h-4 w-4 text-primary" />}>
        Reguli esențiale (pe scurt)
      </SectionHeading>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        Acestea sunt și regulile din care se dau întrebările de la chestionar:
      </p>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        {PERMIS_RULES.map((r) => (
          <li key={r}>{r}</li>
        ))}
      </ul>

      {/* §6 Ce se pregătește */}
      <SectionHeading icon={<Sparkles className="h-4 w-4 text-primary" />}>
        Ce se pregătește (proiect de ordin MADR, mai 2026)
      </SectionHeading>
      <div className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
        <p className="font-semibold">Încă NU în vigoare</p>
        <p className="mt-0.5 text-xs leading-relaxed opacity-90">{PERMIS_UPCOMING.status}</p>
      </div>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed">
        {PERMIS_UPCOMING.bullets.map((b) => (
          <li key={b}>{b}</li>
        ))}
      </ul>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{PERMIS_UPCOMING.unchanged}</p>

      {/* FAQ */}
      <SectionHeading icon={<HelpCircle className="h-4 w-4 text-primary" />}>
        FAQ
      </SectionHeading>
      <dl className="mt-2 flex flex-col gap-3">
        {PERMIS_FAQ.map((f) => (
          <div key={f.q} className="rounded-md border px-3 py-2.5">
            <dt className="text-sm font-semibold">{f.q}</dt>
            <dd className="mt-0.5 text-sm leading-relaxed text-muted-foreground">{f.a}</dd>
          </div>
        ))}
      </dl>

      {/* Surse */}
      <SectionHeading icon={<ExternalLink className="h-4 w-4 text-primary" />}>
        Surse
      </SectionHeading>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        Fiecare afirmație de pe această pagină se bazează pe sursele de mai jos (verificate la{' '}
        {PERMIS_LAST_UPDATED}). Re-verifică-le trimestrial — conținutul este sensibil la timp.
      </p>
      <ul className="mt-2 flex flex-col gap-1.5">
        {PERMIS_SOURCES.map((s) => (
          <li key={s.url} className="text-sm">
            <a
              href={s.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-start gap-1 text-primary hover:underline"
            >
              <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>
                {s.label}
                <span className="block text-xs text-muted-foreground">{s.note}</span>
              </span>
            </a>
          </li>
        ))}
      </ul>

      <p className="mt-8 border-t pt-4 text-xs text-muted-foreground">
        Ultima verificare a faptelor: {PERMIS_LAST_UPDATED}. Conținutul se re-verifică trimestrial
        (portalul de permise, madr.ro, Monitorul Oficial).
      </p>
    </main>
  );
}
