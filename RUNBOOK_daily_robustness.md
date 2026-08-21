# Runbook — daily workload-feasibility robustness (CPLEX machine)

Everything up to the MILP solve has been implemented and verified on the laptop.
This machine only needs to run the solver and hand the results back.

**Backend is CPLEX only.** `highspy` is never imported on this path;
`milp_highs_robust.py` is kept solely as a shared library (`read_data`,
`build_supports`, `greedy_start`, `local_search_visits`, `robust_lhs`) and its
solve function is never called.

Branch: `workload-daily-robustness`.

---

## 0. Environment

```bash
python -m venv .venv-daily && . .venv-daily/Scripts/activate
pip install -r requirements-remote.txt
```

Check CPLEX is actually reachable before running anything long:

```bash
python -c "from docplex.mp.model import Model; m=Model(); x=m.binary_var(); m.maximize(x); m.solve(); print('CPLEX OK', m.objective_value)"
```

If that prints `CPLEX OK 1.0` you are ready. If it reports a community-edition
size limit, the industrial arm will not solve — say so rather than letting it
silently fall back to the warm start.

---

## 1. Reference diagnostics (~3 min)

Establishes the calibration targets the synthetic instances are matched against.
Should reproduce the numbers in the plan exactly.

```bash
python Baselines/demand_diagnostics.py --orders "Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_DATE_ASSIGNED_21.csv" --tag berner
```

Expect: 63 active days, residual cv `0.167`, common share `0.403`, Fano top500
`2.57`, co-spike lift-Pearson `+0.2030`.

---

## 2. Build the folds (~5 min, no solver)

Industrial. `--top-n 2000` leaves the busiest 2,000 SKUs free and pins the rest
to their live station; the full 21,877-SKU placement is not solvable.

```bash
python Baselines/berner_daily_adapter.py --out data/derived/berner_daily_folds --top-n 2000 --tcap-quantile max
```

Synthetic, at three drift levels. `drift=0` is the stationary control; `0.15`
and `0.30` grow demand across the horizon.

```bash
python Baselines/exp02a_daily_adapter.py --out data/derived/exp02a_daily_folds --sizes 500 1000 --drift 0.0 --suffix _d00
```

```bash
python Baselines/exp02a_daily_adapter.py --out data/derived/exp02a_daily_folds --sizes 500 1000 --drift 0.15 --suffix _d15
```

```bash
python Baselines/exp02a_daily_adapter.py --out data/derived/exp02a_daily_folds --sizes 500 1000 --drift 0.30 --suffix _d30
```

Each fold directory is self-contained: the six instance CSVs plus
`fold_meta.json` and `station_daily_loads.csv`.

---

## 3. Smoke test before the full grid (~10 min)

One industrial fold, two budgets, short time limit. Run this first — if it fails
the full grid will fail four hours later.

```bash
python Baselines/run_bs_robust_experiment.py --dir data/derived/berner_daily_folds/berner_daily_r0f0 --prefix berner_daily --folds 0 --gammas 0,1 --betas 1.02 --time 120 --backend cplex --tcap-quantile max --out results/daily_smoke
```

Confirm in the log: `backend=cplex`, `lhat mode=daily`, `T_s re-derived at
q=max`, and a `warm start: ... products seeded` line. The warm start matters —
the ceilings are calibrated on the incumbent, so a from-scratch greedy can
report a false infeasibility.

---

## 4. Full grid

Industrial, four folds x three ceilings. Budget roughly 45 min per fold at
`--time 600`.

```bash
for f in 0 1 2 3; do for q in max p95 p90; do python Baselines/run_bs_robust_experiment.py --dir data/derived/berner_daily_folds/berner_daily_r0f$f --prefix berner_daily --folds $f --gammas 0,1,2,4 --betas 1.02,1.05 --time 600 --backend cplex --tcap-quantile $q --out results/berner_daily_q$q; done; done
```

Synthetic, all instances and drift levels. Much faster (500–1000 SKUs).

```bash
for d in _d00 _d15 _d30; do for t in data/derived/exp02a_daily_folds/syn_*sku_seed*$d_r0f*; do python Baselines/run_bs_robust_experiment.py --dir "$t" --prefix "$(basename "$t" | sed 's/_r0f[0-9]*$//')" --folds "$(basename "$t" | sed 's/.*_r0f//')" --gammas 0,1,2,4 --betas 1.02 --time 180 --backend cplex --tcap-quantile max --out results/exp02a_daily$d; done; done
```

---

## 5. Score everything (~2 min, no solver)

The ceiling sweep is a re-read, not a re-solve, so all three quantiles are
scored from one pass over the stored layouts.

```bash
python Baselines/daily_metrics.py --folds data/derived/berner_daily_folds --results results --quantiles max p95 p90 --out results/daily_metrics_berner.csv
```

```bash
python Baselines/daily_metrics.py --folds data/derived/exp02a_daily_folds --results results --quantiles max p95 p90 --out results/daily_metrics_exp02a.csv
```

Each prints a pooled test-window summary. Sanity check before sending anything
back: **the `incumbent` arm must show 0 days violated on `role=train` at
`q=max`** — that is true by construction under assumption A2, so a violation
means the ceiling was built wrong.

---

## 6. What to send back

Small enough to commit and push on this branch:

- `results/daily_metrics_berner.csv`, `results/daily_metrics_exp02a.csv`
- every `results/*/results.csv`, `calibration.csv`, `per_station.csv`
- `results/diagnostics/diagnostics_berner.json`
- the console logs, especially any `MODEL INFEASIBLE (proven)` lines — a proven
  infeasibility is a *result* here, not a failure: it says the drift does not
  fit inside the revealed capacity at that budget

Please **do not** push `data/derived/` (folds are regenerable from the two
adapters) or the raw order files.

```bash
git add results/ && git commit -m "results: daily robustness grid" && git push
```

---

## Known-good reference

Produced on the laptop without a solver, so you can tell a real difference from
a broken run. Industrial folds, `--top-n 2000`, incumbent arm:

| ceiling | test days violated / 18 | worst-day ratio | mean daily ratio |
|---|---|---|---|
| `q=max` | 5 | 1.440 | 0.800 |
| `q=p95` | 6 | 1.508 | 0.939 |
| `q=p90` | 10 | 1.571 | 1.011 |

All five violated days at `q=max` fall in fold 0, whose training window ends
before the late-October peak; the worst is 2021-10-29, the busiest day in the
horizon. Folds 1–3 contain that peak in training and their test weeks are quiet.
That contrast is the study's central case, visible before any optimisation.
