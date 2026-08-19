import { describe, expect, it } from 'vitest';
import { mergeAssociationLocations } from '@/lib/association-locations';
import type { Association } from '@/types/data';

const association = {
  id: 'assoc-1',
  slug: 'club-one',
  name: 'Club One',
  name_long: 'Club One',
  ape: 2,
  adresa: 'Adresa legacy',
  telefon: '0210000000',
  siteUrl: 'https://club.example',
  bbox: [0, 0, 1, 1],
} as Association;

const location = {
  id: 'location-1',
  associationId: 'assoc-1',
  associationSlug: 'club-one',
  type: 'headquarters',
  label: 'Sediu central',
  address: 'Str. Exemplu 1',
  locality: 'Cluj-Napoca',
  county: 'Cluj',
  country: 'RO',
  contacts: [
    { kind: 'phone', value: '0264000000' },
    { kind: 'email', value: 'contact@club.example' },
    { kind: 'url', value: 'https://club.example/contact' },
  ],
  sources: [{ url: 'https://club.example/contact', publisher: 'Club One', sourceType: 'official', retrievedAt: '2026-08-19' }],
  status: 'verified',
  confidence: 'high',
  freshness: 'needs_confirmation',
  checkedAt: '2026-08-19',
  public: true,
  review: { status: 'approved', approvedAt: '2026-08-19' },
} as const;

describe('mergeAssociationLocations', () => {
  it('groups approved locations by association and preserves qualified fields', () => {
    const [merged] = mergeAssociationLocations([association], { schemaVersion: 1, locations: [location] });
    expect(merged.locations).toEqual([location]);
    expect(merged.locations?.[0].type).toBe('headquarters');
    expect(merged.locations?.[0].freshness).toBe('needs_confirmation');
    expect(merged.adresa).toBe('Adresa legacy');
    expect(merged.telefon).toBe('0210000000');
  });

  it('falls back unchanged when the artifact is missing or malformed', () => {
    expect(mergeAssociationLocations([association], null)[0]).toBe(association);
    expect(mergeAssociationLocations([association], { schemaVersion: 1, locations: [{ nope: true }] })[0]).toBe(association);
    expect(mergeAssociationLocations([association], { schemaVersion: 2, locations: [] })[0]).toBe(association);
  });

  it('does not expose unapproved records or infer pickup/branch semantics', () => {
    const unapproved = { ...location, id: 'location-2', type: 'permit_pickup_point', review: { status: 'needs_review' } };
    const [merged] = mergeAssociationLocations([association], { schemaVersion: 1, locations: [unapproved] });
    expect(merged.locations).toBeUndefined();
  });
});
