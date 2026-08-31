"""Minimal stand-in for unlazy's gate-check.mjs (Node is not installed here).

Enforces the same core contract: a runnable gate is met only when its process
exits 0 AND its EXPECT: matches combined stdout+stderr. Writes EVIDENCE back
into the ledger and exits non-zero when any gate is unmet, so it can fail.
"""
import hashlib
import re
import subprocess
import sys
import time

import os
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(REPO, "GATES_z_contract.md")
CWD = REPO
TIMEOUT = 900

only = set(a.lower() for a in sys.argv[1:] if not a.startswith("-"))

lines = open(LEDGER, encoding="utf-8").read().splitlines()
gates, cur = [], None
for i, ln in enumerate(lines):
    m = re.match(r"^- \[([ x])\] (\w+):\s*(.*)$", ln)
    if m:
        cur = {"i": i, "id": m.group(2), "title": m.group(3),
               "check": None, "expect": None, "ev": None}
        gates.append(cur)
    elif cur is not None:
        s = ln.strip()
        if s.startswith("CHECK:"):
            cur["check"] = s[6:].strip()
        elif s.startswith("EXPECT:"):
            cur["expect"] = s[7:].strip()
        elif s.startswith("EVIDENCE:"):
            cur["ev"] = i

met = unmet = manual = skipped = 0
for g in gates:
    if only and g["id"].lower() not in only:
        skipped += 1
        continue
    if not g["check"]:
        print(f"{g['id']}: MANUAL (no command oracle)")
        manual += 1
        continue
    t0 = time.time()
    try:
        r = subprocess.run(g["check"], shell=True, cwd=CWD, timeout=TIMEOUT,
                           capture_output=True, text=True)
        out = (r.stdout or "") + (r.stderr or "")
        code = r.returncode
    except subprocess.TimeoutExpired:
        out, code = "", 124
    dt = time.time() - t0
    hit = g["expect"] in out
    ok = (code == 0) and hit
    fp = hashlib.sha256(out.encode("utf-8", "replace")).hexdigest()[:12]
    if ok:
        met += 1
        lines[g["i"]] = lines[g["i"]].replace("- [ ]", "- [x]", 1)
        if g["ev"] is not None:
            lines[g["ev"]] = (f"  EVIDENCE: exit=0 expect-matched "
                              f"sha256:{fp} {dt:.1f}s")
        print(f"{g['id']}: MET ({dt:.1f}s)")
    else:
        unmet += 1
        lines[g["i"]] = lines[g["i"]].replace("- [x]", "- [ ]", 1)
        why = f"exit={code} expect_matched={hit}"
        if g["ev"] is not None:
            lines[g["ev"]] = f"  EVIDENCE: UNMET {why} sha256:{fp}"
        print(f"{g['id']}: UNMET {why}")
        tail = [x for x in out.splitlines()
                if x.strip() and not x.startswith("Preprocess")][-4:]
        for t in tail:
            print(f"    | {t}")

open(LEDGER, "w", encoding="utf-8").write("\n".join(lines) + "\n")
print(f"\nmet={met} unmet={unmet} manual={manual} skipped={skipped}")
sys.exit(0 if unmet == 0 else 1)
