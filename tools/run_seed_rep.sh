#!/usr/bin/env bash
# Seed replication: how much of the g0 -> g2 difference is the MODEL, and how
# much is where local search happened to stop? The grid ran one seed per cell,
# so a between-arm difference could not be separated from within-arm spread.
# This re-runs z=4 (the cleanest cell) for Gamma 0 and 2 on all four folds at
# two further seeds; the grid run itself is the third sample.
set -u
REPO="/c/ermal/CSLAP_Full_Project/CSLAP-Synthetic"
PY="/c/ermal/Virtual_Environment_LocalSolver_3/Scripts/python.exe"
cd "$REPO" || exit 1
for s in 11 22; do
  for f in 0 1 2 3; do
    OUT="results/z_contract/_seed_rep/z4_f${f}_s${s}"
    echo "[seed] START fold=$f seed=$s $(date -u +%H:%M:%S)"
    "$PY" Baselines/run_bs_robust_experiment.py \
      --dir "data/derived/berner_daily_folds/berner_daily_r0f${f}" \
      --prefix berner_daily --folds "$f" \
      --gammas 0,2 --betas none --time 600 --backend hexaly --share-z 4 \
      --solver-seed "$s" \
      --layouts-dir "$OUT/_nolayouts" --out "$OUT" \
      > "results/logs/seedrep_z4_f${f}_s${s}.log" 2>&1
    echo "[seed] END   fold=$f seed=$s rc=$? $(date -u +%H:%M:%S)"
    rm -rf "$OUT/_nolayouts"
  done
done
echo "[seed] SEED REPLICATION COMPLETE $(date -u +%H:%M:%S)"
