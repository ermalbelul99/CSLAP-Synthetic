# Revision evidence notes (IJPR revision, 2026-07-29)

Derived numbers computed for the IJPR revision. Every figure below is reproducible from the
artifacts named with it; nothing here is a new experiment except the support counts, which are a
pure recount of the shipped instances.

## 1. Distinct multi-item supports |U| (reviewer Q1)

Source: `Baselines/report_support_counts.py` (env `savoye2023`), output
`exp02a_results/support_counts.csv`. Semantics identical to
`cg_setpart_cplex.aggregate_supports`: a support is the frozenset of an order's products, kept when
it holds at least two products; its weight is the number of orders sharing it. `linking_rows` is
`sum_u |u|`, the number of `z_u >= a_p` rows the persistent pricing model carries.

| Instance class | |U| min | |U| mean | |U| max | linking rows (mean) |
|---|---|---|---|---|
| 50 SKUs (K=12) | 1,398 | 1,830 | 2,242 | 16,957 |
| 500 SKUs (K=10) | 15,371 | 20,367 | 24,393 | 203,521 |
| 1,000 SKUs (K=4) | 32,743 | 37,950 | 44,223 | 381,343 |
| 2,000 SKUs (K=3) | 66,425 | 77,291 | 92,738 | 778,150 |

**Industrial (Company A / BERNER).** Solver instance (after pruning): 15,975 movable SKUs,
83,183 multi-item solver orders, **|U| = 82,224** distinct supports, 1,055,672 linking rows.
Pricing model size therefore ≈ |U| + |P| = 98,199 variables and ≈ 1,055,674 constraints
(linking rows + capacity + workload), built once and re-priced by objective update.
Full evaluation stream (all 284,862 orders, 21,874 SKUs): 167,056 distinct multi-item supports.

**Manuscript correction required.** Section 4.2.3 currently states "roughly 66,000 distinct
supports on the 2,000-SKU instances". 66,425 is the value for seed 1001 only; the three 2,000-SKU
instances span 66,425–92,738 (mean 77,291). Replace with the range or the mean.

## 2. Per-instance win/loss counts (statistical-power concern at K=3,4)

Source: `exp02a_results/exp02a_per_instance_v3.csv` (Hexaly/GA/SA-C/Heuristic) and
`exp02a_results/exp02a_cg_setpart.csv` (CG), paired on (size_n, instance_seed).

CG (set-partitioning) versus the set-variable reference:

| N | K | CG wins | mean per-instance delta |
|---|---|---|---|
| 50 | 12 | 1/12 | +0.46% |
| 500 | 10 | 1/10 | +0.75% |
| 1,000 | 4 | 3/4 | −0.06% |
| 2,000 | 3 | 3/3 | −2.44% |

Sign consistency of the reference against the baselines where the confidence intervals are wide:
the set-variable approach beats GA on 4/4 (N=1,000) and 3/3 (N=2,000) instances, and beats SA-C on
4/4 and 3/3 respectively. Every large-instance ranking claim is therefore unanimous across the
instances drawn, which is the honest reading available at K=3–4 where the interval estimate is not.
The heuristic is the exception: the reference beats it on 4/4 at N=1,000 but only 1/3 at N=2,000 —
consistent with the manuscript's statement that the heuristic rivals it on raw visits while
breaching the workload cap.

## 3. Industrial CG configuration variants (context for the reported row)

Source: `results_industrial_cg_setpart*.csv`, recovered 2026-07-29 from the CG repository
(`belulerm/CSLAP_Problem`, commit `bf233e1`) into this tree.

| Run | Workload envelope | Visits | util. std dev | wl_broken |
|---|---|---|---|---|
| `_matchhexaly` (**the row reported in the paper**) | the set-variable MILP's own caps, ceiling only | 1,000,844 | 2.413 | 10 (all inside the site's +10% tolerance) |
| default | current workload pinned (floor = ceiling = 1.0) | 1,004,223 | 0.004 | 0 |
| `_ceil100_floor0` | free to reduce, never exceed current | 1,005,857 | 0.004 | 0 |
| `_slack10` | ±10% band | 805,350 | 9.081 | 9 |

The paper reports the `_matchhexaly` configuration, which is the only apples-to-apples comparison:
it hands the column generation byte-for-byte the inputs the set-variable MILP received. The
`_slack10` row is not comparable and is not reported.
