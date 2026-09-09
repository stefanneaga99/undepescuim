import type { Metadata } from 'next';
import { LegalPage } from '@/components/legal/LegalPage';
import { legalSections } from '@/content/legal';

export const metadata: Metadata = {
  title: 'Termeni și utilizare — UndePescuim.ro',
  description: 'Termeni informativi și reguli de utilizare responsabilă.',
};

export default function TermeniPage() {
  return (
    <LegalPage
      title="Termeni și utilizare responsabilă"
      intro="Folosirea site-ului înseamnă acceptarea acestor limite. Termenii nu exclud drepturi sau răspunderi care nu pot fi excluse prin lege."
      sections={[
        { heading: 'Scop informativ, fără garanții', body: legalSections.terms },
        { heading: 'Rapoarte și takedown', body: legalSections.reports },
        { heading: 'Utilizare acceptabilă', body: 'Nu încerca să accesezi, să descarci sau să preiei în masă serviciul, dalele OSM ori datele altor persoane. Nu trimite conținut ilegal, amenințări, date de autentificare sau acuzații despre persoane identificabile. Pentru o sesizare urgentă contactează autoritățile, nu site-ul.' },
        { heading: 'Actualizări și surse oficiale', body: 'Datele și regulile se pot schimba. Verifică actele și administratorul apei înainte de pescuit; o hartă sau un raport public nu dovedește dreptul de pescuit și nu ține loc de permis.' },
      ]}
    />
  );
}
