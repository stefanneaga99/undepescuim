import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Sesizare incidente — UndePescuim.ro',
  description: 'Unde raportezi în siguranță braconajul, poluarea și uneltele ilegale.',
};

export default function SesizeazaLayout({ children }: { children: React.ReactNode }) {
  return children;
}
