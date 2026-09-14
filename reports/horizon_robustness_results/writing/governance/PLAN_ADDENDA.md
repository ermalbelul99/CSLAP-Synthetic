# Plan addenda

Corrections to `WRITING_ORCHESTRATION_PLAN_20260914.md` made after the go. Every entry has a `## A-### <title>` heading and a line `DR: DR-###` or `U: U#`.

## A-001 Governance format and rule-table extensions (P0 plan-conformance gaps 3–7)

DR: DR-001

**Effective date (amendment R).** These rule-table changes take effect only once the code-reviewer re-review of the P0 fix round returns `VERDICT: PASS`, recorded as a verdict record. Until then, P0:G4 cannot be recorded MET.

1. **Required-gate registry** (`W/governance/required_gates.json`).
   - The registry lists every gate of plan §6 (P0–P9) with its type (runnable or manual), expected tokens, required evidence and waiving user decisions.
   - New mode `check_governance.py --phase P#`: every gate of phases up to P# must have a record, except the governance gate being evaluated.
   - A record passes if it is MET (exit_code 0 and every expected token found for runnable gates; the required evidence present for manual gates), or if it is UNMET with a valid waiver.
   - Without `--phase`, the audit applies these completeness rules to the phases listed in `state.json` `closed_phases`.
2. **Waivers** (amendment S3). A gate record may carry `waiver: {"by": "USER", "decision": "U#", "file": ".../user_decisions.md", "condition": "..."}`. The waiver is valid only if all of the following hold:
   - the decision heading exists in `user_decisions.md`;
   - the registry lists that decision as allowed to waive the gate;
   - the `condition` field is present and holds. A missing or empty `condition` makes the waiver invalid;
   - for protected-source waivers, `exit_code` is 1 and the stored output is exactly one `MODIFIED protected file: <f>` line for each file the decision covers, with no other line.

   The P0:G2 record receives this `condition` before P0:G4 runs.
3. **Verdict records** (`W/governance/verdicts.jsonl`). Each line has the form `{"id": "V-###", "phase", "seq", "identity", "role", "artifacts": [...], "token", "result_file", "ts"}`. A record is valid only if `seq` is a completed dispatch with the same identity and `result_file` contains `token` verbatim.
4. **Red-team pre-mortem records** (`W/governance/rtp/RTP-###.json`). Each record has the form `{"id", "phase", "seq", "identity", "package", "points": [{"text", "locator", "disposition": "FIXED|REJECTED|DISCLOSED", "evidence"}]}`. A record is valid only if every point has a disposition with evidence and `seq` is a completed dispatch.
5. **Evidence references.** `evidence_refs` may contain `DR-###`, `F-###`, `V-###`, `RTP-###` or `FILE:<repository path>`, and every reference must resolve. Rule (g) checks each gate's required evidence as listed in the registry, not merely that the references are non-empty.
6. **Decision records as verifiers** (amendment S1). `verification.by` may be `"DR-###"`, meaning that ADP-3 DR decided the finding. This is the plan §4.4 route for artifacts ORCH built. The DR must be panel ADP-3, and its `artifacts_under_decision` must include the finding's artifact.
7. **Mandatory check-script registry.** Every `.py` file under `W/tools/`, `W/math/tools/` and `W/checks/` must appear in `check_scripts.json` with `kind` set to `check` or `generator`. The existing rule (h) applies to `check` entries. `W/governance/tools/*.py` are ORCH utilities and are exempt. A missing registry is a violation once any such file exists.
8. **Addenda.** An addendum entry must carry either `DR: DR-###` or `U: U#`, the latter naming a user decision in `user_decisions.md`.
9. **Replaced seats and ballot identity.** As in the clarifications of 14 Sep:
   - seat role `replaced` requires `replaced_by_seq`;
   - a ballot's identity is taken from its seat;
   - for artifacts ORCH built, the verifier and the fix confirmer are never `"ORCH"`.
10. **Dispatch-log completeness** (amendment S3).
    - `log_dispatch.py` requires `--allowed` for builder and check-author roles, and `--inputs` or `--review` for every role other than probe.
    - Earlier events may be corrected by appending a superseding event with the same `seq` and a `correction` field saying what changed and why. A correction event is matched on (`seq`, `event`).
    - Back-filled timestamps are flagged `"backfilled": true`.
    - Every `completed` event carries `self_reported_model` as a string, or the literal `"not reported"`.

## A-002 Carry user decision U5 into P9 (P0 plan-conformance gap 2)

DR: DR-001

P9 step 1 re-runs `tools/horizon_robustness/check_protected_sources.py`. That run will again report `IJPR_CSLAP_v4.tex` and `IJPR_CSLAP_v4_supplementary.tex` as modified relative to the prior study's ledger of 8 Sep, because of the user's commit `16b6003`.

Under U5, the P9 record of that re-run is `UNMET` with waiver U5. The waiver is valid if and only if all three hold:
- (i) `exit_code` is 1;
- (ii) the output consists of exactly the lines `MODIFIED protected file: IJPR_CSLAP_v4.tex` and `MODIFIED protected file: IJPR_CSLAP_v4_supplementary.tex`, in either order, and no other line;
- (iii) the `check_inputs.py` record from the same P9 run is `MET`.

Any other `MODIFIED` or `MISSING` line, or a failure of `check_inputs.py`, triggers H7. Any other output leaves the record `UNMET` with no waiver, and H8 applies.

## A-003 Identity-level reading of P1 critic seats; family diversity (P0 plan-conformance gap 9)

DR: DR-001

Plan §4.4 defines identity as agent type plus model family, and forbids a builder from reviewing its own artifact. The plan's own P1 roster already pairs a general-purpose/opus builder (the register) with a results-integrity-reviewer/opus critic.

With fable unavailable, general-purpose/opus also performs document-value extraction B. `results-integrity-reviewer`/opus nevertheless remains a valid P1 critic, because its identity differs from that of every builder. The family-level test applies to reseats (§4.4 reseat rule) and to independent confirmers (default-seat table); it does not apply to planned critic seats.

Recorded notes:

1. After the reseats, the P1 red-team and blue-team seats are both sonnet.
2. ORCH runs on Opus 5 and counts as family opus for §4.4. Independent confirmers and fix confirmers of an artifact ORCH built must come from an available non-opus family, as the default-seat table requires ("family different from the builder"). If no non-opus family is available for the needed agent type, the finding goes to ADP-3.

## A-004 Missing P0 deliverables and gate-file corrections (P0 plan-conformance gaps 1 and 8; nice-to-haves)

DR: DR-001

1. **New gate P0:G6 (manual).** `W/governance/environment.md` and `W/evidence/verification_inventory.md` exist and cover plan P0 steps 3 and 6. Evidence: `FILE:` references plus a verdict from the plan-conformance critic.
2. **Automated suites as separate records.** P8:G1 and P9:G1 are recorded as one gate record per script of the automated suite:
   - P8: `ck_ext all`, `check_manuscript_claims`, `check_numbers`, `check_numbers --coverage`, `overlap_scan`, `check_anonymisation_writing`, `check_latex_static`, `check_governance --phase P8`.
   - P9: the same scripts, plus `check_inputs`, `check_protected_sources` (under A-002), the repository `check_anonymisation`, `verify_campaign --all --authorization`, and `check_latex_static --root W/export`.
3. **Gate-file corrections.**
   - P0:G3 expects both tokens (`CAMPAIGN ACCOUNTING VERIFIED`, `AUTHORIZATION VERIFIED`).
   - The OWNS lines of P6 and P7 include their fixture directories.
   - Each P8 prose wave produces an `EDIT INVARIANTS PASSED` gate record.
4. **Briefs.** Every brief dispatched from now on carries the `user_decisions.md` pointer.

## A-005 Tooling fix-round budget before H8 (hard stop H8-P0-001)

U: U8

This amends plan §3 H8 and §4.5 (targeted fix round) for tooling gates only.

**Tooling-gate failure.** A required gate that fails only because of open findings against a check script or fixture under `W/tools/`, `W/math/tools/`, `W/checks/` or `L/fixtures/`.

**The budget.** For such a failure, ORCH may run up to 2 further targeted fix rounds beyond the one the plan allows, before H8 applies.
- Each round is followed by a `code-reviewer` re-review.
- The budget is counted per phase.
- In P0, fix round 3 (seq 23) is the first of the two.

H8 applies unchanged to every other gate: evidence, claims, numbers, literature, mathematics and manuscript.

## A-006 No git writes; D1 commits suspended

U: U8

1. **D1 suspended.** Decision D1 (§2) is suspended until the user lifts the git restriction in U8. There is no commit at the ends of P4, P7 and P9. At each of those points ORCH instead takes `check_governance.py --snapshot P4-END`, `P7-END` or `P9-END`, and records the snapshot SHA-256 lines in `L/status.log`.
2. **H5 covers every git write.** That means `commit`, `push`, `init`, `add`, `stash`, `checkout`, `reset` and `config`, in the project repository or in any temporary repository.
3. **Allowed git calls.** Agents run no git command, and fixtures and tools stub git. The only git calls allowed are:
   - ORCH's read-only inspection (`git --no-optional-locks status`, `log`, `diff`);
   - the read-only status call inside `check_governance.py`.
4. **Commit messages.** Steps that would produce a commit (Appendix F) write the commit message text to `W/governance/commit_messages/<phase>.txt` only, for the user to use later.
