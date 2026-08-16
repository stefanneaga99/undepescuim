import { describe, it, expect } from 'vitest';
import {
  sanitizeWaterName,
  sanitizeSlug,
  fenceDetails,
  neutralizeInline,
  stripControl,
} from './sanitize';

describe('sanitizeWaterName', () => {
  it('keeps letters (incl. diacritics), digits, space, dot and dash', () => {
    expect(sanitizeWaterName('Bâsca Mare 2')).toBe('Bâsca Mare 2');
    expect(sanitizeWaterName('Râul Someșul-Cald')).toBe('Râul Someșul-Cald');
    expect(sanitizeWaterName('Lacul Sf. Ana')).toBe('Lacul Sf. Ana');
  });

  it('strips markdown-active characters from the issue title', () => {
    expect(sanitizeWaterName('@ghost #123 ![x](https://evil/px.png) <b>Bold</b>')).toBe(
      'ghost 123 xhttpsevilpx.png bBoldb',
    );
  });

  it('collapses whitespace and trims', () => {
    expect(sanitizeWaterName('  Someșul\n  Rece  ')).toBe('Someșul Rece');
  });

  it('truncates to MAX_WATER_NAME chars', () => {
    const long = 'A'.repeat(500);
    expect(sanitizeWaterName(long)).toHaveLength(128);
  });

  it('never yields an empty title fragment for pure-symbol input', () => {
    expect(sanitizeWaterName('###')).toBe('');
  });
});

describe('sanitizeSlug', () => {
  it('keeps slug-safe characters and strips the rest', () => {
    expect(sanitizeSlug('raul-somesu-mare')).toBe('raul-somesu-mare');
    expect(sanitizeSlug('`evil`;#123')).toBe('evil123');
  });
});

describe('fenceDetails', () => {
  it('wraps details in a fenced code block', () => {
    expect(fenceDetails('a line')).toBe('```\na line\n```');
  });

  it('preserves markdown verbatim INSIDE the fence (@mention becomes inert)', () => {
    const md = '@someuser #123 ![x](https://attacker.example/px.png) [ ] task';
    const out = fenceDetails(md);
    expect(out).toContain(md);
    expect(out.startsWith('```')).toBe(true);
    expect(out.endsWith('```')).toBe(true);
  });

  it('lengthens the fence when the text contains backticks (no breakout)', () => {
    const md = 'before ```\nevil\n``` after';
    const out = fenceDetails(md);
    expect(out.startsWith('````')).toBe(true); // 4-backtick fence beats the 3-run
    expect(out).toContain('```\nevil\n```'); // the user fence is now inert content
  });

  it('returns a placeholder for empty input', () => {
    expect(fenceDetails('   ')).toBe('_(nespecificat)_');
  });

  it('truncates to MAX_DETAILS chars', () => {
    expect(fenceDetails('A'.repeat(5000))).toHaveLength(2000 + 8); // 2000 + 2 fences + 2 newlines
  });
});

describe('neutralizeInline', () => {
  it('escapes leading heading markers', () => {
    expect(neutralizeInline('# Title\n## Sub')).toBe('\\# Title\n\\#\\# Sub');
  });

  it('escapes leading @mentions', () => {
    expect(neutralizeInline('@maintainer hi')).toBe('\\@maintainer hi');
  });

  it('escapes leading image syntax', () => {
    expect(neutralizeInline('![px](https://evil/1.png)')).toBe('!\\[px](https://evil/1.png)');
  });

  it('escapes leading blockquote markers', () => {
    expect(neutralizeInline('> quoted')).toBe('\\> quoted');
    expect(neutralizeInline('>> nested')).toBe('\\>\\> nested');
  });

  it('does not touch mid-line characters (the fence handles those)', () => {
    expect(neutralizeInline('say @user hi')).toBe('say @user hi');
  });
});

describe('stripControl', () => {
  it('removes control characters including newlines', () => {
    expect(stripControl('a@b.com\n@mention')).toBe('a@b.com@mention');
    expect(stripControl('ok\x00\x1f')).toBe('ok');
  });
});