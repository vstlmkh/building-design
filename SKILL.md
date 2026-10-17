---
name: building-design
description: >
  Use when the operator wants to build a product design system from scratch or extend an
  existing one — brand, logo and app-icon packs (web favicon/PWA, iOS, Android adaptive),
  design tokens, a UI kit with light and dark themes, user stories and flows, screens,
  banners, landing pages — stored in a git repo that teammates and AI coding agents can
  consume to reproduce the design exactly in an app or website. Scaffolds a `design/`
  workspace when none exists, adopts the operator's existing assets, keeps a runnable
  zero-install interactive prototype as the source of visual truth, and always answers a
  design request with several labelled options (A–E) before the operator picks one. Triggers
  on "design system", "brand kit", "app icon pack", "UI kit", "dark theme", "make a
  banner/screen", "design handoff for agents", and Russian equivalents ("дизайн-система",
  "сделай дизайн", "брендбук", "иконки приложения", "тёмная тема"). Not for code
  architecture reviews or one-off Figma/Penpot edits.
license: MIT
metadata:
  version: "0.1.0"
---

# building-design

Build and grow a product's design as a **versioned, runnable artifact** in a git repo, not as
a pile of images. The deliverable is a `design/` workspace whose single source of visual truth
is a zero-install interactive prototype any teammate can open locally, backed by DTCG design
tokens, a UI kit, icon packs for every platform, and UX artifacts (stories, flows, screen
specs) — structured so an AI coding agent can reimplement it pixel-for-pixel in Flutter,
SwiftUI, Compose, or the web.

Related but different: `building-ui-ux` designs *inside* a design tool (Penpot MCP) for one
screen or flow. This skill owns the **repo-resident design system and its lifecycle**. When a
Penpot/Figma MCP is connected and the operator wants to work in that canvas, use the other
skill and store its exports here.

## Contents

- Non-negotiables
- Workflow (Phases 0–6)
- The A–E rule
- Gotchas
- Scripts
- References

## Non-negotiables

Every design this skill produces reaches `design/` complete. These are not aspirations —
`scripts/check_design.py` fails the build when one is missing.

1. **Brand** — `design/brand/brand.md` with positioning, personality, voice, and the logo set
   (primary, monochrome, wordmark, favicon-safe mark) as SVG.
2. **Icon packs for all three platforms** — web (favicon + PWA + maskable), iOS (store/outer
   icon + in-app icon set, incl. dark and tinted variants), Android (adaptive outer icon with
   foreground/background/monochrome + Play listing + in-app icon set). Outer = the launcher /
   store icon; inner = icons used inside the product.
3. **UI kit in brand colors** — every component with all states (default, hover, focus-visible,
   active, disabled, loading, error) and all sizes, bound to semantic tokens.
4. **Light and dark themes** — both, always, both contrast-checked. A design shipped in one
   theme only is incomplete.
5. **Runnable prototype** — `design/prototype/` runs with one command, no npm install, with
   real animations and interactions.

## Workflow

Copy this checklist into the session and tick each phase.

```
Design cycle:
- [ ] Phase 0 — Survey: detect an existing design workspace / loose design assets
- [ ] Phase 1 — Adopt or scaffold: intake existing work, or create design/ from scratch
- [ ] Phase 2 — Clarify: analyze the operator's prompt, ask only the unanswered questions
- [ ] Phase 3 — Ground in UX: user stories + flow + screen inventory for anything interactive
- [ ] Phase 4 — Variants: produce A–E genuinely different options, rendered in the prototype
- [ ] Phase 5 — Verify: operator picks/edits; loop 4↔5 until approved; check_design.py passes
- [ ] Phase 6 — Land: commit into the structure, update tokens/UI kit/prototype/handoff docs
```

**Phase 0 — Survey.** Before anything else, look for design that already exists:

```bash
python3 scripts/check_design.py --survey .
```

It reports one of three states: `workspace` (a `design/` with `design.config.json` — read it
and continue the existing system), `assets` (loose design files — logos, SVGs, Figma/Penpot
exports, a `tokens.json`, a `tailwind.config`, stylesheets with a palette), or `empty`.
Never create a second design system next to an existing one; extend what is there.

**Phase 1 — Adopt or scaffold.**
- State `empty` → propose the structure to the operator (show the tree from
  [references/repo-structure.md](references/repo-structure.md)), get a yes, then
  `python3 scripts/scaffold_design.py --name "<Product>" --dest .`
- State `assets` → do **not** overwrite. Run the intake in
  [references/adopting-existing.md](references/adopting-existing.md): inventory → classify →
  extract tokens from what exists → place into the structure → report what was inferred vs
  found. The operator's existing work is the ground truth; the structure bends to it.
- State `workspace` → read `design.config.json`, `brand/brand.md`, and the token files, then
  continue in the system's established conventions.

**Phase 2 — Clarify.** Analyze the prompt and name what it leaves open — audience, platform,
tone, constraints, required content, where it lives in the product. Ask the **unanswered**
questions only, in one batch, max five, each with a recommended default so the operator can
answer "defaults are fine." Do not ask what the repo already answers. In a non-interactive
run, adopt the defaults and state them explicitly.

**Phase 3 — Ground in UX.** For anything a user interacts with (screen, flow, feature, page —
not a standalone logo or banner), write or update the UX artifacts **before** pixels: user
stories with acceptance criteria, a user flow with decision points and failure branches, and
the screen inventory each flow needs. Format in [references/ux-artifacts.md](references/ux-artifacts.md).
A screen with no story behind it is a guess.

**Phase 4 — Variants.** Apply the A–E rule below. Render every variant in the prototype under
`design/variants/<date>-<slug>/` so the operator *interacts* with them instead of judging a
static picture.

**Phase 5 — Verify with the operator.** Present the variants with a one-line rationale each
and your recommendation. The operator picks, rejects, or requests edits. Edits → apply →
return to verification. Nothing lands until the operator approves. Before declaring done:

```bash
python3 scripts/check_design.py .
```

**Phase 6 — Land.** Move the chosen variant out of `variants/` into its permanent home,
record the rejected options and the reasoning in that round's `DECISION.md`, promote any new
pattern into the UI kit and tokens, rebuild (`build_tokens.py`, `build_icons.py`), and update
`design/handoff/AGENTS.md` so the next coding agent picks it up. See
[references/repo-structure.md](references/repo-structure.md) for what belongs where.

## The A–E rule

Any concrete design request ("make a nice banner", "design the onboarding screen", "we need a
logo") is answered with **several labelled variants, never one**. Default five (A–E); three
(A–C) is acceptable for small, tightly-constrained asks; one is never acceptable.

Variants must differ on a **stated axis** — layout, hierarchy, tone, density, motion — not in
hue or corner radius. Five near-identical options are worse than three real ones. Each variant
gets: a label, a one-sentence concept, the axis it explores, and a live render in the
prototype. See [references/variants.md](references/variants.md) for the axis catalogue and the
anti-sameness check.

## Gotchas

- **Survey before you scaffold.** Operators frequently have a logo, a palette in a
  `tailwind.config.js`, or an exported `tokens.json` lying around. Scaffolding a fresh
  `design/` on top of that is the single most destructive thing this skill can do.
- **The prototype must not need `npm install`.** It is static files served over HTTP
  (`python3 -m http.server 4321 --directory design/prototype`). A teammate on a locked-down
  laptop, and a coding agent in a sandbox, both have to run it. Keep it dependency-free; use
  ES modules and CSS custom properties, never a bundler.
- **Prototype files must be opened over HTTP, not `file://`.** ES module imports and `fetch`
  of the token JSON fail under `file://` with an opaque CORS error. The scaffold's
  `design/prototype/run.sh` exists so nobody double-clicks the HTML.
- **Themes are tokens, not a stylesheet copy.** Dark mode is a second set of *semantic* token
  values pointing at the same primitives. If you find yourself writing a second `.dark .btn
  { background: #… }` rule, the token layer is wrong.
- **iOS app icons must have no alpha channel** and are a flat square — the system applies the
  mask. Android adaptive icons are the opposite: a 108dp canvas where only the central 72dp is
  safe, and the outer ring *will* be cropped. A single flat PNG reused for both always looks
  broken on one of them. The monochrome layer is required for Android themed icons.
- **A favicon is not a shrunk logo.** Below 32px a wordmark is mud. The brand set must include
  a dedicated favicon-safe mark; generating the favicon from the full logo is a defect.
- **Contrast-check both themes, every time.** A palette that passes AA on white routinely fails
  on the dark surface (and vice versa for inverted text). `check_design.py` runs the WCAG math;
  do not eyeball it.
- **Never invent a token value silently.** If the design needs a shade that does not exist,
  add it to the primitive ramp explicitly and say so. Silent one-off hexes are how a design
  system dies.
- **Variants are disposable, decisions are not.** Delete rejected variant renders, but keep
  `DECISION.md` — "why not B" is the most frequently re-litigated question on a design team.
- **`build_icons.py` falls back to headless Chrome when no SVG rasterizer is installed**, and
  that path is slow (~1 minute for a full three-platform pack) and needs its own
  `--user-data-dir`, which the script supplies — without it Chrome contends with the user's
  running browser profile and hangs rather than failing. If icon builds are frequent,
  `brew install librsvg` makes it roughly instant.
- **Binary assets belong in git, but generated ones do not.** Source SVGs and masters are
  committed; everything under a `build/` directory is produced by the scripts and gitignored.
  If a teammate cannot regenerate it from source, it is not a source.

## Scripts

All are Python standard library only — no install, no network. Run them; do not reimplement
their logic inline. Paths below are **relative to this skill's directory**, while `<repo>` is
the operator's project — invoke them as
`python3 <skill-dir>/scripts/<name>.py <repo>` from the project root.

```bash
# Phase 0 — what design already exists here?
python3 scripts/check_design.py --survey <repo>

# Phase 1 — create the workspace (never run on a non-empty design/ without --force)
python3 scripts/scaffold_design.py --name "Acme" --dest <repo>

# Phase 4 — start an A–E exploration round
python3 scripts/new_round.py banner --dest <repo> --variants 5

# Phase 6 — regenerate platform artifacts
python3 scripts/build_tokens.py <repo>/design      # DTCG → css/ts/dart/swift/kotlin/xml
python3 scripts/build_icons.py <repo>/design       # master SVG → web/iOS/Android packs

# Phase 5/6 — enforce the non-negotiables (exit 1 = incomplete design)
python3 scripts/check_design.py <repo>
```

Exit codes: `0` pass · `1` design incomplete / check failed · `2` bad usage · `3` a required
external tool is missing (only `build_icons.py` rasterization — it names the install command).

## References

Load a reference when its phase comes up, not preemptively.

- [references/repo-structure.md](references/repo-structure.md) — Phases 1/6: the full
  directory contract, `design.config.json`, and the `handoff/AGENTS.md` implementation
  contract that makes the design machine-reproducible.
- [references/adopting-existing.md](references/adopting-existing.md) — Phase 1, state
  `assets`: the intake protocol for work the operator already has.
- [references/brand-and-tokens.md](references/brand-and-tokens.md) — Phase 1/6: brand kit
  contents, token tiers and naming, theming, type/spacing/motion scales.
- [references/icon-packs.md](references/icon-packs.md) — Phase 6: the exact per-platform
  icon deliverables, sizes, and formats.
- [references/ux-artifacts.md](references/ux-artifacts.md) — Phase 3: user story, user flow,
  and screen spec formats, with IDs that trace to code.
- [references/variants.md](references/variants.md) — Phase 4: the axis catalogue, how to make
  A–E genuinely different, and how to present them.
- [references/prototype.md](references/prototype.md) — Phases 4/6: prototype architecture,
  how to add a screen or a variant, animation conventions, how teammates run it.
- [references/iteration-loop.md](references/iteration-loop.md) — Phases 2/5: the clarifying
  question protocol and the verification loop, including how to handle vague feedback.
