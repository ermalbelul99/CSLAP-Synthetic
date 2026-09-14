Read the ballot brief and all required evidence: the Q-010 card, the addenda draft, plan §0, §3, §4.3, §4.4 and §5, user_decisions.md, the P0-007 plan-conformance review, GATES.md, and leaf-P0, leaf-P8 and leaf-P9. The findings follow as four ballot blocks in the brief's Appendix B format.

```
BALLOT  Q-010/A-001  voter: plan-reviewer/sonnet  round: 1  seat: plain  slice: S1
POSITION: b
AMENDMENT (if b): In item 6, replace "The DR must be panel ADP-3 or ADP-5" with "The DR must be panel ADP-3."
REASONS:
1. Items 1-5 and 7-10 fix exactly the defects the plan-conformance review found: the registry gap (cg:28, no required-gate list), rule (e) accepting UNMET or absent records (cg:322-323, 346-349), rule (g) checking only that refs are non-empty (cg:351-359), and rule (h) passing vacuously (cg:364-365) [P0-007-conformance-plan-reviewer.md gaps 3, 4, 6].
2. Item 6's confirmer route matches plan §4.4's rejection route for ORCH-built artifacts. The plan text, however, names only "an independent confirmer or ... an ADP-3" (plan:247-248), and the review's own recommended fix reads "when that DR is an ADP-3" [P0-007-conformance-plan-reviewer.md gap 5, line 29]. The draft's "ADP-3 or ADP-5" widens the route without a stated reason.
3. Every listed item carries "DR: DR-001" (Q-010-addenda-draft.md:3). That satisfies plan §0's DR requirement for post-go corrections (plan:28) and INV-11's "changes to the table require a DR" (plan:421).
STEELMAN:
(a) Adopt as drafted: gaps 3-7 map one-to-one onto verified defects, so verbatim adoption is fastest and lowest-risk. Fails because item 6 still goes beyond the reviewer's own scoped fix and the plan's literal wording, with no justification recorded in the DR.
(c) Reject: bundling eight rule and format changes in one DR is a large simultaneous change. Fails because rules (e), (g) and (h) are independently confirmed to pass vacuously today (cg:322-323, 351-359, 364-365). That itself breaches INV-11's "no empty passes" (plan:408), and leaving them open blocks an honest P0:G4.
BLOCKING OBJECTION: none
PROPOSED MISSING OPTION: none
CONFIDENCE: medium
WOULD CHANGE MY MIND: a locator showing that plan §4.4, or a prior DR, already extends the ORCH-artifact rejection route to ADP-5.
```

```
BALLOT  Q-010/A-002  voter: plan-reviewer/sonnet  round: 1  seat: plain  slice: S1
POSITION: a
AMENDMENT (if b): n/a
REASONS:
1. The waiver condition ("lists no modified or missing file other than those two") matches user_decisions.md:24-27 verbatim, including the instruction not to refresh the ledger.
2. Without this addendum, P9's re-run of check_protected_sources.py fails again on the same two files (P0-007-conformance-plan-reviewer.md gap 2, citing P0-G2.txt:1-2 and plan:1025). An UNMET runnable gate after the fix round is H8 (plan:137), on a question the user has already closed.
3. user_decisions.md:4 states that a user decision "needs no decision record", so citing "U: U5" rather than a fresh DR is the correct mechanism. A-001 item 8, in this same round, is what lets a gate record cite U-numbers.
STEELMAN:
(b) Amend the condition wording: no gap found. The drafted condition is copied from the user's own list of consequences (user_decisions.md:26), so there is nothing to tighten.
(c) Reject, and edit check_protected_sources.py's ledger instead: fails because user_decisions.md:26 explicitly forbids refreshing or editing the prior study's ledger. Doing so would also breach H2 (protected-source edit, plan:131) if the ledger counts as a protected artifact.
BLOCKING OBJECTION: none
PROPOSED MISSING OPTION: none
CONFIDENCE: high
WOULD CHANGE MY MIND: evidence that a file other than the two named IJPR files is also modified, which would make the waiver invalid under A-001 item 2's own condition test.
```

```
BALLOT  Q-010/A-003  voter: plan-reviewer/sonnet  round: 1  seat: plain  slice: S1
POSITION: a
AMENDMENT (if b): n/a
REASONS:
1. The plan's own P1 roster already pairs `results-integrity-reviewer`/opus as critic with the register's builder. The blue-team seat is separately qualified as one "which built none of these artifacts" (plan:587-588). The plan therefore distinguishes identity (agent type) from family at this seat, rather than testing family alone.
2. The reseat rule at plan:241-245 governs filling a seat "after a collision, or when a family is unavailable". `results-integrity-reviewer`/opus was not reseated (P0-007-conformance-plan-reviewer.md gap 9), so that rule's family-level test does not apply.
3. The family-difference language at plan:288 is scoped to the "Independent confirmer" row of the default-seats table. That is a distinct role from a pre-planned BCL critic seat (plan §4.5, BCL steps 2-3), so it does not transfer to this seat by default.
STEELMAN:
(b) Amend the plan text to spell out "identity, not family": unnecessary, because the plan's pre-go roster (lines 587-588) already implements this reading. Adding the text changes nothing operative.
(c) Reject, and reseat the critic to a non-opus family for a uniform safety margin: fails against the plan's own precedent at lines 587-588. It would also spend a reseat on a seat that never collided, contrary to the reseat rule's trigger condition (plan:242).
BLOCKING OBJECTION: none
PROPOSED MISSING OPTION: none
CONFIDENCE: medium
WOULD CHANGE MY MIND: a P1-specific rule elsewhere in the plan, not found by this search, that explicitly requires family difference for BCL critic seats as well as confirmers.
```

```
BALLOT  Q-010/A-004  voter: plan-reviewer/sonnet  round: 1  seat: plain  slice: S1
POSITION: a
AMENDMENT (if b): n/a
REASONS:
1. Confirmed directly: `.unlazy/horizon-writing/gates/leaf-P8.md` and `leaf-P9.md` each run a single CHECK (check_governance.py and check_latex_static.py respectively), not the full suite named at plan lines 1001-1002, 1020, 1024-1025 and 1044. This matches gap 1's fix of one gate record per suite script.
2. Confirmed directly: `.unlazy/horizon-writing/gates/leaf-P0.md` has no G6 and no check of environment.md or verification_inventory.md, matching gap 8. Both files are required deliverables (plan:449-450, 466-467).
3. Confirmed directly: P0:G3's CHECK has one EXPECT token in leaf-P0.md:17, while P0-G3.txt reports two tokens at lines 11 and 22. This is exactly the mismatch A-004 item 3 fixes. INV-11's "no empty passes" and exact token matching (plan:403-408) require both tokens to be checked.
STEELMAN:
(b) Merge the per-script suite checks into one combined P8/P9 gate record: fails INV-11 rule (e), which requires "its exit code and hash recorded" per gate (plan:415). A combined record cannot show which script failed, so it would reproduce today's defect at a larger scale.
(c) Reject, and defer these corrections until after P0:G4: fails because P0-007-conformance-plan-reviewer.md's consensus note requires gaps 1 and 8 to be closed "before P0:G4 closes" (line 59). The token and fixture-directory fixes address mismatches already observed, not new scope.
BLOCKING OBJECTION: none
PROPOSED MISSING OPTION: none
CONFIDENCE: high
WOULD CHANGE MY MIND: evidence that leaf-P8.md and leaf-P9.md already contain the per-script CHECK/EXPECT lines that A-004 says are missing.
```

Escalation: none required. All four positions rest on locators I read directly, and I found no blocking objection. Route the consensus tally to the orchestrator, per the brief.

**Files read:** `reports/horizon_robustness_results/writing/governance/questions/Q-010.md`, `.../Q-010-addenda-draft.md`, `.../governance/user_decisions.md`, `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (§0, §3, §4.3, §4.4, §5), `.../writing/governance/results/P0-007-conformance-plan-reviewer.md`, `.unlazy/horizon-writing/GATES.md`, `.unlazy/horizon-writing/gates/leaf-P0.md`, `leaf-P8.md`, `leaf-P9.md`.
