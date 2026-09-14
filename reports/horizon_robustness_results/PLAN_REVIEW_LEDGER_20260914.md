# Plan review ledger: WRITING_ORCHESTRATION_PLAN_20260914.md

14 September 2026. This ledger records how each review finding on the orchestration plan was
handled. The executing run pins it in P0 and uses it as a requirements source in P1 step 4.
Every adopted finding was first checked against the repository by the orchestrator; the check
is noted where it decided the outcome.

## Reviews run

| ID | Reviewer (agent/model) | Plan revision | Verdict |
|---|---|---|---|
| DRY1 | general-purpose/sonnet, execution dry run | 1 | 3 blockers, 5 guess points, 3 contradictions |
| RT1 | scientific-reviewer/fable, red team | 1 | SOUND_WITH_FIXES (5 blocking, 11 major) |
| PR1 | plan-reviewer/opus, plan gate | 1 | PLAN_NEEDS_REVISION (20 gaps) |
| RT2 | scientific-reviewer/fable, red-team closure | 2 | SOUND_WITH_FIXES (3 new blocking) |
| PR2 | plan-reviewer/opus, gate round 2 | 2 | PLAN_NEEDS_REVISION (8 open, 9 new) |
| RT3a | scientific-reviewer/fable, red-team round 3 | 3 | Failed before review: HTTP 429, out of fable usage credits (plan F21) |
| RT3 | scientific-reviewer/sonnet, red-team round 3 (retry) | 3 | SOUND (0 blocking) |
| PR3 | plan-reviewer/opus, gate round 3 (final under cap) | 3 | PLAN_NEEDS_REVISION (1 blocking) |

Revision 4 closes the one blocking PR3 gap exactly as that reviewer specified. No fourth gate round was run. Plan decision D5 leaves this choice to the user, and P0 step 7 runs plan-reviewer again before any other work.

## Rejected findings

| Finding | Reason, with evidence |
|---|---|
| DRY1 G5: the commit trailer should name Sonnet 5 | The orchestrating session runs Claude Opus 5 under its own attribution instruction. The reviewer was quoting its own session's model. Plan Appendix F now says the trailer follows the orchestrator's instruction at commit time. |
| PR1 nice-to-have: `.unlazy/` is not gitignored | `git check-ignore -v .unlazy/horizon-cslap/PLAN.md` prints `.unlazy/.gitignore:1:*`. PR2 accepted this rejection. |
| DRY1 note: `check_scoring_regression.py` is not cited | Not adopted. The writing run changes no scoring code, and the check reads campaign records outside the writing scope. The recorded runs are cited instead. |

## Adopted findings and where revision 3 carries them

### DRY1

| Finding | Revision 3 location |
|---|---|
| B1: `check_protected_sources.py` covers only its own ledger (verified: 0 IJSSOL entries) | F4; INV-2 |
| B2: MAX_PATH risk from copying campaigns into the scratchpad (verified: 163 + 135 characters) | F5; INV-4; §7 note |
| B3: `structure-review` has no usable residue | P8 step 1 |
| G1, C2: three option writers share one file | §4.5 DBR/OCL return-in-reply rule; P4 step 3 |
| G2, C3: OCL draft path and ownership | INV-9; §4.5 |
| G3: solver-free test classification | F6 (no tests are run) |
| G4: canon conflict batching | P5a Part 3 |
| C5: parallelism cap conflicts with the reviewed plan | §0 superseded table |

### RT1

| Finding | Revision 3 location |
|---|---|
| B1: drift wording | P1 claims table Drift row; Q-008, made decisive by RT2 |
| B2: incumbent headroom (verified: handoff 1028-1032) | claims row; Q-005; reader question |
| B3: upper-only versus two-sided reversal (verified: handoff 973-979) | F12; claims row; reader question |
| B4: over-qualification | INV-5 scope-once rule; §4.1 definition of "conservative"; blue-team seats |
| B5: AI declaration (verified: `IJSSOL_CSLAP_v1.tex:750-751`) | §3 |
| M1: replication vocabulary | Protocol row; INV-5 label rule |
| M2: seed ranges (verified exactly) | F11 |
| M3: minimum-slack mechanism (verified) | F10; Mechanism row; P5b and P6 displays |
| M4: non-comparability with the companion's savings | claims row; reader question |
| M5: why undated (verified: export header has no date column) | F9; Q-006 |
| M6: drafting order and provisional freezes | P7 order |
| M7: blueprint over-constraint | P5b |
| M8: prose must not be voted | §4.5 OCL; Appendix G |
| M9: loop budget | BCL-2; P8 rounds |
| M10: style conflicts (verified: list sites and §XIX-A G7) | P5a Part 3 |
| M11 and protocol improvements 1-9 | §4.3; P4 step 2 |
| Likely-missed gaps 1-10 | claims rows; INV-8; Q-007; §3 data availability; P5b reader questions |
| Minor items | F8; INV-3; INV-7; P5a; Appendix A; P6 study-design table |

### PR1

| Finding | Revision 3 location |
|---|---|
| 1: native tests (verified: `test_cplex.py:67` calls `solve`) | F6; P0 step 6 |
| 2: `make_analysis` aliases read the full export | F5; INV-4 |
| 3: check-script authorship | INV-13; check-author waves in every phase |
| 4: negative-control method | INV-11 |
| 5: manual gates self-certified | INV-11 `check_governance.py` rule table; §4.4 |
| 6: conservative ordering and runoff | §4.1; §4.3 |
| 7: novelty stop decided by a vote | §3 H6 |
| 8: ballot handling | §4.3 |
| 9: builder identity and read-only claim | §4.4 |
| 10: tool limits (verified: `results-integrity-reviewer.md:52`; researcher has no Write) | P1 step 2; P2 step 2 |
| 11: ownership | INV-9 |
| 12: `ck_ext` checks (verified: T0 `[H]` rule at `ck.py:230-232`) | F15; P7 |
| 13: requirements coverage | P1 step 4 |
| 14: macro and display coverage | P5b; P6:G4 |
| 15: precedence conflicts | §0 |
| 16: CRT priming and the §III path (verified: line 110) | Appendix A2; §4.5 |
| 17: gate exits | Appendix A; P5:G3; P8 |
| 18: resume protocol and budget | §6; INV-10; §8 |
| 19: dataviz and structure-review | P6; P8 |
| 20: citation eligibility | P2 step 4 |
| Nice-to-haves other than the rejected `.unlazy/` point | P0 step 5; Appendix A; INV-8; §4.2; INV-10; §4.3; P5b; P8 step 2; INV-12 |

### RT2

| Finding | Revision 3 location |
|---|---|
| B1 reopened: "despite substantial product-mix change" fails once the drift comparison is made fair (verified: `drift_survey.py:12-18` compares each block with a pooled history that contains it) | F16; Q-008 decisive test; Drift row forbidden wording |
| Margin-rule dispersion is from the exploratory prefix (verified: `dispersion_survey.csv` rows 89-91) | F17; Margin-rule row |
| Wrong JSON key names (verified: `validation.*_exact` fields) | F18; INV-3 |
| Upper-only "floor-breach counts" wording | P1 step 2 |
| "About 15 %" should be 13-16 % by arm | Non-comparability row; reader question |
| Governance weight: technical-term whitelist | P3 step 1; P5a Part 5 |
| Governance weight: batch the canon conflicts | P5a Part 3 |
| Governance weight: merge check scripts; `check_canon.py` becomes a PRES sign-off; companion measurement becomes a one-off | P1; P5a; §7 |
| Governance weight: scope of the numeral check | INV-3 |
| Governance weight: limit blueprint imports | P5b step 3 |
| Governance weight: compare with the reviewed plan's anchors at displayed precision | §4.2; P1 step 2 |
| New blocking: an anchor that cannot be computed | Margin-rule row |
| New blocking: Q-008 lacked a decisive test | Q-008 |
| New blocking: the "Replication endpoint" label (verified: predeclaration line 456) | F19; INV-5 label rule |
| Minor: qualifiers in abstract and conclusion | INV-5 |
| Minor: gap and bound moved to the supplement | claims row |
| Minor: replacement cap | §4.3 |
| Minor: display rounding | Appendix D |
| Minor: 412 versus 413 (verified: `analysis_audit.md:35`) | F20; Q-009 |

### PR2

| Finding | Revision 3 location |
|---|---|
| Open 3: check authorship in P5 and P1 | P1 step 1; P5b step 0; INV-13 |
| Open 5: `check_governance.py` rule table and identity checks | INV-11 |
| Open 6: decision-rule edge cases | §4.3 |
| Open 8: duplicate-ballot replacement limited to round 1 | §4.3 |
| Open 9: snapshot ordering and repository-wide writes | §4.4; INV-10 |
| Open 13: the reviews as a requirements source | this ledger; P0 step 3 |
| Open 15: superseded REVISE_* meanings and venue rules | §0 |
| Open 17: BCL-3 in P5b; failing automated check; H7 and H8 scope | P5b; P8; §3 |
| N1: guard scope, plan pinning, manifest scope | INV-2; P0 step 3; PLAN_ADDENDA |
| N2: document values | INV-3; P1 step 3 |
| N3: citing the companion and software | P2 step 3; Appendix D |
| N4: identity collision on the map | P1 step 4 |
| N5: canon panel size | P5a Part 3 |
| N6: blind pairs | §4.5 DBR |
| N7: P9 stripping claim comments | P9 export |
| N8: model families and probe | §0; P0:G5; H9 |
| N9: seat defaults | §4.4 |
| Nice-to-haves | §8 sum; §7 path note; resume protocol "if present"; INV-4 read-path scan; INV-13 scope; P1 sources; P7 tokens; P5b CRT brief; boundary rule |

### RT3 (sonnet retry; verified F10, F11, F16, F17, F18, F19, F20 and the new claims rows, finding no misstatement)

| Finding | Revision 4 location |
|---|---|
| P7 could be read as five reviewer agents drafting the sections (a misreading, but it shows the text was ambiguous) | INV-9; P7 "Order" (the integrator drafts everything; the listed agents only critique) |
| Repeating the full referee cycle unconditionally in P8 would reopen settled prose | P8 round table (round 2 re-runs steps 1-2 only if round-1 structural or referee gaps remain) |
| The savings range is an arm-level mean over seeds; single runs vary more widely | P1 step 2 (single-run range anchored); Savings row |
| Q-009 must show both counts | P1 step 6 errata |
| Minor: pointer for the upper-only "floor-breach counts" wording | P1 step 2, F12 reconciliation bullet (replaces that wording) |

### PR3

| Finding | Revision 4 location |
|---|---|
| **Blocking:** in P1, general-purpose/sonnet authored the document-values check, made one of the extractions it compares, and served as blue-team critic; the reseat rule had no fallback | P1 builder list; P1 step 3 pair changed to haiku + fable; §4.4 reseat rule and blue-team default reworded as specified; INV-11 rule (h) |
| 1. `dispersion_survey.py` has the same in-reference bias (verified: lines 11-13; like-for-like about 1.83 and 1.80 pp) | F17; Margin-rule row; P1 step 2 |
| 2. Break-even w\* ≈ 0.0028 (verified arithmetic) | F16; Q-008 decisive test |
| 3. Run the model probe before the check-author wave | P0 step 3 |
| 4. Snapshot timing | §4.4 read-only waves |
| 5. Targeted fix round in every phase | H8; §4.5 BCL |
| 6. P4:G1 criteria and argument-option format | P4:G1; Appendix D `argument_option_X.json`; P0 step 7 |
| 7. Scope of the anchor cross-check | P1 step 2 |
| 8. DBR termination for non-numeric pairs | §4.5 DBR |
| 9. positioning-reviewer tool limits | P2 step 4 |
| 10. Appendix A qualifier aligned with INV-5 | Appendix A |
| 11. Fallback when round-1 ballots tie | §4.3 decision rule |
| 12. T0-T16 classification named (verified against the `ck.py` docstring) | P7 |
| 13. Both narrative-reviewer identities must accept | P8 convergence |
| 14. Conflict 4 proposed in the batch rather than pre-settled | P5a Part 3 |
| 15. Pin every root-level .tex and .bib | H2; INV-2; P0 step 4 |
| 16. Figure text must survive the anonymisation scan | INV-8; P6 step 2 |
| 17. ORCH exempt from rule (c); a DR without a named panel is ADP-3 | INV-11; §4.3 |
| 18. Builders must not compute or display significance tests | INV-4; Appendix A; P5a; P6 |
| 19. P0 step 7 wording | P0 step 7 |
| Added by the orchestrator: family availability and credit exhaustion (RT3a failure) | F21; §4.4; H9; `state.json` families |
