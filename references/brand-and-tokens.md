# Brand and tokens

What the brand kit must contain, and the token architecture everything else binds to.

## Contents

- Brand kit contents
- Token tiers
- Naming
- Colour: building the ramps
- Themes (light + dark)
- Type scale
- Space, size, radius
- Motion tokens
- Elevation / shadow
- DTCG format

## Brand kit contents

`brand/brand.md` is written before any pixel and answers, in one page:

- **Positioning** — one sentence: for *whom*, what it does, why it is different.
- **Personality** — 3–5 adjectives, each with an "and not" ( "confident, *not* loud" ).
  Adjectives without an "and not" are decoration; they constrain nothing.
- **Voice & tone** — how the product talks in success, in error, in empty states. Include
  3 real microcopy examples, not rules in the abstract.
- **Do / don't** — the five misuses most likely to happen.

The logo set (`brand/logo/`) is five SVGs, minimum: primary lockup, inverse lockup, mono
(`fill="currentColor"`, no hardcoded colour), wordmark, and **mark** — the standalone glyph
that survives at 16px. Every SVG has a `viewBox`, no embedded raster, no text elements
(outline the type), and no `<style>` blocks.

## Token tiers

Two tiers are the default; add the third only when a semantic token has become too broad to
name honestly.

| Tier | File | Contains | Referenced by |
| --- | --- | --- | --- |
| 1 Primitive | `primitives.tokens.json` | raw ramps — `color.palette.*`, `space.*`, `size.*`, `radius.*`, `font.*`, `duration.*`, `easing.*` | semantic tokens only |
| 2 Semantic | `semantic.tokens.json` | intent — `color.bg.*`, `color.fg.*`, `color.border.*`, `color.accent.*`, `color.status.*`, `space.inset.*`, `text.*` | components, screens, code |
| 3 Component | `components.tokens.json` | `button.primary.bg.hover` where tier 2 cannot express it | that component only |

**Never let a component or a screen reference a tier-1 token.** That is the rule the whole
architecture exists to enforce; breaking it makes theming impossible. A primitive referenced
directly in a component spec is a defect `check_design.py` reports.

## Naming

Dot-path, kebab-case segments, intent before appearance:

```
color.bg.canvas            color.fg.default        color.border.subtle
color.bg.surface           color.fg.muted          color.border.strong
color.bg.surface-raised    color.fg.on-accent      color.border.focus
color.accent.default       color.status.success    space.inset.md
color.accent.hover         color.status.warning    text.body.md
color.accent.subtle        color.status.danger     radius.control
```

`color.accent.*` rather than `color.brand-blue.*`: a rebrand should change values, not names.

## Colour: building the ramps

Start from the brand's anchor colour and build an 11-step ramp (`50, 100, 200 … 900, 950`)
per hue family. Minimum families: `neutral` (the workhorse — 12+ steps, slightly tinted
toward the brand hue), `accent`, `success`, `warning`, `danger`. Add `info` only if the
product distinguishes it from accent.

Build ramps in a perceptual space (OKLCH) so steps look evenly spaced: hold chroma and hue,
step lightness. Then **check the pairs you actually use**, not the ramp in the abstract —
`check_design.py` computes every semantic fg/bg pair in both themes.

Targets: body text ≥ 4.5:1, large text (≥24px, or ≥18.66px bold) and UI borders/icons that
carry meaning ≥ 3:1. Focus indicators ≥ 3:1 against both the component and the background.

## Themes (light + dark)

A theme is a **second set of values for the same semantic names**. Never a second stylesheet.

```json
"color": { "bg": { "canvas": {
  "$type": "color",
  "$value": "{color.palette.neutral.0}",
  "$extensions": { "themes": { "dark": "{color.palette.neutral.950}" } }
}}}
```

Dark-theme rules that are not symmetric with light:

- Do not invert. Pure `#000` canvas plus pure `#fff` text causes halation; use `neutral.950`
  / `neutral.100`.
- Elevation reads as **lighter surfaces**, not bigger shadows — shadows are nearly invisible
  on dark. `surface` and `surface-raised` must differ by enough lightness to be visible.
- Saturated brand colours vibrate on dark backgrounds. Dark-theme accent is usually a
  *lighter, less saturated* step (e.g. `accent.400` instead of `accent.600`).
- Images and illustrations need a dark-theme treatment or a neutral backplate.

## Type scale

Pick at most two families (display + text; a mono third only if the product shows code).
Record for each: source (Google Fonts / licensed / system stack), weights actually used, and
the fallback stack. A font with no licence note is a legal defect.

Scale: a modular ramp (1.200 or 1.250) across `text.display.lg … text.body.sm …
text.caption`. Each entry is a composite token carrying `fontFamily`, `fontSize`,
`lineHeight`, `letterSpacing`, `fontWeight` — not a bare size. Line height ≥ 1.4 for body
copy; tighter only for display sizes.

## Space, size, radius

One 4px-based space scale (`space.0 … space.24`), used for *everything* — padding, gaps,
margins. `size.*` is for control heights and icon sizes (min touch target 44pt iOS / 48dp
Android / 24px web pointer). `radius.*` is named by role (`radius.control`, `radius.surface`,
`radius.pill`, `radius.full`), not by pixel value, so the whole product's roundness changes
in one edit.

## Motion tokens

Animation is part of the design system, not decoration added later:

```
duration.instant 80ms · duration.fast 160ms · duration.base 240ms · duration.slow 400ms
easing.standard cubic-bezier(.2,0,0,1)   — most transitions
easing.decelerate cubic-bezier(0,0,0,1)  — entering
easing.accelerate cubic-bezier(.3,0,1,1) — exiting
easing.emphasized cubic-bezier(.2,0,0,1) — large/hero movement
```

Every animation in the prototype uses these tokens, and every one of them respects
`prefers-reduced-motion: reduce` (cut to opacity, or to `duration.instant`).

## Elevation / shadow

Define 4–5 levels mapped to meaning (`elevation.flat`, `.raised`, `.overlay`, `.modal`,
`.popover`), each a composite of shadow(s) plus — for dark theme — the surface step that
carries the elevation instead.

## DTCG format

Use the W3C Design Tokens Community Group JSON format: `$type`, `$value`, `$description`, and
`{dot.path}` aliases. It is what `build_tokens.py` consumes and what Figma/Penpot/Style
Dictionary import. Group names are the dot path; do not invent a parallel flat key format.
