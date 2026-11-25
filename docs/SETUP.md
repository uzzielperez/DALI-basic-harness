# DALI agent — setup for your IDE

> **This whole harness is in beta.** Every instruction in these docs, in
> `AGENTS.md`, and in the DALI skills is still being tested and may change
> between releases. Breakages are expected — please report them.

> Website-ready page for dali-agent.web.cern.ch (agent-setup style).
> Mirrors README.md "Setup — pick your IDE" 1:1; keep both in sync.

One command wires the DALI agent — skills, membrane, sandbox, and
instructions — into your editor. The agent itself is IDE-agnostic: files,
shell, and Snakemake only.

| IDE | Skills land in | Callable agent | Instructions file |
|---|---|---|---|
| [opencode](#opencode) | `.opencode/skill/` or `~/.config/opencode/skill/` | `agent/dali.md` — `/agent dali` | `AGENTS.md` |
| [Claude Code](#claude-code) | `.claude/skills/` or `~/.claude/skills/` | `agents/dali.md` — `@dali` | `CLAUDE.md` |
| [Cursor](#cursor) | `.cursor/skills/` or `~/.cursor/skills/` | `.cursor/agents/dali.md` (custom mode) | `AGENTS.md` |
| [Codex](#codex) | `.codex/skills/` or `~/.codex/skills/` | `.codex/agents/dali.md` | `AGENTS.md` |
| [GitHub Copilot](#github-copilot) | `.github/skills/` | `/dali` prompt (`.github/prompts/`) | `AGENTS.md` + `.github/copilot-instructions.md` |
| [VS Code](#vs-code) | `.github/skills/` (native MCP client) | `/dali` prompt (`.github/prompts/`) | `AGENTS.md` |
| [Vibe (Mistral)](#vibe-mistral) | `.agents/skills/` | `.agents/dali.md` | `AGENTS.md` |

Every target gets the same four things: the skills, the enforcement toolkits
copied to `<workspace>/.dali/{membrane,sandbox}`, a marker-delimited
instructions block, and a **callable DALI agent** (single source:
`install/dali-agent.md`, adapted per IDE dialect). Re-running the installer
updates in place; `--uninstall` removes exactly what was installed; `--check`
(alias `--diff`) shows what an update would change without writing anything.

## Prerequisites (lxplus / CERN)

| Requirement | Notes |
|---|---|
| lxplus or any machine with CVMFS + AFS | LCG stack and EOS data access |
| Kerberos ticket | `kinit` for EOS access |
| Python 3.9+ | Membrane scripts are stdlib-only |
| bubblewrap | For `sandbox_run.sh` (available on lxplus) |

## Get the harness

You do **not** need git, or a CERN account, to get the harness. Pick any route:

**1. Clone from the public GitHub mirror (the light option — recommended)** —
a `git clone` is lighter than the ZIP, and it is the route that makes later
updates trivial (just `git pull`, see "Updating an existing install"):

```bash
git clone https://github.com/uzzielperez/DALI-basic-harness.git /tmp/dali-harness
cd /tmp/dali-harness
```

**2. Download a ZIP (no git, no account)** — grab the
[latest ZIP](https://github.com/uzzielperez/DALI-basic-harness/archive/refs/heads/main.zip),
unzip it, and `cd` into the `DALI-basic-harness-main/` folder:

```bash
curl -fsSL -o dali-harness.zip https://github.com/uzzielperez/DALI-basic-harness/archive/refs/heads/main.zip
unzip dali-harness.zip && cd DALI-basic-harness-main
```

**3. CERN members with access** — the source of truth lives on GitLab
(`gitlab.cern.ch/lasalle/DALI-nucleus`, CERN SSO required):

```bash
git clone https://gitlab.cern.ch/lasalle/DALI-nucleus /tmp/dali-harness
```

(Or use your local checkout; substitute its path below. In every route the
installer is `install/install.sh`.)

Or pull it from PyPI, which ships the same skills, the DALI agent definition,
the membrane and the sandbox as package data of
[`rag-ai-scientist`](https://pypi.org/project/rag-ai-scientist/):

```bash
pip install rag-ai-scientist
PKG=$(python -c "import rag_ai_scientist, pathlib; print(pathlib.Path(rag_ai_scientist.__file__).parent)")
"$PKG/install/install.sh" --ide opencode --workspace "$PWD"   # from the installed tree
```

### One-command onboarding for a new project (`dali-onboard`)

Since `rag-ai-scientist >= 0.1.10` the PyPI package also ships the DALI
onboarding state machine (LangGraph, Python >= 3.10). Give it a paper and a
codebase (paths or URLs) and it embeds them into a project RAG brain
(`.dali/brain`), lets you test the brain (human gate), plans the reproduction
steps with an LLM, then runs an execute → validate → correct loop with a
human gate per step, ending in a smoke-test gate:

```bash
pip install rag-ai-scientist
dali-onboard --workspace ~/my-analysis
# equivalent: rag-ai-scientist onboard --workspace ~/my-analysis
```

Deterministic nodes do all the work; the LLM (Groq / OpenAI-compatible) only
proposes the plan and fixes, and every proposal is executed and validated by
the harness before being accepted. Sessions checkpoint under
`.dali/onboard/` and resume across invocations.

## Updating an existing install

The harness is in beta and moves fast — new skills, membrane fixes, and agent
definition changes land regularly. Updating is a two-step **refresh, then
apply**: first refresh the harness sources, then re-run the same `install.sh`
command you used at install time. Re-running the installer updates everything
in place (skills, instructions block, `.dali/` toolkits) — nothing to
uninstall first.

**Step 1 — refresh the harness sources**, using the same route you installed
from:

- **Git clone route** (the light option — this is why the clone is
  recommended):
  ```bash
  cd /tmp/dali-harness && git pull
  ```
- **ZIP route:** re-download the
  [latest ZIP](https://github.com/uzzielperez/DALI-basic-harness/archive/refs/heads/main.zip)
  and unpack it over the existing checkout (or unpack fresh and use the new
  path below):
  ```bash
  curl -fsSL -o dali-harness.zip https://github.com/uzzielperez/DALI-basic-harness/archive/refs/heads/main.zip
  unzip -o dali-harness.zip
  ```
- **pip route:**
  ```bash
  pip install -U rag-ai-scientist
  ```

**Step 2 — see what the update would change** (optional but recommended):
from your analysis workspace root, run `--check` (alias `--diff`). It compares
your installed skills, instructions block, and `.dali/` toolkits against the
refreshed sources and prints the drift — new skills, changed or missing files
— without writing anything. Exit code 1 means an update is available:

```bash
/path/to/harness/install/install.sh --check --ide opencode --workspace "$PWD"
```

**Step 3 — apply the update** by re-running the exact same `install.sh`
command you used at install time (drop `--check`):

```bash
/path/to/harness/install/install.sh --ide opencode --workspace "$PWD"
```

This pulls in the updated skills set and rewrites the instructions block and
toolkits in place. Marker-delimited blocks are replaced, not duplicated, so
re-running is safe. (pip route: re-derive `$PKG` as above and run
`"$PKG/install/install.sh"` from the updated tree.)

## opencode

1. **Install opencode** — see [opencode.ai/docs](https://opencode.ai/docs)

   ```bash
   curl -fsSL https://opencode.ai/install | bash
   ```

2. **Install the DALI harness** — from your analysis workspace root:

   ```bash
   /tmp/dali-harness/install/install.sh --ide opencode --workspace "$PWD"
   ```

   Add `--scope user` to install skills and the membrane-preflight plugin
   globally (`~/.config/opencode/`) instead of per workspace.

3. **Launch the DALI agent (`/agent dali` in opencode, `@dali` in Claude
   Code, `/dali` in Copilot — or just say `setup`) and it takes over**

   ```bash
   opencode
   ```

4. **Try a prompt**

   ```txt
   setup
   ```

## Claude Code

1. **Install Claude Code** — see the [setup guide](https://docs.anthropic.com/en/docs/claude-code/setup)

   ```bash
   curl -fsSL https://claude.ai/install.sh | bash
   ```

2. **Install the DALI harness** — from your analysis workspace root:

   ```bash
   /tmp/dali-harness/install/install.sh --ide claude-code --workspace "$PWD"
   ```

3. **Launch the DALI agent (`/agent dali` in opencode, `@dali` in Claude
   Code, `/dali` in Copilot — or just say `setup`) and it takes over**

   ```bash
   claude
   ```

4. **Try a prompt**

   ```txt
   extract the pipeline from the notes in docs/ and show me state/pipeline.yaml
   ```

## Cursor

1. **Install Cursor** — from [cursor.com](https://cursor.com); MCP support is
   built in.

2. **Install the DALI harness** — from your analysis workspace root:

   ```bash
   /tmp/dali-harness/install/install.sh --ide cursor --workspace "$PWD"
   ```

   Skills go to `.cursor/skills/` (repo) — use `--scope user` for
   `~/.cursor/skills/` shared across all your analyses.

3. **Open the workspace, launch the DALI agent (see table above), say `setup`**
   Optional MCP servers (RAG, Overleaf, GitLab CERN): merge
   `.dali/mcp/cursor.json` into `~/.cursor/mcp.json`, then
   **Ctrl+Shift+P** → "MCP: Reload".

4. **Try a prompt**

   ```txt
   run all and give me status
   ```

## Codex

1. **Install Codex** — see the [Codex guide](https://developers.openai.com/codex/)

   ```bash
   npm i -g @openai/codex
   ```

2. **Install the DALI harness** — from your analysis workspace root:

   ```bash
   /tmp/dali-harness/install/install.sh --ide codex --workspace "$PWD"
   ```

3. **Launch the DALI agent (`/agent dali` in opencode, `@dali` in Claude
   Code, `/dali` in Copilot — or just say `setup`) and it takes over**

   ```bash
   codex
   ```

4. **Try a prompt**

   ```txt
   status
   ```

## GitHub Copilot

1. **Install the Copilot extension** and enable agent mode in your editor.

2. **Install the DALI harness** — from your analysis workspace root:

   ```bash
   /tmp/dali-harness/install/install.sh --ide copilot --workspace "$PWD"
   ```

   Skills go to `.github/skills/`, and `.github/copilot-instructions.md` gets
   a pointer to `AGENTS.md` + `skills/dali/SKILL.md`.

3. **Open Copilot Chat in agent mode, run `/dali`, say `setup`**

4. **Try a prompt**

   ```txt
   run selection and validate against the paper reference
   ```

## VS Code

VS Code is covered by the Copilot flow above (same skills dir), plus native
MCP: merge `.dali/mcp/vscode.json` via the MCP extension / settings.

```bash
/tmp/dali-harness/install/install.sh --ide vscode --workspace "$PWD"
```

## Vibe (Mistral)

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

4. **Launch the DALI agent (see table above), say `setup`**

   ```bash
   vibe
   ```

## Verify the install (any IDE)

```bash
python3 .dali/membrane/tests/selftest.py        # 18 checks, synthetic data
sandbox/bin/sandbox_run.sh --workspace "$PWD" --timeout 60 -- echo confined
```

## Commands the agent understands

`setup` · `extract` · `run <step>` / `run all` · `status` · `report`

## Tips

- Start the agent from the analysis workspace root — that is where `.dali/`,
  `AGENTS.md`, and the Snakemake pipeline live.
- Arm the membrane before discussing unpublished numbers; the membrane
  preflight plugin asks about it at session start in opencode.
- Credentials live in env vars or gitignored files, never in version control.
- `--dry-run` shows exactly what would change; `--uninstall` reverses it.
- `--check` (alias `--diff`) compares your installed skills, instructions block,
  and `.dali/` toolkits against the repo and prints the drift — new skills,
  changed or missing files — without writing anything. Exit code 1 means an
  update is available; re-run the same install command to apply it. See
  [Updating an existing install](#updating-an-existing-install) for the full
  refresh-then-apply procedure per install route.

## Troubleshooting

**Skills not found by the agent** — confirm the installer wrote to the path in
the table above, and that your agent version loads skills from there (opencode:
`.opencode/skill/`, singular; Vibe: `.agents/skills/`).

**Membrane selftest fails** — you need Python 3.9+; the scripts are
stdlib-only, no venv required.

**sandbox_run.sh: "bwrap not found"** — install bubblewrap (present on
lxplus); without it, EXECUTE-phase code runs unconfined and the harness
contract is broken.

**Instructions block duplicated after re-running** — it should not be (the
block is marker-delimited and replaced in place); delete everything between
`<!-- BEGIN DALI HARNESS ... -->` and `<!-- END DALI HARNESS -->` once, then
re-run.
