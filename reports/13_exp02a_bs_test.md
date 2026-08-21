# Report 13 — Bertsimas–Şim robust workload placement on the exp02a article benchmark

**Date:** 2026-07-15 · **Requested by:** Ermal (test the BS approach on the article's instances)
**Code:** `Baselines/exp02a_bs_adapter.py` (fold builder), `Baselines/run_bs_robust_experiment.py`
(harness, unchanged model), `reports/12_workload_feasibility/code/aggregate_exp02a.py`
**Data:** `reports/12_workload_feasibility/data/exp02a/` (per-instance results + merged
`exp02a_all.csv`, `exp02a_summary.csv`). Folds are derived, regenerable via the adapter
(deterministic; NOT committed).

## Protocol

All 29 exp02a instances (12×50, 10×500, 4×1000, 3×2000 SKU; uniform stations = SKU/100, 100
slots each — exactly binding except the 50-SKU family). Per instance: ONE temporal 70/30 cut
by ORDER rank (U1); `REAL_LINES` = train pick-line **row counts** (the instances contain
duplicate (ORDER, PRODUCT) rows and their own `TIME_CAPACITY` follows the row-count
convention — verified: `T = ceil(1.10 · rows/|S|)` exactly); train ceiling recomputed
κ-invariantly on the train volume. Arms, paired within instance: Γ ∈ {0, 1, 2, 4} at **full
M3 magnitude** (α = 1) + uniform tightening β = 1.02. Same solver pipeline as report §12/5
(greedy → deterministic local search — extended with a single-move neighbourhood for the
non-binding 50-SKU family — → HiGHS probes); evaluation on real held-out orders against the
1.10-rule contract `Tⁿ`. Every feasible robust arm re-verified against the pre-dualization
top-Γ constraint (`robust_ok` = True in all 116 robust-arm runs).

## Headline results (means over seeds; full table in `exp02a_summary.csv`)

| Size | arm | PoR % | viol/|S| | peak Wₛ/Tⁿ (max) | X % | infeasible |
|---|---|---|---|---|---|---|
| 50   | Γ=0 | 0.00 | 0.67/5 | 1.00 (1.05) | 0.3 | 0 |
| 50   | Γ=4 | 2.29 | **0.00** | 0.95 (0.98) | 0.0 | 0 |
| 500  | Γ=0 | 0.00 | 0.30/5 | 0.99 (1.01) | 0.1 | 0 |
| 500  | Γ=4 | 0.13 | 0.20 | 0.99 (1.00) | 0.0 | 0 |
| 1000 | Γ=0 | 0.00 | 0.75/10 | 1.00 (1.01) | 0.0 | 0 |
| 1000 | Γ=4 | 0.94 | 0.50 | 1.00 (1.00) | 0.0 | 0 |
| 2000 | Γ=0 | 0.00 | 0.67/20 | 1.01 (1.02) | 0.0 | 0 |
| 2000 | Γ=4 | 0.47 | 0.33 | 1.00 (1.02) | 0.0 | 0 |
| —    | β=1.02 | 0.7–2.7 | 0.00 | 0.94–0.96 | 0.0 | 1 (one 50-SKU seed) |

## Findings

1. **The benchmark is near-stationary, and the nominal layout is already (essentially)
   workload-feasible out of sample.** Violations are hairline: mean 0.2–0.75 stations at
   ratios 1.00–1.05, excess fraction X ≤ 0.3%. Calibration confirms it: the M2 diagnostic
   coefficient is c(0.9) ≈ 2.8–3.8 and the largest per-product deviation ≈ 90 lines —
   versus c ≈ 70–97 and σ_max = 13,307 on the drifting ISCF stream. exp02a deviations are
   sampling noise, not demand drift.
2. **Full-magnitude BS protection is implementable everywhere and essentially free.**
   Zero infeasible robust arms across 29 instances (vs. *provably impossible* at Γ ≥ 4 on
   iscf480 under the same 10% contract); PoR mostly < 1% (max 2.3% at 50 SKU, within seed
   noise, sd 0.5–3.1). Γ = 4 removes even the hairline violations (viol → 0–0.5, peaks
   ≤ 1.0).
3. **Uniform tightening also works here** (β = 1.02: peaks 0.94–0.96 at 0.7–2.7% PoR) —
   with one caveat: it went infeasible-within-budget on one 50-SKU seed while full-σ BS
   never did. On stationary data both instruments are cheap; the dominance of targeted
   protection observed on ISCF is a *drift* phenomenon, not a universal one.
4. **Mechanism confirmed by contrast.** Same model, same solver, same contract:
   on the drifting ISCF stream full protection does not fit the slack and partial
   protection buys a 10% peak reduction at a real price; on the stationary article
   benchmark protection costs nothing *because there is nothing to insure*. The value
   **and** the cost of the budgeted robust workload constraint are both driven by demand
   drift — absent by construction in exp02a. Robustness conclusions for the CSLAP workload
   constraint should therefore be evaluated on temporally drifting order streams
   (ISCF/BERNER-like), not on stationary synthetic benchmarks.

## Caveats

(i) One temporal cut per instance (seed replication across instances provides the spread);
(ii) metaheuristic incumbents (PoR magnitudes carry LS noise ~±1%, hence occasional small
negative PoR); (iii) the 50-SKU family has non-binding slot capacity — the local search
gained a move neighbourhood for it, all other families are exactly binding as on iscf480;
(iv) the tight-β infeasible verdict is undetermined-within-budget, not a certificate.
