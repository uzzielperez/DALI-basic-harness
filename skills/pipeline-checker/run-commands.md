# Run-commands template

This file is **per-analysis**, not part of the generic skill. Copy it into your
repo (e.g. `docs/RUN_COMMANDS.md` or `skills/<yours>/run-commands.md`) and fill
one row per pipeline step. The pipeline-checker skill reads this to turn each
❌ matrix cell into a concrete command — so keep it current.

All paths relative to `REPO` (see `state/anchors.yaml`). Prefer the orchestrator
wrapper for real runs so checkpoints/rollback/feedback happen:

```bash
./scripts/run_step_with_corrector.sh --step <step> --run-cmd "<cmd>" --paths "<outputs>"
```

## Step table

| Step | Command | Bins / configs | Notes |
|------|---------|----------------|-------|
| 0 setup | `<env setup: source ...>` | one shell per run | |
| 1 <step> | `<cmd>` | `<config glob per bin>` | |
| 2 <step> | `<cmd>` | | |
| … | | | |
| gates | `<harness sandbox run cmd>` | offline, deterministic | |
| publish | `<publish cmd>` (manual only) | verifies live site after sync | |

## Conventions

- Dry-run first: add `--dry-run` to batch runners; run a gold-reference bin first.
- List every bin explicitly (years / polarity / `q²` / categories) so the loop
  is copy-pasteable.

## Blockers

List any bin/step that cannot run yet and what it waits on (a fit topology, a
human decision, an external sample). The checker reports these instead of
working around them.

| Blocked item | Waiting on | Doc / issue |
|--------------|-----------|-------------|
| | | |
