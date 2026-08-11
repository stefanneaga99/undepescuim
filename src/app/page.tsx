import { Suspense } from 'react';
import { Header } from '@/components/layout/Header';
import { MapShell } from '@/components/map/MapShell';

/**
 * Server shell (flat structure — [locale]/i18n is a follow-up milestone,
 * see docs/component_structure_plan.md §2.3). No Leaflet imports here.
 */
export default function Home() {
  return (
    <main className="flex h-dvh flex-col overflow-hidden">
      <Header />
      <Suspense fallback={null}>
        <MapShell />
      </Suspense>
    </main>
  );
}
