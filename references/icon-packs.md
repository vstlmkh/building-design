# Icon packs

The exact deliverables per platform. "Outer" = the launcher/store icon the OS shows; "inner" =
icons used inside the product. Both are required for iOS and Android.

## Contents

- Source of truth
- Web
- iOS
- Android
- In-product (UI) icon set
- Verification

## Source of truth

Everything is generated from `icons/app/master.svg` — a **1024×1024 viewBox, square, full
bleed, no transparency in the artwork area, no text**. Keep the important mark inside the
central 70% so platform masks and Android's crop do not clip it.

`build_icons.py` rasterizes with whichever tool is available (`rsvg-convert`, `inkscape`,
`magick`, or headless Chrome) and exits `3` naming the install command when none is. It
assembles `.ico` and Xcode/Android metadata itself.

## Web — `icons/app/build/web/`

| File | Size | Notes |
| --- | --- | --- |
| `favicon.svg` | vector | from `brand/logo/mark.svg`, **not** the full logo; add a `prefers-color-scheme` variant if the mark needs one |
| `favicon.ico` | 16+32+48 | multi-image ICO, still needed for legacy and for some crawlers |
| `apple-touch-icon.png` | 180×180 | opaque background, no transparency — iOS does not composite it |
| `icon-192.png`, `icon-512.png` | PWA any | |
| `maskable-512.png` | 512×512 | artwork inside the central 80% safe circle; `"purpose": "maskable"` |
| `og-image.png` | 1200×630 | social card — brand lockup + product name, readable at 300px wide |
| `site.webmanifest` | — | `name`, `short_name`, `icons`, `theme_color`, `background_color` from the tokens |

## iOS — `icons/app/build/ios/`

**Outer (launcher / App Store).** A single `1024×1024` PNG, **no alpha channel**, sRGB, square
with no pre-applied corner radius — the system applies the mask. Modern Xcode takes the one
1024 asset and downscales; older projects still want the full size matrix, which the script
emits when `--legacy-sizes` is passed.

Current iOS wants three appearance variants, each 1024×1024, in
`AppIcon.appiconset/` with a generated `Contents.json`:

- **Light** — the default.
- **Dark** — designed against a dark surface; the artwork must keep contrast without relying
  on a light background. Omit the background layer where the system supplies it.
- **Tinted** — a **grayscale** rendition the system colourizes. Design it as luminance only;
  anything that depends on hue disappears here. This is the variant most often forgotten and
  the one that most often looks wrong.

**Inner (in-app).** A tab-bar / toolbar icon set from `icons/ui/`, exported as template PDFs
or SF Symbols-compatible shapes: single colour, `currentColor`, 24pt grid, aligned to Apple's
optical weights. Prefer an actual SF Symbol where one exists — a custom icon next to SF
Symbols looks off-weight. Ship @1x/@2x/@3x PNGs only for raster-only pipelines.

## Android — `icons/app/build/android/`

**Outer (launcher).** An **adaptive icon**: a 108×108dp canvas where only the central **72dp**
is guaranteed visible — OEM masks crop the rest, and the system animates (parallax) within
the margin. Three layers:

- `ic_launcher_foreground` — the mark, inside the 72dp safe zone, transparent background.
- `ic_launcher_background` — a full-bleed colour or shape layer.
- `ic_launcher_monochrome` — a single-colour silhouette for themed icons. Required; without
  it the launcher falls back to a washed-out auto-generated version.

Emitted as `mipmap-anydpi-v26/ic_launcher.xml` + `ic_launcher_round.xml` referencing the
layers, plus raster fallbacks in `mipmap-mdpi/hdpi/xhdpi/xxhdpi/xxxhdpi` (48/72/96/144/192 px)
for pre-API-26 devices.

**Play listing.** `play-store-512.png` — 512×512, 32-bit PNG, **no transparency**, no
pre-applied mask, and no "Google Play" or award badges in the artwork.

**Inner (in-app).** Vector drawables (`res/drawable/ic_*.xml`) on a 24dp grid with a 2dp
keyline, `android:tint="?attr/colorControlNormal"` so they follow the theme. Convert from
`icons/ui/*.svg`; do not hand-author the path data.

## In-product (UI) icon set — `icons/ui/`

One grid (24px default, recorded in `design.config.json`), one stroke width (1.5 or 2px, not
both), consistent terminals and corner radii, `fill="currentColor"` or `stroke="currentColor"`
— never a hardcoded hex, or the icons will not theme. Name by function (`action.delete`), and
record keywords in `icons/icons.manifest.json` so an agent can find the right icon without
opening every file.

If the product adopts an existing set (Lucide, Phosphor, Material Symbols), record *which*
and its licence in the manifest, and only author custom icons for what the set lacks — in its
style, on its grid.

## Verification

`check_design.py` verifies, per platform listed in `design.config.json`: the master SVG exists
and is square; every required output file is present; iOS 1024s carry no alpha; the Play icon
carries no alpha; the Android monochrome layer exists; the favicon derives from `mark.svg`
rather than a full lockup; and the manifest's `theme_color` matches the token value.

Specs drift between OS releases. Before a store submission, re-check the current Apple HIG and
Android launcher docs rather than trusting this file.
