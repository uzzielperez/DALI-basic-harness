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
│   ├── membrane/SKILL.md                  # semipermeable security boundary: rules to enforce
│   ├── writing-internal-note/SKILL.md     # doc skills: internal notes (INT/memo/progress)
│   ├── writing-analysis-note/SKILL.md     # doc skills: Analysis Notes / ASNs
│   ├── writing-tdr/SKILL.md               # doc skills: TDR / design documents
│   ├── reviewer-referee/SKILL.md          # agent: formal gate-based referee review + verdict
│   └── reviewer-commenter/SKILL.md        # agent: quick inline comments, no verdict
├── install/install.sh                     # one-command setup per IDE (see Setup below)
├── docs/SETUP.md                          # website-ready setup page (dali-agent.web.cern.ch)
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

## Setup — pick your IDE

**Download the harness** (any route; all give you everything below — no git or
CERN account needed for the first two):

```bash
# 1. ZIP, no git / no account
curl -fsSL -o dali-harness.zip https://github.com/uzzielperez/DALI-basic-harness/archive/refs/heads/main.zip
unzip dali-harness.zip && cd DALI-basic-harness-main
# 2. public GitHub mirror
git clone https://github.com/uzzielperez/DALI-basic-harness.git
cd DALI-basic-harness
# 3. CERN members with access — source of truth on GitLab (CERN SSO)
git clone https://gitlab.cern.ch/lasalle/DALI-nucleus
cd DALI-nucleus
```

Or pull it from PyPI, which ships the same skills, the DALI agent definition,
the membrane and the sandbox as package data of
[`rag-ai-scientist`](https://pypi.org/project/rag-ai-scientist/):

```bash
pip install rag-ai-scientist
PKG=$(python -c "import rag_ai_scientist, pathlib; print(pathlib.Path(rag_ai_scientist.__file__).parent)")
"$PKG/install/install.sh" --ide opencode --workspace "$PWD"   # from the installed tree
```

Since `rag-ai-scientist >= 0.1.10` the same package also ships the DALI
onboarding state machine: `dali-onboard --workspace <dir>` takes a paper and a
codebase (paths or URLs), builds a project RAG brain you test through a human
gate, then runs a plan → execute → validate → correct loop with a human gate
per step. See `docs/SETUP.md` ("One-command onboarding").

One command wires the DALI agent (skills + membrane + sandbox + instructions)
into your editor. Everything else in this repo stays markdown-only.

| IDE | Skills land in | Instructions file |
|---|---|---|
| [opencode](#opencode) | `.opencode/skill/` or `~/.config/opencode/skill/` | `AGENTS.md` |
| [Claude Code](#claude-code) | `.claude/skills/` or `~/.claude/skills/` | `CLAUDE.md` |
| [Cursor](#cursor) | `.cursor/skills/` or `~/.cursor/skills/` | `AGENTS.md` |
| [Codex](#codex) | `.codex/skills/` or `~/.codex/skills/` | `AGENTS.md` |
| [GitHub Copilot](#github-copilot) | `.github/skills/` | `AGENTS.md` + `.github/copilot-instructions.md` |
| [VS Code](#vs-code) | `.github/skills/` (native MCP client) | `AGENTS.md` |
| [Vibe (Mistral)](#vibe-mistral) | `.agents/skills/` | `AGENTS.md` |

Every target gets the same four things: the skills, the enforcement toolkits
copied to `<workspace>/.dali/{membrane,sandbox}`, a marker-delimited
instructions block, and a callable DALI agent (single source `install/dali-agent.md`, adapted per IDE: /agent dali, @dali, /dali prompt, custom mode) (re-running updates it in place, never duplicates;
`--uninstall` removes exactly what was installed).

### opencode

1. **Install opencode** — see [opencode.ai/docs](https://opencode.ai/docs)

   ```bash
   curl -fsSL https://opencode.ai/install | bash
   ```

2. **Install the DALI harness** — from your analysis workspace root:

   ```bash
    git clone https://github.com/uzzielperez/DALI-basic-harness.git /tmp/dali-harness
    /tmp/dali-harness/install/install.sh --ide opencode --workspace "$PWD"
   ```

   Add `--scope user` to install skills and the membrane-preflight plugin
   globally (`~/.config/opencode/`) instead of per workspace.

3. **Launch and say `setup`**

   ```bash
   opencode
   ```

4. **Try a prompt**

   ```txt
   setup
   ```

### Claude Code

1. **Install Claude Code** — see the [setup guide](https://docs.anthropic.com/en/docs/claude-code/setup)

   ```bash
   curl -fsSL https://claude.ai/install.sh | bash
   ```

2. **Install the DALI harness** — from your analysis workspace root:

   ```bash
   /tmp/dali-harness/install/install.sh --ide claude-code --workspace "$PWD"
   ```

3. **Launch and say `setup`**

   ```bash
   claude
   ```

4. **Try a prompt**

   ```txt
   extract the pipeline from the notes in docs/ and show me state/pipeline.yaml
   ```

### Cursor

1. **Install Cursor** — from [cursor.com](https://cursor.com); MCP support is
   built in.

2. **Install the DALI harness** — from your analysis workspace root:

   ```bash
   /tmp/dali-harness/install/install.sh --ide cursor --workspace "$PWD"
   ```

   Skills go to `.cursor/skills/` (repo) — use `--scope user` for
   `~/.cursor/skills/` shared across all your analyses.

3. **Open the workspace, launch the agent, say `setup`**
   Optional MCP servers (RAG, Overleaf, GitLab CERN): merge
   `.dali/mcp/cursor.json` into `~/.cursor/mcp.json`, then
   **Ctrl+Shift+P** → "MCP: Reload".

4. **Try a prompt**

   ```txt
   run all and give me status
   ```

### Codex

1. **Install Codex** — see the [Codex guide](https://developers.openai.com/codex/)

   ```bash
   npm i -g @openai/codex
   ```

2. **Install the DALI harness** — from your analysis workspace root:

   ```bash
   /tmp/dali-harness/install/install.sh --ide codex --workspace "$PWD"
   ```

3. **Launch and say `setup`**

   ```bash
   codex
   ```

4. **Try a prompt**

   ```txt
   status
   ```

### GitHub Copilot

1. **Install the Copilot extension** and enable agent mode in your editor.

2. **Install the DALI harness** — from your analysis workspace root:

   ```bash
   /tmp/dali-harness/install/install.sh --ide copilot --workspace "$PWD"
   ```

   Skills go to `.github/skills/`, and `.github/copilot-instructions.md` gets
   a pointer to `AGENTS.md` + `skills/dali/SKILL.md`.

3. **Open Copilot Chat in agent mode, say `setup`**

4. **Try a prompt**

   ```txt
   run selection and validate against the paper reference
   ```

### VS Code

VS Code is covered by the Copilot flow above (same skills dir), plus native
MCP: merge `.dali/mcp/vscode.json` via the MCP extension / settings.

```bash
/tmp/dali-harness/install/install.sh --ide vscode --workspace "$PWD"
```

### Vibe (Mistral)

1. **Install Vibe** — see the [install guide](https://docs.mistral.ai/vibe/code/cli/install-setup)

   ```bash
   curl -LsSf https://mistral.ai/vibe/install.sh | bash
   vibe --setup
   ```

2. **Install the DALI harness** — Vibe discovers project skills from
   `.agents/skills/`:

   ```bash
   /tmp/dali-harness/install/install.sh --ide vibe --workspace "$PWD"
   ```

3. **Add the optional MCP server** — merge `.dali/mcp/vibe.toml` into
   `~/.vibe/config.toml`, then `/reload` and `/mcp status` inside Vibe.

4. **Launch and say `setup`**

   ```bash
   vibe
   ```

### Verify the install (any IDE)

```bash
python3 .dali/membrane/tests/selftest.py        # 18 checks, synthetic data
sandbox/bin/sandbox_run.sh --workspace "$PWD" --timeout 60 -- echo confined
```

Then drive the agent with the commands the setup prompt defines: `setup`,
`extract`, `run <step>` / `run all`, `status`, `report`.

`harness-tutorial` references the `ras` CLI for its demo commands. That CLI is
optional — the *ideas* (golden sets, gates, remedies, determinism checks) are
tool-agnostic and are the reason to read these files. To get the actual CLI:

```bash
python3 -m venv ~/harness_env
source ~/harness_env/bin/activate
pip install rag-ai-scientist
```

### Prerequisites on lxplus / CERN (HEP workflows)

The membrane and sandbox toolkits are stdlib-only and need no install, but the
full harness around them assumes a typical CERN environment:

| Requirement | Notes |
|---|---|
| **lxplus** or any machine with CVMFS + AFS | For the LCG stack and EOS data access |
| **Kerberos ticket** | `kinit` for EOS access |
| **Python 3.9+** | Membrane scripts are stdlib-only; LCG or conda is fine |
| **bubblewrap** | For `sandbox/bin/sandbox_run.sh` (available on lxplus) |
| **Cursor IDE with MCP support** | Only if you wire the harness into Cursor (see below) |
| **Git tokens** | Overleaf and/or GitLab — optional, per integration |

### Optional: wiring the harness into Cursor + MCP

If you run the harness inside Cursor alongside MCP servers (RAG knowledge
base, Overleaf, GitLab CERN), register the servers in `~/.cursor/mcp.json`
(or a workspace `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "my-analysis-rag": {
      "command": "/path/to/mcp_env/bin/python",
      "args": ["/path/to/your-analysis/.cursor/mcp_server.py"]
    },
    "overleaf": {
      "command": "node",
      "args": ["/path/to/your-analysis/.local_packages/overleafMCP-rw/overleaf-mcp-server.js"]
    },
    "gitlab-cern": {
      "url": "https://gitlab.cern.ch/api/v4/mcp",
      "headers": { "Authorization": "Bearer ${env:GITLAB_TOKEN}" }
    },
    "lbap-app": {
      "url": "https://lbap.app.cern.ch/mcp/"
    }
  }
}
```

Reload in Cursor: **Ctrl+Shift+P** → "MCP: Reload". Keep the harness rules
dominant: MCP tools feed the PLAN/VALIDATE phases, EXECUTE still runs
confined through `sandbox_run.sh`, and anything quoted back to the model
still passes the membrane filter.

### Credentials

| Secret | Location | Protection |
|---|---|---|
| Overleaf Git token | `.local_packages/overleafMCP-rw/projects.json` | Gitignored via `.local_packages/` |
| GitLab token | `$GITLAB_TOKEN` env var | Never committed |
| RAG vector DB | `.cursor/rag_db/` | Local only; gitignored |

Credentials live in **env vars** or **gitignored files** — never in version
control. The membrane's secret patterns (`membrane/config/secrets.patterns`)
are the last line of defense, not the first: rotate a token if you suspect it
reached model context.

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

## Writing and reviewing documents

Basic, deliberately thin doc skills you can grow: `writing-internal-note`,
`writing-analysis-note` (AN/ASN), `writing-tdr`. Each is a skeleton plus
harness rules (every number from a run dir, status lines honest, membrane
on unpublished values). Two review agents: `reviewer-commenter` for quick
inline feedback (questions, no verdict), `reviewer-referee` for formal
severity-ranked reviews with an approve/revise gate. Typical loop: draft
with a writing skill -> commenter pass -> fix -> referee pass -> verdict
gate -> revise or circulate.

## Setup prompt: self-adapt the harness to your project

### DALI setup prompt (ready to paste)

Paste this into `AGENTS.md` at your analysis workspace root (or into the
agent's system prompt). It builds on this repo: the execute → validate →
correct loop follows `harness-tutorial`, all data access goes through the
`membrane` skill, and the step definitions live in `skills/dali/SKILL.md`,
which you create from `skills/_template/` and keep as the single per-step
source of detail. To wire it into your IDE with one command, see
[Setup — pick your IDE](#setup--pick-your-ide) above.

```markdown
# Role
You are the DALI agent: an analysis-workspace orchestrator for an LHCb physics
analysis. You set up the workspace, build an inspectable pipeline of the
analysis steps, and run an execute → validate → correct loop on each step and
on the whole pipeline. You are IDE-agnostic: use only files, shell commands,
and Snakemake, so the same instructions work in OpenCode, Claude Code, Cursor,
VS Code, Codex, and Vibe. OpenCode is the primary target.

# Self-introduction (first activation in a session)
Before doing anything else, introduce yourself in 3-4 lines: who you are, that
you morph into the skilled agent each stage needs by loading skills (one
agent, many skills - never fork new agents), which domain profile you adopted
from `state/domain.yaml` (default `analysis` if absent), and the commands the
user can give (`setup`, `extract`, `run <step>`/`run all`, `status`,
`report`). Then wait for the command. Do not re-introduce on later turns of
the same session.

# Morphing (one agent, many skills)
At stage start read `state/domain.yaml` and adopt the matching profile from
`skills/dali/profiles/<domain>.md` (analysis | reconstruction | simulation),
then compose with capability skills as the stage requires: `membrane` before
any data read, `harness-tutorial` for loop mechanics, `reviewer-referee` /
`reviewer-commenter` for reviews, `writing-*` for documents. A new workflow =
copy `skills/_template/` into a new skill; never fork the loop itself.

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

`AGENTS.md` and `skills/dali/SKILL.md` are not shipped in this repo: the
prompt creates them in your workspace. The prompt is an LHCb/Snakemake
example — adapt the step names and references to your own pipeline.

### Lazy version — "let the AI figure it out"

If you don't want to answer interview questions, paste just this:

```text
You are the DALI agent: a workspace orchestrator that morphs into the skilled
agent each stage needs by loading skills (membrane, harness-tutorial,
reviewer-*, writing-*, domain profiles) - one agent, many skills. Introduce
yourself in 3-4 lines first (who you are, the morphing contract, your domain
profile, the commands), then proceed.

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
You are the DALI agent: a workspace orchestrator that morphs into the skilled
agent each stage needs by loading skills (membrane, harness-tutorial,
reviewer-*, writing-*, domain profiles) - one agent, many skills. Introduce
yourself in 3-4 lines first (who you are, the morphing contract, your domain
profile, the commands), then proceed.

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

## Thinking out loud: how DALI explains itself

Add this to the end of either setup prompt (or paste it once per session):

```text
Narrate your reasoning. Before each phase (SETUP, PLAN, EXECUTE, VALIDATE,
CORRECT) print a "Thinking:" block: what you are about to do, why, which
files/commands you will touch, and what could go wrong. After each phase
print a "Decided:" block: the outcome, the evidence (gate exit codes,
selftest counts, file diffs), and what it commits you to. On any gate
failure, state the gate, its remedy per the skill's failure table, and
which config you will change - never the validated output.
```

What that means phase by phase, and what you should see:

| phase | what the agent sets up and explains | you check |
|---|---|---|
| SETUP | which skills/configs it loaded, `$WS`/`$MEM`/`$SB` it resolved, allowlist vs workspace layout mismatches it found | the layout it describes is really yours |
| PLAN | the step list, which steps are gated, which golden/negative control decides pass | you agree what "validated" means before code runs |
| EXECUTE | each command *before* running it, wrapped in `sandbox_run.sh`, why it is confined that way | no command runs unconfined; deny paths match `!` denials |
| VALIDATE | each gate run through the membrane: gate exit codes, filtered output only, tokens not literals | no `[REDACTED]`-free raw content in the transcript |
| CORRECT | failed gate -> named remedy -> config change -> re-run, with the diff shown | outputs were never hand-edited |

Usage after setup, day to day:

1. Start the session, arm the membrane (and sandbox) per the skill rules.
2. Give the task; the agent plans with gates, you approve the plan.
3. Let it execute confined; it quotes you only filtered results.
4. Gates decide "done", not the agent's opinion; on failure you read the
   Decided block, approve the named remedy, and it retries.
5. The run directory + ADAPTATION.md are the audit trail: anyone can
   reproduce and see every decision that was made.

## How to adapt to your own pipeline

1. Copy `skills/_template/` to `skills/<your-workflow>/`.
2. Fill in concrete steps, validation checks, and failure recovery.
3. Follow the rules from `harness-tutorial`:
   - never edit an answer to satisfy a gate; change the input or the config;
   - always keep at least one negative control in your golden set;
   - every run must be reproducible from its run directory alone.

### What you swap out vs. what you keep

| Swap out (your physics) | Keep (the framework) |
|---|---|
| `skills/<your-workflow>/` steps and gates | `harness-tutorial` — gated-loop conventions |
| `membrane/config/approved-crossings.txt` | `membrane/bin/` scripts (stdlib, analysis-agnostic) |
| `membrane/config/pseudonymize.patterns`, `secrets.patterns` | `membrane/tests/selftest.py` regression checks |
| `sandbox/config/deny-paths.txt` | `sandbox/bin/sandbox_run.sh` confinement logic |
| Reference values in your validation gates | `reviewer-referee` / `reviewer-commenter` review loop |

## Security model in one paragraph

Three layers, each with a different failure mode: the **membrane** is a
discipline boundary deciding what *text* may enter model context (only
declared aggregate outputs cross; raw data, credentials and the
pseudonymization table never do); the **sandbox** is an OS-level boundary
deciding what *code* may touch (workspace read-write, deny paths invisible,
no network); **MCP servers** run locally against your own repos and tokens —
assume anything pasted into the chat may reach the model provider, so arm the
membrane before discussing unpublished numbers and never paste tokens.

## Provenance

Extracted from the packaged skills of `rag-ai-scientist`
(`rag_ai_scientist/skills/`). BsPhiGamma-specific, MCP-setup, and
Overleaf-sync skills were excluded; no local paths, keys, or personal config
are included.
