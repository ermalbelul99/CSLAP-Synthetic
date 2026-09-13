r"""Volume-normalised per-station share contract for the daily workload row.

THE CONTRACT
------------

For every station :math:`s` and every day :math:`d`:

.. math::

   W_s(d) \;\le\; \bigl(\mu_s + z\,\sigma_s\bigr)\, L(d)

where :math:`W_s(d)` is the pick-lines handled by station *s* on day *d*,
:math:`L(d)` is the warehouse-wide total that day, and :math:`\mu_s`,
:math:`\sigma_s` are the mean and standard deviation of station *s*'s **share**
of the daily lines, fitted on TRAINING days under the incumbent layout.

Why a share band rather than a fixed ceiling
--------------------------------------------

The previous rule set :math:`T_s` to the station's own busiest observed day.
That is circular (the incumbent then satisfies it by algebra) and it leaves
*zero* slack at every station by construction: on its peak day a station sits
exactly on its ceiling. The only aggregate room (3-7% on this site) is the
accident of peaks not coinciding, and a Bertsimas-Sim budget of
:math:`\Gamma = 1` already consumes ~110% of it. A revealed-peak ceiling spends
the entire budget before robustness is asked for.

Because both sides here scale with :math:`L(d)`, warehouse-wide (common)
demand drift is absorbed structurally, leaving :math:`\Gamma` to insure the
idiosyncratic part -- the only form under which assumption A4 can hold.

Units
-----

Everything is in LINES. The station speed :math:`V_s` cancels: the old ceiling
was itself derived as *(observed lines)/V_s* while the load was divided by the
same :math:`V_s`. Staying in lines removes a 1677x spread in :math:`V_s` from
the arithmetic and is far better conditioned.

Population
----------

Shares are computed over the FREE products only -- the ones the model may move
(2,000 of 21,874 here). This matches ``station_daily_loads.csv``, which
``daily_folds.py`` also builds free-only when frozen products exist, so both
sides of the row describe the same population. Note the consequence: balancing
the free products does not by itself balance a station's *total* load. It is
:math:`\mu_s` that carries the frozen load implicitly, since it is measured
from how the client actually distributes free products given their fixed
holdings.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np

__all__ = [
    "fit_share_band", "allowance_lines", "tighten", "evaluate_layout",
    "onehot_from_assignment", "check_identities",
]


def onehot_from_assignment(assignment: Dict[str, str],
                           products: List[str],
                           station_ids: List[str]) -> np.ndarray:
    """``(n_products, n_stations)`` 0/1 matrix, one 1 per row.

    Raises when a product has no resolvable home: a silently unplaced product
    would understate every station's load and make a layout look feasible.
    """
    s_idx = {str(s): i for i, s in enumerate(station_ids)}
    oh = np.zeros((len(products), len(station_ids)), dtype=float)
    missing = 0
    for i, p in enumerate(products):
        j = s_idx.get(str(assignment.get(p, "")))
        if j is None:
            missing += 1
            continue
        oh[i, j] = 1.0
    if missing:
        raise ValueError(
            f"{missing} of {len(products)} products have no station in the "
            f"assignment; every product must have a home (A5)")
    return oh


def fit_share_band(daily_lines: np.ndarray,
                   onehot: np.ndarray) -> Tuple[np.ndarray, np.ndarray,
                                                np.ndarray]:
    """Fit the share band on training days.

    Args:
        daily_lines: ``(n_days, n_products)`` realised training lines.
        onehot: ``(n_products, n_stations)`` incumbent layout.

    Returns:
        ``(mu, sigma, shares)``. ``shares`` is ``(n_days, n_stations)`` and each
        of its rows sums to 1 by construction.
    """
    if daily_lines.ndim != 2 or onehot.ndim != 2:
        raise ValueError("daily_lines and onehot must both be 2-D")
    if daily_lines.shape[1] != onehot.shape[0]:
        raise ValueError(
            f"product axis mismatch: daily_lines has {daily_lines.shape[1]} "
            f"columns but onehot has {onehot.shape[0]} rows")
    totals = daily_lines.sum(axis=1)
    if not np.all(totals > 0):
        raise ValueError("a training day has zero lines; cannot form shares")
    if daily_lines.shape[0] < 2:
        raise ValueError("need >= 2 training days to estimate sigma")
    shares = (daily_lines @ onehot) / totals[:, None]
    return shares.mean(axis=0), shares.std(axis=0, ddof=1), shares


def allowance_lines(mu: np.ndarray, sigma: np.ndarray, z: float,
                    day_totals: np.ndarray,
                    beta: float = 1.0) -> np.ndarray:
    """Right-hand side of the workload row, in LINES.

    Args:
        day_totals: ``L(d)`` for each day being constrained.
        beta: optional uniform tightening; the band is divided by it, so
            ``beta = 1.02`` makes every allowance 2% smaller.

    Returns:
        ``(n_days, n_stations)`` matrix of line allowances.
    """
    if z < 0:
        raise ValueError("z must be non-negative")
    if beta <= 0:
        raise ValueError("beta must be positive")
    band = (mu + z * sigma) / float(beta)
    return np.outer(np.asarray(day_totals, dtype=float), band)


def tighten(mu: np.ndarray, sigma: np.ndarray, z: float,
            beta: float) -> np.ndarray:
    """The tightened band itself, for reporting: ``(mu + z*sigma)/beta``.

    This replaces the previous beta arm, which rebuilt a single flat ceiling
    from ``stations[0]["SPEED"]`` for every station -- a homogeneous-speed
    formula applied to a site whose speeds span 1677x, producing a flat 13
    against revealed ceilings spanning 0.015 to 87. Here beta tightens exactly
    the object Gamma protects, so the two are finally comparable and A4 is
    testable.
    """
    return (mu + z * sigma) / float(beta)


def evaluate_layout(daily_lines: np.ndarray, onehot: np.ndarray,
                    mu: np.ndarray, sigma: np.ndarray, z: float,
                    beta: float = 1.0) -> dict:
    """Score a layout against the contract on the supplied days.

    ``mu`` and ``sigma`` stay FROZEN from training; only ``daily_lines``
    changes between the train and test call. The day totals are taken from the
    days being scored, which is legitimate: the contract grants a share of
    whatever volume arrives, and the layout cannot influence that volume.
    """
    rhs = allowance_lines(mu, sigma, z, daily_lines.sum(axis=1), beta)
    load = daily_lines @ onehot
    over = load > rhs + 1e-9
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(rhs > 0, load / rhs, 0.0)
    return {
        "n_days": int(load.shape[0]),
        "station_days_over": int(over.sum()),
        "days_violated": int(over.any(axis=1).sum()),
        "worst_ratio": float(ratio.max()) if ratio.size else 0.0,
        "mean_ratio": float(ratio.mean()) if ratio.size else 0.0,
        "worst_station": (int(np.unravel_index(np.argmax(ratio), ratio.shape)[1])
                          if ratio.size else -1),
    }


def check_identities(mu: np.ndarray, sigma: np.ndarray, z: float,
                     shares: Optional[np.ndarray] = None,
                     tol: float = 1e-9) -> None:
    """Assert the arithmetic the contract rests on. Raises on violation.

    1. ``sum(mu) == 1`` -- the shares are a complete carve-up of each day.
    2. ``sum(mu + z*sigma) == 1 + z*sum(sigma) > 1`` -- total permission always
       exceeds the day's work, so aggregate infeasibility (the failure that
       killed the quantile sweep) is impossible by construction.
    3. every ``sigma_s >= 0``.
    4. if ``shares`` is given, every day's shares sum to 1.
    """
    if abs(float(mu.sum()) - 1.0) > tol:
        raise AssertionError(f"sum(mu) = {mu.sum():.12f}, expected 1")
    if np.any(sigma < 0):
        raise AssertionError("negative sigma")
    total = float((mu + z * sigma).sum())
    identity = 1.0 + z * float(sigma.sum())
    if abs(total - identity) > tol:
        raise AssertionError(
            f"allowance sums to {total:.12f}, identity says {identity:.12f}")
    if total <= 1.0:
        raise AssertionError(
            f"total permission {total:.6f} does not exceed the day's work; "
            f"aggregate infeasibility would be possible")
    if shares is not None:
        err = float(np.abs(shares.sum(axis=1) - 1.0).max())
        if err > tol:
            raise AssertionError(f"a day's shares sum to {1 + err:.12f}")


if __name__ == "__main__":  # pragma: no cover - reproducible fold summary
    import argparse
    import os
    import sys

    import pandas as pd

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from milp_highs_robust import read_data

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", required=True, help="fold directory")
    ap.add_argument("--z", type=float, nargs="+", default=[3.0, 4.0, 6.0])
    a = ap.parse_args()

    tag = os.path.basename(a.dir.rstrip("/\\"))
    st = pd.read_csv(os.path.join(a.dir, tag + "_train_stations.csv"), sep=";")
    pr = pd.read_csv(os.path.join(a.dir, tag + "_train_products.csv"), sep=";")
    tro = pd.read_csv(os.path.join(a.dir, tag + "_train_orders.csv"), sep=";")
    teo = pd.read_csv(os.path.join(a.dir, tag + "_test_orders.csv"), sep=";")
    _o, _s, prods, _l = read_data(tag + "_train", a.dir)
    sids = [str(s) for s in st["STATION_ID"]]

    def mat(df):
        piv = (df.assign(_P=df["PRODUCT"].astype(str))
               .groupby(["DELIVERY_DATE", "_P"]).size().unstack(fill_value=0))
        return piv.reindex(columns=[str(p) for p in prods],
                           fill_value=0).to_numpy(float)

    warm = {f"PROD_{r.PRODUCT_ID}": str(r.WARM_STATION) for r in pr.itertuples()}
    oh = onehot_from_assignment(warm, prods, sids)
    Dtr, Dte = mat(tro), mat(teo)
    mu, sd, shares = fit_share_band(Dtr, oh)

    print(f"{tag}: {Dtr.shape[0]} train days, {Dte.shape[0]} test days, "
          f"{len(sids)} stations, {int(Dtr.sum())} free train lines")
    print(f"  sum(mu) = {mu.sum():.12f}   sum(sigma) = {sd.sum():.6f}")
    print(f"  busiest station mu = {mu.max():.4f} "
          f"({mu.max() * len(sids):.2f}x an even share); "
          f"quietest = {mu.min():.4f} ({mu.min() * len(sids):.2f}x)")
    zz = (shares.max(axis=0) - mu) / np.maximum(sd, 1e-12)
    print(f"  z the incumbent needs: worst station {zz.max():.2f}, "
          f"median {np.median(zz):.2f}")
    print()
    print(f"  {'z':>5} {'total permission':>18} {'train days viol':>16} "
          f"{'test days viol':>15}")
    for z in a.z:
        check_identities(mu, sd, z, shares)
        tr = evaluate_layout(Dtr, oh, mu, sd, z)
        te = evaluate_layout(Dte, oh, mu, sd, z)
        print(f"  {z:5.1f} {1 + z * sd.sum():17.3f}x "
              f"{tr['days_violated']:>9}/{tr['n_days']:<6} "
              f"{te['days_violated']:>8}/{te['n_days']:<6}")
