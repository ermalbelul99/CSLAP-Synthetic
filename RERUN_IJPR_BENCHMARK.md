# Re-run the IJPR synthetic benchmark under the published budgets

**Run this on the machine that has CPLEX** (the one with `Virtual_Environment_CPLEX_1`).
It re-runs every method in Table 5 of `IJPR_CSLAP_v2.tex` under the budgets the table prints, so
the reported protocol and the actual runs agree.

## Why this is needed

The table states one budget per size for all optimising methods and claims the set-variable MILP and
the column generation "each consume the full budget at every size, so their visit comparison is made
at equal computational effort". The stored results contradict that:

| Size | Table says | Hexaly actually used | CG actually used | SA-C actually used |
|---|---|---|---|---|
| 50 | 120 s | 123 s | 86 s | 39 s |
| 500 | 300 s | **1,148 s** (range 455–4,684) | **476 s** (600 s budget) | 341 s |
| 1,000 | 600 s | 645 s | 599 s | **977 s** |
| 2,000 | 1,200 s | **1,049 s** (900 s configured) | 1,199 s | 1,096 s |

The synthetic instances are released with the paper, so a referee can recompute this. Two entries
are the problem: the CG ran at 500 SKUs with a 600 s budget (now corrected to 300 s in
`run_exp02a_cg_setpart.py`), and the earlier Hexaly/SA-C runs overran their configured limits.

## Binding protocol

Budgets, per size, for **every** method: **120 s (50 SKUs), 300 s (500), 600 s (1,000), 1,200 s
(2,000)**. The 29 instances in `exp02a_instances/` are unchanged — do not regenerate them; their
SHA-256 hashes are in `exp02a_results/hash_manifest_v3.txt`.

## Step 0 — get this version

```bash
git clone https://github.com/ermalbelul99/CSLAP-Synthetic.git
cd CSLAP-Synthetic
git checkout ijpr-revision-20260729
```

If the repository already exists on that machine, `git fetch origin && git checkout ijpr-revision-20260729`.

## Step 1 — verify the instances survived the transfer

```bash
python Baselines/verify_instance_hashes.py
```

Expect `29/29 instances match`. If any differ, stop: the re-run would not be comparable with the
published table.

## Step 2 — metaheuristics and the set-variable MILP (Hexaly environment)

Writes to a **fresh** directory so nothing overwrites the existing results.

```bash
python Baselines/run_exp02a_multiseed.py \
  --sizes 50 500 1000 2000 --k-per-size 12 10 4 3 \
  --ga-seeds 20240612 --ga-sideprobe-seeds 20240613 20240614 \
  --sideprobe-size 50 --sideprobe-k 3 \
  --instance-seed-start 1001 \
  --time-limits 120 300 600 1200 \
  --theta 0.7 \
  --out-dir exp02a_results_rerun --instance-dir exp02a_instances
```

Runs Heuristic, SA-C, GA and Hexaly on all 29 instances. Restartable: re-running skips
`(size, seed, method, solver_seed)` combinations already recorded, so a crash or a reboot costs only
the run in flight. Expect roughly 9–11 hours.

## Step 3 — set-partitioning column generation (CPLEX environment)

```bash
# activate Virtual_Environment_CPLEX_1 first
python run_exp02a_cg_setpart.py --sizes 50 500 1000 2000
```

Appends to `exp02a_results/exp02a_cg_setpart.csv`. **Move or rename the existing file first** if you
want the old rows kept separately:

```bash
mv exp02a_results/exp02a_cg_setpart.csv exp02a_results/exp02a_cg_setpart_600s500.csv
```

`BUDGET` in that script is now `{50: 120, 500: 300, 1000: 600, 2000: 1200}`, matching the table.
Expect roughly 3 hours. Steps 2 and 3 are independent and can run at the same time if the machine
has the cores; if not, run step 3 first (it is shorter and it is the one that needs CPLEX).

## Step 4 — aggregate and send back

```bash
python Baselines/run_exp02a_multiseed.py --aggregate-only --out-dir exp02a_results_rerun
git add exp02a_results_rerun exp02a_results/exp02a_cg_setpart*.csv
git commit -m "Re-run exp02a benchmark under published per-size budgets"
git push origin ijpr-revision-20260729
```

If `--aggregate-only` is not accepted by that version of the runner, skip it: the per-instance CSV is
what matters and the aggregation is recomputed on the other side.

Then say the push is done, and Table 5, the statistical tests and every gap figure in Section 5 get
rebuilt from the new per-instance numbers.

## What is not re-run, and why

- **The industrial case (Table 8) and the k-sweep (Table 10).** Both already ran at their stated
  budgets (36,000 s and 3,600 s per k) and their stored results match the manuscript.
- **The heuristic threshold-sensitivity sweep.** It runs under these same caps and needs no CPLEX,
  so it is being run on the laptop.
- **The temporal hold-out (Table 9).** No stored artifact for those six numbers has been found in
  either repository. If you have the script or the output on that machine, copy it in — otherwise
  that table has to be regenerated or dropped before submission.

## Note on reproducibility

The clustering heuristic is not deterministic across processes: it groups products through Python
sets, so its greedy tie-breaks follow set iteration order, which CPython randomises per process. On
`syn_50sku_seed1004`, three identical unseeded runs gave 6,643 / 6,622 / 6,622 visits; with
`PYTHONHASHSEED=0` every run gives 6,622. Set `PYTHONHASHSEED=0` before step 2 if you want the
heuristic rows to be reproducible run to run:

```bash
export PYTHONHASHSEED=0      # PowerShell: $env:PYTHONHASHSEED = "0"
```

The GA and SA-C carry their own seeds and are unaffected; Hexaly and CPLEX are seeded in the code.
