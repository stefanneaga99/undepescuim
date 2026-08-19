import type { FullResult, Reporter, TestCase, TestResult } from '@playwright/test/reporter';

/** Small CI breadcrumb reporter: identify the project/test that starts or
 * stalls without writing a shared log file from parallel workers. */
class LifecycleReporter implements Reporter {
  onBegin(): void {
    console.log(`[e2e] run:start ${new Date().toISOString()}`);
  }

  onTestBegin(test: TestCase, result: TestResult): void {
    console.log(`[e2e] test:start project=${test.parent.project()?.name ?? 'unknown'} worker=${result.workerIndex} title=${test.title}`);
  }

  onTestEnd(test: TestCase, result: TestResult): void {
    console.log(`[e2e] test:end project=${test.parent.project()?.name ?? 'unknown'} worker=${result.workerIndex} status=${result.status} duration_ms=${result.duration} title=${test.title}`);
  }

  onEnd(result: FullResult): void {
    console.log(`[e2e] run:end status=${result.status} ${new Date().toISOString()}`);
  }
}

export default LifecycleReporter;