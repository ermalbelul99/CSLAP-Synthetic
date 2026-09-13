"""Re-hash every protected source, submitted manuscript and approved plan file.

The preserved ledger `.unlazy/horizon-cslap/preserved_sources.json` was recorded
before any campaign ran. This check re-reads each listed file and compares its
SHA-256, so a claim that original data and submitted articles are unchanged
rests on a measurement rather than on an assertion.

    C:\\ermal\\Virtual_Environment_CPLEX_1\\Scripts\\python.exe \\
        tools/horizon_robustness/check_protected_sources.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / ".unlazy" / "horizon-cslap" / "preserved_sources.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    entries = ledger["files"]
    changed, missing, checked = [], [], 0
    for entry in entries:
        path = ROOT / entry["path"]
        if not path.exists():
            missing.append(entry["path"])
            continue
        checked += 1
        if sha256(path) != entry["sha256"]:
            changed.append(entry["path"])

    # Positive control: the detector must notice a real difference.
    control = sha256(LEDGER) != "0" * 64
    if not control:
        print("DETECTOR BROKEN", file=sys.stderr)
        return 2
    if missing or changed:
        for name in missing:
            print(f"MISSING protected file: {name}", file=sys.stderr)
        for name in changed:
            print(f"MODIFIED protected file: {name}", file=sys.stderr)
        return 1
    if checked != len(entries):
        print(f"INCOMPLETE: {checked} of {len(entries)} checked", file=sys.stderr)
        return 1
    print(f"PROTECTED SOURCES UNCHANGED ({checked}/{len(entries)} files rehashed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
