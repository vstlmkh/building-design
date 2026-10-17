#!/usr/bin/env python3
"""Generate the web / iOS / Android icon packs from icons/app/master.svg.

Rasterization needs one external tool (none ships with Python). The script detects
rsvg-convert, inkscape, magick/convert, or headless Chrome, and exits 3 naming the install
command when none is present. Everything else — the multi-image .ico, Xcode Contents.json,
the Android adaptive-icon XML, site.webmanifest — is assembled here with the stdlib.

Exit codes: 0 ok · 1 bad/missing master · 2 bad usage · 3 no rasterizer available
"""
import argparse
import json
import re
import shutil
import atexit
import struct
import subprocess
import tempfile
import sys
from pathlib import Path

VIEWBOX = re.compile(r'viewBox\s*=\s*"([-\d.\s]+)"')

# (binary, argv builder) in preference order: quality first, then availability.
RASTERIZERS = [
    ("rsvg-convert", lambda b, s, d, px: [b, "-w", str(px), "-h", str(px), "-o", str(d), str(s)]),
    ("inkscape", lambda b, s, d, px: [b, str(s), "--export-type=png", f"--export-filename={d}",
                                      f"--export-width={px}", f"--export-height={px}"]),
    ("magick", lambda b, s, d, px: [b, "-background", "none", "-density", "384", str(s),
                                    "-resize", f"{px}x{px}", str(d)]),
    ("convert", lambda b, s, d, px: [b, "-background", "none", "-density", "384", str(s),
                                     "-resize", f"{px}x{px}", str(d)]),
]
INSTALL_HINT = ("Install one of:\n"
                "  brew install librsvg        # rsvg-convert (recommended)\n"
                "  brew install imagemagick    # magick\n"
                "  brew install --cask inkscape\n"
                "  apt-get install librsvg2-bin | imagemagick")

WEB_PNGS = {"apple-touch-icon.png": 180, "icon-192.png": 192, "icon-512.png": 512,
            "maskable-512.png": 512}
ICO_SIZES = (16, 32, 48)
ANDROID_DPI = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}


_PROFILE = None


def chrome_profile():
    """A throwaway Chrome profile dir, created once and removed at exit."""
    global _PROFILE
    if _PROFILE is None:
        _PROFILE = tempfile.mkdtemp(prefix="build-icons-chrome-")
        atexit.register(shutil.rmtree, _PROFILE, True)
    return _PROFILE


def find_rasterizer():
    for name, build in RASTERIZERS:
        path = shutil.which(name)
        if path:
            return name, path, build
    for chrome in ("google-chrome", "chromium", "chromium-browser",
                   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                   "/Applications/Chromium.app/Contents/MacOS/Chromium"):
        path = shutil.which(chrome) or (chrome if Path(chrome).exists() else None)
        if path:
            def build(b, s, d, px):
                # s is an HTML wrapper (see rasterize): the SVG is sized exactly to the
                # viewport with zero margin, so the screenshot has no letterboxing.
                # --user-data-dir is mandatory: without it headless Chrome contends with the
                # user's running Chrome profile lock and hangs forever instead of erroring.
                return [b, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--no-first-run", "--no-default-browser-check",
                        f"--user-data-dir={chrome_profile()}",
                        "--force-device-scale-factor=1",
                        "--default-background-color=00000000",
                        f"--screenshot={d}", f"--window-size={px},{px}", s.resolve().as_uri()]
            return "chrome", path, build
    return None, None, None


CHROME_WRAPPER = """<!doctype html><meta charset="utf-8">
<style>html,body{{margin:0;padding:0;width:100%;height:100%;overflow:hidden}}
svg{{display:block;width:100%;height:100%}}</style>
{svg}
"""


def with_grayscale(svg: str) -> str:
    """Wrap the artwork in a saturate(0) filter.

    iOS colourizes the tinted variant from luminance alone, so shipping a colour image as
    `tinted` hides exactly the failure mode you need to see. Rendering it grayscale shows
    the designer what the system will actually do.
    """
    i = svg.find(">", svg.find("<svg")) + 1
    end = svg.rfind("</svg>")
    defs = ('<defs><filter id="__gray"><feColorMatrix type="saturate" values="0"/>'
            "</filter></defs>")
    return svg[:i] + defs + '<g filter="url(#__gray)">' + svg[i:end] + "</g></svg>"


def rasterize(tool, bin_path, build, src: Path, dst: Path, px: int, opaque_bg=None,
              grayscale=False):
    dst.parent.mkdir(parents=True, exist_ok=True)
    svg_text = src.read_text()
    if grayscale:
        svg_text = with_grayscale(svg_text)
    if opaque_bg:
        # iOS/Play icons must carry no alpha; flatten by compositing onto a solid rect.
        svg_text = with_background(svg_text, opaque_bg)
    tmp = None
    src_used = src
    if tool == "chrome":
        tmp = dst.parent / f".wrap-{dst.stem}.html"
        tmp.write_text(CHROME_WRAPPER.format(svg=svg_text))
        src_used = tmp
    elif opaque_bg:
        tmp = dst.parent / f".flat-{dst.stem}.svg"
        tmp.write_text(svg_text)
        src_used = tmp
    cmd = build(bin_path, src_used, dst, px)
    try:
        # 90s is generous for a single icon; past that the tool is wedged, not slow.
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        print(f"ERROR: {tool} timed out rendering {dst.name}. Install a dedicated "
              f"rasterizer instead of relying on the browser fallback:\n{INSTALL_HINT}",
              file=sys.stderr)
        return False
    finally:
        if tmp:
            tmp.unlink(missing_ok=True)
    if r.returncode != 0 or not dst.exists():
        print(f"ERROR: {tool} failed on {dst.name}:\n{r.stderr.strip()[:500]}", file=sys.stderr)
        return False
    return True


def with_background(svg: str, color: str) -> str:
    vb = VIEWBOX.search(svg)
    w = h = "1024"
    if vb:
        nums = vb.group(1).split()
        if len(nums) == 4:
            w, h = nums[2], nums[3]
    rect = f'<rect x="0" y="0" width="{w}" height="{h}" fill="{color}"/>'
    i = svg.find(">", svg.find("<svg"))
    return svg[:i + 1] + rect + svg[i + 1:]


def png_size(path: Path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


def write_ico(pngs, dst: Path):
    """Assemble a multi-image ICO. PNG-compressed entries are valid since Vista."""
    blobs = [p.read_bytes() for p in pngs]
    n = len(blobs)
    header = struct.pack("<HHH", 0, 1, n)
    offset = 6 + 16 * n
    entries, body = b"", b""
    for p, blob in zip(pngs, blobs):
        w, h = png_size(p)
        entries += struct.pack("<BBBBHHII", w % 256, h % 256, 0, 0, 1, 32, len(blob), offset)
        offset += len(blob)
        body += blob
    dst.write_bytes(header + entries + body)


def ios_contents(filenames):
    images = []
    for fn, appearance in filenames:
        entry = {"filename": fn, "idiom": "universal", "platform": "ios", "size": "1024x1024",
                 "scale": "1x"}
        if appearance == "dark":
            entry["appearances"] = [{"appearance": "luminosity", "value": "dark"}]
        elif appearance == "tinted":
            entry["appearances"] = [{"appearance": "luminosity", "value": "tinted"}]
        images.append(entry)
    return json.dumps({"images": images, "info": {"author": "build_icons.py", "version": 1}},
                      indent=2) + "\n"


ADAPTIVE_XML = """<?xml version="1.0" encoding="utf-8"?>
<!-- GENERATED by build_icons.py. 108dp canvas; only the central 72dp is guaranteed visible. -->
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
    <monochrome android:drawable="@drawable/ic_launcher_monochrome"/>
</adaptive-icon>
"""

BG_DRAWABLE = """<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <solid android:color="%s"/>
</shape>
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("design", nargs="?", default="design")
    ap.add_argument("--bg", default=None,
                    help="opaque background for iOS/Play icons (default: token "
                         "color.bg.surface light value, else #ffffff)")
    ap.add_argument("--legacy-sizes", action="store_true",
                    help="also emit the full pre-Xcode-14 iOS size matrix")
    a = ap.parse_args(argv)

    design = Path(a.design).resolve()
    if not design.is_dir():
        print(f"ERROR: not a directory: {design}", file=sys.stderr)
        return 2
    cfg_path = design / "design.config.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    platforms = cfg.get("platforms", ["web", "ios", "android"])

    master = design / "icons" / "app" / "master.svg"
    if not master.exists():
        print(f"ERROR: {master} not found. Every launcher/store icon is generated from it.\n"
              f"  It must be a square 1024x1024 viewBox, full bleed, no text.", file=sys.stderr)
        return 1
    svg = master.read_text()
    vb = VIEWBOX.search(svg)
    if vb:
        nums = [float(x) for x in vb.group(1).split()]
        if len(nums) == 4 and abs(nums[2] - nums[3]) > 0.5:
            print(f"ERROR: master.svg is not square ({nums[2]}x{nums[3]}). "
                  f"Platform masks assume a square canvas.", file=sys.stderr)
            return 1

    bg = a.bg or token_color(design, "color.bg.surface") or "#ffffff"
    tool, bin_path, build = find_rasterizer()
    if not tool:
        print("ERROR: no SVG rasterizer found.\n" + INSTALL_HINT, file=sys.stderr)
        return 3

    out = design / "icons" / "app" / "build"
    made = []

    # --- web ---------------------------------------------------------------
    if "web" in platforms:
        web = out / "web"
        web.mkdir(parents=True, exist_ok=True)
        mark = design / "brand" / "logo" / "mark.svg"
        if not mark.exists():
            print("ERROR: brand/logo/mark.svg missing — a favicon is not a shrunk logo.",
                  file=sys.stderr)
            return 1
        shutil.copyfile(mark, web / "favicon.svg")
        made.append("web/favicon.svg")
        tmp = []
        for px in ICO_SIZES:
            p = web / f".ico-{px}.png"
            if not rasterize(tool, bin_path, build, mark, p, px):
                return 1
            tmp.append(p)
        write_ico(tmp, web / "favicon.ico")
        for p in tmp:
            p.unlink()
        made.append("web/favicon.ico")
        for fn, px in WEB_PNGS.items():
            # apple-touch-icon is composited on an opaque background by iOS otherwise.
            src = master
            opaque = bg if fn == "apple-touch-icon.png" else None
            if not rasterize(tool, bin_path, build, src, web / fn, px, opaque):
                return 1
            made.append(f"web/{fn}")
        manifest = {
            "name": cfg.get("product", "App"),
            "short_name": cfg.get("product", "App")[:12],
            "icons": [
                {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
                {"src": "maskable-512.png", "sizes": "512x512", "type": "image/png",
                 "purpose": "maskable"},
            ],
            "theme_color": token_color(design, "color.accent.default") or bg,
            "background_color": bg,
            "display": "standalone",
        }
        (web / "site.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n")
        made.append("web/site.webmanifest")

    # --- iOS ---------------------------------------------------------------
    if "ios" in platforms:
        appicon = out / "ios" / "AppIcon.appiconset"
        appicon.mkdir(parents=True, exist_ok=True)
        dark_src = design / "icons" / "app" / "master-dark.svg"
        if not dark_src.exists():
            print("WARNING: icons/app/master-dark.svg is absent — the dark variant is a copy "
                  "of the light one. Design it against a dark surface before shipping.",
                  file=sys.stderr)
        variants = [("icon-1024.png", master, "any"),
                    ("icon-1024-dark.png", dark_src if dark_src.exists() else master, "dark"),
                    ("icon-1024-tinted.png", master, "tinted")]
        for fn, src, appearance in variants:
            # No alpha: iOS rejects icons with an alpha channel; flatten onto an opaque bg.
            flat_bg = "#000000" if appearance == "dark" else bg
            if not rasterize(tool, bin_path, build, src, appicon / fn, 1024, flat_bg,
                             grayscale=(appearance == "tinted")):
                return 1
            made.append(f"ios/AppIcon.appiconset/{fn}")
        (appicon / "Contents.json").write_text(
            ios_contents([(fn, ap_) for fn, _, ap_ in variants]))
        made.append("ios/AppIcon.appiconset/Contents.json")
        if a.legacy_sizes:
            for px in (20, 29, 40, 58, 60, 76, 80, 87, 120, 152, 167, 180):
                if not rasterize(tool, bin_path, build, master, appicon / f"icon-{px}.png", px, bg):
                    return 1
            made.append("ios legacy size matrix")
        print("NOTE: the tinted iOS variant is colourized by the system from luminance only — "
              "open icon-1024-tinted.png and confirm the mark still reads in grayscale.")

    # --- Android -----------------------------------------------------------
    if "android" in platforms:
        droid = out / "android"
        (droid / "mipmap-anydpi-v26").mkdir(parents=True, exist_ok=True)
        (droid / "drawable").mkdir(parents=True, exist_ok=True)
        (droid / "mipmap-anydpi-v26" / "ic_launcher.xml").write_text(ADAPTIVE_XML)
        (droid / "mipmap-anydpi-v26" / "ic_launcher_round.xml").write_text(ADAPTIVE_XML)
        (droid / "drawable" / "ic_launcher_background.xml").write_text(BG_DRAWABLE % bg)
        fg_src = design / "icons" / "app" / "foreground.svg"
        for name, src in (("ic_launcher_foreground", fg_src if fg_src.exists() else master),
                          ("ic_launcher_monochrome",
                           design / "icons" / "app" / "monochrome.svg")):
            target = droid / "drawable" / f"{name}.xml"
            if src.exists():
                target.write_text(svg_to_vector_note(src))
            else:
                target.write_text(svg_to_vector_note(master, mono=(name.endswith("monochrome"))))
            made.append(f"android/drawable/{name}.xml")
        for dpi, px in ANDROID_DPI.items():
            d = droid / f"mipmap-{dpi}"
            if not rasterize(tool, bin_path, build, master, d / "ic_launcher.png", px, bg):
                return 1
        made.append("android/mipmap-{mdpi…xxxhdpi}/ic_launcher.png")
        if not rasterize(tool, bin_path, build, master, droid / "play-store-512.png", 512, bg):
            return 1
        made.append("android/play-store-512.png")
        print("NOTE: Android crops everything outside the central 72dp of the 108dp canvas. "
              "Check ic_launcher_foreground against the safe zone before shipping.")

    print(f"\nBuilt with {tool}: {len(made)} artifacts under {out}")
    for m in made:
        print(f"  {m}")
    return 0


def token_color(design: Path, path: str):
    """Best-effort read of a semantic colour's default-theme value; None when unavailable."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from build_tokens import flatten, load_tokens, resolve
        tree, _ = load_tokens(design / "tokens")
        flat = flatten(tree)
        cfg = json.loads((design / "design.config.json").read_text())
        v = str(resolve(flat, cfg.get("defaultTheme", "light"), path))
        return v if v.startswith("#") else None
    except Exception:
        return None


def svg_to_vector_note(src: Path, mono: bool = False) -> str:
    """Wrap the SVG path data in a VectorDrawable shell.

    Only simple single-path SVGs convert losslessly this way; anything with gradients,
    groups or transforms must be converted in Android Studio (Vector Asset). The marker
    comment tells the implementer which case they are in.
    """
    text = src.read_text()
    paths = re.findall(r'<path[^>]*\bd="([^"]+)"', text)
    tint = ' android:tint="#000000"' if mono else ""
    head = ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<!-- GENERATED by build_icons.py from %s -->\n' % src.name)
    if not paths:
        head += ("<!-- WARNING: no simple <path> found. Re-import this SVG via Android Studio "
                 "> New > Vector Asset; this file is a placeholder. -->\n")
    body = "".join(f'    <path android:fillColor="{"#000000" if mono else "#FFFFFF"}" '
                   f'android:pathData="{d}"/>\n' for d in paths)
    return (head + '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
            f'    android:width="108dp" android:height="108dp"\n'
            f'    android:viewportWidth="108" android:viewportHeight="108"{tint}>\n'
            + body + "</vector>\n")


if __name__ == "__main__":
    sys.exit(main())
