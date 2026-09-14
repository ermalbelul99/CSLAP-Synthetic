I have everything needed. Here is the final report.

## Report

**Files changed** (all within the four allowed paths):
- `reports/horizon_robustness_results/writing/tools/check_governance.py`
- `reports/horizon_robustness_results/writing/tools/check_inputs.py`
- `.unlazy/horizon-writing/fixtures/check_governance/compare_tracked_outside_edited_twice/run_fixture.py` (full rewrite)
- `.unlazy/horizon-writing/fixtures/check_governance/run_all.py`
- New: `.../check_governance/compare_match/run_fixture.py`, `.../check_governance/snapshot_file_tampered/run_fixture.py`
- Removed: `.../compare_match/meta.json`, `.../compare_match/.unlazy/horizon-writing/snapshots/base.compare.json`, `.../snapshot_file_tampered/meta.json`, `.../snapshot_file_tampered/.unlazy/horizon-writing/snapshots/base.compare.json` (leftover receipts, per F-037)
- New fixtures: `.../check_governance/batched_outcome_key_without_ballots/**`, `.../check_governance/weighted_no_valid_ballots_post_u7/**`, `.../check_governance/ballot_missing_round/**`, `.../check_governance/output_file_outside_gate_outputs/**`, `.../check_inputs/counts_null/**`

**Changes 1–6:**
1. **F-036 (N1):** `compare_tracked_outside_edited_twice/run_fixture.py` fully rewritten — loads `check_governance.py` via `importlib.util.spec_from_file_location`, stubs `module.run_git_status` to return `([" M outside.txt"], True, None)`, calls `cmd_snapshot`/`cmd_compare` in-process, exits 1 at the first failed step. No git anywhere. `run_all.py:46-66` (`GIT_ARG_PATTERNS`, `scan_for_git_calls`), `run_all.py:149-169` (proof + real scan wired into `main()`).
2. **F-038 (N3):** `check_governance.py:648-659` (empty-valid-ballots branch) and `check_governance.py:676-681` (empty-relevant per sub-question), inside rewritten `check_weighted_votes` (`check_governance.py:588-707`).
3. **F-037 (N2):** `run_all.py:141-147` (invokes new runners); new `compare_match/run_fixture.py` and `snapshot_file_tampered/run_fixture.py` (each copies `reports/`+`.unlazy/` into `_work/run-<id>/`, runs `--compare`, deletes copy in `finally`); old `meta.json`/receipt files removed from both fixture trees.
4. **F-039 (N4):** `check_governance.py:685-688` — `b.get("round", 1)` used both for `final_round` and the per-ballot filter.
5. **F-040 (N5):** `check_governance.py:199-209` (`gate_output_file_ok` helper) and `check_governance.py:1083-1093` (wired into `check_phase_completeness`'s MET branch).
6. **F-041 (N6):** `check_inputs.py:150-165` — non-int/bool `counts[group]` values now report `MANIFEST COUNTS MISSING <group>` and are excluded from the mismatch check.

**Fixtures added:** `batched_outcome_key_without_ballots`, `weighted_no_valid_ballots_post_u7`, `ballot_missing_round` (passes), `output_file_outside_gate_outputs`, `check_inputs/counts_null` — plus the rewritten `compare_tracked_outside_edited_twice` and the git-free `compare_match`/`snapshot_file_tampered` runners, and the no-git-scan proof pair.
`run_all.py` result: **`FIXTURES OK (55)`**. No `_work/` residue and no `.compare.json` receipts remained in any fixture tree afterward (verified by directory listing).

**Git ban:** No git command was run by me, directly or indirectly — I never invoked `git` in any Bash/PowerShell call, and every fixture now avoids git entirely (stub or `.git`-absent copies). The permitted read-only call inside `check_governance.py` (`--snapshot`/`--compare`) was never exercised on the real root, per instruction. `run_all.py`'s no-git scan reports clean: `ok: check_governance/no_git_scan (proof fires)` and `ok: check_governance/no_git_scan (fixtures are git-free)`.

**Real-root outputs (verbatim):**

`check_inputs.py` (last two lines):
```
MANIFEST SHA256 9fad69dd6da6967b8593d33f44319c2ef43687ea95437991d198f8d3ae8f20d0
INPUTS UNCHANGED (3502 files)
```

`--allow-pending`:
```
IN FLIGHT 23
GOVERNANCE CONSISTENT
```

`--phase P0` (full violation list):
```
VIOLATION (log): IN FLIGHT 23
VIOLATION (a): finding F-036 is CONFIRMED with a null fix_confirmed_by
VIOLATION (a): finding F-038 is CONFIRMED with a null fix_confirmed_by
VIOLATION (phase): P0:G4 is the target self gate but required evidence {'kind': 'VERDICT', 'agent_type': 'code-reviewer', 'token_any': ['VERDICT: PASS'], 'note': 'DR-001 amendment R: formats sections 9-19 take effect, and P0:G4 can be MET, only after a code-reviewer re-review of the P0 checkers returns VERDICT: PASS (finding F-031).'} does not resolve
VIOLATION (phase): P0:G6 has no gate record (P0)
GOVERNANCE VIOLATIONS (5)
```
(The `IN FLIGHT 23` line is this dispatch itself, still open while running; the other four match the brief's expected set exactly: F-036/F-038 fix confirmations, P0:G4 code-reviewer PASS evidence, P0:G6 record.)

`--probe`:
```
family fable: retry after 2026-09-14T19:27:48Z
family haiku: excluded
family opus: available
family sonnet: available
MODEL FAMILIES AVAILABLE (2: opus, sonnet)
```

**Q-cards:** None — no ambiguity required stopping for a decision.
