#!/usr/bin/env python3
"""Tail a log through the membrane: last N lines, secret-redacted and
pseudonymized. Refuses files the allowlist gate denies.

Usage: membrane_tail.py [--workspace WS] [-n 20] file.log [file.log ...]
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default=os.environ.get("BUBBLE", "."))
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()

    gate = subprocess.run(
        [sys.executable, os.path.join(HERE, "membrane_check.py"),
         "--workspace", args.workspace, "--quiet"] + args.files,
        capture_output=True, text=True)
    if gate.returncode != 0:
        denied = [f for f in args.files]
        print("membrane_tail: DENIED by allowlist: %s" % ", ".join(denied),
              file=sys.stderr)
        return 1

    for fn in args.files:
        try:
            with open(fn, errors="replace") as f:
                lines = f.readlines()[-args.n:]
        except OSError as e:
            print("membrane_tail: cannot read %s: %s" % (fn, e), file=sys.stderr)
            return 1
        print("===== %s (last %d lines, membrane-filtered) =====" %
              (os.path.basename(fn), len(lines)))
        proc = subprocess.run(
            [sys.executable, os.path.join(HERE, "membrane_filter.py"),
             "--workspace", args.workspace, "--quiet-secrets"],
            input="".join(lines), capture_output=True, text=True)
        sys.stdout.write(proc.stdout)
        if proc.stderr:
            sys.stderr.write(proc.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
