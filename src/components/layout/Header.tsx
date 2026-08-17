'use client';

import Link from 'next/link';
import { Fish, Menu } from 'lucide-react';
import { AssociationSearch } from '@/components/associations/AssociationSearch';
import { ThemeToggle } from '@/components/layout/ThemeToggle';
import { PwaStatusBar } from '@/components/pwa/PwaStatusBar';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

/**
 * Info-page links shown in the mobile hamburger menu. Desktop keeps the
 * inline header links (below); this array just drives the Sheet — extend
 * here when a new page lands (no empty links — each must have a route).
 */
const MOBILE_NAV_LINKS = [
  { href: '/specii', label: 'Specii', description: 'Dimensiuni de reținere' },
  { href: '/permis', label: 'Permis 2026', description: 'Acte și taxe de pescuit' },
] as const;

/**
 * Fixed top bar (mobile-layout-spec §2): logo left, association search
 * center (icon → fullscreen overlay on mobile, inline dropdown ≥768px),
 * language badge right. Reads no store state itself.
 *
 * Mobile (<sm): the inline nav links are hidden, so a hamburger Sheet
 * (right drawer) keeps Specii / Permis reachable without clicking a water
 * first (t_f930e4f3). Desktop: inline links unchanged, no hamburger.
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

      <nav className="flex shrink-0 items-center gap-1.5">
        <Link
          href="/permis"
          data-testid="nav-permis"
          className="hidden items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-semibold text-muted-foreground hover:bg-accent hover:text-foreground sm:inline-flex"
        >
          Permis 2026
        </Link>
        <Link
          href="/specii"
          data-testid="nav-specii"
          className="hidden items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-semibold text-muted-foreground hover:bg-accent hover:text-foreground sm:inline-flex"
        >
          Specii
        </Link>
      </nav>

      {/* Theme toggle — sits left of the RO badge, visible on all
          viewports (mobile too: hamburger nav doesn't include it). */}
      <ThemeToggle />

      {/* F6 PWA light: data freshness chip (≥sm) + offline banner (all sizes). */}
      <PwaStatusBar />

      <span
        className="shrink-0 rounded-md border px-2 py-0.5 text-xs font-semibold text-muted-foreground"
        title="Limba site-ului — EN în curând"
      >
        RO
      </span>

      {/* Mobile-only hamburger → right sheet with the info-page links.
          z-[1200]/z-[1100] keeps it above the map's z-1000 filter overlay
          (stacking pitfall t_7a7192ea — portaled popups need z > 1000). */}
      <Sheet>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon-sm"
            className="sm:hidden"
            aria-label="Meniu"
            data-testid="hamburger"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="right" className="z-[1200]" overlayClassName="z-[1100]">
          <SheetHeader>
            <SheetTitle>Meniu</SheetTitle>
          </SheetHeader>
          <nav className="flex flex-col gap-1 px-2 pb-4">
            {MOBILE_NAV_LINKS.map(({ href, label, description }) => (
              <SheetClose asChild key={href}>
                <Link
                  href={href}
                  data-testid={href === '/specii' ? 'nav-sheet-specii' : 'nav-sheet-permis'}
                  className="flex flex-col gap-0.5 rounded-lg px-3 py-3 text-sm font-semibold transition-colors hover:bg-accent hover:text-foreground"
                >
                  {label}
                  <span className="text-xs font-normal text-muted-foreground">
                    {description}
                  </span>
                </Link>
              </SheetClose>
            ))}
          </nav>
        </SheetContent>
      </Sheet>
    </header>
  );
}
