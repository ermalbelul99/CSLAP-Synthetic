"""ORCH utility: write the P0 source manifest (plan P0 step 4, INV-2).

Pinned: every file under reports/horizon_robustness_results/ except writing/; every root-level
.tex and .bib; manuscript_checks/ (except out/); tools/horizon_robustness/;
Baselines/horizon_robustness/; Baselines/horizon_robustness_analysis/; tests/horizon_robustness/;
.claude/agents, .claude/commands, .claude/skills; .unlazy/horizon-cslap/preserved_sources.json.
__pycache__ directories and .pyc files are excluded everywhere.

For each file the manifest records SHA-256, size and the git blob id of the working-tree bytes.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
R = ROOT / "reports" / "horizon_robustness_results"
W = R / "writing"
OUT = W / "governance" / "source_manifest.json"


def excluded(path: Path) -> bool:
    parts = set(path.parts)
    return "__pycache__" in parts or path.suffix == ".pyc"


def files_under(base: Path, skip: list[Path] = ()) -> list[Path]:
    result = []
    for p in base.rglob("*"):
        if not p.is_file() or excluded(p):
            continue
        if any(s == p or s in p.parents for s in skip):
            continue
        result.append(p)
    return result


def digest(path: Path) -> tuple[str, str, int]:
    sha256 = hashlib.sha256()
    size = path.stat().st_size
    blob = hashlib.sha1(b"blob %d\0" % size)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha256.update(chunk)
            blob.update(chunk)
    return sha256.hexdigest(), blob.hexdigest(), size


def main() -> int:
    groups: dict[str, list[Path]] = {
        "results_except_writing": files_under(R, skip=[W]),
        "root_tex_bib": sorted(p for p in ROOT.iterdir() if p.is_file() and p.suffix in (".tex", ".bib")),
        "manuscript_checks": files_under(ROOT / "manuscript_checks", skip=[ROOT / "manuscript_checks" / "out"]),
        "tools_horizon_robustness": files_under(ROOT / "tools" / "horizon_robustness"),
        "baselines_horizon_robustness": files_under(ROOT / "Baselines" / "horizon_robustness"),
        "baselines_horizon_robustness_analysis": files_under(ROOT / "Baselines" / "horizon_robustness_analysis"),
        "tests_horizon_robustness": files_under(ROOT / "tests" / "horizon_robustness"),
        "claude_agents_commands_skills": files_under(ROOT / ".claude" / "agents")
        + files_under(ROOT / ".claude" / "commands") + files_under(ROOT / ".claude" / "skills"),
        "prior_study_ledger": [ROOT / ".unlazy" / "horizon-cslap" / "preserved_sources.json"],
    }
    entries = []
    for group, paths in groups.items():
        for p in sorted(set(paths)):
            sha, blob, size = digest(p)
            entries.append({"path": p.relative_to(ROOT).as_posix(), "group": group, "sha256": sha,
                            "git_blob_worktree": blob, "size": size})
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    manifest = {
        "created": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_head": head,
        "companion_reference": {
            "decision": "D2 default: root IJSSOL_CSLAP_v1.tex, IJSSOL_CSLAP_v1_supplementary.tex and IJSSOL_CSLAP_v1.bib at HEAD are the aligned companion; manuscript_checks/baseline/IJSSOL_CSLAP_v1.tex is recorded as the pre-revision copy",
            "files": ["IJSSOL_CSLAP_v1.tex", "IJSSOL_CSLAP_v1_supplementary.tex", "IJSSOL_CSLAP_v1.bib"],
        },
        "counts": {g: len(set(p)) for g, p in groups.items()},
        "files": entries,
    }
    OUT.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(f"MANIFEST WRITTEN ({len(entries)} files, HEAD {head[:7]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
