/**
 * Single source of truth for the data-testid attributes added across the app
 * (docs/e2e-test-plan.md §5.1). Components render these IDs; POMs and specs
 * reference ONLY these constants — never raw strings, never Leaflet internals.
 */
export const Selectors = {
  mapRoot: 'map-root',
  watersDrawn: 'waters-drawn',
  locateButton: 'locate-button',
  geolocationBubble: 'geolocation-bubble',
  countyChip: 'county-chip',
  localityFilter: 'locality-filter',
  localityOption: 'locality-option',
  localityReset: 'locality-reset',
  typeFilter: 'type-filter',
  typeOption: 'type-option',
  contractFilter: 'contract-filter',
  contractOption: 'contract-option',
  assocSearch: 'assoc-search',
  assocSearchMobile: 'assoc-search-mobile',
  assocOption: 'assoc-option',
  assocChip: 'assoc-chip',
  assocDetailSheet: 'assoc-detail-sheet',
  assocDetailName: 'assoc-detail-name',
  waterCard: 'water-card',
  permitRow: 'permit-row',
  reportPositive: 'report-positive',
  reportFlag: 'report-flag',
  nearbySheet: 'nearby-sheet',
  nearbyRow: 'nearby-row',
  reportDialog: 'report-dialog',
  reportReason: 'report-reason',
  navSpecii: 'nav-specii',
  navPermis: 'nav-permis',
  navSheetSpecii: 'nav-sheet-specii',
  navSheetPermis: 'nav-sheet-permis',
  hamburger: 'hamburger',
  speciesSearch: 'species-search',
  speciesSearchMobile: 'species-search-mobile',
  speciesOption: 'species-option',
  themeToggle: 'theme-toggle',
  langSwitcher: 'lang-switcher',
  lastUpdated: 'last-updated',
  offlineBanner: 'offline-banner',
} as const;

export type TestId = (typeof Selectors)[keyof typeof Selectors];