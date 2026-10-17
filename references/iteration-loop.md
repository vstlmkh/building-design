# The iteration loop

How to turn an operator prompt into a landed design: clarify → variants → verify → land,
looping on verification until approved.

## Contents

- The loop
- Phase 2 — clarifying questions
- Phase 5 — presenting for verification
- Handling feedback
- Vague feedback
- Contradictory feedback
- When the operator approves
- Non-interactive runs

## The loop

```
operator prompt
   ↓
analyze → ask only what is unanswered (≤5, batched, each with a default)
   ↓
UX grounding (if interactive) → A–E variants in the prototype
   ↓
present with a recommendation → operator verifies
   ↓                                  ↑
edits requested ──────────────────────┘   (loop; never land unapproved work)
   ↓ approved
land: move into structure, DECISION.md, tokens/UI kit, rebuild, update handoff/AGENTS.md
```

## Phase 2 — clarifying questions

Analyze the prompt against what the workspace already answers. Ask about what remains, and
nothing else.

Rules:
- **Batch them.** One message with up to five questions, not a five-turn interrogation.
- **Each question carries a recommended default**, so "defaults are fine" is a valid, complete
  answer. A question with no default is an unpaid tax on the operator.
- **Never ask what the repo answers.** Brand tone is in `brand.md`; the palette is in the
  tokens; the platforms are in `design.config.json`. Asking anyway signals the skill did not
  read the workspace.
- **Ask about consequences, not preferences.** "Should this banner live in-app too, or only on
  the marketing site?" changes the design. "Do you like blue?" does not.
- Ask in the operator's language (Russian prompts get Russian questions).

The four highest-yield questions for a typical request:

1. **Where does it live and who sees it?** (surface + audience → size, density, tone)
2. **What is the one action/outcome it must produce?** (→ hierarchy)
3. **What content is fixed?** (real copy, product shot, legal text → layout constraints)
4. **What must it not do?** (brand/legal/technical constraints → the variants' boundaries)

## Phase 5 — presenting for verification

Give the operator, in this order: the prototype URL, the compact variants table (see
[variants.md](variants.md)), your recommendation with one reason, and a short list of what you
deliberately did *not* do. Keep the chat message short — the prototype carries the detail.

Call out explicitly anything that changes the system rather than just this artifact: a new
token, a new component, a new pattern. Those need a louder yes than "this banner looks good."

## Handling feedback

Classify every piece of feedback before acting:

| Kind | Example | Action |
| --- | --- | --- |
| **Pick** | "go with C" | land it |
| **Graft** | "C but with B's headline" | build the graft, re-present as a single option |
| **Property edit** | "make the CTA bigger" | apply, re-present; if it recurs, it is a token change |
| **Direction change** | "none of these — it should feel calmer" | the axis was wrong; pick a new axis and run a fresh A–E round |
| **System change** | "the accent is too dark everywhere" | stop, raise it as a token-level change with its blast radius, then do a round on the token |

Always return to verification after edits. Never land on an assumption that the edit was what
the operator meant.

## Vague feedback

"Make it pop", "it feels off", "not quite there" are the normal case, not a failure. Convert
them before redesigning:

1. **Locate** — "Is it the whole thing, or mostly the top/the type/the colour?"
2. **Compare** — "Closer to A or to D?" Comparison is far easier than articulation.
3. **Name the axis** — translate the answer into an axis and show two options along it.

Do not silently guess at three changes at once; you lose the signal about which one worked.
Change one axis per iteration.

## Contradictory feedback

If new feedback contradicts an earlier decision, say so plainly, point at the `DECISION.md`
line, and ask which should win. Then update `DECISION.md` — a reversed decision that is not
recorded gets re-reversed next month.

## When the operator approves

Approval is explicit ("go with C", "ship it"), not inferred from silence or from "looks
nice". Then, in order:

1. Move the chosen artifact into its permanent home.
2. Fill `DECISION.md`, delete the rejected route files.
3. Promote any new pattern into `ui-kit/` and any new value into the token files.
4. `build_tokens.py` + `build_icons.py` if either source changed.
5. Update `handoff/AGENTS.md`, `ui-kit/README.md`, and `CHANGELOG.md`.
6. `check_design.py` must pass before you report done.

## Non-interactive runs

In a background or scripted run there is no operator to verify with. Do not block. Instead:
adopt the defaults, **state every assumption explicitly** at the top of the output, produce
the full A–E round, write `BRIEF.md` with the open questions, and leave `DECISION.md`
unfilled with a clear `PENDING OPERATOR REVIEW` marker. Nothing is landed without approval.
