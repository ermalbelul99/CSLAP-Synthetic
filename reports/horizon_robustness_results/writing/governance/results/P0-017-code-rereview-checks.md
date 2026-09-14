VERDICT: REVISE

This review is static: I only read files and ran nothing. Abbreviations: cg = `W/tools/check_governance.py`, ci = `W/tools/check_inputs.py`, rs = `L/fixtures/check_governance/snapshot_change/run_snapshot_fixture.py`. ORCH's run shows all 27 fixtures matching byte for byte (`L/gate_outputs/fixround_governance_run_all.txt:28`).

## Fix confirmation F-001..F-012
- **F-001:** FIXED (cg:712-715, 943).
- **F-002:** FIXED (cg:619, 632-641).
- **F-003:** FIXED in code (cg:1063-1070, 1098-1103), with the gap documented at cg:17-21. PLAN_ADDENDA.md has no addendum for it. No fixture exercises this path, because the rs tree has no `.git` (cg:1058).
- **F-004:** NOT FIXED for `--compare`. It writes a receipt without validating the ID or the root (cg:1149-1156, 1112). The snapshot side is fixed (cg:1118-1145).
- **F-005:** FIXED (cg:797, 820, 829, 839).
- **F-006:** FIXED (cg:602-605, 676-683).
- **F-007:** FIXED (run_all.py:34-46; rs:85-112). The pass fixture now has a rule (b) finding (findings.jsonl:2) and replaced and second_chair seats (DR-001.md:31-44).
- **F-008:** FIXED (cg:75-79, 256, 292).
- **F-009:** FIXED (cg:493, 515-516), but see D2.
- **F-010:** FIXED (cg:133, 620, 729).
- **F-011:** FIXED (cg:1064, 1191-1197).
- **F-012:** FIXED (ci:144-154, 159).

## A-001 implementation
1. NOT as adopted (cg:917-966); see D3.
2. PARTIAL (cg:872-914); see D7.
3. IMPLEMENTED (cg:179-205); see D4.
4. IMPLEMENTED (cg:208-235). Disposition values are not checked (cg:226).
5. IMPLEMENTED (cg:376-428, 717-719, 756-773); see D5.
6. IMPLEMENTED (cg:360-373, 454-455, 479-481).
7. IMPLEMENTED (cg:776-849).
8. IMPLEMENTED (cg:725-753).
9. IMPLEMENTED (cg:632-641, 108-118, 525-529, 476-484).
10. IMPLEMENTED (cg:252-262, 282-284; log_dispatch.py:95-98).

- **Formats §19:** IMPLEMENTED (cg:116-117, 553-566); see D6.
- **Formats §20:** NOT IMPLEMENTED. cg:171-176 always reads `<stem>.txt` and ignores `output_file` (GOVERNANCE_FORMATS.md:235). The real records pass only because their `output_file` happens to equal that path (gates/P0-G1.json:8, P0-G2.json:9).
- **Amendment R:** not enforced. The P0:G4 entry lists no code-reviewer VERDICT evidence (required_gates.json:44-52).

**U7**
- **(a)** IMPLEMENTED (cg:1220-1264).
- **(b)** IMPLEMENTED for seats (cg:642-645), ballots (659-662), verdicts (203), registry identities (821, 830) and dispatches (299-308). Finding identities are checked only for ORCH-built findings (cg:494), and `raised_by` is never checked. Coverage there is only indirect (cg:307, 343).
- **(c)** PARTIAL; see D6.
- **(d)** IMPLEMENTED. No fixture covers a weight that differs from `vote_weights`, or a `retry_after` already in the past.

## New defects (severity; file:line; claim; evidence; fix)
- **D1, MAJOR; cg:1149-1156.** `--compare ../../../x` writes `<root>/x.compare.json`, and a wrong `--root` creates snapshot directories under that root. Fix: check the ID against `ID_RE` and require the governance directory before any write.
- **D2, MAJOR; cg:516.** The fix confirmer must have log role `critic`. This re-review (seq 17) is logged with role `code_review` (dispatch_log.jsonl:49). Recording it as fix confirmer for F-001..F-012 therefore raises one rule (c) violation per finding. My own F-009 wording caused this. Fix: accept `critic` or `code_review`.
- **D3, MAJOR; cg:925, 936-940.**
  - Every `self` gate is skipped, so `--phase P1` never requires a P0:G4 record. A-001 exempts only "the governance gate being evaluated" (PLAN_ADDENDA.md:13).
  - A manual gate recorded UNMET passes if its evidence resolves.
  - Fix: exempt only the target phase's self gate, and require MET for manual gates.
- **D4, MAJOR; cg:197-201.** A verdict's `result_file` is not tied to the dispatch log's `result_file` for that seq. Any file containing the token satisfies it, for example required_gates.json:200. A null `token` crashes the audit at cg:200. Fix: require the two paths to be equal, and require a string token.
- **D5, MAJOR; cg:402-416.** VERDICT evidence ignores phase, so a P0 plan-reviewer PLAN_SOLID verdict satisfies P5:G3. Fix: match the verdict's `phase` to the gate's phase.
- **D6, MAJOR; cg:538, 560, 571, 664.**
  - A family missing from `weights` gets weight 1, so `"weights": {}` validates an unweighted tally.
  - The final round is computed once for the whole DR. A sub-question settled in an earlier round, as A-004 was in DR-001 (DR-001.md:22-29), gets an empty tally and a false violation.
  - The DR-001 exemption is dead code, because DR-001 carries no `weights`.
  - A DR after U7 that omits `weights` escapes the rule, although U7 requires every DR to record them (user_decisions.md:59).
  - Fix: use the weights from `state.json`, compute the final round per sub-question, require `weights` and `weighted_tally` whenever any seat seq is at least `u7_from_seq`, and remove the exemption.
- **D7, MAJOR; cg:171-176, 902.** §20 is missing. The waiver path also never compares `output_sha256`, so edited output text still passes. Fix: read `output_file` and check its hash on both the MET and waiver paths.
- **D8, MINOR.**
  - The printed snapshot SHA is computed before `snapshot_sha256` is added to the file (cg:1139-1143), so it is not the file's hash.
  - P0-G5.json:11 names `probe_two_families`, a fixture the fix round removed.
  - If `counts` is absent, the group-count check is silently skipped (ci:148).

**Fixture honesty.**
- Each failing fixture's `expected.txt` holds exactly its stated violation. `orch_self_rejection` uses a MINOR finding (findings.jsonl:1), so rule (a) stays silent.
- The pass fixture does not exercise:
  - `round_seqs` or batched positions;
  - weights;
  - `output_file`;
  - `FILE:` or `V-` references;
  - `closed_phases`.

## Required changes (if REVISE)
1. Fix D1 to D7.
2. Add fixtures for:
   - a bad compare ID;
   - a tracked file outside W and L edited twice;
   - a compare that should report MATCH;
   - a weight mismatch;
   - a past `retry_after`;
   - a manual gate recorded UNMET;
   - a verdict pointing at an unrelated file;
   - a batched DR with a sub-question settled only in round 1;
   - an `output_file` that differs from the stem.
3. ORCH items:
   - add code-reviewer VERDICT evidence to P0:G4, which enforces amendment R;
   - add an addendum for the F-003 gap;
   - re-record P0:G5's negative control.
