---
name: pipeline-checker
description: Audits an analysis note, draft or Overleaf project against its reconstruction/analysis code repo — extracts the pipeline steps, builds the DAG and gate inventory, and produces a missing-results matrix (per bin / per year / per category) mapping every FIXME or blank number to the concrete pipeline command to run (e.g. per-year Snakemake). Analysis-agnostic: works for any binned analysis (any decay, any binning), not one channel. Use when the user asks what still needs to be piped/run for an analysis, to cross-check a draft against the repo, or to refresh the results-by-bin table.
---

# Pipeline checker (audit + run mapping)

This skill is **analysis-agnostic**. It carries no channel-specific knowledge.
Before doing anything, resolve the four anchors for *your* analysis; every
concrete command later is derived from these, never hard-coded.

## Step 0 — Resolve the four anchors

| Anchor | What it is | How to find it in a new repo |
|--------|------------|------------------------------|
| `REPO` | root of the analysis/reconstruction code | dir with `Snakefile` / `python/<step>/` / `config_*.yaml` |
| `DRAFT` | the note/draft being audited | user-provided PDF path or Overleaf project id |
| `HARNESS` | verification harness (gates, sandbox) | dir with the sandbox runner / gate definitions |
| `GOLD` | pinned reference values to check against | `*.json` reference files, published-paper PDFs |

Also resolve the **binning axis** the analysis is segmented on — years, magnet
polarity, `q²` bins, decay modes, categories, etc. — because the matrix columns
are *your* bins, not a fixed list. Record all of these in `state/anchors.yaml`
so a later session does not have to rediscover them.

If any anchor is ambiguous, STOP and ask the human; never guess a repo path or
a reference value.

## Mode 1 — Audit (default, read-only)

1. **Extract steps from the draft.** PDF: extract text with a PDF lib
   (`pymupdf`/`pdfplumber`). Overleaf: pull the `.tex` via the overleaf tooling.
   Collect: section titles, table captions, every `FIXME`, every blank `± `
   cell, every "TBD"/"UPDATE".
2. **Extract steps from the repo.** Pipeline docs, directory order
   (`python/<step>/`), Snakemake rules and per-bin configs (`config_<BIN>.yaml`),
   and the orchestrator wrapper if present.
3. **Split pipeline variants per bin.** The same bin can carry *separate*
   pipelines with different inputs and purposes (e.g. a frozen-legacy "closure"
   pipeline validated against gold references vs. a "updated" pipeline feeding a
   later combination). Detect variants from config families (distinct config
   globs, frozen vs fresh input paths) and give each its own matrix columns —
   never merge their cells.
4. **Align the two lists.** Every draft section must map to a repo step and
   vice versa. Report: draft-only sections (unimplemented), repo-only steps
   (undocumented), order conflicts (e.g. MC corrections must precede BDT).
5. **Gate inventory.** From the harness, list each gate id, rule, and current
   pass/fail from the latest run (`runs/`, validation dashboard).
6. **Missing-results matrix.** Write a `docs/RESULTS_BY_<BIN>.md`-style table:
   rows = quantities (per-bin efficiency chain, yields, observables, syst
   total), columns = your bins, plus a golden-benchmark column. Cells:
   ✅ value · 🔶 partial · ❌ FIXME. Highlight the headline quantities against
   the golden values. Use `results-matrix-template.md` as the starting point.
7. **Report** in chat: counts (steps aligned, FIXMEs, gates failing) + path
   to the matrix. Detail goes in the doc, not chat.

Honesty rules: never fill a cell from memory or guesswork — only from the
draft, repo outputs, or pinned references; mark anything inferred
`needs_review`; never edit a golden reference to make a cell/gate pass.

## Mode 2 — Run mapping (execute what the audit found missing)

For each ❌ cell, emit and (with user OK) run the mapped command. Always go
through the orchestrator/wrapper if the repo has one, so checkpoints, rollback
and the corrector loop (Mode 3) happen. Discover the real command from the repo
(its `run-commands` doc, Snakefile targets, or step scripts) — do not assume a
channel's command.

Generic per-bin loop (substitute your step dir, config glob and bin list):

```bash
for BIN in <your bins>; do
  cd <step dir>
  snakemake --configfile config_${BIN}.yaml -j 4   # small test: add --dry-run first
done
```

Execution rules:
1. Validate on one small sample/bin first (`--dry-run`, then a bin that has
   gold references to check against).
2. Stop on first gate failure; enter **Mode 3 — audited self-heal** (bounded
   corrector loop), then escalate to the human with the gate's `proposed_fix`.
3. Respect blockers (a bin waiting on a fit topology, a decision, an external
   sample) — report them, do not work around them.
4. After a successful step: re-run the audit for the affected rows and update
   the matrix cells with values + source file path.

## Mode 3 — Audited self-heal (corrector loop, never silent)

When a gate fails, the skill may propose and apply a *bounded* correction and
re-run — but a heal is an **auditable event, not a quiet retry**. Two absolute
properties:

- **Every heal is reported** — in chat the same turn it happens, and in a
  persistent ledger (`state/heal_log.jsonl` + a `docs/HEAL_LOG.md` table). No
  heal may be collapsed into a generic "fixed" line.
- **We never cheat to make a gate pass.** A heal may only change the *input or
  the config* that produced the failure. The immutables below are the
  anti-cheating boundary; touching one to flip a gate is a violation, not a
  fix — STOP and escalate.

### Anti-cheating boundary (immutable during a heal)

| Never modify to pass a gate | Why |
|---|---|
| Golden / pinned reference values | the benchmark is the point of the gate |
| Gate definitions, thresholds, or the check `bound` | moving the goalposts |
| Pipeline outputs directly (hand-edit a result file) | faking the result |
| The check contract (`type`, `key`, `bound`) | weakening the test |
| Seeds / binning / selection to dodge a failure, unless the *plan* changed | tuning until it passes |

Allowed heal levers: fix a wrong input path, a config typo, a missing
dependency, an upstream step that must run first, a genuinely stale derived
file. If the only way to pass is on the forbidden side of that line, **it is
not a heal — escalate.**

### One heal = one append-only ledger record (emit before AND after)

```json
{
  "ts": "<ISO8601>", "step": "<step>", "bin": "<bin>",
  "gate": "<gate id>", "rule": "<gate rule>",
  "failed_value": "<observed>", "bound": "<threshold>",
  "diagnosis": "<one line>",
  "lever": "<input|config|dep|ordering|regen>",   // MUST be an allowed lever
  "changed_files": ["<path>", "..."],
  "before": "<value/state>", "after": "<value/state>",
  "attempt": 1, "max_attempts": 3,
  "result": "<pass|fail|escalate>",
  "immutables_touched": false                      // must stay false; true => violation, halt
}
```

Rules:
1. **Log before you re-run** (record with `result` pending), then update the
   same record with the post-run `result` — the ledger shows the *attempt*, not
   just the happy path.
2. **Max 3 attempts per gate.** On the 3rd failure, or the instant a lever
   would cross the boundary, set `result: escalate` and hand the human the
   gate id, both values, the diagnosis, and the `proposed_fix`.
3. **Report in chat the moment it happens**, one line per heal, e.g.:
   `🔧 heal: <step>/<bin> gate=<gate> lever=config <before>→<after> attempt 1/3 → PASS`
   Failures and escalations get the same visibility, never swallowed.
4. **Reflect the heal in the matrix**: a healed cell shows the value, the
   source file, *and* a heal marker linking to its `heal_log` entry — so a
   reader can tell a clean pass from a corrected one at a glance.
5. **Never batch or back-fill heals.** If a heal was applied outside this
   loop, record it as `lever: manual` with a reason, same fields.

## Outputs checklist (definition of done)

- [ ] `state/anchors.yaml` with REPO / DRAFT / HARNESS / GOLD + binning axis
- [ ] DAG (mermaid) with the hard ordering constraints marked
- [ ] Gate inventory with current status
- [ ] Missing-results matrix per bin with golden column
- [ ] FIXME → command map (Mode 2 table), blockers listed
- [ ] `state/heal_log.jsonl` + `docs/HEAL_LOG.md` — every heal logged, all
      `immutables_touched` false, escalations surfaced (empty file OK if no heals)
- [ ] Chat summary: N aligned / N missing / N gates failing + doc path
