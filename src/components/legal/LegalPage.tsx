import Link from 'next/link';
import { LEGAL_NAV_ITEMS, LEGAL_PLACEHOLDERS } from '@/content/legal';

export function LegalFooter() {
  return (
    <footer className="border-t bg-background/95 px-4 py-3 text-xs text-muted-foreground backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p>
          Informații juridice în curs de completare: {LEGAL_PLACEHOLDERS.entity} ·{' '}
          {LEGAL_PLACEHOLDERS.email}
        </p>
        <nav aria-label="Informații juridice" className="flex flex-wrap gap-x-3 gap-y-1">
          {LEGAL_NAV_ITEMS.map((item) => (
            <Link key={item.href} href={item.href} className="font-medium text-foreground underline-offset-2 hover:underline">
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}

export function LegalPage({
  title,
  intro,
  sections,
}: {
  title: string;
  intro: string;
  sections: Array<{ heading: string; body: string }>;
}) {
  return (
    <main className="mx-auto flex min-w-0 w-full max-w-4xl flex-1 flex-col gap-6 px-4 py-8 md:px-6 md:py-12">
      <div className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
        <strong>Suprafață în curs de completare</strong>
        <p className="mt-1 leading-relaxed">
          Operatorul, adresa și contactele oficiale sunt marcate cu placeholder. Nu publica și nu prezenta această pagină ca dovadă de conformitate până la verificarea lor și revizuirea de către consilier juridic român.
        </p>
      </div>
      <header>
        <h1 className="text-3xl font-bold tracking-tight md:text-4xl">{title}</h1>
        <p className="mt-3 max-w-3xl text-base leading-7 text-muted-foreground">{intro}</p>
      </header>
      <div className="grid gap-4">
        {sections.map((section) => (
          <section key={section.heading} className="rounded-lg border p-5">
            <h2 className="text-lg font-semibold">{section.heading}</h2>
            <p className="mt-2 break-words leading-7 text-muted-foreground [overflow-wrap:anywhere]">{section.body}</p>
          </section>
        ))}
      </div>
      <p className="text-sm text-muted-foreground">
        English summary is available by reading the same disclosures; Romanian is the controlling language for this information surface.
      </p>
    </main>
  );
}
