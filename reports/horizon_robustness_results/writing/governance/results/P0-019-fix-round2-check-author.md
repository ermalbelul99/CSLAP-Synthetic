All governance checker changes are implemented, all fixtures pass, and the real-root runs are complete. Here is the report in the requested format.

**Files changed.**
- `reports/horizon_robustness_results/writing/tools/check_governance.py`
- `reports/horizon_robustness_results/writing/tools/check_inputs.py`
- `.unlazy/horizon-writing/fixtures/check_governance/run_all.py` (added the compare_bad_id no-write check and the new procedural fixture invocation)
- `.unlazy/horizon-writing/fixtures/check_governance/pass/**` (extended)
- `.unlazy/horizon-writing/fixtures/check_governance/haiku_post_u7/expected.txt` (regression fix, see below)
- 19 new fixture directories under `.unlazy/horizon-writing/fixtures/check_governance/**`
- `.unlazy/horizon-writing/fixtures/check_inputs/counts_missing/**` (new)

**Where each change landed.**
1. F-022 (D1) — `check_governance.py:1258-1268` (`cmd_compare`): validates `ID_RE` then the governance dir before any read/write; prints `COMPARE FAILED: <reason>`.
2. F-023 (D2, Q-011a) — `check_governance.py:357-390` (`check_participant` now takes `expected_roles: set`); call site `check_governance.py:558-559` (`verification.by` still `{"confirmer"}`, `fix_confirmed_by` now `{"critic","code_review"}`).
3. F-024 (D3) — `check_governance.py:1006-1068` (`check_phase_completeness`), new `target_phase_self_exempt` param; self-gate exemption at `1020`; manual-gate MET+evidence rule at `1035-1041`.
4. F-025 (D4) — `check_governance.py:199-240` (`load_verdicts`): token-type check, result_file equality check, no-crash guard.
5. F-026 (D5) — `check_governance.py:427-471` (`resolve_evidence_item`, new `gate_phase` param, VERDICT branch at `444-458`); threaded through call sites at `856`, `1022`, `1040`, `1062`.
6. F-027 (D6) — `check_governance.py:575-669` (`check_weighted_votes`, rewritten: weights from `state.json`, per-sub-question final round, mandatory-once-`applies` rule); call site `746-749` (DR-001 exemption removed).
7. F-028 (D7) — `check_governance.py:186-196` (`load_gate_output_text`, `output_file` param); waiver-path hash check at `986-996`; MET-path at `1047-1049`.
8. F-029 (D8a) — `check_governance.py:1219-1255` (`cmd_snapshot`, two digests) and `1258-1301` (`cmd_compare`, tamper check); documented at `17-27`.
9. F-030 (D8c) — `check_inputs.py:145-158`.
10. F-035 — `check_governance.py:29-36` (module docstring).

**Fixtures.** Added: `compare_bad_id`, `compare_match`, `compare_tracked_outside_edited_twice` (procedural, temporary git repo under `_work/`, `-c user.name=fixture -c user.email=fixture@invalid`), `snapshot_file_tampered`, `weight_mismatch`, `weights_missing_post_u7`, `batched_early_settled_pass`, `probe_fable_retry_past`, `manual_gate_unmet`, `self_gate_earlier_phase_missing`, `self_gate_evidence_unresolved`, `verdict_unrelated_file`, `verdict_null_token`, `verdict_wrong_phase`, `output_file_differs_from_stem_pass`, `output_file_hash_mismatch`, `waiver_hash_mismatch`, `fix_confirmer_code_review_pass`, `fix_confirmer_wrong_role`, and `check_inputs/counts_missing`. `pass` was extended with `round_seqs`, batched sub-questions settled in different rounds, weights, an `output_file` differing from its stem, `FILE:`/`V-` evidence_refs, `closed_phases`, and an F-003 finding fix-confirmed by a `code_review` dispatch. `haiku_post_u7`'s `expected.txt` was updated (2→3 violations): its DR now legitimately also trips the new "seat at/after u7_from_seq but no weights" rule — a real, correct consequence of D6, not a defect.

`run_all.py` result: **`FIXTURES OK (48)`**.

**Real-root output, verbatim.**

`check_inputs.py`, last two lines:
```
MANIFEST SHA256 9fad69dd6da6967b8593d33f44319c2ef43687ea95437991d198f8d3ae8f20d0
INPUTS UNCHANGED (3502 files)
```

`--allow-pending`:
```
IN FLIGHT 19
GOVERNANCE CONSISTENT
```

`--phase P0`, full violation list:
```
VIOLATION (log): IN FLIGHT 19
VIOLATION (a): finding F-004 is CONFIRMED with a null fix_confirmed_by
VIOLATION (a): finding F-022 is CONFIRMED with a null fix_confirmed_by
VIOLATION (a): finding F-023 is CONFIRMED with a null fix_confirmed_by
VIOLATION (a): finding F-024 is CONFIRMED with a null fix_confirmed_by
VIOLATION (a): finding F-025 is CONFIRMED with a null fix_confirmed_by
VIOLATION (a): finding F-026 is CONFIRMED with a null fix_confirmed_by
VIOLATION (a): finding F-027 is CONFIRMED with a null fix_confirmed_by
VIOLATION (a): finding F-028 is CONFIRMED with a null fix_confirmed_by
VIOLATION (a): finding F-031 is PENDING without --allow-pending
VIOLATION (phase): P0:G4 is the target self gate but required evidence {'kind': 'VERDICT', 'agent_type': 'code-reviewer', 'token_any': ['VERDICT: PASS'], 'note': 'DR-001 amendment R: formats sections 9-19 take effect, and P0:G4 can be MET, only after a code-reviewer re-review of the P0 checkers returns VERDICT: PASS (finding F-031).'} does not resolve
VIOLATION (phase): P0:G6 has no gate record (P0)
GOVERNANCE VIOLATIONS (12)
```
All 12 are ORCH's open work, not checker defects: seq 19 is this dispatch, still in flight; F-022–F-028/F-031 are the findings this very round addresses (fix confirmation is the next re-review's job); F-004's remainder is tracked as F-022; F-029/F-030/F-032–F-035 are MINOR so rule (a) doesn't gate them; P0:G4 and P0:G6 are exactly the two gaps the brief said to expect.

`--probe`:
```
family fable: retry after 2026-09-14T19:27:48Z
family haiku: excluded
family opus: available
family sonnet: available
MODEL FAMILIES AVAILABLE (2: opus, sonnet)
```

**Q-cards.** None.
