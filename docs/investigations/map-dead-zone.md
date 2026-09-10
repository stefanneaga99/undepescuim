# Live map dead-zone investigation

Date: 2026-09-10

## Scope and baseline

- Tested the clean current `origin/main` checkout (`81f47afad31624bfd0709e8fa972b5f18eafc468`) and compared the rollback reference `e85b1f3867f87fb6ed33b3f1e73606d8e8a767b7`.
- The production hostname could not be resolved from this WSL environment (`curl: (6) Could not resolve host: undepescuim.ro`), so the reproducible before/after trace was run against a clean production build of the current application at `http://localhost:3111`.
- The diagnostic used Playwright's real `page.mouse.click(x, y)`. It did not use `force`, Leaflet `fire`, DOM `.click()`, or an any-water assertion. The report endpoint was intercepted by the existing live suite only; no report was created.

## Reproduction and result

The rollback/current app renders the same map interaction behavior. The former live test used the center of each SVG path's bounding box. For curved or dashed features this is not generally on the stroke: in the 1280x800 trace, 56 of the first 80 path bounding-box centers hit the map container or another layer rather than the sampled `leaflet-interactive` path. This is the dead-zone: a click can be swallowed without selecting a water even though the rendered stroke is visible.

The deterministic replacement samples each actual SVG path with `getPointAtLength()` at 19 fractions (0.05 through 0.95), converts with `getScreenCTM()`, verifies `document.elementFromPoint()` is in `.leaflet-overlay-pane` and has pointer events enabled, resolves the topmost hit layer's feature identity, and then dispatches a real mouse click at that screen coordinate.

| viewport | map rect | rendered paths sampled | deterministic point | hit identity | selected card | zoom before/after | console errors |
|---|---:|---:|---|---|---|---|---|
| 1280x800 | x=0,y=56,w=1280,h=744 | 80 | (476.237, 388.763) | `unc-0f0847fbf7` / Abrud | Abrud | 7 / 7 | 0 |
| 390x844 | x=0,y=222,w=390,h=622 | 80 | (31.237, 493.763) | `unc-0f0847fbf7` / Abrud | Abrud | 7 / 7 | 0 |

The mobile card opens as expected; Vaul then sets `body { pointer-events: none }` and the overlay pane becomes `pointer-events: none` while the sheet is open. That is expected modal behavior after selection, not a map dead-zone before selection. The before-click body and map were pointer-enabled.

The full machine-readable trace is `docs/investigations/map-dead-zone-trace.json`. Screenshots are in `docs/investigations/assets/`:

- `map-before-1280.png`, `map-after-1280.png`
- `map-before-390.png`, `map-after-390.png`

## Layer / hit-test inventory

At the successful click point the hit chain was:

1. `path.leaflet-interactive`, `pointer-events: auto`, `z-index: auto`, stroke `#14b8a6`.
2. parent `g`, `pointer-events: none`.
3. Leaflet animated SVG, `z-index: 200`, `pointer-events: none`.
4. `.leaflet-overlay-pane`, `z-index: 400`, `pointer-events: auto` before the card opens.
5. `.leaflet-map-pane`, `z-index: 400`, `pointer-events: auto` before the card opens.
6. `.map-touch.leaflet-container`, `z-index: 0`, `pointer-events: auto` before the card opens.

No backdrop, filter panel, or pane intercepted the deterministic pre-click point. The path's visible stroke is generally 1.5px (`#14b8a6` in the national view), which makes a box-center click particularly unreliable for a curved feature. The SVG path's bounding rectangle is not a valid click target; the rendered path geometry is.

## Before/after acceptance evidence

The corrected live suite from commit `c8c701c3f249143a31927c90cd94dad73645388f` ran against the clean local production build with the same application data:

- 8/8 passed: 4 tests at 1280x800 and 4 tests at 390x844.
- Real mouse clicks selected a named card on both viewports.
- Report POST was intercepted and returned a controlled 200 response; no external report was created.
- Report dialog z-index assertion passed.
- Theme/language and species/permit/manifest checks passed.
- No retries were used.
- `npm run build` passed before the run.

The original bounding-box-center implementation is retained in the rollback side of the diff for comparison; the minimal recommendation is the on-stroke sampler and named identity assertion in `tests/e2e/specs/live-prod.spec.ts` from `c8c701c`, not a production map-layer change.

## Data preservation hashes

The following canonical data files have identical SHA-256 values at current `origin/main` and rollback `e85b1f3`:

```text
public/data/waters.json              56380740bbc6a9f91a49b1f4f57ee8465821e9d144eaa39822e9d19d8caab7c0
public/data/associations.json        388ff8ef7efc267914d3a67a20f2f5a9230dd6bc0a0fdf9b87188b8f2fbaafa9
public/data/uncontracted_rivers.json 06414eb6c569770513c10d90d8a68d3338d7f4508ef5c7d76cb20add195db4dd
public/data/uncontracted_lakes.json  59c9b9969f3c501e06bdabc2cf33d06e4ccf1c055680169264cbce636e17f44e
public/data/association_locations.json bc54ab5ce74c07e282ac2d1f51b16247180d2d5bfd5e3389f2c11735a9c6b9a7
```

The current Class2 preview artifact is `8e5a548340d59187b5c02233889541375661f846cf9da2cb53a026bff37a4576`; it is an additive current-main artifact and was not used to select the map target. No canonical geometry, ownership, association, endpoint, legal, or ledger file was modified by this investigation.

## Recommendation

Do not change production map geometry, z-index, pointer-events, Leaflet handlers, or canonical data. Replace the bounding-box-center probe with deterministic rendered-stroke sampling, preserve the browser hit-chain check, use real mouse/touch input, assert the returned named water/sector identity, and assert zoom is unchanged across the click. This is the smallest fix that removes the test-induced false dead-zone while detecting a genuinely swallowed user click.
