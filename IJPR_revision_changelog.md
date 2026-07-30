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

*(Sensitivity numbers, the appendix table, and the calibration recipe are inserted once the sweep
completes; this section is finalised then.)*

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
