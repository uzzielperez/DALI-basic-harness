# DALI-basic-harness

Lightweight, markdown-only extraction of the agent-harness skills from
[`rag-ai-scientist`](https://pypi.org/project/rag-ai-scientist/) — no code, no
dependencies, nothing to install. Just the conventions: gated
PLAN → EXECUTE → VALIDATE → CORRECT loops, golden sets, negative controls,
and skill templates you can adapt to any analysis pipeline.

## Contents

```
DALI-basic-harness/
├── skills/
│   ├── harness-tutorial/SKILL.md          # the core: how the gated harness works end to end
│   ├── _template/SKILL.md                 # copy + rename to write your own workflow skill
│   ├── cms-higgs-opendata/SKILL.md        # worked example: CMS open-data Higgs replication
│   ├── ap-starterkit-execution/SKILL.md   # worked example: LHCb Analysis Productions starterkit
│   └── membrane/SKILL.md                  # semipermeable security boundary: rules to enforce
├── membrane/                              # the toolkit the membrane skill drives (stdlib Python)
│   ├── bin/{check,filter,tail}.py         # gate a read / sanitize a quote / tail a log
│   ├── config/*.patterns, *.txt           # allowlist + pseudonymization + secret patterns
│   └── tests/selftest.py                  # 18 checks, synthetic data only
├── sandbox/                               # OS-level execution boundary (bubblewrap)
│   ├── bin/sandbox_run.sh                 # run EXECUTE-phase code confined
│   └── config/deny-paths.txt              # workspace paths hidden from sandboxed code
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

## Using the sandbox

The membrane filters what text enters model context; the sandbox confines what
code the harness executes (bubblewrap user namespaces: workspace read-write,
raw-data dirs invisible, no network, no host writes):

```bash
sandbox/bin/sandbox_run.sh --workspace $WS --timeout 600 -- python3 fit.py
```

Keep `sandbox/config/deny-paths.txt` in sync with the `!` denials in
`membrane/config/approved-crossings.txt`. See `sandbox/README.md`.

## Setup prompt: self-adapt the harness to your project

### Lazy version — "let the AI figure it out"

If you don't want to answer interview questions, paste just this:

```text
My project: <one or two sentences describing it>.

Adapt this DALI harness to my use case, no interview: inspect my workspace
(layout, data formats, outputs, logs) and infer everything you can. Propose
the full adaptation (membrane allowlist + patterns, sandbox deny paths,
skills/<my-workflow>/SKILL.md, ADAPTATION.md) with every inferred decision
marked [inferred] and every guess you could not verify marked [assumed].
Apply it, run membrane/tests/selftest.py plus one gate/filter/sandbox smoke
test, and end with a short list of the [assumed] items for me to confirm or
correct. Never guess a raw-data or credential path as safe: when unsure,
deny it.
```

You stay in control the same way as before: correct any `[assumed]` item
later by re-running the prompt with that one fact fixed; the agent edits
config, never validated outputs.

### Full version — interview

Paste this into your agent (opencode, Cursor, ...) in a session where this
repo's skills are available, replacing the first line with your project in a
few words:

```text
My project: <one or two sentences, e.g. "electron ID calibration on EESTool
in a containerized analysisbox workspace" or "ML jet tagging on OOD runs,
results as yaml + plots in out/">.

Adapt this DALI harness to my use case. Do not write anything yet: first
interview me. Ask one question at a time, max ~7 questions, each with
plausible default answers, covering:

1. workspace layout: where raw/forbidden data lives, where aggregate
   outputs, logs and validation tables are written;
2. what may cross to the model (aggregate outputs only? which formats?)
   and what must never cross (raw events, credentials, identifiers);
3. identifying metadata to pseudonymize: path prefixes, run/dataset/stream
   labels, hostnames, account names specific to my experiment;
4. token/secret formats my infrastructure issues (beyond the shipped
   patterns);
5. the EXECUTE-phase commands the harness must run, and whether they need
   network or write access outside the workspace (they should not);
6. what "validated" means for me: the 2-4 concrete checks and the lowest
   bin count allowed in quoted tables;
7. one golden example run and one negative control I can provide.

Then produce, editing files in this repo (never inventing paths I did not
confirm):

- membrane/config/approved-crossings.txt rewritten for my layout, keeping
  every '!' denial class;
- membrane/config/pseudonymize.patterns and secrets.patterns extended with
  my specifics (experiment rules above the generic ones);
- sandbox/config/deny-paths.txt in sync with the '!' denials;
- skills/<my-workflow>/SKILL.md from skills/_template/ with my concrete
  steps, validation gates and failure-recovery table;
- a short ADAPTATION.md summarizing the decisions and what to re-check
  when the workspace layout changes.

Finish by running membrane/tests/selftest.py plus one gate/filter/sandbox
smoke test against my real workspace, and report pass/fail per check.
```

The agent should iterate: wrong answer in the interview -> edit the config,
never the validated output (same rule as the gates). Re-run the prompt
whenever your pipeline evolves; ask for a diff instead of a rewrite.

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
