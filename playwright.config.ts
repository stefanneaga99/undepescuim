import { defineConfig, devices } from '@playwright/test';

/**
 * UndePescuim.ro — E2E test configuration (docs/e2e-test-plan.md §4.2).
 *
 * Ports: the app runs on 3000 in CI (free) but 3100 on this WSL host (3000
 * is a docker browserless Chrome service). Override with E2E_PORT.
 * Base URL override: PLAYWRIGHT_BASE_URL (used for Vercel previews etc).
 */
const PORT = process.env.E2E_PORT ?? (process.env.CI ? '3000' : '3100');
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? `http://localhost:${PORT}`;

export default defineConfig({
  testDir: './tests/e2e/specs',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  // Leaflet + a single prod server: keep sequential to avoid zoom/tile flake
  // (the plan's §5 strategy — determinism over parallelism).
  fullyParallel: false,
  workers: process.env.CI ? 2 : 1,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI
    ? [['list'], ['html', { open: 'never' }], ['github']]
    : [['list']],
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    serviceWorkers: 'block',
    // t_5a65abcf: the app's UI default is HARD RO — navigator.language is
    // ignored entirely. The ro-RO emulation just makes the RO-default
    // assertions in the specs reflect a typical Romanian visitor; the
    // i18n spec overrides this with an en-US describe to prove the
    // no-auto-switch mandate.
    locale: 'ro-RO',
    timezoneId: 'Europe/Bucharest',
  },
  projects: [
    {
      // 390×844 — the mobile branch (hamburger nav, vaul bottom sheets).
      // iPhone 14 device presets + forced chromium (only chromium is installed).
      name: 'mobile',
      use: { ...devices['iPhone 14'], browserName: 'chromium' },
    },
    {
      // 768×1024 — the `md` breakpoint boundary: desktop filter panel but
      // still the compact (<1024px) vaul drawer for detail sheets.
      name: 'tablet',
      use: { ...devices['iPad (gen 7)'], browserName: 'chromium' },
    },
    {
      // 1280×800 — desktop: inline nav, side panel, floating nearby panel.
      name: 'desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } },
    },
  ],
  webServer: {
    // Build once, serve once — closer to prod than `next dev`, and stable
    // (dev-mode HMR + on-demand compile is the #1 timing-flake source).
    command: `npm run build && PORT=${PORT} npm run start`,
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 240_000,
  },
});
