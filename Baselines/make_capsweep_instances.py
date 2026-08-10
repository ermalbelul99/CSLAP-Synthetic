"""EXP-02c: build the capacity-scaling instance family.

The EXP-02a benchmark confounds catalogue size with station capacity. Its
generator sets |S| = max(5, N//100), so zeta = floor(N/|S|) = 100 for EVERY size
at or above 500 SKUs, and the community bound beta = max(5, min(15, N//20))
saturates at 15 for every N >= 300. Across the whole reported family, therefore,
beta/zeta is the constant 0.15 and no experiment on those instances can tell a
catalogue-scaled rule (beta ~ N) from a capacity-scaled rule (beta ~ zeta).

This script builds the family that separates them: two catalogue sizes crossed
with four station counts, chosen so the SAME four zeta values appear at both
sizes.

    N = 500   |S| = 5, 10, 20, 25   ->  zeta = 100, 50, 25, 20
    N = 1000  |S| = 10, 20, 40, 50  ->  zeta = 100, 50, 25, 20

Ten seeds per cell (2001..2010), disjoint from the 1001..1012 series behind
Table 5, so the new study never reuses an instance a reported result was
computed on. Seeds 2001-2005 are the tuning half and 2006-2010 the test half;
that split is applied in the analysis, not here.

Because `generate_synthetic_data_zhang` draws the historical-station label from a
dedicated RNG stream once |S| is passed explicitly, the order structure - sizes,
itemsets, product fills, quantities - is IDENTICAL across the four station counts
at a fixed seed. A cell-to-cell comparison therefore varies zeta and nothing else.

Layout (mirrors exp02a_instances/):
    capsweep_instances/syn_{N}sku_s{S}_seed{seed}/syn_{N}sku_{orders,stations,products}.csv

Reproduce
---------
cd CSLAP-Synthetic
python Baselines/make_capsweep_instances.py --dry-run
python Baselines/make_capsweep_instances.py
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Tuple

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_THIS_DIR)
_GEN_DIR = os.path.join(_ROOT, "Data_Generators")
if _GEN_DIR not in sys.path:
    sys.path.insert(0, _GEN_DIR)

from synthetic_data_zhang import generate_synthetic_data_zhang  # noqa: E402

# (N, station counts) chosen so both sizes span the same zeta grid.
CELLS: Tuple[Tuple[int, Tuple[int, ...]], ...] = (
    (500, (5, 10, 20, 25)),
    (1000, (10, 20, 40, 50)),
)
SEEDS: Tuple[int, ...] = tuple(range(2001, 2011))
THETA: float = 0.7          # same correlation degree as the EXP-02a family


def plan() -> List[Tuple[int, int, int, int]]:
    """[(N, |S|, zeta, seed)] for every instance in the family."""
    out: List[Tuple[int, int, int, int]] = []
    for size_n, station_counts in CELLS:
        for n_stations in station_counts:
            zeta = size_n // n_stations
            for seed in SEEDS:
                out.append((size_n, n_stations, zeta, seed))
    return out


def instance_dirname(size_n: int, n_stations: int, seed: int) -> str:
    return f"syn_{size_n}sku_s{n_stations}_seed{seed}"


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Build the EXP-02c capacity-scaling family.")
    p.add_argument("--out-dir", type=str, default="capsweep_instances")
    p.add_argument("--dry-run", action="store_true",
                   help="List the cells and exit without generating.")
    p.add_argument("--force", action="store_true",
                   help="Regenerate instances whose directory already exists.")
    args = p.parse_args(argv)

    items = plan()
    if args.dry_run:
        print(f"[dry-run] {len(items)} instances "
              f"({len(CELLS)} sizes x 4 station counts x {len(SEEDS)} seeds)")
        seen = set()
        print(f"{'N':>6}{'|S|':>6}{'zeta':>7}{'seeds':>10}")
        print("-" * 29)
        for size_n, n_stations, zeta, _seed in items:
            key = (size_n, n_stations)
            if key in seen:
                continue
            seen.add(key)
            print(f"{size_n:>6}{n_stations:>6}{zeta:>7}{len(SEEDS):>10}")
        return 0

    made = skipped = 0
    for idx, (size_n, n_stations, zeta, seed) in enumerate(items, start=1):
        name = instance_dirname(size_n, n_stations, seed)
        inst_dir = os.path.join(args.out_dir, name)
        prefix = f"syn_{size_n}sku"
        csvs = [os.path.join(inst_dir, f"{prefix}_{k}.csv")
                for k in ("orders", "stations", "products")]
        if all(os.path.exists(c) for c in csvs) and not args.force:
            print(f"[{idx}/{len(items)}] skip {name} (exists)")
            skipped += 1
            continue
        os.makedirs(inst_dir, exist_ok=True)
        print(f"[{idx}/{len(items)}] {name} (zeta={zeta})")
        generate_synthetic_data_zhang(
            num_skus=size_n,
            theta=THETA,
            seed=seed,
            output_dir=inst_dir,
            num_stations=n_stations,
            prefix=prefix,
        )
        made += 1

    print(f"[done] {made} generated, {skipped} already present -> {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
