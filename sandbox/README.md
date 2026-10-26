# Sandbox: OS-level execution boundary for harness EXECUTE-phase code

The membrane decides what **text** may enter model context. The sandbox decides
what **code the model runs** may touch on the machine. It wraps a command in
[bubblewrap](https://github.com/containers/bubblewrap) (user namespaces, no
root needed):

| property | effect |
|---|---|
| workspace bound read-write at the sandbox cwd | EXECUTE code can read inputs and write outputs |
| deny paths masked with empty tmpfs (`config/deny-paths.txt`) | raw-data dirs are invisible, not just denied |
| host root read-only, `/tmp` `/home` `/afs` `/eos` `/cvmfs` tmpfs'd | no writes outside the workspace, home tokens unreadable |
| network namespace unshared (default) | no exfiltration, no downloads |
| pid/ipc/uts namespaces unshared | cannot see or signal host processes |
| optional `--timeout` | runaway jobs are killed |

## Usage

```bash
export SB=/path/to/DALI-basic-harness/sandbox
WS=/path/to/your/analysis/workspace

$SB/bin/sandbox_run.sh --workspace $WS -- python3 fit.py --in out/agg.yaml
$SB/bin/sandbox_run.sh --workspace $WS --timeout 600 -- make -j4
$SB/bin/sandbox_run.sh --workspace $WS --net -- pip install --no-deps pkg  # explicit opt-in
```

Exit codes: the command's own code; `64` bad usage, `70` bwrap missing.
`$SANDBOX=1` is set inside the sandbox so scripts can detect it.

Keep `config/deny-paths.txt` in sync with the `!` denials in
`../membrane/config/approved-crossings.txt`: the membrane keeps those paths
out of model context; the sandbox keeps them out of reach of executed code.

## Scope and limits

- Protects against: buggy or prompt-injected analysis code reading raw
  tuples, writing outside the workspace, phoning home, or touching `$HOME`
  credentials.
- Does NOT protect against: a kernel exploit, side channels through data you
  deliberately mount read-only (the whole host FS is visible read-only
  except the tmpfs'd mounts — set `DENY` paths for anything sensitive inside
  the workspace), or data the command legitimately writes to allowed outputs
  (that is the membrane's job on the way out).
- If bubblewrap is unavailable (kernel without user namespaces), fall back to
  `podman run --rm -v $WS:/workspace -v $WS/raw:/raw:ro --network none ...`
  or run EXECUTE stages on a batch worker.

## Layout

```
sandbox/
├── README.md
├── bin/sandbox_run.sh          bwrap wrapper (this tool)
└── config/deny-paths.txt       workspace-relative paths to make invisible
```
