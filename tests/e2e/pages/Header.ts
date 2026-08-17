/**
 * POM — header nav (logo, inline links, mobile hamburger sheet).
 * Docs/e2e-test-plan.md §4.3. Selectors are data-testid only.
 */
import type { Page } from '@playwright/test';
import { Selectors } from '../helpers/selectors';

export class Header {
  constructor(private readonly page: Page) {}

  get logo() {
    return this.page.getByRole('link', { name: /UndePescuim/ });
  }

  get navSpecii() {
    return this.page.getByTestId(Selectors.navSpecii);
  }

  get navPermis() {
    return this.page.getByTestId(Selectors.navPermis);
  }

  get hamburger() {
    return this.page.getByTestId(Selectors.hamburger);
  }

  /** RO ⇄ EN language toggle (t_920a7b7b). */
  get languageSwitcher() {
    return this.page.getByTestId(Selectors.langSwitcher);
  }

  get sheetSpeciiLink() {
    return this.page.getByTestId(Selectors.navSheetSpecii);
  }

  get sheetPermisLink() {
    return this.page.getByTestId(Selectors.navSheetPermis);
  }

  /** Open the mobile hamburger menu; no-op on desktop (button hidden). */
  async openMenu(): Promise<void> {
    await this.hamburger.click();
  }

  /** Navigate home via the logo. */
  async goHome(): Promise<void> {
    await this.logo.click();
  }
}