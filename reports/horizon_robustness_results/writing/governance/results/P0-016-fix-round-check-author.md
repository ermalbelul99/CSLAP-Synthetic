## Report

**Files changed (only the four allowed paths):**
- `reports/horizon_robustness_results/writing/tools/check_inputs.py`: rewritten.
- `reports/horizon_robustness_results/writing/tools/check_governance.py`: rewritten.
- `.unlazy/horizon-writing/fixtures/check_inputs/**`: `pass`, `modified`, `added` and `empty`, plus the new `missing` and `group_count_mismatch`. Each has a `meta.json` and an `expected.txt`.
- `.unlazy/horizon-writing/fixtures/check_governance/**`:
  - rebuilt: `pass`, `orch_self_rejection`, `author_collision`, `empty_log`;
  - rewritten: `snapshot_change/run_snapshot_fixture.py`;
  - added: `met_nonzero_exit`, `replaced_seat_miscounted`, `missing_phase_gate`, `invalid_waiver`, `verdict_token_missing`, `unregistered_check_script`, `duplicate_dr_id`, `addendum_missing_dr`, `haiku_post_u7`, `weighted_tally_mismatch`, `weighted_outcome_mismatch`, `probe_required_available`, `probe_sonnet_missing`, `probe_only_haiku_fable`, `probe_fable_retry_future`, and `run_all.py`;
  - removed: `probe_two_families`.

**Where each required change is implemented:**
1. `rule_e()` (F1): MET requires `exit_code` 0 and `token_found` True.
2. `rule_d()` (F2): `replaced` and `second_chair` seats are excluded from the count, and `replaced_by_seq` is validated against the log.
3. `run_git_status()` and `compute_snapshot()` (F3): git runs with `--no-optional-locks`; a non-zero git exit fails; every porcelain path outside W/L is hashed. The remaining gap is documented in the module docstring.
4. `cmd_snapshot()`, `cmd_compare()` and `write_receipt()` (F4): IDs are validated; existing snapshots are not overwritten; empty snapshots are refused; the SHA-256 is printed; a `<ID>.compare.json` receipt is written.
5. `rule_h()` (F5): scans `all_events`. The registry becomes mandatory once any script exists under W/tools, math/tools or checks. Author and reviewer are resolved through `check_participant`, and paths go through `norm_path()`.
6. `load_drs()`, `load_gates()`, `rule_d()` and `rule_e()` (F6): records are keyed by file name. An id that does not match its file name, or a duplicate gate id, is flagged.
7. Fixtures, `run_all.py` and the rewritten `run_snapshot_fixture.py` (F7).
8. `check_log_integrity()`, `rule_a()`, `rule_b()`, the `load_drs()` regex, `rule_f()`, `run_git_status()` and `cmd_compare()` (F8–F11).
9. `check_inputs.py:main()` (F12): adds `GROUP COUNT MISMATCH` and a `MANIFEST SHA256` line; `elapsed` now drives a warning when a run exceeds 60 s.

**Where each A-001 item is implemented:**
1. `check_phase_completeness()`, `load_registry()` and `phases_up_to()`.
2. `waiver_valid()`.
3. `load_verdicts()`.
4. `load_rtp()`.
5. `ref_exists()` and `resolve_evidence_item()`.
6. `check_dr_ref()`: `verification.by` as `DR-###` (§14/S1).
7. `rule_h()`: the `kind` field.
8. `rule_f()`: the `DR:`/`U:` line.
9. `rule_d()` (`replaced_by_seq`), plus `build_seat_index()` and `rule_c()` (ballot identity through `round_seqs`, §19).

Two further rules:
- The `--allow-pending` default from the Q-card lives in `rule_a()`: a null `fix_confirmed_by` is tolerated only with that flag.
- A-003 (a finding against an ORCH-built artifact is never confirmed by ORCH or by opus) is enforced by `check_orch_confirmer()`, called from `rule_b()`.

**`run_all.py` output:** `FIXTURES OK (27)`, exit 0. The 27 are 6 check_inputs fixtures, 19 check_governance fixtures (audit, phase and probe), and the procedural snapshot control; each is matched on exit code and byte-exact stdout.

**Real-root results:**
- `check_inputs.py`: 12.7 s, `MANIFEST SHA256 9fad69dd...`, `INPUTS UNCHANGED (3502 files)`, exit 0.
- `--allow-pending`: `IN FLIGHT 16`, then `GOVERNANCE CONSISTENT`, exit 0.
- `--phase P0` without `--allow-pending`: exit 1 with 18 violations, all of them real unfinished ORCH work rather than checker bugs:
  - `IN FLIGHT 16`;
  - F-001…F-007 and F-013…F-021 are `CONFIRMED` with a null `fix_confirmed_by`. This is accurate: findings.jsonl records fix confirmation as pending the re-review;
  - `P0:G6 has no gate record`. Also accurate: no gate file exists yet.
- `--probe`: `family fable: retry after 2026-09-14T19:27:48Z`, `family haiku: excluded`, opus and sonnet available, giving `MODEL FAMILIES AVAILABLE (2: opus, sonnet)`, exit 0.

## U7
1. `cmd_probe()` and `family_effective_status()`: haiku's `excluded` status never counts. Fable counts only if `status == "available"` or `now >= retry_after`; otherwise it is reported as `retry after <ts>`. Success requires every entry in `required_families` (default `[opus, sonnet]`); otherwise the probe reports `MODEL FAMILIES INSUFFICIENT (<missing>)`.
2. `check_haiku_post_u7()` and `check_haiku_dispatches()`: applied to DR seats and `round_seqs`, ballots, verdicts, check-script authors and reviewers, findings (`verification.by` and `fix_confirmed_by` through `rule_b`), and raw dispatched events. All are gated on `state.json:u7_from_seq`.
3. `check_weighted_votes()` in `rule_d()`: validates `weights` against `state.json:vote_weights`, recomputes `weighted_tally` from the final round's valid ballots, and requires the recorded outcome to hold a strict weighted majority. DR-001 is exempt.
4. New fixtures, listed above. `run_all.py` covers all of them: a haiku seat and dispatch, a tally mismatch, an outcome mismatch, and four probe scenarios.

## Q-card
- **Question:** where does a runnable gate's raw output text live, for `--phase` token and hash verification and for the waiver `exact_lines` checks?
- **Why it matters:** GOVERNANCE_FORMATS.md §4 stores only `output_sha256`, not the text, and §18 mentions `L/gate_outputs/` only for snapshot-compare receipts.
- **Decisive test:** ask ORCH where P0:G2's stored output actually lives.
- **Options:**
  - (a) `L/gate_outputs/<gate-stem>.txt`. This is what I used, inferred from DR-001's chair_checks (`gate_outputs/P0-G2.txt`) and from §18.
  - (b) Some other convention.
- **Conservative default:** (a), implemented in `load_gate_output_text()`. Class J, because the format document is outside my allowed paths.
