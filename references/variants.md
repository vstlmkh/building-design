# Variants — the A–E rule

How to produce several options that are genuinely different, and how to present them so the
operator can decide quickly.

## Contents

- Why several
- How many
- Choose an axis first
- Axis catalogue
- The anti-sameness check
- Rendering variants
- Presenting variants
- Landing the decision

## Why several

A single proposal forces the operator into a yes/no on *your* taste. Several options along a
stated axis turns it into a design conversation: the operator can say "B's layout with D's
tone", which is information you cannot get from one option. It also surfaces the brief's
unstated constraints — the reason a variant gets rejected is usually a requirement nobody
wrote down.

## How many

- **Five (A–E)** — the default for anything open-ended: a banner, a landing page, a logo
  direction, an onboarding screen, an empty state.
- **Three (A–C)** — acceptable when the brief is tightly constrained (an existing system, a
  fixed layout, a single changed property), or when the operator asks for fewer.
- **One** — never. If the answer is genuinely forced, say *why* it is forced and show the two
  rejected directions anyway, briefly.

More than five is noise; by F the options are permutations.

## Choose an axis first

Before drawing anything, write one line: **"A–E vary by ___."** Then make each letter an
honest extreme of that axis, not a dial at 20/40/60/80%. Two axes at once is acceptable
(layout × tone); three is unreadable.

## Axis catalogue

| Axis | A ↔ E endpoints | Use for |
| --- | --- | --- |
| **Layout** | centred stack ↔ split asymmetric ↔ full-bleed ↔ grid ↔ overlay | banners, landings, heroes, cards |
| **Hierarchy** | one dominant element ↔ co-equal elements | screens with competing CTAs |
| **Density** | spacious/editorial ↔ compact/utilitarian | dashboards, lists, tables |
| **Tone** | playful ↔ neutral ↔ authoritative | marketing, empty states, errors |
| **Imagery** | type-only ↔ illustration ↔ photo ↔ 3D/abstract ↔ product screenshot | heroes, cards, stores |
| **Motion** | static ↔ subtle reveal ↔ sequenced ↔ continuous ambient | landings, onboarding |
| **Colour strategy** | neutral + one accent ↔ duotone ↔ gradient ↔ full-bleed brand | banners, promo |
| **Flow shape** | one long screen ↔ stepped wizard ↔ progressive disclosure ↔ modal | forms, onboarding |
| **Mark construction** (logos) | lettermark ↔ wordmark ↔ abstract symbol ↔ pictorial ↔ combination | brand rounds |
| **Nav model** | tabs ↔ drawer ↔ bottom sheet ↔ stack ↔ search-first | app IA |

## The anti-sameness check

Before showing them, test the set. If you cannot answer all four, redo the weak variants.

1. **Thumbnail test** — at 120px wide with no colour, are the layouts still distinguishable?
   If not, the variation is cosmetic.
2. **One-sentence test** — can each variant be described in one sentence that does not apply
   to any other? "A: single centred claim, no imagery." / "B: product shot bleeding off the
   right edge, copy left."
3. **Trade-off test** — each variant must be *better at something* and *worse at something*
   than the others. A variant that is strictly dominated is filler; replace it.
4. **Constraint test** — at least one variant should push against a brief constraint, with
   the tension named. That is where the useful conversation happens.

Never vary only: hue, corner radius, font weight, button size, or shadow depth. Those are
token edits, not variants.

## Rendering variants

Every variant is a **live prototype route** under `variants/<round>/<letter>/`, not a static
picture — the operator must be able to hover, click, resize, and toggle the theme. Each
variant:

- uses the real tokens and real UI-kit components (a variant built from loose hexes cannot be
  landed without a rewrite);
- renders in **both themes** — operators pick in light and ship in dark more often than you
  would expect;
- is reachable from the round's index route so they can be flipped through side by side;
- includes the real content length, not lorem ipsum — a layout that only works at 40
  characters is a layout that does not work.

## Presenting variants

Present in chat as a compact table, then the link to the prototype route. Per variant:
**label · one-sentence concept · the axis position · best for / worst at**. End with your
recommendation and the single reason for it — a recommendation is required; a neutral menu
pushes the decision back onto the operator.

```
Round: 2026-10-17-banner · A–E vary by layout × imagery · http://localhost:4321/variants/banner

A  Centred claim, no imagery        strongest message, weakest scroll-stop
B  Split: copy left, product right  clearest product comprehension, needs a good screenshot
C  Full-bleed gradient + overlay    most scroll-stopping, worst on small screens
D  Editorial: oversized type        most distinctive, least conventional
E  Compact strip for in-app use     reusable everywhere, lowest impact

Recommendation: B — the brief's goal is comprehension, not awareness.
```

## Landing the decision

On approval, fill `DECISION.md` in the round folder:

```markdown
# Decision — <round>

**Chosen:** C (with B's headline treatment)
**Date:** YYYY-MM-DD · **Decided by:** <operator>

## Why
<one paragraph — the goal it serves, not "it looks better">

## Rejected
- A — <reason>
- B — <reason, plus what was salvaged>
- D — <reason>
- E — <reason, and the condition under which it would win>

## Consequences
- New tokens / components added: …
- Follow-ups: …
```

Then delete the rejected variants' route files and promote the chosen one. `DECISION.md`
stays forever — "why not B" is the most re-litigated question on any design team.
