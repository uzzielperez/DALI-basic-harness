---
name: membrane
description: Semipermeable security boundary for analysis workspaces. Gate every file read, pseudonymize and redact anything quoted to the model, and tail logs only through the filter. Use whenever an agent works in a workspace containing raw event/data files, credentials, or unpublished results.
---

# Membrane

## Purpose

Keep raw data and secrets out of model context while still letting the agent
do real work: read aggregate outputs, validate results, repair failures.

`$MEM` = the `membrane/` directory shipped alongside this skill (adjust the
path if you move it). `$WS` = the analysis workspace you are working in.

## Preconditions

- `$MEM/bin/membrane_check.py`, `membrane_filter.py`, `membrane_tail.py` exist.
- `$MEM/config/approved-crossings.txt` describes *this* workspace's output
  layout. If it does not, edit it before starting - a stale allowlist either
  blocks all work or lets everything through.
- `python3` available (stdlib only).

## Rules (enforce for the whole session)

1. **Gate before reading.** Run
   `python3 $MEM/bin/membrane_check.py --workspace $WS <path>` before opening
   or quoting any file. Exit 0 = may cross; exit 1 = denied, do not open it;
   exit 2 = no allowlist, stop and configure it.
2. **Quote only filtered output.** Any file content that enters the
   conversation goes through
   `python3 $MEM/bin/membrane_filter.py --workspace $WS`. Never hand-quote raw
   file content, even when the gate approved the file.
3. **Logs are tails, never whole files.**
   `python3 $MEM/bin/membrane_tail.py --workspace $WS -n 20 logs/<x>.log`.
4. **Exit 3 from the filter means a secret was found.** Do not quote that
   source; report the line count and the surrounding non-secret lines instead.
5. **Numbers must come from an approved file.** If a needed value lives only
   in a denied file, write a small script that reads it inside the workspace
   and prints only the aggregate; quote the script's filtered output, never
   the file.
6. **Suppress low-statistics bins** (N < 10) before quoting tables.
7. **Never print** absolute paths, account names, hostnames, proxy DNs, or the
   mapping table. Use the `<PATH_n>` / `<DS_n>` / `<HOST_n>` tokens the filter
   produced. `$WS/.deid/mapping.tsv` is local-only.
8. **Write inside `$WS` only.** Never edit a reference/readonly copy of the
   workspace to make a check pass.

## Hard denials (checked first, no exceptions)

Raw event data (`tuple/**`, `*.root`, `*.dst`, `*.ndst`, `*.h5`, `*.parquet`,
`*.bk`), credentials (`*.p12`, `*.pem`, `*.key`, `.env*`, `*.x509*`,
`*.proxycache*`), and membrane state (`.deid/**`).

## Steps

1. Confirm the allowlist matches the workspace layout; adjust if needed.
2. Gate, then read; filter, then quote.
3. On a denied path you genuinely need: aggregate script (rule 5), not an
   override.
4. Verify at any time with `python3 $MEM/tests/selftest.py` (synthetic data
   only; touches nothing outside a temp dir).

## Validation

- Every quoted path/label/hostname appears as a token, not a literal.
- No `[REDACTED]`-free raw content in the transcript.
- No file under a denied glob was opened this session.

## Failure recovery

| symptom | remedy |
|---|---|
| gate denies a legitimate output file | add its directory to `approved-crossings.txt` above the `!` lines; re-gate |
| filter leaks a literal path/label | add a rule to `pseudonymize.patterns` (experiment-specific above generic), re-run selftest |
| filter exits 3 on a clean log | a pattern is too greedy (usually the long base64/hex rule); narrow it, re-run selftest |
| tokens unreadable across sessions | mapping is per-workspace; reuse the same `$WS` so `.deid/mapping.tsv` persists |
| everything denied | allowlist is for another layout; rewrite it for this workspace |

## Notes

- The membrane is a **discipline boundary for the LLM**, not a sandbox: it does
  not stop a compromised analysis script (which legitimately reads raw data)
  or a malicious binary. Do not present its output as a security guarantee.
- The mapping table is local but unencrypted.
- Optional session pre-flight (opencode only): `plugins/membrane-preflight.js`.
