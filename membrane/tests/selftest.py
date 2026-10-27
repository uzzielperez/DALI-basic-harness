#!/usr/bin/env python3
"""Self-test for the membrane toolkit. Uses only synthetic fake strings."""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(HERE, "..", "bin")

FAKE_INPUT = """Run2 2018 Bs2PhiGamma BDT_WP_hi selected 1523 events
root://eoslhcb.cern.ch//eos/lhcb/user/c/jdoe01/tuple/data_run2_2018.dst
email me at jdoe01@lxplus.cern.ch or sk-abc123DEF456ghi789
AKIAABCDEFGHIJKLMNOP ghp_0123456789abcdef0123456789abcdef0123
/home/jdoe01/analysis/workflow/Snakefile
MC16a DDQQD|MC16a/14165004/Bs2PhiGamma.mixed
"""

failures = []


def check(name, cond, detail=""):
    print("%s %s %s" % ("PASS" if cond else "FAIL", name, detail))
    if not cond:
        failures.append(name)


def run(script, *args, **kw):
    return subprocess.run([sys.executable, os.path.join(BIN, script)] + list(args),
                          capture_output=True, text=True, **kw)


with tempfile.TemporaryDirectory() as ws:
    # 1. filter redacts secrets and pseudonymizes
    r = run("membrane_filter.py", "--workspace", ws, input=FAKE_INPUT)
    out = r.stdout
    check("exit3-on-secrets", r.returncode == 3, "rc=%d" % r.returncode)
    check("secret-sk-redacted", "sk-abc" not in out and "[REDACTED]" in out)
    check("secret-akia-redacted", "AKIAABC" not in out)
    check("secret-ghp-redacted", "ghp_0123" not in out)
    check("email-redacted", "jdoe01@lxplus" not in out)
    check("path-pseudonymized", "/home/jdoe01" not in out and "<PATH_" in out)
    check("run-pseudonymized", "Run2" not in out and "<DS_" in out)
    check("eos-host-pseudonymized", "eoslhcb.cern.ch" not in out)
    check("mc-simlabel-pseudonymized", "MC16a" not in out)
    check("mapping-written", os.path.exists(os.path.join(ws, ".deid", "mapping.tsv")))
    check("mapping-not-on-stdout", "\t" not in out)
    with open(os.path.join(ws, ".deid", "mapping.tsv")) as f:
        mp = f.read()
    check("mapping-has-originals", "/home/jdoe01" in mp and "Run2" in mp)

    # 2. token stability across invocations
    r2 = run("membrane_filter.py", "--workspace", ws, input="Run2 again\n")
    check("token-stable", "<DS_1>" in r2.stdout, r2.stdout.strip())

    # 3. allowlist gate
    good = os.path.join(ws, "branching_ratio", "output")
    os.makedirs(good, exist_ok=True)
    open(os.path.join(good, "branching_ratio_run2.yaml"), "w").write("x")
    bad = os.path.join(ws, "tuple", "mass_fit")
    os.makedirs(bad, exist_ok=True)
    open(os.path.join(bad, "x.yaml"), "w").write("x")
    open(os.path.join(ws, "secret.p12"), "w").write("x")

    g = run("membrane_check.py", "--workspace", ws, "--quiet",
            os.path.relpath(os.path.join(good, "branching_ratio_run2.yaml"), ws))
    check("gate-allows-approved", g.returncode == 0, g.stdout + g.stderr)
    g = run("membrane_check.py", "--workspace", ws, "--quiet",
            os.path.relpath(os.path.join(bad, "x.yaml"), ws))
    check("gate-denies-tuple", g.returncode == 1)
    g = run("membrane_check.py", "--workspace", ws, "--quiet", "secret.p12")
    check("gate-denies-p12", g.returncode == 1)
    g = run("membrane_check.py", "--workspace", ws, "--quiet", "random/thing.txt")
    check("gate-denies-unknown", g.returncode == 1)

    # 4. tail refuses denied files, filters approved ones
    logdir = os.path.join(ws, "logs")
    os.makedirs(logdir, exist_ok=True)
    with open(os.path.join(logdir, "run.log"), "w") as f:
        f.write("line1 sk-aaaaaaaaaaaaaaaaa\n" * 50)
    t = run("membrane_tail.py", "--workspace", ws, "-n", "3",
            os.path.join(logdir, "run.log"))
    check("tail-works", t.returncode == 0 and "sk-aaaa" not in t.stdout)
    check("tail-count", t.stdout.count("line1") == 3)
    t = run("membrane_tail.py", "--workspace", ws, os.path.join(bad, "x.yaml"))
    check("tail-refuses-denied", t.returncode == 1)

print("\n%d/%d passed" % (18 - len(failures), 18))
sys.exit(1 if failures else 0)
