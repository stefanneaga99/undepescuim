'use client';

import Link from 'next/link';
import { Fish } from 'lucide-react';
import { AssociationSearch } from '@/components/associations/AssociationSearch';

/**
 * Fixed top bar (mobile-layout-spec §2): logo left, association search
 * center (icon → fullscreen overlay on mobile, inline dropdown ≥768px),
 * language badge right. Reads no store state itself.
 */
export function Header() {
  return (
    <header className="z-50 flex h-12 shrink-0 items-center gap-2 border-b bg-background/95 px-3 backdrop-blur md:h-14 md:gap-4 md:px-4">
      <Link href="/" className="flex shrink-0 items-center gap-2" aria-label="UndePescuim.ro — acasă">
        <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Fish className="h-4 w-4" />
        </span>
        <span className="hidden text-base font-bold tracking-tight sm:block">
          UndePescuim<span className="text-primary">.ro</span>
        </span>
      </Link>

      <div className="flex min-w-0 flex-1 justify-center md:justify-start">
        <AssociationSearch />
      </div>

      <nav className="shrink-0">
        <Link
          href="/permis"
          className="hidden items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-semibold text-muted-foreground hover:bg-accent hover:text-foreground sm:inline-flex"
        >
          Permis 2026
        </Link>
      </nav>

      <span
        className="shrink-0 rounded-md border px-2 py-0.5 text-xs font-semibold text-muted-foreground"
        title="Limba site-ului — EN în curând"
      >
        RO
      </span>
    </header>
  );
}
