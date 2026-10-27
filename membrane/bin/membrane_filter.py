#!/usr/bin/env python3
"""Membrane: pseudonymize + secret-redact text crossing from a bubble workspace.

Reads stdin (or files), writes deidentified text to stdout.
Mapping table (token -> original) is appended to a LOCAL-only TSV and never
printed. Exit 3 if any secret pattern matched (so callers can hard-fail).

Usage:
  membrane_filter.py [--workspace WS] [--quiet-secrets] < file.log
  some_command | membrane_filter.py
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "..", "config")


def load_patterns(path):
    pats = []
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.lstrip().startswith("#"):
                continue
            pats.append(line)
    return pats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default=os.environ.get("BUBBLE", "."))
    ap.add_argument("--quiet-secrets", action="store_true",
                    help="do not exit 3 when secrets are found")
    ap.add_argument("--files", nargs="*", default=None)
    args = ap.parse_args()

    secret_pats = [re.compile(p) for p in
                   load_patterns(os.path.join(CONFIG, "secrets.patterns"))]
    deid_rules = []
    with open(os.path.join(CONFIG, "pseudonymize.patterns")) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.lstrip().startswith("#"):
                continue
            tok, pat = line.split("\t", 1)
            deid_rules.append((tok, re.compile(pat)))

    deid_dir = os.path.join(args.workspace, ".deid")
    os.makedirs(deid_dir, exist_ok=True)
    map_path = os.path.join(deid_dir, "mapping.tsv")
    # stable within session (and across): load existing mapping
    fwd, rev = {}, {}
    if os.path.exists(map_path):
        with open(map_path) as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) == 2:
                    tok, orig = parts
                    fwd[orig] = tok
                    rev[tok] = orig

    counters = {}
    new_rows = []
    secret_hits = 0

    def token_for(orig, tok_type):
        if orig in fwd:
            return fwd[orig]
        n = counters.get(tok_type, 0) + 1
        # continue numbering from existing mapping
        while "<%s_%d>" % (tok_type, n) in rev:
            n += 1
        counters[tok_type] = n
        tok = "<%s_%d>" % (tok_type, n)
        fwd[orig] = tok
        rev[tok] = orig
        new_rows.append("%s\t%s" % (tok, orig))
        return tok

    def process(text):
        nonlocal secret_hits
        for p in secret_pats:
            text, n = p.subn("[REDACTED]", text)
            secret_hits += n
        for tok_type, pat in deid_rules:
            def sub(m):
                return token_for(m.group(0), tok_type)
            text = pat.sub(sub, text)
        return text

    if args.files:
        chunks = []
        for fn in args.files:
            with open(fn, errors="replace") as f:
                chunks.append(process(f.read()))
        sys.stdout.write("\n".join(chunks))
    else:
        data = sys.stdin.read()
        sys.stdout.write(process(data))

    if new_rows:
        with open(map_path, "a") as f:
            for row in new_rows:
                f.write(row + "\n")

    if secret_hits and not args.quiet_secrets:
        sys.stderr.write("membrane: %d secret pattern hit(s) - output redacted, "
                         "treat source as untrusted for quoting\n" % secret_hits)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
