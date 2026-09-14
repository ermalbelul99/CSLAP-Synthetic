# Claim register (P1 step 5)

Readable view of `claims.json`, built by general-purpose/opus (dispatch seq 40). `claims.json` is authoritative; this file repeats its content. Every number traces to `anchors.json` or `document_values.json` at the stated display rounding. Small counts and parameters with no anchor are written in words.

## Index

### Plan P1 step 5 table rows

| P1 row | Claim ids |
|---|---|
| Scenario trade-off | C-01 |
| Margin reading | C-02 (primary endpoint), C-03 (secondary factorial reading) |
| Mechanism | C-04 |
| Solver returns | C-05 |
| Drift | C-06 |
| Protocol | C-07 |
| Margin rule | C-08 |
| Target definition and incumbent headroom | C-09 |
| Upper-only versus two-sided | C-10 |
| Model relation | C-11 |
| Band shape | C-12 |
| Savings in context | C-13 |
| Synthetic evidence role | C-14 |
| Unused tail | C-15 |
| Trapped-activation correction | C-16 |
| Negative results | C-17 |

### First plan C1 to C8, as corrected by the reviewed plan §2

| First-plan claim | Claim ids |
|---|---|
| C1 undated problem posing | C-07, C-25, C-27, C-28 |
| C2 upper-only screen | C-18, C-10 |
| C3 two-sided exploratory screen | C-19 |
| C4 δ sensitivity | C-20 |
| C5 held-out factorial | C-01, C-02, C-03, C-13 |
| C6 set coverage and total variation | C-21, C-31, C-06, C-08 |
| C7 exact counterpart and validation | C-22, C-16, C-05 |
| C8 conditional feasibility versus observed performance | C-23 |

### Reviewed plan §2 corrections

| Row (reviewed plan line) | Claim ids |
|---|---|
| Novel undated contract and rolling-origin protocol (95) | C-07 |
| Scenarios add nothing versus buy fidelity (96) | C-01, C-03 |
| Matches incumbent fidelity (97) | C-01 |
| The mechanism is isolated (98) | C-03, C-05 |
| Everything predeclared (99) | endpoint_status of every observation; C-01, C-03 |
| TV too loose, so margins from station dispersion (100) | C-08, C-31 |
| The held-out window was not easy (101) | C-06 |
| Robust arms' misses are downward (102) | C-19, C-03 |
| Scenarios do not beat tightening on the benchmark (103) | C-18 |
| Exact counterpart validated by a validator (104) | C-22 |
| No other deployment segment (105) | C-15 |

### Further claims

C-24 is the scope-once paragraph (INV-5). C-26 covers the data contract (Q-001). C-29 covers study accounting (Q-009). C-30 is the operational reading that plan P5b requires as a reader question.

### Values with no anchor or document value

These are written in words or left out, never as digits:
- the exploratory origin index (C-07, C-10, C-19)
- the upper-only tolerance of one percentage point (C-10, C-18)
- δ of one and three percentage points in the sensitivity campaigns (C-20)
- the reserved margin of one percentage point, λδ (C-08, C-30, C-31)
- the incumbent's two-sided pass count at the exploratory origin (not stated; C-19)
- the upper-only synthetic instance count (not stated; C-14, C-18)
- exploratory-origin total-variation distances (not stated as numbers; C-31)
- breach magnitude by direction (only worst breach and counts by direction are anchored; C-03)
- test-suite counts (not stated; interpretation_errata.md E-29)

## C-01: Scenario trade-off

**Type:** observation. **Endpoint status:** additional_descriptive.

**Statement.** On the held-out window, the arms with historical scenarios and activation had smaller largest absolute station deviations from target and higher mean visits than the matching arms without them, both without and with the reserved margin. Over the three optimizer seeds the largest deviation ranged from 2.939 to 3.144 percentage points for NOM against 2.069 to 2.179 for HIST+ACT, and from 1.209 to 1.756 for TIGHT against 1.026 to 1.160 for HIST+ACT-T, so the two margin arms' seed ranges do not overlap. Mean future visits per order were 3.232 for NOM against 3.264 for HIST+ACT, and 3.270 for TIGHT against 3.347 for HIST+ACT-T, which is 2.4% more visits than TIGHT; per seed, TIGHT made 3.266 to 3.276 visits per order and HIST+ACT-T 3.304 to 3.386.

**Allowed wording.**
- With the margin reserved, HIST+ACT-T kept its largest station deviation between 1.026 and 1.160 percentage points over the seeds, against 1.209 to 1.756 for TIGHT, and made 2.4% more mean future visits per order than TIGHT.
- Without the margin, the largest station deviation of HIST+ACT ranged from 2.069 to 2.179 percentage points over the seeds, against 2.939 to 3.144 for NOM, at 3.264 against 3.232 mean visits per order.
- On this maximum-deviation statistic HIST+ACT-T, at most 1.160 percentage points over the seeds, is close to the incumbent's 1.157 on the same window; the statistic does not show that their station profiles are the same.
- The scenario-and-activation arms stayed closer to the historical shares at a higher visit count; they did not change which arms satisfied the band.

**Required qualifiers.**
- (sentence) Visit counts compare time-capped returned layouts, not optima.
- (sentence) Historical scenarios and activation are bundled in this factorial, so their separate contributions are not identified.
- (sentence) The maximum-deviation comparison and the visit ratio are additional descriptive analyses, not predeclared endpoints.
- (scope_paragraph) One held-out origin and three optimizer seeds, as stated in the scope paragraph (C-24).

**Forbidden wording.**
- "identical profile to the incumbent"
- "matches the incumbent's fidelity"
- "same station profile as the incumbent"
- "equivalent tail risk"
- "protection against other futures"
- "protects against future demand"
- "a separate activation effect"
- "the effect of activation"
- "scenarios add nothing"
- "scenario protection is useless"
- "2.35%"
- "cost of protection"

**Sources.**
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §13.2 lines 1184-1189 (every cell); §13.3 lines 1196-1203 (factorial reading, bundled scenarios and activation)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): lines 80-86 (held-out anchor table); §2 lines 96-98 (scenarios buy fidelity; 2.355907%; close on the maximum-deviation statistic only)
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): §1 F11 line 74 (seed ranges); P1 step 5 table, row Scenario trade-off, line 546
- `reports/horizon_robustness_results/tables/station_profile_industrial.csv` (sha256 `fabfca653d3a…`): rows with campaign ho3_20260913 (station deviations per arm and seed)
- `reports/horizon_robustness_results/tables/case_frame.csv` (sha256 `0e9dc1f5f4c8…`): 12 rows with campaign ho3_20260913 (mean visits per order)

**Anchor keys:** `ho.maxdev.NOM.min`, `ho.maxdev.NOM.max`, `ho.maxdev.TIGHT.min`, `ho.maxdev.TIGHT.max`, `ho.maxdev.HIST_ACT.min`, `ho.maxdev.HIST_ACT.max`, `ho.maxdev.HIST_ACT_T.min`, `ho.maxdev.HIST_ACT_T.max`, `ho.maxdev.incumbent`, `ho.visits.NOM.mean`, `ho.visits.TIGHT.mean`, `ho.visits.HIST_ACT.mean`, `ho.visits.HIST_ACT_T.mean`, `ho.visits.TIGHT.s11`, `ho.visits.TIGHT.s22`, `ho.visits.TIGHT.s33`, `ho.visits.HIST_ACT_T.s11`, `ho.visits.HIST_ACT_T.s22`, `ho.visits.HIST_ACT_T.s33`, `ho.visits.HIST_ACT_T_over_TIGHT.pct`.
**Document-value keys:** none.

**Unit:** pp (largest absolute station deviation); visits_per_order; pct (visit ratio). **Denominator:** three optimizer seeds per arm at one held-out origin; the deviation is the maximum over the 24 evaluated stations; means are over the three seeds. **Display rounding (decimals):** `{"pp": 3, "visits_per_order": 3, "pct": 1}`.

**Scope boundary.** Held-out campaign ho3_20260913 only. The percentage uses the companion's one-decimal convention (plan F13); if STYLE_CANON.md fixes another rounding, only the displayed digits change (2.355907 exact). Never computed from three-decimal display values.

**Supersedes:** WRITING_PLAN_20260914.md §1 C5 (line 61), scenario part; WRITING_EXECUTION_PLAN_REVIEWED_20260914.md §2 rows 'Scenarios add nothing' and 'Matches incumbent fidelity' (lines 96-97).

## C-02: Margin reading (primary endpoint)

**Type:** observation. **Endpoint status:** predeclared_primary.

**Statement.** The predeclared primary endpoint required TIGHT to satisfy the two-sided band with δ = 0.02 at n = P = 21,874 on the held-out window starting at order index 243,151 for at least two of the three optimizer seeds. TIGHT satisfied the band for all three seeds, so the endpoint was met.

**Allowed wording.**
- TIGHT satisfied the two-sided band on all three optimizer seeds at the held-out origin, which meets the predeclared primary endpoint of at least two seeds.
- The predeclared "Replication endpoint" tests the same policy at a later origin of the same order stream, whose history contains the exploratory origin's data; TIGHT met it on all three optimizer seeds.
- TIGHT passed 3/3 seeds against a predeclared threshold of two.

**Required qualifiers.**
- (sentence) The endpoint tests the same fixed policy at a later origin of the same order stream, and that origin's training history contains the exploratory origin's data and scored futures.
- (sentence) Meeting the endpoint supports a bounded case-study claim only.
- (scope_paragraph) Three optimizer seeds at one origin describe optimizer variability, not future demand (C-24).

**Forbidden wording.**
- "replicated"
- "REPLICATED"
- "independent replication"
- "replication of the exploratory result"
- "confirms the exploratory finding"
- "validated policy"
- "certified band"
- "guarantees compliance"

**Sources.**
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §9.3 lines 456-458: "Replication endpoint (primary): TIGHT passes the two-sided ±2 band at n = P on the held-out future for at least two of the three seeds. Failure closes the fixed-policy claim; passing supports a bounded case-study claim only."; §9.2 lines 429-443 (origin, horizon, frozen policy)
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §13.2 line 1187 (TIGHT row, three passes); §13.3 line 1193 (endpoint read; its word REPLICATED is rejected, see interpretation_errata.md)
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): §5 INV-5 label rule lines 374-376; F19 line 82
- `reports/horizon_robustness_results/tables/case_frame.csv` (sha256 `0e9dc1f5f4c8…`): rows campaign ho3_20260913, arm TIGHT (joint two-sided pass per seed)

**Anchor keys:** `ho.pass.TIGHT.count`.
**Document-value keys:** `pred.holdout.delta`, `pred.holdout.n`, `pred.holdout.origin`.

**Unit:** count (seeds passing). **Denominator:** three optimizer seeds at one held-out origin. **Display rounding (decimals):** `{"count": 0, "share": 2}`.

**Scope boundary.** Held-out campaign ho3_20260913 only. The predeclared label may be quoted once, immediately followed by the qualifier (INV-5).

**Supersedes:** EXPERIMENT_REVIEW_HANDOFF.md §13.3 line 1193 'REPLICATED.'; WRITING_PLAN_20260914.md §1 C5 (line 61), compliance part.

## C-03: Margin reading (secondary factorial reading)

**Type:** observation. **Endpoint status:** predeclared_secondary.

**Statement.** In the held-out factorial, both arms with the reserved margin, TIGHT and HIST+ACT-T, satisfied the two-sided band on all three optimizer seeds, and neither arm without it, NOM or HIST+ACT, satisfied it on any seed. The misses differed in size: the worst breach beyond the band ranged over the seeds from 0.939 to 1.144 percentage points for NOM and from 0.069 to 0.179 for HIST+ACT. Both no-margin arms breached in both directions: NOM above the cap and below the floor on every seed, HIST+ACT above the cap on two seeds and below the floor on all three.

**Allowed wording.**
- The margin arms passed 3/3 seeds and the no-margin arms 0/3.
- Table note: worst breach over the seeds, HIST+ACT 0.069–0.179 pp, NOM 0.939–1.144 pp.
- Every arm with the reserved margin satisfied the band on every seed, and every arm without it missed on every seed; the worst breach of HIST+ACT was at most 0.179 percentage points, and that of NOM at least 0.939.

**Required qualifiers.**
- (sentence) This two-factor comparison under equal configured solve budgets at one origin is not a causal law, and it does not isolate the margin from solver and layout effects.
- (sentence) Breach magnitudes are the worst excess per seed; a small breach is still a miss of the declared policy.
- (scope_paragraph) Pass counts are counts over three optimizer seeds at one origin (C-24).

**Forbidden wording.**
- "isolated mechanism"
- "the mechanism is isolated"
- "margin decides the pass"
- "the margin causes compliance"
- "attributes compliance to the reserved margin"
- "scenarios add nothing"
- "scenario protection is useless"
- "negligible breach"
- "the whole factorial interpretation was predeclared"

**Sources.**
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §9.3 lines 459-465 (factorial reading, secondary, descriptive: pass count and breach magnitudes in both directions)
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §13.2 lines 1186-1189 (cap/floor breaches and worst breach per seed); §13.3 lines 1196-1203
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §2 line 98 ('The mechanism is isolated' corrected); line 99 (predeclared versus additional)
- `reports/horizon_robustness_results/tables/case_frame.csv` (sha256 `0e9dc1f5f4c8…`): 12 rows campaign ho3_20260913 (joint pass, worst excess, cap and floor violation counts)

**Anchor keys:** `ho.pass.NOM.count`, `ho.pass.TIGHT.count`, `ho.pass.HIST_ACT.count`, `ho.pass.HIST_ACT_T.count`, `ho.breach.NOM.s11.worst`, `ho.breach.NOM.s22.worst`, `ho.breach.NOM.s33.worst`, `ho.breach.HIST_ACT.s11.worst`, `ho.breach.HIST_ACT.s22.worst`, `ho.breach.HIST_ACT.s33.worst`, `ho.breach.NOM.s11.cap_count`, `ho.breach.NOM.s22.cap_count`, `ho.breach.NOM.s33.cap_count`, `ho.breach.NOM.s11.floor_count`, `ho.breach.NOM.s22.floor_count`, `ho.breach.NOM.s33.floor_count`, `ho.breach.HIST_ACT.s11.cap_count`, `ho.breach.HIST_ACT.s22.cap_count`, `ho.breach.HIST_ACT.s33.cap_count`, `ho.breach.HIST_ACT.s11.floor_count`, `ho.breach.HIST_ACT.s22.floor_count`, `ho.breach.HIST_ACT.s33.floor_count`.
**Document-value keys:** none.

**Unit:** count (seeds passing; stations breaching); pp (worst breach). **Denominator:** three optimizer seeds per arm at one held-out origin; breach counts over the 24 evaluated stations. **Display rounding (decimals):** `{"count": 0, "pp": 3}`.

**Scope boundary.** Held-out campaign ho3_20260913 only. The anchors give the worst breach per seed without its direction and the breach counts by direction; a magnitude per direction is not anchored and is not stated.

**Supersedes:** WRITING_PLAN_20260914.md §3 line 115 'isolated mechanism'; EXPERIMENT_REVIEW_HANDOFF.md §13.3 line 1203 'the margin decides the pass'; WRITING_EXECUTION_PLAN_REVIEWED_20260914.md §2 row 'The mechanism is isolated' (line 98).

## C-04: Mechanism

**Type:** observation. **Endpoint status:** additional_descriptive.

**Statement.** Every returned held-out layout used essentially its whole training allowance. The minimum training slack each layout required lay between 0.019997 and 0.019999 for NOM and HIST+ACT, which optimised against the band with δ = 0.02, and between 0.009992 and 0.009999 for TIGHT and HIST+ACT-T, whose band was tightened with λ = 0.5.

**Allowed wording.**
- No returned layout kept spare slack on its training scenarios: each required almost exactly the allowance its arm was given.
- The layouts without a margin required between 0.019997 and 0.019999 of the allowed 0.02, and the layouts with the margin between 0.009992 and 0.009999.

**Required qualifiers.**
- (sentence) The minimum required slack is measured on each arm's own training scenario set, not on the future window.
- (sentence) It describes the time-capped layouts the optimizer returned, not a property of an optimum.

**Forbidden wording.**
- "optimal layouts use the whole allowance"
- "the optimizer always exhausts the band"
- "the band binds at the optimum"

**Sources.**
- `reports/horizon_robustness_results/tables/case_frame.csv` (sha256 `0e9dc1f5f4c8…`): 12 rows campaign ho3_20260913, column minimum_required_slack (exact field validation.minimum_required_slack_exact in the case records)
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): §1 F10 line 73; P1 step 5 table, row Mechanism, line 548
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §9.2 lines 418-420 (margin level: optimise inside the band tightened by λ)

**Anchor keys:** `ho.min_slack.NOM.s11`, `ho.min_slack.NOM.s22`, `ho.min_slack.NOM.s33`, `ho.min_slack.HIST_ACT.s11`, `ho.min_slack.HIST_ACT.s22`, `ho.min_slack.HIST_ACT.s33`, `ho.min_slack.TIGHT.s11`, `ho.min_slack.TIGHT.s22`, `ho.min_slack.TIGHT.s33`, `ho.min_slack.HIST_ACT_T.s11`, `ho.min_slack.HIST_ACT_T.s22`, `ho.min_slack.HIST_ACT_T.s33`.
**Document-value keys:** `pred.holdout.delta`, `pred.holdout.lambda`.

**Unit:** share. **Denominator:** 12 held-out layouts (four arms, three seeds each). **Display rounding (decimals):** `{"share": 6}`.

**Scope boundary.** Held-out campaign ho3_20260913 only. Display: the per-station overlay of target, training envelope, realised share and band (plan P5b) carries this observation.

**Supersedes:** none.

## C-05: Solver returns

**Type:** scope. **Endpoint status:** not_applicable.

**Statement.** All 12 held-out solves returned time-capped layouts with no proof of optimality: each reports a gap of about 0.985 against a bound of 11,517, and the 12 solves were configured for 21,600 seconds in total. Visit costs therefore compare returned layouts, and no difference between arms is a difference between optimal objectives. The gap and bound belong in the supplement, with one sentence in the main text.

**Allowed wording.**
- Every held-out layout is the best solution the solver returned within its time limit; none is shown to be optimal.
- Each held-out solve ended with a gap of about 0.985 against a bound of 11,517 (supplement).

**Required qualifiers.**
- (sentence) Differences in visits between arms compare returned layouts under equal configured budgets.
- (sentence) No visit figure is an optimal value, so the visit cost of the margin is not identified exactly.

**Forbidden wording.**
- "the optimal layout"
- "optimal layouts"
- "optimal visit cost"
- "proven optimal protection cost"
- "cost of protection"
- "price of robustness"
- "a new exact optimizer"

**Sources.**
- `reports/horizon_robustness_results/tables/case_frame.csv` (sha256 `0e9dc1f5f4c8…`): 12 rows campaign ho3_20260913, columns gap and bound
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §9.2 lines 440-443 (time cap per solve; 12 unique solves, 21,600 s configured)
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §9.2 items 4 and 4b lines 871-879 (returned incumbents, not optima); §13.1 line 1178
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): §1 F10 line 73 (gap ≈ 0.985, bound 11,517); P1 step 5 table, row Solver returns, line 549

**Anchor keys:** `ho.gap.NOM.s11`, `ho.gap.NOM.s22`, `ho.gap.NOM.s33`, `ho.gap.TIGHT.s11`, `ho.gap.TIGHT.s22`, `ho.gap.TIGHT.s33`, `ho.gap.HIST_ACT.s11`, `ho.gap.HIST_ACT.s22`, `ho.gap.HIST_ACT.s33`, `ho.gap.HIST_ACT_T.s11`, `ho.gap.HIST_ACT_T.s22`, `ho.gap.HIST_ACT_T.s33`, `ho.bound.NOM.s11`, `ho.bound.NOM.s22`, `ho.bound.NOM.s33`, `ho.bound.TIGHT.s11`, `ho.bound.TIGHT.s22`, `ho.bound.TIGHT.s33`, `ho.bound.HIST_ACT.s11`, `ho.bound.HIST_ACT.s22`, `ho.bound.HIST_ACT.s33`, `ho.bound.HIST_ACT_T.s11`, `ho.bound.HIST_ACT_T.s22`, `ho.bound.HIST_ACT_T.s33`.
**Document-value keys:** `pred.holdout.solves`, `pred.holdout.configured_seconds`.

**Unit:** fraction (gap); visits (bound); count (solves); seconds. **Denominator:** 12 held-out solves. **Display rounding (decimals):** `{"fraction": 3, "visits": 0, "count": 0, "seconds": 0}`.

**Scope boundary.** Held-out campaign ho3_20260913. The same limit applies to every returned layout of every campaign (handoff §9.2 items 4 and 4b), but only the held-out gap and bound are anchored.

**Supersedes:** WRITING_PLAN_20260914.md §3 lines 122-124 'what the band costs'.

## C-06: Drift

**Type:** context. **Endpoint status:** additional_descriptive.

**Statement.** Measured only after the held-out window had been scored, its product mix lay at a total-variation distance of 0.195 from the pooled history it was scored against. The stored historical values over 11 blocks, a maximum of 0.194 and a mean of 0.171, measure each block against a pooled history that contains that block, which shrinks each value by the factor one minus the block's mass fraction. With that fraction taken by order count, about 0.09, the like-for-like historical maximum, each block measured against the rest of the history, is about 0.214, above the held-out value; the stored ordering reverses for any mass fraction above about 0.0028. The incumbent layout satisfied the two-sided band on the held-out window.

**Allowed wording.**
- Measured against the rest of the history, the largest historical block distance is about 0.214, and the held-out product mix, at 0.195 from the pooled history, lies below it.
- The stored comparison, 0.195 against a historical maximum of 0.194, places each historical block inside its own reference; corrected for that, the historical maximum is about 0.214.
- The incumbent layout satisfied the two-sided band on the held-out window.

**Required qualifiers.**
- (sentence) Block line mass is not stored, so the block mass fraction is taken by order count, and this is disclosed.
- (sentence) Total-variation distance measures product-mix change, not the difficulty of holding station shares, because aggregation within a station can cancel product-level change.
- (sentence) The future distance is ex post; the reserved margin was not chosen from this survey and is not re-chosen after the result.

**Forbidden wording.**
- "substantial", forbidden while Q-008 has outcome `w_greater_than_w_star`
- "despite", forbidden while Q-008 has outcome `w_greater_than_w_star`
- "beyond the historical maximum", forbidden while Q-008 has outcome `w_greater_than_w_star`
- "difficult"
- "demanding"
- "stress test"
- "not an easy case"
- "not an easy one"
- "at the top of the historical range"
- "extreme drift"
- "calibrated extremeness"
- "unprecedented"

**Sources.**
- `reports/horizon_robustness_results/tables/drift_survey.csv` (sha256 `60e729006f50…`): row dataset_id = BERNER@holdout (file line 17): historical_blocks 11, historical_tv_max, historical_tv_mean, future_tv_ex_post
- `tools/horizon_robustness/drift_survey.py` (sha256 `fcf8168967ed…`): lines 13-15 ("TV between each right-aligned n-block of the history prefix and the pooled history of the SAME prefix"); lines 83-87
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): §1 F16 line 79 (TV(block, pooled) = (1 − w)·TV(block, rest); w*); P1 step 5 table, row Drift, line 550
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §2 row 'The held-out window was not easy', line 101
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §9.4 lines 476-478 (drift survey reported as explanatory context only; margin not chosen from it)
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §13.2 line 1186 (incumbent pass on the same future); §13.3 line 1205 (rejected reading, see interpretation_errata.md)

**Anchor keys:** `drift.holdout.future_tv`, `drift.holdout.hist_tv_max`, `drift.holdout.hist_tv_mean`, `drift.holdout.blocks`, `drift.holdout.w_order_count`, `drift.holdout.w_star`, `drift.holdout.hist_tv_max.like_for_like`, `ho.incumbent.joint_pass`.
**Document-value keys:** none.

**Unit:** tv; fraction (w, w*); count (blocks); bool (incumbent pass). **Denominator:** 11 matched historical blocks of n = 21,874 orders in the prefix before order index 243,151; one scored future window. **Display rounding (decimals):** `{"tv": 3, "fraction_w_order_count": 2, "fraction_w_star": 4, "count": 0}`.

**Scope boundary.** Q-008 decisive test resolved w_greater_than_w_star (Resolution line of Q-008), so the three conditional wordings stay forbidden. The replacement wording is Class J and is decided by SCI-5 with a blue-team seat; allowed_wording here is the conservative default and may be amended by that DR. Q-003 governs the like-for-like correction.

**Supersedes:** EXPERIMENT_REVIEW_HANDOFF.md §13.3 line 1205; WRITING_EXECUTION_PLAN_REVIEWED_20260914.md line 101 'high product-mix drift' as a comparison with history.

## C-07: Protocol

**Type:** definition. **Endpoint status:** not_applicable.

**Statement.** The study evaluates layouts with an order-indexed, horizon-conditioned protocol. At a deployment origin in the stream of complete orders, ordered by order identifier, the targets and training scenarios are computed from the prefix before the origin, the layout is frozen, and it is scored on the next n complete orders. The evidence comes from an exploratory origin and one later held-out deployment at order index 243,151 with n = 21,874, whose training prefix contains the exploratory origin's history and every future scored there.

**Allowed wording.**
- We use an order-indexed, horizon-conditioned protocol with a later held-out deployment.
- The held-out deployment starts at order index 243,151 and scores the next 21,874 complete orders; its training prefix contains the exploratory origin's data and scored futures.

**Required qualifiers.**
- (sentence) The predeclared label "Replication endpoint" may be quoted once, immediately followed by the statement that it tests the same policy at a later origin of the same stream, whose history contains the exploratory origin's data.
- (sentence) This is a contribution relative to the companion; out-of-sample and rolling-origin evaluation are established techniques, and the companion already evaluates layouts on unseen dated weeks.
- (sentence) The held-out window was unexamined in this study, not unexamined by anyone: the companion's temporal hold-out used a different dated extract.

**Forbidden wording.**
- "novel methodology"
- "novel undated information contract"
- "rolling-origin experiment"
- "rolling-origin protocol"
- "replicated"
- "independent replication"
- "first out-of-sample evaluation"
- "unexamined by anyone"
- "nobody else has measured this"

**Sources.**
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §2 row 1, line 95 ("Prefer order-indexed, horizon-conditioned protocol with a later held-out deployment"); line 74 (companion already contains dated unseen-week evaluation)
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §9.2 lines 429-435 (origin at the end of the furthest scored future; target from the full prefix, frozen; 'unexamined in this study', not 'unexamined by anyone')
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): INV-5 label rule lines 374-376; P1 step 5 table, row Protocol, line 551; P4 step 4 line 717 ("Nobody else has measured this" is inadmissible)
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md` (sha256 `b8ffb5df2bf0…`): §2 line 27 (next n complete orders); §8 line 85 (prefix-only training, layout fixed before scoring)

**Anchor keys:** none.
**Document-value keys:** `pred.holdout.origin`, `pred.holdout.n`.

**Unit:** count (order index; orders). **Denominator:** one exploratory origin and one held-out origin. **Display rounding (decimals):** `{"count": 0}`.

**Scope boundary.** Type 'definition' because the row states what the protocol is; its contribution status relative to the companion is carried by the second qualifier. 'novel methodology' stays forbidden unless a P4 NOV-5 DR establishes it and supersedes this entry. The exploratory origin's index has no anchor or document value and is therefore not written as a number.

**Supersedes:** WRITING_PLAN_20260914.md §0 lines 37-38 'undated information contract and predeclared rolling-origin protocol'; WRITING_PLAN_20260914.md §1 C1 (line 57).

## C-08: Margin rule

**Type:** limitation. **Endpoint status:** not_applicable.

**Statement.** The study obtained no validated rule for choosing the reserved margin. On the exploratory prefix, the incumbent layout's largest station-share deviation in a single historical block was 1.70 percentage points at n = P/2, 1.63 at n = P and 1.47 at n = 2P, each block measured against a pooled history that contains it; against the rest of the history the values are about 1.80, 1.83 and 1.89. Either way they exceed the reserved margin of one percentage point, and the margin arms nevertheless satisfied the band on the held-out window, so the margin was neither set from this statistic nor validated by it.

**Allowed wording.**
- No validated rule for choosing the margin was obtained.
- The incumbent's largest historical block deviation on the exploratory prefix, 1.63 percentage points at n = P against a reference that contains the block and about 1.83 against the rest of the history, was larger than the reserved margin of one percentage point.

**Required qualifiers.**
- (sentence) These dispersion values come from the prefix before the exploratory origin; no value exists for the held-out prefix, and none is stated about it.
- (sentence) The like-for-like values take the block mass fraction by order count.
- (sentence) The incumbent's dispersion belongs to its own layout and does not calibrate the margin of an optimised layout, and the failure of the total-variation certificate does not imply any particular alternative rule.

**Forbidden wording.**
- "margins must come from station-level dispersion"
- "margin has to be set from station-level dispersion"
- "any date-free margin rule has to be predeclared from station-level dispersion"
- "empirically calibrated margin rule"
- "automatic margin calibration"
- "the reserved margin is validated"
- "dispersion of the held-out prefix"
- "about 1.7 points at most"

**Sources.**
- `reports/horizon_robustness_results/tables/dispersion_survey.csv` (sha256 `74d52002a50f…`): rows dataset_id = BERNER, origin 199403, n = 10937 / 21874 / 43748 (file lines 89-91), column max_abs_pp
- `tools/horizon_robustness/dispersion_survey.py` (sha256 `d3f4c75e6f12…`): lines 10-13 (blocks plus pooled history; b_s pooled share; d_ks = block share minus b_s)
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §8.2 lines 354-356 ("1.70 pp in a single historical block relative to its pooled share")
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): §1 F17 line 80; P1 step 5 table, row Margin rule, line 552
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §2 row 'TV is too loose, so margins have to come from station dispersion', line 100
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §12.6 line 1162 (rejected reading, see interpretation_errata.md); §12.6 line 1158 (λ frontier not run)

**Anchor keys:** `disp.explor.n_half.max_abs`, `disp.explor.n_P.max_abs`, `disp.explor.n_2P.max_abs`, `disp.explor.n_half.max_abs.like_for_like`, `disp.explor.n_P.max_abs.like_for_like`, `disp.explor.n_2P.max_abs.like_for_like`.
**Document-value keys:** `pred.twosided.block_deviation_quoted`.

**Unit:** pp. **Denominator:** historical blocks by 24 evaluated stations under the incumbent, exploratory prefix, three horizons. **Display rounding (decimals):** `{"pp": 2}`.

**Scope boundary.** Exploratory prefix (origin of the first scored futures) only. The reserved margin of one percentage point is λδ at the held-out policy (δ = 0.02 share, λ = 0.5); it is written in words because no anchor holds that product.

**Supersedes:** WRITING_PLAN_20260914.md §0 lines 43-45 'margin has to be set from station-level dispersion'; EXPERIMENT_REVIEW_HANDOFF.md §12.6 line 1162, last two sentences.

## C-09: Target definition and incumbent headroom

**Type:** assumption. **Endpoint status:** not_applicable.

**Statement.** The targets b_s are the incumbent layout's own historical station shares over the training prefix, frozen at the origin, so the incumbent starts with the whole allowance as headroom while an optimised layout spends it. On the single history scenario on which NOM and TIGHT train, the incumbent's minimum required slack is 0, against about 0.020 for the NOM layouts and about 0.010 for the TIGHT layouts. On the scenario set of HIST+ACT and HIST+ACT-T, 11 historical blocks plus the history scenario, the incumbent requires about 0.0157, inside δ = 0.02 and above the tightened allowance, against about 0.020 for the HIST+ACT layouts and about 0.010 for the HIST+ACT-T layouts.

**Allowed wording.**
- The targets are the incumbent's own historical shares, so on the history scenario the incumbent needs no slack, whereas every optimised layout uses its whole allowance.
- On the block scenario set of the scenario arms the incumbent needs about 0.0157 of share, which fits within δ = 0.02 but not within the tightened allowance.

**Required qualifiers.**
- (sentence) State the target definition and this asymmetry before any result that compares arms with the incumbent (handoff §11, second question).
- (sentence) The incumbent is scored on the same future as context, not as a feasibility standard for the optimised arms.

**Forbidden wording.**
- "optimisation harms compliance"
- "the incumbent is more robust"
- "the incumbent passes because it is robust"
- "a neutral target"

**Sources.**
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §11 question 2, lines 1028-1032: "Because b is the incumbent's own historical share, the incumbent starts with the full δ of headroom while any optimizer spends it."
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §9.2 lines 432-433 (target b_s computed from the full prefix and then frozen)
- `reports/horizon_robustness_results/tables/case_frame.csv` (sha256 `0e9dc1f5f4c8…`): rows campaign ho3_20260913, column minimum_required_slack (arms); incumbent value from reference_evaluation.validation in the case records
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): P1 step 5 table, row Target definition and incumbent headroom, line 553; P1 step 7 Q-005, lines 575-576

**Anchor keys:** `ho.incumbent.training_slack.history`, `ho.incumbent.training_slack.hist_act`, `ho.min_slack.NOM.s11`, `ho.min_slack.NOM.s22`, `ho.min_slack.NOM.s33`, `ho.min_slack.TIGHT.s11`, `ho.min_slack.TIGHT.s22`, `ho.min_slack.TIGHT.s33`, `ho.min_slack.HIST_ACT.s11`, `ho.min_slack.HIST_ACT.s22`, `ho.min_slack.HIST_ACT.s33`, `ho.min_slack.HIST_ACT_T.s11`, `ho.min_slack.HIST_ACT_T.s22`, `ho.min_slack.HIST_ACT_T.s33`, `drift.holdout.blocks`.
**Document-value keys:** `pred.holdout.delta`, `handoff.q2.incumbent_headroom`.

**Unit:** share (minimum required slack); count (blocks). **Denominator:** incumbent on each training scenario set; 12 held-out layouts. **Display rounding (decimals):** `{"share_arms": 3, "share_incumbent_hist_act": 4, "count": 0}`.

**Scope boundary.** Q-005 key rule: ho.incumbent.training_slack.history is compared only with NOM and TIGHT, and ho.incumbent.training_slack.hist_act only with HIST+ACT and HIST+ACT-T; the retired key ho.incumbent.training_slack is never cited. The motivation for share targets (Q-004) is open until P2; this claim states the definition and the asymmetry only.

**Supersedes:** none.

## C-10: Upper-only versus two-sided

**Type:** interpretation. **Endpoint status:** exploratory.

**Statement.** The upper-only screen and the two-sided campaigns order TIGHT and HIST+ACT differently on BERNER, and the difference is consistent with the size and side of the margin each rule reserved. Under the upper-only rule, with a tolerance of one percentage point, HIST+ACT satisfied the caps at two of three horizons and TIGHT at none; the TIGHT layouts required a training allowance of about 0.005, so half a percentage point was reserved, on the cap side only. Under the two-sided rule with δ = 0.02, the TIGHT layouts required about 0.010, so one percentage point was reserved on each side; TIGHT satisfied the band at all three horizons and HIST+ACT at one, and the misses of the scenario arms were mostly below the floor, with 0 cap and 3 floor breaches for HIST+ACT and 1 cap and 8 floor breaches for HIST, summed over the three horizons.

**Allowed wording.**
- The upper-only screen reserved half a percentage point on the cap side, and the two-sided rule one percentage point on each side; TIGHT satisfied none of the three BERNER horizons under the first and all three under the second.
- Under the two-sided rule the scenario arms missed mostly below the floor: 0 cap and 3 floor breaches for HIST+ACT, and 1 cap and 8 floor breaches for HIST.

**Required qualifiers.**
- (sentence) Both campaigns are exploratory, with one seed at one origin, and the two-sided policy was fixed after the same futures had been examined under the upper-only rule.
- (sentence) Upper-only and two-sided results are reported side by side and never pooled, and consistency with the margin size is not a causal isolation.
- (sentence) Upper-only caps limit increases only, so an upper-only pass does not show that station profiles were preserved.

**Forbidden wording.**
- "the two-sided result contradicts the upper-only screen"
- "HIST+ACT is better than TIGHT"
- "TIGHT is better than HIST+ACT"
- "robust-arm misses are downward"
- "two-sided balance preservation"
- "the held-out result reverses the screen"

**Sources.**
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §10.4 lines 973-979 (upper-only BERNER violations; HIST+ACT passes two of three); §12.2 lines 1084-1108 (two-sided BERNER cells and pass table); §12.5 item 5 line 1149 (11 floor against 1 cap breaches); §12.6 line 1160 (exploratory)
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §2 lines 59-62 (TIGHT λ = 0.5; upper-only primary δ = 0.01); §8.3 lines 382-384 (TIGHT at λ = 0.5 under δ = 0.02 optimises inside the ±1 band)
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md` (sha256 `b8ffb5df2bf0…`): §3 lines 31-37 (upper-only protection is not two-sided balance preservation)
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): §1 F12 line 75; P1 step 2 lines 516-517 (margin size under each rule; breach directions); P1 step 5 table, row Upper-only versus two-sided, line 554
- `reports/horizon_robustness_plan/PLAN.md` (sha256 `69ce4d643497…`): line 169 ("label the resulting study retrospective/exploratory, not a newly untouched confirmatory holdout")

**Anchor keys:** `uo.berner.pass.NOM.count`, `uo.berner.pass.TIGHT.count`, `uo.berner.pass.HIST.count`, `uo.berner.pass.HIST_ACT.count`, `uo.berner.min_slack.TIGHT.10937`, `uo.berner.min_slack.TIGHT.21874`, `uo.berner.min_slack.TIGHT.43748`, `ts.berner.d02.pass.NOM.count`, `ts.berner.d02.pass.TIGHT.count`, `ts.berner.d02.pass.HIST.count`, `ts.berner.d02.pass.HIST_ACT.count`, `ts.berner.d02.min_slack.TIGHT.10937`, `ts.berner.d02.min_slack.TIGHT.21874`, `ts.berner.d02.min_slack.TIGHT.43748`, `ts.berner.d02.HIST_ACT.cap_breaches_total`, `ts.berner.d02.HIST_ACT.floor_breaches_total`, `ts.berner.d02.HIST.cap_breaches_total`, `ts.berner.d02.HIST.floor_breaches_total`.
**Document-value keys:** `pred.twosided.delta_primary`.

**Unit:** count (horizons passing; breaches); share (training allowance). **Denominator:** three BERNER horizons at the exploratory origin, one seed, per rule. **Display rounding (decimals):** `{"count": 0, "share": 3}`.

**Scope boundary.** BERNER at the exploratory origin: campaign screen_20260910 (upper-only) and ts_d02_20260912 (two-sided). The upper-only tolerance has no anchor or document value and is written in words (CAMPAIGN_PREDECLARATION.md:62). The reserved margin is the tolerance minus the TIGHT training allowance; it equals that allowance because λ = 0.5.

**Supersedes:** WRITING_PLAN_20260914.md §1 C2 (line 58), BERNER part; earlier plan wording 'floor-breach counts' (orchestration plan P1 step 2, lines 516-517).

## C-11: Model relation

**Type:** definition. **Endpoint status:** not_applicable.

**Statement.** The extension keeps the companion's assignment variables x_ps and visit variables z_os, its single-station assignment and slot-capacity rows with slot counts ζ_s, and its objective of minimising total order-station visits. It replaces the companion's station workload-budget rows, which bound each station's load by its budget T_s, with share-policy rows that keep each station's share of total workload inside a band around its target b_s; share preservation is therefore a feasibility policy, not an objective. For a given total workload, an upper share row is a budget row whose budget is proportional to that total, and multiplying every product's workload by a common positive factor leaves every share, and so share feasibility, unchanged; this is the only sense in which the share rows stand in for budgets.

**Allowed wording.**
- Station budgets are replaced, not supplemented, by share-policy rows; the visit objective and the assignment rows are unchanged.
- A share row equals a budget row scaled with total workload, so the policy needs no absolute workload level.

**Required qualifiers.**
- (sentence) Uniform scaling leaves shares unchanged, but it does not make the learned layout or its future compliance independent of the horizon.
- (sentence) Notation follows the companion: ζ_s counts slots and C_s is the companion's line capacity, so C_s is not used for slots, and V_s and T_s are inherited context only.
- (sentence) The band half-width δ is an absolute share allowance and is not the companion's relative workload tolerance.
- (sentence) Industrial workload here counts distinct retained product-order pairs, not the companion's load normalised by processing rate.

**Forbidden wording.**
- "new objective"
- "share-preservation objective"
- "workload-share preservation objective"
- "rows added to the companion's feasible set"
- "supplements the budget constraints"
- "scale invariance makes the layout independent of the horizon"

**Sources.**
- `IJSSOL_CSLAP_v1.tex` (sha256 `441f7fd2e2fa…`): lines 186-193 (notation table tab:data: line 192 "$T_s$ & Workload budget of station $s$", line 193 "$C_s$ & Line capacity $T_s V_s$ of station $s$ over the horizon"); lines 228-237 (eq:obj, eq:assign, eq:cap, eq:link, eq:wl); lines 249-252 (eq:setobj to eq:setwl); line 212 ("Workload balance therefore enters as a constraint and not as a term of the objective."); line 584 (budget $T_s$ is $110\%$ of legacy load)
- `IJSSOL_CSLAP_v1_supplementary.tex` (sha256 `e5a65a053a8a…`): lines 532-533 ("the workload budget $T_s$ is $110\%$ of a station's complete legacy load, the $10\%$ being the tolerance the site operates to.")
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md` (sha256 `b8ffb5df2bf0…`): §1 lines 9-13 (workload counts; complete station share); §2 lines 21-25 (scale invariance; delta an absolute share allowance)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §3 table lines 141-147 (workload restriction replaced, not supplemented); lines 152-154 (not a new objective); lines 201-203 (scale invariance is not invariance of the learned layout); §5 override 1 lines 275-281 (notation)
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): P1 step 5 table, row Model relation, line 555

**Anchor keys:** none.
**Document-value keys:** `comp.budget.definition`, `comp.supp.workload.definition`.

**Unit:** none. **Denominator:** not applicable. **Display rounding (decimals):** `{"none": null}`.

**Scope boundary.** Definition of the model relation only; the formal delta is written in P3 (W/math/model_delta.md). MATHEMATICAL_SCOPE.md §1 line 15 uses C_s for slots; that internal usage is not carried into the paper.

**Supersedes:** WRITING_PLAN_20260914.md §2 lines 85-86 'the extension's rows are added to that feasible set'; WRITING_PLAN_20260914.md §2 line 95 'the workload-share preservation objective'.

## C-12: Band shape

**Type:** premise. **Endpoint status:** not_applicable.

**Statement.** The policy band is absolute: station s must keep its future share within [max(0, b_s − δ), min(1, b_s + δ)], so every station receives the same allowance in share units whatever its target, and at the primary setting δ = 0.02 that allowance is two percentage points on each side. A band proportional to b_s was not studied.

**Allowed wording.**
- The band is absolute, the same number of percentage points at every station; a relative band was not run.

**Required qualifiers.**
- (sentence) Findings about the absolute band do not transfer to a relative band.

**Forbidden wording.**
- "holds for relative bands"
- "proportional band"
- "does not depend on the band shape"

**Sources.**
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §8.1 lines 342-344 ("Every station must stay within ±δ of its historical share"; floors clipped at zero, caps at one)
- `reports/horizon_robustness_plan/PLAN.md` (sha256 `69ce4d643497…`): line 90 ("a transparent, identical absolute-share departure limit"; not the article's relative allowance)
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md` (sha256 `b8ffb5df2bf0…`): §2 line 21 (delta measured as an absolute share allowance)
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): P1 step 5 table, row Band shape, line 556

**Anchor keys:** none.
**Document-value keys:** `pred.holdout.delta`, `pred.twosided.delta_primary`.

**Unit:** share. **Denominator:** not applicable. **Display rounding (decimals):** `{"share": 2}`.

**Scope boundary.** All two-sided campaigns use this band; the upper-only screen uses the cap side only.

**Supersedes:** none.

## C-13: Savings in context

**Type:** context. **Endpoint status:** predeclared_secondary.

**Statement.** On the held-out window every optimised arm made fewer future station visits per order than the incumbent layout, which made 3.847: the arm-level mean over three optimizer seeds was 16.0% fewer for NOM, 15.0% for TIGHT, 15.2% for HIST+ACT and 13.0% for HIST+ACT-T, and single runs ranged from 12.0% to 17.5% fewer. These savings are not comparable with the companion's 6.6% and 7.4% on unseen weeks, or with its 13.7% in sample, because the extract, the order stream, the reference layout and the workload restriction all differ.

**Allowed wording.**
- Against the incumbent on the same held-out window, the arms made 13.0–16.0% fewer future visits per order (arm-level means over three optimizer seeds; single runs 12.0–17.5%).
- These savings are not comparable with the companion's 6.6% and 7.4% on unseen weeks, which come from a different extract, stream, reference layout and workload restriction.

**Required qualifiers.**
- (sentence) The savings compare time-capped returned layouts with the incumbent on the same future window.
- (sentence) The companion already evaluates layouts out of sample on dated weeks, so out-of-sample testing is not presented as new.
- (scope_paragraph) The savings are arm-level means over three optimizer seeds at one origin, not an expected saving at other deployments (C-24).

**Forbidden wording.**
- "improves on the companion's out-of-sample saving"
- "better than the companion"
- "twice the companion's saving"
- "about 15% fewer visits"
- "13–15%"
- "what the band costs"

**Sources.**
- `IJSSOL_CSLAP_v1.tex` (sha256 `441f7fd2e2fa…`): line 633 (\subsection{Robustness on unseen weeks}\label{sec:temporal}); line 640 ("The 13.7\% of Table~\ref{tab:industrial} is in sample; on unseen weeks the same method removes 6.6\% and 7.4\%"); line 611 (13.7\% in text); line 595 (13.65 in table tab:industrial); line 634 (split on the recorded delivery date); line 754 (the dated extract behind Table tab:temporal)
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §9.3 lines 460-461 (mean visits per order relative to the incumbent scored on the same future, secondary); §9.2 lines 433-435 (different dated extract)
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §13.3 lines 1196-1201 (column 'vs incumbent')
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): lines 153-154 ("Percentage visit savings from different extracts, horizons and baselines are not directly comparable across papers."); line 74
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): P1 step 2 lines 504-505 (arm-level means and single-run range); P1 step 5 table, row Savings in context, line 557

**Anchor keys:** `ho.visits.incumbent`, `ho.saving.NOM.pct`, `ho.saving.TIGHT.pct`, `ho.saving.HIST_ACT.pct`, `ho.saving.HIST_ACT_T.pct`, `ho.saving.single_run.min.pct`, `ho.saving.single_run.max.pct`.
**Document-value keys:** `comp.saving.heldout.low`, `comp.saving.heldout.high`, `comp.saving.in_sample`, `comp.temporal.section`, `comp.temporal.label`.

**Unit:** pct; visits_per_order. **Denominator:** arm-level means over three optimizer seeds; single-run range over the 12 held-out layouts. **Display rounding (decimals):** `{"pct": 1, "visits_per_order": 3}`.

**Scope boundary.** Held-out campaign ho3_20260913. The companion's in-sample value is its text value 13.7 (IJSSOL_CSLAP_v1.tex:611, :640); its table gives 13.65 (line 595), so any use of the table value needs its own document value (Q-002, Q-015).

**Supersedes:** WRITING_PLAN_20260914.md §1 C5 (line 61) '≈15 % fewer visits'; WRITING_PLAN_20260914.md §3 lines 122-124 'the 13–15 % visit saving'.

## C-14: Synthetic evidence role

**Type:** scope. **Endpoint status:** exploratory.

**Statement.** The two-sided synthetic evidence covers 4 synthetic warehouses, run at the exploratory origin with one seed; the larger upper-only synthetic benchmark is a different campaign under a different rule, and its instance count is never attached to a two-sided statement. The synthetic generator is stationary, so these instances are a control on finite-sample and solver effects, not evidence about robustness to real demand drift, and their historically inactive product sets are empty, so HIST+ACT is the same model as HIST on them.

**Allowed wording.**
- Under the two-sided rule the synthetic evidence consists of 4 warehouses at one origin with one seed.
- On the synthetic instances HIST+ACT reduces to HIST, which is reported as an identity.

**Required qualifiers.**
- (sentence) Synthetic results are exploratory context and are never pooled with the industrial held-out evidence.
- (sentence) Where the inactive set is empty, the equality of HIST+ACT and HIST is an identity, not evidence that activation protection is costless or beneficial.

**Forbidden wording.**
- "29 instances"
- "a 29-instance two-sided benchmark"
- "synthetic evidence of robustness to drift"
- "activation helps on synthetic data"

**Sources.**
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §12.3 lines 1110-1127 (four synthetic warehouses at δ = 0.02); §9.2 items 5-6 lines 880-885 (empty inactive sets; stationary generator)
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §8.3 line 374 (screen subset); §5 lines 114-116 (HIST+ACT reduces to HIST, reported as an identity)
- `reports/horizon_robustness_results/WRITING_PLAN_20260914.md` (sha256 `ffd8157b6b5c…`): line 68 (must not make: 'a 29-instance two-sided benchmark (only 4 ran two-sided)')
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): P1 step 5 table, row Synthetic evidence role, line 558

**Anchor keys:** `ts.synthetic_instances.count`.
**Document-value keys:** none.

**Unit:** count (synthetic warehouses). **Denominator:** distinct synthetic datasets run two-sided (campaign ts_d02_20260912). **Display rounding (decimals):** `{"count": 0}`.

**Scope boundary.** The forbidden '29 instances' applies to two-sided statements; the upper-only benchmark count has no anchor or document value, so the register states no number for it. extra.ts.synthetic_instances.instances is not cited.

**Supersedes:** none.

## C-15: Unused tail

**Type:** disclosure. **Endpoint status:** not_applicable.

**Statement.** The retained industrial stream holds 284,862 complete orders and the held-out window ends at order index 265,025, so 19,837 retained orders after it were used by no solve, score or survey of this study. That tail is shorter than P = 21,874 orders but long enough for a smaller horizon; it is not an approved further test and not an independent warehouse, and the writing process does not read it.

**Allowed wording.**
- The last 19,837 retained orders, after the held-out window, were not used.

**Required qualifiers.**
- (sentence) The count treats 284,862 as the number of retained orders, as its source states (Q-013).

**Forbidden wording.**
- "there is no other deployment segment"
- "no retained orders remain"
- "a second held-out test"
- "independent deployment segment"

**Sources.**
- `reports/horizon_robustness_results/DATA_PROVENANCE.md` (sha256 `d592b49606d2…`): line 14 ("| Complete retained orders | 284,862 |")
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §13 line 1172 ("future [243,151, 265,025)")
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §9.2 lines 430-432 (orders from the held-out origin onward read by no earlier solve, survey, re-scoring or diagnostic)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §2 last row, line 105 ("19,837 retained orders remain after index 265,025, fewer than P but enough for a smaller horizon")
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): P1 step 3 line 531; P1 step 5 table, row Unused tail, line 559; §3 H1 line 130

**Anchor keys:** none.
**Document-value keys:** `prov.stream_end`, `prov.tail_start`, `prov.tail_unused`, `prov.products`.

**Unit:** count (orders). **Denominator:** retained complete orders of the approved export. **Display rounding (decimals):** `{"count": 0}`.

**Scope boundary.** prov.stream_end semantics is 'length' (Q-013), so the computation 284,862 − 265,025 applies without an off-by-one correction.

**Supersedes:** WRITING_EXECUTION_PLAN_REVIEWED_20260914.md §2 row 'There is no other deployment segment' (line 105).

## C-16: Trapped-activation correction

**Type:** derivation. **Endpoint status:** not_applicable.

**Statement.** After the second independent review, the two-sided model's lower activation endpoint was corrected: when every historically inactive product sits at one station, the activation mass cannot be placed elsewhere, so that station's lowest share over the uncertainty set is A_sk rather than (1 − ν)·A_sk. The correction changes no recorded result, because no executed model has a station holding every inactive product: the synthetic inactive sets are empty, and on the industrial case the inactive products span several stations in every layout. The correction is documented in the supplement.

**Allowed wording.**
- The corrected lower activation endpoint changes no recorded result and is documented in the supplement.

**Required qualifiers.**
- (sentence) Zero impact rests on the executed models' inactive-product placement and on the revalidation of every stored certificate under the corrected code recorded in handoff §6.8; neither was re-run during writing.

**Forbidden wording.**
- "the original two-sided model was exact"
- "no correction was needed"
- "the correction improved the results"

**Sources.**
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §6.8 lines 506-521 ("Lower activation endpoint ... When every inactive product sits at station s the mass is trapped there and the lowest share is A_sk ... Zero impact on recorded results")
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §6 Step 2 preflight item 4, lines 380-384
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §8.1 lines 345-348 (original lower rows using (1−ν)·A_sk)
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): P1 step 5 table, row Trapped-activation correction, line 560

**Anchor keys:** none.
**Document-value keys:** none.

**Unit:** none. **Denominator:** every executed two-sided model. **Display rounding (decimals):** `{"none": null}`.

**Scope boundary.** Supplement. The derivation of both endpoints is checked in P3 (derivations A and B); this claim records the correction and its recorded impact only.

**Supersedes:** none.

## C-17: Negative results

**Type:** limitation. **Endpoint status:** not_applicable.

**Statement.** The negative results are classified by the reviewer-first categories. Demonstrated boundary condition: the conditional robust guarantee assumes that the future lies in the uncertainty set, and on the held-out window every returned layout had a station below its lowest modelled share, which shows that the assumption failed there; the sufficient total-variation certificate assumes a product-mix distance within the reserved margin, and every surveyed future window exceeded that margin. Empirical limitation: neither arm without a margin satisfied the band on any held-out seed, and at the exploratory origin a wider band did not bring the scenario arms into compliance, while the mechanism is not isolated. Experimental limitation: scenarios and activation are bundled, there is one held-out origin and one horizon, no λ, δ or ν frontier was run at that origin, and no validated margin rule was obtained. Implementation limitation: every held-out layout is time-capped without proof of optimality, cells with no returned layout within the time limit are not infeasibility, and the earlier minimum-slack diagnostics are logged but not replayable.

**Allowed wording.**
- The departure of the realised future from every arm's modelled set is a demonstrated boundary condition of the conditional guarantee: the assumption is named and the evidence shows where it fails.
- The misses of the arms without a margin are an empirical limitation whose mechanism is not isolated.
- The bundled scenarios and activation, the single held-out origin and the absence of frontiers are experimental limitations.
- Time-capped layouts and non-replayable diagnostics are implementation limitations.

**Required qualifiers.**
- (sentence) Each limitation states what failed, under which conditions, whether its explanation is demonstrated or hypothetical, and which experiment would resolve it; no experiment is run for this paper.
- (sentence) Negative and mixed results are reported as found; no band, activation budget, arm, instance or horizon was changed or removed to improve a table.

**Forbidden wording.**
- "the method fails"
- "robust optimisation fails"
- "proves that historical scenarios cannot protect"
- "a boundary condition of robust optimisation in general"

**Sources.**
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §13.2 lines 1184-1189 (stations outside the modelled set, above/below); §12.2 lines 1102-1107 (δ = 0.03 passes); §9.2 lines 862-897 (known limitations); §1.1 lines 38-42 (six diagnostics not replayable); §13.4 line 1209
- `reports/horizon_robustness_results/tables/drift_survey.csv` (sha256 `60e729006f50…`): every row, column future_tv_within_rho = False
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §5 lines 107-116 (reporting commitments); §7.3 lines 308-311 (six runs not replayable); §9.3 lines 466-468 (what is not tested)
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): P1 step 5 table, row Negative results, line 561

**Anchor keys:** `ho.pass.NOM.count`, `ho.pass.HIST_ACT.count`, `ho.departures.HIST_ACT.s11.below`, `ho.departures.HIST_ACT.s22.below`, `ho.departures.HIST_ACT.s33.below`, `ho.departures.HIST_ACT_T.s11.below`, `ho.departures.HIST_ACT_T.s22.below`, `ho.departures.HIST_ACT_T.s33.below`, `ts.berner.d03.pass.HIST.count`, `ts.berner.d03.pass.HIST_ACT.count`, `drift.holdout.future_tv`.
**Document-value keys:** none.

**Unit:** none (classification). **Denominator:** not applicable. **Display rounding (decimals):** `{"none": null}`.

**Scope boundary.** Categories from .claude/skills/reviewer_first_skill/SKILL_Academic_Manuscript_Architect_and_Critical_Reviewer.md §XII (lines 566-598). No item is classified as a genuine failure; the classification is a judgement open to BCL and SCI-5 review. Details of each item are carried by C-03, C-05, C-08, C-20, C-21, C-24, C-29 and C-31.

**Supersedes:** none.

## C-18: none (first plan C2, corrected by reviewed plan §2)

**Type:** observation. **Endpoint status:** exploratory.

**Statement.** Under the upper-only rule the screening campaign compared the four arms on the synthetic benchmark and on BERNER at one origin with one seed. On the synthetic benchmark the comparison between historical scenarios and tightening is mixed across catalogue-size strata and rests on unequal scored denominators, because the robust arms returned no layout within the time limit in part of the smallest family, so it supports no single ranking of the arms. On BERNER, HIST+ACT satisfied the caps at two of three horizons, and NOM, TIGHT and HIST at none.

**Allowed wording.**
- Under the upper-only rule no single ranking of historical scenarios against tightening holds across the synthetic strata; paired outcomes within matched cells and the non-returned cells are reported together.
- On BERNER under the upper-only rule, HIST+ACT met the caps at two of three horizons and every other arm at none.

**Required qualifiers.**
- (sentence) A cell with no returned layout within the time limit is not infeasibility.
- (sentence) The upper-only study is exploratory and is reported separately from the two-sided campaigns, never pooled with them.
- (sentence) On stationary synthetic data, differences between scenarios and tightening reflect finite-sample and solver behaviour, not robustness to drift.

**Forbidden wording.**
- "historical scenarios do not beat tightening on the benchmark"
- "tightening explains the robustness gain"
- "universal superiority"
- "superior"
- "the smallest instances are infeasible"

**Sources.**
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §10.1 lines 909-920 (returned layouts and passes per arm); §10.3 lines 935-966 (H2 mixed by stratum); §10.4 lines 973-979 (BERNER); §10.6 lines 1005-1008 (non-returns are not infeasibility)
- `reports/horizon_robustness_results/tables/paired_stratum_summary.csv` (sha256 `7772ec24689f…`): upper-only rows, baseline TIGHT, by catalogue-size stratum and horizon
- `reports/horizon_robustness_results/tables/stratum_summary.csv` (sha256 `5162f2c98182…`): upper-only rows by stratum, arm and horizon (scored denominators)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §2 row 'Historical scenarios do not beat tightening on the benchmark', line 103
- `reports/horizon_robustness_plan/PLAN.md` (sha256 `69ce4d643497…`): line 169 (retrospective/exploratory label); lines 277-280 (hypotheses H1-H4)

**Anchor keys:** `uo.berner.pass.NOM.count`, `uo.berner.pass.TIGHT.count`, `uo.berner.pass.HIST.count`, `uo.berner.pass.HIST_ACT.count`.
**Document-value keys:** none.

**Unit:** count (horizons passing). **Denominator:** three BERNER horizons, one seed, one origin; synthetic strata use the instance as unit with scored and non-returned cells stated. **Display rounding (decimals):** `{"count": 0}`.

**Scope boundary.** Campaign screen_20260910. Synthetic stratum values and the synthetic instance count have no anchors and are not stated as numbers here; a display of them needs numbers.json keys first.

**Supersedes:** WRITING_PLAN_20260914.md §1 C2 (line 58); EXPERIMENT_REVIEW_HANDOFF.md §10.3 lines 951-953 'is explained by ordinary tightening'.

## C-19: none (first plan C3, corrected by reviewed plan §2)

**Type:** observation. **Endpoint status:** exploratory.

**Statement.** Under the two-sided rule with δ = 0.02, at the exploratory origin with one seed, TIGHT satisfied the band at all three BERNER horizons, HIST+ACT at one, and HIST and NOM at none. Summed over the three horizons the misses comprised 0 cap and 3 floor breaches for HIST+ACT and 1 cap and 8 floor breaches for HIST, so the scenario arms missed mostly, but not only, below the floor. In every two-sided BERNER cell the realised future also fell below the lowest modelled share at some station; leaving the modelled set and breaching the band are different metrics.

**Allowed wording.**
- At the exploratory origin TIGHT satisfied the two-sided band at all three BERNER horizons, HIST+ACT at one, and HIST and NOM at none.
- The misses of the scenario arms included cap breaches as well as floor breaches.

**Required qualifiers.**
- (sentence) Exploratory: the two-sided policy was fixed before its solves but after the same futures had been examined under the upper-only rule.
- (sentence) The three horizons share one origin and are not replicates.

**Forbidden wording.**
- "misses are downward"
- "robust-arm misses are small and downward"
- "three replicates"
- "independent confirmation"
- "TIGHT is the method"

**Sources.**
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §12.2 lines 1084-1108; §12.5 items 1 and 5, lines 1145 and 1149; §12.6 lines 1155, 1160 and 1161 (downward departures in every two-sided BERNER cell)
- `reports/horizon_robustness_results/tables/two_sided_novelty_survey.csv` (sha256 `9ee2156215fa…`): BERNER two-sided rows (departures below the lowest modelled share)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §2 row 'Robust arms' misses are downward', line 102
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): §1 F12 line 75

**Anchor keys:** `ts.berner.d02.pass.NOM.count`, `ts.berner.d02.pass.TIGHT.count`, `ts.berner.d02.pass.HIST.count`, `ts.berner.d02.pass.HIST_ACT.count`, `ts.berner.d02.HIST_ACT.cap_breaches_total`, `ts.berner.d02.HIST_ACT.floor_breaches_total`, `ts.berner.d02.HIST.cap_breaches_total`, `ts.berner.d02.HIST.floor_breaches_total`.
**Document-value keys:** `pred.twosided.delta_primary`.

**Unit:** count (horizons passing; breaches). **Denominator:** three BERNER horizons at the exploratory origin, one seed. **Display rounding (decimals):** `{"count": 0}`.

**Scope boundary.** Campaign ts_d02_20260912, BERNER only. The incumbent's two-sided pass count at the exploratory origin is not anchored and is not stated; add an anchor before any use.

**Supersedes:** WRITING_PLAN_20260914.md §1 C3 (line 59) 'robust-arm misses are small (≤ 0.41 pp) and downward'.

## C-20: none (first plan C4)

**Type:** observation. **Endpoint status:** exploratory.

**Statement.** At the exploratory origin on BERNER, with each δ a separately optimised model and one seed: with δ of three percentage points TIGHT satisfied the band at all three horizons and NOM, HIST and HIST+ACT at none; with δ of one percentage point TIGHT satisfied it at one horizon and the other arms at none. Widening the band did not bring the scenario arms into compliance, and the narrower band was met once.

**Allowed wording.**
- A wider band did not make the scenario arms comply at the exploratory origin; only TIGHT satisfied the band at every horizon with δ of three percentage points.

**Required qualifiers.**
- (sentence) Each δ is a different model and a different solve, so a wider band does not imply better future compliance, and the δ values form a sampled response, not a frontier.
- (sentence) No lower bound was certified, so no band is shown unattainable, and no λ frontier was run.
- (sentence) Exploratory, one seed at one origin, and never pooled with the held-out evidence.

**Forbidden wording.**
- "Pareto frontier"
- "optimal frontier"
- "wider bands improve compliance"
- "the band is unattainable"
- "infeasible band"

**Sources.**
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §12.2 lines 1102-1108 (passes by δ); §12.5 items 2-3, lines 1146-1147; §12.6 lines 1158-1159 and 1164
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §8.2 lines 363-368 (δ = 0.02 primary; 0.01 aspiration; 0.03 fallback; no headline moves)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): lines 107-111 (not an optimal Pareto frontier); lines 451-453 (separately optimized models; no monotone compliance)

**Anchor keys:** `ts.berner.d01.pass.NOM.count`, `ts.berner.d01.pass.TIGHT.count`, `ts.berner.d01.pass.HIST.count`, `ts.berner.d01.pass.HIST_ACT.count`, `ts.berner.d03.pass.NOM.count`, `ts.berner.d03.pass.TIGHT.count`, `ts.berner.d03.pass.HIST.count`, `ts.berner.d03.pass.HIST_ACT.count`.
**Document-value keys:** none.

**Unit:** count (horizons passing). **Denominator:** three BERNER horizons per δ at the exploratory origin, one seed. **Display rounding (decimals):** `{"count": 0}`.

**Scope boundary.** Campaigns ts_b01_20260912 and ts_b03_20260912. The δ values of one and three percentage points have no anchor or document value and are written in words (CAMPAIGN_PREDECLARATION.md:363-366).

**Supersedes:** WRITING_PLAN_20260914.md §1 C4 (line 60).

## C-21: none (first plan C6, set-coverage part)

**Type:** observation. **Endpoint status:** predeclared_secondary.

**Statement.** On the held-out window every returned layout had stations whose realised share fell below the lowest share its modelled scenario set allowed: two to four stations for HIST+ACT-T, three or four for HIST+ACT, and 12 or 13 for NOM and TIGHT, whose modelled set is the single pooled-history point. Above the highest modelled share there were at most three such stations for the scenario arms and 11 or 12 for NOM and TIGHT. A realised share outside a station's modelled range shows that the future lay outside that arm's uncertainty set.

**Allowed wording.**
- The realised future lay outside the uncertainty set of every returned held-out layout, mostly in the downward direction for the scenario arms.

**Required qualifiers.**
- (sentence) Staying inside every station's modelled range does not prove that the future lay inside the uncertainty set; only a departure proves non-membership.
- (sentence) Leaving the modelled set is not a band violation: the margin arms left their sets and still satisfied the band.
- (scope_paragraph) Counts over three optimizer seeds at one origin (C-24).

**Forbidden wording.**
- "the future stayed inside the uncertainty set"
- "compliance comes from the reserved margin, not from set membership"
- "compliance rests on within-station cancellation"
- "proves that historical scenarios cannot protect"

**Sources.**
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §13.2 lines 1182-1189 (stations outside the modelled set above/below per seed); §13.3 lines 1196-1201
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §9.3 lines 461-462 (departures from the modelled set in both directions, secondary)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §6 Step 3 lines 454-456 (outside an envelope proves non-membership; inside every envelope does not prove membership)
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md` (sha256 `b8ffb5df2bf0…`): §5 line 65 (station-direction envelopes expose departures but do not certify membership)

**Anchor keys:** `ho.departures.NOM.s11.below`, `ho.departures.NOM.s22.below`, `ho.departures.NOM.s33.below`, `ho.departures.TIGHT.s11.below`, `ho.departures.TIGHT.s22.below`, `ho.departures.TIGHT.s33.below`, `ho.departures.HIST_ACT.s11.below`, `ho.departures.HIST_ACT.s22.below`, `ho.departures.HIST_ACT.s33.below`, `ho.departures.HIST_ACT_T.s11.below`, `ho.departures.HIST_ACT_T.s22.below`, `ho.departures.HIST_ACT_T.s33.below`, `ho.departures.NOM.s11.above`, `ho.departures.NOM.s22.above`, `ho.departures.NOM.s33.above`, `ho.departures.TIGHT.s11.above`, `ho.departures.TIGHT.s22.above`, `ho.departures.TIGHT.s33.above`, `ho.departures.HIST_ACT.s11.above`, `ho.departures.HIST_ACT.s22.above`, `ho.departures.HIST_ACT.s33.above`, `ho.departures.HIST_ACT_T.s11.above`, `ho.departures.HIST_ACT_T.s22.above`, `ho.departures.HIST_ACT_T.s33.above`.
**Document-value keys:** none.

**Unit:** count (stations). **Denominator:** 24 evaluated stations per layout; 12 held-out layouts. **Display rounding (decimals):** `{"count": 0}`.

**Scope boundary.** Held-out campaign ho3_20260913. Exploratory-origin departures are in C-19.

**Supersedes:** WRITING_PLAN_20260914.md §1 C6 (line 62) 'so compliance rests on within-station cancellation, not on set membership'; EXPERIMENT_REVIEW_HANDOFF.md §12.6 line 1161 'its compliance comes from the reserved margin, not from set membership'.

## C-22: none (first plan C7, corrected by reviewed plan §2)

**Type:** derivation. **Endpoint status:** not_applicable.

**Statement.** For a fixed layout, the largest and the smallest share of a station over the declared historical-hull-and-activation uncertainty set are attained at finitely many scenario vertices and activation endpoints, including the trapped-activation case for the smallest share, so the robust rows are finitely many linear rows. Multiplying each row by its integer scenario total, and the activation endpoint also by the denominator of ν, gives integer-count rows with floor and ceiling thresholds that define the same set of layouts. Exactness rests on this derivation; agreement between the solvers, the independent exact validator and the vertex oracle supports the implementation, not the mathematics.

**Allowed wording.**
- The robust counterpart is an exact finite restatement over the uncertainty set, and its integer-count form defines the same feasible layouts.

**Required qualifiers.**
- (sentence) A finite-precision solver return is not an exact certificate; the stored layouts were revalidated in exact rational arithmetic by code that shares nothing with the solvers.
- (sentence) Finite rows, integer rescaling, safety margins, scenario hulls and chronological splits are established techniques and are not presented as new.

**Forbidden wording.**
- "validated by the validator, therefore exact"
- "a new exact optimizer"
- "novel robust counterpart"
- "newly invented"
- "integer rescaling is new"

**Sources.**
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md` (sha256 `b8ffb5df2bf0…`): §4 lines 41-53 (exact finite robust counterpart, upper side); §10 lines 103-142 (integer-count restatement defines the same set)
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §6.6 lines 413-465; §6.8 lines 506-521 (lower endpoint, vertex oracle); §9.1 lines 839-846 (exact revalidation and scoring)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §2 row 'Exact counterpart is validated by a validator', line 104; §3 lines 132-135 (not newly invented techniques)

**Anchor keys:** none.
**Document-value keys:** none.

**Unit:** none. **Denominator:** not applicable. **Display rounding (decimals):** `{"none": null}`.

**Scope boundary.** The two-sided lower endpoint and edge cases are derived in P3 (preflight items 4-5); MATHEMATICAL_SCOPE.md §4 states the upper side only. If P3 derivations disagree, this claim is routed back.

**Supersedes:** WRITING_PLAN_20260914.md §1 C7 (line 63) 'is validated by an independent exact validator'.

## C-23: none (first plan C8)

**Type:** interpretation. **Endpoint status:** not_applicable.

**Statement.** Conditional robust feasibility and observed future compliance are different quantities. If a layout satisfies every finite robust row and the realised future product mix lies in the declared uncertainty set, every station respects its band; nothing in the study establishes that a future lies in that set or gives a probability of future compliance, and observed compliance on the held-out window is one realisation scored for three optimizer seeds.

**Allowed wording.**
- The model provides conditional robust feasibility for its uncertainty set under the stated assumptions; it does not guarantee compliance on future orders.

**Required qualifiers.**
- (sentence) Robust feasibility is stated only as conditional on the declared uncertainty set and its assumptions.

**Forbidden wording.**
- "guarantees future compliance"
- "future-feasibility guarantee"
- "universal future reliability"
- "reliability probability"
- "95% coverage"
- "robust to any future demand"
- "operationally certified"
- "λ = 0.5 is certified"

**Sources.**
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md` (sha256 `b8ffb5df2bf0…`): §4 line 53 (the guarantee and what it is not); §6 lines 69-71 (no universal guarantee)
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §13.4 line 1209; §9.2 item 10 lines 895-897
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §6 Step 4 lines 489-492 (allowed: conditional robust feasibility for U; forbidden: universal future reliability, calibrated automatic margin rule, new exact optimizer, proven optimal protection cost, independent-demand replication from three seeds)
- `reports/horizon_robustness_results/WRITING_PLAN_20260914.md` (sha256 `ffd8157b6b5c…`): §1 C8 line 64; 'must not make' lines 66-67

**Anchor keys:** none.
**Document-value keys:** none.

**Unit:** none. **Denominator:** not applicable. **Display rounding (decimals):** `{"none": null}`.

**Scope boundary.** Applies to every arm and campaign.

**Supersedes:** none.

## C-24: none (INV-5 scope-once paragraph)

**Type:** scope. **Endpoint status:** not_applicable.

**Statement.** The held-out evidence is one industrial warehouse, one deployment origin at order index 243,151, one horizon of n = 21,874 complete orders and three optimizer seeds under one frozen policy with δ = 0.02, ν = 0.01 and λ = 0.5. The seeds describe optimizer variability at that origin, not variation in future demand, so no significance test or interval is computed and nothing is claimed about other origins, horizons or warehouses. The study cannot separate historical scenarios from activation, cannot isolate the margin from solver and layout effects, and ran no λ, δ or ν frontier at the held-out origin.

**Allowed wording.**
- One held-out origin and three optimizer seeds.
- Seeds are averaged within the origin and never counted as independent futures.

**Required qualifiers.**
- (scope_paragraph) Stated once at the head of Results and once in Limitations; the abstract and the conclusion each carry one qualifier clause.
- (sentence) The held-out results are reported in their own section, with the incumbent as same-future context, and are never pooled with the exploratory campaigns.

**Forbidden wording.**
- "replicates"
- "independent futures"
- "statistically significant"
- "confidence interval"
- "p-value"
- "Wilcoxon"
- "generalises to other warehouses"
- "independent-demand replication"

**Sources.**
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §9.2 lines 427-443; §9.3 lines 464-468 ("Three seeds measure optimiser variability, not demand variability"; what is not tested); §9.4 lines 472-475
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §13.4 line 1209; §13.3 line 1203 (separate contributions not isolated)
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): INV-5 scope-once lines 369-373; INV-4 lines 365-366 (no significance tests or intervals over three seeds)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §5 override 4 lines 289-292

**Anchor keys:** none.
**Document-value keys:** `pred.holdout.origin`, `pred.holdout.n`, `pred.holdout.delta`, `pred.holdout.nu`, `pred.holdout.lambda`.

**Unit:** count; share; fraction. **Denominator:** one origin, one horizon, three optimizer seeds, four arms. **Display rounding (decimals):** `{"count": 0, "share": 2, "fraction_nu": 2, "fraction_lambda": 1}`.

**Scope boundary.** The reviewed plan's allowed phrase 'optimizer seed replication' (line 490) is not used: INV-5, which has precedence, keeps replication vocabulary out of the paper's own voice.

**Supersedes:** none.

## C-25: none (first plan C1 boundary; Q-006)

**Type:** premise. **Endpoint status:** not_applicable.

**Statement.** The approved industrial export has the header PRODUCT;ORDER;QTY;STATION;BOX_ID and no date column, so the protocol orders complete orders by their numeric order identifiers. That this order matches the creation, release, picking and delivery sequence on site is an assumption, and whether dates exist operationally at the site is left for author confirmation.

**Allowed wording.**
- The export carries no dates, so horizons are counted in complete orders taken in order-identifier sequence.

**Required qualifiers.**
- (sentence) Chronology is assumed from order identifiers; sorting does not establish it.
- (sentence) The dated alternative is deferred, not disproved, and the study does not show that dates are unnecessary for operational decisions in general.

**Forbidden wording.**
- "dates are unnecessary for every operational decision"
- "the stream is chronological"
- "the dated approach is inferior"
- "the dated alternative is disproved"

**Sources.**
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): §1 F9 line 72 ("The export header is PRODUCT;ORDER;QTY;STATION;BOX_ID, with no date column")
- `reports/horizon_robustness_results/DATA_PROVENANCE.md` (sha256 `d592b49606d2…`): line 27 ("This checks the implementation's sequence, not the operational truth of order-ID chronology.")
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §9.2 item 8 lines 891-892 ("Order-ID chronology is an assumption.")
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md` (sha256 `b8ffb5df2bf0…`): §2 line 27 (dates unnecessary to define the next n complete orders; necessary for calendar horizons, arrival rates or date-specific behaviour)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): lines 16-19 (not evidence that dates are unnecessary for every operational decision; dated alternative deferred, not disproved); line 196 (chronology assumed)

**Anchor keys:** none.
**Document-value keys:** none.

**Unit:** none. **Denominator:** not applicable. **Display rounding (decimals):** `{"none": null}`.

**Scope boundary.** Q-006 resolution (plan F9). On-site dates are % AUTHOR-CONFIRM.

**Supersedes:** none.

## C-26: none (reviewed plan §3 data contract; Q-001)

**Type:** premise. **Endpoint status:** not_applicable.

**Statement.** The industrial instance keeps the shared loader's retained catalogue of 21,874 products in 21,874 slots and 24 evaluated stations, with 5,899 frozen and 15,975 movable products. The companion reports 26 stations and evaluates the same 24, so the two excluded stations are not a new exclusion; they and their products enter neither workloads, visits nor denominators. Every included product occupies a slot even with zero historical workload, no new product arrives in a future window, and frozen products keep their stations while their changing demand still counts in workloads and visits.

**Allowed wording.**
- We use the 24 evaluated stations and the 21,874 products of the companion's industrial case, 5,899 of them frozen.

**Required qualifiers.**
- (sentence) Industrial workload counts distinct retained product-order pairs, not units ordered or processing hours.
- (sentence) The catalogue is a closed snapshot: unknown new products are outside scope, and an export cannot prove that never-ordered physical inventory is complete.

**Forbidden wording.**
- "we exclude two stations"
- "26 evaluated stations"
- "the catalogue is the complete physical inventory"

**Sources.**
- `reports/horizon_robustness_results/DATA_PROVENANCE.md` (sha256 `d592b49606d2…`): lines 11-13 (21,874 / 21,874; 24 stations; 5,899 / 15,975); line 21 (excluded stations enter neither catalogue, workloads, visits nor denominators); line 27 (one-product freeze edge case)
- `IJSSOL_CSLAP_v1.tex` (sha256 `441f7fd2e2fa…`): line 569 ("21{,}874 products and 26 picking stations. We evaluate 24 stations;"); lines 577-579 (15,975 reassignable, 5,899 fixed; all products remain in evaluation and workloads)
- `IJSSOL_CSLAP_v1_supplementary.tex` (sha256 `e5a65a053a8a…`): lines 516-519 (products, free to relocate, frozen, stations of which evaluated)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §3 data contract lines 178-191
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md` (sha256 `b8ffb5df2bf0…`): §1 lines 7-9 (closed catalogue; workload counts distinct product-order pairs)

**Anchor keys:** none.
**Document-value keys:** `prov.products`, `prov.stations_evaluated`, `prov.fixed`, `prov.movable`, `comp.products`, `comp.stations.reported`, `comp.stations.evaluated`.

**Unit:** count. **Denominator:** retained industrial system. **Display rounding (decimals):** `{"count": 0}`.

**Scope boundary.** Q-001 resolution: the paper says 'the 24 evaluated stations'. Synthetic workload keeps line multiplicity (MATHEMATICAL_SCOPE.md:9).

**Supersedes:** WRITING_PLAN_20260914.md §2 lines 100-101 'the extension's retained system has 24 after two exclusions'.

## C-27: none (first plan C1 boundary; reviewed plan §3)

**Type:** assumption. **Endpoint status:** not_applicable.

**Statement.** The industrial catalogue, incumbent layout, slot capacities, freeze mask and order-retention rule are reconstructed by the shared loader from the whole export and assumed known before deployment; that reconstruction depends on future orders, so the experiment is snapshot-conditioned and retrospective. Conditional on the snapshot, targets, training counts and scenarios use only the prefix before the origin, the targets are frozen at the origin and never recomputed from the scored future or from the incumbent's future profile, and each layout is written before its future segment is scored.

**Allowed wording.**
- Conditional on an assumed pre-known snapshot of the catalogue, incumbent and freeze mask, all estimation uses only the orders before the origin.

**Required qualifiers.**
- (sentence) Prefix-only estimation conditional on the snapshot is not evidence that the metadata were available at each historical origin.

**Forbidden wording.**
- "prospectively verified metadata"
- "prospective reconstruction"
- "no future information entered the pipeline"
- "fully prospective"

**Sources.**
- `reports/horizon_robustness_results/DATA_PROVENANCE.md` (sha256 `d592b49606d2…`): line 5 (assumed pre-known, not prospectively verified; future-dependent retention acknowledged)
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md` (sha256 `b8ffb5df2bf0…`): §8 line 85 (retrospective snapshot-conditioned experiment)
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §9.1 lines 854-856 (layout written before scoring); §9.2 item 7 lines 886-890
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §3 lines 192-200 (assumed pre-known metadata; freeze targets, never retarget)

**Anchor keys:** none.
**Document-value keys:** none.

**Unit:** none. **Denominator:** not applicable. **Display rounding (decimals):** `{"none": null}`.

**Scope boundary.** Industrial case. Synthetic instances have no snapshot reconstruction.

**Supersedes:** none.

## C-28: none (reviewed plan §3 horizon bullets)

**Type:** definition. **Endpoint status:** not_applicable.

**Statement.** Horizons are counted in complete orders. The exploratory grid n ∈ {⌈P/2⌉, P, 2P}, with P the catalogue size, is a declared sensitivity design, not an operationally optimal horizon, and historical scenario blocks use the same n as the scored future. At one origin, where the larger horizon is an integer multiple of the smaller, the larger horizon's uncertainty set is contained in the smaller one's; this constrains the model but implies nothing monotone about realised future compliance or about time-capped returned costs. The held-out deployment used n = P only.

**Allowed wording.**
- The horizon grid is a declared sensitivity design, not a recommended planning interval.

**Required qualifiers.**
- (sentence) Nesting holds only for matched horizons that are integer multiples at a common origin; it does not transfer to other horizons or origins.

**Forbidden wording.**
- "optimal horizon"
- "universal planning interval"
- "compliance improves with n"
- "monotone future feasibility"

**Sources.**
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md` (sha256 `b8ffb5df2bf0…`): §2 line 27 (declared sensitivity design; matched n); §9 lines 91-99 (U_large subset of U_small; no monotone future feasibility)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §3 lines 204-206
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §2 lines 55-57 (three declared horizons); §9.2 lines 436-439 (held-out horizon n = P only)

**Anchor keys:** none.
**Document-value keys:** none.

**Unit:** none. **Denominator:** not applicable. **Display rounding (decimals):** `{"none": null}`.

**Scope boundary.** The numeric value of P is carried by C-26 and C-07.

**Supersedes:** none.

## C-29: none (study-design accounting; Q-009; first plan 'must not make' list)

**Type:** disclosure. **Endpoint status:** not_applicable.

**Statement.** The analysis uses six non-superseded campaigns and excludes four superseded directories, which were never analysed. Across the analysed campaigns 464 rows were authorized: 412 returned a layout that was scored on its future horizon and 52 returned no allocation, and the scored rows hold 188 distinct layouts. A row with no layout within its time limit is not infeasibility. The earlier minimum-slack diagnostics were logged without saving their layouts, so they are reported only as logged results.

**Allowed wording.**
- Of 464 authorized rows, 412 were scored and 52 returned no allocation.
- The scored rows contain 188 distinct layouts.

**Required qualifiers.**
- (sentence) Scored cases and distinct layouts are different counts: a layout shared by several scored rows is counted once.
- (sentence) Optimization failure, independent-validation failure and future-window violation are separate quantities and are never pooled.

**Forbidden wording.**
- "413 layouts"
- "results from superseded directories"
- "the min-slack diagnostics show"
- "replayed diagnostics"
- "infeasible cells"

**Sources.**
- `reports/horizon_robustness_results/analysis_audit.md` (sha256 `b8a7ed083178…`): lines 13-20 (six campaigns included); line 22 (four excluded as superseded); lines 28-36 (464 authorized, 52 no allocation, 412 scored); lines 44-46 (status detail)
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 `9e122abb0eb2…`): §3 lines 86-89 (denominators; superseded directories excluded); §5 lines 107-111; §7.3 lines 308-311 (six runs logged, not replayable)
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §1.1 lines 38-42
- `reports/horizon_robustness_results/tables/case_frame.csv` (sha256 `0e9dc1f5f4c8…`): all 464 rows; scored rows' layout_hash (188 distinct)
- `reports/horizon_robustness_results/WRITING_PLAN_20260914.md` (sha256 `ffd8157b6b5c…`): lines 66-70 (must not make: non-replayable diagnostics beyond 'logged'; superseded directories)

**Anchor keys:** `acct.campaigns.analysed`, `acct.campaigns.superseded`, `acct.rows.authorized`, `acct.rows.scored`, `acct.rows.no_allocation`, `acct.layouts.scored`.
**Document-value keys:** `audit.rows.authorized`, `audit.rows.scored`, `audit.rows.no_allocation`.

**Unit:** count. **Denominator:** authorized manifest rows of the six analysed campaigns. **Display rounding (decimals):** `{"count": 0}`.

**Scope boundary.** Q-009 resolution: acct.layouts.scored counts distinct layout_hash among scored rows. The reviewed plan's 413 matches no stored population and is recorded in interpretation_errata.md. The extra.* layout counts are context only.

**Supersedes:** WRITING_EXECUTION_PLAN_REVIEWED_20260914.md line 60 '413 layouts'.

## C-30: none (P5b mandatory reader question on practice)

**Type:** recommendation. **Endpoint status:** not_applicable.

**Statement.** For a site that wants fewer station visits while keeping every station's workload share inside a band, the tested policy is to optimise inside a band tightened to reserve part of the policy band, and to examine the station-level variation in the site's own history against that reserve before adopting a layout. On this case the reserve of one percentage point was smaller than the incumbent's largest historical block deviation, and the tightened layouts still satisfied the band on the held-out window; the policy is untested at other sites, origins and reserve sizes.

**Allowed wording.**
- A practitioner can reserve part of the band during optimisation and check the reserve against the station-level variation in the site's own history, treating the result as a policy tested on one case, not a validated rule.

**Required qualifiers.**
- (sentence) This is a policy tested on one case that still needs validation, not a calibrated or automatic margin rule.
- (sentence) The incumbent's historical variation belongs to its own layout, so the check informs but does not set the reserve for an optimised layout.

**Forbidden wording.**
- "empirically calibrated margin rule"
- "automatic margin calibration"
- "set λ = 0.5"
- "reserve one percentage point at every site"
- "operationally certified"
- "the method to adopt"

**Sources.**
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (sha256 `c6b9746b70f4…`): P5b step 2 lines 812-813 ("A tested policy still needing validation (§XIV): reserve part of the band, and check station-level history against the reserve before adopting a layout.")
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §6 Step 4 lines 490-492 (forbidden: an empirically calibrated automatic margin rule)
- `reports/horizon_robustness_results/tables/dispersion_survey.csv` (sha256 `74d52002a50f…`): row BERNER, origin 199403, n = 21874 (file line 90), column max_abs_pp
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §13.2 lines 1187 and 1189 (TIGHT and HIST+ACT-T pass on every seed)

**Anchor keys:** `ho.pass.TIGHT.count`, `ho.pass.HIST_ACT_T.count`, `disp.explor.n_P.max_abs`.
**Document-value keys:** none.

**Unit:** none. **Denominator:** one case, one held-out origin, three optimizer seeds. **Display rounding (decimals):** `{"none": null}`.

**Scope boundary.** Recommendation; P4:G1 forbids a contribution resting only on this claim. Wording is subject to SCI-5 if disputed.

**Supersedes:** none.

## C-31: none (first plan C6, certificate part; reviewed plan §3 contribution 4)

**Type:** observation. **Endpoint status:** additional_descriptive.

**Statement.** A station share can move from its pooled-history value by at most the total-variation distance between the future product mix and pooled history, so a layout inside the tightened band on pooled history stays inside the policy band on any future within the reserved margin of that history. This sufficient condition did not hold on any surveyed window: the held-out product mix lay at a distance of 0.195 from pooled history against a reserved margin of one percentage point, and the stored distances of the futures scored at the exploratory origin also exceed that margin. The margin arms nevertheless satisfied the band on the held-out window, which is consistent with product-level changes cancelling within stations but does not establish it.

**Allowed wording.**
- The product-level total-variation certificate does not apply on these windows: the held-out distance of 0.195 is many times the reserved margin.

**Required qualifiers.**
- (sentence) The failure of a sufficient condition does not establish any particular alternative margin rule.
- (sentence) These distances are ex post diagnostics, labelled as such and never used to choose a parameter.

**Forbidden wording.**
- "the TV bound is too loose, so margins must come from station dispersion"
- "compliance rests on cancellation"
- "the certificate is useless in general"

**Sources.**
- `tools/horizon_robustness/drift_survey.py` (sha256 `fcf8168967ed…`): lines 3-10 (|r_s(x, q) − r_s(x, qH)| <= TV(q, qH); TIGHT reserves rho = lambda * delta)
- `reports/horizon_robustness_results/tables/drift_survey.csv` (sha256 `60e729006f50…`): rows BERNER (file lines 14-16) and BERNER@holdout (line 17), columns future_tv_ex_post, reserved_margin_rho and future_tv_within_rho
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` (sha256 `5b39596c024a…`): §12.6 line 1162 (TV reading valid but vacuous here; rejected closing sentences in interpretation_errata.md)
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (sha256 `1118dea21c6d…`): §3 line 131 (contribution 4: failure of a particular sufficient TV certificate); §2 line 100

**Anchor keys:** `drift.holdout.future_tv`, `drift.holdout.hist_tv_max`.
**Document-value keys:** none.

**Unit:** tv. **Denominator:** one held-out window and the futures scored at the exploratory origin. **Display rounding (decimals):** `{"tv": 3}`.

**Scope boundary.** Exploratory-origin distances have no anchors and are not written as numbers. The reserved margin is λδ at the primary two-sided policy, written in words.

**Supersedes:** WRITING_PLAN_20260914.md §1 C6 (line 62), total-variation part.
