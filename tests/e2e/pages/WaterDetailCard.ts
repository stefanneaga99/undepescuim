/**
 * POM — the water detail card (inside the desktop aside / mobile vaul
 * drawer). Docs/e2e-test-plan.md §4.3.
 *
 * Compact-viewport note (WSL/browserless + vaul translate, skill §t_abccfd6c
 * pitfall 1 & 13): while the vaul drawer is open the page body has
 * pointer-events:none and the drawer is translated so card content can sit
 * outside the clickable strip — card BUTTON interactions use
 * `evaluate(el.click())` (the proven primary path) and text assertions use
 * web-first `toHaveText`/`toContainText` (bounding-box based, no viewport
 * requirement). `expand()` taps the vaul handle to the top snap when the
 * whole card must be on-screen.
 */
import { expect, type Locator, type Page } from '@playwright/test';
import { Selectors } from '../helpers/selectors';

export class WaterDetailCard {
  constructor(private readonly page: Page) {}

  get card() {
    return this.page.getByTestId(Selectors.waterCard);
  }

  get name() {
    return this.card.locator('h2').first();
  }

  get permitRows() {
    return this.card.getByTestId(Selectors.permitRow);
  }

  get reportPositive() {
    return this.card.getByTestId(Selectors.reportPositive);
  }

  get reportFlag() {
    return this.card.getByTestId(Selectors.reportFlag);
  }

  get permisLink() {
    // The card can render TWO /permis links (the standard button on contracted
    // cards + the teal guide link on uncontracted notices) — both target the
    // guide. Prefer the guide link ("Vezi ghidul"), fall back to the button.
    return this.card
      .getByRole('link', { name: /Vezi ghidul „Permis/ })
      .or(this.card.getByRole('link', { name: 'Permis & Reguli 2026', exact: true }))
      .first();
  }

  get speciiLink() {
    return this.card.getByRole('link', { name: /Dimensiuni de reținere/ });
  }

  private isCompact(): Promise<boolean> {
    return this.page.evaluate(() => window.innerWidth < 1024);
  }

  /** Tap the vaul handle → highest snap, so the whole card is on-screen. */
  async expand(): Promise<void> {
    if (!(await this.isCompact())) return;
    const handle = this.page.locator('[data-vaul-handle]').first();
    await handle.click();
    await expect(this.card).toBeVisible();
  }

  /** Click a card button (evaluate path on compact; real click on desktop). */
  async clickButton(locator: Locator): Promise<void> {
    if (await this.isCompact()) {
      await locator.evaluate((el) => (el as HTMLElement).click());
    } else {
      await locator.click();
    }
  }
}