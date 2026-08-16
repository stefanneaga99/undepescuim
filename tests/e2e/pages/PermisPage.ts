/**
 * POM — /permis page (2026 permit & rules guide). Docs/e2e-test-plan.md §4.3.
 */
import type { Page } from '@playwright/test';

export class PermisPage {
  constructor(private readonly page: Page) {}

  get h1() {
    return this.page.getByRole('heading', { name: /Permis.*Reguli 2026/ });
  }

  get backLink() {
    return this.page.getByRole('link', { name: 'Înapoi la hartă' });
  }

  get portalLink() {
    return this.page.getByRole('link', { name: /Deschide portalul de permise/ });
  }

  get speciiCrossLink() {
    return this.page.getByRole('link', { name: /Vezi dimensiunile minime pe specii/ });
  }
}