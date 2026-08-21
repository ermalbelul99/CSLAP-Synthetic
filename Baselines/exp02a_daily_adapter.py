r"""Adapter: dated exp02a article instances -> rolling-origin daily folds.

Synthetic arm of the workload-feasibility study, built on the same benchmark
family as the submitted article. The published instances carry no time
dimension -- the Zhang construction draws an i.i.d. bag of orders -- so the
generator is re-run with its optional calendar layer enabled, which places each
order on a business day without altering the orders themselves. The instances
therefore remain the article's instances; only a ``DELIVERY_DATE`` is added.

Calendar parameters default to the values measured on the industrial series by
``demand_diagnostics.py``, so the synthetic warehouse is not merely "some
time series" but one whose daily behaviour matches a real one where it can be
matched. Two deliberate differences from the industrial arm:

* **No incumbent.** exp02a's ``STATION`` column is a random label, not an
  operating layout, so there is no live assignment to reveal capacity from.
  Folds are built in ``balanced`` mode -- an equal share of a quantile day --
  and the control arm is the nominal :math:`\Gamma = 0` layout rather than an
  incumbent.
* **No freezing.** The catalogues are small enough to place in full, so every
  SKU stays a decision variable.

``--drift`` sweeps demand growth between the training and test windows, which
is the dial the industrial data cannot offer: one site, one season, one
realisation. Sweeping it turns "does protection help under drift?" from an
anecdote into a dose-response curve.

No solver is used or imported.

CLI::

    python exp02a_daily_adapter.py --out <folds_root> [--sizes 500 1000]
        [--seeds 1001 1002] [--drift 0.0] [--tcap-quantile max]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

import pandas as pd

BASE: str = os.path.dirname(os.path.abspath(__file__))
_ROOT: str = os.path.dirname(BASE)
sys.path.insert(0, BASE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "Data_Generators"))

from daily_folds import QUANTILES, build_daily_folds  # noqa: E402
from paths import DERIVED, EXP02A_INSTANCES  # noqa: E402
from synthetic_data_zhang import generate_synthetic_data_zhang  # noqa: E402

DEFAULT_OUT: str = os.path.join(DERIVED, "exp02a_daily_folds")
_TAG_RE = re.compile(r"^syn_(\d+)sku_seed(\d+)$")


def discover_instances(instances_dir: str) -> List[Tuple[int, int]]:
    """List the ``(num_skus, seed)`` pairs of the committed benchmark family.

    Args:
        instances_dir: Directory holding ``syn_<N>sku_seed<S>`` subdirectories.

    Returns:
        Sorted ``(num_skus, seed)`` pairs.
    """
    found: List[Tuple[int, int]] = []
    if not os.path.isdir(instances_dir):
        return found
    for name in sorted(os.listdir(instances_dir)):
        m = _TAG_RE.match(name)
        if m:
            found.append((int(m.group(1)), int(m.group(2))))
    return sorted(found)


def generate_dated_instance(num_skus: int, seed: int, work_dir: str,
                            **calendar_kwargs) -> pd.DataFrame:
    """Regenerate one benchmark instance with the calendar layer enabled.

    The order stream is identical to the committed instance -- the calendar
    draws come from a dedicated RNG stream -- so this adds a date column rather
    than producing different demand.

    Args:
        num_skus: Catalogue size.
        seed: Instance seed.
        work_dir: Scratch directory for the generated CSVs.
        **calendar_kwargs: Passed through to the generator.

    Returns:
        ``(orders, stations)`` for the dated instance.
    """
    os.makedirs(work_dir, exist_ok=True)
    orders, stations, _products = generate_synthetic_data_zhang(
        num_skus=num_skus, seed=seed, output_dir=work_dir,
        calendar=True, **calendar_kwargs)
    return orders, stations


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Dated exp02a instances -> rolling-origin daily folds")
    parser.add_argument("--instances", type=str, default=EXP02A_INSTANCES)
    parser.add_argument("--out", type=str, default=DEFAULT_OUT)
    parser.add_argument("--work", type=str, default=None,
                        help="Scratch dir for the dated instances "
                             "(default: <out>/_instances)")
    parser.add_argument("--sizes", nargs="*", type=int, default=None,
                        help="Restrict to these catalogue sizes")
    parser.add_argument("--seeds", nargs="*", type=int, default=None,
                        help="Restrict to these seeds")
    parser.add_argument("--tcap-quantile", type=str, default="max",
                        choices=sorted(QUANTILES))
    parser.add_argument("--min-train-weeks", type=int, default=8)
    parser.add_argument("--test-weeks", type=int, default=4)
    parser.add_argument("--days", type=int, default=63)
    parser.add_argument("--start-date", type=str, default="2021-09-01")
    parser.add_argument("--residual-cv", type=float, default=0.167)
    parser.add_argument("--month-end-index", type=float, default=1.27)
    parser.add_argument("--cospike-cv", type=float, default=0.35)
    parser.add_argument("--drift", type=float, default=0.0)
    parser.add_argument("--suffix", type=str, default="",
                        help="Appended to each fold tag, e.g. '_drift03'")
    args = parser.parse_args()

    pairs = discover_instances(args.instances)
    if args.sizes:
        pairs = [p for p in pairs if p[0] in set(args.sizes)]
    if args.seeds:
        pairs = [p for p in pairs if p[1] in set(args.seeds)]
    if not pairs:
        raise SystemExit(f"no instances matched under {args.instances}")

    work = args.work or os.path.join(args.out, "_instances")
    cal = {
        "days": args.days, "start_date": args.start_date,
        "residual_cv": args.residual_cv,
        "month_end_index": args.month_end_index,
        "cospike_cv": args.cospike_cv, "drift": args.drift,
    }
    print(f"[exp02a_daily_adapter] {len(pairs)} instances | drift={args.drift:g} "
          f"| q={args.tcap_quantile}", flush=True)

    total = 0
    for num_skus, seed in pairs:
        tag = f"syn_{num_skus}sku_seed{seed}{args.suffix}"
        inst_dir = os.path.join(work, tag)
        orders, stations = generate_dated_instance(
            num_skus, seed, inst_dir, **cal)

        # PRODUCT arrives as "PROD_<id>"; the fold builder re-applies the
        # prefix, so hand it the bare identifier.
        od = orders.rename(columns={"DELIVERY_DATE": "DATE"}).copy()
        od["PRODUCT"] = od["PRODUCT"].str.replace("PROD_", "", regex=False)
        od["DATE"] = pd.to_datetime(od["DATE"])

        out_dirs = build_daily_folds(
            orders=od[["ORDER", "PRODUCT", "QTY", "DATE"]],
            stations=stations,
            out_root=args.out,
            tag=tag,
            incumbent=None,
            min_train_weeks=args.min_train_weeks,
            n_test_weeks=args.test_weeks,
            tcap_mode="balanced",
            tcap_quantile=args.tcap_quantile,
            extra_meta={"dataset": "exp02a", "num_skus": num_skus,
                        "seed": seed, "drift": args.drift,
                        "cospike_cv": args.cospike_cv},
        )
        total += len(out_dirs)

    print(f"[exp02a_daily_adapter] wrote {total} folds -> {args.out}")


if __name__ == "__main__":
    main()
