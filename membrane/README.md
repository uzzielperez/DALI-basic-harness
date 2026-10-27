# Membrane: semipermeable security boundary for LLM analysis harnesses

Pure-stdlib Python 3.9+ toolkit. No install, no dependencies, no config
required to try it. Three tools stand between a raw analysis workspace and
the model's context:

| tool | question it answers |
|---|---|
| `bin/membrane_check.py` | *May this file cross to the model at all?* |
| `bin/membrane_filter.py` | *Rewrite this text so it is safe to quote.* |
| `bin/membrane_tail.py` | *Show me the last N log lines, safely.* |

## The model

```
OUTSIDE (model-visible)          MEMBRANE                INSIDE (workspace)
reports, tables, manifests  <-   aggregate YAMLs,    <-   raw tuples / events /
pseudonymized summaries          pseudonymized,           detector data
                                 coarsened                (never read, never
                                                          listed by name)
```

Only aggregate, pseudonymized output crosses. Raw data, credentials, and the
token mapping table never enter model context.

What the membrane does:

1. **Allowlist gate** - only declared output paths may cross; raw data,
   credentials, and the mapping table are hard-denied.
2. **Pseudonymization** - file paths, run/dataset/stream labels, hostnames and
   usernames become stable `<PATH_n>` / `<DS_n>` / `<HOST_n>` tokens. The
   token-to-original map is written to `<workspace>/.deid/mapping.tsv`, which
   stays local and is never printed.
3. **Secret redaction** - API keys, private keys, certificates, emails, and
   long hex/base64 runs become `[REDACTED]`; the filter exits 3 so a caller can
   hard-fail instead of quoting.
4. **Low-statistics suppression** - coarsen or drop bins with N < 10 before
   quoting; very low counts leak identifying information.

## Scope and limits

This is a **discipline boundary for the LLM**, not a security sandbox for the
machine.

Protects against: raw event data or identifying metadata (paths, run/stream
names, hostnames) reaching model context through agent reads or quoted output;
secrets entering prompts or logs; accidental writes outside the workspace.

Does NOT protect against: a compromised analysis script (it legitimately reads
raw data), a malicious tool binary, side channels through aggregate values in
very low-count bins (hence the N < 10 rule), or a shell that bypasses the
harness's own read-permission config. The mapping table is local but not
encrypted.

## Usage

```bash
export MEM=/path/to/DALI-basic-harness/membrane
WS=/path/to/your/analysis/workspace

# 1. gate a file before reading or quoting it
python3 $MEM/bin/membrane_check.py --workspace $WS validation/tables.md
#   exit 0 = approved, exit 1 = denied, exit 2 = no allowlist configured

# 2. filter anything before it enters model context
python3 $MEM/bin/membrane_filter.py --workspace $WS < results.yaml

# 3. logs: never whole files, only gated tails
python3 $MEM/bin/membrane_tail.py --workspace $WS -n 20 logs/run.log

# self-test (synthetic fake strings only, touches nothing outside a temp dir)
python3 $MEM/tests/selftest.py
```

`--workspace` defaults to `$BUBBLE`, then the current directory. The `.deid/`
directory and mapping table are created on first use; delete `.deid/` to reset
token numbering.

## Layout

```
membrane/
├── README.md
├── bin/
│   ├── membrane_check.py              allowlist gate (exit 0/1/2)
│   ├── membrane_filter.py             pseudonymize + redact (exit 3 on secrets)
│   └── membrane_tail.py               gated last-N-lines log tail
├── config/
│   ├── approved-crossings.txt         allowlist; '!' lines = hard denials
│   ├── pseudonymize.patterns          <TOKEN_TYPE>\t<regex>, first match wins
│   └── secrets.patterns               one regex per line -> [REDACTED]
└── tests/
    └── selftest.py                    18 checks, no network, no real data
```

## Adapting to your own experiment

The shipped patterns default to HEP-flavoured examples. Edit and extend:

- `config/approved-crossings.txt` - list your aggregate output locations; keep
  the `!` denials for raw data and credentials, and put them before anything
  that could match a raw-data glob.
- `config/pseudonymize.patterns` - your run periods, production/stream labels,
  storage paths, and hostnames. One rule per line: token type, TAB, regex.
- `config/secrets.patterns` - add any token format your infrastructure issues.

Rules of thumb: put experiment-specific patterns above generic ones (first
match wins per token type); test with `selftest.py` after editing; never add a
pattern that matches a raw-data directory into the allowlist.

## Integrating into a harness

Instruct the agent to: run `membrane_check.py` before any read; quote only
output that passed through `membrane_filter.py` or `membrane_tail.py`; treat
exit 3 as "do not quote this source"; and, when a needed number lives only in
a denied file, write a small script that reads it inside the workspace and
prints only the aggregate value.

See `../skills/membrane/SKILL.md` for the skill-form version of these rules,
suitable for dropping into `~/.config/opencode/skill/` or `.cursor/skills/`.

## Optional: session pre-flight prompt

To have the harness ask at session start whether to activate the membrane,
copy `plugins/membrane-preflight.js` into `~/.config/opencode/plugins/`. It
appends a prompt to the TUI on a session's first idle, and injects the
enforcement rules into your message when you reply "membrane on". The plugin
is opencode-specific and optional; the three scripts work with any agent.
