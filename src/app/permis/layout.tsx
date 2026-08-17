import type { Metadata } from 'next';

// Server layout — keeps the SEO metadata while the page below is a client
// component (so it can re-render per locale, t_920a7b7b).
export const metadata: Metadata = {
  title: 'Permis & Reguli 2026 — UndePescuim.ro',
  description:
    'Ghid 2026: tranziția ANPA→ANADSPA, cum obții și reînnoiești permisul de pescuit recreativ, capcane și reguli esențiale.',
};

export default function PermisLayout({ children }: { children: React.ReactNode }) {
  return children;
}