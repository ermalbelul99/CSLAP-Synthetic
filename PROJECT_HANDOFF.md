# CSLAP Robustness — Repository Map & Handoff

**Purpose.** This document tells a new contributor exactly where every piece of the
robustness study lives, what is reproducible, what is defensible, and what is not.
It is written to be read cold, before touching anything.

---

## 0. Repository identity

| | |
|---|---|
| **Local path** | `c:\ermal\CSLAP_Full_Project\CSLAP-Synthetic` |
| **Remote** | `https://github.com/ermalbelul99/CSLAP-Synthetic.git` |
| **Branch** | `daily-robustness-cplex-run` |
| **State** | ahead of `origin`, **never pushed**; working tree clean |

Two distinct studies of the same research question live side by side in this
repository. They are referred to throughout as **Path 1** and **Path 2**. They
share a code base but differ in the constraint they enforce, the way they split
data, and the instances they run on. Keeping them straight is the main purpose of
this file.

---

## 1. The two paths at a glance

The research question is the same in both: *a storage layout is optimised on
historical orders but operated on future orders; will it still respect each
station's workload limit, and what does protecting it cost in station visits?*

| | **Path 1** | **Path 2** |
|---|---|---|
| workload unit | whole train/test **window** | each **calendar day** |
| ceiling | `T_s = ⌈σ · ΣL_p^tr / (V_s·\|S\|)⌉`, `σ = 1.10` — equal share + fixed 10 % margin | `W_s(d) ≤ (μ_s + z·σ_s)·L(d)` — station's own share, own tolerance, scales with the day's volume |
| data split | expanding **order-rank** cuts (50/50, 60/40, 70/30, 80/20, 90/10) | 4 nested expanding **calendar** folds |
| solvers | HiGHS + CPLEX | Hexaly (local search) |
| instances | iscf480, iscf10kt, exp02a (29), bern2000 | BERNER only |
| robust budget | Bertsimas–Şim Γ | Bertsimas–Şim Γ, plus the tolerance `z` |
| status | complete, written up | complete, pre-registered, gated, adversarially reviewed |

The essential structural difference: **Path 1's constraint is strictly weaker than
Path 2's.** A window-aggregate limit lets a busy day and a quiet day cancel inside
the sum, so a layout can satisfy the window total while overloading a station on
its peak day. Path 2's per-day constraint implies Path 1's; the converse is false.

---

## 2. PATH 1 — where it lives

Window-aggregate contract, order-rank splits, no calendar dates required.

### Reports and write-up

| path | what it is |
|---|---|
| `reports/12_workload_feasibility/` | the main study (≈ 6.7 MB) |
| `reports/13_exp02a_bs_test.md` | the stationary-benchmark control |
| `paper/beginner_explainer.tex` | plain-language explainer, 912 lines, self-contained, compiles on Overleaf |

### Analysis code — `reports/12_workload_feasibility/code/`

```
aggregate_berner.py            analyze_iscf480_workload.py    make_figures.py
aggregate_exp02a.py            gamma_calibration.py           secondary_family_workload.py
analyze_berner_workload.py     make_experiment_outputs.py     shift_asrun_aggregate.py
analyze_iscf10kt_workload.py
```

### Data — `reports/12_workload_feasibility/data/`

| folder | contents | regenerable here? |
|---|---|---|
| `iscf480/` | `per_fold.csv`, `per_station.csv`, 4 heatmap CSVs | **No** — source instances absent |
| `iscf10kt/` | `per_fold.csv`, `per_station.csv`, `k_effect.csv`, `sparse_train_effect.csv` | **No** — source instances absent |
| `experiment*/` | 12 α-variant run dirs (`_f0_a0.25` … `_f4_a0.5`) plus `layouts/` | **No** — ISCF-based |
| `exp02a/` | `exp02a_all.csv`, `exp02a_summary.csv`, 29 per-instance dirs | **Yes** |
| `bern/` | 8 run dirs (β ∈ {1.0, 1.05, 1.1, 1.2} × 2) plus `bern_grid.csv`, `bern_all.csv` | **Yes** |
| `berner/` | `berner_bindingness.csv`, `berner_feasibility_audit.csv` | **Yes** |
| `gamma/`, `secondary/` | deviation-calibration and secondary-family diagnostics | mixed |

### Figures — `reports/12_workload_feasibility/figures/`

Nine PDFs: `fig_bindingness`, `fig_concentration`, `fig_exp_frontier`,
`fig_exp_stations`, `fig_exp_tradeoff`, `fig_gamma`, `fig_k_effect`,
`fig_ratio_heatmap`, `fig_violations`.

### The file not to overlook

**`reports/12_workload_feasibility/data/bern/bern_grid.csv`** is Path 1's Γ sweep on
a 2 000-SKU BERNER instance. It shows that under the 10 % contract **Γ = 1, 2 and 4
were all infeasible**; only loosening station capacity to ×1.20 made Γ = 4 fit. It
is the direct empirical bridge between the two paths, and it independently
anticipates the infeasibility wall Path 2 later proved arithmetically.

> ⚠️ In this file `β` **multiplies capacity upward** (loosens the ceiling). In Path 2
> `β` **divides the allowance** (tightens it). Same letter, opposite meaning — never
> merge the two tables without renaming one.

---

## 3. PATH 2 — where it lives

Per-day volume-normalised share band, calendar folds, BERNER only.

| path | what it is |
|---|---|
| `results/z_contract/` | the 12-cell grid and all supporting runs (≈ 7.6 MB) |
| `GATES_z_contract.md` | pre-registration + 20-gate ledger (18 runnable gates met, 2 manual) |
| `POSTMORTEM_robust_slotting.tex` | full write-up including retractions; compiles on Overleaf |
| `tools/` | gate oracles, mutation tests, runbooks, table builders |
| `ISCF_project_CSLAP_robustness.docx` | student project brief derived from this work |

### Inside `results/z_contract/`

| item | contents |
|---|---|
| `z3/`, `z4/`, `z6/` | one per contract value: `results.csv` (24 rows = 4 folds × 6 arms), `calibration.csv`, `per_station.csv`, `layouts/`, `_snapshots/` |
| `metrics_z{3,4,6}.csv` | scored train/test metrics per arm |
| `per_station_z{3,4,6}.csv` | per-station `mu`, `sigma`, `gamma_bind`, `gamma_cover` |
| `headline_vs_incumbent.csv` | the headline table (visits and violations vs the operating layout) |
| `incumbent_visits.csv` | the incumbent's visit baseline |
| `seed_replication_z4.csv` | 3 seeds × 4 folds × {Γ=0, Γ=2} |
| `pilot_f0_z3_120s/` | the pilot that **failed** — kept deliberately as evidence |
| `pilot_f0_z3_600s/` | the pilot at the pre-registered time limit |
| `_probe_g4_600s/`, `_seed_rep/` | targeted probes |

### Tooling — `tools/`

| file | role |
|---|---|
| `checks_z.py` | all 20 gate oracles (`python tools/checks_z.py z1` … `z20`) |
| `run_gates_z.py` | runs the ledger, writes evidence back into `GATES_z_contract.md` |
| `mutate_z_gates.py`, `mutate_z9.py`, `mutate_z10.py` | mutation tests — prove each gate can fail, not only pass |
| `run_z_grid.sh` | the 12-cell grid runbook |
| `run_seed_rep.sh` | the seed-replication runbook |
| `headline_table.py` | rebuilds `headline_vs_incumbent.csv` |
| `make_project_brief.py` | regenerates the student `.docx` |

Mutation scripts sandbox themselves via the `CSLAP_ZDIR_SANDBOX` environment
variable and refuse to run if their fixture path is not inside that sandbox. Do not
remove that guard: earlier versions destroyed committed results twice.

---

## 4. Shared code — `Baselines/`

Both paths share this directory. **Splitting the repository by path would break
both**, because the harness is common and the contract is selected by a flag.

| file | role | used by |
|---|---|---|
| `milp_highs_robust.py` | core model, `read_data`, `build_supports`, HiGHS backend | both |
| `milp_cplex_robust.py` | CPLEX twin of the same model | Path 1 |
| `milp_hexaly_robust.py` | Hexaly backend; per-day rows, `rhs_lines`, dual seeding | Path 2 |
| `run_bs_robust_experiment.py` | **the shared harness — this is the fork point.** `--share-z` switches from the Path-1 contract to the Path-2 contract; `--backend` selects the solver | both |
| `evaluate_layout_robust.py` | visit and workload evaluator | both |
| `share_contract.py` | share band: `fit_share_band`, `allowance_lines`, identity checks | Path 2 |
| `daily_metrics.py` | scorer against a frozen per-station ceiling | Path 2 (early) |
| `daily_metrics_share.py` | scorer against the share band; `gamma_bind`, `gamma_cover` | Path 2 |
| `daily_folds.py`, `berner_daily_adapter.py` | calendar fold construction | Path 2 |
| `exp02a_bs_adapter.py`, `berner_bs_adapter.py` | order-rank fold construction | Path 1 |
| `incumbent_visits.py` | evaluates the operating layout through the same path as every arm | Path 2 |

`paths.py` at the repository root defines every filesystem anchor. Read it first.

---

## 5. ⚠️ Data inputs — the most important section

| input | location | present |
|---|---|---|
| **ISCF instances** | `data/instances/iscf` | ❌ **ABSENT** |
| exp02a instances | `exp02a_instances/` — 29 files | ✅ tracked in git |
| BERNER raw order lines | `Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv` (78 MB) | ✅ tracked in git |
| derived folds | `data/derived/` (≈ 1.1 GB; 951 MB of it is `exp02a_daily_folds`) | ✅ on disk, **gitignored**, regenerable from the adapters |

`paths.py` states explicitly that the ISCF families "were not ported" to this
repository. The consequence is severe and must not be glossed over:

> **Path 1's two headline instances — `iscf480` and `iscf10kt` — cannot be
> regenerated here.** Only their aggregated result CSVs survive. Every results table
> in `paper/beginner_explainer.tex` except the exp02a control rests on input data
> that is not in this repository.

This is a **data-availability** problem, not a methodological one. The analysis was
performed; the inputs are simply elsewhere. Either recover the ISCF instances, or
scope future claims to `exp02a` and `BERNER`, which are both fully reproducible.

---

## 6. Known defects and stale references

1. **`paper/beginner_explainer.tex`, final "Reproducibility" section, is wrong on
   three counts.** It points at `src/…` (the code is in `Baselines/`) and at
   `results/experiment_iscf10kt_cplex/` and `results/experiment_iscf10kt_highs/`,
   neither of which exists. Fix before circulating the explainer.
2. **The `β` collision** described in §2 — opposite meanings in the two paths.
3. **`results/RUN_NOTES_daily_robustness.md`** and the `step2`–`step6` and
   `hexaly_smoke` log files under `results/logs/` document superseded runs whose
   outputs are no longer in the tree. They are stale and should be removed; the logs
   belonging to current work are `zgrid_*`, `pilot_*`, `probe_*`, `seedrep_*` and
   `mutation_suite.log`.
4. **`data/derived/exp02a_daily_folds` is 951 MB** of regenerable intermediate. It is
   gitignored, so it costs nothing in the repository, but it dominates disk usage.

---

## 7. What is defensible, and what is not

### Solid — build on these

- **Path 1's bindingness audit.** The diagnostic `B = Σ_p L_p^te / Σ_s V_s T_s`
  collapses from 1.005 to 0.125 across the five cuts, so a verdict of "0 stations
  overloaded" on late cuts measures how little demand arrived, not how balanced the
  layout is. This finding is path-independent and Path 2 inherits it.
- **Path 1's exp02a stationary control.** On 29 near-stationary instances protection
  is free and gains nothing. This establishes that the value *and* the cost of the
  robust constraint are both driven by demand drift. Fully reproducible.
- **Path 1's `bern_grid.csv`.** Γ was infeasible at every level under the 10 %
  contract on the industrial instance.
- **Path 2's counting-infeasibility proof.** Solver-free arithmetic: at sub-maximum
  quantiles `Σ_s T_s < max_d L(d)`, so two of three declared quantile settings
  describe an *empty* feasible set. No solver could have rescued them.
- **Path 2's share-band identity.** `Σ_s(μ_s + z·σ_s) = 1 + z·Σ_s σ_s > 1`
  guarantees aggregate feasibility by construction, which is what finally made
  Γ ≥ 2 solvable on the industrial instance.
- **Path 2's seed replication.** Γ=0 gave {8, 10, 7} violated test days across three
  seeds; Γ=2 gave {1, 1, 2}. Disjoint distributions, so the effect exceeds
  local-search variability.
- **Three premise measurements** (computed and reported in session, **not yet
  scripted into the repository** — re-derive before citing): station shares are
  volume-independent (median |r| = 0.14 across a 3.6× volume swing); station-share
  variance is ≈ 90 % genuine composition drift; product-level deviations are ≈ 65 %
  Poisson counting noise.

### Not defensible — do not cite without repair

- Path 1's `iscf480` / `iscf10kt` headline tables — source data absent (§5).
- Path 1's `iscf480` positive result — relied on a hand-tuned half-strength factor
  `α = 0.5` chosen after seeing results.
- Path 1's strongest claim, "targeted budget beats equal-price uniform tightening" —
  won 5/5 on `iscf480` but only **2/5** on `iscf10kt`. Instance-specific, not a law.
- Path 2's mechanism story. In the winning layouts the Bertsimas–Şim row is slack
  almost everywhere (`gamma_bind ≤ 4` at 0–5.2 % of station-folds), and the realised
  test overshoots would have needed `gamma_cover` of 5–52, far outside the declared
  range. Γ reliably produces the effect; **Bertsimas–Şim coverage does not explain
  why.**
- Path 2's comparisons against the operating layout — statistical ties
  (McNemar *p* ≥ 0.51). Power is capped at *p* = 0.125 by four independent weekly
  units, arithmetically, and cannot be fixed by analysis.
- **Both paths: no cost-matched control.** β costs 0.4–1.2 % of visits, Γ costs
  7–15 %. "Does Γ beat β?" is confounded with "does spending more help?" A β
  calibrated to cost ≈ 6 % is the single most valuable missing experiment.

---

## 8. Suggested reading order for a new contributor

1. `POSTMORTEM_robust_slotting.tex` — Path 2 end to end, including what was retracted
2. `paper/beginner_explainer.tex` — Path 1 end to end, from first principles
3. `GATES_z_contract.md` — the pre-registration and what was actually verified
4. `reports/13_exp02a_bs_test.md` — the control that explains *why* the method works

**Then the data:**
`results/z_contract/headline_vs_incumbent.csv` ·
`results/z_contract/seed_replication_z4.csv` ·
`reports/12_workload_feasibility/data/bern/bern_grid.csv` ·
`reports/12_workload_feasibility/data/exp02a/exp02a_summary.csv`

**Then the code:**
`Baselines/run_bs_robust_experiment.py` (the fork point) ·
`Baselines/share_contract.py` · `Baselines/milp_hexaly_robust.py`

---

## 9. The open proposal — "Path 3"

A **window-level share band with a variance decomposition**: keep Path 2's
volume-normalised share contract, but enforce it over a window of any size rather
than per day, so that it works on data with no calendar — only a chronological
ordering. Specified in session; **not yet implemented.**

Its premise (shares are volume-stable, so scale is absorbable and only the mix
matters) has been measured and holds. Three gaps are known, each with a stated fix:

1. **A variance needs repeated observations.** One training window gives one share
   per station and zero degrees of freedom. Requires segmenting the training window
   into ≈ 30–50 order-rank blocks.
2. **The tolerance is window-size dependent.** Observed share variance mixes real
   drift (scale-free) with sampling noise (∝ 1/N). Fit `σ²_drift` by subtracting the
   sampling term, then re-inflate to the target window size.
3. **The per-product deviations `lhat_p` are mostly counting noise** (≈ 65 %), which
   averages out as the window grows. Use a drift-corrected `lhat`, and expect Γ to
   matter less at window scale than the tolerance `z` does.

**Why it is attractive:** it repairs all three defects of Path 1's contract (equal
share → own share; fixed 10 % → per-station tolerance; frozen training total →
scales with the actual window), while keeping Path 1's dateless applicability — and
therefore its reach across all 29 `exp02a` instances. That cross-instance
replication is the single biggest weakness of Path 2, which has *n* = 1 site.

---

## 10. Reproducing what is here

```bash
# gate ledger for Path 2 (writes evidence back into GATES_z_contract.md)
C:/ermal/Virtual_Environment_LocalSolver_3/Scripts/python.exe tools/run_gates_z.py

# a single gate
C:/ermal/Virtual_Environment_LocalSolver_3/Scripts/python.exe tools/checks_z.py z12

# prove the gates can fail, not only pass
C:/ermal/Virtual_Environment_LocalSolver_3/Scripts/python.exe tools/mutate_z_gates.py

# rebuild the headline table
C:/ermal/Virtual_Environment_LocalSolver_3/Scripts/python.exe tools/headline_table.py

# the full 12-cell grid (~12 h 40 m) and the seed replication (~2 h 50 m)
bash tools/run_z_grid.sh
bash tools/run_seed_rep.sh
```

Path 2 requires the Hexaly virtual environment at
`C:\ermal\Virtual_Environment_LocalSolver_3`. Path 1 requires CPLEX at
`C:\ermal\Virtual_Environment_CPLEX_1`, or runs on HiGHS with no licence.
