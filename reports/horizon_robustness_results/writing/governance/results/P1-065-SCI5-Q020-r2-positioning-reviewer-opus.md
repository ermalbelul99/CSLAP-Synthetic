BALLOT  Q-020  voter: positioning-reviewer/opus  round: 2  seat: blue  slice: S3

POSITION: d

REBUTTALS AND CONCESSIONS:
- **Argument 2, reason 1 (the cause is "anchored, not uncertain").** Rebut. Both facts also hold for arms that passed on every seed:
  - HIST+ACT-T and TIGHT used 0.009992 to 0.009999 of their allowance [W/evidence/claims.json:135].
  - HIST+ACT-T had 2, 4 and 4 stations below its modelled set and still passed 3 of 3 [W/evidence/anchors.json:133, 145, 157, 158].
- **Argument 2, reason 2 (the margin, not set departure, separates passing from failing arms).** I concede the pattern. It is my reason for rejecting (e). It is not a cause:
  - C-03 requires that the comparison "does not isolate the margin from solver and layout effects" [claims.json:101].
  - "margin decides the pass" and "attributes compliance to the reserved margin" are forbidden [claims.json:108, 110].
- **Argument 2, reason 3 (the pattern holds within each scenario group).** I concede that it holds the scenario design factor fixed. It does not hold layouts fixed: every solve has a gap of about 0.985 [WRITING_ORCHESTRATION_PLAN_20260914.md:73; claims.json:854]. The lesson for a site manager is already stated at full strength [claims.json:98].
  - For NOM, a genuine failure needs "the proposed method" [SKILL:586]. NOM's stated purpose is "Nominal CSLAP extension" [reports/horizon_robustness_plan/PLAN.md:266].
  - (d) keeps NOM scored and reported, so Argument 2's would-change-my-mind test does not bear on (d).
- **Argument 1, reason 3 and option (e) (NOM's miss as a demonstrated boundary condition).** Rebut. TIGHT has the same single-point set, all 24 stations lie off it, and it passed 3 of 3 [anchors.json:52-53, 64-65, 76-78]. C-21 requires "Leaving the modelled set is not a band violation" [claims.json:757]. The evidence does not show NOM's miss following from that assumption, which SKILL:570 requires.
- **Argument 4 steelman and the red-team critic's F4 (HIST+ACT misses consistently).** I concede the consistency: 0/3, 1/3 and 0/3 at the exploratory origin, never pooled, and 0/3 held out [anchors.json:211, 219, 234, 118]. Rebut on intent:
  - The original plan's H1 expected scenario protection to reduce "joint station-cap violations relative to NOM" [PLAN.md:277]. It was not predeclared for the held-out stage.
  - Held out, HIST+ACT had 1, 2 and 0 stations above the cap against NOM's 4, 4 and 2 [anchors.json:85, 97, 109, 5, 17, 29].
  - Its worst breach above the cap was at most 0.085 pp, against NOM's at least 0.939 (`ho.breach.*.cap_worst`, F-078).
  - This is descriptive, one origin and three seeds. It fits "performed poorly under a tested configuration" [SKILL:574], not "did not work as intended" [SKILL:586].
- **Arguments 3 and 4, reason 3 (for (a): keeping NOM in C-17 avoids looking like rhetorical rescue).** Rebut.
  - The predeclaration forbids removing an arm "to obtain a favourable table" [CAMPAIGN_PREDECLARATION.md:112-113]. (d) removes no arm from any table.
  - C-03 states NOM's 0/3 and its 0.939 to 1.144 pp breaches [claims.json:94, 102].
  - My wording below adds a pointer to C-03.
- **My own round 1 premise [claims.json:127] ("a magnitude per direction is not anchored").** Conceded: it is now stale, because F-078 added `ho.breach.<ARM>.<SEED>.cap_worst` and `.floor_worst`. The text at claims.json:127 still says otherwise and needs updating. My round 1 anchors.json line locators have also shifted; the current lines are cited here.

WHAT CHANGED MY MIND: Argument 5, reason 1 and its proposed option.
- SKILL:574 defines an empirical limitation as "The method performed poorly". My own round 1 reason 1 (NOM is the control, not the method) therefore rules NOM out of that category as much as out of genuine failure.
- Yet (a) keeps NOM there [claims.json:609, 612].
- The F-078 anchors add that the two arms' misses are not one kind of result: HIST+ACT's worst breach was at most 0.179 pp, NOM's at least 0.939 [claims.json:94].

REASONS:
1. **No §XII category fits NOM, so the correct report is the contrast.**
   - Both the genuine-failure and empirical-limitation definitions presuppose "the method" [SKILL:574, 586].
   - The boundary-condition category fails on TIGHT's record (rebuttal above).
   - NOM is the (0,0) reference cell of the margin main effect [CAMPAIGN_PREDECLARATION.md:422-423, 462-463].
   - The reviewed plan lists "neither no-margin arm passes" as a strength of the design [WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:66-69].
   - "Report the correct category" [SKILL:588] is therefore met by C-03 [claims.json:94-102].
2. **HIST+ACT is a protection variant that missed, for a reason that is not isolated.**
   - Its plan purpose was protection relative to NOM [PLAN.md:269, 277].
   - Its candidate explanations also hold for passing arms [claims.json:135; anchors.json:133-158].
   - C-17's qualifier asks for four of the five §XII answers and omits "Why might it happen?" [claims.json:617; SKILL:596]. (d) requires all five.
3. **Positioning (S3).**
   - NOM is the nominal extension of the companion's model. The companion's budget is a one-sided 110% cap [IJSSOL_CSLAP_v1.tex:584], on a different extract [CAMPAIGN_PREDECLARATION.md:433-435].
   - Listing NOM's miss among this paper's limitations invites a verdict on the companion that the design cannot deliver.
   - The plan's negative-result purpose, "scope and mechanism are examined" [WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:135-137], fits the scenario bundle, which is part of contribution 3 (lines 128-129). It does not fit the control.

STEELMAN: The best case for (a), my second choice, is that one Limitations item listing every held-out miss removes any appearance of pruning [SKILL:590; CAMPAIGN_PREDECLARATION.md:112]. It fails for three reasons:
- Disclosure is already complete in C-03 [claims.json:94, 98, 102].
- (a) assigns NOM a category whose definition presupposes a method [SKILL:574].
- (a) leaves "Why might it happen?" unanswered [claims.json:617].

BLUE WORDING: This replaces C-17's empirical-limitation item for the held-out misses; the other items stay unchanged.

"Empirical limitation: HIST+ACT, the scenario-and-activation arm without a reserved margin, satisfied the two-sided band on none of the three held-out seeds under the frozen policy. It breached below the floor on every seed and above the cap on two, with a worst breach of 0.069 to 0.179 percentage points; a small breach is still a miss of the declared policy. One possible explanation is that each returned layout used its whole training allowance while the future fell below its modelled set at three or four stations. That explanation is hypothetical: HIST+ACT-T also used its whole, tightened allowance and had two to four stations below its set, yet satisfied the band on every seed, and the comparison does not isolate the margin from solver and layout effects. Further held-out origins with a λ frontier, and layouts solved closer to proven optimality, would resolve it; neither is run for this paper. The misses of NOM, the unprotected (0,0) control, are not classified here and are reported with the factorial contrast (C-03)."

Locators for the wording:
- 0 of 3 seeds: anchors.json:118
- directions: claims.json:94
- worst breach: claims.json:97
- small breach is still a miss: claims.json:102
- whole allowance: claims.json:135
- stations below the set: anchors.json:93, 105, 117
- HIST+ACT-T record: anchors.json:133, 145, 157, 158
- not isolated: claims.json:101
- the experiment that would resolve it and "not run": claims.json:609, 617, as §XII answer 5 requires [SKILL:598]; this names an experiment, it does not demand one
- NOM as the control: CAMPAIGN_PREDECLARATION.md:422-423

BLOCKING OBJECTION: none

SECOND PREFERENCE: a

CONFIDENCE: medium
