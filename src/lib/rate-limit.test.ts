import { describe, it, expect } from 'vitest';
import {
  SlidingWindowRateLimiter,
  getClientIp,
} from './rate-limit';

describe('SlidingWindowRateLimiter', () => {
  const T0 = 1_000_000;

  it('allows up to max requests per key, then blocks', () => {
    const rl = new SlidingWindowRateLimiter({ windowMs: 600_000, max: 3 });
    for (let i = 0; i < 3; i++) {
      expect(rl.check('ip-a', T0 + i * 1000)).toEqual({ allowed: true, retryAfterSec: null });
    }
    const blocked = rl.check('ip-a', T0 + 3 * 1000);
    expect(blocked.allowed).toBe(false);
    expect(blocked.retryAfterSec).toBeGreaterThan(0);
  });

  it('sliding window: old hits expire and the key can go again', () => {
    const rl = new SlidingWindowRateLimiter({ windowMs: 600_000, max: 2 });
    expect(rl.check('ip-a', T0).allowed).toBe(true);
    expect(rl.check('ip-a', T0 + 1000).allowed).toBe(true);
    expect(rl.check('ip-a', T0 + 2000).allowed).toBe(false);
    // 9 minutes later: the two original hits are still inside the 10-min window
    expect(rl.check('ip-a', T0 + 500_000).allowed).toBe(false);
    // 10+ minutes later: both expired, key is fresh again
    expect(rl.check('ip-a', T0 + 601_000).allowed).toBe(true);
  });

  it('tracks keys independently', () => {
    const rl = new SlidingWindowRateLimiter({ windowMs: 600_000, max: 1 });
    expect(rl.check('ip-a', T0).allowed).toBe(true);
    expect(rl.check('ip-a', T0 + 1).allowed).toBe(false);
    expect(rl.check('ip-b', T0 + 1).allowed).toBe(true);
  });

  it('reports a usable retryAfterSec from the oldest hit', () => {
    const rl = new SlidingWindowRateLimiter({ windowMs: 60_000, max: 1 });
    expect(rl.check('ip', T0).allowed).toBe(true);
    const blocked = rl.check('ip', T0 + 10_000);
    expect(blocked.allowed).toBe(false);
    // oldest hit was 10s ago within a 60s window -> ~50s remaining
    expect(blocked.retryAfterSec).toBe(50);
  });

  it('reset clears all state', () => {
    const rl = new SlidingWindowRateLimiter({ windowMs: 600_000, max: 1 });
    rl.check('ip', T0);
    expect(rl.size).toBe(1);
    rl.reset();
    expect(rl.size).toBe(0);
    expect(rl.check('ip', T0 + 1).allowed).toBe(true);
  });
});

describe('getClientIp', () => {
  const req = (headers: Record<string, string>) =>
    new Request('http://localhost/api/report', { method: 'POST', headers });

  it('takes the leftmost x-forwarded-for entry', () => {
    expect(getClientIp(req({ 'x-forwarded-for': '8.8.8.8, 10.0.0.1' }))).toBe('8.8.8.8');
  });

  it('falls back to x-real-ip', () => {
    expect(getClientIp(req({ 'x-real-ip': '9.9.9.9' }))).toBe('9.9.9.9');
  });

  it('falls back to a stable unknown key when no proxy headers exist', () => {
    expect(getClientIp(req({}))).toBe('unknown');
  });
});