/**
 * REM-1: in-memory per-key (per-IP) sliding-window rate limiter.
 *
 * Purpose: stop a scripted loop from flooding POST /api/report (spam issue
 * creation + burning the GitHub token's API quota).
 *
 * Serverless caveat: Vercel function instances are ephemeral and each has its
 * own memory — this limiter is PER-INSTANCE, not global. It still stops a
 * single warm instance being hammered by the same IP, but a determined
 * attacker can fan out across instances or rotate IPs. It is a cheap first
 * line of defense; the hardening path if spam materializes is a durable store
 * (Vercel KV / Upstash) or a Vercel WAF rate-limit rule. See
 * docs/security-test-plan.md REM-1.
 */

export interface RateLimiterOptions {
  /** Sliding window length in milliseconds. Default 10 minutes. */
  windowMs?: number;
  /** Max requests per key per window. Default 5. */
  max?: number;
  /** Opportunistic purge once the key map grows past this size. Default 10k. */
  maxKeys?: number;
}

export interface RateLimitResult {
  allowed: boolean;
  /** Seconds the client should wait before retrying (null when allowed). */
  retryAfterSec: number | null;
}

export class SlidingWindowRateLimiter {
  private readonly hits = new Map<string, number[]>();
  private readonly windowMs: number;
  private readonly max: number;
  private readonly maxKeys: number;

  constructor(opts: RateLimiterOptions = {}) {
    this.windowMs = opts.windowMs ?? 10 * 60 * 1000;
    this.max = opts.max ?? 5;
    this.maxKeys = opts.maxKeys ?? 10_000;
  }

  /** Record a hit (or reject one) for `key`, sliding-window style.
   *  `now` is injectable for deterministic tests. */
  check(key: string, now: number = Date.now()): RateLimitResult {
    const cutoff = now - this.windowMs;
    const timestamps = (this.hits.get(key) ?? []).filter((t) => t > cutoff);

    if (timestamps.length >= this.max) {
      // Already at the cap: keep the window (TTL) so retryAfter is accurate.
      this.hits.set(key, timestamps);
      const oldest = timestamps[0];
      return {
        allowed: false,
        retryAfterSec: Math.max(1, Math.ceil((this.windowMs - (now - oldest)) / 1000)),
      };
    }

    timestamps.push(now);
    this.hits.set(key, timestamps);

    // Opportunistic purge so a hostile many-IP sweep can't grow the map forever.
    if (this.hits.size > this.maxKeys) {
      for (const [k, ts] of this.hits) {
        if (ts.length === 0 || ts[ts.length - 1] <= cutoff) this.hits.delete(k);
      }
    }

    return { allowed: true, retryAfterSec: null };
  }

  /** Clear all state (tests / hot reloads). */
  reset(): void {
    this.hits.clear();
  }

  /** Number of tracked keys (tests / observability). */
  get size(): number {
    return this.hits.size;
  }
}

/**
 * Resolve the client IP from the usual proxy headers. Vercel populates
 * `x-forwarded-for` with the real client IP (leftmost entry). Falls back to
 * `x-real-ip`, then a stable placeholder so requesters without proxy headers
 * still share a usable key.
 */
export function getClientIp(request: Request): string {
  const xff = request.headers.get('x-forwarded-for');
  if (xff) {
    const first = xff.split(',')[0]?.trim();
    if (first) return first;
  }
  const realIp = request.headers.get('x-real-ip');
  if (realIp) return realIp;
  return 'unknown';
}

/** Shared limiter for the report endpoint: ~5 requests / 10 min per IP. */
export const reportRateLimiter = new SlidingWindowRateLimiter({
  windowMs: 10 * 60 * 1000,
  max: 5,
});

/** Test hook: clear the shared limiter so suites start from a clean state. */
export function resetReportRateLimiter(): void {
  reportRateLimiter.reset();
}