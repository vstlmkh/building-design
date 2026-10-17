# building-design

An [Agent Skill](https://agentskills.io/specification) for building and growing a product's
design as a **versioned, runnable artifact** in a git repo.

It scaffolds (or adopts) a `design/` workspace containing the brand, DTCG design tokens with
light and dark themes, icon packs for web / iOS / Android, a UI kit, UX artifacts (user
stories, flows, screen specs), and a zero-install interactive prototype that any teammate can
run locally — structured so an AI coding agent can reimplement the design exactly in Flutter,
SwiftUI, Compose, or on the web.

## Install

```bash
ln -s "$(pwd)" ~/.claude/skills/building-design
```

## What it enforces

Every design that lands is complete: brand + logo set · icon packs for every declared
platform (web favicon/PWA, iOS light/dark/tinted, Android adaptive with a monochrome layer) ·
a UI kit with every component state · both themes, contrast-checked · a runnable prototype.
`scripts/check_design.py` fails the build when one is missing.

Every open-ended design request is answered with **A–E variants** along a stated axis, rendered
live in the prototype, before the operator picks one.

## Scripts

| Script | Purpose |
| --- | --- |
| `check_design.py --survey <repo>` | detect existing design: `workspace` / `assets` / `empty` |
| `scaffold_design.py --name X --dest <repo>` | create the `design/` workspace (`--adopt` for intake) |
| `build_tokens.py <design>` | DTCG tokens → CSS, TS, Dart, Swift, Kotlin, Android XML |
| `build_icons.py <design>` | `master.svg` → web / iOS / Android icon packs |
| `new_round.py <slug> --dest <repo>` | scaffold an A–E variant round |
| `check_design.py <repo>` | enforce the completeness rules (exit 1 = incomplete) |

Standard library only. `build_icons.py` needs one external rasterizer
(`rsvg-convert`, `inkscape`, `magick`, or headless Chrome as a slow fallback).

## Layout

- `SKILL.md` — the skill body: non-negotiables, the 7-phase workflow, the A–E rule, gotchas
- `references/` — loaded on demand per phase
- `scripts/` — the five utilities
- `evals/` — trigger, output-conformance, and negative near-miss scenarios
