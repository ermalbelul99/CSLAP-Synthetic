r"""
Check the 29 EXP-02a instances against the manifest recorded with the results.

Run this on any machine before re-running the benchmark: a re-run is only
comparable with the published table if it uses byte-identical instance files.

Usage (from the CSLAP-Synthetic root):
    python Baselines/verify_instance_hashes.py
Exit status is 0 when every listed file matches, 1 otherwise.
"""

from __future__ import annotations

import hashlib
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
MANIFEST = os.path.join(_ROOT, "exp02a_results", "hash_manifest_v3.txt")
INSTANCE_DIR = os.path.join(_ROOT, "exp02a_instances")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_manifest(path: str) -> dict:
    """Map instance-relative file path -> expected digest.

    Manifest rows are `size_n instance_seed regenerated basename sha256`, so the
    directory name is rebuilt from the first two fields.
    """
    expected = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            size_n, seed, _regen, basename, digest = (
                parts[0], parts[1], parts[2], parts[-2], parts[-1])
            if len(digest) != 64:
                continue
            rel = f"exp02a_instances/syn_{size_n}sku_seed{seed}/{basename}"
            expected[rel] = digest.lower()
    return expected


def main() -> int:
    if not os.path.exists(MANIFEST):
        print(f"[error] manifest not found: {MANIFEST}", file=sys.stderr)
        return 1
    expected = parse_manifest(MANIFEST)
    if not expected:
        print(f"[error] no digests parsed from {MANIFEST}", file=sys.stderr)
        return 1

    ok = missing = bad = 0
    for rel, digest in sorted(expected.items()):
        path = os.path.join(_ROOT, rel)
        if not os.path.exists(path):
            alt = os.path.join(INSTANCE_DIR, os.path.basename(rel))
            path = alt if os.path.exists(alt) else path
        if not os.path.exists(path):
            print(f"MISSING  {rel}")
            missing += 1
            continue
        actual = sha256(path)
        if actual == digest:
            ok += 1
        else:
            print(f"MISMATCH {rel}\n  expected {digest}\n  actual   {actual}")
            bad += 1

    instances = sorted(d for d in os.listdir(INSTANCE_DIR)
                       if os.path.isdir(os.path.join(INSTANCE_DIR, d)))
    print(f"\n{len(instances)} instance directories present")
    print(f"{ok} files match, {bad} differ, {missing} missing "
          f"(of {len(expected)} listed)")
    if bad or missing:
        print("\nDo NOT re-run the benchmark: the instances are not the ones the "
              "published table was produced from.")
        return 1
    print("\nInstances verified: safe to re-run the benchmark.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
