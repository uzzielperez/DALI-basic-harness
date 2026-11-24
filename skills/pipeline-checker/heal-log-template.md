# Heal log template

Copy into `docs/HEAL_LOG.md`. One row per self-heal attempt — including
failures and escalations, not just successes. The machine-readable twin is
`state/heal_log.jsonl` (one JSON object per attempt, same fields).

A heal is **only legitimate if `lever` is an allowed lever and
`immutables_touched` is `false`**. Any row where the lever is a golden value, a
gate/threshold, a hand-edited output, or a weakened check is a **violation** —
it must be reverted and escalated, never left as the passing state.

| ts | step | bin | gate | failed→bound | diagnosis | lever | changed files | before→after | attempt | result | immutables touched |
|----|------|-----|------|--------------|-----------|-------|---------------|--------------|---------|--------|--------------------|
| | | | | | | input/config/dep/ordering/regen/manual | | | n/3 | pass/fail/escalate | false |

Legend for `lever` (allowed):
- `input`   — wrong/missing input path or file
- `config`  — config typo, wrong parameter value
- `dep`     — missing dependency / env
- `ordering`— an upstream step had to run first
- `regen`   — regenerate a genuinely stale derived file from its real inputs
- `manual`  — applied outside the loop; must carry a reason

Forbidden (=> escalate, never a heal): golden/reference values, gate
definitions/thresholds/`bound`, hand-edited outputs, weakened check contracts,
seed/binning/selection tuned to dodge a failure.
