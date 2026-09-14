BALLOT  Q-020  voter: positioning-reviewer/opus  round: 1  seat: blue  slice: S3

POSITION: a

REASONS:
1. **(b) applies "genuine failure" to arms that are not the method under test.** The skill defines a genuine failure as "The proposed method did not work as intended" [.claude/skills/reviewer_first_skill/SKILL_Academic_Manuscript_Architect_and_Critical_Reviewer.md:584-586].
   - At the held-out origin the frozen policy sets λ = 0.5 [reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md:440].
   - The predeclared primary endpoint concerns TIGHT [CAMPAIGN_PREDECLARATION.md:456-458; claims.json C-02, line 54].
   - NOM (0,0) and HIST+ACT (1,0) are the no-margin levels of a factorial built to ask "does explicitly reserving the margin explain compliance" [CAMPAIGN_PREDECLARATION.md:412-413, 417-423]. When the arms without a factor miss, that miss is the contrast the design measures. It is not the proposed method failing.
   - Even the critic who argues for (b) concedes "NOM is the unprotected control, not a method" [W/governance/results/P1-043-critic-results-integrity.md:39]. Yet (b), in both its card wording and the confirmer's rewording, still names NOM.
2. **The mechanism is uncertain, which is what "empirical limitation" requires** [SKILL:572-574].
   - The two facts offered as the anchored cause also hold for arms that passed. HIST+ACT-T and TIGHT also used essentially their whole tightened allowance, 0.009992 to 0.009999 [claims.json:135].
   - HIST+ACT-T had 2 to 4 stations below its modelled set [W/evidence/anchors.json:113, 123, 133].
   - TIGHT had 12 or 13 stations below and 11 or 12 above its modelled set [anchors.json:44-45, 54-55, 64-65], and still passed 3 of 3 seeds [anchors.json:66].
   - What separates passing from failing arms is the margin. C-03 requires the qualifier that the comparison "does not isolate the margin from solver and layout effects" [claims.json:101], and C-24 repeats it [claims.json:854].
   - A breach magnitude per direction is not anchored [claims.json:127].
   - Calling the misses a failure "of that arm's no-margin design" names the missing margin as the cause. That is the reverse of the forbidden "attributes compliance to the reserved margin" and "margin decides the pass" [claims.json:108, 110].
3. **Positioning against the companion (slice S3).**
   - The companion's abstract says that on held-out weeks "every station remaining inside its workload budget" [IJSSOL_CSLAP_v1.tex:66]. That budget is an upper limit of 110% of legacy load [IJSSOL_CSLAP_v1.tex:584], "the tolerance the site operates to" [IJSSOL_CSLAP_v1_supplementary.tex:533]. The companion already scopes its stability: it "may not carry to more volatile assortments" [IJSSOL_CSLAP_v1.tex:640].
   - The companion used a different extract [CAMPAIGN_PREDECLARATION.md:433-435].
   - If the unprotected nominal level is labelled a "genuine failure", a referee reading both papers can take it as a verdict on the companion's model. This evidence was never designed to deliver that verdict.
   - The reviewed plan places the negative results as "scope and mechanism are examined" and lists the contributions as the margin result and the diagnosis of a misspecified uncertainty set [WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:128-131, 135-137]. A no-margin method is not among them.

STEELMAN:
- **For (b):** both arms missed on 0 of 3 seeds [anchors.json:32, 100] and breached in both directions [claims.json:94]. The predeclaration commits that "A negative or mixed result is reported as such" [CAMPAIGN_PREDECLARATION.md:112]. The skill warns against turning negatives into boundary conditions and prefers maturity to "rhetorical rescue" [SKILL:562, 590].
- **Why it fails:**
  - Option (a) rescues nothing. C-17 does not call these misses a boundary condition; it lists them as negative results [claims.json:609, 612]. C-03 already requires "a small breach is still a miss of the declared policy" [claims.json:102].
  - The reporting commitment governs whether results are disclosed, not which category they belong to. The category "genuine failure" needs a proposed method that did not work as intended, and at this origin neither arm is that method.
  - I also reject the blue-team critic's route of treating the misses as a boundary condition [P1-045-critic-blueteam.md:10]. The chair's table shows set departure does not explain the misses: TIGHT departed as often as NOM and passed. C-21 also requires the qualifier "Leaving the modelled set is not a band violation" [claims.json:757].
- **Confirmer's rewording:** "each arm ... that arm's no-margin design" fixes the singular-policy ambiguity [P1-048-confirm-Q020-ordering.md:15]. It does not change my position, because it still labels the control level NOM a failure and still attributes the misses to the missing margin.

BLUE WORDING: "Empirical limitation: neither arm without a reserved margin, NOM or HIST+ACT, satisfied the two-sided band on any of the three held-out seeds, and both breached it in both directions. A small breach is still a miss of the declared policy. The layouts that passed had also used their whole training allowance and also had stations outside their modelled set, so what produced these misses is not isolated from solver and layout effects. Both arms are the no-margin levels of the predeclared factorial, whose primary endpoint concerned TIGHT, and their misses are reported as found."

Locators for the wording:
- "neither ... satisfied": anchors.json:32, 100
- both directions: claims.json:94
- small breach is still a miss: claims.json:102
- whole allowance used: claims.json:135
- stations outside the modelled set: anchors.json:44-65, 113-133
- not isolated: claims.json:101
- factorial levels and primary endpoint: CAMPAIGN_PREDECLARATION.md:417-423, 456-458
- reported as found: claims.json:618

BLOCKING OBJECTION: none

PROPOSED MISSING OPTION: (c) Classify only HIST+ACT's held-out misses as a genuine failure of scenario-and-activation protection without a reserved margin. NOM's misses stay in the empirical limitation as the contrast from the unprotected control. This separates the case the critic for (b) actually makes [P1-043-critic-results-integrity.md:33-39] from the NOM case, which that critic concedes. I would still rank (a) above (c), for reason 2.

CONFIDENCE: medium

WOULD CHANGE MY MIND: I would move to (c) for HIST+ACT if either of these is shown:
- a predeclaration or contribution text that presents HIST+ACT without a margin as a proposed protection method expected to satisfy the two-sided band out of sample, rather than as a factorial level;
- a verified exploratory-stage record that names HIST+ACT without a margin as the recommended policy before its misses were scored.

For NOM, nothing in the anchored evidence would move me, because it is the unprotected control by design [CAMPAIGN_PREDECLARATION.md:419-422].
