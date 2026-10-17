#!/usr/bin/env python3
"""Scaffold a `design/` workspace: directory tree, token stubs, and a zero-install prototype.

Standard library only. Safe by default: refuses to touch an existing design/ unless --force.

Exit codes: 0 ok · 1 refused (target exists) · 2 bad usage
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

ALL_PLATFORMS = ("web", "ios", "android")


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "product"


# --- token stubs -----------------------------------------------------------
# A neutral starter palette. Deliberately NOT a brand: the first design round
# replaces the accent ramp. Ramps are 11-step so semantic tokens always have a
# step to point at without anyone inventing a one-off hex.
PRIMITIVES = {
    "color": {
        "palette": {
            "neutral": {
                "0": "#ffffff", "50": "#f8fafc", "100": "#f1f5f9", "200": "#e2e8f0",
                "300": "#cbd5e1", "400": "#94a3b8", "500": "#64748b", "600": "#475569",
                "700": "#334155", "800": "#1e293b", "900": "#0f172a", "950": "#020617",
            },
            "accent": {
                "50": "#eef2ff", "100": "#e0e7ff", "200": "#c7d2fe", "300": "#a5b4fc",
                "400": "#818cf8", "500": "#6366f1", "600": "#4f46e5", "700": "#4338ca",
                "800": "#3730a3", "900": "#312e81", "950": "#1e1b4b",
            },
            "success": {"100": "#dcfce7", "400": "#4ade80", "600": "#16a34a", "900": "#14532d"},
            "warning": {"100": "#fef3c7", "400": "#fbbf24", "600": "#d97706", "900": "#78350f"},
            "danger": {"100": "#fee2e2", "400": "#f87171", "600": "#dc2626", "900": "#7f1d1d"},
        }
    },
    "space": {str(i): f"{i * 4}px" for i in (0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24)},
    "radius": {"none": "0px", "sm": "4px", "md": "8px", "lg": "12px", "xl": "20px", "full": "9999px"},
    "size": {"control-sm": "32px", "control-md": "40px", "control-lg": "48px",
             "icon-sm": "16px", "icon-md": "24px", "icon-lg": "32px", "touch-min": "44px"},
    "font": {
        "family": {"display": "Inter, system-ui, sans-serif",
                   "text": "Inter, system-ui, sans-serif",
                   "mono": "ui-monospace, SFMono-Regular, Menlo, monospace"},
        # 1.200 modular scale from 16px
        "size": {"xs": "12px", "sm": "14px", "md": "16px", "lg": "20px",
                 "xl": "24px", "2xl": "30px", "3xl": "36px", "4xl": "48px"},
        "weight": {"regular": "400", "medium": "500", "semibold": "600", "bold": "700"},
        "line-height": {"tight": "1.2", "snug": "1.35", "normal": "1.5", "relaxed": "1.65"},
    },
    "duration": {"instant": "80ms", "fast": "160ms", "base": "240ms", "slow": "400ms"},
    "easing": {
        "standard": "cubic-bezier(0.2, 0, 0, 1)",
        "decelerate": "cubic-bezier(0, 0, 0, 1)",
        "accelerate": "cubic-bezier(0.3, 0, 1, 1)",
        "emphasized": "cubic-bezier(0.2, 0, 0, 1)",
    },
}

# semantic: (dot.path, light alias, dark alias)
SEMANTIC = [
    ("color.bg.canvas", "color.palette.neutral.50", "color.palette.neutral.950"),
    ("color.bg.surface", "color.palette.neutral.0", "color.palette.neutral.900"),
    ("color.bg.surface-raised", "color.palette.neutral.0", "color.palette.neutral.800"),
    ("color.bg.subtle", "color.palette.neutral.100", "color.palette.neutral.800"),
    ("color.bg.inverse", "color.palette.neutral.900", "color.palette.neutral.100"),
    ("color.fg.default", "color.palette.neutral.900", "color.palette.neutral.100"),
    ("color.fg.muted", "color.palette.neutral.600", "color.palette.neutral.400"),
    ("color.fg.on-accent", "color.palette.neutral.0", "color.palette.neutral.950"),
    ("color.fg.inverse", "color.palette.neutral.0", "color.palette.neutral.900"),
    ("color.border.subtle", "color.palette.neutral.200", "color.palette.neutral.700"),
    ("color.border.strong", "color.palette.neutral.400", "color.palette.neutral.500"),
    ("color.border.focus", "color.palette.accent.600", "color.palette.accent.400"),
    ("color.accent.default", "color.palette.accent.600", "color.palette.accent.400"),
    ("color.accent.hover", "color.palette.accent.700", "color.palette.accent.300"),
    ("color.accent.subtle", "color.palette.accent.50", "color.palette.accent.950"),
    ("color.status.success", "color.palette.success.600", "color.palette.success.400"),
    ("color.status.warning", "color.palette.warning.600", "color.palette.warning.400"),
    ("color.status.danger", "color.palette.danger.600", "color.palette.danger.400"),
]

# Pairs check_design.py contrast-checks in both themes: (foreground, background, role)
CONTRAST_PAIRS = [
    ["color.fg.default", "color.bg.canvas", "body"],
    ["color.fg.default", "color.bg.surface", "body"],
    ["color.fg.muted", "color.bg.surface", "body"],
    ["color.fg.on-accent", "color.accent.default", "body"],
    ["color.border.focus", "color.bg.canvas", "nontext"],
    ["color.status.danger", "color.bg.surface", "nontext"],
]


def dtcg_primitives():
    def wrap(node):
        if isinstance(node, dict):
            return {k: wrap(v) for k, v in node.items()}
        t = "color" if str(node).startswith("#") else (
            "duration" if str(node).endswith("ms") else
            "cubicBezier" if str(node).startswith("cubic") else "dimension")
        if t == "dimension" and not str(node).endswith("px"):
            t = "number" if str(node).replace(".", "").isdigit() else "fontFamily"
        return {"$type": t, "$value": node}
    return wrap(PRIMITIVES)


def dtcg_semantic():
    root = {}
    for path, light, dark in SEMANTIC:
        node = root
        parts = path.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = {
            "$type": "color",
            "$value": "{%s}" % light,
            "$extensions": {"themes": {"dark": "{%s}" % dark}},
        }
    root["$extensions"] = {"contrastPairs": CONTRAST_PAIRS}
    return root


# --- static file bodies ----------------------------------------------------
RUN_SH = """#!/usr/bin/env bash
# Serve the prototype. Do NOT open index.html directly: file:// breaks ES modules.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-__PORT__}"
echo "Prototype: http://localhost:$PORT"
exec python3 -m http.server "$PORT" --directory "$DIR"
"""

INDEX_HTML = """<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__PRODUCT__ — design prototype</title>
<link rel="stylesheet" href="styles/tokens.css">
<link rel="stylesheet" href="styles/base.css">
</head>
<body>
<header class="shell-bar">
  <a class="shell-brand" href="#/">__PRODUCT__ design</a>
  <nav class="shell-nav">
    <a href="#/ui-kit">UI kit</a>
    <a href="#/screens">Screens</a>
    <a href="#/variants">Variants</a>
  </nav>
  <button id="theme-toggle" class="shell-toggle" type="button" aria-label="Toggle theme">◐</button>
</header>
<main id="app"></main>
<script type="module" src="app.js"></script>
</body>
</html>
"""

APP_JS = """// Hash router + theme persistence. No build step, no dependencies.
import { routes } from "./routes/index.js";

const app = document.getElementById("app");

// --- theme ---------------------------------------------------------------
const THEME_KEY = "design-prototype-theme";
const stored = localStorage.getItem(THEME_KEY);
const initial = stored || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
document.documentElement.dataset.theme = initial;
document.getElementById("theme-toggle").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  localStorage.setItem(THEME_KEY, next);
});

// --- router --------------------------------------------------------------
async function render() {
  const path = location.hash.replace(/^#/, "") || "/";
  const entry = routes[path] || routes["/"];
  app.innerHTML = "";
  document.title = (entry.title ? entry.title + " — " : "") + "__PRODUCT__ design";
  const mod = typeof entry.load === "function" ? await entry.load() : entry;
  (mod.render || entry.render)(app, { path });
}

addEventListener("hashchange", render);
render();
"""

ROUTES_INDEX_JS = """// Route registry. One module per route; add new screens and variants here.
export const routes = {
  "/": { title: "Home", render: home },
  "/ui-kit": { title: "UI kit", load: () => import("./ui-kit.js") },
  "/screens": { title: "Screens", render: (r) => list(r, "Screens", [], "ux/screens") },
  "/variants": { title: "Variants", render: (r) => list(r, "Variants", [], "variants") },
};

function home(root) {
  root.innerHTML = `
    <section class="page">
      <h1>__PRODUCT__ design prototype</h1>
      <p class="lede">The interactive source of visual truth. Toggle the theme in the bar above;
      every route must look right in both.</p>
      <ul class="cards">
        <li><a href="#/ui-kit"><strong>UI kit</strong><span>Every component, every state</span></a></li>
        <li><a href="#/screens"><strong>Screens</strong><span>Specs rendered live, all states</span></a></li>
        <li><a href="#/variants"><strong>Variants</strong><span>A–E exploration rounds</span></a></li>
      </ul>
    </section>`;
}

function list(root, title, items, dir) {
  root.innerHTML = `
    <section class="page">
      <h1>${title}</h1>
      ${items.length
        ? `<ul class="cards">${items.map((i) => `<li><a href="#${i.path}"><strong>${i.id}</strong><span>${i.title}</span></a></li>`).join("")}</ul>`
        : `<p class="lede">Nothing here yet. Add one under <code>${dir}/</code> and register it in <code>routes/index.js</code>.</p>`}
    </section>`;
}
"""

UIKIT_JS = """// The gallery: every component rendered across its variants x sizes x states.
// A gap here is visible rather than theoretical.
import { ButtonPrimary } from "../components/ButtonPrimary.js";

const STATES = ["default", "hover", "focus", "active", "disabled", "loading"];
const SIZES = ["sm", "md", "lg"];

export function render(root) {
  root.innerHTML = `<section class="page"><h1>UI kit</h1>
    <p class="lede">Components bound to semantic tokens. Toggle the theme — nothing here
    contains a theme conditional.</p>
    <h2>ButtonPrimary</h2>
    <table class="matrix"><thead><tr><th></th>${STATES.map((s) => `<th>${s}</th>`).join("")}</tr></thead>
    <tbody>${SIZES.map((size) => `<tr><th>${size}</th>${STATES.map((state) =>
      `<td>${ButtonPrimary({ label: "Continue", size, state })}</td>`).join("")}</tr>`).join("")}
    </tbody></table>
  </section>`;
}
"""

BUTTON_JS = """// Props mirror the variant/state axes in spec.md, with identical names — those names
// travel into the React / Compose / SwiftUI implementation.
export function ButtonPrimary({ label, size = "md", state = "default", icon = null }) {
  const cls = ["btn", "btn--primary", `btn--${size}`, state !== "default" ? `is-${state}` : ""]
    .filter(Boolean).join(" ");
  const disabled = state === "disabled" || state === "loading" ? " disabled" : "";
  return `<button type="button" class="${cls}"${disabled}>
    ${state === "loading" ? '<span class="btn__spinner" aria-hidden="true"></span>' : ""}
    ${icon ? `<span class="btn__icon">${icon}</span>` : ""}
    <span class="btn__label">${label}</span>
  </button>`;
}
"""

MOTION_JS = """// Durations and easings come from the motion tokens. No literal "0.3s ease" anywhere.
const css = getComputedStyle(document.documentElement);
const token = (name, fallback) => (css.getPropertyValue(name) || fallback).trim();

export const duration = {
  instant: token("--duration-instant", "80ms"),
  fast: token("--duration-fast", "160ms"),
  base: token("--duration-base", "240ms"),
  slow: token("--duration-slow", "400ms"),
};
export const easing = {
  standard: token("--easing-standard", "cubic-bezier(0.2,0,0,1)"),
  decelerate: token("--easing-decelerate", "cubic-bezier(0,0,0,1)"),
  accelerate: token("--easing-accelerate", "cubic-bezier(0.3,0,1,1)"),
  emphasized: token("--easing-emphasized", "cubic-bezier(0.2,0,0,1)"),
};

export const reducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Animate transform/opacity only — width/top/box-shadow jank on mid-range Android. */
export function animate(el, keyframes, { dur = duration.base, ease = easing.standard } = {}) {
  if (reducedMotion()) return el.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 80 });
  return el.animate(keyframes, { duration: parseFloat(dur), easing: ease, fill: "both" });
}
"""

BASE_CSS = """/* Element defaults. Values come from tokens only — no literals below this line. */
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  background: var(--color-bg-canvas);
  color: var(--color-fg-default);
  font-family: var(--font-family-text);
  font-size: var(--font-size-md);
  line-height: var(--font-line-height-normal);
}
a { color: var(--color-accent-default); }
:focus-visible { outline: 2px solid var(--color-border-focus); outline-offset: 2px; }

/* Global reduced-motion guard. Do not defeat this per-component. */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: var(--duration-instant) !important;
    transition-duration: var(--duration-instant) !important;
  }
}

.shell-bar {
  display: flex; align-items: center; gap: var(--space-4);
  padding: var(--space-3) var(--space-5);
  background: var(--color-bg-surface);
  border-bottom: 1px solid var(--color-border-subtle);
  position: sticky; top: 0; z-index: 10;
}
.shell-brand { font-weight: var(--font-weight-semibold); text-decoration: none; }
.shell-nav { display: flex; gap: var(--space-4); margin-inline-start: auto; }
.shell-toggle {
  min-width: var(--size-touch-min); min-height: var(--size-touch-min);
  background: transparent; border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-md); color: var(--color-fg-default); cursor: pointer;
  transition: background var(--duration-fast) var(--easing-standard);
}
.shell-toggle:hover { background: var(--color-bg-subtle); }

.page { max-width: 72rem; margin: 0 auto; padding: var(--space-8) var(--space-5); }
.lede { color: var(--color-fg-muted); max-width: 60ch; }
.cards { list-style: none; padding: 0; display: grid; gap: var(--space-4);
         grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); }
.cards a {
  display: flex; flex-direction: column; gap: var(--space-1);
  padding: var(--space-5); text-decoration: none; color: inherit;
  background: var(--color-bg-surface); border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  transition: transform var(--duration-fast) var(--easing-standard),
              border-color var(--duration-fast) var(--easing-standard);
}
.cards a:hover { transform: translateY(-2px); border-color: var(--color-border-strong); }
.cards span { color: var(--color-fg-muted); font-size: var(--font-size-sm); }
.matrix { border-collapse: collapse; }
.matrix th, .matrix td { padding: var(--space-3); text-align: start;
  border-bottom: 1px solid var(--color-border-subtle); font-weight: var(--font-weight-regular); }

.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: var(--space-2);
  font-family: inherit; font-weight: var(--font-weight-medium);
  border: 1px solid transparent; border-radius: var(--radius-md); cursor: pointer;
  transition: background var(--duration-fast) var(--easing-standard),
              transform var(--duration-instant) var(--easing-standard);
}
.btn--sm { min-height: var(--size-control-sm); padding-inline: var(--space-3); font-size: var(--font-size-sm); }
.btn--md { min-height: var(--size-control-md); padding-inline: var(--space-4); font-size: var(--font-size-md); }
.btn--lg { min-height: var(--size-control-lg); padding-inline: var(--space-5); font-size: var(--font-size-lg); }
.btn--primary { background: var(--color-accent-default); color: var(--color-fg-on-accent); }
.btn--primary:hover, .btn--primary.is-hover { background: var(--color-accent-hover); }
.btn--primary.is-focus { outline: 2px solid var(--color-border-focus); outline-offset: 2px; }
.btn--primary.is-active { transform: scale(0.98); }
.btn--primary.is-disabled, .btn--primary:disabled { opacity: 0.45; cursor: not-allowed; }
.btn__spinner {
  width: var(--size-icon-sm); height: var(--size-icon-sm); border-radius: var(--radius-full);
  border: 2px solid currentColor; border-top-color: transparent;
  animation: spin var(--duration-slow) linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
"""

GITIGNORE = """# Generated by build_tokens.py / build_icons.py — regenerate, never commit.
tokens/build/
icons/app/build/
"""

BRAND_MD = """# __PRODUCT__ — brand

> Written before any pixel. Every section must constrain a decision; delete nothing, fill it in.

## Positioning
For <audience>, __PRODUCT__ is the <category> that <differentiator>, because <reason to believe>.

## Personality
Each adjective needs an "and not" — without it, it constrains nothing.

- <adjective> — and *not* <the nearby thing we are not>
- <adjective> — and *not* <…>
- <adjective> — and *not* <…>

## Voice & tone
| Situation | Tone | Example copy |
| --- | --- | --- |
| Success | | |
| Error | | |
| Empty state | | |

## Do / don't
1. …
"""

AGENTS_MD = """# Implementation contract

You are implementing a design that already exists. Reproduce it; do not reinterpret it.

## Read in this order
1. `../design.config.json` — product, platforms, targets, conventions.
2. `../tokens/build/<file for your target>` — generated token constants. Run
   `python3 scripts/build_tokens.py design` first if `build/` is absent.
3. `../ui-kit/README.md` — the component inventory and its status.
4. The `SCR-###` spec in `../ux/screens/` for the screen you are building.
5. The prototype route named in that spec — run `../prototype/run.sh` and open it.

## Hard rules
- **No literal values.** Colour, spacing, radius, font size, duration, easing — every one
  resolves to a token. A hex in a widget is a defect.
- **Names match exactly.** `ButtonPrimary` in `ui-kit/components/` is `ButtonPrimary` in code.
  Never reorder to `PrimaryButton`.
- **Every state in `spec.md` exists in code** — including loading, empty, error, disabled.
- **Both themes.** Light and dark are driven by the same semantic names; no theme conditional
  inside a component.
- **Motion matches.** Durations and easings come from the motion tokens, honouring
  reduced-motion.

## Token mapping
See `platform-map.md` for token → CSS / Flutter / SwiftUI / Compose.

## How to verify
Run the prototype on the port in `design.config.json`, open the route named in the spec, and
compare state by state against your implementation in **both themes**. List any divergence.

## Intentional divergences
Document here what *should* differ per platform (native navigation, system fonts, haptics) so
nobody "fixes" a deliberate choice.
"""

PLATFORM_MAP_MD = """# Token → platform map

| Token group | Web (`tokens.css` / `tokens.ts`) | Flutter (`tokens.dart`) | SwiftUI (`Tokens.swift`) | Compose (`Tokens.kt`, `colors.xml`) |
| --- | --- | --- | --- | --- |
| colour | `var(--color-…)` | `AppColors.…` (ThemeExtension) | `Color.…` | `AppColors.…` / `@color/…` |
| spacing | `var(--space-N)` | `AppSpace.nN` | `Space.nN` | `AppSpace.nN.dp` |
| radius | `var(--radius-…)` | `BorderRadius.circular(AppRadius.…)` | `.cornerRadius(Radius.…)` | `RoundedCornerShape(AppRadius.…)` |
| type | `var(--font-size-…)` + `--font-line-height-…` | `AppText.…` (TextStyle) | `Font.…` | `AppType.…` (TextStyle) |
| motion | `var(--duration-…)`, `var(--easing-…)` | `Duration`/`Curves` in `AppMotion` | `Animation.timingCurve` | `tween(AppMotion.…)` |

Theme switching: web `[data-theme="dark"]` · Flutter `ThemeMode` + the dark `ThemeExtension`
· SwiftUI `@Environment(\\.colorScheme)` with asset colour sets · Android `values-night/`.
"""


def write(path: Path, content: str, product: str, port: int, force: bool) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.replace("__PRODUCT__", product).replace("__PORT__", str(port)))
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", required=True, help="product name, e.g. 'Acme'")
    ap.add_argument("--dest", default=".", help="repo root (design/ is created inside)")
    ap.add_argument("--platforms", default="web,ios,android")
    ap.add_argument("--port", type=int, default=4321)
    ap.add_argument("--adopt", action="store_true",
                    help="intake mode: create the tree + tokens but no placeholder brand/icon "
                         "files, so nothing shadows the operator's real assets")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    a = ap.parse_args(argv)

    platforms = [p.strip() for p in a.platforms.split(",") if p.strip()]
    bad = [p for p in platforms if p not in ALL_PLATFORMS]
    if bad:
        print(f"ERROR: unknown platform(s): {', '.join(bad)} (allowed: {', '.join(ALL_PLATFORMS)})",
              file=sys.stderr)
        return 2

    root = Path(a.dest).resolve() / "design"
    if root.exists() and any(root.iterdir()) and not (a.force or a.adopt):
        print(f"ERROR: {root} already exists and is not empty.\n"
              f"  Run check_design.py --survey to read the existing workspace, or pass --adopt "
              f"(intake) / --force (overwrite).", file=sys.stderr)
        return 1

    dirs = ["brand/logo", "tokens", "icons/ui", "icons/app", "ui-kit/components", "ux/flows",
            "ux/screens", "prototype/routes/screens", "prototype/routes/variants",
            "prototype/routes/_data", "prototype/components", "prototype/styles", "variants",
            "handoff/exports", "decisions"]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

    created, skipped = [], []

    def put(rel, content):
        ok = write(root / rel, content, a.name, a.port, a.force)
        (created if ok else skipped).append(rel)

    config = {
        "product": a.name,
        "version": "0.1.0",
        "placement": "in-product-repo",
        "platforms": platforms,
        "themes": ["light", "dark"],
        "defaultTheme": "light",
        "paths": {"tokens": "tokens", "icons": "icons", "uiKit": "ui-kit", "ux": "ux",
                  "prototype": "prototype", "variants": "variants", "handoff": "handoff"},
        "prototype": {"command": "./prototype/run.sh", "port": a.port},
        "targets": {"web": {"framework": "react", "styling": "css-custom-properties"},
                    "ios": {"framework": "swiftui"}, "android": {"framework": "compose"}},
        "conventions": {"componentNaming": "PascalCase", "tokenNaming": "kebab-case-dot-path",
                        "iconGrid": 24},
    }
    config["targets"] = {k: v for k, v in config["targets"].items() if k in platforms}

    put("design.config.json", json.dumps(config, indent=2) + "\n")
    put("tokens/primitives.tokens.json", json.dumps(dtcg_primitives(), indent=2) + "\n")
    put("tokens/semantic.tokens.json", json.dumps(dtcg_semantic(), indent=2) + "\n")
    put(".gitignore", GITIGNORE)
    put("prototype/index.html", INDEX_HTML)
    put("prototype/app.js", APP_JS)
    put("prototype/routes/index.js", ROUTES_INDEX_JS)
    put("prototype/routes/ui-kit.js", UIKIT_JS)
    put("prototype/components/ButtonPrimary.js", BUTTON_JS)
    put("prototype/motion.js", MOTION_JS)
    put("prototype/styles/base.css", BASE_CSS)
    # Placeholder so index.html does not 404 before the first token build.
    put("prototype/styles/tokens.css",
        "/* Placeholder. Run: python3 scripts/build_tokens.py design */\n")
    put("handoff/AGENTS.md", AGENTS_MD)
    put("handoff/platform-map.md", PLATFORM_MAP_MD)
    put("ui-kit/components/ButtonPrimary/ButtonPrimary.js", BUTTON_JS)
    put("ui-kit/components/ButtonPrimary/spec.md",
        "# ButtonPrimary\n\n## Anatomy\n[icon?] label [spinner?]\n\n"
        "## Variants / sizes\nsm · md · lg\n\n"
        "## States\ndefault · hover · focus-visible · active · disabled · loading\n\n"
        "## Tokens\nbg `color.accent.default` / hover `color.accent.hover` · fg "
        "`color.fg.on-accent` · radius `radius.md` · height `size.control-{sm,md,lg}`\n\n"
        "## Accessibility\nMin touch target `size.touch-min`; focus ring >= 3:1; loading state "
        "sets `aria-busy` and keeps the label.\n\n"
        "## Motion\nbackground `duration.fast` / `easing.standard`; press scale 0.98 at "
        "`duration.instant`.\n")
    put("ui-kit/README.md",
        "# UI kit\n\n| Component | Status | Prototype route |\n| --- | --- | --- |\n"
        "| ButtonPrimary | ready | `#/ui-kit` |\n")
    put("ux/personas.md", "# Personas\n\n<2-4 personas; each must be able to kill a design idea>\n")
    put("ux/stories.md",
        "# User stories\n\n| ID | Story | Acceptance criteria | Flow | Priority |\n"
        "| --- | --- | --- | --- | --- |\n")
    put("CHANGELOG.md", "# Design changelog\n\nNewest first.\n\n## Unreleased\n- Workspace scaffolded.\n")
    if not a.adopt:
        put("brand/brand.md", BRAND_MD)
        put("brand/clearspace.md", "# Clear space & minimum sizes\n")
        put("brand/imagery.md", "# Imagery direction\n")

    put("README.md", f"""# {a.name} — design

The design system for {a.name}: brand, tokens, icon packs, UI kit, UX artifacts, and a
runnable prototype. `design.config.json` is the entry point.

## Run the prototype

```bash
./design/prototype/run.sh
```

Then open <http://localhost:{a.port}>. Do **not** open `index.html` directly — `file://`
breaks ES modules and the token fetch.

## Regenerate platform artifacts

```bash
python3 scripts/build_tokens.py design     # tokens  -> css / ts / dart / swift / kotlin / xml
python3 scripts/build_icons.py design      # master.svg -> web / iOS / Android icon packs
python3 scripts/check_design.py .          # enforce the completeness rules
```

## Implementing this design in code
Read `handoff/AGENTS.md` first. It is the contract.
""")

    run = root / "prototype/run.sh"
    if write(run, RUN_SH, a.name, a.port, a.force):
        run.chmod(0o755)
        created.append("prototype/run.sh")
    else:
        skipped.append("prototype/run.sh")

    print(f"Scaffolded {root}")
    print(f"  created: {len(created)} files" + ("  (adopt mode: no placeholder brand/icon files)"
                                                if a.adopt else ""))
    if skipped:
        print(f"  skipped (exists): {', '.join(skipped)}")
    print("\nNext:")
    print(f"  python3 scripts/build_tokens.py {root.name}")
    print(f"  {root}/prototype/run.sh")
    return 0


if __name__ == "__main__":
    sys.exit(main())
