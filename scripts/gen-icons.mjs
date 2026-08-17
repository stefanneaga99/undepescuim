#!/usr/bin/env node
/**
 * F6 PWA light (docs/offline-pwa-feasibility.md §5): generate PWA icons from a
 * single source SVG using sharp (a Next.js dependency — no new install).
 *
 * Outputs (public/icons/):
 *   icon-192.png                192x192  regular Android/Chromium icon
 *   icon-512.png                512x512  regular high-res icon
 *   icon-512-maskable.png       512x512  purpose: maskable (glyph in the 80%
 *                                        safe zone; full-bleed bg — the OS
 *                                        rounds/crops it)
 *   apple-touch-icon-180x180.png 180x180 iOS home-screen icon (SOLID bg, no
 *                                        transparency — Apple fills alpha
 *                                        black otherwise)
 *
 * The logo: white fish glyph (the Header's lucide Fish identity) on the app's
 * near-black primary (#171717) tile with a blue accent dot — matches the
 * manifest theme_color + the in-app logo tile.
 */
import sharp from "sharp";
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const outDir = join(dirname(fileURLToPath(import.meta.url)), "..", "public", "icons");

const BG = "#171717";
const FISH = "#ffffff";
const ACCENT = "#3b82f6"; // blue accent (status dot)

/**
 * Source SVG. `radius` = background corner radius (0 = full bleed), `scale`
 * = glyph size as a fraction of the canvas (maskable needs ~0.62 to stay
 * inside the 80% safe zone; regular icons can use the full canvas).
 */
function svg({ size, radius, scale }) {
  const g = (size * scale) / 512; // glyph transform scale
  const pad = (size - 512 * g) / 2; // center the 512-box glyph
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
  <defs>
    <clipPath id="c"><rect width="${size}" height="${size}" rx="${radius}"/></clipPath>
  </defs>
  <g clip-path="url(#c)">
    <rect width="${size}" height="${size}" fill="${BG}"/>
    <!-- translate(-17 12): the fish glyph's content bbox (x≈96..450, y≈126..362)
         is off-center in the 512 design box; shift it onto the canvas center
         (applied pre-scale so the shift scales with the glyph). -->
    <g transform="translate(${pad} ${pad}) scale(${g}) translate(-17 12)">
      <!-- fish body + tail (white) -->
      <path d="M160 256 C 160 176 330 150 410 220 C 450 245 450 267 410 292 C 330 362 160 336 160 256 Z" fill="${FISH}"/>
      <path d="M160 256 L 96 172 C 128 218 128 294 96 340 Z" fill="${FISH}"/>
      <!-- eye (background-colored pupil) -->
      <circle cx="348" cy="224" r="13" fill="${BG}"/>
      <!-- top fin -->
      <path d="M280 168 L 312 126 L 342 176 Z" fill="${FISH}" opacity="0.85"/>
      <!-- blue accent bubble -->
      <circle cx="196" cy="180" r="10" fill="${ACCENT}"/>
      <circle cx="220" cy="152" r="6" fill="${ACCENT}"/>
    </g>
  </g>
</svg>`;
}

const targets = [
  { file: "icon-192.png", size: 192, radius: 43, scale: 1.0 },
  { file: "icon-512.png", size: 512, radius: 115, scale: 1.0 },
  { file: "icon-512-maskable.png", size: 512, radius: 0, scale: 0.62 },
  { file: "apple-touch-icon-180x180.png", size: 180, radius: 0, scale: 0.9 },
];

mkdirSync(outDir, { recursive: true });
for (const t of targets) {
  const out = join(outDir, t.file);
  await sharp(Buffer.from(svg(t)))
    .png({ compressionLevel: 9 })
    .toFile(out);
  const meta = await sharp(out).metadata();
  console.log(`[gen-icons] ${t.file}  ${meta.width}x${meta.height}  ${meta.format}`);
}
console.log(`[gen-icons] done -> ${outDir}`);
