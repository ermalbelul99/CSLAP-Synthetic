## Report

**1. Files written** (all within the four allowed paths)
- `reports/horizon_robustness_results/writing/tools/check_inputs.py`
- `reports/horizon_robustness_results/writing/tools/check_governance.py`
- `.unlazy/horizon-writing/fixtures/check_inputs/{pass,modified,added,empty}/**`
- `.unlazy/horizon-writing/fixtures/check_governance/{pass,orch_self_rejection,author_collision,empty_log,probe_two_families}/**` and `.../snapshot_change/run_snapshot_fixture.py`

**2. CLI and success tokens**

`check_inputs.py [--root DIR]`
- `INPUTS UNCHANGED (<n> files)`
- `INPUTS CHANGED (<k> problems)`
- `INPUTS CHECK FAILED: ...`

`check_governance.py [--root DIR] [--allow-pending]`
- `GOVERNANCE CONSISTENT`
- `GOVERNANCE VIOLATIONS (<k>)`

`check_governance.py --snapshot ID [--root DIR]`
- `SNAPSHOT WRITTEN <ID>`

`check_governance.py --compare ID [--root DIR]`
- `SNAPSHOT MATCH <ID>`
- `SNAPSHOT CHANGED <ID>`

`check_governance.py --probe [--root DIR]`
- `MODEL FAMILIES AVAILABLE (<n>: names)`
- `MODEL FAMILIES INSUFFICIENT (<n>)`

Both scripts sit at `W/tools/` (`reports/horizon_robustness_results/writing/tools/`), four directories below the repository root. The brief specified `parents[3]` as the default root. I checked `Path(__file__).resolve().parents[N]` directly: `parents[3]` resolves to `.../reports`, one level too high, so the default `--root` would not work. Both scripts use `parents[4]`, which I confirmed against `git rev-parse --show-toplevel`.

**3. Fixtures and observed exit codes**

| Fixture | Exit |
|---|---|
| `check_inputs/pass` | 0 (`INPUTS UNCHANGED (12 files)`) |
| `check_inputs/modified` | 1 (`MODIFIED tools/horizon_robustness/sample_tool.py`) |
| `check_inputs/added` | 1 (`ADDED tests/horizon_robustness/test_extra_unlisted.py`) |
| `check_inputs/empty` | 1 (`INPUTS CHECK FAILED: empty manifest`) |
| `check_governance/pass` | 0 (`GOVERNANCE CONSISTENT`) |
| `check_governance/orch_self_rejection` | 1 (rules a+b) |
| `check_governance/author_collision` | 1 (rule h) |
| `check_governance/empty_log` | 1 (zero-items rule) |
| `check_governance/probe_two_families` (`--probe`) | 1 (`MODEL FAMILIES INSUFFICIENT (2)`) |
| `check_governance/snapshot_change/run_snapshot_fixture.py` | 1 (propagates `--compare`'s exit; the negative control fired correctly) |

Testing found one bug, now fixed. Rule (h) first scanned raw dispatch events, so each seq's `dispatched` and `completed` records were counted twice and every violation printed twice. It now scans only the latest event per `seq`.

**4. Real-root run.** `check_inputs.py` with no `--root` (default resolution), over the actual 1.7 GB pinned set: 13 seconds, result line `INPUTS UNCHANGED (3502 files)`, exit 0.

**5. Q-cards (ambiguities in `GOVERNANCE_FORMATS.md`), Class J**

- **Q-card A.** Rule (a) says the verifier and fix confirmer "must not equal the `built_by` identity (same agent_type and family)". But `built_by` and `verification.by` can both be the bare string `"ORCH"`, which has no agent_type or family. The format document offers no decisive test; this is a design choice.
  - Option (i): treat `"ORCH"=="ORCH"` as an identity match, and so a violation. This is consistent with plan §4.4: "for artifacts ORCH built, ... by an independent confirmer".
  - Option (ii): exempt ORCH from rule (a) entirely, leaving only rule (b)'s narrower REJECTED case covered.
  - Implemented: (i), the conservative default.
- **Q-card B.** Rule (c) says it covers "DR ballots", but the ballot schema (`{"seq","round","valid","position"}`) carries no `agent_type` or `family`; only seats do. The document offers no decisive test.
  - Implemented (conservative default): a ballot's identity is resolved through the seat with the same `seq` in the same DR. An orphan ballot, with no matching seat, is itself flagged.
- **Q-card C.** Rule (d)'s seat-count check excludes "second_chair and replaced voters", but the seat schema has no field that marks a seat as replaced.
  - Implemented (conservative default): no seat is treated as replaced, so every seat that is not second_chair counts, because the format defines no such marker.
