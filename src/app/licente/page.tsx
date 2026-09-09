import type { Metadata } from 'next';
import { LegalPage } from '@/components/legal/LegalPage';
import { legalSections } from '@/content/legal';

export const metadata: Metadata = {
  title: 'Licențe și surse date — UndePescuim.ro',
  description: 'Surse, atribuire OpenStreetMap și informare ODbL.',
};

export default function LicentePage() {
  return (
    <LegalPage
      title="Licențe și surse de date"
      intro="Această pagină explică sursele cartografice și limitele licențelor. Registrul complet al datelor livrate trebuie menținut și verificat înainte de producție."
      sections={[
        { heading: 'OpenStreetMap și ODbL', body: legalSections.licence },
        { heading: 'Atribuire vizibilă', body: 'Atribuirea trebuie să rămână vizibilă lângă hartă, pe mobil și desktop: © OpenStreetMap contributors. Linkul către copyright explică licența ODbL și sursele contribuțiilor.' },
        { heading: 'Registrul surselor', body: 'Pentru fiecare set de date cartografice și administrativ trebuie păstrate sursa, data extragerii, transformările, clasificarea (bază de date, bază derivată sau produs) și metoda de a oferi datele derivate când ODbL o cere. Nu confundăm un câmp de proveniență cu o concluzie juridică.' },
        { heading: 'Limite tehnice și responsabilitate', body: 'Harta nu oferă descărcare în masă sau prefetch de dale. Sursele externe pot avea politici, limite și disponibilitate proprii; verifică întotdeauna termenii lor în vigoare.' },
      ]}
    />
  );
}
