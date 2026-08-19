/**
 * POM — report dialog (Radix Dialog portal). Docs/e2e-test-plan.md §4.3.
 * Reasons carry data-testid="report-reason" + data-value.
 */
import type { Page } from '@playwright/test';
import { Selectors } from '../helpers/selectors';

export class ReportDialog {
  constructor(private readonly page: Page) {}

  get dialog() {
    return this.page.getByTestId(Selectors.reportDialog);
  }

  reason(value: string) {
    return this.dialog
      .getByTestId(Selectors.reportReason)
      .and(this.page.locator(`[data-value="${value}"]`));
  }

  get submitButton() {
    return this.dialog.getByRole('button', { name: /Trimite raportul/ });
  }

  get cancelButton() {
    // Dismiss-only report controls intentionally use the neutral close label.
    return this.dialog.getByRole('button', { name: 'Închide' });
  }

  get details() {
    return this.dialog.getByLabel('Detalii (opțional)');
  }

  get email() {
    return this.dialog.getByLabel(/Email/);
  }

  get successText() {
    return this.dialog.getByText('Mulțumim! Raportul a fost trimis.');
  }

  get githubLink() {
    return this.dialog.getByRole('link', { name: 'Vezi raportul pe GitHub' });
  }

  get errorText() {
    return this.dialog.getByRole('alert');
  }

  async pickReason(value: string): Promise<void> {
    await this.reason(value).locator('input').check({ force: true });
  }

  async submit(): Promise<void> {
    await this.submitButton.click();
  }
}