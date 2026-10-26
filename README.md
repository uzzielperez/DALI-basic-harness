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
