# Adopting existing work

The intake protocol for Phase 1 state `assets` — the operator already has design work, and it
must be absorbed into the structure without being overwritten or silently reinterpreted.

## Contents

- The rule
- Step 1 — Inventory
- Step 2 — Classify
- Step 3 — Extract tokens
- Step 4 — Place
- Step 5 — Report
- Reverse-engineering a palette
- Common intake sources

## The rule

**The operator's existing work is ground truth; the structure bends to it.** Never rename,
recolour, redraw, or "improve" an incoming asset during intake. Intake is placement and
extraction only. Improvements are a separate, proposed, A–E round afterwards.

Never delete or overwrite an incoming file. Copy into the structure, leave the original in
place, and list the originals in the report so the operator can remove them deliberately.

## Step 1 — Inventory

List everything design-ish before touching anything:

```bash
find . -path ./node_modules -prune -o \
  \( -iname '*.svg' -o -iname '*.png' -o -iname '*.ai' -o -iname '*.sketch' \
     -o -iname '*.fig' -o -iname '*.penpot' -o -iname '*.pdf' \
     -o -iname '*token*.json' -o -iname 'tailwind.config.*' -o -iname '*.css' \
     -o -iname '*theme*' -o -iname '*brand*' -o -iname '*logo*' -o -iname '*icon*' \) -print
```

Also check: `assets/`, `public/`, `static/`, `Assets.xcassets/`, `res/mipmap-*/`,
`res/values/colors.xml`, any `*.styleguide`/`*.md` that reads like a brand doc, and the
README for brand links.

## Step 2 — Classify

Sort the inventory into: **brand** (logos, marks, wordmarks) · **app icons** (launcher/store)
· **UI icons** · **tokens/palette** (any file with colour values) · **components** (existing
code or specs) · **screens/mocks** (exports, PDFs) · **UX docs** (stories, flows, research) ·
**unknown**. Put the unknowns in the report rather than guessing.

## Step 3 — Extract tokens

The highest-value step: turn whatever holds the colours into real tokens.

- `tailwind.config.*` → `theme.extend.colors` is usually already a ramp; map it to
  `color.palette.*` primitives, then write semantic tokens on top.
- CSS/SCSS variables → group by prefix; a `--brand-*` / `--gray-*` split is a ramp in disguise.
- `res/values/colors.xml` + `values-night/` → the second file **is** the dark theme; this is
  the cheapest dark theme you will ever get.
- `Assets.xcassets/*.colorset` → `Any`/`Dark` appearances map to the two themes.
- A `*.tokens.json` already in DTCG → use as-is; only add the missing tiers.
- Nothing but a logo → sample the logo's colours as the accent family and build the ramps
  around them (see below).

Preserve the operator's existing *names* where they are already intent-named. Rename only raw
appearance names (`blue-500` → stays as a primitive; a new semantic token points at it).

## Step 4 — Place

Scaffold the structure, then copy assets in:

```bash
python3 scripts/scaffold_design.py --name "<Product>" --dest . --adopt
```

`--adopt` creates the tree and token stubs but **does not** write placeholder brand or icon
files, so nothing can shadow a real asset. Then place: logos → `brand/logo/` (renamed to the
contract names, originals untouched), the best launcher-icon source → `icons/app/master.svg`
(if only raster exists, note it — rasters cannot be cleanly upscaled to 1024), UI icons →
`icons/ui/`, mocks → `handoff/exports/`, UX docs → `ux/`.

## Step 5 — Report

Report back in three lists, explicitly separated:

1. **Found and placed** — file → new path.
2. **Inferred** — anything you derived rather than read: extracted ramps, a dark theme built
   by lightness inversion, a mark cropped from a lockup. Each needs operator confirmation.
3. **Missing against the non-negotiables** — the gaps (no dark theme, no monochrome Android
   layer, no favicon-safe mark, no UI kit), each with the cost of closing it.

Then propose the first round. Do not start designing until the operator has confirmed list 2.

## Reverse-engineering a palette

When the only input is a logo or a screenshot:

1. Pull the distinct colours (for a screenshot, quantize and drop near-duplicates).
2. The most saturated colour that is not pure black/white is the accent anchor; the most
   frequent near-neutral is the neutral anchor.
3. Build 11-step ramps around each anchor by stepping lightness in OKLCH, holding hue and
   chroma.
4. Derive semantic tokens from the ramps, build the dark theme properly (see
   [brand-and-tokens.md](brand-and-tokens.md) — not by inverting lightness).
5. Mark the whole palette as **inferred** in the report. It is a starting point to be
   confirmed, not a decision.

## Common intake sources

| Source | What you can get | Watch out for |
| --- | --- | --- |
| Figma/Penpot export (SVG/PNG) | layout, type scale, spacing | exports lose variants/states; re-spec, don't trace |
| `tailwind.config.js` | the full palette + spacing + radii, nearly token-shaped | defaults bleed in — keep only what the product uses |
| Existing React/Flutter app | components, states, real content lengths | hardcoded hexes everywhere; extract, then tokenize |
| `Assets.xcassets` / `res/` | app icons, per-theme colours | raster-only app icons may be unusable at 1024 |
| A PDF brand book | positioning, voice, logo rules, clear space | usually outdated; confirm what still holds |
| A single logo file | the accent anchor | a lockup is not a favicon mark; one must be designed |
