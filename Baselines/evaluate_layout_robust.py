r"""
Fixed-layout evaluation functional for CSLAP robustness.

Implements Method Report (``reports/2_method_report.md``) Section C.5,
equation (11): given a **fixed** layout :math:`a: P \to S` and a fresh order
family :math:`O^{te}`, it computes the total station visits and the companion
robustness statistics (coverage :math:`\kappa`, realised workloads, constraint
violations). This is a direct computation -- **no solver is imported** -- and is
the sole reader of test orders in the no-leakage protocol (Method Report E.2).

Evaluation functional (Method Report eq. 11, C.5)
-------------------------------------------------
.. math::
    \mathcal{V}(a, O^{te}) = \sum_{o \in O^{te}}
    \big|\{\, a(p) : p \in P_o \cap \operatorname{dom}(a) \,\}\big| .       \tag{11}

Companions:

* Per-order mean visits :math:`\mathcal{V}(a, O^{te}) / |O^{te}|`.
* Coverage :math:`\kappa = \sum_o |P_o \cap \operatorname{dom}(a)| /
  \sum_o |P_o|` -- fraction of test pick-lines whose SKU exists in the training
  universe. SKUs unseen in training are **excluded from (11)** and reported via
  :math:`\kappa`, identically for all compared layouts so the comparison is fair.
* Realised workloads :math:`W_s = \sum_{p:\,a(p)=s} L_p^{te} / V_s` checked
  against the **true** ``TIME_CAPACITY`` of the test instance (``wl_broken``), and
  product counts checked against ``CAPACITY`` (``cap_broken``).

The layout is a JSON ``{product: station}`` persisted by the harness from each
runner's ``assignment`` (the first element of the standard return tuple).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

EVAL_CSV_COLUMNS: List[str] = [
    "layout_id", "solver", "instance", "k", "variant", "split",
    "test_prefix", "theta_prime", "rho", "test_seed",
    "total_visits", "mean_visits_per_order", "num_orders",
    "coverage_kappa", "num_unseen_lines",
    "cap_broken", "wl_broken", "max_workload", "workload_std",
    "domain_size", "universe_size",
]


# ---------------------------------------------------------------------------
#  DATA LOADING (test instance; semicolon schema)
# ---------------------------------------------------------------------------
def load_test_instance(
    prefix: str, data_dir: str
) -> Tuple[Dict[str, List[str]], List[dict], Dict[str, int]]:
    r"""Load a test instance's orders, stations, and realised pick-lines.

    Args:
        prefix: Test dataset prefix.
        data_dir: Directory holding the test CSVs (semicolon-separated).

    Returns:
        ``(order_prods, stations, prod_lines_te)`` where ``order_prods`` maps each
        order id to its product list, ``stations`` is the station record list, and
        ``prod_lines_te`` maps each product token to its realised line count
        :math:`L_p^{te}`.
    """
    orders_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";")
    stations_df = pd.read_csv(os.path.join(data_dir, f"{prefix}_stations.csv"), sep=";")
    order_prods = orders_df.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
    stations = stations_df.to_dict(orient="records")
    prod_lines_te = orders_df.groupby("PRODUCT").size().to_dict()
    return order_prods, stations, prod_lines_te


# ---------------------------------------------------------------------------
#  EVALUATION FUNCTIONAL (eq. 11 + C.5)
# ---------------------------------------------------------------------------
def evaluate_layout(
    assignment: Dict[str, object],
    order_prods: Dict[str, List[str]],
    stations: List[dict],
    prod_lines_te: Dict[str, int],
) -> Dict[str, object]:
    r"""Evaluate a fixed layout on a test order family (Method Report eq. 11, C.5).

    Args:
        assignment: Layout :math:`a` as a ``{product: station}`` dict.
        order_prods: Test orders, product lists per order.
        stations: Test station records (``STATION_ID``/``CAPACITY``/
            ``TIME_CAPACITY``/``SPEED``).
        prod_lines_te: Realised test pick-line counts :math:`L_p^{te}`.

    Returns:
        Dict of metrics: ``total_visits``, ``mean_visits_per_order``,
        ``num_orders``, ``coverage_kappa``, ``num_unseen_lines``, ``cap_broken``,
        ``wl_broken``, ``max_workload``, ``workload_std``, ``domain_size``.
    """
    domain = set(assignment.keys())

    # eq. (11): visits over SKUs present in the layout domain.
    total_visits = 0
    total_lines = 0
    covered_lines = 0
    for _o, prods in order_prods.items():
        visited: set = set()
        for p in prods:
            total_lines += 1
            if p in domain:
                covered_lines += 1
                visited.add(assignment[p])
        total_visits += len(visited)

    num_orders = len(order_prods)
    mean_visits = total_visits / num_orders if num_orders else 0.0
    kappa = covered_lines / total_lines if total_lines else 0.0
    num_unseen = total_lines - covered_lines

    # Realised workloads vs the TRUE test capacities (C.5).
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}
    caps = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    station_ids = [s["STATION_ID"] for s in stations]

    station_counts: Dict[object, int] = defaultdict(int)
    station_workload: Dict[object, float] = defaultdict(float)
    for p, sid in assignment.items():
        station_counts[sid] += 1
        v = speeds.get(sid, 1.0)
        station_workload[sid] += prod_lines_te.get(p, 0) / v if v > 0 else 0.0

    cap_broken = sum(1 for sid in station_ids if station_counts[sid] > caps.get(sid, 0))
    wl_broken = sum(
        1 for sid in station_ids if station_workload[sid] > time_caps.get(sid, 0)
    )
    workloads = [station_workload[sid] for sid in station_ids]
    max_wl = float(np.max(workloads)) if workloads else 0.0
    std_wl = float(np.std(workloads)) if workloads else 0.0

    return {
        "total_visits": total_visits,
        "mean_visits_per_order": mean_visits,
        "num_orders": num_orders,
        "coverage_kappa": kappa,
        "num_unseen_lines": num_unseen,
        "cap_broken": cap_broken,
        "wl_broken": wl_broken,
        "max_workload": max_wl,
        "workload_std": std_wl,
        "domain_size": len(domain),
    }


def load_layout(layout_path: str) -> Dict[str, object]:
    r"""Load a ``{product: station}`` layout JSON persisted by the harness."""
    with open(layout_path) as fh:
        data = json.load(fh)
    # Layouts may be nested under "assignment"; accept both forms.
    if isinstance(data, dict) and "assignment" in data and isinstance(
        data["assignment"], dict
    ):
        return data["assignment"]
    return data


def append_eval_row(csv_path: str, row: Dict[str, object]) -> None:
    r"""Append one evaluation row to ``results_robustness_eval.csv``.

    Writes the header if the file does not yet exist. Unknown keys are dropped and
    missing columns are filled blank, so the schema stays stable across callers.
    """
    exists = os.path.exists(csv_path)
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    with open(csv_path, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=EVAL_CSV_COLUMNS)
        if not exists:
            writer.writeheader()
        writer.writerow({c: row.get(c, "") for c in EVAL_CSV_COLUMNS})


def evaluate_and_log(
    layout_path: str,
    test_prefix: str,
    data_dir: str,
    results_csv: str = "results_robustness_eval.csv",
    meta: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    r"""Evaluate a layout file on a test prefix and append a results row.

    Args:
        layout_path: Path to the layout JSON.
        test_prefix: Test dataset prefix.
        data_dir: Directory of the test CSVs.
        results_csv: Output results CSV (appended).
        meta: Optional metadata merged into the row (solver, k, theta', rho, ...).

    Returns:
        The full row dict that was appended.
    """
    assignment = load_layout(layout_path)
    order_prods, stations, prod_lines_te = load_test_instance(test_prefix, data_dir)
    metrics = evaluate_layout(assignment, order_prods, stations, prod_lines_te)

    row: Dict[str, object] = {
        "layout_id": os.path.splitext(os.path.basename(layout_path))[0],
        "test_prefix": test_prefix,
    }
    if meta:
        row.update(meta)
    row.update(metrics)
    append_eval_row(results_csv, row)
    return row


# ---------------------------------------------------------------------------
#  CLI
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI entry point: evaluate one layout JSON on one test prefix."""
    parser = argparse.ArgumentParser(
        description="Evaluate a fixed CSLAP layout on test orders (eq. 11, C.5)."
    )
    parser.add_argument("--layout", type=str, required=True,
                        help="Path to the {product: station} layout JSON.")
    parser.add_argument("--prefix", type=str, required=True,
                        help="Test dataset prefix.")
    parser.add_argument("--dir", type=str, default="synthetic_datasets")
    parser.add_argument("--results-csv", type=str,
                        default="results_robustness_eval.csv")
    parser.add_argument("--solver", type=str, default="")
    parser.add_argument("--instance", type=str, default="")
    parser.add_argument("--k", type=str, default="")
    parser.add_argument("--variant", type=str, default="")
    args = parser.parse_args()

    meta = {
        "solver": args.solver, "instance": args.instance,
        "k": args.k, "variant": args.variant,
    }
    row = evaluate_and_log(
        args.layout, args.prefix, args.dir, args.results_csv, meta
    )
    print(
        f"visits={row['total_visits']} "
        f"mean/order={row['mean_visits_per_order']:.4f} "
        f"kappa={row['coverage_kappa']:.4f} "
        f"cap_broken={row['cap_broken']} wl_broken={row['wl_broken']} "
        f"-> {args.results_csv}"
    )


if __name__ == "__main__":
    main()
