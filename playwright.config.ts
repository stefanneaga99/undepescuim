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
const RUN_ID = process.env.PLAYWRIGHT_RUN_ID ?? process.env.GITHUB_RUN_ID ?? String(process.pid);
const OUTPUT_DIR = process.env.PLAYWRIGHT_OUTPUT_DIR ?? `test-results/${RUN_ID}`;
const MATRIX = process.env.E2E_MOBILE_MATRIX === '1';
const LIVE_PROD = process.env.LIVE_PROD === '1';
const LIVE_URL = process.env.LIVE_URL ?? 'https://undepescuim.vercel.app';

// Device profiles are Chromium emulations for reproducible CI coverage. Native
// Safari/Chrome runs remain a release-gate follow-up on physical devices.
const mobileMatrixProjects = ([
  ['iphone-current', 'iPhone 15'],
  ['iphone-previous', 'iPhone 14'],
  ['pixel-current', 'Pixel 7'],
  ['pixel-previous', 'Pixel 5'],
  ['samsung-current', 'Galaxy S24'],
  ['samsung-previous', 'Galaxy S21'],
] as const).map(([name, device]) => ({
  name,
  grepInvert: /@data/,
  testIgnore: /live-prod\.spec\.ts/,
  use: { ...devices[device], browserName: 'chromium' as const },
}));

export default defineConfig({
  testDir: './tests/e2e/specs',
  globalSetup: './tests/e2e/global-setup.ts',
  outputDir: OUTPUT_DIR,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  // Leaflet + a single prod server: keep sequential to avoid zoom/tile flake
  // (the plan's §5 strategy — determinism over parallelism).
  fullyParallel: false,
  workers: process.env.CI ? 2 : 1,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI
    ? [
        ['list'],
        ['./tests/e2e/reporters/lifecycle.ts'],
        ['html', {
          open: 'never',
          outputFolder: process.env.PLAYWRIGHT_REPORT_DIR ?? 'playwright-report',
        }],
        ['github'],
      ]
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
  projects: LIVE_PROD ? [
    {
      name: 'live-prod-desktop',
      testMatch: /(?:live-prod|olt-viewport-culling)\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        baseURL: LIVE_URL,
        browserName: 'chromium',
        serviceWorkers: 'allow',
        viewport: { width: 1280, height: 800 },
      },
    },
    {
      name: 'live-prod-mobile',
      testMatch: /(?:live-prod|olt-viewport-culling)\.spec\.ts/,
      use: {
        ...devices['iPhone 14'],
        baseURL: LIVE_URL,
        browserName: 'chromium',
        serviceWorkers: 'allow',
      },
    },
  ] : [
    {
      // 390×844 — the mobile branch (hamburger nav, vaul bottom sheets).
      // iPhone 14 device presets + forced chromium (only chromium is installed).
      name: 'mobile',
      grepInvert: /@data/,
      testIgnore: /live-prod\.spec\.ts/,
      use: { ...devices['iPhone 14'], browserName: 'chromium' },
    },
    {
      // 768×1024 — the `md` breakpoint boundary: desktop filter panel but
      // still the compact (<1024px) vaul drawer for detail sheets.
      name: 'tablet',
      grepInvert: /@data/,
      testIgnore: /live-prod\.spec\.ts/,
      use: { ...devices['iPad (gen 7)'], browserName: 'chromium' },
    },
    {
      // 1280×800 — desktop: inline nav, side panel, floating nearby panel.
      name: 'desktop',
      testIgnore: /live-prod\.spec\.ts/,
      grepInvert: /@data/,
      use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } },
    },
    {
      // Keep real-data probes in this same Playwright invocation so the
      // server/build lifecycle is not repeated. Its browser context remains
      // independent from the seeded projects.
      name: 'data',
      testIgnore: /live-prod\.spec\.ts/,
      grep: /@data/,
      use: { ...devices['Desktop Chrome'], browserName: 'chromium' },
    },
    ...(MATRIX ? mobileMatrixProjects : []),
  ],
  webServer: LIVE_PROD || process.env.E2E_SERVER_READY
    ? undefined
    : {
        // Build once, serve once — closer to prod than `next dev`, and stable
        // (dev-mode HMR + on-demand compile is the #1 timing-flake source).
        command: `npm run build && PORT=${PORT} npm run start`,
        url: BASE_URL,
        reuseExistingServer: !process.env.CI,
        timeout: 240_000,
      },
});
