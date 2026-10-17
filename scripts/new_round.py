#!/usr/bin/env python3
"""Start an A-E variant exploration round: folder, BRIEF.md, prototype routes, DECISION.md.

Exit codes: 0 ok · 1 round already exists · 2 bad usage
"""
import argparse
import datetime as _dt
import json
import re
import sys
from pathlib import Path

LETTERS = "ABCDE"

BRIEF = """# Brief — {slug}

**Date:** {date}
**Axis:** A–{last} vary by <state the axis here before drawing anything>

## Operator prompt
> {prompt}

## Clarified
| Question | Answer / assumed default |
| --- | --- |
| Where does it live, who sees it? | |
| The one action or outcome it must produce? | |
| What content is fixed (real copy, assets)? | |
| What must it not do (brand / legal / technical)? | |

## Constraints
-

## Variants
| | Concept (one sentence) | Axis position | Best at | Worst at |
| --- | --- | --- | --- | --- |
{rows}
"""

DECISION = """# Decision — {slug}

**Status:** PENDING OPERATOR REVIEW
**Chosen:** —
**Date:** — · **Decided by:** —

## Why
<the goal it serves, not "it looks better">

## Rejected
{rejected}

## Consequences
- New tokens / components added:
- Follow-ups:
"""

INDEX_JS = """// Round index: all variants side by side at device widths, in the current theme.
const LETTERS = {letters};
const SLUG = "{slug}";

export function render(root) {{
  root.innerHTML = `
    <section class="page">
      <h1>Round: ${{SLUG}}</h1>
      <p class="lede">A–{last} vary by <strong>&lt;axis&gt;</strong>. Toggle the theme in the bar —
      every variant must work in both. Open one full-screen to interact with it.</p>
      <div class="variant-grid">
        ${{LETTERS.map((l) => `
          <figure class="variant">
            <figcaption><strong>${{l}}</strong> <a href="#/variants/${{SLUG}}/${{l.toLowerCase()}}">open</a></figcaption>
            <iframe src="index.html#/variants/${{SLUG}}/${{l.toLowerCase()}}" width="390" height="720"
                    title="Variant ${{l}}" loading="lazy"></iframe>
          </figure>`).join("")}}
      </div>
    </section>`;
}}
"""

VARIANT_JS = """// Variant {letter} — <one-sentence concept>
// Axis position: <where this sits on the round's axis>
// Build from real UI-kit components and semantic tokens only; a variant made of loose
// hexes cannot be landed without a rewrite.
import {{ ButtonPrimary }} from "../../../components/ButtonPrimary.js";

export function render(root) {{
  root.innerHTML = `
    <section class="page">
      <h1>{slug} — variant {letter}</h1>
      <p class="lede">Replace this with the variant. Use real content at realistic length,
      not lorem ipsum.</p>
      ${{ButtonPrimary({{ label: "Primary action", size: "lg" }})}}
    </section>`;
}}
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("slug", help="short kebab-case name, e.g. 'banner' or 'onboarding'")
    ap.add_argument("--dest", default=".", help="repo root containing design/")
    ap.add_argument("--variants", type=int, default=5, choices=(3, 4, 5))
    ap.add_argument("--prompt", default="<paste the operator's prompt here>")
    ap.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")
    a = ap.parse_args(argv)

    slug = re.sub(r"[^a-z0-9]+", "-", a.slug.lower()).strip("-")
    if not slug:
        print("ERROR: slug must contain letters or digits", file=sys.stderr)
        return 2
    date = a.date or _dt.date.today().isoformat()

    root = Path(a.dest).resolve()
    design = root / "design" if (root / "design" / "design.config.json").exists() else root
    if not (design / "design.config.json").exists():
        print(f"ERROR: no design workspace at {design}. Run check_design.py --survey first.",
              file=sys.stderr)
        return 2
    cfg = json.loads((design / "design.config.json").read_text())
    proto = design / cfg.get("paths", {}).get("prototype", "prototype")

    letters = list(LETTERS[:a.variants])
    round_dir = design / cfg.get("paths", {}).get("variants", "variants") / f"{date}-{slug}"
    if round_dir.exists():
        print(f"ERROR: round already exists: {round_dir}", file=sys.stderr)
        return 1
    round_dir.mkdir(parents=True)

    rows = "\n".join(f"| {l} | | | | |" for l in letters)
    (round_dir / "BRIEF.md").write_text(
        BRIEF.format(slug=slug, date=date, last=letters[-1], prompt=a.prompt, rows=rows))
    (round_dir / "DECISION.md").write_text(DECISION.format(
        slug=slug, rejected="\n".join(f"- {l} — " for l in letters)))

    rdir = proto / "routes" / "variants" / slug
    rdir.mkdir(parents=True, exist_ok=True)
    (rdir / "index.js").write_text(INDEX_JS.format(
        letters=json.dumps(letters), slug=slug, last=letters[-1]))
    for l in letters:
        (rdir / f"{l.lower()}.js").write_text(VARIANT_JS.format(letter=l, slug=slug))

    print(f"Round created: {round_dir}")
    print(f"Routes:        {rdir}")
    print("\nNext:")
    print(f"  1. Fill the axis line in BRIEF.md BEFORE drawing — 'A–{letters[-1]} vary by ___'.")
    print("  2. Register the routes in prototype/routes/index.js:")
    print(f'       "/variants/{slug}": {{ title: "{slug}", load: () => '
          f'import("./variants/{slug}/index.js") }},')
    for l in letters:
        print(f'       "/variants/{slug}/{l.lower()}": {{ load: () => '
              f'import("./variants/{slug}/{l.lower()}.js") }},')
    print("  3. Run the anti-sameness check (references/variants.md) before showing the operator.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
