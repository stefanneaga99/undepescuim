import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { POST } from '@/app/api/report/route';

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
});