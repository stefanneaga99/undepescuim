/**
 * Base test fixture for the seeded tier (docs/e2e-test-plan.md §4.4).
 * Every logic/UI spec extends this: routes are intercepted with the
 * deterministic seed before the page ever loads, and `mapReady` is the
 * single entry point into the map.
 */
import { test as base, expect } from '@playwright/test';
import { seed, type SeedData } from './seed-data';
import { routeData } from './routes';
import { waitForMapReady } from '../helpers/map';

// Playwright fixtures conventionally name their continuation callback `use`;
// it is not React's hook.
/* eslint-disable react-hooks/rules-of-hooks */

type AppFixtures = {
  seedData: SeedData;
  /** Navigate (default `/`) with seeded data and wait until the map is drawn. */
  mapReady: (path?: string) => Promise<void>;
  /** Console/page errors observed during this test (smoke gate). */
  collectedErrors: string[];
};

export const test = base.extend<AppFixtures>({
  page: async ({ page }, use) => {
    await routeData(page, seed);
    await use(page);
  },
  seedData: async ({}, use) => {
    await use(seed);
  },
  mapReady: async ({ page }, use) => {
    await use(async (path = '/') => {
      await page.goto(path);
      await waitForMapReady(page);
    });
  },
  collectedErrors: async ({ page }, use) => {
    const errors: string[] = [];
    page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
    page.on('console', (m) => {
      if (m.type() === 'error') errors.push(`console.error: ${m.text()}`);
    });
    await use(errors);
  },
});

export { expect };
