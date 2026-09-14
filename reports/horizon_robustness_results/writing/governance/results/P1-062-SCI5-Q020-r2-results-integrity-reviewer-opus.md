BALLOT  Q-020  voter: results-integrity-reviewer/opus  round: 2  seat: plain  slice: S1

POSITION: d

REBUTTALS AND CONCESSIONS:
- **Argument 2, reason 1** (the cause is anchored, so the misses are a genuine failure). Rebut. The premise is false. Both facts it cites also hold for arms that passed: `ho.min_slack.TIGHT.s11` 0.009992 and `ho.min_slack.HIST_ACT_T.s22` 0.009998 (both whole allowance), and `ho.departures.HIST_ACT_T.s22.below` 4 against `ho.departures.HIST_ACT.s11.below` 3. The solver gap does not separate the arms either: every `ho.gap.*` value lies between 0.98452 (NOM s33) and 0.98540 (HIST_ACT_T s22). So the mechanism is uncertain, which §XII places under empirical limitation (SKILL:574).
- **Argument 2, reason 3** (the within-group pattern isolates the margin, and the label undersells the site-manager lesson). Rebut. That contrast is the predeclared margin main effect (CAMPAIGN_PREDECLARATION.md:462-463). It is "secondary, descriptive" (:459) and, per C-03, not isolated "from solver and layout effects" (claims.json:101). The operational lesson is already an allowed sentence: "every arm without it missed on every seed" (claims.json:98). Classification takes nothing away from it.
- **Argument 2, would change my mind** (NOM is scored like every other arm). Concede. NOM is scored per arm (CAMPAIGN_PREDECLARATION.md:459-460). Option (d) keeps that score: NOM's 0/3 seeds and its 0.939 to 1.144 pp breach in both directions stay in C-03's statement (claims.json:94).
- **Argument 1, reason 3 and proposed (e)** (NOM's miss is a boundary condition of its single-point set). Rebut. TIGHT has the same single-point set, with all 24 stations outside it by construction (`ho.departures.TIGHT.s11.above/below` 12/12), and it passed 3/3 (`ho.pass.TIGHT.count`). The evidence does not show a single-point-set assumption failing. Once that is removed, what is left of (e) is "without a margin", which is the margin attribution C-03 forbids (claims.json:108-110). C-21 also requires "Leaving the modelled set is not a band violation" (claims.json:757). The departure of the future from the modelled set is already a boundary condition for every arm (claims.json:609, 611), so (e) would count it twice for NOM.
- **Argument 1, reasons 1 and 4** (the guarantee is conditional, and the cause is not isolated). Concede. Both support (d) as much as (a) (claims.json:818, 101).
- **Argument 3, blue wording, and the steelmen of Arguments 3 and 5** (keep NOM inside the limitation, because "a negative result is reported as such" and a referee will call 0/3 a failure). Rebut. Argument 3 itself says that commitment governs disclosure, not category (CAMPAIGN_PREDECLARATION.md:112). Under (d), NOM's miss is disclosed at full strength in C-03 (claims.json:94, 102), so nothing is rescued (SKILL:590).
- **Argument 4 (my own round 1 ballot, for a), reason 3** ((a) does not soften the result). Concede that (a) is honest. It differs from (d) only in how NOM is classified.
- **Critic P1-043 for (c)** (HIST+ACT missed consistently: `ho.pass.HIST_ACT.count` 0; `ts.berner.d01/d02/d03.pass.HIST_ACT.count` 0, 1, 0). Rebut. See reason 2 below.

WHAT CHANGED MY MIND: Option (d), proposed by Argument 5. It cited PLAN.md:266 and :277, which I opened. SKILL:574 makes "the method" the subject of empirical limitation as well as of genuine failure (SKILL:586). My round 1 reason 2, that NOM is the control and not a method, therefore rules NOM out of (a)'s category too. NOM's declared purpose is "Nominal CSLAP extension" (PLAN.md:266), the reference level against which the protection hypothesis is read (PLAN.md:277). Nothing moved me on (b) or (c). The new F-078 breach anchors are outcomes, not a quantity that separates the passing layouts from the failing ones.

REASONS:
1. **(d) types each miss by its declared role.**
   - NOM is the (0,0) cell of the factorial (CAMPAIGN_PREDECLARATION.md:422). Its miss is one side of the predeclared contrast (:462-463), not a method's performance.
   - HIST+ACT is a protection arm with a hypothesis on record (PLAN.md:269, 277). Its miss is a real negative result, and (d) keeps it in C-17.
2. **The only intent on record for HIST+ACT is relative, and on the held-out window it went the way H1 predicts.**
   - H1: scenario protection "reduces held-out joint station-cap violations relative to NOM" (PLAN.md:277).
   - Cap breaches per seed (`ho.breach.*.cap_count`): HIST+ACT 1, 2, 0 against NOM 4, 4, 2.
   - All breaches, cap plus floor: HIST+ACT 1+1=2, 2+2=4, 0+2=2 against NOM 4+5=9, 4+4=8, 2+4=6.
   - This is descriptive only: three optimizer seeds at one origin, and H1 comes from the original plan, not §9 (CAMPAIGN_PREDECLARATION.md:464-465). No threshold was declared for HIST+ACT at the held-out origin; only TIGHT had one (:456-458).
   - So "did not work as intended" (SKILL:586) is not shown. The (c) label "genuine failure of scenario-and-activation protection" also generalises from one configuration (:440) toward the forbidden "proves that historical scenarios cannot protect" (claims.json:623) and "scenario protection is useless" (:112).
3. **Loses no number and fills all five §XII answers from existing anchors.**
   - What failed: the band, 0/3 seeds (`ho.pass.HIST_ACT.count`).
   - Under which conditions: δ = 0.02, ν = 0.01, λ = 0.5, one origin, one horizon (CAMPAIGN_PREDECLARATION.md:440, 436).
   - Why it might happen: breaches mostly below the floor. Floor breaches occurred on all three seeds, and the largest cap breach was 0.085 pp (`ho.breach.HIST_ACT.s22.cap_worst`). Three or four stations fell below the modelled set (`ho.departures.HIST_ACT.*.below`).
   - Demonstrated or hypothetical: hypothetical, because HIST+ACT-T had the same pattern and passed (`ho.departures.HIST_ACT_T.*.below` 2, 4, 4).
   - Which experiment would resolve it: the unrun items C-17 already lists (claims.json:609). They are named, not requested.
   - This completes C-17's own required qualifier (claims.json:617).
   - NOM's figures stay traceable in C-03 (claims.json:94, 97). The companion-positioning risk raised in Argument 3 (reason 3) goes away (WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:128-131).

STEELMAN: The strongest case for (a) is visibility. It keeps the largest breach in the study, NOM at up to 1.144 pp (`ho.breach.NOM.s33.cap_worst`), in the negative-results list, so no referee can say the nominal model's miss was moved out of Limitations. It fails for three reasons. The miss stays stated in full in C-03 (claims.json:94). §XII's categories need a method as their subject (SKILL:574, 586), and NOM is not one (PLAN.md:266). And (a)'s grouping, "neither arm without a margin" (claims.json:609), frames the limitation around the margin factor, which C-03 says is not isolated (claims.json:101).

RED CASE: not applicable (plain seat)

BLUE WORDING: not applicable (plain seat)

BLOCKING OBJECTION: none

SECOND PREFERENCE: a

CONFIDENCE: medium
