# Interpretation errata (P1 step 6)

Built by general-purpose/opus, dispatch seq 40. The protected sources are left unchanged. Each entry records a reading this register rejects or restricts, with its locator, the text quoted verbatim, the reason, and the register claim that replaces it. Numbers used to reject a reading name their anchor or document-value key.

Status labels:
- **REJECTED**: the paper must not use the reading.
- **RESTRICTED**: the reading is correct only with the qualification stated.
- **UNRECONCILED**: two documents disagree, and the register makes no claim until the disagreement is settled.

The required entries are E-01 to E-04. The other entries record further rejected wordings found while building the register.

---

## E-01 Handoff §8: "None of these launches a solver" (REJECTED)

- **Locator:** `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md:696-697`, against `tests/horizon_robustness/test_cplex.py:67`.
- **Rejected text:** "**None of these launches a solver**; the analysis path never imports an optimizer."
- **Why:** the command block that follows runs `tests.horizon_robustness.test_cplex` (handoff line 706). That test calls the native solver:
  - `test_cplex.py:64` loops over the arms `("NOM", "TIGHT", "HIST", "HIST+ACT")`;
  - `test_cplex.py:67` reads `result = solve(candidate, time_limit=5)`.

  At least one listed command therefore launches CPLEX (plan F6, `WRITING_ORCHESTRATION_PLAN_20260914.md:69`).
- **Replacing claim:** none. The register makes no claim about test commands. `W/evidence/verification_inventory.md` records the correction, and no test is run in this writing run (H1).

## E-02 Handoff §13.3: "The held-out window was not an easy one" (REJECTED)

- **Locator:** `EXPERIMENT_REVIEW_HANDOFF.md:1205`.
- **Rejected text:** "**The held-out window was not an easy one.** Measured only after the campaign had scored it, its product mix sits 0.195 from the pooled history it was scored against in total variation, against a historical block maximum of 0.194 and mean 0.171 over 11 blocks (`tables/drift_survey.csv`, row `BERNER@holdout`): drift at the top of the historical range, not below it."
- **Why:** `drift_survey.py:13-15` measures each historical block against the pooled history of the same prefix, so every block is inside its own reference. The held-out future is not inside its reference. Writing w for the block mass fraction:
  - TV(block, pooled) = (1 − w)·TV(block, rest) (Q-003).
  - The stored ordering reverses once w > w* = 1 − hist_tv_max/future_tv ≈ 0.0028 (`drift.holdout.w_star`).
  - Taking w by order count gives w ≈ 0.09 (`drift.holdout.w_order_count`), and the like-for-like historical maximum is about 0.214 (`drift.holdout.hist_tv_max.like_for_like`), above the held-out 0.195 (`drift.holdout.future_tv`).

  Two further problems:
  - total-variation distance is product-mix change, not evidence that station shares were hard to hold;
  - "not an easy one" asserts a difficulty the evidence does not measure.

  Q-008 resolved the decisive test as w_greater_than_w_star.
- **Replacing claim:** C-06.

## E-03 Handoff §12.6: compliance rests on cancellation; margin rule from station-level dispersion (REJECTED)

- **Locator:** `EXPERIMENT_REVIEW_HANDOFF.md:1162`, last two sentences.
- **Rejected text:** "Compliance therefore rests on cancellation across the thousands of products inside a station, which the station-level dispersion survey measures (about 1.7 points at most), not on the product-level bound (`tables/drift_survey.csv`). Any date-free margin rule has to be predeclared from station-level dispersion."
- **Why:**
  1. The failure of a sufficient product-level certificate does not establish any particular alternative rule. The reviewed plan calls this a non sequitur (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:100`).
  2. "Rests on cancellation" is asserted, not shown. The evidence is only consistent with cancellation.
  3. "About 1.7 points at most" is the in-reference value. `dispersion_survey.py:10-13` measures each block against a pooled share that contains it. On the exploratory prefix the stored values are 1.70 at n = P/2 and 1.63 at n = P (`disp.explor.n_half.max_abs`, `disp.explor.n_P.max_abs`). Against the rest of the history they are about 1.80 and 1.83 (the `.like_for_like` keys).
  4. The incumbent's dispersion belongs to its own layout and does not calibrate an optimised layout's margin.

  The first sentence of line 1162, the valid total-variation bound, is kept.
- **Replacing claims:** C-08 (margin rule) and C-31 (certificate).

## E-04 Reviewed plan line 60: "413 layouts" (REJECTED; both numbers shown)

- **Locator:** `WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:60`.
- **Rejected text:** "These are checks of stored evidence, not a fresh replay of all 413 layouts or a"
- **Why:** no stored population has 413 members (Q-009).
  - The reviewed plan states 413 (document value `reviewed.layouts.count`).
  - The audit states 412 scored rows (`analysis_audit.md:35`, document value `audit.rows.scored`; anchor `acct.rows.scored`).
  - The scored rows hold 188 distinct layouts (anchor `acct.layouts.scored`, distinct `layout_hash` among scored rows; both independent anchor computations agree).
  - Context only, never traced: 189 distinct solves and 190 layouts counted per campaign (`extra.acct.layouts.scored.distinct_solve_key`, `extra.acct.layouts.scored.per_campaign_sum`).

  The paper states 412 scored cases and, where layouts are named, 188 distinct layouts.
- **Replacing claim:** C-29.

## E-05 Handoff §13.3: "REPLICATED." (REJECTED)

- **Locator:** `EXPERIMENT_REVIEW_HANDOFF.md:1193`.
- **Rejected text:** "TIGHT passes ±2 at n = P on the held-out future for 3 of 3 seeds. Predeclared threshold: at least two of three. **REPLICATED.**"
- **Why:** INV-5 forbids "replicated" in the paper's own voice.
  - The held-out origin belongs to the same order stream, and its training prefix contains the exploratory origin's data and scored futures.
  - The predeclared label "Replication endpoint" (`CAMPAIGN_PREDECLARATION.md:456`) may be quoted once, immediately followed by that qualifier.

  The pass count itself (`ho.pass.TIGHT.count`) stands.
- **Replacing claim:** C-02.

## E-06 Handoff §13.3: "the margin decides the pass", "a cost-protection trade-off" (REJECTED)

- **Locator:** `EXPERIMENT_REVIEW_HANDOFF.md:1203`.
- **Rejected text:** "So the margin decides the pass; the scenarios buy fidelity to the historical shares at a visit cost: a cost-protection trade-off, not evidence that scenario protection is useless."
- **Why:**
  - "Decides" states a causal law. The design is a two-factor comparison at one origin under equal configured budgets, and it does not isolate the margin from solver and layout effects (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:98`).
  - "Cost-protection trade-off", read as a cost of protection, would treat time-capped returned layouts as optima. Every held-out solve reports a gap of about 0.985 (`ho.gap.*`).

  The descriptive observation stands: smaller largest deviation at a higher visit count.
- **Replacing claims:** C-03 (pass pattern), C-01 (deviation and visits), C-05 (returned layouts).

## E-07 Handoff §12.6: "its compliance comes from the reserved margin, not from set membership" (REJECTED)

- **Locator:** `EXPERIMENT_REVIEW_HANDOFF.md:1161`.
- **Rejected text:** "and TIGHT passes ±2 regardless: its compliance comes from the reserved margin, not from set membership."
- **Why:** causal attribution from exploratory cells with one seed and one origin. The departure counts show that the future left the modelled set, and that leaving the set is not a band violation. They do not show where compliance comes from.
- **Replacing claims:** C-19 (exploratory departures) and C-21 (held-out departures).

## E-08 Handoff §1.1: "attributes compliance to the reserved margin" (REJECTED)

- **Locator:** `EXPERIMENT_REVIEW_HANDOFF.md:54-55`.
- **Rejected text:** "its predeclared replication endpoint is met and its factorial reading attributes compliance to the reserved margin, not to the scenarios."
- **Why:**
  - "Attributes" is a causal reading of a two-factor comparison.
  - "Replication endpoint ... is met" uses the label without the INV-5 qualifier.
- **Replacing claims:** C-03 and C-02.

## E-09 Handoff §10.3: gain "explained by ordinary tightening" (REJECTED)

- **Locator:** `EXPERIMENT_REVIEW_HANDOFF.md:951-953`.
- **Rejected text:** "much of the apparent robustness gain **is** explained by ordinary tightening"
- **Why:**
  - Causal wording on the upper-only synthetic screen, which is mixed across strata and has unequal scored denominators (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:103`).
  - The generator is stationary.
  - The study is labelled retrospective and exploratory (`reports/horizon_robustness_plan/PLAN.md:169`).
- **Replacing claim:** C-18.

## E-10 Handoff §12.6: the incumbent's pass "says only that" its layout drifted less (REJECTED)

- **Locator:** `EXPERIMENT_REVIEW_HANDOFF.md:1157`.
- **Rejected text:** "the incumbent's ±2 pass says only that the warehouse's own layout drifted less than the optimised ones drained."
- **Why:** the reading omits the headroom asymmetry. The targets are the incumbent's own historical shares, so:
  - on the history scenario its minimum required slack is 0 (`ho.incumbent.training_slack.history`);
  - every returned optimised layout uses its whole allowance (`ho.min_slack.*`; Q-005).

  The incumbent pass cannot be read as a drift comparison without that qualifier.
- **Replacing claim:** C-09.

## E-11 First plan: "2.35 %" computed from rounded display values (REJECTED)

- **Locator:** `reports/horizon_robustness_results/WRITING_PLAN_20260914.md:25`.
- **Rejected text:** "| HIST+ACT-T costs about 2.36 % more visits than TIGHT | 3.347 / 3.270 | 2.35 %; confirmed |"
- **Why:** the ratio was computed from three-decimal display values.
  - From exact means the value is 2.355907% (`ho.visits.HIST_ACT_T_over_TIGHT.pct`): 2.4% at the companion's one-decimal convention, 2.36% at two decimals.
  - The reviewed plan forbids ratios from display values (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:96`).
- **Replacing claim:** C-01.

## E-12 First plan: "undated information contract and predeclared rolling-origin protocol" (REJECTED)

- **Locator:** `WRITING_PLAN_20260914.md:37-38`.
- **Rejected text:** "**undated information contract and predeclared rolling-origin protocol**"
- **Why:**
  - Rolling-origin evaluation is established.
  - The executed evidence has one exploratory origin and one later held-out origin, not an extensive rolling-origin experiment (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:95`).
  - Novelty relative to literature is decided in P4, not asserted here.
- **Replacing claim:** C-07.

## E-13 First plan: "margin has to be set from station-level dispersion" (REJECTED)

- **Locator:** `WRITING_PLAN_20260914.md:44-45`.
- **Rejected text:** "total-variation bound is far too loose to be a margin rule, so margin has to be set from station-level dispersion."
- **Why:** same non sequitur as E-03 (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:100`). No validated margin rule was obtained.
- **Replacing claims:** C-08 and C-31.

## E-14 First plan C2: "do not beat ordinary tightening on the benchmark" (REJECTED)

- **Locator:** `WRITING_PLAN_20260914.md:58`.
- **Rejected text:** "historical scenarios reduce cap breaches against NOM but do not beat ordinary tightening on the benchmark"
- **Why:** too broad. The upper-only synthetic screen is mixed across strata and has unequal scored denominators, so it supports no universal ranking (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:103`).
- **Replacing claim:** C-18.

## E-15 First plan C3: "robust-arm misses are small (≤ 0.41 pp) and downward" (REJECTED)

- **Locator:** `WRITING_PLAN_20260914.md:59`.
- **Rejected text:** "robust-arm misses are small (≤ 0.41 pp) and downward"
- **Why:** the policy misses include cap breaches as well as floor breaches.
  - At the exploratory origin with δ = 0.02, HIST has 1 cap breach and 8 floor breaches over the three horizons (`ts.berner.d02.HIST.cap_breaches_total`, `.floor_breaches_total`).
  - On the held-out window HIST+ACT breaches the cap on two seeds (`ho.breach.HIST_ACT.s11.cap_count`, `.s22.cap_count`).
  - Leaving the modelled set and breaching the band are different metrics (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:102`).
  - "Small" does not settle the practical importance of a miss (`EXPERIMENT_REVIEW_HANDOFF.md:1149`).
- **Replacing claims:** C-19 and C-03.

## E-16 First plan C5: "≈15 % fewer visits than the incumbent" (REJECTED)

- **Locator:** `WRITING_PLAN_20260914.md:61`.
- **Rejected text:** "explicit margin gives ±2 compliance on all three seeds with ≈15 % fewer visits than the incumbent"
- **Why:** the two margin arms differ.
  - TIGHT saves 15.0% (`ho.saving.TIGHT.pct`) and HIST+ACT-T 13.0% (`ho.saving.HIST_ACT_T.pct`). Across arms the saving is 13.0–16.0%.
  - Single runs range from 12.0% to 17.5% (`ho.saving.single_run.min.pct`, `.max.pct`).
  - The plan review asked for 13–16% by arm (`PLAN_REVIEW_LEDGER_20260914.md:103`).
- **Replacing claim:** C-13.

## E-17 First plan C6: "compliance rests on within-station cancellation, not on set membership" (REJECTED)

- **Locator:** `WRITING_PLAN_20260914.md:62`.
- **Rejected text:** "so compliance rests on within-station cancellation, not on set membership"
- **Why:** as in E-03 and E-07, the evidence is consistent with cancellation but does not establish it.
- **Replacing claims:** C-21 and C-31.

## E-18 First plan C7: "validated by an independent exact validator" (REJECTED)

- **Locator:** `WRITING_PLAN_20260914.md:63`.
- **Rejected text:** "is validated by an independent exact validator"
- **Why:** software agreement supports implementation correctness. Mathematical exactness needs the derivation (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:104`).
- **Replacing claim:** C-22.

## E-19 First plan §2: "the extension's rows are added to that feasible set" (REJECTED)

- **Locator:** `WRITING_PLAN_20260914.md:85-86`.
- **Rejected text:** "the extension's rows are added to that feasible set."
- **Why:** the companion's workload-budget rows are replaced, not supplemented, by share-policy rows (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:145`).
- **Replacing claim:** C-11.

## E-20 First plan §2: "the workload-share preservation objective" (REJECTED)

- **Locator:** `WRITING_PLAN_20260914.md:95-96`.
- **Rejected text:** "(ii) the workload-share preservation objective replacing a fixed budget"
- **Why:** share preservation is a feasibility policy, not an objective. The objective stays station visits (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:152-153`).
- **Replacing claim:** C-11.

## E-21 First plan §2: "24 after two exclusions" (REJECTED)

- **Locator:** `WRITING_PLAN_20260914.md:100-101`.
- **Rejected text:** "the article says 26 stations, the extension's retained system has 24 after two exclusions"
- **Why:** the companion itself reports 26 stations and evaluates 24 (`IJSSOL_CSLAP_v1.tex:569`, document values `comp.stations.reported`, `comp.stations.evaluated`). The extension's 24 evaluated stations are not a new exclusion (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:183-185`; Q-001).
- **Replacing claim:** C-26.

## E-22 First plan §3: "isolated mechanism"; "what nobody else has measured" (REJECTED)

- **Locator:** `WRITING_PLAN_20260914.md:115` and `:119`.
- **Rejected text:**
  - "(1) C5, the predeclared held-out factorial with an isolated mechanism"
  - "they are what nobody else has measured on real data"
- **Why:**
  - The mechanism is not isolated (see E-06).
  - "Nobody else has measured this" is inadmissible as a novelty argument (`WRITING_ORCHESTRATION_PLAN_20260914.md:717`; `WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:245-247`).
- **Replacing claims:** C-03 and C-07.

## E-23 First plan §3: "margin decides compliance", "13–15 %", "what the band costs" (REJECTED)

- **Locator:** `WRITING_PLAN_20260914.md:120-124`.
- **Rejected text:** "margin decides compliance, scenarios buy fidelity to historical shares at a visit cost; the incumbent already sits inside ±2 on both futures, so the gain is the 13–15 % visit saving at equal compliance, and NOM's extra point of saving is what the band costs."
- **Why:**
  - "Decides" is causal (E-06).
  - The by-arm saving is 13.0–16.0% (E-16).
  - "What the band costs" reads a difference between time-capped returned layouts as the cost of a constraint at the optimum (`ho.gap.*` about 0.985).
  - The incumbent comparison omits the headroom asymmetry (E-10).
- **Replacing claims:** C-03, C-13, C-05 and C-09.

## E-24 First plan §0: Winkelmann et al. as "no robust optimisation; dated" foil (REJECTED; routed to P2)

- **Locator:** `WRITING_PLAN_20260914.md:30`.
- **Rejected text:**
  - "deterministic MILP, day-of-week demand, workload balance across days; no robust optimisation; **dated**"
  - "it is the dated, deterministic counterpart of our undated protocol"
- **Why:** the reviewed plan checked the journal version (*FSMJ* 37, 558-598, DOI 10.1007/s10696-024-09549-7). It imposes upper and lower workload bounds relative to the station average for each weekday (§5.2, eqs 10-12) and includes out-of-sample simulation (§5.4). It is a close variation-aware comparison, "not merely a deterministic dated foil" (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:212-221`).
- **Replacing claim:** none in this register. Literature positioning belongs to P2 (`W/literature/source_register.json`).

## E-25 First plan §0: Dündar "Unverified" (SUPERSEDED; routed to P2)

- **Locator:** `WRITING_PLAN_20260914.md:31`.
- **Rejected text:** "**Unverified**: the writing agent must confirm title and scope before citing"
- **Why:** the reviewed plan verified the title and scope (`WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:222-229`). P2 verifies them again under its own protocol.
- **Replacing claim:** none in this register (P2).

## E-26 Reviewed plan: "This is high product-mix drift" (RESTRICTED)

- **Locator:** `WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:101`.
- **Restricted text:** "The new row shows TV 0.194956 versus historical maximum 0.194411 and mean 0.171100 over 11 matched blocks. This is high **product-mix drift**, not proof of workload-feasibility difficulty."
- **Why:** the held-out distance is large relative to the reserved margin of one percentage point (C-31). It is not high relative to history once blocks are measured like for like: the historical maximum is about 0.214 (`drift.holdout.hist_tv_max.like_for_like`). The sentence's own caveat, "not proof of workload-feasibility difficulty", is kept.
- **Replacing claims:** C-06 and C-31.

## E-27 Predeclaration §8.2: "1.70 pp in a single historical block relative to its pooled share" (RESTRICTED)

- **Locator:** `CAMPAIGN_PREDECLARATION.md:354-356`.
- **Restricted text:** "one station's share moved up by as much as 1.70 pp in a single historical block relative to its pooled share, so **±1 is violated by the warehouse's own history**"
- **Why:** the value is correct against the stated reference (document value `pred.twosided.block_deviation_quoted`; anchor `disp.explor.n_half.max_abs`). That reference contains the block. Against the rest of the history the value is about 1.80 (`disp.explor.n_half.max_abs.like_for_like`). The paper names the reference whenever it uses either number. The predeclaration itself is unchanged.
- **Replacing claim:** C-08.

## E-28 Reviewed plan §6 Step 4: "optimizer seed replication" allowed when qualified (RESTRICTED)

- **Locator:** `WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:489-490`.
- **Restricted text:** 'Allowed: "conditional robust feasibility for U" with its assumptions; "optimizer seed replication" when explicitly qualified.'
- **Why:** INV-5 of the orchestration plan has precedence (plan §0) and keeps replication vocabulary out of the paper's own voice. The register writes "three optimizer seeds" and never uses the phrase.
- **Replacing claim:** C-24.

## E-29 Test-suite size: 260 against 241 (UNRECONCILED)

- **Locators:** `WRITING_PLAN_20260914.md:23`; `WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:61`; `EXPERIMENT_REVIEW_HANDOFF.md:58`.
- **Texts:**
  - First plan: "260 tests pass" and "234 shared + 26 Hexaly".
  - Reviewed plan: "new run of the 260-test suite".
  - Handoff: "**Test suite grown from 173 to 241** (218 shared/CPLEX + 23 Hexaly)".
- **Why:** the counts disagree.
  - The handoff line may predate the tests added by the 13 September repairs (§6.8), but this cannot be checked without running tests, which H1 forbids.
  - `verification_inventory.md` cites the handoff figure.
  - No test count has an anchor or document value.
- **Replacing claim:** none. The register states no test count; any count in the paper first needs an agreed document value.

## E-30 Companion §1: "26 stations" in the contribution list (RESTRICTED for reuse)

- **Locator:** `IJSSOL_CSLAP_v1.tex:93`.
- **Text:** "We validate on an operating warehouse of 21,874 products and 26 stations"
- **Why:** correct for the companion, which evaluates 24 of those stations (`IJSSOL_CSLAP_v1.tex:569`). The extension does not copy "26 stations" as its evaluated set, and it says "the 24 evaluated stations" (Q-001).
- **Replacing claim:** C-26.
