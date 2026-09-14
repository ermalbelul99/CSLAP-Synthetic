VERDICT: REVISE

This review is static: I read files and ran nothing. Abbreviations: cg = `W/tools/check_governance.py`, ci = `W/tools/check_inputs.py`, rf = `L/fixtures/check_governance/compare_tracked_outside_edited_twice/run_fixture.py`, Fx = `L/fixtures/check_governance`. ORCH's run printed `FIXTURES OK (48)` (`L/gate_outputs/fixround2_run_all.txt:49`).

## Fix confirmation (F-022..F-030, F-035) and regressions
- **F-022:** FIXED (cg:1262-1268). F-004 is now fixed too.
- **F-023:** FIXED (cg:386-390, 559). This matches formats §2 (`GOVERNANCE_FORMATS.md:48`) and Q-011 (a).
- **F-024:** FIXED. Only the target phase's self gate is exempt (cg:1020, 1121), its evidence is still checked (cg:1021-1023), and a manual gate needs MET (cg:1037-1038).
- **F-025:** FIXED (cg:222-237).
- **F-026:** FIXED (cg:446, 455; passed on at 468, 856, 1022, 1040, 1062).
- **F-027:** FIXED (cg:579-615, 637-645). The DR-001 exemption is gone (cg:746-749). The real DR-001 seat seqs are 9-15 (`DR-001.md:16-19`), all below `u7_from_seq` 17 (`state.json:64`).
- **F-028:** FIXED (cg:186-196, 994, 1047-1049).
- **F-029:** FIXED (cg:1245-1254, 1297-1301; docstring cg:17-23).
- **F-030:** FIXED (ci:148-155).
- **F-035:** FIXED (cg:29-36).

**No regressions.**
- F-001 to F-012: F-001 (cg:796-799), F-002 (701, 714-723), F-003 (1198-1205, now exercised by rf), F-005 (922-933), F-006 (159-172, 764-767), F-008 (287-297), F-009 (386-390, 534-551), F-010 (148, 702, 811-814), F-011 (1166, 1171-1172), F-012 (ci:157-166).
- A-001 items 1-10, formats §19 (cg:123-133, 640) and §20 all hold.
- Amendment R is enforced (`required_gates.json:52-61`; cg:1020-1023).
- U7:
  - (a) and (b), Haiku exclusion: cg:334-354 and its call sites.
  - (c), weights: cg:575-669.
  - (d), Fable retry window: cg:1358-1363.

## Fixture honesty
**All 20 required fixtures exist and match** (`fixround2_run_all.txt:1-48`). Each `expected.txt` holds only its stated violation. Spot checks:
- **`verdict_unrelated_file`:** `other.md:1` contains the token, so the only failure is the `result_file` mismatch.
- **`verdict_wrong_phase`:** the verdict's phase is P1 (`verdicts.jsonl:1`).
- **`output_file_differs_from_stem_pass`:** there is no stem file, so a stem fallback would fail.
- **`snapshot_file_tampered`:** the stored digest has 63 digits (`base.json:10`).
- **`probe_fable_retry_past` / `_future`:** the dates are 2020 and 2099, so both results are stable.
- **`haiku_post_u7`:** its third line is a correct consequence of F-027.

**The `pass` fixture now exercises all six items:**
- **`round_seqs` and batched positions:** `Fx/pass/.../DR-001.md:15-17, 65-100`.
- **Weights, with the rule applying:** `DR-001.md:52-64`; `state.json:4`.
- **`output_file`:** `TEST-G1.json:15`. The stale stem file holds different text (`TEST-G1.txt:1`), so reading the wrong file would fail.
- **`FILE:` and `V-` references:** `TEST-G2.json:10-15`.
- **`closed_phases`:** `state.json:10-12`. The self gate TEST:G3 has to have a record.
- **A `code_review` fix confirmer:** `findings.jsonl:3`; `dispatch_log.jsonl:14`. Rule (c) checks every severity (cg:555-559), so the MINOR finding is still tested.

**Writes and git.**
- **Procedural runners:** they write only under `_work/run-*` and delete it in `finally` (`run_snapshot_fixture.py:72, 113-115`; rf:90, 141-143). `_work` currently holds no files.
- **Git calls:** they use `-C tmp` and the fixture identity (rf:35-41), except on the failure path in N1.
- **Compare receipts:** `compare_match` and `snapshot_file_tampered` write `base.compare.json` inside their own fixture trees (cg:1331; the file exists under `Fx/compare_match/.unlazy/horizon-writing/snapshots/`). See N2.

## New defects (severity; file:line; claim; evidence; fix)
- **N1, MAJOR; rf:97-102.** If `git init` fails, the script keeps going.
  - Evidence: each step only does `ok &= expect(...)`. `git -C tmp add` and `commit` would then find the project repository that contains `_work`. `add` fails because `.unlazy` is gitignored (F-035), but `commit` would commit the project's staged changes under the identity "fixture".
  - Fix: return 1 at the first failed git step. Also set `GIT_CEILING_DIRECTORIES` to `_work` for every git call, or check that `rev-parse --show-toplevel` equals tmp.
- **N2, MINOR; cg:1275, 1331.** Compare receipts land outside `_work` with a new timestamp on every run, so the fixture tree changes each time.
  - Results are unaffected, because the snapshots directory is excluded from hashing (cg:1189).
  - Fix: run those two compares on a copy under `_work`.
- **N3, MAJOR; cg:622-623, 643-644.** The weighted-vote check can pass without checking anything.
  - Evidence: a sub-question with no ballot position for it is skipped. An outcome key typed "A-01" against positions keyed "A-001" therefore passes with no tally check. A post-U7 DR whose ballots are all invalid also returns ok. The seq 16 code flagged the first case.
  - Fix: make both cases violations, unless that sub-question's rule is runoff, conservative_default, fallback or orch_pick.
- **N4, MINOR; cg:645 vs 648.** A ballot with no `round` counts as round 1 when the final round is chosen, but is dropped from the tally.
  - Fix: use the same default in both places.
- **N5, MINOR; cg:189-190.** `output_file` is not confined to `L/gate_outputs/`, although §20 requires it (`GOVERNANCE_FORMATS.md:237`).
  - Fix: check the path prefix.
- **N6, MINOR; ci:154, 159-161.** A `counts` entry that is present but null skips the count check silently.
  - Fix: report any non-integer count as MISSING.

## Real-root P0 violations
All 11 recorded violations (`fixround2_real_phase_P0.txt:1-11`) are ORCH's open work, not checker defects:
- **Lines 1-8:** fix confirmations for F-004 and F-022 to F-028, which can be recorded once a re-review passes.
- **Line 9:** F-031 is waiting for a non-opus confirmer (A-003).
- **Line 10:** P0:G4 needs a verdict record.
- **Line 11:** the P0:G6 gate record is missing.

F-032 does not appear because the checker looks only at the negative control's exit code, not whether its fixture exists (cg:1059). That is the existing design, not a regression.

## Required changes (if REVISE)
1. **N1:** abort at the first failed git step and keep git from finding the project repository (rf).
2. **N3:** flag a sub-question with no ballot positions and a post-U7 DR with no valid ballots, keeping the four rule exemptions (cg).
3. **Add fixtures:** `batched_outcome_key_without_ballots` (must fail), plus one runner check that a failed git step exits before any further git call.
4. **Optional this round:** N2, N4, N5 and N6. ORCH may record them as MINOR findings.
5. **Then:** a narrow re-review of rf and cg:575-669 only.
