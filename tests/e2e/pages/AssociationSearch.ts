/**
 * POM — association command search (mobile fullscreen / desktop dropdown).
 * Docs/e2e-test-plan.md §4.3: `assoc-option` items carry data-slug.
 */
import type { Page } from '@playwright/test';
import { Selectors } from '../helpers/selectors';

export class AssociationSearch {
  constructor(private readonly page: Page) {}

  /** Visible trigger: mobile icon or desktop inline button. */
  trigger() {
    return this.page
      .getByTestId(Selectors.assocSearchMobile)
      .or(this.page.getByTestId(Selectors.assocSearch))
      .filter({ visible: true });
  }

  option(slug: string) {
    return this.page
      .getByTestId(Selectors.assocOption)
      .and(this.page.locator(`[data-slug="${slug}"]`))
      .filter({ visible: true });
  }

  get allAssociationsOption() {
    return this.option('__all__');
  }

  async open(): Promise<void> {
    await this.trigger().click();
  }

  /** Open + select an association by slug. */
  async select(slug: string): Promise<void> {
    await this.open();
    await this.option(slug).click();
  }

  /** Open + clear the selection ("Toate asociațiile"). */
  async clearSelection(): Promise<void> {
    await this.open();
    await this.allAssociationsOption.click();
  }
}