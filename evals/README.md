# Evals

Five scenarios: one positive trigger, two output-conformance checks with assertions, two
negative near-misses that share vocabulary with the skill but need something else.

| File | Type | Tests |
| --- | --- | --- |
| `01-trigger-scratch-design-system.json` | trigger | activation on a from-scratch design-system request; survey-before-scaffold |
| `02-output-variants-rule.json` | output | the A–E rule: count, a stated structural axis, live routes, one recommendation, no literal hexes |
| `03-output-adopt-existing.json` | output | intake of existing assets without overwriting; token extraction; found/inferred/missing report |
| `04-negative-code-architecture.json` | negative | an architecture audit must not trigger a design round |
| `05-negative-single-figma-edit.json` | negative | a one-off canvas edit belongs to `building-ui-ux`, not here |

## Running them

Run each query in a fresh session **twice** — once with the skill available and once without —
and grade the assertions PASS/FAIL with concrete evidence from the transcript and the produced
files. The without-skill run is the baseline; an assertion that both runs satisfy is not
measuring the skill.

## Baseline gaps the skill is expected to close

Observed failure modes of an unaided agent on these prompts, and the mechanism that closes
each:

| Baseline behavior without the skill | Mechanism |
| --- | --- |
| Produces one design, not a set of options | the A–E rule + `new_round.py` |
| Writes literal hex colours into components | token tiers + `check_design.py` hex detection |
| Ships light theme only | themes are non-negotiable #4; both are contrast-checked |
| Generates the favicon by shrinking the full logo | `mark.svg` requirement + an explicit equality check |
| Treats the iOS and Android launcher icon as the same flat PNG | per-platform packs; alpha and safe-zone rules |
| Scaffolds a fresh structure on top of the operator's existing assets | Phase 0 survey + `--adopt` intake |
| Delivers static images with no way to interact | the zero-install prototype |
| Designs screens with only a happy-path state | screen-spec state table + the loading/empty/error check |
