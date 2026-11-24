# Authoring a DALI skill — a subtask that plugs into the orchestrator

> Website-ready page for dali-agent.web.cern.ch. Companion to
> `skills/_template/SKILL.md` (the fill-in template this guide is based on).

DALI is **one agent that morphs by loading skills** — it does *not* fork its
gated PLAN → EXECUTE → VALIDATE → CORRECT loop into a new agent per task. So
"adding a capability" never means "writing a new agent": it means **authoring a
subtask skill** the `dali` orchestrator can load on demand, run through the
same loop, and register in the pipeline DAG.

This guide shows the whole path, end to end, using an `onnx_export` subtask as
the running example.

## The mental model

A subtask skill:

- is **loaded on demand** by the orchestrator, matched by the trigger words in
  its `description` front-matter (the only thing the orchestrator sees before
  loading it);
- **does one job**, then hands control back — it never schedules other steps or
  decides global order;
- **reuses the orchestrator loop**: it exposes a *run* command and a *check*
  contract; the orchestrator wraps them in execute → validate → correct (max 3
  attempts, then escalate to the human);
- is **registered** in `state/pipeline.yaml` so the orchestrator knows the step
  exists and which skill fulfils it.

## 1. Copy the template

```bash
cp -r skills/_template/ skills/onnx_export/
```

Rename the folder to your skill name (the folder name is what you register in
`pipeline.yaml`). Every `<angle-bracket>` is a placeholder; the `<example>`
blocks in the template are a worked `onnx_export` instance — delete them once
your own content is in.

## 2. Write the `description` like a trigger

The `description` is a routing rule, not prose. State **what** it does and
**when** to load it, with concrete keywords the orchestrator (or a user) will
say:

```yaml
description: Exports trained models to ONNX and checks parity against the
  original. Use when dali reaches an onnx_export step or the user says
  "export onnx" / "parity check".
```

Vague descriptions never fire; over-broad ones fire on the wrong step.

## 3. Get the four 🔗 LINK points right

The template marks the four places that make a skill *compose* with the
orchestrator. Everything else is free-form.

| Link | What you provide | Why the orchestrator needs it |
|---|---|---|
| **LINK 1 — run command** | The exact command(s) to execute + declared outputs | It logs the attempt to `state/log.jsonl` and captures outputs for rollback |
| **LINK 2 — check contract** | A machine-checkable PASS/FAIL condition + verdict file | The loop gates without guessing — one of `scalar_sigma` / `dist_ks` / `determinism` / `negative_control` |
| **LINK 3 — register** | A `state/pipeline.yaml` entry (step, skill, needs, run, check, outputs) | It can schedule the step and load the right skill |
| **LINK 4 — capability needs** | Which other skills to compose mid-step (`membrane`, `reviewer-*`, `writing-*`, `rag-memory`) | It loads them around the *same* loop instead of spawning an agent |

### LINK 3 in full — the `pipeline.yaml` entry

```yaml
- step: onnx_export
  skill: onnx_export          # folder name
  needs: [bdt_train]          # upstream steps (DAG edges)
  run: "scripts/onnx_parity.py --ref analysis/bdt/model.pkl --onnx analysis/bdt/model.onnx --report state/onnx_parity.json"
  check:
    type: scalar_sigma        # scalar_sigma | dist_ks | determinism | negative_control
    file: state/onnx_parity.json
    key: max_abs_diff
    bound: 1.0e-5
  outputs:
    - analysis/bdt/model.onnx
    - state/onnx_parity.json
```

Pick the `check.type` the loop understands:

| Type | Use when | PASS condition |
|---|---|---|
| `scalar_sigma` | a number vs a reference | within bound / Nσ of the golden value |
| `dist_ks` | comparing distributions | KS/chi² p-value above threshold |
| `determinism` | stochastic step must be reproducible | output hash matches pinned seed run |
| `negative_control` | you must prove the check bites | the deliberately-broken input FAILS |

Keep at least one `negative_control` in any pipeline — a gate that can't fail
isn't a gate.

## 4. Respect the hard rules

These are inherited from the orchestrator and are **not** negotiable per-skill:

- **Gate every data read** through the membrane (`membrane_check.py` before a
  read; quote only `membrane_filter.py` output; tail logs via `membrane_tail.py`).
- **EXECUTE-phase code runs confined** via `sandbox/bin/sandbox_run.sh`.
- **Never edit an output or a reference to satisfy a gate** — change the input
  or the config.
- **Escalate to the human after 3 failed attempts.**

## 5. Verify before you rely on it

- [ ] `description` fires on the intended trigger and nothing else
- [ ] run command produces its declared outputs
- [ ] check contract yields a verdict file the loop can read
- [ ] `pipeline.yaml` entry present and DAG-consistent (`snakemake -n` passes)
- [ ] at least one negative control fails when the step is broken

## Where to go next

- Fill-in template: `skills/_template/SKILL.md`
- Orchestrator contract: `skills/dali/SKILL.md` ("Morphing")
- Verification loop mechanics: `skills/harness-tutorial/SKILL.md`
- Security boundary: `skills/membrane/SKILL.md`
