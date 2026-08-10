# IJPR revision — change log and response

Manuscript: `IJPR_CSLAP_v2.tex`. Baseline for every "before" quote: git tag
`pre-ijpr-revision-20260729` (commit `bea0e8a`). Diff the whole revision with

```
git diff pre-ijpr-revision-20260729 -- IJPR_CSLAP_v2.tex
```

Two audiences share this file: **Part A** answers the supervisor's readability comments, **Part B**
answers the external review point by point. Part C lists the journal-compliance edits, Part D the
things we deliberately did not do and why.

---

## Part A — Supervisor's comments (all applied)

Each item was fixed by rewriting the passage it sits in, not the sentence alone.

### A1. "The move from manual picker-to-parts warehouses to automated, conveyor-driven, zone-picking systems changes which model is appropriate."

Opened Section 2 with the physical difference instead of an abstraction about models:

> In a manual warehouse a picker walks to the shelves, so the time to prepare an order follows the
> distance walked, and storage models minimise that distance. In an automated pick-and-pass
> warehouse a conveyor carries the order past fixed stations and nobody walks, so the model has to
> minimise something else.

### A2. "pod-station" undefined

Defined at first use, in the sentence that needs it:

> in a robotic mobile fulfilment system, robots carry movable shelf racks, called pods, to fixed
> picking stations, so a pod-station visit is the delivery of one rack to one station, the analogue
> of our station visit.

The term now carries its own definition, so the comparison table can keep using it.

### A3. "The heuristic returns fast layouts but no certificate, and the set-variable approach carries no valid bound on the visit count."

The certificate/bound doublet was one idea said twice. Replaced with:

> Both methods above return a layout, but neither says how far that layout might be from the best
> one possible. A column-generation framework supplies the missing yardstick, a lower bound on the
> visit count, while it still produces usable layouts.

The word "certificate" no longer appears in the paper.

### A4. "For a homogeneous warehouse the station index becomes a liability."

Replaced by what actually goes wrong:

> Two solutions that differ only in which label sits on which station then describe the same
> physical layout, and the master cannot tell them apart. The relaxation becomes degenerate, the
> integer search spends time revisiting relabelled copies of a partition it has already seen, and
> the |S| pricing calls repeat the same work, since they differ only in the dual.

### A5. "Price-and-complete drive" — simplify throughout

The 340-word paragraph is now six short ones, one per component: why one column at a time fails,
warm start, swap descent, pricing, completion, integer master and polish.

- **A5.1** the flagged AI-sounding pair ("A cardinality-tight partition master does not advance on
  isolated columns…plateaus even while deeply negative reduced-cost columns exist") is gone. In its
  place: *"The master selects at most |S| bundles and they must together cover every product, so one
  new bundle cannot enter any solution until matching bundles for the rest of the catalogue exist as
  well. Progress stalls even though excellent bundles keep arriving."*
- **A5.2** "column-at-a-time" is now defined before it is used: *"Standard column generation adds a
  single new bundle per iteration, the one with the most negative reduced cost. That loop does not
  work here."*
- **A5.3** the `cnt[i][u]` machinery moved out of the main text into a new appendix,
  *Incremental evaluation of the swap descent* (`app:swapeval`). The main text keeps one sentence
  saying the visit change is computed from per-station support counts rather than by re-scanning
  the orders.
- **A5.4** the closing sentence is now plain: *"Whichever is better, the layout from the integer
  master or the best layout found during the loop, is polished for the remaining time. All visit
  counts we report are recounted directly on the raw orders; we never quote the model's internal
  objective."*

### A6. "Lower bound and scope" — deep rewrite

Split into three paragraphs: what the bound is and where its formula comes from; why it stays valid
when a pricing call is cut short; what it is worth in practice. The abstract sentence about
degeneracy became:

> The covering master admits many equally good dual solutions, which slows how fast the bound rises:
> the bound can be weak, but it is never wrong.

### A-general. Redundancy and AI-flavoured phrasing

A pass over the whole paper removed roughly 360 words of repetition (facts restated across Sections
5–7, hedge-and-restate constructions, "not X but Y" parallelisms, rule-of-three lists) and split
sentences that stacked three or more clauses. The Managerial insights section keeps all five of its
messages because IJPR requires it, but each number is now stated once.

---

## Part B — External review

### B1. Ablations of the column-generation design (reviewer weakness; Q2)

Partly answered with real runs, partly deferred, and the difference is stated in the paper.

The one design choice we can evidence is the one that governs scale. The earlier implementation
priced with a coverage variable per raw order on a station-indexed master; it stalled beyond 500
SKUs and, on the industrial instance, returned its warm start unchanged after ten hours under both
engines tried (`results_industrial_benchmark_36.csv`: 1,062,507 visits, identical to the legacy
layout). The current method finishes at 2,000 SKUs and on the 21,874-product catalogue. Section 5
now reports this and immediately qualifies it: the two implementations differ in more than that one
choice, so it is evidence that aggregation makes the decomposition usable at scale, **not** a
controlled ablation. Isolating the greedy pricing step, the completion policy and the final descent
is listed as future work with the protocol it would need.

### B2. Size of U and pricing-model size (Q1)

Recomputed for every instance (`Baselines/report_support_counts.py` → `exp02a_results/support_counts.csv`).

| Instances | \|U\| range | mean | pricing linking rows (mean) |
|---|---|---|---|
| 50 SKUs | 1,398–2,242 | 1,830 | 16,957 |
| 500 SKUs | 15,371–24,393 | 20,367 | 203,521 |
| 1,000 SKUs | 32,743–44,223 | 37,950 | 381,343 |
| 2,000 SKUs | 66,425–92,738 | 77,291 | 778,150 |

Industrial solver instance: 15,975 movable SKUs, 83,183 multi-item orders, **|U| = 82,224**,
1,055,672 linking rows, giving a pricing model of about 98,000 variables built once and re-priced
thereafter.

**Correction this exposed.** The submitted text said "roughly 66,000 distinct supports on the
2,000-SKU instances". 66,425 is one seed; the class spans 66,425–92,738. The text now gives the
range and the mean.

### B3. Dual stabilisation (Q3)

Not implemented, and the paper says so rather than implying otherwise. Section 2 now names
stabilisation as the standard answer to master degeneracy, Section 4.2.6 states exactly what the
bound delivers without it (informative at 50 SKUs, vacuous from 500), and Perspectives keeps it as
the lever that would turn the matheuristic reading into certified gaps. No CPLEX licence was
available on the machine used for this revision, so no stabilisation experiment could be run.

### B4. Heuristic sensitivity to its four constants (Q4)

New experiment: 19 configurations (one-at-a-time multipliers 0.5/0.75/1.5/2 on each of the four
thresholds, plus all-loose and all-tight corners) over all 29 instances, under the per-size budgets
of Table 5. Multipliers apply to the **post-clamp** values, otherwise the community-size bound would
have been unchanged at every size studied. Runner: `Baselines/run_exp02a_sensitivity.py`; results:
`exp02a_results/exp02a_sensitivity.csv` and `_agg.csv`.

**A finding that changed the design.** The heuristic is not deterministic across processes. It
groups products through Python sets keyed by product identifiers, so its greedy tie-breaks follow
set iteration order, which CPython randomises per process. On `syn_50sku_seed1004`, three identical
unseeded runs returned 6,643 / 6,622 / 6,622 visits; with `PYTHONHASHSEED=0` all runs return 6,622.
Every sweep run therefore pins the seed, and the base configuration is repeated across five seeds to
measure the tie-break noise floor — without it, a small delta from a threshold change cannot be
told apart from run-to-run noise.

**Superseded 2026-08-04 by B4bis, and B4bis in turn by B4ter.** The threshold work below stands as
internal record; what the article now reports is the repaired heuristic of B4ter, which is feasible
by construction and therefore no longer needs the failure narrative B4bis built.

### B4ter. The heuristic now respects the workload constraint (supersedes B4bis for the article)

**What changed in the method.** Station assignment used to place communities by historical preference
under the slot capacity alone, never reading constraint~(5). It now (i) restricts candidates to
stations that keep *both* the slot capacity and the workload cap, choosing the most historically
preferred among them with the lowest resulting relative load as tie-break, and (ii) runs a repair
that exchanges products between stations until every station is inside its cap, taking at each step
the exchange that breaks the least co-occurrence weight.

**Why an exchange and not a relocation.** Slot capacity is exhausted by construction: the generator
gives $\sum_s \zeta_s = |P|$ exactly at all four sizes, and industrially each station's capacity is
the count of products it already holds. Every station is full once placement ends, so a move-based
repair has nowhere to move anything and would have run to no effect on all 29 instances. Exchanges
preserve each station's product count, so slot feasibility is maintained for free.

**Placement rule chosen by measurement.** Two rules were implemented and run over all 29 instances.
Balance-first and preference-first are statistically indistinguishable there (paired Wilcoxon
$p = 0.35$, mean difference $+0.006\%$) — unsurprising, since the synthetic generator assigns the
historical station at random, so that signal is noise on this family. The industrial instance, where
the history is real, decides: preference-first gives 1,050,514 visits against balance-first's
1,076,849, the latter being *worse than the legacy layout*. Preference-first ships.

**Results.** All 29 instances feasible (`wl_broken = cap_broken = 0`) with every product placed.
Table 5 heuristic rows become 8,142 (+7.6\%), 78,804 (+3.2\%), 197,146 (+2.5\%) and 484,398
(+0.1\%), all at 0\% workload violation; the heuristic now joins the ranking and its standing
improves with scale, from last-but-one at 50 SKUs to second of seven at 2,000. Table 6 becomes
1,050,514 visits (14.50\% above the best layout, 1.1\% below the site's current one) with **every
station inside the +10\% tolerance**, making it the only method on that instance that is both
feasible and fast. Runners: `Baselines/run_heuristic_benchmark.py`,
`run_industrial_heuristic_alone.py`; results under `exp02a_results_repaired/`.

**A pre-existing industrial defect this surfaced.** The industrial pipeline optimises in `pl_solver`
units and is judged in `pl_full` units. The two disagree per product (ratio 1.03–2.63, mean 1.35) and
per station (a station's solver capacity covers 56–77\% of its true load), so a repair that targets
the solver-unit ceiling lands on its boundary there and overshoots the real tolerance — measured at
+16.7\% on the worst station, 10 of 24 outside +10\%. `run_industrial_heuristic_alone.py` therefore
rebuilds the workload view in evaluation units, giving each station the budget the tolerance leaves
for movable products once the statically fixed ones are paid for. This affects only the heuristic's
own run; the other methods in Table 6 still optimise in solver units, which is worth revisiting.

**Side effects.** The method is now deterministic: repeating the nominal configuration under five
hash seeds returns an identical layout on every instance at every size, so the tie-break noise floor
the appendix used to report is gone (0.000\% everywhere) and the `PYTHONHASHSEED` pinning is belt and
braces rather than a requirement. A latent bug was also closed — the old Step 4 silently dropped
products once every station was full, which corrupts the visit count; every run is now asserted to
place all $|P|$ products.

**Article scope.** Per author decision the article presents the final method only, tested on the 29
synthetic instances plus the industrial case. Appendix D collapses to one table on the shipped
configuration; the dominance table, the 80-instance geometry study and the geometry table are
withdrawn from the manuscript (artifacts retained in the repository). The float budget falls from
15/15 to 13/15. The Data Availability Statement, which promises exactly the 29 instances, is correct
again without edit.

---

*The B4bis record below is retained for provenance.*

### B4bis. Threshold calibration, corrected and extended (Q4, and the open half of Q3)

**(i) A paper↔code mismatch in the kept-edge ratio.** §4.1 described the pair-support ratio as
"at least a tenth of the more frequent product's own demand", but the code divided by the frequency
of the **lexicographically first** endpoint (`combinations(sorted(...))` makes `p1` the alphabetically
smaller identifier, not the more frequent product). The filter was therefore asymmetric and dependent
on product naming, which is what produced the non-monotone `r` rows of the old appendix table
(+0.49, −0.06, +0.06, +0.40 at 500 SKUs). `heuristic_synthetic.heuristic_cslap` now normalises by
`max(cnt_i, cnt_j)`, matching the article; `ratio_denominator="first"` reproduces the pre-fix
behaviour bit-for-bit and is retained only as an audit path.
*Effect.* Kept pairs fall 22 % at 50 SKUs and 0.2 % at 500; at 1,000 and 2,000 SKUs the output is
**per-instance identical**. Table 5's heuristic rows move to 7,715 (+2.2 %) and 78,727 (+3.2 %), the
1,000- and 2,000-SKU rows are unchanged, and the 500-SKU workload-violation share drops 80 %→70 %
(so "80 to 100 %" becomes "70 to 100 %" throughout). Table 6's heuristic row becomes 1,012,538 visits
/ max WL 11,009 / util. sd 37.26 / 9 stations over cap. Every kept-edge-ratio interval now covers
zero at both scales: that threshold has **no effect this design can resolve**, correcting the
"small but measurable, at most 1.2 %" claim listed in the audit table below.

**(ii) The inertness of the two floors is structural, and it expires.** Reporting Δ = 0.00 % is weak
evidence. `Baselines/verify_threshold_dominance.py` replays the filter chain on all 29 instances and
evaluates the two conditions now stated as eq. (12) in §4.1. The frequency floor removes no product
at any scale, with a margin falling 78 → 29 → 14.8 → 7.1 as $N$ grows. The co-occurrence floor removes
no pair either, but the *sufficient condition* certifies that only to 1,000 SKUs (margins 8.05, 2.68,
1.53); at 2,000 it drops to 0.77. The redundancy is therefore size-dependent and would lapse on a
catalogue materially larger than 2,000 SKUs — a caveat the previous wording did not carry.
Artifact: `exp02a_results/threshold_dominance_all.csv`.

**(iii) The calibration recipe was wrong, and the new experiment says so.** The old §4.1 advised
setting the community bound "to the largest value the workload cap will absorb". That recipe was
never tested, and it is untestable on the benchmark family, whose generator ties $|S|$ to $N$ so that
$\zeta = 100$ at every size from 500 SKUs up while $\beta$ is clamped at 15 above 300 products —
$\beta/\zeta$ is the constant 0.15 across the entire published benchmark, which is also the
unanswered half of the reviewer's "MNOPPC independent of $|S|$".
New experiment EXP-02c (`Baselines/make_capsweep_instances.py`, `run_capacity_sweep.py`,
`analyze_capacity_sweep.py`): 80 instances crossing $N \in \{500, 1000\}$ with four station counts so
the same $\zeta \in \{100,50,25,20\}$ occurs at both sizes, ten seeds per cell, station labels drawn
from a separate RNG stream so the order structure is identical across cells at a fixed seed. 926 runs,
$\beta$ from 2 to $\zeta$.
*Result, and it is negative.* Visits fall essentially monotonically in $\beta$ (mean Spearman −0.98,
−14.0 % end to end), so the objective identifies no interior optimum. Neither does the constraint: the
least overloaded setting in every one of the eight geometries still breaches the cap on average (1.01×
to 1.38×), and it is always the *smallest* bound, at which clustering is effectively off. Only 24 of
940 runs are feasible, all in the two $\zeta = 100$ cells; six of eight geometries admit no feasible
layout at any $\beta$. Because the overload survives switching the clustering off, it is produced by
the **station-assignment stage**, which never reads constraint (5) — no clustering threshold can
repair it. The pre-registered scaling hypotheses ($\beta^\ast \sim \zeta$ vs $\beta^\ast \sim N$) are
reported as **not estimable**: the quantity they predict does not exist on 70 of 80 instances, and the
analysis withholds the verdict rather than reading it off the 10 survivors.
Appendix D is restructured into three parts (dominance, sensitivity, geometry) with two new tables,
`tab:dominance` and `tab:capsweep`; the orphan hardware paragraph that opened it moved to §5.2, where
it belongs and where it was previously absent.

**Methodology references added** (`IJPR_CSLAP.bib`): Barr et al. (1995), Hooker (1995), Eiben & Smit
(2011), López-Ibáñez et al. (2016), Derrac et al. (2011).

**Reproducibility repairs found along the way.** (a) The industrial heuristic row was not
reproducible: two unpinned runs returned 1,014,600 and 1,014,784 visits with 10 and 9 stations over
cap. `run_industrial_heuristic_alone.py` now re-execs itself with `PYTHONHASHSEED=0`, after which
repeated runs agree exactly. (b) Figure 11's two panels had **no generator in the repository**;
`plot_industrial_heuristic_workload.py` now draws them from the same run that produces the Table 6
row, and cross-checks that the number of stations over capacity equals that row's `wl_broken`.
While writing it, an error was caught: `TIME_CAPACITY` is expressed in speed-adjusted units and must
never be compared against raw line counts, which differ by orders of magnitude on this site.
(c) `evaluate_full_metrics` moved to `Baselines/industrial_metrics.py` so a solver-free re-run is
possible on machines without gurobipy; `run_benchmarks_industrial.py` imports it back, keeping one
definition.

**Timings.** The article reports a single environment, the 16-core server of Section 5.2, and the
`Budget (s)` and `Time (s)` columns are read on that machine. The heuristic's entries are to be
confirmed there on a quiet box before submission; the layouts themselves are deterministic, so
visits, workloads and violations are unaffected by where they were computed.

### B5. Multi-homing for high-demand SKUs (Q5)

Sketched in Perspectives with the change it implies for the decomposition: the covering rows already
allow a product in several selected bundles, so it is the exactly-once tie that relaxes, to a limit
on how many stations a product may occupy, with each extra copy's replenishment cost charged in the
pattern cost so pricing proposes a duplicate only when the visits saved outweigh it.

### B6. Bounded reassignment detail and CG integration (Q6)

Section 6.3 now states the model completely: objective, capacity and workload rows are those of
Section 3, only constraint (11) is added, the legacy layout stays feasible for every k, and the
sweep is solved with the set-variable engine. The CG integration the reviewer asks about is stated:
counting, per bundle, how many products would leave their legacy station turns the limit into one
knapsack-style row over the bundle variables, whose dual enters pricing as a per-product penalty for
moving a product. We flag that we have not run that variant.

### B7. Solver configuration and reproducibility (Q7)

Section 4.2.4 now gives the CG configuration (one configuration for all instances and sizes, four
threads, seed 42) and both stage splits — 8/70/85 % for the homogeneous drive, 5/62/74/82 % for the
station-indexed industrial run. The Data availability statement explains that Hexaly and CPLEX
licences cannot be redistributed, states what is needed to reproduce a run, and confirms the 29
synthetic instances are released with the seeds and generator settings that produced them. Code is
not released: the industrial pipeline is entangled with confidential client data.

### B8. Statistical power at K = 3 and 4 (reviewer weakness)

No new instances; instead the paper reports how the instances split where the intervals are wide,
computed from the existing per-instance results. The splits are unanimous: the set-variable
reference beats GA and SA-C on 4/4 at 1,000 SKUs and 3/3 at 2,000; the column generation beats the
reference on 3/4 and 3/3. The text states plainly that a unanimous split across few instances is
weaker evidence than a tight interval across many.

### B9. Missing related work (LNS, CP-SAT, learning-based hybrids)

One paragraph added to Section 2, with four references verified against their publisher records:
Ropke and Pisinger (2006) and Pisinger and Ropke (2010) for large neighbourhood search, Perron,
Didier and Gay (2023) for CP-SAT, and Barnhart, Jacquillat and Schmid (2024) for the learn-then-
optimize neighbourhood search in robotic warehousing. The last is positioned as a complement: it
schedules operations over a short horizon, whereas this paper fixes the placement those operations
inherit.

### B10. Queueing and throughput (reviewer weakness)

Unchanged in substance and already honest: the labour figure is presented as a linear projection at
a fixed time per visit, explicitly not a queueing result, with discrete-event simulation named as
the way to confirm it.

### B11. Table typos and formatting

Audited. One real defect found and fixed: a stray `\\` inside an unaligned display in the pricing
subproblem, which stops a LaTeX build. Table numbers were re-checked against their source files and
reproduce (13.7 %, 5.8 %, 9.09 %, all k-sweep reductions).

---

## Part C — Journal compliance

| Item | Before | After |
|---|---|---|
| `\usepackage{float}` | absent | added (line 34) |
| ORCIDs | absent | placeholder comment per author — **fill before submission** |
| Funding details | buried in Acknowledgements | own section; **CIFRE grant number still `TODO`** |
| Back-matter order | Ack → Contrib → Disclosure → GenAI → Notes → DAS | Contributions → Ack → Funding → Disclosure → GenAI → Notes → DAS |
| Floats | 12, all `[H]` | 12 + 1 appendix sensitivity table = 13 of the 15 allowed, all `[H]` |
| Abstract | 194 words | 194 words (untouched, cap is 200) |
| Word count | ~8,070 excl. references | see final check in Part E |
| Citations ↔ bibliography | 29 ↔ 29 | 33 ↔ 33, no dangling key either way |

---

## Part B2 — Integrity audit (found during this revision, not raised by the reviewer)

A full trace of every number in the paper against the stored result files turned up problems the
external review did not mention. They matter more than most of the review's own points, because the
synthetic instances ship with the paper and a referee can recompute them.

### Two blocking items, both now marked `TODO(before submission)` in the tex

**1. Table 5's Time column was the budget, not the time actually spent — and the budgets were not
common.** Measured against `exp02a_per_instance_v3.csv` and `exp02a_cg_setpart.csv`:

| Size | Table said | Set-variable actually used | CG budget | CG actually used |
|---|---|---|---|---|
| 50 | 120 | 123 | 120 | 86 |
| 500 | **300** | **1,148** (one instance 4,684) | **600** | **476** |
| 1,000 | 600 | 645 | 600 | 599 |
| 2,000 | 1,200 | 1,049 | 1,200 | 1,199 |

So the claim that the two methods "each consume the full budget at every size, so their visit
comparison is made at equal computational effort" was false in both directions: at 500 SKUs, where
the reference wins by 0.8 %, it had 2.4 times the column generation's wall clock; at 2,000 SKUs,
where the column generation wins by 2.4 %, it had 14 % more than the reference. SA-C also exceeded
its stated budget at 1,000 SKUs (977 s mean, one run 1,747 s).

*Action taken:* the CG runner's 500-SKU budget is corrected to 300 s, the protocol paragraph is
rewritten to describe measured times under a common cap, and the whole benchmark is being re-run
under the published caps on the machine that has CPLEX — see `RERUN_IJPR_BENCHMARK.md`. Table 5, the
paired tests and every gap figure in Section 5 are regenerated from that re-run.

**2. Table 9 (out-of-sample weeks) has no backing artifact, and the delivered data cannot produce
it.** The six visit totals appear only in earlier manuscript files, never in a result file. The
industrial order file is `PRODUCT;ORDER;QTY;STATION;BOX_ID` — no date column — so "13 weeks", the
10/3 and 8/5 splits and the "66-day quarter" cannot be rebuilt from it.
`Baselines/build_berner_instance.py` reproduces a 10/3 and 8/5 split by ranking on order id as a
time proxy, which is a *different* experiment and would have to be described as one.

*Decision needed:* supply the dated extract plus the per-split run output, or delete the subsection,
Table 9 and the rolling-window managerial insight. Nothing else in the paper depends on them.

### Corrected in place

| Item | Was | Now |
|---|---|---|
| Pooled Wilcoxon p-values | 2.6e-6 / 2.9e-6 / 2.4e-5, labelled "exact" | 3.7e-9 / 7.5e-9 / 2.0e-6 (recomputed exact) |
| Pooled visit lead | 1.0 % | 0.97 % |
| Industrial multi-item orders | 83,183 | 83,179 |
| Table 8 footnote a | "SA-C's per-station loads were not retained, so its violation flag is set conservatively" | "SA-C exceeds the tolerance on four stations" (the artifact records `wl_broken=4`) |
| Utilisation std dev | "standard deviation of the relative change in each station's utilisation factor" | defined as computed: dispersion of utilisation levels across stations |
| Table 8 caption | "26 stations" | 26 physical, 24 evaluated |
| Table 10 caption | k as % of 21,874 only | adds that only 15,975 products are movable, so k=5,000 is 31.3 % of the decision pool |
| k-sweep budget | "one-hour budget each" | one-hour limit, four runs respect it, k=1,000 overran to 3.1 h |
| Abstract and conclusion | set-variable "strongest"/"best" across 50–2,000 SKUs | scoped to ≤1,000; the column generation leads at 2,000 |
| GA seed variance | "about 1 %", stated generally | scoped to GA, 50 SKUs, three instances, 0.2–2.2 % |
| Managerial claim | "never breached a workload cap in any experiment" | names which cap on which dataset |
| Table 8 baselines | GA/SA-C rows unexplained | discloses that these are the capacity-respecting runs, and that earlier runs reached fewer visits while overloading stations |

### Removed for lack of a retained artifact

The extended-budget probe figures (86,365 / 226,566 / 404,882), the industrial CG drive counts
(106 iterations, 2,670 columns, 680,270-visit warm start) and the pricing build timings (21 s, 0.2 s)
appear in no stored log. The surrounding sentences now state only what is traceable, with a `TODO`
marker where the re-run should restore the detail.

### Checked and correct — no change made

Every mean, confidence interval, gap, violation share and per-size p-value in Table 5; every visit,
time, workload and utilisation figure in Tables 8 and 10; all derived industrial percentages
(13.7 %, 5.8 %, 9.09 %, 145,042, 61,663, 16,099, 2,198); the |U| figures added this revision; and the
lower-bound comparison, whose premise (no order in any of the 29 instances has a single item, so the
bound and the reported visits are on the same scale) was verified independently across all 623,823
orders.

---

## Part D — Deliberately not done

- **No new CG runs.** The set-partitioning solver needs CPLEX, which is not installed on this
  machine. Reported CG numbers are unchanged and now traceable to recovered artifacts
  (`exp02a_results/exp02a_cg_setpart.csv`, `results_industrial_cg_setpart_matchhexaly.csv`).
- **No dual stabilisation, no CP-SAT or LNS baseline, no discrete-event simulation, no extra large
  instances.** Each is named in Perspectives with the protocol it would need.

## Part E — Verification before submission

1. Fill the four ORCIDs and the CIFRE grant number (both marked `TODO` in the tex).
2. Upload to Overleaf's Taylor & Francis *Interact (APA)* template: `IJPR_CSLAP_v2.tex`,
   `IJPR_CSLAP.bib`, and the seven referenced files in `Images_CSLAP/`. `interact.cls` and
   `apacite` come from the template.
3. Confirm on Overleaf: no undefined references or citations, every float placed `[H]`, and the
   final word count within 12,000 including abstract, tables, captions and references.

---

## Part F — Re-run integration (2026-07-30)

The synthetic benchmark was re-executed on the CPLEX/Hexaly machine under the budgets the paper
prints (`RERUN_IJPR_RESULTS.md`). Instance hashes matched 87/87 before and after; 122/122
metaheuristic-MILP rows and 29/29 CG rows completed with status OK. Table 5, the statistics and
every downstream claim were rebuilt from the new per-instance data by
`Baselines/rebuild_table5.py`, which recomputes means, 95 % t-intervals, mean per-instance gaps,
the time column and the paired tests from
`exp02a_results_rerun/exp02a_per_instance.csv` + `exp02a_results/exp02a_cg_setpart.csv`.

### What the re-run changed in the results

The correction to Hexaly's budget at 500, 1,000 and 2,000 SKUs, where the stored campaign had
overrun, lowered its solution quality at the two largest sizes and reversed the headline ordering.

| | Before | After |
|---|---|---|
| Best feasible method, 1,000 SKUs | set-variable (192,330) | **CG-SetPart (192,452 vs 196,515)**, $-2.0$ % |
| Best feasible method, 2,000 SKUs | CG by 2.4 % | **CG by 5.9 %** (476,692 vs 506,763) |
| CG vs reference, pooled | $-0.2$ % mean gap, $p=0.11$ | $-0.57$ % mean gap, $p=0.73$ |
| Hexaly measured time @500 | 1,148 s mean (range 455–4,684) | 309.6 s (range 306.9–311.3) |

CG's workload and capacity violation counts stay at zero on all 29 instances, so it is now the best
*feasible* method at both large sizes.

### Edits made

- **Table 5** repopulated; rows re-sorted by mean visits; green shading redefined as the
  lowest-visit *feasible* method and moved to CG at 1,000 and 2,000 SKUs. Time column renamed
  "Time budget (s)" and now prints the imposed cap where the method reached it and the measured
  convergence time where it finished early, with footnotes for SA-C's stopping-rule overshoot and
  for Hexaly's times excluding model construction. The 2,000-SKU bracket reports observed
  [min, max]; the 1,000-SKU interval is flagged as a range.
- **Deleted the false equal-effort claim.** The previous text said all optimising methods
  "consume the full budget at every size, so their visit comparison is made at equal computational
  effort". CG converges at 86 s of 120 and 256 s of 300 at the two smaller sizes, so the claim was
  untrue there; the protocol paragraph now states where each method stands relative to its cap.
- **Section 5.3** rewritten: four findings replacing three; the reference is no longer described as
  best at every scale; p-values updated ($0.003$ and $0.006$ for CG vs reference at 50 and 500;
  pooled $0.73$); win counts updated (CG now takes 4/4 at 1,000, previously 3/4).
- **Underpowered tests stated as such.** At $n=4$ and $n=3$ no exact signed-rank test can reach
  significance, because the smallest attainable two-sided $p$ values are $0.125$ and $0.25$. The
  text says this and falls back to reporting how instances split.
- **Heuristic never reported as a winner.** It posts the lowest visit counts at 1,000 and 2,000
  SKUs but breaches the workload cap on 100 % of instances there, so the table caption, Section 5.3
  and the shading rule all exclude it from ranking claims and pair its counts with its violation
  rate.
- **Abstract, conclusion and the "match the tool" managerial insight** updated for the reversed
  ordering. The managerial paragraph now separates the two cases: for a heterogeneous site such as
  Company~A the set-variable approach still gives the deepest reduction, while on interchangeable
  stations CG takes over from 1,000 products upward.
- **Table 9** kept, its artifact having been located (`Compare_W.ipynb`, cells 8–9; all twelve
  values match). The caption now records that the splits are cut on the dated extract's delivery
  dates, that the released file carries no dates, and that a reader working from the released file
  can reproduce the design but not the exact figures.
- **Section 4.1 and new Appendix table `tab:sensitivity`** report the 667-run threshold sweep. The
  unbacked claim that the output "is robust under moderate variation" is replaced by the measured
  result: two frequency floors are bit-identically inert, the kept-edge ratio moves visits by at
  most 1.2 %, and the community size bound is the only threshold that matters, trading visits
  against workload feasibility. Tie-break noise floor 0.09 % measured over five hash seeds.
- **Removed** the stale `exp02a_results/exp02a_cg_setpart_aggregated.csv`, which derived from the
  superseded CG campaign.
- **Resolved two `TODO` markers.** The industrial iteration and column counts were already absent
  from the prose, so the marker went; the per-day figures are now stated on an explicit basis
  ("the 66 operating days recorded in the extract") rather than as bare derived constants.

### Still open

- Four ORCIDs and the CIFRE grant number.
- The 66-operating-day divisor behind the per-day stop figures is attributed to the dated extract
  but could not be recomputed here, the dated file being on the other machine. Worth confirming
  against that extract's distinct delivery dates (the window holds 91 calendar days and 65
  weekdays).

### Part G — Integrity audit of the re-run integration (2026-07-30)

An independent audit recomputed every figure in Table 5, the appendix sensitivity table and the
statistics from the raw per-instance sources, and audited `Baselines/rebuild_table5.py`. Table 5
and `tab:sensitivity` passed in full: all 24 means, all 24 bracket endpoints under both conventions,
all 24 gaps, all time entries, all violation rates, all twelve exact Wilcoxon p-values (cross-checked
by brute-force enumeration of sign assignments), and both noise floors reproduce exactly. Seven
blocking defects were found elsewhere, all in prose or provenance, and all are now fixed.

| Fix | Was | Now |
|---|---|---|
| §3.2.5 lower bound | mean bound 3,272 vs 7,592 visits, from the retired 600 s-at-500 campaign | **3,312 vs 7,590**, from `exp02a_cg_setpart.csv`; no longer contradicts Table 5 |
| §7 k-sweep budget | "four of the five runs respect [the one-hour limit] and one overruns to 3.1 hours" | every run exceeds it, four by 4.5–20.6 % and $k=1{,}000$ threefold; attributed to the same build-time-outside-limit mechanism as Table 5's footnote |
| §5.3, §7 old CG | "returned its warm start unchanged after the full ten hours" | terminated after **1.0 h and 3.0 h** of the ten-hour allowance (3,542 s Hexaly, 10,654 s Gurobi) |
| §5.3 uniqueness | "the only method that respects both constraints on all 29 instances" | every method except the heuristic does; CG is the one whose standing improves with size |
| §5.3 dominance | "dominates every method that respects the cap" (contradicted the tie with the reference in the same sentence) | dominance stated against the two literature baselines only |
| §4.1 sensitivity | "three of the four thresholds are inert" | **two** are inert; the kept-edge ratio is small but above the 0.09 % noise floor — *superseded by B4bis: after the ratio-denominator fix every kept-edge-ratio interval covers zero, so three of the four are in fact without resolvable effect* |
| §4.1 recipe | "set the community bound to the largest value the workload cap will absorb" | withdrawn: on six of eight warehouse geometries the cap absorbs nothing at any bound (B4bis iii) |
| §4.1 ratio | "a tenth of the more frequent product's own demand" | the code divided by the lexicographically first endpoint; code corrected to match the article (B4bis i) |
| §7 industrial deviations | CG range [−3.8 %, +5.8 %] had no producing artifact (the CSV's `dev_*` columns measure deviation against the cap, not the legacy load) | recomputed by the new `Baselines/report_industrial_deviation.py`: **[−3.78 %, +5.82 %]**, std 2.41 %, 10 stations above legacy, 24/24 inside the +10 % tolerance — matching every printed value |

Reporting fixes in the same pass: the GA/SA-C early-stop claim now restricted to 50 SKUs; "converges"
replaced by "returns before the cap", since the two early finishes are stage exhaustion rather than
the pricing-out criterion; Table 5's bracket column relabelled "95 % CI / [min, max]"; the |U|
industrial figures identified as the pruned solver instance; the non-monotone workload-violation
sequence stated as endpoints only; the GA probe seeds documented as a probe, with the effect of
including them quantified (7,767 → 7,770); the appendix scope restricted to 50 and 500 SKUs, with the
50-SKU clamp no-op disclosed; Table 8's separate GA/SA-C harness disclosed; Table 9's caption now
points to the external notebook as well as the dated extract; and a new paragraph in §5.2 states the
hardware, CPLEX and Hexaly versions, thread count, all seeds, and the `PYTHONHASHSEED=0` control the
heuristic requires.

The per-visit dwell constant behind the "nine working days" figure was never recorded, so the
arithmetic is now parametric: **40.3 hours freed per second of per-visit cycle time**, with 1.7 s
given as the illustrative value that reproduces the original figure.

The industrial `MILP Gurobi` row of `results_industrial_benchmark_36.csv` is byte-identical to the
`Heuristic` row across visits, time, max workload and utilisation spread, so it is a logging
artifact rather than a result. The manuscript no longer asserts an industrial outcome for the binary
formulation; it states only that the row is absent and points to the synthetic evidence, which is
sourced.

### Still open after Part G

- Four ORCIDs and the CIFRE grant number.
- The set-variable industrial deviation range [−5.9 %, +9.6 %]. Its standard deviation (4.48) and its
  ten-stations-above-legacy count are both confirmed from `results_industrial_benchmark_36.csv`, and
  the profile is plotted in Figure 5, but the layout file itself is not in either repository, so the
  two endpoints rest on the original run's recorded output. Locate that assignment on the CPLEX
  machine and re-run `Baselines/report_industrial_deviation.py --layout <file>` to close this.
- The 66-operating-day divisor behind the per-day stop figures.
- `Compare_W.ipynb` and the dated extract behind Table 9 should be versioned into the repository.

### Part H — Separating the bound from the layout (2026-07-30)

A co-author asked how the column generation can return before its budget at 50 and 500 SKUs and
still lose to the set-variable approach, and whether the paper was implicitly selling the method as
exact. Both concerns were justified and the manuscript now addresses them directly.

**Two distinct claims were being blurred.** Pricing out proves the *linear* master is solved; it says
nothing about the layout. The gap is large here: at 50 SKUs the bound settles near 3,312 while the
best layouts need about 7,556 visits. On top of that integrality gap, the layout is produced by the
dual-guided greedy step, the greedy completion, the swap descent and a final integer master
restricted to the bundles a run happened to generate, with no branching anywhere. Column generation
supplies the columns the linear programme needs, not those an optimal integer solution would need. A
run can therefore price out and still be beaten by a metaheuristic. `sec:cgbound` gains a paragraph
saying exactly this, and `sec:reliability` explains the 50- and 500-SKU case in those terms.

**Neither early return was a price-out.** 85.9 s of 120 and 256.1 s of 300 are 71.6% and 85.4% of
budget, just past the 70% generation and 85% integer-master boundaries of the stage split, which is
the signature of a run that used its whole generation window and then found its final descent at a
local optimum. The text states this rather than claiming convergence, which no artifact records.

**Four misuses of "exact" removed.** The word had been used to mean "model-based" in places where it
reads as "provably optimal": the warm start given to "every exact method", "all exact models are
seeded", "the two exact approaches", and Hexaly described as pairing local search "with exact
methods". Neither the Hexaly engine nor the column generation is exact, and the reference sentence
now says so. The Hexaly description now notes the engine is heuristic and reports no bound.

The bound machinery itself was re-verified against `Baselines/cg_setpart_cplex.py`: `rc_lb` is
CPLEX's dual bound on the pricing MIP minus the cardinality dual, valid on timeout; the Farley
expression is monotone across iterations; exact pricing runs every iteration and is the sole
convergence test. The validity claims in the paper are accurate. What was missing was the statement
of their limits.

### Part I — Table 5 layout (2026-07-30)

The table overflowed the text block. Rebuilt to fit, with no change to any value.

- `tabular*` at `\textwidth` with `\extracolsep{\fill}`, so the table now spans exactly the text
  width instead of overrunning it. Font stays at `\small`.
- Row and column labels shortened, which is what created the room: "Set-variable MILP" to
  "Set-variable", "CG (set-part.)" to "CG", "Feasible start (LPT)" to "LPT start", and the headers to
  Method / Mean visits / Interval / Gap / Budget (s) / WL viol.
- Caption cut from six sentences to two, keeping only the reference, the shading rule and the reason
  the heuristic is excluded from it.
- Footnotes a and b deleted. Footnote a duplicated the caveat already in Section 5.3, so nothing was
  lost. Footnote b's two substantive disclosures — SA-C's stopping-rule overshoot and the set-variable
  engine's build time falling outside its search limit — moved into the Section 5.2 protocol prose,
  where the k-sweep discussion now points as well. The surviving unlabelled note keeps the load-bearing
  definitions: solver identification, the interval convention including the [min, max] substitution at
  2,000 SKUs, the gap definition with the pooled figure, the time convention, and the LPT anchor.
- The four block-header rows are now black with white text, which separates the size blocks without
  needing the inter-block rules.

Verified after the rewrite: 24 data rows all carrying six columns, four black headers and four green
best-feasible rows, environments balanced, and every mean, interval endpoint and gap still matching
`table5_rebuilt.csv`.

### Part J — AI-pattern sweep of the full narrative (2026-07-30)

Ran the humanizer checklist over the whole manuscript. The register is a formal OR paper, so the
guide's "personality and soul" section does not apply: neutral academic prose is the correct human
voice here, and no opinions or first-person colour were added.

Clean on inspection, no action taken: no em or en dashes anywhere in the prose (the `---` matches are
the comment-block separators, and every `--` is either a TikZ path segment or a numeric range such as
"Steps 1--2"); no curly quotes; no negative parallelisms; no participle padding; no filler or hedging
formulas; no significance inflation. "Landscape" and "robustness" were checked and kept, since both
are standard optimisation vocabulary here rather than AI filler. The naming variation across
"set-variable approach", "set-variable reformulation", "Hexaly" and "the reference" is principled,
each denoting a different aspect, so it is not synonym cycling. Sentence length varies from 7 to 48
words in the results narrative.

Fixed:

| Pattern | Was | Now |
|---|---|---|
| Signposting plus filler | "It is worth stating plainly what the bound does not do, because the two sides of this method carry very different guarantees." | "The bound and the layout carry very different guarantees." |
| Copula avoidance | "its result stands as a matheuristic reading" | "its result is a matheuristic reading" |
| Forced rule of three | "it spreads workload most evenly, ignores correlation, and pays the largest visit penalty" | recast causally: ignoring correlation is why it spreads evenly and pays the penalty |
| Padding | "which is what one expects of a local-search engine whose move space grows faster than the budget it is granted" | "because the move space of a local-search engine grows with the catalogue while its budget does not" |
| Rhetorical verb | "deserves a separate reading" | "needs a separate reading" |

The larger problem was density rather than vocabulary, and it was of my own making: the re-run
integration had grown four paragraphs to between 9 and 18 sentences, which is the same wall-of-text
fault the supervisor flagged in the price-and-complete subsection. The 18-sentence paragraph in
Section 5.3 is now three, the 11-sentence findings paragraph is two, and the sensitivity paragraph in
Section 4.1 is two. One 9-sentence paragraph in Section 3.2.5 was left intact: it carries a single
argument with explicit "first" and "second" signposting, and splitting it would break the reasoning.

The abstract was re-read and left as it stands. Its two triples are factual, three real methods and
three real properties of the column generation, not decorative padding.

### Part K — IJPR literature positioning (2026-08-01)

Reviewer point: IJPR asks for an exhaustive reading of prior work in *Production Research* itself,
and the bibliography carried only two IJPR entries out of 31. Sourced entirely from the user's
NotebookLM notebook "IJPR Articles on CSLAP" (7 distinct IJPR articles across 11 sources); no open
web search was used. Bibliography now holds 40 entries, 10 of them IJPR.

Added and woven into Section 2:

| Work | Where | Role in the argument |
|---|---|---|
| Pang & Chan (2017) | §2 ¶1, Table 1 | Correlated storage by association-rule mining, scored in travel distance: the closest predecessor whose objective we replace |
| Larco et al. (2017) | §2 ¶1, Table 1 | IJPR storage assignment that optimises worker discomfort rather than distance, establishing that the objective should follow the system |
| Jaghbeer et al. (2020) | §2 ¶2 | 119-study review of automated picking; design links to performance through system throughput, not picker travel |
| de Koster et al. (2012) | §2 ¶2, Table 1 | Pick-and-sort zoning by batch completion time; sets the number of zones where we fill zones whose count the hardware fixes |
| Saylam et al. (2023) | §2 ¶4 (new), Table 1 | Min--max makespan in synchronised dynamic zone picking: balance as the objective |
| Vanheusden et al. (2022) | §2 ¶4 (new), Table 1 | Balancing measures under hard picker capacity; the right measure depends on the managerial reason for balancing |
| Vanheusden et al. (2023) | §2 ¶4 (new) | Planning models that omit real operating constraints yield schedules a warehouse cannot run |

The new fourth paragraph of Section 2 uses Saylam and Vanheusden to state a choice the paper had
left implicit: balance can sit in the objective or in the constraints, and we put it in the
constraints because an installed conveyor gives each station an engineered budget that operations
treat as a line not to cross. Table 1 grows from six comparators to ten.

**Not added, deliberately.** de Vries et al. (2016) was named in the review but studies picker
personality with pick-by-voice and RF terminals. Our system has no walking picker, so the citation
would support no claim we make. Larco and de Vries were also available only second-hand, as entries
in the reference list of the Vanheusden review rather than as sources in the notebook; Larco is
cited on the single point that review actually documents.

Two bibliographic traps resolved against the sources: de Koster et al. is dated **2012**, the issue
year for IJPR 50(3), not the 2011 online-first date; and Pang & Chan is carried without volume or
pages because the notebook holds the accepted manuscript, with a `TODO` in the `.bib`. A third was
avoided: the review lists van Gils et al. (2018) as "IJPR 197(Part C)", but volume 197 with those
pages is *International Journal of Production Economics*, so that work was not added on this record.

**Word budget.** These additions pushed the estimated total past the 12,000 cap. Recovered by
tightening prose written earlier in this revision (the industrial table note, the data availability
statement, the reproducibility paragraph, the GA-probe sentence, and a bound-versus-layout passage
that duplicated Section 3.2.5), and by removing **Notes on contributors**, which is a Taylor &
Francis template element absent from the sequence IJPR's instructions require. Its removal also
brings the back matter into exact agreement with that sequence. The section is preserved at
`C:\tmp\tex_with_bios_backup.tex` and can be restored in full if the editor asks for author
biographies; roughly 100 words would then have to come out elsewhere.

Estimated total ~11,965 of 12,000; abstract 198/200; floats 13/15; citations and bibliography in
exact 1:1 correspondence.

### Part L — Table 8 note pruned (2026-08-01)

The note under the industrial table ran to 182 words and repeated the main text. Cut to 107 with
nothing unique lost.

Removed: the sentence reporting that ten stations rise above their raw legacy load under the
set-variable and column-generation layouts and twelve do so under the legacy layout itself, which
the Section 7 discussion already states two paragraphs below; and "Time 36,000 s is the full
ten-hour budget", which duplicates both the caption and the Time column.

Kept, because each appears nowhere else: the definition of Max WL; the feasibility rule, including
the 10,915-line bound on the busiest station and the warning that a Max WL under that figure does
not certify feasibility, since the test is per station; the solver behind each row; and the
provenance of the GA and SA-C rows with the visit counts of the earlier, better-scoring runs that
were rejected as infeasible (GA 1,027,131; SA-C 1,077,070, busiest station 22,179 and 10,287 lines).
That last item is the honest disclosure that the table reports the feasible runs rather than the
lowest-visit ones, so it stays.

### Part M — Justifying the binary-formulation claim (2026-08-02)

The manuscript asserted in five places that the binary formulation stalls under branch-and-bound,
but neither Table 5 nor Table 8 carried a row for it. The claim rested on one legacy run
(`results_gurobi_alone_syn_1000sku.csv`: Gurobi returns its warm start unchanged, 290,549 visits at
3,669 s) on a single instance that is **not** part of the 29-instance benchmark and ran under a
3,600 s limit rather than the published 600 s. The industrial `MILP Gurobi` row is unusable, being
byte-identical to the Heuristic row across four fields.

**Attempting the runs locally failed on licensing, twice.** The installed Gurobi is a restricted
non-production licence and rejects the model at every benchmark size, including 50 SKUs
("Model too large for size-limited license"). HiGHS through `scipy.optimize.milp` accepts no MIP
start, so it cannot test a claim that presupposes the LPT seed; given 120 s on the smallest instance
it returned no feasible solution at all.

**The load-bearing half of the claim turned out to be provable, which is stronger than any run.**
New Appendix D proves that the linear relaxation of the binary programme has value at least $|O|$
always, and exactly $|O|$ whenever the uniform fractional assignment is feasible, which holds
throughout the synthetic family. The root bound is therefore the trivial statement that every order
visits at least one station, independent of the correlation structure that makes one instance harder
than another. `Baselines/verify_lp_bound.py` confirms it numerically: the relaxation returns 2,482
and 1,697 on the first two 50-SKU instances, exactly their order counts.

The three prose claims now cite Proposition 1 rather than asserting the behaviour, and the protocol
paragraph's "no non-trivial bound at 500 SKUs and beyond" is corrected to the stronger and now
proved "at any size".

**Still open.** The empirical half, that branch-and-bound fails to improve on the LPT seed under the
published budgets, remains supported only by the single legacy instance. Producing the Table 5 row
needs a solver this machine cannot provide. `Baselines/run_exp02a_binary_milp.py` is written and
ready: it warm-starts from the same LPT seed, enforces the per-size budgets, recounts visits on the
raw orders, and records the dual bound and whether the layout moved off the seed at all. It calls
Gurobi, so running it on the CPLEX machine requires either a full Gurobi licence there or a docplex
port of `milp_gurobi_synthetic.run_milp_gurobi`.

**Word budget.** Appendix D sits in an appendix deliberately: IJPR counts "Abstract, Main Text,
Tables, References and Figure/Table Captions", and appendices are not in that list. The main text
carries a five-line summary and a pointer. Counted total ~11,996 of 12,000.

### Part N — Narrative clean-up for referee legibility (2026-08-04)

The draft read as over-generated: too many numbers inline, redundant prose around every table, and
terms used before they were defined. This pass changed no result. Nothing was re-derived from the
project; everything is grounded in the article's own tables.

**Corrected a real error introduced in the previous round.** Section 5.3 asserted that the paired
tests ran "on per-instance percentage gaps". They do not. Reproducing the published values against
`exp02a_results/final_formulation_analysis_perinstance.csv` shows the tests were run on **raw
per-instance visit differences** with ties dropped: that convention returns 0.0488, 0.0010, 0.0273,
1.00, 0.25 and 0.1828, matching six of the seven published figures. On percentage gaps the pooled
CG comparison would return 0.0258 and contradict the paper's own null result. The protocol
paragraph now states the raw-difference convention and notes that the Gap column measures size
while the test measures consistency. Every published p-value is printed unchanged; only cells the
article did not previously report were recomputed.

**Fixed a comment that was deleting text from the compiled PDF.** A `% TODO(before submission)`
marker sat on the same source line as live prose, silently removing two sentences including the
"best found rather than a proven optimum" caveat. The caveat is restored, reworded to claim nothing
about any solver. All TODO markers are now gone from the `.tex` and the `.bib`: the ORCID
placeholders were deleted, the Funding statement no longer prints a placeholder grant number, and
`pang2017datamining` was completed to IJPR 55(14), 4035--4052.

**Legibility.** A statistical-protocol paragraph now defines the paired test, the null, and the
$2^{1-n}$ floor before any $p$ appears. All p-values moved out of prose into a new table
(`tab:tests`) whose Min.\ $p$ column shows that the 1,000- and 2,000-SKU rows are saturated rather
than failing. Section 5.3 was rewritten as five bold-led findings. The two pooling conventions,
which disagree in sign, were split into their own paragraph.

**Tables and figures.** Table 4 rebuilt with one fixed method order across all four blocks, a
"Gap vs.\ ref" header, a "Time (s)" header, `n` instead of `K` (removing the collision with the
pattern set $K_s$ and the relocation cap $k$), and `[min, max]` marked in the 2,000-SKU block. The
industrial table gained a "Reduction (%)" column carrying the headline 13.65 and 5.80 figures,
which previously appeared only in prose. The three near-identical workload figures were merged into
one three-panel float, and the freed slots went to `tab:tests` and a new crossover figure built
from Table 4's Gap column. Display items stand at exactly 15.

**Wording.** Method names normalised to "set-variable MILP" and "binary MILP"; "cap" used for the
time limit throughout. Every characterisation of the Hexaly solver's internals was removed, in both
directions, since the paper cannot claim what the engine does. "Support", "pattern", "master",
"pricing" and "LPT" are now defined on first use. The contributions paragraph was split into three.
The temporal claim "captures most of the attainable benefit" was corrected to over half on the
10-week split and nearly three-quarters on the 8-week one, which is what the table supports.

**Still open.** GA and SA-C parameters are not reported, so those two baselines are not reproducible
from the text alone. The industrial `Binary MILP` and station-indexed `CG` rows have no producing
artifact in this repository. The set-variable industrial deviation range rests on the original run's
recorded output.

Abstract 191 words, main text 10,030, appendices 769, total 10,799 of 12,000.

### Part O — GA and SA-C parameters, and two corrections they exposed (2026-08-04)

New Appendix D reports the parameters of both metaheuristic baselines, closing the reproducibility
gap left open in Part N. It is written as prose rather than a table so that it adds no display item
to the 15/15 count. Values were read from `Baselines/ga_baseline.py` and `Baselines/sa_correlated.py`
and checked against the harness that produced the published rows,
`Baselines/run_exp02a_multiseed.py`, which passes only `time_limit` and overrides no algorithmic
parameter. The published GA, SA-C and LPT rows of Table 4 reproduce
`exp02a_results_rerun/table5_rebuilt.csv` exactly.

**Correction 1: the shared warm start did not exist on the synthetic campaign.** Section 4.4 stated
that "every method is seeded with the same feasible start" and that "the GA and SA-C receive the
same start". `run_exp02a_multiseed.py` contains no `warm_start` argument at all. In that campaign
SA-C starts from its own cube-per-order-index ordering, the GA from a random capacity-feasible
population, the column generation from the LPT partition of Algorithm 1, and the two model
formulations from no warm start (the harness marks the Hexaly call "NO warm start" explicitly). The
text now describes each start as it actually was, and notes that each baseline uses the
initialisation its own source prescribes. The LPT row remains the correlation-blind anchor. This
does not weaken the comparison: the baselines trail by 20 to 27\% at the two larger sizes, and
starting each from its own literature-standard initialisation is the more faithful reading of
Kim \& Smith (2012) and Zhang et al. (2019) than forcing a common start.

**Correction 2: the seed statement was wrong for SA-C.** The text reported "seed 20240612 for the GA
and SA-C". Both algorithms in fact draw their search decisions from `np.random.RandomState(42)`.
SA-C makes no other random call, so it is deterministic and 20240612 never touches it. The GA's
capacity repair alone uses the global NumPy stream, which the harness seeds at 20240612. The
protocol paragraph now says this, and the sentence classifying methods as randomised was corrected:
SA-C belongs with the clustering heuristic as deterministic, not with the randomised methods.

Two further descriptions of the GA were corrected against the code: selection is binary tournament,
not quality-proportional, and the crossover is a partially mapped crossover adapted to
station-assignment vectors, not a subset crossover.

Abstract 191 words, total main text plus appendices 11,248 of 12,000. Display items unchanged at 15.
