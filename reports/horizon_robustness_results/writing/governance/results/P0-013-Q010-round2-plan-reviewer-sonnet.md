I read the brief, the plan sections it cites (lines 241–250, 288, 296–299, 402–421 and 495–589), `user_decisions.md` (U5 and U6), the P0:G2 gate record and its output file, `check_protected_sources.py`, the dispatch log, the P0-006 code review, and `Q-010-addenda-draft.md`, which holds the actual text of A-001, A-002 and A-003. I did this to check the round-1 claims before voting. Every locator below was confirmed against the source rather than taken from the brief.

```
BALLOT  Q-010/A-001  voter: plan-reviewer/sonnet  round: 2  seat: plain  slice: S1
POSITION: b3
REBUTTALS:
- For (a), "verbatim is fastest": item 6 as drafted literally permits ADP-5 (Q-010-addenda-draft.md:32), but plan:248 names only ADP-3 for the ORCH-built-artifact route. Choosing speed would bring back a confirmed scope error. [plan:248; addenda-draft.md:32]
- For (a), against S3, "amendments unneeded": item 2's drafted condition ("output names only the covered files") passes when the output has zero lines. `check_protected_sources.py:46-48` returns exit 2 with "DETECTOR BROKEN" and no MODIFIED line at all, which satisfies "names only" vacuously. That is a real empty pass, forbidden by plan:408. [check_protected_sources.py:46-48; plan:408]
- For (c), "code review found BLOCKING flaws (F1, F2, F5, F6), so adopting first is premature": conceded that F1, F2, F5 and F6 are real BLOCKING or MAJOR flaws in `check_governance.py` itself (P0-006-code-review-checks.md:7,9,22,28). That point stands. R closes exactly this gap. It makes the rule-table change take effect only after a passing code-reviewer re-review, so adopting the DR text now does not by itself change the checker (chair note), and P0:G4 cannot be recorded MET until the fix is verified. Rejecting and redoing (c) buys the same safety at higher cost and adds no protection.
WHAT CHANGED MY MIND: R is new this round and answers directly the INV-11 ordering question the chair flagged. I verified that plan:421 ("changes to the table require a DR and a new code-reviewer review") says nothing about order, so R's explicit gate supplies the missing piece rather than adding a new requirement.
RED CASE: n/a (plain seat)
BLOCKING OBJECTION: none
CONFIDENCE: high
```

```
BALLOT  Q-010/A-002  voter: plan-reviewer/sonnet  round: 2  seat: plain  slice: S1
POSITION: b3
REBUTTALS:
- For (a), "the condition is copied from the user's own consequences list, and rejecting brings H8": conceded that the text follows user_decisions.md:24-27. But the drafted test ("lists no modified/missing file other than those two") is vacuously true on a crash or on DETECTOR BROKEN output with zero lines (verified: `check_protected_sources.py:46-48`). O's three conditions (exit_code == 1, exactly two lines, and check_inputs.py MET) close that gap without changing the substance of U5. [check_protected_sources.py:46-48]
- Against H, "U5 names only P0:G2, so carrying it to P9 is an expansion": rebutted. U5 item 4 states "From P0 on, protection of every pinned file, IJPR files included, rests on `check_inputs.py`" (user_decisions.md:27). The forward scope is already in U5's own text; H makes an existing scope explicit and invents no authority.
- Against O condition (iii): no objection was raised beyond those answered above. I confirmed that P0-G2.json's stored output (`.unlazy/horizon-writing/gate_outputs/P0-G2.txt`) is exactly the two MODIFIED lines O requires, matching sha256 62cf6a5b… in the gate record. O's exact-match test is therefore no stricter than what was actually waived.
WHAT CHANGED MY MIND: b3 is new this round. I read U5's "From P0 on" line directly, and it independently supports H rather than merely being asserted. I also confirmed that O's empty-pass gap exists in the shipped script. Combining both amendments closes two separate real gaps, not one.
RED CASE: n/a (plain seat)
BLOCKING OBJECTION: none
CONFIDENCE: high
```

```
BALLOT  Q-010/A-003  voter: plan-reviewer/sonnet  round: 2  seat: plain  slice: S1
POSITION: b
REBUTTALS:
- For (c)/(d), "identity includes family (plan:56) and panels mix at least two families (plan:250), so two opus seats (general-purpose/opus builder plus results-integrity-reviewer/opus critic) violate the plan": rebutted.
  - Plan:250 sits in the "Panels" table (SCI-5, NOV-5, MATH-3, PRES-3, PRES-5, REF-3; plan:270-279). That is a different governed category from the P1 BCL-2 critic set (plan:587-589).
  - Plan:241 forbids an agent of the same identity (agent type plus family, plan:56) from reviewing its own artifact; it does not forbid the same family. results-integrity-reviewer/opus and general-purpose/opus are different agent types, hence different identities.
  - This matches the second chair's independently checked FALSE verdict (governance/results/P0-012…, cited in the chair notes). I cross-checked it against the plan text myself rather than taking it on trust.
- Against adopting as drafted, in favour of (b)/O: note 2 currently reads "ORCH prefers non-opus independent confirmers" (Q-010-addenda-draft.md:63). That softens what plan:288's default-seat table states as a requirement ("family different from the builder"). It matters because ORCH itself builds `document_values.json` (plan:526), an ORCH-built artifact that falls under plan:247-248's independent-confirmer route. With sonnet and haiku both available, "prefers" is an unforced weakening, not a necessary hedge.
WHAT CHANGED MY MIND: the second chair's check, new this round, is the first grounded rebuttal of the plan:250 premise. I verified its three supporting locators (plan:242, plan:56, plan:241) myself, and they hold. That rules out (c) and (d), leaving note 2's wording as the only live defect, which (b) fixes.
RED CASE: n/a (plain seat)
BLOCKING OBJECTION: none
CONFIDENCE: high
```

Files consulted (read-only):
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (lines 46–56, 230–300, 400–425, 495–598)
- `reports/horizon_robustness_results/writing/governance/user_decisions.md`
- `reports/horizon_robustness_results/writing/governance/gates/P0-G2.json`
- `.unlazy/horizon-writing/gate_outputs/P0-G2.txt`
- `tools/horizon_robustness/check_protected_sources.py`
- `reports/horizon_robustness_results/writing/governance/dispatch_log.jsonl`
- `reports/horizon_robustness_results/writing/governance/results/P0-006-code-review-checks.md`
- `reports/horizon_robustness_results/writing/governance/questions/Q-010-addenda-draft.md`
- `reports/horizon_robustness_results/writing/governance/PLAN_ADDENDA.md`
