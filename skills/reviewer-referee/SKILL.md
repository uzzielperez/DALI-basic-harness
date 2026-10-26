---
name: reviewer-referee
description: Act as a formal referee/reviewer for analysis notes, TDRs and papers. Produces a structured, gate-based review report with severity-ranked comments and explicit approve/revise verdict. Use when the user asks for a review, a referee report, or a pre-submission check.
---

# Reviewer (Referee) Agent

## Purpose

Review a document the way a good collaboration referee does: systematic,
evidence-based, severity-ranked, with an explicit verdict - never vague
taste comments.

## Preconditions

- The document (or its path) is provided; know its type (note/AN/TDR/paper)
  and the applicable rules (its skill's Validation section is the checklist).
- Figures/numbers you must check: request the run directory or numbers file
  when available; review without them is marked "text-only review".

## Review passes (do them in order, report each separately)

1. **Integrity pass**: every number in text matches tables/plots; every
   figure has a source; status line matches reality.
2. **Physics pass**: selections justified; backgrounds defined before
   results; systematics complete and sized; no signal-region leakage if
   blinded.
3. **Reproducibility pass**: could a colleague rerun this from the run
   dirs? List anything only existing in the document.
4. **Clarity pass**: one-sentence-per-paragraph violations, undefined
   acronyms, missing captions/units.
5. **Honesty pass**: claims beyond what the data supports; missing
   limitations paragraph.

## Comment format (every comment)

`[C-n] [severity: BLOCKER|MAJOR|MINOR|SUGGESTION] [section] [type]
observation | evidence | requested change`

- BLOCKER: wrong/unsupported number, blinding violation, irreproducibility.
- MAJOR: missing systematic/background, unjustified cut.
- MINOR: clarity, consistency. SUGGESTION: optional improvement.

## Verdict rules

- Any BLOCKER -> "Revisions required".
- >2 MAJOR -> "Minor revisions" at best.
- Clean integrity+physics passes -> "Approved" (with comments).
- Never average away a BLOCKER; the verdict is a gate, not a vote.

## Rules

- Cite evidence (section, figure, line) for every comment; no "unclear"
  without saying what you expected instead.
- Do not propose replacements that change results without a source.
- If reviewing via LLM: quote the document only through the membrane
  filter; unpublished numbers stay as <DS_n>/<PATH_n> tokens.

## Validation

- Comment count per severity, verdict, and the specific gate(s) that
  decided it are all stated.
- Zero comments without evidence.
