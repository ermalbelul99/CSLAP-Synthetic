# CSLAP — code and data for the IJPR manuscript

Reproduction package for:

> **Efficient and practical solutions for the correlated storage location assignment
> problem in automated pick-and-pass warehouses**
> Belul, Bouznif, Nace, Jouglet — submitted to the *International Journal of Production
> Research*.

Manuscript: [`IJPR_CSLAP_v2.tex`](IJPR_CSLAP_v2.tex) + [`IJPR_CSLAP.bib`](IJPR_CSLAP.bib).
Compiled on Overleaf from the Taylor & Francis *Interact* (APA) template — see
[`OVERLEAF_UPLOAD.md`](OVERLEAF_UPLOAD.md).

**This branch (`ijpr-revision-20260729`) is trimmed to what reproduces that article.**
Earlier paper generations (Computers & OR, Computers & Industrial Engineering), the
robust-covering / P-K study, and the retired Zhang synthetic pool live on `main` and the
other branches.

---

## The problem

Assign products to picking stations on a conveyor so that orders visit as few stations as
possible, subject to a hard slot capacity and a hard per-station workload budget. The
objective counts mechanical station stops, not picker travel — which is what makes it hard:
the visit count changes only when a whole order gains or loses a station, so it gives a
local search almost no gradient, and the binary programme's LP relaxation is worth exactly
`|O|` regardless of the correlation structure (Proposition 1, Appendix E).

## The four methods

| Method | Implementation | Engine | Article |
|---|---|---|---|
| Greedy clustering heuristic | [`Baselines/heuristic_synthetic.py`](Baselines/heuristic_synthetic.py) | pure Python | §4.1, Alg. 1, App. A |
| MILP, **set** decision variables (reference) | [`Baselines/milp_synthetic.py`](Baselines/milp_synthetic.py) | Hexaly | §3.4 |
| MILP, **binary** decision variables | [`Baselines/milp_binary_hexaly.py`](Baselines/milp_binary_hexaly.py) | Hexaly | §3.4 |
| Set-partitioning column generation | [`Baselines/cg_setpart_cplex.py`](Baselines/cg_setpart_cplex.py) (aggregated, homogeneous)<br>[`Baselines/cg_setpart_hetero_cplex.py`](Baselines/cg_setpart_hetero_cplex.py) (station-indexed, industrial) | CPLEX | §4.3 |

Baselines: [`Baselines/ga_baseline.py`](Baselines/ga_baseline.py) (GA) and
[`Baselines/sa_correlated.py`](Baselines/sa_correlated.py) (SA-C), parameters in Appendix D.
[`Baselines/milp_gurobi_synthetic.py`](Baselines/milp_gurobi_synthetic.py) is retained for
its canonical `read_data()` and because `verify_lp_bound.py` needs it — it is not a
published row.

## Data

| What | Where | Size |
|---|---|---|
| **29 synthetic benchmark instances** (12×50, 10×500, 4×1000, 3×2000 SKUs) | `exp02a_instances/` | 142 MB |
| Generator (Zhang common-itemset, correlation 0.7) | [`Data_Generators/synthetic_data_zhang.py`](Data_Generators/synthetic_data_zhang.py) | — |
| **Industrial** order lines (Company A: 21,874 SKUs, 26 stations) | `Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv` | 77 MB |
| Capacity-sweep instances (80, EXP-02c — withdrawn from the manuscript) | `capsweep_instances/` — **gitignored**, regenerate with `Baselines/make_capsweep_instances.py` | 557 MB |

Instance integrity is pinned: `python Baselines/verify_instance_hashes.py` must report
**29/29 instances, 87/87 files match** against `exp02a_results/hash_manifest_v3.txt`.

## Results behind each display item

| Article item | Artifact |
|---|---|
| Table 4 `tab:reliability` (29-instance benchmark) | `exp02a_results_rerun/exp02a_per_instance.csv` → `table5_rebuilt.csv` |
| Table 4, CG rows | `exp02a_results/exp02a_cg_setpart.csv` |
| Table 4, heuristic rows (repaired method) | `exp02a_results_repaired/heuristic_benchmark.csv` |
| Table 5 `tab:tests` (paired Wilcoxon) | `exp02a_results/final_formulation_analysis_perinstance.csv` |
| Table 6 `tab:industrial` | `results_industrial_benchmark.csv`, `results_industrial_binary_hexaly.csv`, `results_industrial_cg_setpart*.csv`, `results_industrial_heuristic_final.csv`, `results_metaheuristics_industrial_alone.csv` |
| Table 7 `tab:temporal` | **not reproducible here** — needs the dated extract, see `RERUN_IJPR_RESULTS.md` §4 |
| Table 8 `tab:reassign`, Fig. `fig:ksweep` | `results_reassignment_ksweep_v2.csv` |
| Table C1 `tab:sensitivity` (Appendix C) | `exp02a_results_repaired/exp02a_sensitivity_agg.csv` |
| Fig. `fig:workload` (3 panels) | `plot_industrial_heuristic_workload.py`, `plot_hexaly_industrial_lines.py`, `plot_cg_industrial_lines.py` |
| Appendix E, Prop. 1 | `Baselines/verify_lp_bound.py` |

## Reproducing

Two environments, both Python 3.10: **CPLEX 22.1.1** for the column generation,
**Hexaly** for the two MILP formulations. Reported timings are from a 16-core Windows
Server 2019 host with 128 GB RAM. Per-size caps: 120 / 300 / 600 / 1,200 s.

```bash
export PYTHONHASHSEED=0          # PowerShell: $env:PYTHONHASHSEED = "0"

python Baselines/verify_instance_hashes.py

# Column generation (CPLEX env), ~2h40m
python run_exp02a_cg_setpart.py --sizes 50 500 1000 2000

# Metaheuristics + both MILP formulations (Hexaly env), ~9h20m, restartable
python Baselines/run_exp02a_multiseed.py \
  --sizes 50 500 1000 2000 --k-per-size 12 10 4 3 \
  --ga-seeds 20240612 --ga-sideprobe-seeds 20240613 20240614 \
  --sideprobe-size 50 --sideprobe-k 3 --instance-seed-start 1001 \
  --time-limits 120 300 600 1200 --theta 0.7 \
  --out-dir exp02a_results_rerun --instance-dir exp02a_instances
```

Run these sequentially, not concurrently — Hexaly takes all physical cores by default and
would contend on the wall-clock measurement.

Industrial runs (each reads the BERNER CSV through `data_loader_industrial.py`):

```bash
python run_benchmarks_industrial.py          # set-variable MILP + GA/SA-C rows
python run_industrial_binary_hexaly.py       # binary MILP row
python run_industrial_cg_setpart.py          # station-indexed CG row
python run_industrial_heuristic_alone.py     # heuristic row (self-execs with PYTHONHASHSEED=0)
python run_reassignment_ksweep.py            # bounded reassignment, k in {250,500,1000,2000,5000}
```

Then rebuild the tables:

```bash
python Baselines/rebuild_table5.py
python Baselines/final_formulation_analysis.py
```

## Reproducibility notes

- The clustering heuristic **is now deterministic** — the B4ter repair removed the
  set-iteration-order tie-breaks. `PYTHONHASHSEED=0` is belt and braces, no longer a
  requirement.
- SA-C tests its clock once per temperature level and can overshoot the cap by one inner
  loop (+14% to +24% measured). Deliberately not fixed: it would change a published
  method's behaviour.
- Hexaly's timer starts before model construction while `param.time_limit` bounds the
  search only, so reported wall clock exceeds the cap by the build cost (0.4 s at 50 SKUs
  up to 152.6 s at 2,000).

Full provenance: [`IJPR_revision_changelog.md`](IJPR_revision_changelog.md).
Re-run protocol and measured outcomes: [`RERUN_IJPR_BENCHMARK.md`](RERUN_IJPR_BENCHMARK.md),
[`RERUN_IJPR_RESULTS.md`](RERUN_IJPR_RESULTS.md).
