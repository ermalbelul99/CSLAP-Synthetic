## Conservative Ordering

**Confirmed, with one amendment.** For A-001 the order should be (c) < (b) < (a), not (b) or (a). The code review (P0-006) marks `check_governance.py` REVISE, with BLOCKING findings in INV-11 rules (e), (f) and (h) themselves. F1, F2, F5 and F6 are architectural flaws: exit-code validation, seat counting, registry enforcement and record keying all fail. Adopting governance extensions before the structural code fixes are verified would be governance theater. The conservative sequence is: reject, fix the code, re-review, then adopt the extensions. A-002 (a), A-003 (a) and A-004 (a) are unchanged. [P0-006:1-8, 60-86]

---

## BALLOT Q-010/A-001

**BALLOT** Q-010/A-001 **voter:** general-purpose/haiku **seat:** red **slice:** S2
**POSITION:** c
**REASONS:**
1. The code review finds four BLOCKING failures in the enforcement logic itself [P0-006:7-8, 22-27, 28]:
   - F1, rule (e): a gate can be MET without exit 0 or the token.
   - F2: replaced seats count toward panel size.
   - F5, rule (h): only the latest event is scanned, and an absent registry passes.
   - F6: gates are keyed by id rather than filename, so duplicate gates drop records.
2. A-001 proposes new record types that depend on INV-11 working correctly: a required-gate registry, verdict records, RTP records, and decisions as verifiers. The table is not working. [A-001:1-40, P0-006:1]
3. The required fixes (§62-86) are substantial. F1 needs new validation logic, F2 needs the seat count reworked, F5 needs registry and dispatch-log matching, and F6 needs file-name keying. These must be coded, tested through fixtures, and verified by a round-2 code review before any governance extension is deployed.

**STEELMAN:** (a) relies on plan-reviewer re-validating the extensions at P0:G4, but plan-reviewer is not a code reviewer. (b) adopts with an amendment requiring the code fixes and trusts that A-001 items 1–8 will work, yet the rule table that governs them is marked REVISE.

**RED CASE:** A-001 treats the code-review findings as cosmetic gaps that can be handled in parallel with adoption. F1, F2, F5 and F6 are architectural flaws: the rule table that enforces INV-11 across the whole run is broken. Adopting extensions to a broken table before the fixes are verified is false incrementalism. The conservative course is to reject, fix the code first, then re-propose the extensions with a passing code review.

**BLOCKING OBJECTION:** INV-11 (plan:421) requires rule-table changes to have "a DR and a new code-reviewer review". A-001 proposes such changes, and P0 has not completed a second code-reviewer round. [plan:409, 421]

**CONFIDENCE:** high

**WOULD CHANGE MY MIND:** a code-reviewer round 2 marked ACCEPTED, showing all F1–F6 fixes implemented and tested.

---

## BALLOT Q-010/A-002

**BALLOT** Q-010/A-002 **voter:** general-purpose/haiku **seat:** red **slice:** S2
**POSITION:** b
**AMENDMENT:** "U5 establishes the baseline files (IJSSOL only) as sovereign authority across the entire run, per plan §0 precedence. The P9 step 1 re-run applies that authority: protected-source records are UNMET with waiver U5 if the output lists only IJPR files; any other file triggers H7."
**REASONS:**
1. U5 decides the P0:G2 baseline but does not name P9. A-002 says it "carries forward", but extending a P0 waiver to P9 is an expansion, not merely a restatement. [user_decisions.md:6-27, A-002:42-50]
2. The amendment clarifies U5's scope: under plan §0 precedence it applies to all phases, so any check that examines baseline files uses IJSSOL as the only baseline. This removes any doubt about whether the waiver reaches P9 or stops at P0.
3. The condition "no other file modified" maps correctly to H7 when violated, so the gate stays honest.

**RED CASE:** "Carries forward" conflates a user decision, which is global and covers all phases, with one gate waiver, the P0:G2 record. As drafted, A-002 leaves open whether U5's authority is global or limited to P0. If U5 is global, as it should be under a precedence rule, the addendum should say so. If U5 applies only to P0, P9 needs its own decision, grounded in U5 but separate.

**CONFIDENCE:** medium

**WOULD CHANGE MY MIND:** an explicit statement in A-002 that U5's baseline authority applies to all phases, or a clear restriction to P0 with a proposal for a separate P9 decision.

---

## BALLOT Q-010/A-003

**BALLOT** Q-010/A-003 **voter:** general-purpose/haiku **seat:** red **slice:** S2
**POSITION:** c
**REASONS:**
1. Plan §4.4 line 56 defines identity as "agent type plus model family". Lines 241–245 forbid "a builder from reviewing its own artifact", which covers all panel seats. Line 250 requires "panels mix at least two families". These rules are stated without conditions. [plan:56, 241-245, 250]
2. The P1 default panel pairs a general-purpose/opus builder with a results-integrity-reviewer/opus critic, both in the opus family. Under the plan's own rules, two opus seats violate the "at least two families" requirement. [plan:274]
3. A-003 carves out an exception for "planned seats", claiming that family diversity applies only to reseats and independent confirmers. The plan does not distinguish kinds of seat, so this reads as an amendment, not a clarification. [A-003:52-64]

**STEELMAN:** (a) is defensible if the "family-level test" is read as narrower than the "two families" rule. The plan does not use that language, though: it says identity includes family and panels mix families.

**RED CASE:** The plan states that identity is agent type plus family and that panels mix at least two families, so two opus seats are a family violation. A-003 tries to exempt planned seats after the fact, but the reseat rule (§4.4, lines 241–245) already covers such collisions. Apply it: find an agent type from a non-opus family (for example formulation-reviewer/sonnet) to review the general-purpose/opus artifacts.

**BLOCKING OBJECTION:** The identity rule (plan §4.4, line 56) and the diversity rule (line 250) contain no exception for "planned seats". Applying an exception that is not in the text is an amendment, not a clarification. [plan:56, 250]

**PROPOSED MISSING OPTION:** (d) Reseat the P1 critic under the §4.4 reseat rule to a different agent type from a non-opus family.

**CONFIDENCE:** high

**WOULD CHANGE MY MIND:** explicit plan text exempting planned seats from family diversity, or plan-reviewer acceptance of the exception.

---

## BALLOT Q-010/A-004

**BALLOT** Q-010/A-004 **voter:** general-purpose/haiku **seat:** red **slice:** S2
**POSITION:** a
**REASONS:**
1. Plan §6 P0 (lines 443–481) lists gates G1–G5 but names no gates for P0 steps 3 (model probe) and 6 (citation of existing checks), although the plan requires both steps. P0:G6 fills that gap. [A-004:69, plan:443-481]
2. Separate records per automated script (ck_ext, check_manuscript_claims, check_numbers, overlap_scan and so on) make the audit honest: they show which script passed and which failed. [A-004:71-72]
3. The gate-file corrections align the gate definitions with the plan's intent: two tokens for P0:G3, the OWNS fixture lines for P6/P7, and EDIT INVARIANTS for P8. Briefs carry the user_decisions.md pointer so that U5 and U6 apply in every phase. [A-004:73-77]

**STEELMAN:** (c) rejects the addendum as feature creep: A-004 is an enhancement rather than a correction, separate records inflate the gate count without adding constraints, and the pointer in briefs is an operational improvement rather than a plan change.

**RED CASE:** A-004 is presented as "corrections", yet it adds a new gate (P0:G6) and changes the gate-recording policy from per suite to per script. These are plan enhancements, not missing pieces. The plan already covers P0 steps 3 and 6; it simply does not name gates for them. The conservative course is to keep the gates as written (G1–G5) and let operational practice handle environment documentation and per-script honesty.

**CONFIDENCE:** medium

**WOULD CHANGE MY MIND:** evidence that per-script gate records are needed for honesty (for example, a recent script failure that per-script records would have caught and per-suite records did not), or plan-reviewer acceptance of A-004 as written.

---

**Summary:** Ballots are c, b, c and a, under 1,200 words, each with a RED CASE against the conservative or amended leading option. All locators are included.
