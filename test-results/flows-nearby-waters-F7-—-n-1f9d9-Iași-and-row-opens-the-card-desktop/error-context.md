# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: flows/nearby-waters.spec.ts >> F7 — nearby waters (geolocation grant) >> adaptive radius expands 25 → 50 km when <3 nearby (Iași) and row opens the card
- Location: tests/e2e/specs/flows/nearby-waters.spec.ts:41:7

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: getByTestId('nearby-sheet')
Expected substring: "Rază: 50 km"
Received string:    "Ape în apropierePoziția ta este live; datele despre ape sunt anuale (date 2026). Rază: 330 km.Râul Bahlui TestAsociațieIași · Asociația Beta0 mRâul Nicolina TestAsociațieIași · Asociația Beta1.3 kmLacul TestAsociațieBrașov · Asociația Alpha216.5 kmRâul Someșul TestAsociațieCluj · Asociația Alpha271.8 kmRâul cu un nume foarte lung pentru verificarea trunchierii textului în cartela de detalii la diferite lățimi de ecran și în lista de asociațiiAsociațieCluj · Asociația Alpha295.9 kmLacul București 4AsociațieIlfov · Asociația Beta311.6 kmLacul Beta Fără Permis OnlineAsociațieIlfov · Asociația Beta314.5 kmLacul București 2AsociațieIlfov · Asociația Beta318.2 kmLacul București 1AsociațieIlfov · Asociația Beta321.5 kmLacul București 3AsociațieIlfov · Asociația Beta326.0 kmDoar apele contractate sunt listate aici — pentru râuri/bălți necontractate folosește filtrul „Necontractate”."
Timeout: 10000ms

Call log:
  - Expect "toContainText" with timeout 10000ms
  - waiting for getByTestId('nearby-sheet')
    23 × locator resolved to <div data-nearby-sheet="" data-testid="nearby-sheet" class="absolute bottom-[calc(var(--sheet-snap-h,0vh)+88px)] left-3 z-[1000] flex w-[360px] max-w-[calc(100vw-24px)] flex-col gap-1.5 rounded-xl border bg-background/95 p-3 shadow-md backdrop-blur">…</div>
       - unexpected value "Ape în apropierePoziția ta este live; datele despre ape sunt anuale (date 2026). Rază: 330 km.Râul Bahlui TestAsociațieIași · Asociația Beta0 mRâul Nicolina TestAsociațieIași · Asociația Beta1.3 kmLacul TestAsociațieBrașov · Asociația Alpha216.5 kmRâul Someșul TestAsociațieCluj · Asociația Alpha271.8 kmRâul cu un nume foarte lung pentru verificarea trunchierii textului în cartela de detalii la diferite lățimi de ecran și în lista de asociațiiAsociațieCluj · Asociația Alpha295.9 kmLacul București 4AsociațieIlfov · Asociația Beta311.6 kmLacul Beta Fără Permis OnlineAsociațieIlfov · Asociația Beta314.5 kmLacul București 2AsociațieIlfov · Asociația Beta318.2 kmLacul București 1AsociațieIlfov · Asociația Beta321.5 kmLacul București 3AsociațieIlfov · Asociația Beta326.0 kmDoar apele contractate sunt listate aici — pentru râuri/bălți necontractate folosește filtrul „Necontractate”."

```

```yaml
- heading "Ape în apropiere" [level=2]
- button "Închide lista"
- paragraph: "Poziția ta este live; datele despre ape sunt anuale (date 2026). Rază: 330 km."
- list:
  - listitem:
    - button "Râul Bahlui Test Asociație Iași · Asociația Beta 0 m":
      - text: Râul Bahlui Test Asociație
      - paragraph: Iași · Asociația Beta
      - text: 0 m
  - listitem:
    - button "Râul Nicolina Test Asociație Iași · Asociația Beta 1.3 km":
      - text: Râul Nicolina Test Asociație
      - paragraph: Iași · Asociația Beta
      - text: 1.3 km
  - listitem:
    - button "Lacul Test Asociație Brașov · Asociația Alpha 216.5 km":
      - text: Lacul Test Asociație
      - paragraph: Brașov · Asociația Alpha
      - text: 216.5 km
  - listitem:
    - button "Râul Someșul Test Asociație Cluj · Asociația Alpha 271.8 km":
      - text: Râul Someșul Test Asociație
      - paragraph: Cluj · Asociația Alpha
      - text: 271.8 km
  - listitem:
    - button "Râul cu un nume foarte lung pentru verificarea trunchierii textului în cartela de detalii la diferite lățimi de ecran și în lista de asociații Asociație Cluj · Asociația Alpha 295.9 km":
      - text: Râul cu un nume foarte lung pentru verificarea trunchierii textului în cartela de detalii la diferite lățimi de ecran și în lista de asociații Asociație
      - paragraph: Cluj · Asociația Alpha
      - text: 295.9 km
  - listitem:
    - button "Lacul București 4 Asociație Ilfov · Asociația Beta 311.6 km":
      - text: Lacul București 4 Asociație
      - paragraph: Ilfov · Asociația Beta
      - text: 311.6 km
  - listitem:
    - button "Lacul Beta Fără Permis Online Asociație Ilfov · Asociația Beta 314.5 km":
      - text: Lacul Beta Fără Permis Online Asociație
      - paragraph: Ilfov · Asociația Beta
      - text: 314.5 km
  - listitem:
    - button "Lacul București 2 Asociație Ilfov · Asociația Beta 318.2 km":
      - text: Lacul București 2 Asociație
      - paragraph: Ilfov · Asociația Beta
      - text: 318.2 km
  - listitem:
    - button "Lacul București 1 Asociație Ilfov · Asociația Beta 321.5 km":
      - text: Lacul București 1 Asociație
      - paragraph: Ilfov · Asociația Beta
      - text: 321.5 km
  - listitem:
    - button "Lacul București 3 Asociație Ilfov · Asociația Beta 326.0 km":
      - text: Lacul București 3 Asociație
      - paragraph: Ilfov · Asociația Beta
      - text: 326.0 km
- paragraph: Doar apele contractate sunt listate aici — pentru râuri/bălți necontractate folosește filtrul „Necontractate”.
```

# Test source

```ts
  1  | /**
  2  |  * F7 — nearby waters via geolocation (docs/e2e-test-plan.md §3).
  3  |  * Runs in all three viewports. Local chromium + localhost = secure context →
  4  |  * real `grantPermissions` + `setGeolocation` work (plan §5.5 — no CDP).
  5  |  */
  6  | import { test, expect } from '../../fixtures/app';
  7  | import { GEO_POINTS } from '../../fixtures/seed-data';
  8  | import { MapPage } from '../../pages/MapPage';
  9  | 
  10 | test.describe('F7 — nearby waters (geolocation grant)', () => {
  11 |   test('grant near Bucharest → dot + radius + sheet rows with km/county; default 25 km', async ({
  12 |     context,
  13 |     page,
  14 |     mapReady,
  15 |   }) => {
  16 |     await context.grantPermissions(['geolocation']);
  17 |     await context.setGeolocation({
  18 |       latitude: GEO_POINTS.bucharest.lat,
  19 |       longitude: GEO_POINTS.bucharest.lon,
  20 |     });
  21 |     await mapReady();
  22 | 
  23 |     const map = new MapPage(page);
  24 |     await map.locateButton.click();
  25 | 
  26 |     // user dot + radius circle on the overlay (t_5ddc6022)
  27 |     await expect(page.locator('.user-position-dot')).toBeVisible();
  28 |     expect(await map.pathsByColor(['#2563eb'])).toBeGreaterThan(0);
  29 | 
  30 |     const sheet = map.nearbySheet;
  31 |     await expect(sheet.sheet).toBeVisible();
  32 |     // default radius stays 25 km (≥3 contracted waters within it)
  33 |     await expect(sheet.sheet).toContainText('Rază: 25 km');
  34 |     // rows carry distance + county (Ilfov polygon in the counties seed)
  35 |     await expect(sheet.rows).toHaveCount(5);
  36 |     await expect(sheet.row('Lacul București 1')).toBeVisible();
  37 |     await expect(sheet.row('Lacul București 1')).toContainText('Ilfov');
  38 |     await expect(sheet.sheet).toContainText('· Asociația Beta');
  39 |   });
  40 | 
  41 |   test('adaptive radius expands 25 → 50 km when <3 nearby (Iași) and row opens the card', async ({
  42 |     context,
  43 |     page,
  44 |     mapReady,
  45 |   }) => {
  46 |     await context.grantPermissions(['geolocation']);
  47 |     await context.setGeolocation({
  48 |       latitude: GEO_POINTS.iasi.lat,
  49 |       longitude: GEO_POINTS.iasi.lon,
  50 |     });
  51 |     await mapReady();
  52 | 
  53 |     const map = new MapPage(page);
  54 |     await map.locateButton.click();
  55 | 
  56 |     const sheet = map.nearbySheet;
  57 |     await expect(sheet.sheet).toBeVisible();
> 58 |     await expect(sheet.sheet).toContainText('Rază: 50 km');
     |                               ^ Error: expect(locator).toContainText(expected) failed
  59 | 
  60 |     // row tap → the water's detail card opens
  61 |     await sheet.openRow('Râul Bahlui Test');
  62 |     await expect(map.waterCard.name).toHaveText('Râul Bahlui Test');
  63 |   });
  64 | });
```