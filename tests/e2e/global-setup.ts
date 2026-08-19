import type { FullConfig } from '@playwright/test';

/** Emit a bounded breadcrumb before workers start; useful when a webServer or
 * browser launch hangs without changing test timeouts or assertions. */
export default async function globalSetup(config: FullConfig): Promise<void> {
  const projects = config.projects.map(({ name }) => name).join(',');
  const outputDir = config.projects[0]?.outputDir ?? 'test-results';
  console.log(`[e2e] setup:start projects=${projects} output=${outputDir}`);
  console.log(`[e2e] setup:ready baseURL=${config.projects[0]?.use.baseURL ?? 'webServer'}`);
}