import type { Metadata } from 'next';
import { LegalPage } from '@/components/legal/LegalPage';
import { legalSections } from '@/content/legal';

export const metadata: Metadata = {
  title: 'Confidențialitate și stocare — UndePescuim.ro',
  description: 'Informare în limba română despre date, geolocație și stocarea offline.',
};

export default function ConfidentialitatePage() {
  return (
    <LegalPage
      title="Confidențialitate și stocare"
      intro="Această informare descrie, în limbaj simplu, datele folosite de UndePescuim. Nu este consultanță juridică și nu afirmă că serviciul este conform legal."
      sections={[
        { heading: 'Operator și responsabilități', body: legalSections.privacy },
        { heading: 'Scopuri și temeiuri', body: legalSections.purposes },
        { heading: 'Destinatari și transferuri', body: legalSections.recipients },
        { heading: 'Păstrare și ștergere', body: legalSections.retention },
        { heading: 'Drepturile tale și ANSPDCP', body: legalSections.rights },
        { heading: 'Geolocație', body: legalSections.geolocation },
        { heading: 'Stocare locală și offline', body: legalSections.storage },
      ]}
    />
  );
}
