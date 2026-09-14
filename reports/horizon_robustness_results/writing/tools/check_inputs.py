"""Prove that every pinned source is unchanged (plan INV-2, P0:G1).

Recomputes SHA-256 for every entry of ``W/governance/source_manifest.json`` and independently
re-enumerates the pinned groups with the same rules as
``W/governance/tools/make_manifest.py`` (re-implemented here, not imported, so this checker does
not depend on the tool it checks). Reports ``MODIFIED``, ``MISSING``, ``ADDED`` files and
``GROUP COUNT MISMATCH`` when a group's manifest entry count no longer matches the ``counts``
recorded at manifest build time (this catches a file deleted together with its own manifest
entry, which the per-file scan cannot see: F-012).

Usage: ``check_inputs.py [--root DIR]``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

# The manifest groups, re-implemented independently of make_manifest.py (INV-13: the checker must
# not import the tool it checks).
GROUP_NAMES = (
    "results_except_writing",
    "root_tex_bib",
    "manuscript_checks",
    "tools_horizon_robustness",
    "baselines_horizon_robustness",
    "baselines_horizon_robustness_analysis",
    "tests_horizon_robustness",
    "claude_agents_commands_skills",
    "prior_study_ledger",
)


def excluded(path: Path) -> bool:
    return "__pycache__" in path.parts or path.suffix == ".pyc"


def files_under(base: Path, skip: list[Path] = ()) -> list[Path]:
    if not base.is_dir():
        return []
    result = []
    for p in base.rglob("*"):
        if not p.is_file() or excluded(p):
            continue
        if any(s == p or s in p.parents for s in skip):
            continue
        result.append(p)
    return result


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def enumerate_groups(root: Path) -> dict[str, list[Path]]:
    r_dir = root / "reports" / "horizon_robustness_results"
    w_dir = r_dir / "writing"
    return {
        "results_except_writing": files_under(r_dir, skip=[w_dir]),
        "root_tex_bib": sorted(p for p in root.iterdir() if p.is_file() and p.suffix in (".tex", ".bib")),
        "manuscript_checks": files_under(root / "manuscript_checks", skip=[root / "manuscript_checks" / "out"]),
        "tools_horizon_robustness": files_under(root / "tools" / "horizon_robustness"),
        "baselines_horizon_robustness": files_under(root / "Baselines" / "horizon_robustness"),
        "baselines_horizon_robustness_analysis": files_under(root / "Baselines" / "horizon_robustness_analysis"),
        "tests_horizon_robustness": files_under(root / "tests" / "horizon_robustness"),
        "claude_agents_commands_skills": (
            files_under(root / ".claude" / "agents")
            + files_under(root / ".claude" / "commands")
            + files_under(root / ".claude" / "skills")
        ),
        "prior_study_ledger": [
            p for p in [root / ".unlazy" / "horizon-cslap" / "preserved_sources.json"] if p.is_file()
        ],
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None, help="Repository root (defaults to the script's own location)")
    args = parser.parse_args(argv)

    script_path = Path(__file__).resolve()
    # This script lives at <root>/reports/horizon_robustness_results/writing/tools/check_inputs.py,
    # four directories below the repository root.
    root = Path(args.root).resolve() if args.root else script_path.parents[4]

    manifest_path = root / "reports" / "horizon_robustness_results" / "writing" / "governance" / "source_manifest.json"

    if not manifest_path.is_file():
        print(f"INPUTS CHECK FAILED: manifest not found at {manifest_path}")
        return 1
    manifest_bytes = manifest_path.read_bytes()
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        print(f"INPUTS CHECK FAILED: could not parse manifest ({exc})")
        return 1
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    entries = manifest.get("files", [])
    if not entries:
        print("INPUTS CHECK FAILED: empty manifest")
        return 1

    start = time.time()
    problems: list[tuple[str, str]] = []

    manifest_by_group: dict[str, dict[str, dict]] = {}
    for e in entries:
        manifest_by_group.setdefault(e.get("group", ""), {})[e["path"]] = e

    # 1. Recompute SHA-256 for every manifest entry.
    for e in entries:
        rel_path = e["path"]
        fp = root / rel_path
        if not fp.is_file():
            problems.append(("MISSING", rel_path))
            continue
        actual = sha256_file(fp)
        if actual != e.get("sha256"):
            problems.append(("MODIFIED", rel_path))

    # 2. Re-enumerate every pinned group and report files present on disk but absent from the
    #    manifest.
    groups = enumerate_groups(root)
    for group in GROUP_NAMES:
        known = manifest_by_group.get(group, {})
        for p in groups.get(group, []):
            rel = p.relative_to(root).as_posix()
            if rel not in known:
                problems.append(("ADDED", rel))

    # 3. Cross-check per-group manifest entry counts against the counts recorded at manifest
    #    build time (F-012). This is the only way to catch a file deleted together with its own
    #    manifest entry: step 1 no longer sees it (no entry to recompute), and step 2 no longer
    #    sees it either (it is gone from disk), so only a count mismatch reveals the tamper.
    #
    # F-030 (D8c): a manifest with no counts object at all, or missing a count for one of the
    # pinned groups, no longer skips the check silently -- it is a reported problem, one line per
    # missing group ("all" when the whole object is absent), and it fails the run.
    counts = manifest.get("counts")
    if not isinstance(counts, dict):
        problems.append(("MANIFEST COUNTS MISSING", "all"))
        counts = {}
    else:
        for group in GROUP_NAMES:
            # F-041 (N6, U8 fix round 3): a count that is present but not an integer (null, a
            # string, a bool -- bool is an int subclass in Python, so it is excluded explicitly)
            # is exactly as unusable as an absent one and is reported the same way.
            val = counts.get(group, None)
            if group not in counts or not isinstance(val, int) or isinstance(val, bool):
                problems.append(("MANIFEST COUNTS MISSING", group))

    for group in GROUP_NAMES:
        known = manifest_by_group.get(group, {})
        expected_count = counts.get(group)
        if not isinstance(expected_count, int) or isinstance(expected_count, bool):
            continue
        if len(known) != expected_count:
            problems.append((
                "GROUP COUNT MISMATCH",
                f"{group} (manifest has {len(known)} entries, counts records {expected_count})",
            ))

    for kind, path in sorted(set(problems), key=lambda x: (x[1], x[0])):
        print(f"{kind} {path}")

    print(f"MANIFEST SHA256 {manifest_sha256}")

    elapsed = time.time() - start
    if elapsed > 60:
        print(f"WARNING: check_inputs took {elapsed:.1f}s, over the ~60s budget", file=sys.stderr)

    if problems:
        print(f"INPUTS CHANGED ({len(set(problems))} problems)")
        return 1
    print(f"INPUTS UNCHANGED ({len(entries)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
