---
name: <skill-name>
description: <One sentence: WHAT this subtask does and WHEN the dali orchestrator should load it. This string is the only thing the orchestrator sees before loading — make the trigger conditions and keywords explicit, e.g. "Exports trained models to ONNX and checks parity against the original. Use when dali reaches an onnx_export step or the user says export onnx / parity check.">
---

# <Skill title> — subtask skill for the DALI orchestrator

> Copy this whole folder, rename it to `<skill-name>/`, and fill the angle
> brackets. This is BOTH a template and a worked example: the shaded
> `<example>` lines show one concrete subtask (`onnx_export`) so you can see
> how each section plugs into the orchestrator. Delete the example lines when
> you are done.

## How this skill relates to the orchestrator

DALI is **one agent that morphs by loading skills** — it never forks its
execute → validate → correct loop into a new agent (see `skills/dali/SKILL.md`
"Morphing"). A subtask skill like this one:

- is **loaded on demand** by the `dali` orchestrator when a pipeline step needs
  it, matched by the `description` trigger words above;
- **does its one job**, then hands control back. It does NOT drive the
  pipeline, schedule other steps, or decide global order;
- **reuses the orchestrator loop**: it exposes a *run* command and a *check*
  contract; the orchestrator wraps them in execute → validate → correct (max 3
  attempts, then escalate).
- is **registered** in `state/pipeline.yaml` so the orchestrator knows the step
  exists and which skill fulfils it.

The four link points are marked **🔗 LINK** below. Get those right and the
skill composes correctly; everything else is free-form.

## Purpose

<What single subtask this performs, in one or two sentences.>
<example>Convert a trained BDT/DNN to ONNX and verify the exported graph
reproduces the original model's outputs within tolerance.</example>

## Preconditions

- <Environment / toolchain the subtask needs.>
- <Required inputs and where they come from in the workspace.>
- <Membrane: if this step reads data or results, gate every read with
  `.dali/membrane/bin/membrane_check.py` and quote only filtered output.>
<example: trained model at `analysis/bdt/model.pkl`; `onnx`, `onnxruntime`,
`numpy` in the env; runs confined via `sandbox/bin/sandbox_run.sh`.>

## Steps

<The concrete commands this subtask runs. Keep them runnable and ordered.>
<example>
1. `sandbox/bin/sandbox_run.sh --workspace . -- python scripts/export_onnx.py \
     --model analysis/bdt/model.pkl -o analysis/bdt/model.onnx`
2. `sandbox/bin/sandbox_run.sh --workspace . -- python scripts/onnx_parity.py \
     --ref analysis/bdt/model.pkl --onnx analysis/bdt/model.onnx \
     --report state/onnx_parity.json`
</example>

### 🔗 LINK 1 — run command (what the orchestrator executes)

State the exact command the orchestrator should run for this step, and the
outputs it produces. The orchestrator logs the attempt to `state/log.jsonl` and
captures these paths for rollback.
<example: run cmd = step 2 above; outputs = `analysis/bdt/model.onnx`,
`state/onnx_parity.json`.>

## Validation

<How the orchestrator decides PASS/FAIL for this step. Pick the check type the
dali loop understands: scalar-in-sigma, distribution chi2/KS p-value,
determinism hash, or a negative control that MUST fail when broken.>

### 🔗 LINK 2 — check contract (what the orchestrator asserts)

Give a machine-checkable condition and where the verdict lives, so the loop can
gate without guessing.
<example: PASS iff max|onnx_out − ref_out| < 1e-5 over the validation batch
(`state/onnx_parity.json: max_abs_diff`), AND the negative control (permuted
weights) FAILS the same bound. Verdict file: `state/onnx_parity.json`.>

### 🔗 LINK 3 — register the step in `state/pipeline.yaml`

Add an entry so the orchestrator can schedule and load this skill. Mirror the
existing entries' shape:
<example>
```yaml
- step: onnx_export
  skill: onnx_export          # this skill's folder name
  needs: [bdt_train]          # upstream steps (DAG edges)
  run: "scripts/onnx_parity.py --ref analysis/bdt/model.pkl --onnx analysis/bdt/model.onnx --report state/onnx_parity.json"
  check:
    type: scalar_sigma        # one of: scalar_sigma | dist_ks | determinism | negative_control
    file: state/onnx_parity.json
    key: max_abs_diff
    bound: 1.0e-5
  outputs:
    - analysis/bdt/model.onnx
    - state/onnx_parity.json
```
</example>

### 🔗 LINK 4 — capability-skill needs

If this subtask needs another capability mid-step, name it so the orchestrator
composes them (it will load them around the same loop, not call a new agent):

| Need | Skill to load |
|---|---|
| Reads data/results | `membrane` (always, before any read) |
| Formal gate review of this step | `reviewer-referee` |
| Quick inline feedback, no verdict | `reviewer-commenter` |
| Writes a workspace doc | `writing-internal-note` / `writing-analysis-note` / `writing-tdr` |
| Cross-repo recall at step start | `rag-memory` MCP (`brain_search` / `rag_search`) |

## Failure Recovery

- <Common failure modes and the corrector action for each.>
- <What counts as a genuine failure vs. a config mistake.>
- **Escalate to the human after 3 failed attempts** — never edit an output or a
  reference to satisfy the gate; change the input or the config.
<example: parity diff > bound usually means a preprocessing mismatch (feature
order / dtype), not an export bug — re-check the feature vector before touching
the exporter. Missing `onnxruntime` op is an env problem: report, do not
downgrade the check.>

## Definition of done

- [ ] Run command produced its declared outputs
- [ ] Check contract satisfied (verdict file shows PASS)
- [ ] Negative control failed as required
- [ ] `state/pipeline.yaml` entry present and DAG-consistent
- [ ] Attempt logged to `state/log.jsonl`
