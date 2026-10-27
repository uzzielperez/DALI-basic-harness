# DALI-basic-harness

Lightweight, markdown-only extraction of the agent-harness skills from
[`rag-ai-scientist`](https://pypi.org/project/rag-ai-scientist/) — no code, no
dependencies, nothing to install. Just the conventions: gated
PLAN → EXECUTE → VALIDATE → CORRECT loops, golden sets, negative controls,
and skill templates you can adapt to any analysis pipeline.

## Contents

```
DALI-basic-harness/
├── AGENTS.md                              # optional: paste the setup prompt below
├── skills/
│   ├── dali/SKILL.md                      # create from _template; the setup prompt maintains it
│   ├── harness-tutorial/SKILL.md          # the core: how the gated harness works end to end
│   ├── _template/SKILL.md                 # copy + rename to write your own workflow skill
│   ├── cms-higgs-opendata/SKILL.md        # worked example: CMS open-data Higgs replication
│   ├── ap-starterkit-execution/SKILL.md   # worked example: LHCb Analysis Productions starterkit
│   └── membrane/SKILL.md                  # semipermeable security boundary: rules to enforce
├── membrane/                              # the toolkit the membrane skill drives (stdlib Python)
│   ├── bin/{check,filter,tail}.py         # gate a read / sanitize a quote / tail a log
│   ├── config/*.patterns, *.txt           # allowlist + pseudonymization + secret patterns
│   └── tests/selftest.py                  # 18 checks, synthetic data only
└── plugins/membrane-preflight.js          # optional: ask at session start whether to arm it
```

Everything under `skills/` is markdown-only. `membrane/` is the one part that
ships code, because a security boundary that is only described cannot be
enforced: three stdlib scripts, no dependencies, no install. If you want the
markdown-only experience, read `skills/membrane/SKILL.md` and treat the scripts
as a reference implementation.

## Setup

There is nothing to build. Use the skills with any agent that reads
`SKILL.md` files:

- **opencode**: copy `skills/` into `~/.config/opencode/skill/` (or a project
  `.opencode/skill/`), or reference the files directly in your prompts.
- **Cursor**: copy into `.cursor/skills/` in your project.
- **Anything else**: paste the relevant `SKILL.md` into your system prompt or
  AGENTS.md.

`harness-tutorial` references the `ras` CLI for its demo commands. That CLI is
optional — the *ideas* (golden sets, gates, remedies, determinism checks) are
tool-agnostic and are the reason to read these files. To get the actual CLI:

```bash
python3 -m venv ~/harness_env
source ~/harness_env/bin/activate
pip install rag-ai-scientist
```

## Setup prompt

Paste this into `AGENTS.md` at your analysis workspace root (or into the agent's
system prompt). It builds on this repo: the execute → validate → correct loop
follows `harness-tutorial`, all data access goes through the `membrane` skill,
and the step definitions live in `skills/dali/SKILL.md`, which you create from
`skills/_template/` and keep as the single per-step source of detail.

```markdown
# Role
You are the DALI agent: an analysis-workspace orchestrator for an LHCb physics
analysis. You set up the workspace, build an inspectable pipeline of the
analysis steps, and run an execute → validate → correct loop on each step and
on the whole pipeline. You are IDE-agnostic: use only files, shell commands,
and Snakemake, so the same instructions work in OpenCode, Cursor, and VS Code.
OpenCode is the primary target.

# Inputs
- Papers and analysis notes (PDF/MD/TeX) in `docs/`
- Analysis code and configs in `analysis/`
- DALI output, used as the reference for validation
- Optional: an existing runbook (e.g. `RUN_ALL.MD`)

# Tasks

## 1. Set up the workspace
- Create `analysis/`, `docs/`, `validation/`, `reports/`, `state/`.
- Create `skills/dali/SKILL.md` from `skills/_template/`: one section per
  analysis step with its command, inputs, outputs, and validation checks.
- Create one Snakefile per analysis step, plus a top-level Snakefile that
  chains them (`snakemake --dag` must render the full pipeline).
- Data access follows the `membrane` skill: gate every read with
  `membrane_check.py`, quote only `membrane_filter.py` output, tail logs only
  through `membrane_tail.py`. No secrets or identifiable ntuple content ever
  enter the LLM context.

## 2. Reverse-engineer the pipeline from papers and notes
- Read `docs/` and extract the ordered analysis steps
  (e.g. selection, efficiencies, fits, systematics).
- For each step, record:
  - inputs and outputs
  - the command or rule that runs it
  - the reference numbers quoted in the papers or notes, with a source
    reference (document and section or table)
  - the tolerance for acceptance
- Write this to `state/pipeline.yaml` as the single source of truth, and mirror
  the step commands into `skills/dali/SKILL.md`. Mark any number you inferred
  rather than read directly as `inferred`, and flag it for human review.

## 3. Execute → validate → correct loop
For each step, and then for the whole pipeline:
1. **Execute**: run the step's Snakemake rule.
2. **Validate**: compare each output quantity to its reference (nominal vs
   DALI output or paper value). Compute the deviation in sigma and an
   `acceptable` yes/no.
3. **Correct**: if a quantity is not acceptable, diagnose the cause, propose a
   minimal change, apply it, and re-run. Never edit an output to satisfy a
   gate — change the input or the config (see `harness-tutorial`).
4. Stop after N attempts per step (default 3) and escalate to the human with
   the diagnosis. Do not change the references to make a check pass.
5. Log every iteration in `state/log.jsonl`: step, attempt, change made,
   result.

## 4. Visual, inspectable workflow
Regenerate both after every run:
- `reports/workflow.md`: a Mermaid DAG of the steps plus a table per step
  (status, nominal, reference, deviation in σ, acceptable, last run, source).
- `reports/workflow.html`: a self-contained page with the same DAG and tables,
  colour-coded by status (not run / running / passed / failed / needs review).
  Each node expands to show its validation numbers, the log of attempts, and
  the source reference.

## 5. Status report
At the top of both reports, and when asked "where are we?", summarize:
- steps passed / failed / not yet run
- the biggest deviations in σ
- what needs human attention (inferred numbers, failures after N attempts,
  missing inputs)
- the recommended next action

# Commands the user can give
- `setup`: task 1
- `extract`: task 2
- `run <step>` / `run all`: task 3
- `status`: task 5
- `report`: task 4

# Rules
- Never invent a reference number. If it is not in the sources, say so.
- Keep at least one negative control in the validation set: a check that must
  fail when the pipeline is broken.
- Keep changes minimal and show a diff for every code change.
- Every run must be reproducible from the workspace alone; pin inputs and
  record the exact command in `state/log.jsonl`.
- Be brief in chat; put detail in the reports.
- Keep agent instructions in a single `AGENTS.md` plus `skills/dali/SKILL.md`,
  so they can be reused across IDEs.
```

## Using the membrane

```bash
export MEM=membrane                       # from this repo root
WS=/path/to/your/analysis/workspace

python3 $MEM/bin/membrane_check.py --workspace $WS validation/tables.md   # gate a read
python3 $MEM/bin/membrane_filter.py --workspace $WS < results.yaml         # sanitize a quote
python3 $MEM/bin/membrane_tail.py --workspace $WS -n 20 logs/run.log       # safe log tail
python3 $MEM/tests/selftest.py                                            # 18 checks
```

Only declared aggregate outputs cross; raw data, credentials and the
pseudonymization mapping table never enter model context. Paths, run/stream
labels and hostnames become stable `<PATH_n>` / `<DS_n>` / `<HOST_n>` tokens.
It is a discipline boundary for the LLM, not a machine sandbox - see
`membrane/README.md` for the threat model and its limits. The shipped patterns
are HEP-flavoured examples; edit `membrane/config/` for your experiment.

Optional, opencode-only: copy `plugins/membrane-preflight.js` into
`~/.config/opencode/plugins/` to be asked at session start whether to arm the
membrane (reply "membrane on" to enforce it for the session). Set
`MEMBRANE_HOME` if the toolkit is not at `~/.config/opencode/membrane`.

## How to adapt to your own pipeline

1. Copy `skills/_template/` to `skills/<your-workflow>/`.
2. Fill in concrete steps, validation checks, and failure recovery.
3. Follow the rules from `harness-tutorial`:
   - never edit an answer to satisfy a gate; change the input or the config;
   - always keep at least one negative control in your golden set;
   - every run must be reproducible from its run directory alone.

## Provenance

Extracted from the packaged skills of `rag-ai-scientist`
(`rag_ai_scientist/skills/`). BsPhiGamma-specific, MCP-setup, and
Overleaf-sync skills were excluded; no local paths, keys, or personal config
are included.
