'use client';
import dynamic from 'next/dynamic';
import type { PilotCollection } from '@/lib/pilot-geofabrik';
const Map = dynamic(() => import('react-leaflet').then((m) => m.MapContainer), { ssr: false });
const Tile = dynamic(() => import('react-leaflet').then((m) => m.TileLayer), { ssr: false });
const GeoJSON = dynamic(() => import('react-leaflet').then((m) => m.GeoJSON), { ssr: false });

export function AcceptedGeometryLayer({ collection }: { collection: PilotCollection }) {
  return <Map center={[45.95, 25.6]} zoom={9} zoomControl className="h-full w-full" data-testid="pilot-map">
    <Tile attribution='&copy; OpenStreetMap contributors' url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
    {collection.features.map((feature) => <GeoJSON key={feature.properties.slug} data={feature as never} style={{ color: '#c084fc', weight: 5, dashArray: '8 6', opacity: 0.95 }} interactive={false} data-testid="pilot-accepted-geometry" data-pilot-slug={feature.properties.slug} />)}
  </Map>;
}
