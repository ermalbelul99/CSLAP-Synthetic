BALLOT  Q-010/A-001  voter: results-integrity-reviewer/opus  round: 1  seat: plain  slice: S3
POSITION: b
AMENDMENT (if b):
- Item 2, third bullet, replace with: "the `condition` field is present and holds. A missing or empty `condition` makes the waiver invalid. For protected-source waivers the condition holds only if `exit_code` is 1 and the stored output consists of exactly one `MODIFIED protected file: <f>` line for each file the decision covers, and no other line. The P0:G2 record receives this `condition` before P0:G4 runs."
- Item 10, append: "A correction event is matched on (`seq`, `event`). Every `completed` event carries `self_reported_model` as a string or as the literal `\"not reported\"`."

REASONS:
1. The P0:G2 waiver carries only by, decision, file, ts and text; it has no `condition` [W/governance/gates/P0-G2.json:14-20]. `check_governance.py` has no waiver handling: a grep for "waiver|waive|condition" in W/tools/check_governance.py returns nothing. As drafted, the checker could treat a missing condition as satisfied.
2. The drafted test, "the gate output names only the files the decision covers" [W/governance/questions/Q-010-addenda-draft.md:22], is also true of an output that names no file at all. The script can exit 2 printing only `DETECTOR BROKEN` [tools/horizon_robustness/check_protected_sources.py:46-48]. That would be an empty pass, which the plan forbids [WRITING_ORCHESTRATION_PLAN_20260914.md:408].
3. The log already holds two events per seq: seq 6 was dispatched at W/governance/dispatch_log.jsonl:11 and completed at :14. A correction keyed on seq alone is therefore ambiguous. The completed events for seq 5–8 have `self_reported_model: null` [dispatch_log.jsonl:10,14,15,16], although INV-10 requires that field [plan:395-397].

STEELMAN:
- (a) The draft already fixes the known rule gaps, and the details could be left to the required code review. This fails because code review checks the code against the rule text [plan:421], so a rule that can pass vacuously would be implemented faithfully.
- (c) The addendum grows the rule table. This fails because rule (g) skips gates that are not MET [W/tools/check_governance.py:351-352], so without the registry a missing gate can pass P0:G4 [W/governance/questions/Q-010.md:7].

BLOCKING OBJECTION: none
PROPOSED MISSING OPTION: none
CONFIDENCE: high
WOULD CHANGE MY MIND: a registry format under item 1 that already fixes the exact output lines per gate, or a `log_dispatch.py` that already matches corrections on (`seq`, `event`).

---

BALLOT  Q-010/A-002  voter: results-integrity-reviewer/opus  round: 1  seat: plain  slice: S3
POSITION: b
AMENDMENT (if b): Replace the second paragraph with: "Under U5, the P9 record of that re-run is `UNMET` with waiver U5. The waiver is valid if and only if (i) `exit_code` is 1; (ii) the output consists of exactly the lines `MODIFIED protected file: IJPR_CSLAP_v4.tex` and `MODIFIED protected file: IJPR_CSLAP_v4_supplementary.tex`, in either order, and no other line; and (iii) the `check_inputs.py` record from the same P9 run is `MET`. Any other `MODIFIED` or `MISSING` line, or a failure of `check_inputs.py`, triggers H7. Any other output leaves the record `UNMET` with no waiver, and H8 applies."

REASONS:
1. The drafted test, "lists no modified or missing file other than those two" [Q-010-addenda-draft.md:48], also passes when no file is listed. That happens on `DETECTOR BROKEN` (exit 2) [check_protected_sources.py:46-48] or on a crash before line 49.
2. The prior-study ledger reports both IJPR files as modified whatever their current content, so a new edit made after P0 would still satisfy the waiver. Under U5, protection of every pinned file rests on `check_inputs.py` from P0 onwards [W/governance/user_decisions.md:26-27], and both files are pinned [W/governance/source_manifest.json:22649,22656]. Condition (iii) therefore carries out U5; it does not override it.
3. The P0 output the user waived is exactly those two lines [.unlazy/horizon-writing/gate_outputs/P0-G2.txt:1-2]. I recomputed its sha256 with `sha256sum` (62cf6a5b...), which matches P0-G2.json:7. The amendment carries forward exactly that and nothing more. H7 and H8 remain hard stops [plan:136-137].

STEELMAN:
- (a) The draft is shorter, and P9 runs `check_inputs` anyway [Q-010-addenda-draft.md:72]. This fails because A-001 item 2 judges each waiver on its own terms [Q-010-addenda-draft.md:19-22], so this waiver would stay valid even when the gate that closes the gap had failed.
- (c) U5 names only P0:G2 [user_decisions.md:24]. This fails because U5's ruling that the IJPR files are not a baseline does not expire. Rejecting A-002 would stop P9 under H8 over a matter the user has already decided [Q-010.md:7].

BLOCKING OBJECTION: none
PROPOSED MISSING OPTION: none
CONFIDENCE: medium (the conservative default is (a) [prompts/P0-Q010-ballot-results-integrity-reviewer-opus.md:68])
WOULD CHANGE MY MIND: a registry rule that makes a MET `check_inputs.py` record a precondition of every waiver.

---

BALLOT  Q-010/A-003  voter: results-integrity-reviewer/opus  round: 1  seat: plain  slice: S3
POSITION: b
AMENDMENT (if b): Replace note 2 with: "2. ORCH runs on Opus 5 and counts as family opus for the purposes of §4.4. An independent confirmer or fix confirmer of an artifact ORCH built must come from an available non-opus family, per the default-seat table ('family different from the builder'). If no non-opus family is available for the needed agent type, the finding goes to ADP-3."

REASONS:
1. Identity is agent type plus family [plan:56]. The plan's own P1 roster pairs a general-purpose/opus register builder with a results-integrity-reviewer/opus critic [plan:484,587-588], so the identity-level reading follows the plan text. Note 1 is also correct: the red seat was reseated to scientific-reviewer/sonnet [W/governance/reseat_log.md:15], and the blue seat is general-purpose/sonnet [plan:588-589].
2. Note 2 says only that ORCH "prefers" non-opus confirmers [Q-010-addenda-draft.md:63], whereas the default-seat table requires a confirmer family different from the builder [plan:288]. ORCH is Opus 5 [Q-010-addenda-draft.md:63], and both sonnet and haiku are available [W/governance/state.json:26-35]. "Prefers" turns a requirement into a preference.
3. Disclosure: my own identity holds the critic seat that this addendum confirms [dispatch_log.jsonl:19]. Reasons 1 and 2 rest on plan text alone, not on that interest.

STEELMAN:
- (a) The draft keeps the roster, and "prefers" gives ORCH room when there is a collision. This fails because the reseat rule already handles collisions [plan:243-245], so making note 2 mandatory costs nothing.
- (c) After the reseat, opus builds document-value extraction B [reseat_log.md:13], so an opus critic shares a family with one builder. This fails because §4.4 excludes builders by identity, not by family [plan:241], and two sonnet seats review the same artifacts.

BLOCKING OBJECTION: none
PROPOSED MISSING OPTION: none
CONFIDENCE: medium
WOULD CHANGE MY MIND: a plan locator stating that ORCH has no model family for the purposes of §4.4.

---

BALLOT  Q-010/A-004  voter: results-integrity-reviewer/opus  round: 1  seat: plain  slice: S3
POSITION: a

REASONS:
1. The two-token fix for P0:G3 is accurate and does not change the gate's result. The stored output contains both `CAMPAIGN ACCOUNTING VERIFIED (10 campaign(s))` and `AUTHORIZATION VERIFIED (10 campaign(s))` [.unlazy/horizon-writing/gate_outputs/P0-G3.txt]; its sha256 (bf038e2e...) matches P0-G3.json:7. The record currently expects only one of the two tokens [P0-G3.json:4].
2. The per-script suites match the plan: the P8 suite [plan:1001-1002], the P9 additions and export check [plan:1024-1028], and the `EDIT INVARIANTS PASSED` token [plan:997].
3. The P0:G6 deliverables exist and cover the plan's steps:
   - environment.md covers step 3 (families, self-reported models, interpreters, packages, the absence of TeX and Node, and D3) [W/governance/environment.md:9-36].
   - verification_inventory.md covers step 6, separating checks re-run in this run from checks that are only cited [W/evidence/verification_inventory.md:5-23].
   - Every stored P0 output hashes to its recorded value (G1 9853ee3d, G2 62cf6a5b, G3 bf038e2e, G5 2930435a; `sha256sum`).

STEELMAN:
- (b) The card still describes the two files as missing [Q-010.md:8], which is now out of date. This fails because the G6 text states what must exist, not that anything is missing [Q-010-addenda-draft.md:69].
- (c) Splitting the P8 and P9 suites into per-script records adds more ways to trigger H8. This fails because H8 already applies to each required runnable gate [plan:137]; separate records only show which script failed and add no new checks.

BLOCKING OBJECTION: none
PROPOSED MISSING OPTION: none
CONFIDENCE: high
WOULD CHANGE MY MIND: a stored gate output that lacks a token the corrections now expect, or a script in A-004's lists that plan §6 does not name.

Paths: `W` = `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results\writing`; `plan` = `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results\WRITING_ORCHESTRATION_PLAN_20260914.md`.
