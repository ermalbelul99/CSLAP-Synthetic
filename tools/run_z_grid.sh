#!/usr/bin/env bash
# Phase 7: the pre-registered 12-cell grid under the volume-normalised share
# contract. 4 folds x 3 z x (4 Gamma + 2 beta) = 72 solver rows, Hexaly 600 s
# per arm, exactly as declared in GATES_z_contract.md before any solving.
#
# The driver writes results.csv with to_csv (overwrite) from a process-local
# row list, so sending four folds to one --out keeps only the last. Each fold
# is snapshotted the moment its process EXITS (no polling, no race -- the race
# is what cost a complete arm in the earlier Hexaly run), and the snapshots are
# merged into the cell's results.csv once the cell is done.
set -u
REPO="/c/ermal/CSLAP_Full_Project/CSLAP-Synthetic"
PY="/c/ermal/Virtual_Environment_LocalSolver_3/Scripts/python.exe"
cd "$REPO" || exit 1
mkdir -p results/logs

for z in 3 4 6; do
  CELL="results/z_contract/z${z}"
  SNAP="$CELL/_snapshots"
  mkdir -p "$SNAP"
  for f in 0 1 2 3; do
    LOG="results/logs/zgrid_z${z}_f${f}.log"
    # Clear last fold's outputs FIRST. persist() overwrites from a
    # process-local list, so a fold that dies before its first persist would
    # otherwise leave the previous fold's file in place, be snapshotted as a
    # duplicate, and merge into a complete-looking 24 rows with no error.
    rm -f "$CELL/results.csv" "$CELL/calibration.csv" "$CELL/per_station.csv"
    echo "[zgrid] START z=$z fold=$f $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    "$PY" Baselines/run_bs_robust_experiment.py \
      --dir "data/derived/berner_daily_folds/berner_daily_r0f${f}" \
      --prefix berner_daily --folds "$f" \
      --gammas 0,1,2,4 --betas 1.02,1.05 \
      --time 600 --backend hexaly --share-z "$z" \
      --layouts-dir "$CELL/_nolayouts" \
      --out "$CELL" >"$LOG" 2>&1
    rc=$?
    if [ ! -f "$CELL/results.csv" ]; then
      echo "[zgrid] FATAL z=$z fold=$f produced no results.csv (rc=$rc)" >&2
      exit 1
    fi
    for n in results calibration per_station; do
      [ -f "$CELL/$n.csv" ] && cp "$CELL/$n.csv" "$SNAP/f${f}_${n}.csv"
    done
    echo "[zgrid] END   z=$z fold=$f rc=$rc $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  done
  "$PY" - "$CELL" <<'PYEOF'
import glob, os, sys
import pandas as pd
cell = sys.argv[1]
for name in ("results", "calibration", "per_station"):
    parts = sorted(glob.glob(os.path.join(cell, "_snapshots", f"f*_{name}.csv")))
    if len(parts) != 4:
        raise SystemExit(f"[zgrid] {cell} {name}: {len(parts)} snapshots, expected 4")
    d = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
    d.to_csv(os.path.join(cell, f"{name}.csv"), index=False)
    print(f"[zgrid] merged {len(parts)} {name} snapshots -> {len(d)} rows in {cell}")
PYEOF
  rm -rf "$CELL/_nolayouts"
done
echo "[zgrid] ALL 12 CELLS COMPLETE $(date -u +%Y-%m-%dT%H:%M:%SZ)"
