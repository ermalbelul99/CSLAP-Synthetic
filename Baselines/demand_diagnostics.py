r"""Daily-demand diagnostics for the workload-feasibility robustness study.

Reproducible implementation of the calibration targets that ground the study
(Part 2 of the plan). It answers four questions about any dated order stream:

1. **How much of the daily volume swing is predictable?** Ordinary least squares
   of daily pick-lines on calendar dummies (day-of-week, week-of-month). The
   residual is the part a *robust* constraint has to absorb; the explained part
   should be forecast instead, not insured. This is the boundary between this
   study and the deterministic day-of-week storage assignment of Winkelmann et
   al. (arXiv:2209.03998).

2. **Is a spike day a common lift or a set of independent surges?** Each
   product's daily count is regressed on the common volume factor
   :math:`f_d = V_d / \bar V`. The median :math:`R^2` splits per-product
   variance into a *common* share (absorbed by the ceiling, or priced by a
   uniform tightening :math:`\beta`) and an *idiosyncratic* share -- the only
   part a Bertsimas--Sim budget :math:`\Gamma` actually models.

3. **How spiky is a single SKU?** The Fano factor
   :math:`\mathrm{Var}(L_{pd}) / \mathbb{E}[L_{pd}]` over days. Poisson counts
   give 1; anything above signals overdispersion, which is why the synthetic
   generator draws negative-binomial rather than Poisson daily counts.

4. **Do co-ordered products also co-spike?** The load-concentration mechanism of
   the whole study. Daily profiles are **volume-detrended first** (divided by
   :math:`f_d`) so the common factor cannot manufacture the correlation, then
   the Pearson correlation between order co-occurrence and co-spike correlation
   is reported. A positive value means the CSLAP visit objective, which
   co-locates co-ordered products, also concentrates spike risk onto one
   station.

The module is deliberately format-agnostic: it accepts the raw industrial export
and the generated synthetic instances alike, so the same code both measures the
real warehouse and verifies that the generator reproduced it.

No solver is used or imported.

CLI::

    python demand_diagnostics.py --orders <path> --out <dir> [--tag NAME]
        [--top-n 400] [--min-days 10]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from itertools import combinations
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import RESULTS  # noqa: E402

#: Column aliases accepted for each logical field, in priority order.
_ALIASES: Dict[str, Tuple[str, ...]] = {
    "PRODUCT": ("PRODUCT", "PRODUCT_ID", "SKU"),
    "ORDER": ("ORDER", "ORDER_ID"),
    "DATE": ("DELIVERY_DATE", "DATE", "ORDER_DATE", "PREPARATION_DATE"),
    "STATION": ("STATION", "STATION_ID"),
}


def _resolve(columns: List[str], field: str) -> Optional[str]:
    """Return the actual column name backing ``field``, or None if absent."""
    upper = {c.upper(): c for c in columns}
    for alias in _ALIASES[field]:
        if alias in upper:
            return upper[alias]
    return None


def load_order_table(path: str) -> pd.DataFrame:
    """Load a dated order table from either project format.

    Handles the comma-separated industrial export (with a leading index column)
    and the semicolon-separated generated instances, and normalises the column
    names to ``PRODUCT`` / ``ORDER`` / ``DATE`` / ``STATION``.

    Args:
        path: CSV path. Separator is sniffed between ``;`` and ``,``.

    Returns:
        Frame with a ``DATE`` column of dtype datetime64 and rows lacking a
        product, order or date dropped.

    Raises:
        ValueError: If a required column (PRODUCT, ORDER, DATE) is missing.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        head = fh.readline()
    sep = ";" if head.count(";") > head.count(",") else ","

    df = pd.read_csv(path, sep=sep, low_memory=False)
    cols = list(df.columns)

    resolved: Dict[str, Optional[str]] = {f: _resolve(cols, f) for f in _ALIASES}
    missing = [f for f in ("PRODUCT", "ORDER", "DATE") if resolved[f] is None]
    if missing:
        raise ValueError(
            f"{path}: missing required column(s) {missing}. "
            f"Found columns: {cols}. A dated order table is required -- an "
            f"undated instance cannot be diagnosed."
        )

    keep = {resolved[f]: f for f in _ALIASES if resolved[f] is not None}
    out = df[list(keep.keys())].rename(columns=keep)
    out["DATE"] = pd.to_datetime(out["DATE"], errors="coerce")
    out = out.dropna(subset=["PRODUCT", "ORDER", "DATE"])
    return out.reset_index(drop=True)


def daily_series(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to one row per calendar day.

    Args:
        df: Normalised order table.

    Returns:
        Frame indexed by date with ``lines`` (pick-lines) and ``orders``
        (distinct orders), sorted chronologically.
    """
    out = df.groupby("DATE").agg(lines=("PRODUCT", "size"),
                                 orders=("ORDER", "nunique"))
    return out.sort_index()


def _ols_r2(y: np.ndarray, design: np.ndarray) -> float:
    """R^2 of ``y`` on ``design`` (design must already carry an intercept)."""
    beta, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
    resid = y - design @ beta
    ss_tot = float(((y - y.mean()) ** 2).sum())
    if ss_tot <= 0:
        return 0.0
    return 1.0 - float((resid ** 2).sum()) / ss_tot


def variance_decomposition(daily: pd.DataFrame) -> Dict[str, object]:
    r"""Split daily volume variance into calendar structure and residual.

    Fits two nested OLS models on daily pick-lines: day-of-week alone, then
    day-of-week plus week-of-month. The residual of the larger model is the
    genuinely uncertain part -- the only part a robust budget should be asked to
    absorb (assumption A4).

    Args:
        daily: Output of :func:`daily_series`.

    Returns:
        Dict with ``r2_dow``, ``r2_calendar``, ``residual_share``,
        ``residual_cv``, ``dow_index`` and ``week_of_month_index``.
    """
    y = daily["lines"].to_numpy(dtype=float)
    idx = daily.index
    dow = idx.dayofweek.to_numpy()
    wom = ((idx.day - 1) // 7).to_numpy()
    n = len(y)
    mean = float(y.mean())

    ones = np.ones((n, 1))
    d_dow = pd.get_dummies(pd.Series(dow, dtype="category"),
                           drop_first=True).to_numpy(dtype=float)
    d_wom = pd.get_dummies(pd.Series(wom, dtype="category"),
                           drop_first=True).to_numpy(dtype=float)

    r2_dow = _ols_r2(y, np.hstack([ones, d_dow])) if d_dow.size else 0.0
    design_cal = np.hstack([ones] + [d for d in (d_dow, d_wom) if d.size])
    r2_cal = _ols_r2(y, design_cal)

    beta, _, _, _ = np.linalg.lstsq(design_cal, y, rcond=None)
    resid = y - design_cal @ beta

    dow_index = {int(k): float(v / mean)
                 for k, v in pd.Series(y, index=dow).groupby(level=0).mean().items()}
    wom_index = {int(k): float(v / mean)
                 for k, v in pd.Series(y, index=wom).groupby(level=0).mean().items()}

    return {
        "r2_dow": r2_dow,
        "r2_calendar": r2_cal,
        "residual_share": 1.0 - r2_cal,
        "residual_cv": float(resid.std() / mean) if mean else 0.0,
        "dow_index": dow_index,
        "week_of_month_index": wom_index,
    }


def station_peak_ratios(df: pd.DataFrame,
                        min_share: float = 0.001) -> Dict[str, object]:
    r"""Per-station busiest-day to mean-day ratio under the layout in the data.

    The ``STATION`` column of the industrial export is the *live* assignment, so
    this measures what the incumbent layout demonstrably sustained -- the
    evidence behind assumption A2 (revealed capacity).

    Args:
        df: Normalised order table; must carry ``STATION``.
        min_share: Stations holding a smaller share of all lines are dropped as
            non-operational (the industrial export contains two such stubs).

    Returns:
        Dict with the ratio quantiles, the retained station count, and the
        per-station realised daily load matrix as a nested dict.
    """
    if "STATION" not in df.columns:
        return {"available": False}

    total = len(df)
    share = df["STATION"].value_counts() / total
    main = share[share >= min_share].index
    sub = df[df["STATION"].isin(main)]

    piv = sub.groupby(["STATION", "DATE"]).size().unstack(fill_value=0)
    mean = piv.mean(axis=1)
    ratio = (piv.max(axis=1) / mean.replace(0, np.nan)).dropna()

    return {
        "available": True,
        "n_stations": int(piv.shape[0]),
        "n_dropped": int(len(share) - len(main)),
        "peak_over_mean_median": float(ratio.median()),
        "peak_over_mean_p90": float(ratio.quantile(0.90)),
        "peak_over_mean_max": float(ratio.max()),
    }


def sku_dispersion(df: pd.DataFrame, min_days: int = 10,
                   min_mean: float = 0.2) -> Dict[str, object]:
    r"""Per-SKU overdispersion and intermittency of daily demand.

    The Fano factor :math:`\mathrm{Var}/\mathbb{E}` equals 1 for Poisson counts.
    Values above 1 mean the SKU spikes harder than Poisson would allow, which is
    the empirical justification for drawing negative-binomial daily counts in
    the synthetic generator rather than Poisson.

    Args:
        df: Normalised order table.
        min_days: Minimum active days for a SKU to enter the intermittency stats.
        min_mean: Minimum mean daily lines for a SKU to enter the Fano stats.

    Returns:
        Dict of Fano quantiles, the share above 1.5, top-500 medians, and
        intermittency quantiles.
    """
    days = np.sort(df["DATE"].unique())
    n_days = len(days)
    counts = (df.groupby(["PRODUCT", "DATE"]).size()
                .unstack(fill_value=0)
                .reindex(columns=days, fill_value=0))

    mean = counts.mean(axis=1)
    var = counts.var(axis=1, ddof=1)
    active = (counts > 0).sum(axis=1) / n_days

    sel = mean > min_mean
    fano = (var[sel] / mean[sel]).replace([np.inf, -np.inf], np.nan).dropna()

    top = mean.sort_values(ascending=False).head(500).index
    fano_top = (var[top] / mean[top]).replace([np.inf, -np.inf], np.nan).dropna()

    act = active[(counts > 0).sum(axis=1) >= min_days]

    return {
        "n_skus": int(len(mean)),
        "n_skus_scored": int(sel.sum()),
        "fano_p25": float(fano.quantile(0.25)),
        "fano_median": float(fano.median()),
        "fano_p75": float(fano.quantile(0.75)),
        "fano_p90": float(fano.quantile(0.90)),
        "fano_share_above_1_5": float((fano > 1.5).mean()),
        "fano_median_top500": float(fano_top.median()),
        "active_days_median": float(act.median()) if len(act) else 0.0,
        "active_days_p25": float(act.quantile(0.25)) if len(act) else 0.0,
        "active_days_median_top500": float(active[top].median()),
    }


def _volume_head(df: pd.DataFrame, coverage: float,
                 cap: int) -> pd.Index:
    r"""SKUs covering the busiest ``coverage`` fraction of all pick-lines.

    A fixed "top 300" is not comparable across instances of different catalogue
    size -- it is the head of a 21,877-SKU warehouse but well into the tail of a
    2,000-SKU one, and the per-SKU daily counts (hence the Poisson sampling
    noise that dilutes any variance decomposition) differ by an order of
    magnitude. Selecting by volume coverage instead makes the statistic
    scale-free: it always describes the SKUs that carry the workload.

    Args:
        df: Normalised order table.
        coverage: Fraction of total pick-lines the head must cover.
        cap: Hard upper bound on the number of SKUs returned.

    Returns:
        Index of selected product identifiers.
    """
    counts = df["PRODUCT"].value_counts()
    keep = int((counts.cumsum() / counts.sum() <= coverage).sum()) + 1
    return counts.head(min(max(keep, 2), cap)).index


def common_vs_idiosyncratic(df: pd.DataFrame, daily: pd.DataFrame,
                            top_n: int = 300,
                            coverage: float = 0.5) -> Dict[str, object]:
    r"""Share of per-SKU daily variance explained by the common volume factor.

    Each SKU's daily count is regressed on :math:`f_d = V_d/\bar V`. A high
    :math:`R^2` means "the SKU is busy because *everything* is busy" -- a common
    lift that a budgeted constraint cannot represent (it would need the full
    Soyster box). The complement is the idiosyncratic share that :math:`\Gamma`
    is the right instrument for (assumption A4).

    Scored on the volume head (see :func:`_volume_head`) rather than a fixed SKU
    count, so the figure is comparable between the industrial catalogue and the
    much smaller synthetic ones.

    Args:
        df: Normalised order table.
        daily: Output of :func:`daily_series`.
        top_n: Hard cap on the number of SKUs scored.
        coverage: Fraction of pick-lines the scored head must cover.

    Returns:
        Dict with median/mean :math:`R^2`, the share above 0.5, and the implied
        common / idiosyncratic split.
    """
    top = _volume_head(df, coverage, top_n)
    sub = df[df["PRODUCT"].isin(top)]
    mat = (sub.groupby(["DATE", "PRODUCT"]).size().unstack(fill_value=0)
              .reindex(daily.index).fillna(0.0))

    factor = (daily["lines"] / daily["lines"].mean()).to_numpy(dtype=float)
    design = np.column_stack([np.ones(len(factor)), factor])

    r2 = [_ols_r2(mat[c].to_numpy(dtype=float), design)
          for c in mat.columns if mat[c].std() > 0]
    arr = np.asarray(r2, dtype=float)
    if arr.size == 0:
        return {"n_scored": 0}

    return {
        "n_head": int(len(top)),
        "n_scored": int(arr.size),
        "r2_common_median": float(np.median(arr)),
        "r2_common_mean": float(arr.mean()),
        "share_r2_above_0_5": float((arr > 0.5).mean()),
        "common_share": float(np.median(arr)),
        "idiosyncratic_share": float(1.0 - np.median(arr)),
    }


def cospike_vs_cooccurrence(df: pd.DataFrame, daily: pd.DataFrame,
                            top_n: int = 400) -> Dict[str, object]:
    r"""Do products ordered together also surge on the same day?

    The central mechanism of the study. Daily profiles are divided by the common
    volume factor **before** correlating, so a shared busy day cannot by itself
    produce a positive result. A positive Pearson correlation between pairwise
    order co-occurrence and pairwise co-spike correlation means the CSLAP visit
    objective -- which deliberately co-locates co-ordered products -- also
    concentrates spike risk onto individual stations.

    Args:
        df: Normalised order table.
        daily: Output of :func:`daily_series`.
        top_n: Number of highest-volume SKUs to include (pairs grow as n^2).

    Returns:
        Dict with the Pearson correlation, mean co-spike correlation split by
        whether the pair ever co-occurs, and the top-decile mean.
    """
    top = df["PRODUCT"].value_counts().head(top_n).index
    sub = df[df["PRODUCT"].isin(top)]

    mat = (sub.groupby(["DATE", "PRODUCT"]).size().unstack(fill_value=0)
              .reindex(daily.index).fillna(0.0))
    prods = list(mat.columns)
    idx = {p: i for i, p in enumerate(prods)}

    factor = (daily["lines"] / daily["lines"].mean()).to_numpy(dtype=float)
    detr = mat.to_numpy(dtype=float) / np.where(factor == 0, 1.0, factor)[:, None]
    sd = detr.std(axis=0)
    keep = sd > 0
    detr = (detr - detr.mean(axis=0)) / np.where(sd == 0, 1.0, sd)
    corr = np.corrcoef(detr.T)

    co = np.zeros((len(prods), len(prods)), dtype=float)
    for _oid, grp in sub.groupby("ORDER")["PRODUCT"]:
        members = sorted({idx[p] for p in grp})
        for a, b in combinations(members, 2):
            co[a, b] += 1.0
            co[b, a] += 1.0

    iu = np.triu_indices(len(prods), 1)
    valid = keep[iu[0]] & keep[iu[1]]
    co_v = co[iu][valid]
    cs_v = corr[iu][valid]
    ok = ~np.isnan(cs_v)
    co_v, cs_v = co_v[ok], cs_v[ok]
    if co_v.size == 0:
        return {"n_pairs": 0}

    paired = co_v > 0
    res: Dict[str, object] = {
        "n_pairs": int(co_v.size),
        "share_pairs_cooccurring": float(paired.mean()),
        "cospike_mean_cooccurring": float(cs_v[paired].mean()) if paired.any() else 0.0,
        "cospike_mean_never_together": float(cs_v[~paired].mean()) if (~paired).any() else 0.0,
        "pearson_cooccurrence_cospike": float(
            np.corrcoef(np.log1p(co_v), cs_v)[0, 1]),
    }
    if paired.any():
        cut = np.quantile(co_v[paired], 0.9)
        hi = co_v >= cut
        res["cospike_mean_top_decile"] = float(cs_v[hi].mean()) if hi.any() else 0.0

    # Lift controls for popularity. Raw co-occurrence is dominated by pairs that
    # are merely both popular, and the share of genuinely affine pairs in a
    # decile depends on how dense the affinity structure is -- which differs by
    # construction between a real catalogue and a Zhang-style instance, making
    # the raw-count decile incomparable across the two. Lift isolates affinity
    # and is comparable.
    n_orders = float(sub["ORDER"].nunique())
    freq = sub.groupby("PRODUCT")["ORDER"].nunique()
    fv = np.array([float(freq.get(p, 0.0)) for p in prods])
    expected = np.outer(fv, fv) / max(n_orders, 1.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        lift_full = np.where(expected > 0, co / expected, 0.0)
    lift_v = lift_full[iu][valid][ok]
    res["lift_mean"] = float(lift_v[paired].mean()) if paired.any() else 0.0
    res["pearson_lift_cospike"] = (
        float(np.corrcoef(np.log1p(lift_v), cs_v)[0, 1])
        if np.std(lift_v) > 0 else 0.0)
    if paired.any():
        lcut = np.quantile(lift_v[paired], 0.9)
        lhi = lift_v >= lcut
        res["cospike_mean_top_decile_lift"] = (
            float(cs_v[lhi].mean()) if lhi.any() else 0.0)
    return res


def run_diagnostics(orders_path: str, top_n: int = 400,
                    min_days: int = 10) -> Dict[str, object]:
    """Compute the full diagnostic bundle for one dated order table.

    Args:
        orders_path: CSV path (either project format).
        top_n: SKU count for the co-spike analysis.
        min_days: Minimum active days for the intermittency statistics.

    Returns:
        Nested dict with ``horizon``, ``volume``, ``variance``, ``stations``,
        ``sku``, ``factor`` and ``cospike`` sections.
    """
    df = load_order_table(orders_path)
    daily = daily_series(df)
    lines = daily["lines"]

    horizon = {
        "source": os.path.basename(orders_path),
        "rows": int(len(df)),
        "n_orders": int(df["ORDER"].nunique()),
        "n_skus": int(df["PRODUCT"].nunique()),
        "date_min": str(df["DATE"].min().date()),
        "date_max": str(df["DATE"].max().date()),
        "span_days": int((df["DATE"].max() - df["DATE"].min()).days + 1),
        "active_days": int(len(daily)),
    }
    volume = {
        "lines_per_day_mean": float(lines.mean()),
        "lines_per_day_sd": float(lines.std()),
        "lines_per_day_cv": float(lines.std() / lines.mean()) if lines.mean() else 0.0,
        "lines_per_day_max": int(lines.max()),
        "lines_per_day_min": int(lines.min()),
        "peak_over_mean": float(lines.max() / lines.mean()) if lines.mean() else 0.0,
        "peak_date": str(lines.idxmax().date()),
    }

    return {
        "horizon": horizon,
        "volume": volume,
        "variance": variance_decomposition(daily),
        "stations": station_peak_ratios(df),
        "sku": sku_dispersion(df, min_days=min_days),
        "factor": common_vs_idiosyncratic(df, daily, top_n=min(top_n, 300)),
        "cospike": cospike_vs_cooccurrence(df, daily, top_n=top_n),
    }


def _flatten(report: Dict[str, object]) -> pd.DataFrame:
    """Flatten the nested report to a two-column (metric, value) frame."""
    rows: List[Tuple[str, object]] = []
    for section, body in report.items():
        if not isinstance(body, dict):
            rows.append((section, body))
            continue
        for k, v in body.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    rows.append((f"{section}.{k}.{kk}", vv))
            else:
                rows.append((f"{section}.{k}", v))
    return pd.DataFrame(rows, columns=["metric", "value"])


def _print_summary(report: Dict[str, object]) -> None:
    """Print the headline calibration targets."""
    h, v = report["horizon"], report["volume"]
    var, sku = report["variance"], report["sku"]
    fac, cos, st = report["factor"], report["cospike"], report["stations"]

    print(f"  horizon            : {h['date_min']} -> {h['date_max']}  "
          f"({h['active_days']} active days, {h['n_skus']} SKUs)")
    print(f"  lines/day          : mean {v['lines_per_day_mean']:.0f}  "
          f"cv {v['lines_per_day_cv']:.2f}  peak/mean {v['peak_over_mean']:.2f}")
    if st.get("available"):
        print(f"  station peak/mean  : median {st['peak_over_mean_median']:.2f}  "
              f"p90 {st['peak_over_mean_p90']:.2f}  ({st['n_stations']} stations)")
    print(f"  variance dow       : {var['r2_dow']:.3f}")
    print(f"  variance calendar  : {var['r2_calendar']:.3f}   "
          f"residual {var['residual_share']:.3f} (cv {var['residual_cv']:.3f})")
    print(f"  common share       : {fac.get('common_share', float('nan')):.3f}   "
          f"idiosyncratic {fac.get('idiosyncratic_share', float('nan')):.3f}")
    print(f"  SKU Fano           : median {sku['fano_median']:.2f}   "
          f"top500 {sku['fano_median_top500']:.2f}")
    print(f"  co-spike Pearson   : {cos.get('pearson_cooccurrence_cospike', float('nan')):+.4f}"
          f"   top-decile {cos.get('cospike_mean_top_decile', float('nan')):+.4f}"
          f"   never {cos.get('cospike_mean_never_together', float('nan')):+.4f}")
    print(f"  co-spike by LIFT   : pearson {cos.get('pearson_lift_cospike', float('nan')):+.4f}"
          f"   top-decile {cos.get('cospike_mean_top_decile_lift', float('nan')):+.4f}"
          f"   (head n={fac.get('n_head', 0)})")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Daily-demand diagnostics for the workload robustness study")
    parser.add_argument("--orders", type=str, required=True,
                        help="Dated order table (industrial export or instance)")
    parser.add_argument("--out", type=str,
                        default=os.path.join(RESULTS, "diagnostics"))
    parser.add_argument("--tag", type=str, default=None,
                        help="Output basename (default: source file stem)")
    parser.add_argument("--top-n", type=int, default=400,
                        help="SKUs included in the co-spike analysis")
    parser.add_argument("--min-days", type=int, default=10)
    args = parser.parse_args()

    tag = args.tag or os.path.splitext(os.path.basename(args.orders))[0]
    print(f"[demand_diagnostics] {tag}: reading {args.orders}", flush=True)

    report = run_diagnostics(args.orders, top_n=args.top_n,
                             min_days=args.min_days)
    _print_summary(report)

    os.makedirs(args.out, exist_ok=True)
    json_path = os.path.join(args.out, f"diagnostics_{tag}.json")
    csv_path = os.path.join(args.out, f"diagnostics_{tag}.csv")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    _flatten(report).to_csv(csv_path, index=False)
    print(f"[demand_diagnostics] wrote {json_path}")
    print(f"[demand_diagnostics] wrote {csv_path}")


if __name__ == "__main__":
    main()
