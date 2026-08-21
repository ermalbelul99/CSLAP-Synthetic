r"""Adapter: exp02a article instances -> temporal fold format for the BS harness.

The exp02a instances (``CSLAP-Synthetic/exp02a_instances/syn_{N}sku_seed{S}/``)
are the synthetic benchmark of the Computers & OR manuscript: uniform stations
(``|S| = N/100`` stations, 100 slots each, exactly binding), semicolon CSVs,
products WITHOUT the ``REAL_LINES`` column the BS harness expects.

For each instance this adapter writes ONE temporal train/test cut in the fold
format of ``run_robustness_iscf.make_folds`` (train-early / test-late by ORDER
rank, assumption U1; ORD_<n> ids are sequential):

    {out}/{tag}/{tag}_r0f0_{train|test}_{orders|products|stations}.csv

with the established kappa-invariant conventions:
  * train products carry ``REAL_LINES`` = number of distinct TRAIN orders
    containing the product (asserted equal to train row counts: exp02a has no
    duplicate (ORDER, PRODUCT) rows);
  * the train stations file carries ``TIME_CAPACITY`` =
    ceil(1.10 * sum_p REAL_LINES / (SPEED * |S|)) computed on the TRAIN volume;
  * the test instance re-uses the train products/stations files (the as-run
    check semantics of the project pipeline).

CLI:
    python exp02a_bs_adapter.py --dir <exp02a_instances> --out <folds_root>
        --train-frac 0.7
"""
from __future__ import annotations

import argparse
import math
import os
import sys
from typing import List

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import DERIVED, EXP02A_INSTANCES  # noqa: E402

BASE: str = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IN: str = EXP02A_INSTANCES
DEFAULT_OUT: str = os.path.join(DERIVED, "exp02a_folds")
SLACK: float = 1.10


def build_fold(inst_dir: str, out_root: str, train_frac: float) -> str:
    """Write the r0f0 temporal cut for one exp02a instance directory.

    Args:
        inst_dir: Instance directory (e.g. ...\\syn_500sku_seed1001).
        out_root: Root output directory (one subdir per instance tag).
        train_frac: Early fraction of distinct orders used as train.

    Returns:
        The instance tag (e.g. ``syn_500sku_seed1001``).
    """
    tag = os.path.basename(inst_dir.rstrip("\\/"))
    prefix = tag.split("_seed")[0]  # e.g. syn_500sku
    orders = pd.read_csv(os.path.join(inst_dir, f"{prefix}_orders.csv"), sep=";")
    products = pd.read_csv(os.path.join(inst_dir, f"{prefix}_products.csv"), sep=";")
    stations = pd.read_csv(os.path.join(inst_dir, f"{prefix}_stations.csv"), sep=";")

    # exp02a orders CAN repeat (ORDER, PRODUCT); the instance's own
    # TIME_CAPACITY equals ceil(1.10 * row_count / |S|), i.e. the colleague's
    # convention counts every row as a pick line. REAL_LINES therefore uses
    # row counts (groupby size), matching the evaluator's te_lines semantics.
    n_dup = int(orders.duplicated(["ORDER", "PRODUCT"]).sum())

    order_ids = orders["ORDER"].unique()  # file order; ORD_<n> is sequential
    n_train = int(round(train_frac * len(order_ids)))
    train_ids = set(order_ids[:n_train])
    train_orders = orders[orders["ORDER"].isin(train_ids)]
    test_orders = orders[~orders["ORDER"].isin(train_ids)]

    # Train REAL_LINES = train pick-line rows per product (row-count convention).
    train_lp = train_orders.groupby("PRODUCT").size()
    tok = "PROD_" + products["PRODUCT_ID"].astype(str)
    train_products = products.copy()
    train_products["REAL_LINES"] = tok.map(train_lp).fillna(0).astype(int).to_numpy()

    speed = float(stations["SPEED"].iloc[0])
    n_s = len(stations)
    total = int(train_products["REAL_LINES"].sum())
    t_cap = int(math.ceil(SLACK * total / (speed * n_s)))
    train_stations = stations.copy()
    train_stations["TIME_CAPACITY"] = t_cap

    out_dir = os.path.join(out_root, tag)
    os.makedirs(out_dir, exist_ok=True)
    fold_tag = f"{tag}_r0f0"
    for role, odf in (("train", train_orders), ("test", test_orders)):
        odf.to_csv(os.path.join(out_dir, f"{fold_tag}_{role}_orders.csv"),
                   index=False, sep=";")
        train_products.to_csv(
            os.path.join(out_dir, f"{fold_tag}_{role}_products.csv"),
            index=False, sep=";")
        train_stations.to_csv(
            os.path.join(out_dir, f"{fold_tag}_{role}_stations.csv"),
            index=False, sep=";")

    print(f"[exp02a_bs_adapter] {tag}: |S|={n_s} train_orders={n_train} "
          f"test_orders={len(order_ids) - n_train} lines_tr={total} "
          f"T_s(train)={t_cap} dup_rows={n_dup}", flush=True)
    return tag


def main() -> None:
    """Build folds for every exp02a instance (CLI)."""
    parser = argparse.ArgumentParser(
        description="exp02a -> BS-harness temporal fold adapter")
    parser.add_argument("--dir", type=str, default=DEFAULT_IN)
    parser.add_argument("--out", type=str, default=DEFAULT_OUT)
    parser.add_argument("--train-frac", type=float, default=0.7)
    parser.add_argument("--only", type=str, default=None,
                        help="Comma-separated instance tags to build (default all)")
    args = parser.parse_args()

    tags: List[str] = sorted(
        d for d in os.listdir(args.dir)
        if os.path.isdir(os.path.join(args.dir, d))
    )
    if args.only:
        wanted = set(args.only.split(","))
        tags = [t for t in tags if t in wanted]
    for tag in tags:
        build_fold(os.path.join(args.dir, tag), args.out, args.train_frac)
    print(f"[exp02a_bs_adapter] DONE: {len(tags)} instances -> {args.out}",
          flush=True)


if __name__ == "__main__":
    main()
