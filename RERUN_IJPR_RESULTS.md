# EXP-02a re-run results — IJPR revision

Companion to `RERUN_IJPR_BENCHMARK.md`, which specified this re-run. This file reports what was
actually executed and what came out. **Every number below is measured, not configured.**

- **Executed:** 2026-07-29 13:57 UTC → 2026-07-30 01:57 UTC
- **Branch:** `ijpr-revision-20260729`
- **Machine:** Windows Server 2019, 16 physical cores / 32 logical, 128 GB RAM
- **Environments:** CPLEX 22.1.1.0 (`Virtual_Environment_CPLEX_1`), Hexaly (`Virtual_Environment_LocalSolver_3`), both Python 3.10.11
- **`PYTHONHASHSEED=0`** set for both runs, per the reproducibility note in the spec.

## 0. Integrity checks

| Check | Result |
|---|---|
| Instance hashes before runs | 29/29 directories, **87/87 files match, 0 differ, 0 missing** |
| Instance hashes after runs | identical to `exp02a_results/hash_manifest_v3.txt` |
| CG rows | 29/29 `OK`, **zero failures** |
| Metaheuristic/MILP rows | 122/122 `OK`, **zero failures**, zero missing visits |
| Error signatures in either log | none (no traceback, exception, OOM, or kill) |

No instance was regenerated. The comparison to the published table is intact.

**Steps 3 and 4 were run sequentially, not concurrently.** CPLEX is pinned to 4 threads, but Hexaly's
`nb_threads` defaults to `0` (auto) and takes all 16 physical cores, so overlapping them would have
contended on exactly the wall-clock property this re-run exists to fix.

`--aggregate-only` does not exist in this version of `run_exp02a_multiseed.py`; per the spec it was
skipped. The per-instance CSV is authoritative.

## 1. Time column for Table 5 — reporting convention

**Decision (author, 2026-07-30):** report the imposed budget where a method reached it, and the
measured time where a method converged early.

> Where measured time ≥ budget, print the **budget**. Where a method converged below budget, print
> the **measured convergence time**.

Applied, this is the Table 5 time column:

| Size | Budget | Heuristic | SA-C | GA | Hexaly | CG-SetPart |
|---|---|---|---|---|---|---|
| 50 | 120 s | **1.8** | **54.1** | **47.6** | 120 | **85.9** |
| 500 | 300 s | **18.7** | 300 | 300 | 300 | **256.1** |
| 1,000 | 600 s | **35.0** | 600 | 600 | 600 | **599.4** |
| 2,000 | 1,200 s | **72.0** | 1,200 | 1,200 | 1,200 | **1,199.4** |

Bold = measured convergence time (method finished early). Unbolded = budget.

Recommended column header: **"Time budget (s)"**. Two footnotes keep the printed claim true:

1. *SA-C's stopping rule tests the elapsed clock once per temperature level and may overshoot by up
   to one inner loop.* (Measured overshoot: +14% at 500, +24% at 1,000, +20% at 2,000.)
2. *Hexaly times exclude model construction; `param.time_limit` bounds the search only.*

**Do not write that all methods "consume the full budget at every size."** That is false at 50 and
500 SKUs, where CG converges at 86 s and 256 s, and false for the Heuristic everywhere. It holds for
CG at 1,000 and 2,000.

## 2. Solution quality — the substance of Table 5

Mean visits over instances, with mean relative gap to the Hexaly reference.

| Size | Method | Mean visits | Gap vs Hexaly | WL-violating instances |
|---|---|---|---|---|
| 50 | Heuristic | 7,698.4 | +1.97% | **12/12** |
| | SA-C | 7,632.3 | +1.00% | 0 |
| | GA | 7,767.4 | +2.82% | 0 |
| | Hexaly | 7,555.7 | — | 0 |
| | **CG-SetPart** | 7,589.8 | +0.45% | 0 |
| 500 | Heuristic | 78,647.0 | +2.97% | **8/10** |
| | SA-C | 88,688.8 | +16.06% | 0 |
| | GA | 85,362.7 | +11.68% | 0 |
| | Hexaly | 76,406.8 | — | 0 |
| | **CG-SetPart** | 76,681.4 | +0.36% | 0 |
| 1,000 | Heuristic | 196,341.3 | −0.07% | **4/4** |
| | SA-C | 240,693.3 | +22.76% | 0 |
| | GA | 235,207.5 | +19.89% | 0 |
| | Hexaly | 196,514.8 | — | 0 |
| | **CG-SetPart** | **192,452.0** | **−2.07%** | 0 |
| 2,000 | Heuristic | 483,326.0 | −4.51% | **3/3** |
| | SA-C | 615,489.7 | +21.38% | 0 |
| | GA | 608,866.7 | +20.08% | 0 |
| | Hexaly | 506,763.0 | — | 0 |
| | **CG-SetPart** | **476,692.3** | **−5.93%** | 0 |

**Two things must be said together.** CG-SetPart is the best *feasible* method at 1,000 and 2,000
SKUs, beating the Hexaly reference by 2.07% and 5.93% with **zero capacity and zero workload
violations on all 29 instances**. The Heuristic's apparent wins at those sizes (−0.07%, −4.51%) come
from solutions that **violate the workload constraint on 100% of instances** and are not comparable.
Reporting the Heuristic's visit counts without its violation rate would misrepresent it.

Confidence intervals, per-instance rows and pairwise Wilcoxon/paired-t results are in
`exp02a_results_rerun/`. Note `ci_informative = False` for every method at 2,000 SKUs (n=3).

## 3. Measured wall clock — ground truth

Kept here in full because §1 caps some of these for presentation. Mean over instances, seconds;
`%Δ` against the budget.

| Size (budget) | CG-SetPart | Hexaly | GA | SA-C | Heuristic |
|---|---|---|---|---|---|
| 50 (120 s) | 85.9 (−28%) | 120.4 (+0.3%) | 47.6 (−60%) | 54.1 (−55%) | 1.8 |
| 500 (300 s) | 256.1 (−15%) | 309.6 (+3.2%) | 303.1 (+1.0%) | 342.6 (+14%) | 18.7 |
| 1,000 (600 s) | 599.4 (−0.1%) | 635.3 (+5.9%) | 605.5 (+0.9%) | 743.2 (+24%) | 35.0 |
| 2,000 (1,200 s) | 1,199.4 (0%) | 1,352.6 (+13%) | 1,223.0 (+1.9%) | 1,439.4 (+20%) | 72.0 |

Worst single instance: SA-C 1,570.1 s @2,000; Hexaly 1,385.7 s @2,000; GA 1,238.9 s @2,000;
CG 1,199.7 s @2,000.

### What the re-run fixed

| Entry | Before | After |
|---|---|---|
| Hexaly @500 | 1,148.5 s mean, range 455–4,684 s | **309.6 s**, range 306.9–311.3 s |
| CG @500 | 476.3 s under a 600 s budget | **256.1 s** under the correct 300 s budget |
| Hexaly @2,000 | 1,049.2 s (900 s configured) | 1,352.6 s under the correct 1,200 s budget |
| GA @2,000 | 909.2 s (900 s configured) | 1,223.0 s under the correct 1,200 s budget |

The 500-SKU spread collapsing from 455–4,684 s to 306.9–311.3 s is the single most visible
improvement; the old range was the clearest evidence that the printed protocol was not what ran.

### Two structural overruns (not machine noise, not contention)

**SA-C.** `Baselines/sa_correlated.py:256-260` tests the clock only at the top of each outer
temperature loop, then commits to a full inner loop of `inner_iters` evaluations before testing
again, so it can overshoot by one inner loop. Reproducible, not environmental: the stored campaign
measured 341.2 s at 500 SKUs and this re-run measured 342.6 s. Fixing it means moving the check
inside the inner loop, which changes a published method's behaviour — deliberately **not** done here.

**Hexaly.** `Baselines/milp_synthetic.py:46` starts the timer before model construction, while
`optimizer.param.time_limit` bounds the search only. Implied build+extract cost: 0.4 s (50),
9.6 s (500), 35.3 s (1,000), 152.6 s (2,000) — scaling with N as construction would. **Hexaly's
search respected its budget at every size.**

## 4. Temporal hold-out (Table 9) — artifact located

`RERUN_IJPR_BENCHMARK.md` states no artifact for the six numbers was found in either repository.
That is correct but incomplete: **the artifact exists, outside both repositories.**

**Source:** `C:\ermal\notebooks\Correlated_Storage_Assignment_Problem\Notebooks\All_data_testing\Compare_W.ipynb`, cells 8–9.

All six totals *and* all six mean-visit values match `IJPR_CSLAP_v2.tex:491-498` exactly:

| Test period | Layout | Notebook | Table 9 |
|---|---|---|---|
| Last 3 wks | Original | 265876 / 4.05199951 | 265,876 / 4.052 |
| | Optimised on first 10 wks (`exclude_3W`) | 248358 / 3.78502195 | 248,358 / 3.785 |
| | Oracle (`only_in_last_3W`) | 233728 / 3.56205803 | 233,728 / 3.562 |
| Last 5 wks | Original | 423593 / 3.92615627 | 423,593 / 3.926 |
| | Optimised on first 8 wks (`exclude_5W`) | 392318 / 3.63627769 | 392,318 / 3.636 |
| | Oracle (`only_in_last_5W`) | 380356 / 3.52540551 | 380,356 / 3.525 |

**Method:** `time_cut()` (cell 7) computes `cutoff = max_date - timedelta(weeks=N)` for N ∈ {3,5} over
`BERNER_ORDER_LINES_DATE_ASSIGNED_21.csv`, which carries a real `DELIVERY_DATE` column spanning
**2021-09-01 → 2021-11-30 = 90 days ≈ 12.9 weeks** — the paper's "13 weeks". "Stops" are counted as
distinct stations per order, summed. The six `product_assignment_group_*_Hexaly*.csv` layout files sit
beside the notebook, so it re-runs as-is.

**Table 9 does not need regenerating or dropping.** But its reproduction path must be stated, because:

> The repo ships `Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv` with schema
> `PRODUCT;ORDER;QTY;STATION;BOX_ID` — **no date column**. `Baselines/build_berner_instance.py`
> documents this as assumption U1 and substitutes an order-ID *rank quantile* (10/13, 8/13) for the
> real date split. A referee re-running the repository will **not** reproduce these six numbers.

Fix by either shipping the dated extract as supplementary data, or stating in the caption that the
released instance approximates the split by order-ID rank.

> **Update, 2026-08-10.** `Baselines/build_berner_instance.py` was removed when this branch was
> trimmed to the article (it served the robust-covering study, not Table 9). It remains on `main`.
> Nothing above changes: the script never produced Table 9's numbers, and the conclusion stands —
> the six values need the dated extract, which this repository does not ship.

Minor, not affecting published numbers: the notebook also computes a "full assignment" row
(245,619 / 391,324) that Table 9 omits, and in cell 7 that row reads a global `v5W_fulldata` for both
windows regardless of the argument passed.

**Search coverage:** all of `C:\ermal`, the user profile, and local drive `G:`. Network shares `N:`
and `S:` were excluded as not-this-machine. Other co-occurrences of the six numbers were coincidental
— `265876` is a CSV row index in `Products_data_ISCF.csv` and a `BOX_ID` substring in the BERNER
order lines.

## 5. Not re-run, and why

Unchanged from the spec: the industrial case (Table 8) and the k-sweep (Table 10) already ran at
their stated budgets (36,000 s and 3,600 s per k) and their stored results match the manuscript; the
heuristic threshold-sensitivity sweep is being run on the laptop.

## 6. Files

Committed on `ijpr-revision-20260729`:

| Path | Contents |
|---|---|
| `exp02a_results_rerun/exp02a_per_instance.csv` | **authoritative** — one row per (size, seed, method, solver_seed), 122 rows |
| `exp02a_results_rerun/exp02a_per_instance_v3.csv` | joined view with Hexaly-reference gap columns |
| `exp02a_results_rerun/exp02a_aggregated_v3.csv` | per (size, method): mean visits, CIs, gaps, violation rates |
| `exp02a_results_rerun/exp02a_pairwise_v3.csv` | per (size, pair): Wilcoxon + paired-t |
| `exp02a_results_rerun/hash_manifest_v3.txt` | instance hashes as re-verified during the run |
| `exp02a_results/exp02a_cg_setpart.csv` | **new** CG rows under corrected budgets (29 rows) |
| `exp02a_results/exp02a_cg_setpart_600s500.csv` | preserved old CG rows (the 600 s-at-500 campaign) |

`exp02a_results/exp02a_cg_setpart_aggregated.csv` is **stale** — it derives from the old CG run and
was deliberately not touched. Recompute or delete it before submission.

### Reproducing

```bash
git checkout ijpr-revision-20260729
python Baselines/verify_instance_hashes.py            # expect 87/87 files match

export PYTHONHASHSEED=0                               # PowerShell: $env:PYTHONHASHSEED = "0"
# CPLEX env, ~2h40m:
python run_exp02a_cg_setpart.py --sizes 50 500 1000 2000
# Hexaly env, ~9h20m — restartable, skips recorded (size, seed, method, solver_seed):
python Baselines/run_exp02a_multiseed.py \
  --sizes 50 500 1000 2000 --k-per-size 12 10 4 3 \
  --ga-seeds 20240612 --ga-sideprobe-seeds 20240613 20240614 \
  --sideprobe-size 50 --sideprobe-k 3 --instance-seed-start 1001 \
  --time-limits 120 300 600 1200 --theta 0.7 \
  --out-dir exp02a_results_rerun --instance-dir exp02a_instances
```

Run them sequentially, not concurrently (see §0).
