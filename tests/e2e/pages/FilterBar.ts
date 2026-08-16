/**
 * POM — FilterBar controls (county chips, locality popover, type + contract
 * segmented controls). Docs/e2e-test-plan.md §4.3.
 *
 * FilterBar renders its content TWICE (hidden mobile bar + desktop panel);
 * all locators here filter to the visible copy so assertions never see the
 * display:none duplicate (t_dd918db7 pitfall).
 */
import type { Page } from '@playwright/test';
import { Selectors } from '../helpers/selectors';

export class FilterBar {
  constructor(private readonly page: Page) {}

  private visible(testId: string) {
    return this.page.getByTestId(testId).filter({ visible: true });
  }

  countyChip(county: string) {
    return this.page
      .getByTestId(Selectors.countyChip)
      .filter({ visible: true })
      .filter({ hasText: county });
  }

  allCountyChips() {
    return this.visible(Selectors.countyChip);
  }

  get localityTrigger() {
    return this.visible(Selectors.localityFilter);
  }

  localityOption(locality: string) {
    return this.visible(Selectors.localityOption).filter({ hasText: locality });
  }

  get localityReset() {
    return this.visible(Selectors.localityReset);
  }

  typeOption(value: string) {
    return this.visible(Selectors.typeOption).filter({ has: this.page.locator(`[data-value="${value}"]`) });
  }

  contractOption(value: string) {
    return this.visible(Selectors.contractOption).filter({
      has: this.page.locator(`[data-value="${value}"]`),
    });
  }

  async toggleCounty(county: string): Promise<void> {
    // chip click is intercepted by the z-1000 filter panel overlay on desktop
    // (t_1b7c95a7 pitfall 9) — the chip sets store state, evaluate-click is
    // the reliable path in both branches.
    await this.countyChip(county).evaluate((el) => (el as HTMLButtonElement).click());
  }

  async selectLocality(locality: string): Promise<void> {
    await this.localityTrigger.click();
    await this.localityOption(locality).click();
  }

  async resetLocalities(): Promise<void> {
    await this.localityTrigger.click();
    await this.localityReset.click();
  }

  async setType(value: 'all' | 'lac' | 'rau'): Promise<void> {
    await this.typeOption(value).click();
  }

  async setContract(value: 'all' | 'contractate' | 'necontractate'): Promise<void> {
    await this.contractOption(value).click();
  }
}