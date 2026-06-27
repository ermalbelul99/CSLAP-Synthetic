r"""Oracle relative-regret (RR, Method Report eq. 12) for the CSLAP robustness study.

Reviewer item 4. The test-shift gain :math:`G(k)` (eq. 13) tells us whether the
robust layout beats the nominal layout, but not *how much* of the achievable
out-of-sample headroom it captures. The oracle normaliser is the layout the same
solver produces when it is allowed to re-optimise **directly on the test
instance** (test data used as a normaliser only, by design and clearly labelled):

.. math::
    \mathrm{RR}(a) = \frac{\mathcal{V}(a, O^{te}) - \mathcal{V}(a^{or}, O^{te})}
                          {\mathcal{V}(a^{or}, O^{te})} .                 \tag{12}

For the seed-42 syn_50sku train instance only, and the test cells
:math:`(\theta'=0.7,\ \rho \in \{0, 1.0\},\ \text{seed}=43)`, this script:

1. re-optimises each solver (heuristic, sa, ga) directly on the test instance to
   obtain the oracle layout :math:`a^{or}` (same 60s budget, GA global-RNG seed
   fixed as in the main harness);
2. evaluates the stored nominal (k=1) and robust (k=2) layouts and the oracle
   layout on that test cell (eq. 11);
3. writes RR for the k=1 and k=2 layouts to ``results_oracle_rr.csv``.

The oracle is **out of the no-leakage protocol by construction** -- it is a
normaliser, never a deployed layout. The CSV is clearly labelled as such.
"""
from __future__ import annotations

import csv
import os
import sys
from typing import Dict, List

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import evaluate_layout_robust as ev  # noqa: E402
import run_robustness_experiment as H  # noqa: E402


def main() -> None:
    data_dir = os.path.join(_HERE, "..", "synthetic_datasets")
    instance = "syn_50sku"
    solvers = ["heuristic", "sa", "ga"]
    budget = 60
    test_cells = [
        ("syn_50sku_te_t0.7_r0.0_s43", 0.7, 0.0, 43),
        ("syn_50sku_te_t0.7_r1.0_s43", 0.7, 1.0, 43),
    ]
    out_csv = os.path.join(_HERE, "results_oracle_rr.csv")
    cols = ["instance", "solver", "k", "test_prefix", "theta_prime", "rho",
            "test_seed", "V_te_layout", "V_te_oracle", "RR", "note"]
    rows: List[Dict[str, object]] = []

    for solver in solvers:
        for (te_prefix, tp, rho, sd) in test_cells:
            # Oracle: re-optimise directly on the test instance (normaliser).
            if solver == "ga":
                np.random.seed(H.GA_GLOBAL_SEED)
            assignment, _v, elapsed = H.run_solver(
                solver, te_prefix, data_dir, budget, quick=True
            )
            if assignment is None:
                print(f"[{solver} {te_prefix}] oracle: no layout; skip")
                continue
            order_prods, stations, plte = ev.load_test_instance(te_prefix, data_dir)
            v_oracle = ev.evaluate_layout(assignment, order_prods, stations, plte)[
                "total_visits"]

            for k in (1, 2):
                layout_path = os.path.join(
                    _HERE, "layouts", f"{instance}_{solver}_k{k}_exact.json"
                )
                if not os.path.exists(layout_path):
                    print(f"[{solver} k={k}] layout missing: {layout_path}")
                    continue
                lay = ev.load_layout(layout_path)
                v_layout = ev.evaluate_layout(lay, order_prods, stations, plte)[
                    "total_visits"]
                rr = (v_layout - v_oracle) / v_oracle if v_oracle else None
                rows.append({
                    "instance": instance, "solver": solver, "k": k,
                    "test_prefix": te_prefix, "theta_prime": tp, "rho": rho,
                    "test_seed": sd, "V_te_layout": v_layout,
                    "V_te_oracle": v_oracle,
                    "RR": round(rr, 5) if rr is not None else "",
                    "note": "oracle=test-reoptimized normalizer (eq.12); "
                            "test data seen BY DESIGN as normalizer only",
                })
                print(f"[{solver} k={k} {te_prefix}] V_lay={v_layout} "
                      f"V_or={v_oracle} RR={rr:+.4f}")

    with open(out_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {len(rows)} rows -> {out_csv}")


if __name__ == "__main__":
    main()
