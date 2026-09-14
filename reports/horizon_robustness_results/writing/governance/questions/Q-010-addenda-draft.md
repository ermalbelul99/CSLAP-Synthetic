## A-001 Governance format and rule-table extensions (P0 plan-conformance gaps 3–7)

DR: DR-001

Source: P0 plan-conformance review (dispatch seq 7), gaps 3–7, together with the P0 code review (seq 6). These are extensions to `GOVERNANCE_FORMATS.md` and to the INV-11 rule table of `check_governance.py`. Plan §5 INV-11 requires both a DR and a new code-reviewer review for such changes.

1. **Required-gate registry** (`W/governance/required_gates.json`). The registry lists every gate of plan §6 (P0–P9) with:
   - its type (`runnable` or `manual`);
   - its expected tokens;
   - its required evidence;
   - the user decisions that may waive it.

   New mode `check_governance.py --phase P#`: every gate of phases up to and including P#, other than the governance gate being evaluated, must have a record. A record passes when either:
   - it is `MET`, with `exit_code` 0 and every expected token found (runnable gates), or with the required evidence present (manual gates); or
   - it is `UNMET` with a valid waiver.

   Without `--phase`, the audit runs as before and applies these completeness rules to phases listed in `state.json` `closed_phases`.

2. **Waivers.** A gate record may carry `waiver: {"by": "USER", "decision": "U#", "file": ".../user_decisions.md", "condition": "..."}`. The waiver is valid only if all three hold:
   - the decision heading exists in `user_decisions.md`;
   - the registry lists that decision as allowed to waive the gate;
   - the `condition` holds. For protected-source waivers, the condition is that the gate output names only the files the decision covers.

3. **Verdict records** (`W/governance/verdicts.jsonl`). Each line has the form `{"id": "V-###", "phase", "seq", "identity", "role", "artifacts": [...], "token": "VERDICT: PASS" | "PLAN_SOLID" | "STATUS: ACCEPTED" | "NARRATIVE_VERDICT: ACCEPTED" | "PROSE_VERDICT: ACCEPTED" | ..., "result_file", "ts"}`. The record is valid only if:
   - `seq` is a completed dispatch with the same identity;
   - `result_file` exists and contains `token` verbatim.

4. **Red-team pre-mortem records** (`W/governance/rtp/RTP-###.json`). Each record has the form `{"id", "phase", "seq", "identity", "package", "points": [{"text", "locator", "disposition": "FIXED|REJECTED|DISCLOSED", "evidence"}]}`. The record is valid only if every point has a disposition with evidence and `seq` is a completed dispatch.

5. **Evidence references.** `evidence_refs` may contain `DR-###`, `F-###`, `V-###`, `RTP-###` or `FILE:<repository path>`, and every reference must resolve. Rule (g) checks each gate's required evidence as listed in the registry, not merely that the reference list is non-empty.

6. **Decision records as verifiers.** `verification.by` may be `"DR-###"`, meaning the finding was decided by that ADP-3 DR. This is the plan §4.4 route for artifacts ORCH built. The DR must be panel ADP-3 or ADP-5, and its `artifacts_under_decision` must include the finding's artifact.

7. **Check-script registry is mandatory.** Every `.py` file under `W/tools/`, `W/math/tools/` and `W/checks/` must be registered in `check_scripts.json`, with `kind` set to `check` or `generator`. The existing rule (h) applies to `check` entries. `W/governance/tools/*.py` are ORCH utilities and are exempt. A missing registry is a violation once any such file exists.

8. **Addenda.** An addendum entry must carry either `DR: DR-###` or `U: U#`, the latter naming a user decision in `user_decisions.md`.

9. **Replaced seats and ballot identity.** As in the clarifications of 14 Sep: seat role `replaced` with `replaced_by_seq`; the ballot's identity is taken from its seat; for ORCH-built artifacts, neither the verifier nor the fix confirmer may be `"ORCH"`.

10. **Dispatch-log completeness.** `log_dispatch.py` requires `--allowed` for builder and check-author roles, and `--inputs` or `--review` for every role other than probe. Earlier events may be corrected by appending a superseding event with the same `seq` and a `correction` field that explains what changed and why. Back-filled timestamps are flagged `"backfilled": true`.

## A-002 Carry user decision U5 into P9 (P0 plan-conformance gap 2)

DR: DR-001

P9 step 1 re-runs `tools/horizon_robustness/check_protected_sources.py`. That script will again report `IJPR_CSLAP_v4.tex` and `IJPR_CSLAP_v4_supplementary.tex` as modified, relative to the prior study's ledger of 8 Sep, because of the user's commit `16b6003`.

Under U5, the P9 record of that re-run is `UNMET` with waiver U5. The waiver is valid if and only if the output lists no modified or missing file other than those two. Any other listed file is a real protected-source change and triggers H7.

This carries an existing user decision forward. It does not create a new waiver.

## A-003 Identity-level reading of P1 critic seats; family-diversity notes (P0 plan-conformance gap 9)

DR: DR-001

Plan §4.4 defines identity as agent type plus model family and forbids a builder from reviewing its own artifact. The plan's own P1 roster already pairs a general-purpose/opus builder (the register) with a results-integrity-reviewer/opus critic.

Now that fable is unavailable, general-purpose/opus also performs document-value extraction B. `results-integrity-reviewer`/opus therefore remains a valid P1 critic: it has a different identity from every builder. The family-level test applies to reseats (§4.4 reseat rule) and to independent confirmers (default-seat table). It does not apply to planned critic seats.

Two diversity notes follow, and both are recorded:

1. After the reseats, the P1 red-team and blue-team seats are both sonnet.
2. ORCH runs on Opus 5. While fable is unavailable, ORCH prefers non-opus independent confirmers for artifacts that ORCH built.

## A-004 Missing P0 deliverables and gate-file corrections (P0 plan-conformance gaps 1 and 8; nice-to-haves)

DR: DR-001

1. **New gate P0:G6 (manual).** `W/governance/environment.md` and `W/evidence/verification_inventory.md` exist and cover plan P0 steps 3 and 6. Evidence: `FILE:` references plus a verdict from the plan-conformance critic.
2. **Automated suites as separate gate records.** P8:G1 and P9:G1 are recorded as one gate record per script of the automated suite:
   - P8: `ck_ext all`, `check_manuscript_claims`, `check_numbers`, `check_numbers --coverage`, `overlap_scan`, `check_anonymisation_writing`, `check_latex_static`, `check_governance --phase P8`.
   - P9: the same suite, plus `check_inputs`, `check_protected_sources` (under A-002), the repository `check_anonymisation`, `verify_campaign --all --authorization`, and `check_latex_static --root W/export`.
3. **Other gate-file corrections.**
   - P0:G3 expects both tokens, `CAMPAIGN ACCOUNTING VERIFIED` and `AUTHORIZATION VERIFIED`.
   - The OWNS lines for P6 and P7 include their fixture directories.
   - Each P8 prose wave produces an `EDIT INVARIANTS PASSED` gate record.
4. **Briefs.** Every brief dispatched from now on carries the `user_decisions.md` pointer.
