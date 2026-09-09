import type { Metadata } from 'next';
import { LegalPage } from '@/components/legal/LegalPage';
import { legalSections, LEGAL_PLACEHOLDERS } from '@/content/legal';

export const metadata: Metadata = {
  title: 'Contact și drepturi — UndePescuim.ro',
  description: 'Contact operator, cereri privind datele și ruta de takedown.',
};

export default function ContactPage() {
  return (
    <LegalPage
      title="Contact, drepturi și takedown"
      intro="Folosește această rută pentru cereri privind datele, corectarea sau eliminarea unui raport. Datele oficiale sunt încă placeholder și trebuie completate înainte de lansare."
      sections={[
        { heading: 'Operator și contact oficial', body: legalSections.privacy },
        { heading: 'Cereri privind datele', body: legalSections.rights },
        { heading: 'Eliminarea unui raport public', body: legalSections.reports },
        { heading: 'Contacte care trebuie completate', body: `${LEGAL_PLACEHOLDERS.entity} · ${LEGAL_PLACEHOLDERS.address} · ${LEGAL_PLACEHOLDERS.email} · ${LEGAL_PLACEHOLDERS.dataProtection}` },
      ]}
    />
  );
}
