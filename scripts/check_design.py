#!/usr/bin/env python3
"""Survey a repo for existing design, or enforce the design workspace's completeness rules.

  --survey <repo>   print the state: workspace | assets | empty, plus what was found
  <repo>            run the full check (exit 1 when the design is incomplete)

Checks the non-negotiables: brand, icon packs per declared platform, a UI kit with all
component states, light + dark themes that pass WCAG contrast, and a runnable prototype.

Exit codes: 0 pass · 1 FAIL findings present · 2 bad usage
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_tokens import flatten, load_tokens, resolve, themes_present  # noqa: E402

HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
VIEWBOX = re.compile(r'viewBox\s*=\s*"([-\d.\s]+)"')
REQUIRED_STATES = ("default", "hover", "focus", "disabled")
ASSET_GLOBS = ("*.svg", "*.png", "*.ai", "*.sketch", "*.fig", "*.penpot",
               "*token*.json", "tailwind.config.*", "*theme*", "*brand*", "*logo*", "*icon*")
SKIP_DIRS = {"node_modules", ".git", "build", "dist", ".next", "vendor", "Pods",
             "__pycache__", ".venv", "venv"}

findings = []


def add(level, msg, hint=""):
    findings.append((level, msg, hint))


# --- contrast --------------------------------------------------------------
def srgb_to_lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color):
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) < 6:
        return None
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * srgb_to_lin(r) + 0.7152 * srgb_to_lin(g) + 0.0722 * srgb_to_lin(b)


def contrast(fg, bg):
    lf, lb = luminance(fg), luminance(bg)
    if lf is None or lb is None:
        return None
    hi, lo = max(lf, lb), min(lf, lb)
    return (hi + 0.05) / (lo + 0.05)


# --- survey ----------------------------------------------------------------
def walk(root):
    for p in root.rglob("*"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file():
            yield p


def survey(repo: Path):
    cfgs = [p for p in walk(repo) if p.name == "design.config.json"]
    if cfgs:
        cfg_path = cfgs[0]
        try:
            cfg = json.loads(cfg_path.read_text())
        except json.JSONDecodeError as e:
            print(f"state: workspace (BROKEN manifest)\n  {cfg_path}: {e}")
            return 1
        print("state: workspace")
        print(f"  manifest : {cfg_path.relative_to(repo)}")
        print(f"  product  : {cfg.get('product', '?')}  v{cfg.get('version', '?')}")
        print(f"  platforms: {', '.join(cfg.get('platforms', []))}")
        print(f"  themes   : {', '.join(cfg.get('themes', []))}")
        print("\nRead design.config.json, brand/brand.md and the token files, then continue "
              "in this system's conventions. Do NOT scaffold a second workspace.")
        return 0

    hits = []
    for pat in ASSET_GLOBS:
        for p in repo.glob(f"**/{pat}"):
            if any(part in SKIP_DIRS for part in p.parts) or not p.is_file():
                continue
            hits.append(p.relative_to(repo))
    # Stylesheets only count when they actually carry a palette.
    for p in walk(repo):
        if p.suffix in (".css", ".scss") and len(set(HEX.findall(p.read_text(errors="ignore")))) >= 5:
            hits.append(p.relative_to(repo))
    hits = sorted(set(hits))

    if hits:
        print(f"state: assets  ({len(hits)} candidate files)")
        for h in hits[:40]:
            print(f"  {h}")
        if len(hits) > 40:
            print(f"  … and {len(hits) - 40} more")
        print("\nRun the intake protocol (references/adopting-existing.md) before scaffolding. "
              "Existing work is ground truth; never overwrite it.")
    else:
        print("state: empty")
        print("\nNo design found. Propose the structure to the operator, then:")
        print('  python3 scripts/scaffold_design.py --name "<Product>" --dest .')
    return 0


# --- full check ------------------------------------------------------------
def find_design(repo: Path):
    direct = repo / "design"
    if (direct / "design.config.json").exists():
        return direct
    if (repo / "design.config.json").exists():
        return repo
    for p in walk(repo):
        if p.name == "design.config.json":
            return p.parent
    return None


def check_brand(d: Path):
    brand = d / "brand" / "brand.md"
    if not brand.exists():
        add("FAIL", "brand/brand.md is missing", "the brand is non-negotiable #1")
    else:
        text = brand.read_text(errors="ignore")
        if "<audience>" in text or "<adjective>" in text:
            add("WARN", "brand/brand.md still contains scaffold placeholders",
                "positioning and personality must be filled in before design rounds")
        if "not*" not in text and "*not*" not in text and "and not" not in text:
            add("WARN", "brand personality has no 'and not' counterweights",
                "adjectives without an 'and not' constrain nothing")
    logo = d / "brand" / "logo"
    hints = {"logo-primary.svg": "the full lockup on a light background",
             "logo-mono.svg": "single-colour, currentColor — needed wherever the brand is tinted",
             "mark.svg": "the favicon-safe glyph; it is not the full lockup"}
    for required, why in hints.items():
        if not (logo / required).exists():
            add("FAIL", f"brand/logo/{required} is missing", why)
    primary, mark = logo / "logo-primary.svg", logo / "mark.svg"
    if primary.exists() and mark.exists():
        if primary.read_bytes() == mark.read_bytes():
            add("FAIL", "brand/logo/mark.svg is identical to logo-primary.svg",
                "below 32px a lockup is mud; design a dedicated mark")
    mono = logo / "logo-mono.svg"
    if mono.exists() and "currentColor" not in mono.read_text(errors="ignore"):
        add("WARN", "brand/logo/logo-mono.svg does not use currentColor",
            "a mono logo with a baked-in colour cannot be themed")


def check_tokens(d: Path, cfg):
    tdir = d / cfg.get("paths", {}).get("tokens", "tokens")
    if not tdir.is_dir() or not list(tdir.glob("*.tokens.json")):
        add("FAIL", "no *.tokens.json found", "run scaffold_design.py or place the token files")
        return None, None, {}
    tree, ext = load_tokens(tdir)
    flat = flatten(tree)
    declared = cfg.get("themes", ["light", "dark"])
    present = themes_present(flat, declared)
    missing = [t for t in declared if t not in present]
    if missing:
        add("FAIL", f"theme(s) with no token values: {', '.join(missing)}",
            "a design shipped in one theme only is incomplete")
    for t in present:
        for p in flat:
            try:
                resolve(flat, t, p)
            except SystemExit as e:
                add("FAIL", f"token '{p}' ({t}): {e}")
                return flat, present, ext
    return flat, present, ext


def check_contrast(flat, themes, ext):
    pairs = ext.get("contrastPairs") if ext else None
    if not pairs:
        add("WARN", "no $extensions.contrastPairs declared in semantic.tokens.json",
            "declare the fg/bg pairs the product actually uses so they get checked")
        return
    for theme in themes:
        for fg_p, bg_p, role in pairs:
            try:
                fg, bg = resolve(flat, theme, fg_p), resolve(flat, theme, bg_p)
            except SystemExit as e:
                add("FAIL", f"contrast pair {fg_p}/{bg_p}: {e}")
                continue
            ratio = contrast(str(fg), str(bg))
            if ratio is None:
                add("WARN", f"{theme}: {fg_p} on {bg_p} is not a plain colour — checked manually")
                continue
            need = 4.5 if role == "body" else 3.0
            if ratio < need:
                add("FAIL", f"{theme}: {fg_p} on {bg_p} = {ratio:.2f}:1 (needs {need}:1)",
                    "a palette that passes on white routinely fails on the dark surface")


def check_ui_kit(d: Path):
    comp_dir = d / "ui-kit" / "components"
    comps = [p for p in comp_dir.iterdir() if p.is_dir()] if comp_dir.is_dir() else []
    if not comps:
        add("FAIL", "ui-kit/components/ is empty", "the UI kit is non-negotiable #3")
        return
    for c in comps:
        spec = c / "spec.md"
        if not spec.exists():
            add("FAIL", f"ui-kit/components/{c.name}/spec.md is missing")
            continue
        text = spec.read_text(errors="ignore")
        low = text.lower()
        missing = [s for s in REQUIRED_STATES if s not in low]
        if missing:
            add("FAIL", f"{c.name}: spec.md does not define state(s): {', '.join(missing)}",
                "every component carries all states, not just default")
        for hexval in set(HEX.findall(text)):
            add("FAIL", f"{c.name}: spec.md hardcodes {hexval}",
                "that value belongs to a token first")
        for impl in c.glob("*.js"):
            body = impl.read_text(errors="ignore")
            for hexval in set(HEX.findall(body)):
                add("FAIL", f"{c.name}/{impl.name} hardcodes {hexval}")
            if "color.palette." in body or "--color-palette-" in body:
                add("FAIL", f"{c.name}/{impl.name} references a tier-1 primitive directly",
                    "components bind to semantic tokens; primitives are for semantic tokens only")


def check_prototype(d: Path, cfg):
    p = d / cfg.get("paths", {}).get("prototype", "prototype")
    if not p.is_dir():
        add("FAIL", "prototype/ is missing", "the runnable prototype is non-negotiable #5")
        return
    for required in ("index.html", "app.js", "run.sh"):
        if not (p / required).exists():
            add("FAIL", f"prototype/{required} is missing")
    run = p / "run.sh"
    if run.exists() and not run.stat().st_mode & 0o111:
        add("WARN", "prototype/run.sh is not executable", "chmod +x it, or teammates will "
            "double-click index.html and hit the file:// CORS error")
    if not (p / "styles" / "tokens.css").exists():
        add("FAIL", "prototype/styles/tokens.css is missing",
            "run: python3 scripts/build_tokens.py <design>")
    for js in p.rglob("*.js"):
        for hexval in set(HEX.findall(js.read_text(errors="ignore"))):
            add("WARN", f"prototype/{js.relative_to(p)} hardcodes {hexval}",
                "prototype colours must come from tokens or the design cannot be themed")
    readme = d / "README.md"
    if not readme.exists() or "run.sh" not in readme.read_text(errors="ignore"):
        add("FAIL", "design/README.md does not document how to run the prototype",
            "every teammate must be able to start it from the README alone")


def check_icons(d: Path, cfg):
    platforms = cfg.get("platforms", [])
    master = d / "icons" / "app" / "master.svg"
    if not master.exists():
        add("FAIL", "icons/app/master.svg is missing",
            "every launcher/store icon is generated from it")
    else:
        m = VIEWBOX.search(master.read_text(errors="ignore"))
        if not m:
            add("WARN", "icons/app/master.svg has no viewBox — it will not scale cleanly")
        else:
            nums = [float(x) for x in m.group(1).split()]
            if len(nums) == 4 and abs(nums[2] - nums[3]) > 0.5:
                add("FAIL", f"icons/app/master.svg is not square ({nums[2]}x{nums[3]})")
    build = d / "icons" / "app" / "build"
    expected = {
        "web": ["web/favicon.ico", "web/favicon.svg", "web/apple-touch-icon.png",
                "web/icon-192.png", "web/icon-512.png", "web/maskable-512.png",
                "web/site.webmanifest"],
        "ios": ["ios/AppIcon.appiconset/Contents.json", "ios/AppIcon.appiconset/icon-1024.png",
                "ios/AppIcon.appiconset/icon-1024-dark.png",
                "ios/AppIcon.appiconset/icon-1024-tinted.png"],
        "android": ["android/mipmap-anydpi-v26/ic_launcher.xml",
                    "android/drawable/ic_launcher_foreground.xml",
                    "android/drawable/ic_launcher_monochrome.xml",
                    "android/play-store-512.png"],
    }
    for plat in platforms:
        gone = [rel for rel in expected.get(plat, []) if not (build / rel).exists()]
        if gone:
            shown = ", ".join(gone[:3]) + (f" (+{len(gone) - 3} more)" if len(gone) > 3 else "")
            add("FAIL", f"icon pack incomplete for {plat}: {shown}",
                "run: python3 scripts/build_icons.py <design>")
    if "web" in platforms:
        mark = d / "brand" / "logo" / "mark.svg"
        fav = build / "web" / "favicon.svg"
        primary = d / "brand" / "logo" / "logo-primary.svg"
        if fav.exists() and primary.exists() and fav.read_bytes() == primary.read_bytes():
            add("FAIL", "favicon.svg was generated from the full logo, not from mark.svg")
    if not (d / "icons" / "ui").is_dir() or not list((d / "icons" / "ui").glob("*.svg")):
        add("WARN", "icons/ui/ has no icons yet", "the in-product icon set is part of the kit")
    else:
        for svg in (d / "icons" / "ui").glob("*.svg"):
            if HEX.search(svg.read_text(errors="ignore")):
                add("WARN", f"icons/ui/{svg.name} hardcodes a colour",
                    "UI icons use currentColor so they follow the theme")


def check_ux(d: Path):
    screens = list((d / "ux" / "screens").glob("SCR-*.md")) if (d / "ux" / "screens").is_dir() else []
    for s in screens:
        low = s.read_text(errors="ignore").lower()
        missing = [k for k in ("loading", "empty", "error") if k not in low]
        if missing:
            add("FAIL", f"ux/screens/{s.name} has no {', '.join(missing)} state",
                "a screen without loading/empty/error states is not specified")
        if "prototype:" not in low:
            add("WARN", f"ux/screens/{s.name} names no prototype route — the trace is broken")
    if screens and not list((d / "ux" / "flows").glob("FLOW-*.md")):
        add("WARN", "screens exist but ux/flows/ is empty",
            "a screen with no flow behind it is a guess")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--survey", action="store_true", help="detect existing design and stop")
    ap.add_argument("--strict", action="store_true", help="treat WARN as failure")
    a = ap.parse_args(argv)

    repo = Path(a.path).resolve()
    if not repo.is_dir():
        print(f"ERROR: not a directory: {repo}", file=sys.stderr)
        return 2
    if a.survey:
        return survey(repo)

    d = find_design(repo)
    if d is None:
        print("FAIL  no design workspace found (no design.config.json)")
        print("      run: python3 scripts/check_design.py --survey . first")
        return 1
    cfg = json.loads((d / "design.config.json").read_text())

    check_brand(d)
    flat, themes, ext = check_tokens(d, cfg)
    if flat:
        check_contrast(flat, themes, ext)
    check_ui_kit(d)
    check_prototype(d, cfg)
    check_icons(d, cfg)
    check_ux(d)

    fails = [f for f in findings if f[0] == "FAIL"]
    warns = [f for f in findings if f[0] == "WARN"]
    for level, msg, hint in findings:
        print(f"{level}  {msg}")
        if hint:
            print(f"      → {hint}")
    print(f"\n{'FAIL' if fails or (a.strict and warns) else 'PASS'}: "
          f"{len(fails)} failing, {len(warns)} warnings  [{d}]")
    return 1 if fails or (a.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
