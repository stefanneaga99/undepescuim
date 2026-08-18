/**
 * Short-lived in-memory coalescing for semantically identical reports.
 *
 * Like the report rate limiter, this singleton is per warm server instance,
 * not a durable or cross-instance exactly-once guarantee.
 */

export interface ReportDedupeOptions {
  ttlMs?: number;
  now?: () => number;
}

type ReportResult = { issueUrl: string | null };
type Completed = ReportResult & { expiresAt: number };

const DEFAULT_TTL_MS = 60_000;

export class ReportDeduper {
  private readonly pending = new Map<string, Promise<ReportResult>>();
  private readonly completed = new Map<string, Completed>();
  private readonly ttlMs: number;
  private readonly now: () => number;

  constructor(options: ReportDedupeOptions = {}) {
    this.ttlMs = options.ttlMs ?? DEFAULT_TTL_MS;
    this.now = options.now ?? Date.now;
  }

  async run(key: string, create: () => Promise<ReportResult>): Promise<ReportResult> {
    const now = this.now();
    const cached = this.completed.get(key);
    if (cached) {
      if (now < cached.expiresAt) return { issueUrl: cached.issueUrl };
      this.completed.delete(key);
    }

    const existing = this.pending.get(key);
    if (existing) return existing;

    let promise: Promise<ReportResult>;
    try {
      promise = Promise.resolve(create());
    } catch (error) {
      promise = Promise.reject(error);
    }
    this.pending.set(key, promise);

    try {
      const result = await promise;
      this.completed.set(key, { issueUrl: result.issueUrl, expiresAt: this.now() + this.ttlMs });
      return result;
    } finally {
      if (this.pending.get(key) === promise) this.pending.delete(key);
    }
  }

  reset(): void {
    this.pending.clear();
    this.completed.clear();
  }
}

export const reportDeduper = new ReportDeduper();

export function resetReportDeduper(): void {
  reportDeduper.reset();
}
