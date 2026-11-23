# building-design

[![npm](https://img.shields.io/npm/v/building-design)](https://www.npmjs.com/package/building-design)
[![Validate](https://github.com/vstlmkh/building-design/actions/workflows/validate.yml/badge.svg)](https://github.com/vstlmkh/building-design/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> Builds a product design system as a versioned, runnable artifact: brand, DTCG tokens with
> light/dark themes, web/iOS/Android icon packs, a UI kit, UX artifacts and a zero-install
> interactive prototype — structured so AI coding agents can reimplement the design exactly.

`design-system` · `design-tokens` · `dtcg` · `design-to-code` · `design-handoff` · `ui-kit` ·
`dark-mode` · `theming` · `app-icons` · `favicon` · `brand-kit` · `ux` · `user-flows` ·
`prototype` · `accessibility`

An [Agent Skill](https://agentskills.io/specification) for building and growing a product's
design as a **versioned, runnable artifact** in a git repo.

It scaffolds (or adopts) a `design/` workspace containing the brand, DTCG design tokens with
light and dark themes, icon packs for web / iOS / Android, a UI kit, UX artifacts (user
stories, flows, screen specs), and a zero-install interactive prototype that any teammate can
run locally — structured so an AI coding agent can reimplement the design exactly in Flutter,
SwiftUI, Compose, or on the web.

## Install and run

Install the released package for both agents at user level:

```bash
npx building-design install
```

Use `--agent claude` or `--agent kimi` for one agent, and `--project /path/to/repo` for a
project-local install. `npx building-design status` inspects the installation; rerunning
`install` preserves existing files unless `--force` is explicit.

The same directory-form skill works in **Claude Code** and **Kimi Code**; no generated copies
or tool-specific branches are needed. This checkout includes project-local discovery links in
`.claude/skills/` and `.kimi-code/skills/`, so both CLIs can discover it when opened at the
repository root.

To link a development checkout instead of installing the npm release:

```bash
# Claude Code
mkdir -p ~/.claude/skills
ln -s "$(pwd)" ~/.claude/skills/building-design

# Kimi Code
mkdir -p ~/.kimi-code/skills
ln -s "$(pwd)" ~/.kimi-code/skills/building-design
```

Kimi Code also supports the shared `~/.agents/skills/` location. If this checkout is not at the
target path, replace it first or remove the old link before creating a new one.

Invoke manually with `/building-design` in Claude Code or `/skill:building-design` in Kimi
Code. Both agents can also trigger it automatically from the request. In Kimi Code,
`${KIMI_SKILL_DIR}` resolves supporting files; the skill instructions provide the equivalent
path-resolution rule for Claude Code.

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

- `SKILL.md` — shared Claude/Kimi frontmatter and body: workflow, A–E rule, gotchas
- `.claude/skills/building-design` — project-local Claude discovery link to this checkout
- `.kimi-code/skills/building-design` — project-local Kimi discovery link to this checkout
- `references/` — loaded on demand per phase
- `scripts/` — the five utilities
- `evals/` — trigger, output-conformance, and negative near-miss scenarios
