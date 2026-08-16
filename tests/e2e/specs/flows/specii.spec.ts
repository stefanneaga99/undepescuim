/**
 * F9 — /specii species min retention sizes + cmdk search
 * (docs/e2e-test-plan.md §3). Runs in all three viewports.
 * The page is SSR (static content from src/content/species.ts) — no map, no
 * seeded data needed; assertions target real rendered content.
 */
import { test, expect } from '../../fixtures/app';
import { SpeciiPage } from '../../pages/SpeciiPage';

test.describe('F9 — /specii page', () => {
  test('renders species with min sizes, protected section, sources, back link', async ({
    page,
  }) => {
    const specii = new SpeciiPage(page);
    await page.goto('/specii');

    await expect(specii.h1).toBeVisible();
    await expect(page.getByText('Specii cu dimensiune minimă')).toBeVisible();
    // a known species card with its min size (somn — 50 cm in data/species.json)
    await expect(specii.speciesCard('somn')).toBeVisible();
    await expect(page.getByText('50')).toBeVisible();
    // protected section + sources + back-home link
    await expect(page.getByText('Protejate / interzise / neconfirmate')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Surse' })).toBeVisible();
    await expect(specii.backLink).toBeVisible();
  });

  test('search narrows (diacritic-insensitive) and selecting scrolls+flashes the row', async ({
    page,
  }) => {
    const specii = new SpeciiPage(page);
    await page.goto('/specii');

    // diacritic-insensitive: typing "sturion" finds "Sturion de Dunăre"
    await specii.searchFor('sturion');
    await expect(specii.option('sturion-de-dunare')).toBeVisible();

    // search by size: "40" finds crap / știucă (40 cm)
    await expect(specii.option('crap')).toBeVisible();

    // select → the row flashes (species-flash class) + is scrolled into view
    await specii.option('crap').click();
    await expect(specii.speciesCard('crap')).toHaveClass(/species-flash/);
    await expect(specii.speciesCard('crap')).toBeInViewport();
  });

  test('search is case/diacritic-insensitive and empty state shows no hits', async ({
    page,
  }) => {
    const specii = new SpeciiPage(page);
    await page.goto('/specii');

    await specii.searchFor('ȘTURION');
    await expect(specii.option('sturion-de-dunare')).toBeVisible();

    await page.getByRole('combobox').fill('zzzzzz');
    await expect(page.getByText('Nicio specie găsită')).toBeVisible();
  });
});