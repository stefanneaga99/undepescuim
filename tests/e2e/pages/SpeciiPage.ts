/**
 * POM — /specii page (species min retention sizes + cmdk search).
 * Docs/e2e-test-plan.md §4.3.
 */
import type { Page } from '@playwright/test';
import { Selectors } from '../helpers/selectors';

export class SpeciiPage {
  constructor(private readonly page: Page) {}

  get h1() {
    return this.page.getByRole('heading', { name: /Dimensiuni minime de reținere/ });
  }

  get backLink() {
    return this.page.getByRole('link', { name: 'Înapoi la hartă' });
  }

  /** Visible search trigger (mobile full-width button or desktop inline). */
  searchTrigger() {
    return this.page
      .getByTestId(Selectors.speciesSearchMobile)
      .or(this.page.getByTestId(Selectors.speciesSearch))
      .filter({ visible: true });
  }

  option(slug: string) {
    return this.page
      .getByTestId(Selectors.speciesOption)
      .and(this.page.locator(`[data-slug="${slug}"]`))
      .filter({ visible: true });
  }

  speciesCard(slug: string) {
    return this.page.locator(`#specii-${slug}`);
  }

  async openSearch(): Promise<void> {
    await this.searchTrigger().click();
  }

  async searchFor(term: string): Promise<void> {
    await this.openSearch();
    await this.page.getByRole('combobox').fill(term);
  }

  async goToSpecies(slug: string): Promise<void> {
    await this.openSearch();
    await this.option(slug).click();
  }
}