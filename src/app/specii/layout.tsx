import type { Metadata } from 'next';

// Server layout — keeps the SEO metadata while the page below is a client
// component (so it can re-render per locale, t_920a7b7b).
export const metadata: Metadata = {
  title: 'Specii — dimensiuni minime de reținere — UndePescuim.ro',
  description:
    'Dimensiunile minime legale de reținere pentru peștii de apă dulce din România, cu surse și ultima verificare. Valori naționale — bălțile private pot impune limite mai mari.',
};

export default function SpeciiLayout({ children }: { children: React.ReactNode }) {
  return children;
}