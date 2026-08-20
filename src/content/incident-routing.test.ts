import { describe, expect, it } from 'vitest';
import { INCIDENT_ROUTES, OFFICIAL_CONTACTS } from './incident-routing';

describe('incident routing content', () => {
  it('uses HTTPS provenance for every official contact', () => {
    expect(Object.values(OFFICIAL_CONTACTS).every((c) => c.sourceUrl.startsWith('https://'))).toBe(true);
  });
  it('limits 112 to active emergency routes', () => {
    for (const route of INCIDENT_ROUTES) {
      const has112 = route.contactIds.includes('emergency112');
      expect(has112).toBe(route.urgency === 'active_emergency');
    }
  });
  it('does not publish invented national authorities', () => {
    const text = JSON.stringify({ routes: INCIDENT_ROUTES, contacts: OFFICIAL_CONTACTS });
    expect(text).not.toMatch(/ANADSPA|AJVPS|Jandarmeria/);
  });
});
