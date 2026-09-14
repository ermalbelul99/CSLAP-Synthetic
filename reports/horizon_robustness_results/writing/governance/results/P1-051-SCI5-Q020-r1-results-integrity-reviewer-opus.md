BALLOT  Q-020  voter: results-integrity-reviewer/opus  round: 1  seat: plain  slice: S1

POSITION: a

REASONS:
1. The miss is anchored, but its cause is not. "Genuine failure" says the method "did not work as intended" (`.claude/skills/reviewer_first_skill/SKILL_Academic_Manuscript_Architect_and_Critical_Reviewer.md:584-586`). "Empirical limitation" is for poor performance when "the mechanism is uncertain" (same file, :572-574). The two anchored facts offered as the cause of the misses also hold for the arms that passed:
   - **Allowance used.** All four arms used almost their whole training allowance. HIST+ACT needed 0.019997 to 0.019999 of 0.02, which is at least 99.98% (`ho.min_slack.HIST_ACT.s11/s22/s33`). TIGHT and HIST+ACT-T needed 0.009992 to 0.009999 of 0.01, which is at least 99.92% (`ho.min_slack.TIGHT.*`, `ho.min_slack.HIST_ACT_T.*`).
   - **Departures below the modelled set.** HIST+ACT had 3, 4 and 4 stations below its set (`ho.departures.HIST_ACT.*.below`). HIST+ACT-T had 2, 4 and 4 and passed on every seed (`ho.departures.HIST_ACT_T.*.below`). Counting both directions, HIST+ACT-T seed 22 has 4 + 1 = 5 departures and passed, while HIST+ACT seed 11 has 3 + 1 = 4 and failed.
   - **Solver gap.** The gap does not separate them either. All 12 held-out rows lie between 0.98452 and 0.98540 (`tables/case_frame.csv`, campaign ho3_20260913, column `gap`).
   - **What remains.** Only the margin factor separates the passing arms from the failing ones. C-03's qualifier says the comparison "does not isolate the margin from solver and layout effects" (`W/evidence/claims.json:101`). So the mechanism is uncertain, and §XII puts that under empirical limitation.

2. Option (b) names NOM, but NOM is the design's control cell, not a proposed method. The predeclared 2×2 defines NOM as (0,0), with no scenarios and no margin (`CAMPAIGN_PREDECLARATION.md:417-423`). The question the design asks is whether reserving the margin "explain[s] compliance" (:412-413). The only pass criterion was set for TIGHT (:456-458). The rest of the factorial reading is "secondary, descriptive" (:459). No held-out compliance intent was declared for NOM or HIST+ACT, so "did not work as intended" has nothing to measure against. Even the critic who argues for (b) concedes that "NOM is the unprotected control, not a method" (`W/governance/results/P1-043-critic-results-integrity.md:39`). The card's (b) still covers NOM (`W/governance/questions/Q-020.md:6`).

3. Option (a) does not soften the negative result, and (b)'s label claims a cause the register does not support.
   - **The miss is already stated in full.** C-03 states 0 of 3 against 3 of 3 and requires "a small breach is still a miss of the declared policy" (`claims.json:96,102`). C-17 requires "Negative and mixed results are reported as found" (`claims.json:618`). This meets the predeclared reporting commitment (`CAMPAIGN_PREDECLARATION.md:112`), so §XII's warning against "rhetorical rescue" (:590) is respected.
   - **"No-margin design" points to a cause.** A "failure of that arm's no-margin design" names the absent margin as the design fault. That comes close to the forbidden wordings "margin decides the pass" and "attributes compliance to the reserved margin" (`claims.json:105-110`).
   - **What (a) lets the paper say.** Under (a), whole-allowance use, departure from the set and the absent margin can each be reported as a hypothetical explanation, as §XII asks (:596-597).

STEELMAN: The strongest case for (b) concerns HIST+ACT, the scenario arm, and does not need NOM.
- **The pattern.** HIST+ACT never met the band on a held-out seed (`ho.pass.HIST_ACT.count` = 0). At the exploratory origin it passed 0, 1 and 0 of 3 horizons across the three δ campaigns, never pooled (`ts.berner.d01/d02/d03.pass.HIST_ACT.count`). Over the same campaigns TIGHT passed 3 of 3 at δ = 0.02 and δ = 0.03 (`ts.berner.d02/d03.pass.TIGHT.count`).
- **The referee's reading.** A referee could say a design that misses this consistently did not work, and that "empirical limitation" understates it.
- **Why it fails.** Consistency shows that the miss is real, and C-03 already reports it at full strength. It does not show that the design is at fault rather than the uncertainty set, which the future demonstrably left (C-21; `ho.departures.HIST_ACT.*`), or time-capped layouts (gap about 0.985).
- **The C-23 point.** C-23 limits the design's guarantee to futures inside the set (`claims.json:818`). "Did not work as intended" therefore claims more than the arm was built to deliver.

The red-team case for (b) rested on two premises the chair has corrected: that breach was "mechanically certain", and that "primary, data-supported" described an arm (chair notes; `CAMPAIGN_PREDECLARATION.md:363`).

The blue-team alternative of folding the misses into the boundary condition also fails, in the other direction. Its "three to six times" premise does not match the anchors (TIGHT 12 to 13 below, NOM 13 below). C-17 as written rightly keeps the misses out of that category (`claims.json:609,612`).

On the confirmer's rewording (`P1-048-confirm-Q020-ordering.md:15`): the card already carries it, and neither wording changes my vote. The reworded text still covers NOM, and "no-margin design" makes the causal implication in reason 3 sharper.

BLOCKING OBJECTION: none

PROPOSED MISSING OPTION: (b′) classify only HIST+ACT's held-out misses as a genuine failure of that arm, and keep NOM as the unprotected (0,0) control reported under empirical limitation. This is the strongest form of the opposing view (`P1-043-critic-results-integrity.md:33-39`), and the card does not offer it. I would vote (a) against it for reasons 1 and 3.

CONFIDENCE: medium

WOULD CHANGE MY MIND: Any of the following, without new solves.
- **A separating quantity.** An anchored quantity that separates all six failing held-out layouts from all six passing ones, other than the margin factor itself, and that is not open to C-03's solver and layout confound.
- **A declared intent.** A predeclared statement, in `CAMPAIGN_PREDECLARATION.md` §8 or §9 or in the reviewed plan, that HIST+ACT at ±δ without a margin was expected to hold the band on the held-out window, which would make "did not work as intended" testable.

For NOM alone, nothing in S1 would move me: its role as the (0,0) control is fixed by the design.
