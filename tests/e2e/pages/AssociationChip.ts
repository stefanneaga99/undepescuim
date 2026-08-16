/**
 * POM — the persistent association chip on the map + the detail sheet it
 * opens. Docs/e2e-test-plan.md §4.3.
 */
import type { Page } from '@playwright/test';
import { Selectors } from '../helpers/selectors';

export class AssociationChip {
  constructor(private readonly page: Page) {}

  get chip() {
    return this.page.getByTestId(Selectors.assocChip);
  }

  get detailSheet() {
    return this.page.getByTestId(Selectors.assocDetailSheet);
  }

  get detailName() {
    return this.page.getByTestId(Selectors.assocDetailName);
  }

  async openDetail(): Promise<void> {
    await this.chip.click();
  }
}