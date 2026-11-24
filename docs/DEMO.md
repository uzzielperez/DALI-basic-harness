# DALI — 20-minute demo for a collaborator

Goal: from an empty laptop to a working DALI workspace with a built RAG
brain and a planned reproduction, without reading the whole README.
Two routes; pick one (or show both).

## 0. Prerequisites (5 min, once)

| Requirement | Notes |
|---|---|
| Python 3.10+ venv | `python3 -m venv ~/dali-venv && source ~/dali-venv/bin/activate` |
| `pip install -U rag-ai-scientist` | needs **>= 0.1.10** (`pip show rag-ai-scientist` to check) |
| LLM key for the planner | `export GROQ_API_KEY=...` (free at console.groq.com), or `OPENAI_API_KEY` for any OpenAI-compatible endpoint. Without a key the brain still builds; only the plan/fix proposals are skipped. |
| (optional, CERN) bubblewrap + CVMFS | only needed for the sandbox and real LHCb data; not for this demo |

## Route A — `dali-onboard` (LangGraph state machine, one command)

```bash
mkdir ~/dali-demo && cd ~/dali-demo
dali-onboard --workspace ~/dali-demo
```

What to type at each prompt, and what you'll see:

1. **paper >** — path or URL of a paper/tutorial. Demo input: the LHCb
   charm-tutorial write-up (e.g. `docs/Tutorial/main.md` of the D0 -> 3pi
   tutorial repo).
2. **code >** — path or URL of the analysis codebase (git clone of the
   tutorial repo works; for gitlab.cern.ch use a local clone or a PAT in
   `~/.netrc`).
3. **run without asking each step? [y/N]** — answer `N` for the demo so you
   can show the human gates.
4. **model [small/base/large]** — `base` on a modern laptop; `small` if it
   feels slow. First run downloads the embedding model (~0.5-1.3 GB).
5. **Brain gate**: ask it a question you know the answer to, e.g.
   `What is the nominal D0 decay mode?` — check the cited chunks (scores
   and file paths are printed). Approve, or rebuild with a bigger model.
6. **Plan**: the LLM proposes 2-5 reproduction steps from the brain.
7. **Per-step gates**: run / skip / edit each step. The harness executes and
   validates each proposal; the LLM only suggests.
8. Session checkpoints in `.dali/onboard/` — kill it any time and rerun the
   same command to resume (it offers to).

Artifacts: `.dali/brain/` (vector store), `.dali/onboard/` (checkpoints).

## Route B — the agent loop inside your IDE (no LangGraph)

The agent itself is files + shell + Snakemake; it works in opencode, Claude
Code, Cursor, Codex, Copilot.

```bash
git clone https://github.com/uzzielperez/DALI-basic-harness.git /tmp/dali-harness
mkdir ~/dali-ws && cd ~/dali-ws
/tmp/dali-harness/install/install.sh --ide opencode --workspace "$PWD"
opencode        # then: /agent dali   (or just type: setup)
```

Demo script inside the agent (each command is one stage):

```text
setup        # scaffolds analysis/ docs/ state/ reports/ + skill
index        # static code graph of analysis/ into state/code_graph.json
claims       # reference numbers from docs/ into state/claims.yaml (with provenance)
reconcile    # groups code into steps -> state/pipeline.yaml, STOPS for your approval
build        # mirrors pipeline.yaml into Snakefiles; snakemake -n / --dag must pass
run all      # execute -> validate -> correct per step, max 3 attempts then escalate
report       # reports/workflow.md + workflow.html (DAG + per-step tables)
```

Talking points during the demo:

- **Membrane**: ask the agent to read a raw data list — it must refuse or
  return pseudonymized output (`membrane_check.py` DENY). Show the log line.
- **Claims rule**: point at a number that disagrees between doc text and a
  table — the agent files it under `state/open_questions.md` instead of
  picking one.
- **Gates**: a validation failure loops back to fix the *code*, never the
  reference value or the output.

## Expected end state (both routes)

```
~/dali-demo/
├── .dali/brain/        # searchable RAG index over paper + code
├── .dali/onboard/      # LangGraph checkpoints (resumable)
└── (Route B) analysis/ docs/ state/{pipeline.yaml,claims.yaml,log.jsonl}
                validation/ reports/workflow.html
```

## Troubleshooting

- `dali-onboard: command not found` -> old package; `pip install -U rag-ai-scientist`
  and confirm >= 0.1.10 (0.1.x < 0.1.10 has no `onboard` subcommand).
- Plan step says no LLM -> `GROQ_API_KEY` / `OPENAI_API_KEY` not exported in
  this shell.
- Brain hits look off-topic -> rebuild with `base` or `large`; `small` is a
  baseline, not the recommended quality.
- Snakemake stage fails on CVMFS paths -> that's the membrane doing its job;
  demo data lists must be in the allowlist, or run the demo without real data.

Full reference: `docs/SETUP.md` (install per IDE) and `README.md`.

---

## Appendix — paste-able prompt (agent-driven demo)

Precondition: harness installed per Route B, DALI agent open in the IDE.
Paste this as the first message; the agent drives the demo and pauses at
each gate for you:

```text
You are demonstrating this DALI workspace to a visitor. Run the demo
yourself, narrating briefly (one or two lines per stage) and STOPPING to
wait for my OK at each gate marked [GATE]. Never touch raw data directly:
gate every read through the membrane and show me the check output.

Demo script:
 0. Confirm the workspace is installed (AGENTS.md harness block, .dali/,
    skills). If missing, run setup first. Show me the tree. [GATE]
 1. Ask me for two paths: a paper/tutorial directory and an analysis
    codebase. Place them (or symlink them) under docs/ and analysis/. [GATE]
 2. index — build the code graph; tell me node/edge counts and the
    static/traced/inferred split from state/code_graph.json. [GATE]
 3. claims — extract reference numbers into state/claims.yaml with
    provenance. Then deliberately find one number that disagrees between
    doc text and a table, and show me it went to state/open_questions.md
    instead of being silently resolved. [GATE]
 4. reconcile — write state/pipeline.yaml; show me the step list and the
    DAG, and wait for my approval before proceeding. [GATE]
 5. build — mirror the pipeline into Snakefiles; run snakemake -n and
    --dag and show both pass. [GATE]
 6. Membrane demo — attempt to read one raw data list, show the DENY or
    pseudonymized output, then show the same file via membrane_filter.py
    output. Explain the rule in one sentence. [GATE]
 7. run <first step> — execute -> validate -> correct once, small input
    only. Show the validation checks and the state/log.jsonl entries.
    If a check fails, fix the CODE, never the reference or the output. [GATE]
 8. report — regenerate reports/workflow.md and workflow.html and give me
    both paths. [GATE]
End with a 5-line summary: what was built, what gates fired, what a real
analysis would add (real data allowlist, full-scale jobs, referee review).
```

Short variant (if the visitor just wants the feel in 2 minutes):

```text
Demo DALI in 2 minutes on this workspace: show the tree, run index and
claims, trigger one membrane DENY and show it, then render the DAG with
snakemake --dag and point at reports/workflow.html. One line of
explanation per step, stop after each.
```
