import { describe, expect, it, vi } from 'vitest';
import { ReportDeduper } from './report-dedupe';

describe('ReportDeduper', () => {
  it('coalesces overlapping calls and invokes create once', async () => {
    const deduper = new ReportDeduper();
    let resolve!: (value: { issueUrl: string | null }) => void;
    const create = vi.fn(() => new Promise<{ issueUrl: string | null }>((r) => { resolve = r; }));
    const first = deduper.run('same', create);
    const second = deduper.run('same', create);
    expect(create).toHaveBeenCalledOnce();
    resolve({ issueUrl: 'https://github.com/issues/1' });
    await expect(Promise.all([first, second])).resolves.toEqual([
      { issueUrl: 'https://github.com/issues/1' },
      { issueUrl: 'https://github.com/issues/1' },
    ]);
  });

  it('returns the successful result within the TTL', async () => {
    let now = 1000;
    const deduper = new ReportDeduper({ ttlMs: 60, now: () => now });
    const create = vi.fn().mockResolvedValue({ issueUrl: 'url' });
    await deduper.run('same', create);
    await expect(deduper.run('same', create)).resolves.toEqual({ issueUrl: 'url' });
    expect(create).toHaveBeenCalledOnce();
    now = 1060;
    await deduper.run('same', create);
    expect(create).toHaveBeenCalledTimes(2);
  });

  it('evicts rejected creates so retries remain possible', async () => {
    const deduper = new ReportDeduper();
    const create = vi.fn()
      .mockRejectedValueOnce(new Error('temporary'))
      .mockResolvedValueOnce({ issueUrl: null });
    await expect(deduper.run('same', create)).rejects.toThrow('temporary');
    await expect(deduper.run('same', create)).resolves.toEqual({ issueUrl: null });
    expect(create).toHaveBeenCalledTimes(2);
  });

  it('does not merge different keys', async () => {
    const deduper = new ReportDeduper();
    const create = vi.fn().mockResolvedValue({ issueUrl: null });
    await Promise.all([deduper.run('a', create), deduper.run('b', create)]);
    expect(create).toHaveBeenCalledTimes(2);
  });
});
