# Predeclared campaign design for stages B–F

Written **before** any stage-B, D, E or F execution. Its purpose is to fix, in
advance and in writing, every choice that could otherwise be made after a result
became visible. Nothing in this document may be revised on the basis of an
outcome; a revision forced by evidence becomes a new, separately labelled and
separately dated exploratory revision, kept apart from the confirmatory record.

Authority: the scientific protocol in `../horizon_robustness_plan/PLAN.md` as
amended by `../horizon_robustness_plan/INDUSTRIAL_AMENDMENT_20260909.md`, plus
the user's resource authorization of 10 September 2026.

## 1. Authorized budget

The user authorized, on 10 September 2026:

* **Stage A (pilot)** exactly as quoted: 6,840 s configured native time over 8
  solves, a 3-hour overall wall cutoff, a 32-GiB process-tree RSS ceiling and a
  600-second per-attempt build allowance, run sequentially.
* **Stages B–F**: approximately **30 sequential solver-hours in total**, with
  "screening only" scope — all 29 approved synthetic instances plus the complete
  retained BERNER system at the first origin and seed 11, all three declared
  horizons and all four arms; **no seed replication and no second origin**; and
  sensitivity/min-slack work limited to the smaller synthetic families plus a
  partial BERNER.
* Permission to **propose** a uniform reduction of the declared per-solve time
  caps if pilot convergence evidence supports it. Any such reduction requires
  separate approval before use and is applied identically to every arm, instance
  and horizon.

The budget is a ceiling, not a target. Stopping early is allowed; exceeding it
is not.

## 2. Fixed selection rules

These rules are outcome-independent by construction.

**Instances.** Stage B uses every one of the 29 approved synthetic instances and
the complete retained BERNER system. No instance is added, dropped, substituted
or reordered on the basis of its result. The industrial case is never replaced
by a top-SKU subset.

**Reduced subsets.** Where a stage cannot afford the full instance list, the
subset is *the lowest numerical seed in each catalogue-size family*, in this
fixed order: `syn_50sku_seed1001`, `syn_500sku_seed1001`, `syn_1000sku_seed1001`,
`syn_2000sku_seed1001`, `BERNER`. A smaller subset is a **prefix** of that list.
The rule is arithmetic on the seed number and is settled before any solve.

**Origins and seeds.** First eligible origin only, seed 11 only, throughout
stages B–F. Origin index 0 is `floor(0.70 · M)` for that dataset's complete-order
count `M`. Additional origins and seeds 22/33 are outside the authorized budget
and are recorded as *not executed*, never as absent because they looked
unpromising.

**Horizons.** All three declared horizons `ceil(P/2)`, `P`, `2P` wherever
eligible. An `INSUFFICIENT_HISTORY` or `INSUFFICIENT_FUTURE` cell keeps its
explicit eligibility status and its place in every denominator.

**Arms.** All four: NOM, TIGHT (λ = 0.5), HIST, HIST+ACT (ν = 0.01). No arm is
dropped for underperforming.

**Parameters.** δ = 0.01 and ν = 0.01 remain the primary settings for every
headline table. Frontier stages vary exactly one axis at a time over the frozen
grids δ ∈ {0, 0.0025, 0.005, 0.01, 0.02, 0.05}, ν ∈ the same grid, λ ∈ {0, 0.25,
0.5, 0.75, 1}. **No value observed to perform better on a future window may
replace the primary setting**, in any table, figure or recommendation.

**Retries.** A retry requires a distinct retry ID and a written reason recorded
before it runs, and the reason must be a computational or implementation fault,
never an unwelcome result. Retries never enter primary summaries; the primary
case file does. A campaign invalidated by an implementation change is superseded
as a whole directory, never repaired case by case.

## 3. Which attempts enter primary summaries

Frozen before any stage-B result existed, and enforced in code by
`Baselines/horizon_robustness_analysis/analysis.py`:

1. A manifest row enters a primary summary only through its primary case file
   `cases/<case_id>.json`.
2. Deliberate retries under `cases/<case_id>/retries/<retry_id>.json` are
   inventoried and reported separately, never substituted for a primary attempt.
3. A row with no case file is recovered from the supervisor terminal record and
   reported with an explicit missing status. It is never dropped and never
   scored as a zero-cost, zero-violation observation.
4. Denominators are counts of **authorized manifest rows**, not of rows that
   happened to return a layout.
5. Campaign directories carrying `SUPERSEDED.md` are excluded from every table
   and figure and are listed as excluded in `analysis_audit.md`.

## 4. Aggregation and pseudoreplication

1. **Case** — one (dataset, origin, n, arm, seed, parameter) cell.
2. **Instance** — averaged within a dataset across origins and seeds.
3. **Stratum** — summarized across instances of one catalogue size, with the
   **instance** as the unit of analysis.

Solver seeds measure algorithm variability, not additional independent futures.
Horizons at one origin share data and are reported separately, never pooled.
Individual stations are not independent observations. Every paired difference
states the number of instances it rests on. No binomial confidence statement is
attached to correlated windows, and BERNER, having one eligible origin under
this budget, is reported descriptively with that denominator stated.

## 5. Reporting commitments that do not depend on the outcome

* A time limit with no incumbent is `NO_INCUMBENT_LIMIT`, never infeasibility.
* Infeasibility is claimed only from a certified lower bound with stated
  provenance; a solver-free reference upper bound on δ_min never proves it.
* Optimization failure, independent-validation failure and out-of-sample
  violation are three separate quantities and are never pooled.
* A negative or mixed result is reported as such. Neither δ nor ν is widened,
  and no arm, instance or horizon is removed, to obtain a favourable table.
* HIST+ACT reduces exactly to HIST wherever the inactive set `Z_H` is empty or
  ν = 0. Where that happens, it is reported as an identity, not as evidence that
  activation protection is costless or beneficial.

## 6. Stage inventory and execution order

| Stage | Content | Status |
|---|---|---|
| A | Engineering pilot, 8 solves | executed 10 Sep 2026 (see `PILOT_FINDINGS.md`) |
| B | Screening: 30 datasets × origin 0 × seed 11 × 3 horizons × 4 arms | see §7 |
| D | δ, ν and λ frontiers, one axis at a time, on the §2 subset | see §7 |
| E | Minimum-slack diagnostic, including the solver-free δ_min upper-bound survey over every dataset and horizon | see §7 |
| F | Cross-horizon evaluation of already frozen layouts; no new optimization | no solver budget required |

Stage F consumes no solver time: it re-scores layouts that are already frozen,
through `Baselines/horizon_robustness_analysis/rescoring.py`, and its records are
always marked `secondary_cross_horizon`.

## 7. Approved allocation of the stage B–F budget

*Recorded on 10 September 2026, before any stage-B solve ran, and not revised
afterwards.*

### 7.1 Per-solve time caps: unchanged

The pilot showed Hexaly consuming its full configured cap on every solve and
never proving optimality — its reported objective bound is 0 and its gap is
therefore always 1.0, so the solver supplies no convergence evidence of its own.
A convergence probe (re-solving built models at 10 %, 25 % and 50 % of their caps)
was offered to the user and **declined**. It was never executed.

Consequently the declared caps stand exactly as pre-registered — **120 / 300 /
600 / 1200 s** for the 50/500/1000/2000-product families and **1800 s** for the
industrial case — and **no cap reduction is applied anywhere**. This also avoids
the specific risk that a shorter cap manufactures `NO_INCUMBENT_LIMIT` results in
the robust arms, which need search time to reach feasibility at all: the robust
workload rows are hard constraints in the Hexaly model.

### 7.2 Stage B: the full pre-registered screening, run to the session boundary

The user directed that the complete screening be launched and handed off mid-run
rather than reduced to fit one session. Therefore:

* All 29 approved synthetic instances **and** the complete retained BERNER system.
* First eligible origin only; seed 11 only; all three declared horizons; all four
  arms; δ = 0.01, ν = 0.01, λ = 0.5; Hexaly; one thread; sequential.
* Declared caps per §7.1; 32-GiB process-tree RSS ceiling; 600 s per-attempt build
  allowance.
* Rows not reached before the campaign stops keep an explicit
  `WALL_CUTOFF` / `SOLVER_BUDGET_CUTOFF` / missing record and stay in every
  denominator. **They are not evidence of anything about the method.**
* The campaign is resumable. The exact resume command is in the review handoff.
  On resume, at most one case — the solve that was in flight when the campaign
  stopped — will carry an `INTERRUPTED` attempt and requires a deliberate retry
  with a distinct ID and a written reason. That is the runner's fail-closed
  design and is not to be worked around.

**Reporting consequence, fixed in advance:** a partially completed screening is
reported as a partially completed screening. Instances that happen to have been
reached first are not presented as a representative sample, and no hypothesis is
judged on the subset that finished. The instance order is the manifest order,
which is fixed by the dataset list and is independent of any outcome.

### 7.3 Stages D and E: funded only by what stage B leaves

Stage B at declared caps is expected to consume most or all of the authorized
~30 solver-hours. Stages D (δ, ν, λ frontiers) and E (certified min-slack bounds)
are therefore **explicitly at risk of not being executed at all**, and if they are
not, they are reported as *not executed*, never as absent because the results
looked unpromising.

Two δ_min diagnostics are run regardless, because they **cost no solver time**:

1. **Reference-layout upper bounds** over every dataset, horizon and arm
   (`tools/horizon_robustness/slack_survey.py`). The incumbent is always
   structurally feasible, so its required slack bounds δ_min from above.
2. **Cross-arm upper bounds** from every layout the campaign returns
   (`--campaign`). Any structurally feasible layout bounds δ_min from above for
   *every* arm, so a NOM layout scored against the HIST envelope yields a valid
   bound even where the HIST solve itself returned no incumbent.

Both are **upper** bounds. Neither can prove infeasibility, and neither is
reported as doing so. A certified **lower** bound requires a solver — CPLEX in
`min_slack` mode, with `bound_provenance = native_cplex_best_bound` — and is
stage E. If stage E does not run, the question "is δ = 0.01 attainable at all for
the historical-hull uncertainty set?" stays formally **open**, and the handoff
says so.

### 7.3b Numerical formulation revision, 10 September 2026

The pilot's BERNER HIST+ACT case was rejected as `NUMERICAL_ISSUE`: Hexaly
returned a structurally valid partition whose exact robust residual was
**+1.0555e-06**, about 100× the declared 1e-8 model tolerance, because it builds
the model in float64 with an internal feasibility tolerance near 1e-6 and exposes
no way to tighten it.

On the user's instruction the tolerance was **not** widened and no safety margin
was introduced. Instead the fixed-cap visits rows were restated in exact integer
counts (`uncertainty.integer_cap_rows`, version `exact_integer_counts_v2`):

```
base        sum_p x_ps L_p^k                    <= floor( u_s T_k )
activation  (M-N) sum_p x_ps L_p^k + N T_k h_s  <= floor( M u_s T_k )    (nu = N/M)
```

Both left sides are integers, so flooring each right side is an exact
restatement — for integer `z`, `z <= r` and `z <= floor(r)` have the same
solution set. It is neither a relaxation nor a tightening, so **the scientific
feasible set, δ, the evaluation ceilings and the independent exact validator are
all unchanged**. Its only effect is numerical: an integer row cannot be violated
exactly by a solver whose feasibility tolerance is below 1.0.

Scope and limits, as instructed:

* Applied to the fixed-cap **visits** model in **both** backends, so the two are
  compared on identical rows.
* Minimum-slack diagnostics remain defined on the **original rational model**.
* A tightened model is never used, because none exists; no infeasibility or bound
  from this restatement is anything other than a statement about the original
  problem, since the two have identical feasible sets.
* Verified by enumerating every storage-feasible layout of small fixtures and
  requiring agreement with the exact validator, across all four arms, δ = 0,
  clipped caps, exact-floor thresholds, non-empty and empty `Z_H`, ν = 0 and
  ν = 1, plus int64 range guards with negative and positive controls.
* Hexaly expression types are checked with `is_int()` after `model.close()`; the
  build refuses if any row is not integer-typed.
* Bounded industrial recheck: the same BERNER case now validates exactly, with a
  residual of **−1.208e-06** (strictly inside) and `model_feasible_exact = true`.

The implementation is versioned by this change, so every manifest is regenerated
and prior artifacts are preserved under their own implementation hash. Results
produced under the two formulations are never mixed inside one comparison.

### 7.3c Predeclared minimum-slack diagnostics (~2 h, before screening)

Fixed before any of these solves ran.

**Instrument.** CPLEX only. It is the sole backend that returns a bound with
stated provenance (`native_cplex_best_bound`); Hexaly's bound on this objective is
the trivial 0 and carries no information. Mode `min_slack`, on the **original
rational model**.

**Cases.** The unresolved 50-product case first, then a small declared
50/500-product horizon selection:

| Dataset | Origin | Horizons | Arm | Cap per solve |
|---|---|---|---|---|
| `syn_50sku_seed1001` | first eligible | 25, 50, 100 | HIST | 900 s |
| `syn_500sku_seed1001` | first eligible | 250, 500, 1000 | HIST | 1200 s |

Six solves, 6,300 s ≈ 1.75 h. **Model deduplication:** `Z_H` is empty in both
datasets at these origins, so HIST+ACT is the *same model* as HIST and is not
solved twice; NOM and TIGHT are excluded because their min-slack answer is
trivially 0 at the reference. The caps exceed the campaign caps deliberately: a
diagnostic's value is the tightness of its bound interval, and the 120 s probe
already showed an interval two orders of magnitude wide.

**Stopping rules.** Each solve stops at its cap. No case is extended, repeated or
re-tuned because its interval looked interesting — that would make the reported
bound outcome-selected. If a solve returns no incumbent, that case is
`UNRESOLVED` and is not retried at a larger cap.

**Reading the result.** The upper bound is the independently recomputed required
slack of the returned layout, never the solver's objective as reported. The lower
bound is the solver bound, used only when its provenance is recorded and it is
strictly positive. **An interval that straddles δ = 0.01 is UNRESOLVED, with no
directional reading**; `NO_INCUMBENT` is never described as infeasibility. Only a
certified lower bound strictly above δ establishes that the declared tolerance is
unattainable for that model.

**Warm starts.** CPLEX warm-starts from the historical reference layout where
that layout validates — history-only, never a future-informed start. Build and
solve seconds are recorded per case.

**Budget.** Charged explicitly: 6,300 s here, plus 480 s already spent on the
50-product CPLEX diagnosis and 1,800 s on the BERNER numerical recheck.

### 7.3d Diagnostic reassessment, 10 September 2026

The user reserved up to 6 h for minimum-slack diagnostics and asked for a
reassessment after roughly the first 2 h. **Decision: stop after the predeclared
six solves (6,300 s) and give the remaining reserve to screening.** Reasons,
recorded before any further solve:

1. The two `UNRESOLVED` cases advanced their lower bounds only to 0.005865 and
   0.001938 after 900 s each. Closing either above δ = 0.01 within any plausible
   additional budget is not credible.
2. Industrial attainability is already established **constructively at zero extra
   cost**: the BERNER numerical-recheck layout has an independently recomputed
   required slack of ≈ 0.0099988, below δ = 0.01, so a layout meeting the declared
   tolerance demonstrably exists for BERNER HIST+ACT at n = P.
3. Extending only the cases that looked interesting would make the reported
   bounds outcome-selected, which §7.3c's stopping rules forbid.

Results, for the record — four cases constructively resolved, two unresolved
(qualification added 13 Sep 2026: these six runs predate the witness-saving
version of the tool; their layouts were logged, not saved, so the runs are not
replayable and the bounds stand as logged results):

| Dataset | n | η lower | η upper | Verdict |
|---|---:|---:|---:|---|
| syn_50sku_seed1001 | 25 | 0.005865 | 0.031925 | UNRESOLVED (straddles δ) |
| syn_50sku_seed1001 | 50 | 0.001938 | 0.016338 | UNRESOLVED (straddles δ) |
| syn_50sku_seed1001 | 100 | — | 0.007333 | ATTAINABLE |
| syn_500sku_seed1001 | 250 | — | 0.003669 | ATTAINABLE |
| syn_500sku_seed1001 | 500 | — | 0.001670 | ATTAINABLE |
| syn_500sku_seed1001 | 1000 | — | 0.000458 | ATTAINABLE |

No lower bound anywhere exceeded δ, so **nothing was proven unattainable**. The
monotone fall of the upper bounds with n is the empirical signature of the proven
nesting property in `MATHEMATICAL_SCOPE.md` §9, not a new finding.

### 7.4 Stage F: cross-horizon transfer, no solver budget

Runs on whatever layouts exist when the campaign stops, through
`Baselines/horizon_robustness_analysis/rescoring.py`. Every record is marked
`secondary_cross_horizon`, is never substituted for primary same-horizon scoring,
and is never used to choose a preferred n after seeing its future.

## 8. Exploratory revision 2 — the two-sided rule (predeclared 12 Sep 2026)

Written before any two-sided solve runs. Kept **separate** from the completed
upper-only confirmatory study (sections 1–7), whose artifacts, hashes and tables
are unchanged; the only shared code is the solver package, whose upper-only
identities are pinned by `tests/horizon_robustness/test_two_sided.py`.

### 8.1 The rule and the model

Every station must stay within ±δ of its historical share on the future window:
`b_s − δ ≤ r_s ≤ min(1, b_s + δ)`, floors clipped at zero exactly as caps are
clipped at one. The optimizer gains lower rows for every scenario, in exact
integer counts: `Σ x·L ≥ ceil(f_s·T_k)` and, with activation, `(M−N)·Σ x·L ≥
ceil(M·f_s·T_k)`, because the lowest attainable share over the uncertainty set
places all activation mass elsewhere, `(1−ν)·A_sk`. Two-sided joint compliance,
violation counts and worst excess include both sides; the min-slack diagnostic
covers both excursions. HIST+ACT still collapses to HIST wherever `Z_H = ∅`.

### 8.2 Why δ = 0.02 is primary, and what ±1 and ±3 mean here

Chosen from the statistics, not from any future result, as the user directed:
under the layout BERNER actually ran, one station's share moved up by as much as
1.70 pp in a single historical block relative to its pooled share, so **±1 is
violated by the warehouse's own
history**; ±2 is the smallest grid slack that history stays inside at every
horizon, and it is also the smallest that the 500-product family supports.
Re-scoring the 312 existing upper-only layouts two-sided showed that at ±1 no
optimized BERNER layout passes at any horizon (they drain 1.7–3.1 pp from some
station), at ±2 only one does, and at ±3 all robust arms and TIGHT pass.

* **δ = 0.02** — primary, data-supported.
* **δ = 0.01** — the user's preferred rule, run as the *aspiration*: can a
  two-sided optimizer hold a band the incumbent's own history could not?
* **δ = 0.03** — the user's stated fallback.

No headline moves between these three after the futures are seen.

### 8.3 Cases, arms, horizons, budget

| Block | Datasets | δ | Arms | Horizons | Unique solves | Configured native |
|---|---|---|---|---|---:|---:|
| Screen | subset rule of §2: `syn_50/500/1000/2000_seed1001` + BERNER | 0.02 | all four | ½P, P, 2P | 28 | 25,500 s |
| Sensitivity δ=0.01 | BERNER | 0.01 | all four | ½P, P, 2P | 8 | 14,400 s |
| Sensitivity δ=0.03 | BERNER | 0.03 | all four | ½P, P, 2P | 8 | 14,400 s |
| **Total** | | | | | **44** | **54,300 s ≈ 15.1 h** |

(The 50-product warehouse supports no grid slack below ±5 in its own history; it
stays in for completeness and its non-returns are reported as such.) First
eligible origin, seed 11, Hexaly, one thread, sequential, declared caps
120/300/600/1200/1800 s unchanged, 32 GiB, 600 s build allowance. TIGHT at
λ = 0.5 under δ = 0.02 optimises inside the ±1 band, so the ±1 aspiration is also
carried by the screening block's own control arm.

### 8.4 Reporting rules

* Reported only in tables and figures that carry `rule = two_sided` and the
  campaign name; never pooled with the upper-only study.
* `NO_INCUMBENT_LIMIT` is not infeasibility. No certified lower bound, no
  infeasibility claim.
* The three δ values are reported side by side with full denominators; the
  primary is δ = 0.02 regardless of which looks best.
* The incumbent is scored two-sided on the same futures as context, not as the
  headline comparator; the comparison of interest remains NOM / TIGHT / HIST /
  HIST+ACT.
* The two unresolved upper-only small-warehouse cases stay unresolved; nothing
  here revisits them.

## 9. Exploratory revision 3 — the held-out factorial (predeclared 13 Sep 2026)

Written before any revision-3 quote or solve, after the 13 September independent
review and with the user's decision of the same day. Kept separate from the
upper-only study (sections 1–7) and from exploratory revision 2 (section 8); it
does not modify either.

### 9.1 The question

Revision 2 left H2 confounded: TIGHT differs from HIST+ACT in two ways at once,
it reserves a margin and it uses no scenarios. The cells were consistent with a
margin mechanism but did not isolate it. Revision 3 asks one question on demand
that no analysis of this study has read: **does explicitly reserving the margin
explain compliance, and do historical scenarios add anything on top of it?**

### 9.2 Design: a two-by-two on the unexamined tail of the stream

| Factor | Level 0 | Level 1 |
|---|---|---|
| Scenarios and activation | none (pooled history only) | historical blocks and activation, ν = 0.01 |
| Reserved margin | none (optimise at ±δ) | optimise inside ±δ(1−λ), λ = 0.5 |

giving four arms: `NOM` (0,0), `TIGHT` (0,1), `HIST+ACT` (1,0) and the new
`HIST+ACT-T` (1,1), which is HIST+ACT's model with TIGHT's reduced optimisation
band on both sides. `HIST` is not run: on BERNER it differs from HIST+ACT only by
activation, which is not a factor here.

* **Dataset:** BERNER only; the synthetic warehouses have nothing to say about
  industrial regime change and were declined by the user.
* **Deployment origin:** order index **243,151**, the end of the furthest future
  ever scored in this study (first origin 199,403 plus 2P). Orders 243,151 to
  284,862 have been read by no solve, survey, re-scoring or diagnostic of this
  study; the drift survey and every other analysis stop at 243,151. The target
  b_s is computed from the full prefix [0, 243,151) and then frozen. Caveat: the
  submitted article's earlier temporal hold-out used a different dated extract,
  so the claim is "unexamined in this study", not "unexamined by anyone".
* **Horizon:** n = P = 21,874 only (the tail cannot hold 2P; P/2 would cost as much
  again and answers the same question with less data). The protocol's origin
  rule requires room for 2P, so this origin is introduced as an explicit
  `holdout` stage rather than by changing that rule.
* **Policy, frozen:** two-sided rule, δ = 0.02, ν = 0.01, λ = 0.5, seed set
  {11, 22, 33}, Hexaly, one thread, 1800 s per solve, 600 s build allowance,
  32 GiB, sequential. Nothing is chosen after the tail is read.
* **Budget:** 4 arms × 3 seeds × 1 horizon = **12 unique solves, 21,600 s
  configured** (6.0 h), wall cutoff 38,000 s. Requires its own quote and a
  separate launch approval; it is not covered by any earlier authorisation.
  Quoted 13 Sep 09:34 UTC as `manifests/holdout_20260913.json`, manifest hash
  `d4d4ed6c9772565a5caa1f03529f3e3e9cf50aa9b9463bf84ccbe6220b1a1bba` under
  implementation `4e359efde84f…`: 12 rows, 12 solves, 21,600 s, origin 243,151, all
  rows eligible, exactly this design. Approved and launched the same day into
  `campaigns/ho3_20260913/` before any row was solved.
* **Retries:** none chosen on outcome; an interrupted solve is retried once with
  a recorded reason, never a completed one.

### 9.3 Predeclared endpoints and reading

* **Replication endpoint (primary):** TIGHT passes the two-sided ±2 band at n = P
  on the held-out future for at least two of the three seeds. Failure closes the
  fixed-policy claim; passing supports a bounded case-study claim only.
* **Factorial reading (secondary, descriptive):** per arm, the seed-wise pass
  count, the breach magnitudes in both directions, the mean visits per order
  relative to the incumbent scored on the same future, and the departures from
  the modelled set in both directions. Margin main effect = arms (0,1) and (1,1)
  against (0,0) and (1,0); scenario main effect = (1,0) and (1,1) against (0,0)
  and (0,1). Three seeds measure optimiser variability, not demand variability:
  there is one origin, so no claim about origins is made.
* **What is not tested:** no λ or δ frontier; no other origin; no synthetic
  instance. Nothing here can certify a band unattainable, and no result changes
  the primary δ of revision 2.

### 9.4 Reporting rules

* Reported in its own section with `stage = holdout`, never pooled with sections
  1–8; the incumbent scored two-sided on the same future as context.
* Seeds are averaged within the origin and never counted as independent futures.
* `NO_INCUMBENT_LIMIT` is not infeasibility.
* The drift survey (`tables/drift_survey.csv`) is reported beside the reserved
  margin ρ = λδ = 0.01 as explanatory context only; the margin was not chosen
  from it and is not re-chosen after the result.
