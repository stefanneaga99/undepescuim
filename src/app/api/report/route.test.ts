import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { POST } from '@/app/api/report/route';
import { resetReportDeduper } from '@/lib/report-dedupe';
import { resetReportRateLimiter } from '@/lib/rate-limit';

// The route reads process.env.REPORT_GITHUB_TOKEN at request time.
const REAL_TOKEN = process.env.REPORT_GITHUB_TOKEN;

function request(body: unknown): Request {
  return new Request('http://localhost/api/report', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  });
}

function githubResponse(ok: boolean, status: number, body: { html_url?: string }) {
  return {
    ok,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as Response;
}

beforeEach(() => {
  vi.restoreAllMocks();
  resetReportDeduper();
  resetReportRateLimiter();
});

afterEach(() => {
  vi.unstubAllGlobals();
  if (REAL_TOKEN === undefined) delete process.env.REPORT_GITHUB_TOKEN;
  else process.env.REPORT_GITHUB_TOKEN = REAL_TOKEN;
});

describe('POST /api/report', () => {
  it('400 invalid_json for a malformed body', async () => {
    const res = await POST(new Request('http://localhost/api/report', { method: 'POST', body: '{nope' }));
    expect(res.status).toBe(400);
    expect(await res.json()).toMatchObject({ ok: false, error: 'invalid_json' });
  });

  it('400 invalid_reason for an unknown reason', async () => {
    const res = await POST(request({ waterSlug: 'x', waterName: 'y', reason: 'nonsense' }));
    expect(res.status).toBe(400);
    expect(await res.json()).toMatchObject({ error: 'invalid_reason' });
  });

  it('400 missing_water without a slug or name', async () => {
    const res = await POST(request({ reason: 'other' }));
    expect(res.status).toBe(400);
    expect(await res.json()).toMatchObject({ error: 'missing_water' });
  });

  it('silently drops honeypot submissions (bots filling `website`)', async () => {
    const res = await POST(request({ waterSlug: 'x', waterName: 'y', reason: 'other', website: 'spam.example' }));
    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true, issueUrl: null });
  });

  it('503 not_configured without REPORT_GITHUB_TOKEN', async () => {
    delete process.env.REPORT_GITHUB_TOKEN;
    const res = await POST(request({ waterSlug: 'x', waterName: 'y', reason: 'other' }));
    expect(res.status).toBe(503);
    expect(await res.json()).toMatchObject({ error: 'not_configured' });
  });

  it('502 github_error when GitHub returns a non-OK status', async () => {
    process.env.REPORT_GITHUB_TOKEN = 'ghp_test';
    const fetchMock = vi.fn().mockResolvedValue(githubResponse(false, 422, {}));
    vi.stubGlobal('fetch', fetchMock);
    const res = await POST(request({ waterSlug: 'x', waterName: 'y', reason: 'other' }));
    expect(res.status).toBe(502);
    expect(await res.json()).toMatchObject({ error: 'github_error' });
  });

  it('200 with issueUrl on success, sending a Bearer token + report payload', async () => {
    process.env.REPORT_GITHUB_TOKEN = 'ghp_test';
    const fetchMock = vi.fn().mockResolvedValue(githubResponse(true, 201, { html_url: 'https://github.com/neagastefan99/undepescuim/issues/1' }));
    vi.stubGlobal('fetch', fetchMock);

    const res = await POST(request({
      waterSlug: 'raul-buzau',
      waterName: 'Râul Buzău',
      reason: 'wrong_coordinates',
      details: 'Mouth is further south',
      contactEmail: 'fisher@example.ro',
    }));

    expect(res.status).toBe(200);
    expect(await res.json()).toEqual({ ok: true, issueUrl: 'https://github.com/neagastefan99/undepescuim/issues/1' });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('https://api.github.com/repos/neagastefan99/undepescuim/issues');
    const headers = init.headers as Record<string, string>;
    // Guards the Authorization header — it MUST be a real Bearer token, not a
    // redaction artifact (a previous write persisted '*** ${token}' here,
    // which would 401 every report).
    expect(headers.Authorization).toBe('Bearer ghp_test');
    const sent = JSON.parse(init.body as string);
    expect(sent.title).toContain('Râul Buzău');
    expect(sent.labels).toEqual(['report']);
  });

  it('sanitizes matching context and drops stale A→B context', async () => {
    process.env.REPORT_GITHUB_TOKEN = 'ghp_test';
    const fetchMock = vi.fn().mockResolvedValue(githubResponse(true, 201, { html_url: 'https://github.com/issues/context' }));
    vi.stubGlobal('fetch', fetchMock);
    const context = { schemaVersion: 1, captureVersion: 'map-report-context-v1', subject: { water: { slug: 'b', name: 'B' }, selection: { selectedWaterSlug: 'b', segment: null, associationSlug: null, contractRef: null } }, map: null, filters: { counties: [], localities: [], waterType: 'all', contractStatus: 'all', selectedAssociationSlug: null }, page: { pathname: '/' }, client: { formFactor: 'desktop' }, provenance: { appVersion: null, dataUpdatedAt: null, gitSha: null }, consent: { approximateMap: true, preciseLocation: false, screenshot: false } };
    await POST(request({ waterSlug: 'b', waterName: 'B', reason: 'other', reportContext: context }));
    const sent = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
    expect(sent.body).toContain('Context hartă');
    resetReportDeduper();
    fetchMock.mockClear();
    await POST(request({ waterSlug: 'b', waterName: 'B', reason: 'other', reportContext: { ...context, subject: { ...context.subject, water: { slug: 'a', name: 'A' }, selection: { ...context.subject.selection, selectedWaterSlug: 'a' } } } }));
    const staleSent = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
    expect(staleSent.body).toContain('nepartajat');
    expect(staleSent.body).not.toContain('— A');
  });

  it('coalesces overlapping identical requests into one GitHub issue', async () => {
    process.env.REPORT_GITHUB_TOKEN = 'ghp_test';
    let resolve!: (response: Response) => void;
    const fetchMock = vi.fn(() => new Promise<Response>((r) => { resolve = r; }));
    vi.stubGlobal('fetch', fetchMock);
    const payload = { waterSlug: 'same', waterName: 'Same', reason: 'other', details: 'A' };
    const first = POST(request(payload));
    const second = POST(request(payload));
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalledOnce());
    resolve(githubResponse(true, 201, { html_url: 'https://github.com/issues/2' }));
    const responses = await Promise.all([first, second]);
    for (const res of responses) {
      expect(res.status).toBe(200);
      await expect(res.json()).resolves.toEqual({ ok: true, issueUrl: 'https://github.com/issues/2' });
    }
  });

  it('returns the cached URL for a sequential identical retry', async () => {
    process.env.REPORT_GITHUB_TOKEN = 'ghp_test';
    const fetchMock = vi.fn().mockResolvedValue(githubResponse(true, 201, { html_url: 'https://github.com/issues/3' }));
    vi.stubGlobal('fetch', fetchMock);
    const payload = { waterSlug: 'same', waterName: 'Same', reason: 'other' };
    await POST(request(payload));
    const retry = await POST(request(payload));
    expect(retry.status).toBe(200);
    expect(await retry.json()).toEqual({ ok: true, issueUrl: 'https://github.com/issues/3' });
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it('does not merge reports with different details', async () => {
    process.env.REPORT_GITHUB_TOKEN = 'ghp_test';
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(githubResponse(true, 201, { html_url: 'https://github.com/issues/4' }))
      .mockResolvedValueOnce(githubResponse(true, 201, { html_url: 'https://github.com/issues/5' }));
    vi.stubGlobal('fetch', fetchMock);
    const base = { waterSlug: 'same', waterName: 'Same', reason: 'other' };
    await POST(request({ ...base, details: 'A' }));
    await POST(request({ ...base, details: 'B' }));
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});