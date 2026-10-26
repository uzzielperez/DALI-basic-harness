#!/usr/bin/env bash
# sandbox_run.sh: OS-level execution boundary for harness EXECUTE-phase commands.
#
# The membrane (../membrane) filters what TEXT may enter model context.
# This script enforces what CODE may touch on the machine, via bubblewrap:
#
#   - workspace mounted read-write at /workspace (cwd)
#   - deny paths (config/deny-paths.txt, relative to workspace) masked with
#     an empty read-only tmpfs: the command cannot read or write them
#   - $HOME, /afs, /tmp of the host are NOT visible (fresh tmpfs /tmp)
#   - no network (user/pid/ipc/uts namespaces unshared)
#   - optional wall-clock timeout
#
# Exit codes: command's exit code, 70 = bwrap missing, 78 = bwrap failed to
# set up the sandbox (e.g. user namespaces disabled).
#
# Usage:
#   sandbox_run.sh [--workspace DIR] [--sandbox-config FILE] [--timeout SEC]
#                  [--net] -- COMMAND [ARGS...]
#
# Env: SANDBOX_WS defaults to $BUBBLE, then cwd. SANDBOX_CONFIG overrides
# the deny-path file location.

set -u

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS="${SANDBOX_WS:-${BUBBLE:-$PWD}}"
DENY="${SANDBOX_CONFIG:-$HERE/../config/deny-paths.txt}"
TIMEOUT=""
NET=""

while [ $# -gt 0 ]; do
  case "$1" in
    --workspace) WS="$2"; shift 2 ;;
    --sandbox-config) DENY="$2"; shift 2 ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --net) NET=1; shift ;;
    --) shift; break ;;
    *) echo "sandbox_run: unknown option: $1" >&2; exit 64 ;;
  esac
done

if [ $# -eq 0 ]; then
  echo "usage: sandbox_run.sh [--workspace DIR] [--timeout SEC] [--net] -- CMD..." >&2
  exit 64
fi

command -v bwrap >/dev/null 2>&1 || {
  echo "sandbox_run: bwrap not found (install bubblewrap, or fall back to podman)" >&2
  exit 70
}

WS="$(cd "$WS" 2>/dev/null && pwd)" || { echo "sandbox_run: workspace not found: $WS" >&2; exit 64; }

# The sandbox root is the real filesystem, read-only. The workspace mount
# point must exist inside the sandbox; we always mask /mnt with tmpfs, so
# /mnt/workspace is always available as our mount point.
WSMP=/mnt/workspace

# Deny paths: empty read-only tmpfs. Order matters: bind the workspace
# first, then mask the deny subpaths on top of it. Mount points are created
# inside the sandbox itself via /bin/sh -c, so no host directories are made.
MASKS=""
PRE=""
if [ -f "$DENY" ]; then
  while IFS= read -r line; do
    line="${line%%#*}"
    line="$(echo "$line" | tr -d '[:space:]')"
    [ -z "$line" ] && continue
    case "$line" in
      /*) echo "sandbox_run: deny path must be relative: $line" >&2; exit 64 ;;
    esac
    line="${line%/}"
    MASKS="$MASKS --tmpfs $WSMP/$line"
    PRE="$PRE mkdir -p $WSMP/$line;"
  done < "$DENY"
fi

CMD=("$@")
[ -n "$TIMEOUT" ] && CMD=(timeout --signal=KILL "$TIMEOUT" "${CMD[@]}")
UNSHARE=""
[ -n "$NET" ] || UNSHARE="--unshare-net"

# shellcheck disable=SC2086
if [ -n "$PRE" ]; then
  # create deny mount points inside the sandbox, then exec the real command
  WRAP=(/bin/sh -c "$PRE exec \"\$0\" \"\$@\"" "${CMD[@]}")
else
  WRAP=("${CMD[@]}")
fi

exec bwrap \
  --ro-bind / / \
  --dev /dev \
  --proc /proc \
  --tmpfs /tmp \
  --tmpfs /home \
  --tmpfs /mnt \
  --tmpfs /run \
  --tmpfs /var/tmp \
  --tmpfs /afs \
  --tmpfs /eos \
  --tmpfs /cvmfs \
  --unshare-user \
  --unshare-pid \
  --unshare-ipc \
  --unshare-uts \
  $UNSHARE \
  --die-with-parent \
  --bind "$WS" "$WSMP" \
  $MASKS \
  --chdir "$WSMP" \
  --setenv HOME /tmp \
  --setenv SANDBOX 1 \
  -- "${WRAP[@]}"
