BALLOT  Q-010/A-001  voter: results-integrity-reviewer/opus  round: 2  seat: plain  slice: S3
POSITION: b3
REBUTTALS:
- (c) "BLOCKING flaws F1, F2, F5 and F6." Partly wrong. F1, F2 and F3 are BLOCKING; F5 and F6 are MAJOR [W/governance/results/P0-006-code-review-checks.md:7,9,11,22,28]. The flaws are real, but they argue for delaying when the changes take effect, not for rejecting them. Plan:421 sets no order.
- (c) "Adopting before the code review is premature under INV-11." Rebut. R keeps the changes from taking effect until the re-review returns PASS. Rejecting instead leaves rule (g) skipping every gate that is not MET [W/tools/check_governance.py:351-352], so a missing gate could still pass P0:G4 [W/governance/questions/Q-010.md:7].
- (c) "The new record types depend on a working rule table." Conceded. R is the remedy.
- (a) "The items map one-to-one onto defects; fastest." Rebut. Item 2's test, "names only the files the decision covers" [W/governance/questions/Q-010-addenda-draft.md:22], is also satisfied by an output that names no file at all. For example, the check can exit 2 printing only `DETECTOR BROKEN` [tools/horizon_robustness/check_protected_sources.py:46-48]. Plan:408 forbids such empty passes, and S3 closes this one.
- S1 "ADP-5 widens the route with no stated reason." Partly conceded. Plan:248 names only ADP-3. But plan:187 sends claim wording to ADP-5, so under S1 a finding about claim wording on an ORCH-built register needs a separate ADP-3 or an independent confirmer. That makes the route narrower, not weaker, so I accept S1 as part of b3.
WHAT CHANGED MY MIND: R, read together with F1 [P0-006:7]. The unfixed checker accepts a MET gate whose exit_code is 1, so without R, P0:G4 could be recorded MET by the very code under review. I moved from S3 alone in round 1 to b3.
BLOCKING OBJECTION: none
CONFIDENCE: high

---

BALLOT  Q-010/A-002  voter: results-integrity-reviewer/opus  round: 2  seat: plain  slice: S3
POSITION: b2
REBUTTALS:
- (a) "The condition is copied from the user's own list" [W/governance/user_decisions.md:24-27]. The source is conceded; the test is rebutted. The user waived one stored output: two lines, hashed 62cf6a5b... [W/governance/gates/P0-G2.json:7,13]. The draft's "lists no modified or missing file other than those two" [Q-010-addenda-draft.md:48] also passes on an empty output or a crash. It also leaves out `check_inputs.py`, which U5 makes the protection from P0 on [user_decisions.md:26-27].
- H "U5 names only P0:G2, so carrying it to P9 is an expansion." Rebut. U5 is already run-wide, because:
  - it is headed "Consequences for the run" [user_decisions.md:15];
  - the IJPR exclusion has no end date [:19-23];
  - protection applies "From P0 on" [:26-27];
  - user decisions take precedence over every other document [:3; plan:20-21].

  H therefore restates authority that already exists. Its test ("lists only the IJPR files") also disagrees with O on an output of one line or none, so under (b3) the record would carry two tests that give different answers. The ledger lists only the two v4 IJPR files [.unlazy/horizon-cslap/preserved_sources.json:445,450], so O's exact two-line test loses nothing.
- (c) Rejecting sends P9 to H8 on a matter the user already decided [Q-010.md:7; plan:137].
WHAT CHANGED MY MIND: none. I would accept (b3) if it stated that O's test governs wherever H and O differ.
BLOCKING OBJECTION: none
CONFIDENCE: medium

---

BALLOT  Q-010/A-003  voter: results-integrity-reviewer/opus  round: 2  seat: plain  slice: S3
POSITION: b
REBUTTALS:
- (a) "The plan's P1 roster pairs results-integrity-reviewer/opus with general-purpose/opus" [plan:587-589]. Conceded. (b) keeps that identity-level reading and replaces only note 2.
- (a) "The family test applies only to reseats" [plan:241-245]. Conceded.
- (a) "Plan:288's family language is scoped to the independent-confirmer row." The scope is conceded, and it supports (b): that row is exactly what note 2 addresses, and the draft's "prefers" [Q-010-addenda-draft.md:63] weakens the row's "family different from the builder" [plan:288].
- (c)/(d) "Identity includes family, and panels mix at least two families." Plan:56 is conceded; the use of plan:250 is rebutted:
  - plan:250 sits in the panel paragraphs [plan:250,270-279];
  - plan:242 lists panel seats and BCL critics as separate categories;
  - step 8 is a BCL-2 critic set [plan:587];
  - the builder rule bars the same identity, not a shared family [plan:241].

  The second chair found the premise FALSE and confirmed that the critic set spans opus and sonnet [W/governance/results/P0-012-Q010-second-chair-general-purpose-sonnet.md:16-21,27].
- My own check against (b): plan:54 defines a family as an Agent override name, and ORCH is not dispatched with one. Rebut. If ORCH had no family, plan:288's family test would be empty for exactly the artifacts plan:248 singles out. The draft itself says ORCH runs on Opus 5 [Q-010-addenda-draft.md:63].
WHAT CHANGED MY MIND: none. The second-chair check confirms the reading I held in round 1.
DISCLOSURE: option (d) would reseat my own identity's critic seat [P0-011 ballot:50]. The rebuttals above rest on plan text and on the independent second chair.
BLOCKING OBJECTION: none
CONFIDENCE: medium

Paths:
- `W` = `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results\writing`
- `plan` = `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results\WRITING_ORCHESTRATION_PLAN_20260914.md`
- `P0-011 ballot` = `W\governance\results\P0-011-Q010-ballot-results-integrity-reviewer-opus.md`
