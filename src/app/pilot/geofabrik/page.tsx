'use client';

import dynamic from 'next/dynamic';

const Class2PreviewMap = dynamic(() => import('@/components/map/Class2PreviewMap').then((module) => module.Class2PreviewMap), { ssr: false });

export default function GeofabrikPreviewPage() {
  return <Class2PreviewMap />;
}
