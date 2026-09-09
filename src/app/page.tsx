import { Suspense } from 'react';
import { Header } from '@/components/layout/Header';
import { MapShell } from '@/components/map/MapShell';

/**
 * Server shell (flat structure — [locale]/i18n is a follow-up milestone,
 * see docs/component_structure_plan.md §2.3). No Leaflet imports here.
 */
export default function Home() {
  return (
    <main className="flex h-[calc(100dvh-4.5rem)] flex-col overflow-hidden md:h-[calc(100dvh-3.5rem)]">
      <Header />
      <Suspense fallback={null}>
        <MapShell />
      </Suspense>
    </main>
  );
}
