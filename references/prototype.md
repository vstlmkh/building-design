# The prototype

The runnable, interactive source of visual truth. Every teammate must be able to start it in
one command with nothing installed beyond what ships with macOS/Linux/Windows + Python.

## Contents

- Why zero-install
- How a teammate runs it
- Architecture
- Adding a screen
- Adding a variant round
- Components
- Theming
- Animation conventions
- Content and data
- When the product already has a frontend

## Why zero-install

The prototype is read by designers, PMs, QA, mobile engineers who have no Node toolchain, and
AI coding agents in sandboxes. A Vite/Next prototype breaks for at least two of those groups
within a month (node version, lockfile rot, offline install). Static ES modules + CSS custom
properties cost nothing, never rot, and are directly readable by an agent as plain text.

Deviate only if the operator's team already ships a web app and wants the prototype inside
it — see the last section.

## How a teammate runs it

```bash
./design/prototype/run.sh          # serves on the port in design.config.json (default 4321)
# or, equivalently:
python3 -m http.server 4321 --directory design/prototype
```

Then open `http://localhost:4321`. **Not** by double-clicking `index.html` — `file://` blocks
ES module imports and the `fetch` of the token JSON, with an error message that names CORS and
explains nothing. `run.sh` exists to make the wrong path hard to take.

`design/README.md` must carry these two lines verbatim. It is the first thing a new teammate
reads.

## Architecture

```
prototype/
├── index.html          # shell: <main id="app">, theme toggle, nav, imports app.js as a module
├── app.js              # hash router + route registry + theme persistence
├── routes/
│   ├── index.js        # home: links to every route, grouped
│   ├── ui-kit.js       # the gallery — every component, every state, both themes
│   ├── screens/scr-012-resume-summary.js
│   └── variants/<round>/{index,a,b,c,d,e}.js
├── components/         # mirrors ui-kit/components/<Component>/<Component>.js
├── styles/
│   ├── tokens.css      # copied/symlinked from tokens/build/tokens.css — never hand-edited
│   ├── base.css        # reset + element defaults, tokens only
│   └── layout.css
└── motion.js           # durations/easings read from tokens; reduced-motion aware
```

Routing is hash-based (`#/screens/scr-012`) so `python3 -m http.server` needs no rewrite
rules. Each route module exports `render(root, ctx)` and optional `title`, and registers
itself in `app.js`'s route table. One module per route — never a mega-file.

## Adding a screen

1. Write/locate `ux/screens/SCR-###-<slug>.md` first.
2. Create `routes/screens/scr-###-<slug>.js` exporting `render()`.
3. Render **every state** from the spec, switchable in the UI (a state selector in the route
   header), not just the default. This is what makes the prototype a spec rather than a mock.
4. Register the route and add it to `routes/index.js`.
5. Put the `SCR-###` ID in the route's heading so a reviewer can trace it.

## Adding a variant round

`new_round.py <slug>` generates `routes/variants/<slug>/` with an index that shows all
letters side by side (iframes at device widths) plus one module per letter. Variants import
the same components and tokens as production routes — a variant built from loose hexes cannot
be landed without a rewrite.

## Components

A UI-kit component lives once, at `ui-kit/components/<Component>/<Component>.js`, and is
imported by the prototype. Export a pure render function (or define a custom element):

```js
export function ButtonPrimary({ label, size = "md", state = "default", icon }) { … }
```

Props mirror the variant/state axes in `spec.md`, with identical names — those names travel
into the React/Compose/SwiftUI implementation. The `ui-kit` gallery route renders the full
cross-product of variants × sizes × states so a gap is visible rather than theoretical.

## Theming

`tokens.css` declares light values on `:root` and dark on `[data-theme="dark"]`, plus an
`@media (prefers-color-scheme: dark)` default for first load. The toggle in the shell sets
`document.documentElement.dataset.theme` and persists to `localStorage`. **No component ever
contains a theme conditional** — if one does, a semantic token is missing.

Every route must be viewed in both themes before it is shown to the operator.

## Animation conventions

Animation is in scope — "full set of functions including animations" is the point of having a
prototype rather than images.

- Durations and easings come from `motion.js`, which reads the motion tokens. No literal
  `0.3s ease` anywhere.
- Prefer CSS transitions and `@keyframes`; use the Web Animations API for sequenced or
  interruptible motion. No animation library.
- Animate `transform` and `opacity`. Animating `width`/`top`/`box-shadow` janks on mid-range
  Android, which is where the design will actually be judged.
- Honour `prefers-reduced-motion: reduce` globally: reduce to an opacity fade or
  `duration.instant`. `base.css` ships the global guard; do not defeat it per-component.
- Document each non-obvious motion in the screen spec's Behaviour section, with its tokens,
  so the mobile implementation matches rather than approximates.

## Content and data

Use realistic content at realistic lengths, including the longest string the product can
produce, and at least one non-Latin sample if the product localizes. Mock data lives in
`routes/_data/*.json` and is fetched — never inlined per route, so one edit updates every
screen that shows it.

## When the product already has a frontend

If the team ships React/Vue/Svelte and wants the prototype inside that app, keep the
contract and move the implementation: routes under the app's router, components importing the
same `tokens.css`, and `design.config.json.prototype.command` updated to the real dev command.
The non-negotiable is **one command documented in `design/README.md` that a teammate can run
to interact with the current design**, not the specific stack.
