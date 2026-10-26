#!/usr/bin/env python3
"""Membrane gate: check a file path against the approved-crossings allowlist.

Exit 0 = approved (may be read/quoted, still pass through membrane_filter.py).
Exit 1 = denied. Exit 2 = no allowlist configured.

Usage: membrane_check.py [--workspace WS] [--allowlist FILE] path [path...]
"""
import argparse
import fnmatch
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ALLOWLIST = os.path.join(HERE, "..", "config", "approved-crossings.txt")


def load_allowlist(path):
    inc, exc = [], []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("!"):
                exc.append(line[1:])
            else:
                inc.append(line)
    return inc, exc


def relpath(path, ws):
    path = os.path.abspath(path)
    ws = os.path.abspath(ws)
    if path.startswith(ws + os.sep):
        return os.path.relpath(path, ws)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default=os.environ.get("BUBBLE", "."))
    ap.add_argument("--allowlist", default=DEFAULT_ALLOWLIST)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()

    if not os.path.exists(args.allowlist):
        print("membrane: no allowlist at %s" % args.allowlist, file=sys.stderr)
        return 2
    inc, exc = load_allowlist(args.allowlist)

    rc = 0
    for p in args.paths:
        rp = relpath(p, args.workspace)
        approved = any(fnmatch.fnmatch(rp, pat) or fnmatch.fnmatch(rp, pat + "/*")
                       for pat in inc)
        # explicit tuple/ block regardless of allowlist mistakes
        blocked = any(fnmatch.fnmatch(rp, pat) for pat in exc)
        if blocked or not approved:
            rc = 1
            if not args.quiet:
                reason = "denylist" if blocked else "not in allowlist"
                print("DENY  %s (%s)" % (rp, reason))
        elif not args.quiet:
            print("OK    %s" % rp)
    return rc


if __name__ == "__main__":
    sys.exit(main())
