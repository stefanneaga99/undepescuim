/**
 * POM — nearby waters sheet (mobile vaul drawer / desktop floating panel).
 * Docs/e2e-test-plan.md §4.3. The container already exposes
 * `data-nearby-sheet`; rows carry `data-testid="nearby-row"`.
 */
import type { Page } from '@playwright/test';
import { Selectors } from '../helpers/selectors';

export class NearbyWatersSheet {
  constructor(private readonly page: Page) {}

  get sheet() {
    return this.page.getByTestId(Selectors.nearbySheet);
  }

  get rows() {
    return this.sheet.getByTestId(Selectors.nearbyRow);
  }

  row(name: string) {
    return this.rows.filter({ hasText: name });
  }

  async openRow(name: string): Promise<void> {
    // vaul translate / body pointer-events on compact — evaluate-click (same
    // rationale as WaterDetailCard).
    await this.row(name).evaluate((el) => (el as HTMLButtonElement).click());
  }
}