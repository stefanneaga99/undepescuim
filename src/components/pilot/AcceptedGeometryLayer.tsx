'use client';
import dynamic from 'next/dynamic';
import type { PhysicalCourseCollection, PilotCollection } from '@/lib/pilot-geofabrik';
const Map = dynamic(() => import('react-leaflet').then((m) => m.MapContainer), { ssr: false });
const Tile = dynamic(() => import('react-leaflet').then((m) => m.TileLayer), { ssr: false });
const GeoJSON = dynamic(() => import('react-leaflet').then((m) => m.GeoJSON), { ssr: false });

export function AcceptedGeometryLayer({ collection, physicalCourses }: { collection: PilotCollection; physicalCourses: PhysicalCourseCollection }) {
  return <Map center={[46.1, 25.55]} zoom={9} zoomControl className="h-full w-full" data-testid="pilot-map" aria-label="Experimental physical river course preview">
    <Tile attribution='&copy; OpenStreetMap contributors' url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
    {physicalCourses.features.map((feature) => <GeoJSON key={`physical-${feature.properties.slug}`} data={feature as never} style={{ color: '#14b8a6', weight: 5, dashArray: '10 8', opacity: 0.95 }} interactive={false} data-testid="pilot-physical-course-line" data-pilot-slug={feature.properties.slug} />)}
    {collection.features.map((feature) => <GeoJSON key={feature.properties.slug} data={feature as never} style={{ color: '#c084fc', weight: 5, dashArray: '8 6', opacity: 0.95 }} interactive={false} data-testid="pilot-accepted-geometry" data-pilot-slug={feature.properties.slug} />)}
  </Map>;
}
