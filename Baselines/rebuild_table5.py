r"""
Rebuild Table 5 of IJPR_CSLAP_v2.tex from the 2026-07-29/30 re-run.

Sources (authoritative):
  exp02a_results_rerun/exp02a_per_instance.csv   Heuristic, SA-C, GA, Hexaly
  exp02a_results/exp02a_cg_setpart.csv           CG-SetPart, corrected budgets
  exp02a_results/exp02a_feasible_start.csv       LPT anchor (deterministic)

Emits, per (size, method): n, mean visits, 95% t-CI, mean PER-INSTANCE relative
gap to the Hexaly reference, the Table 5 time entry under the convention of
RERUN_IJPR_RESULTS.md section 1 (budget where the method reached it, measured
convergence time where it finished early), and the workload-violation rate.

Also emits paired tests (exact Wilcoxon signed-rank + paired t) for every method
against the Hexaly reference and for CG-SetPart against every baseline, per size
and pooled over all 29 instances.

Usage (env savoye2023, from the CSLAP-Synthetic root):
    python Baselines/rebuild_table5.py
Writes exp02a_results_rerun/table5_rebuilt.csv and table5_pairwise.csv.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
from scipy import stats

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

BUDGET = {50: 120, 500: 300, 1000: 600, 2000: 1200}
GA_PRIMARY_SEED = 20240612
REFERENCE = "Hexaly"
ORDER = ["Hexaly", "CG-SetPart", "Heuristic", "SA-C", "GA", "LPT start"]


def load_visits() -> pd.DataFrame:
    """One row per (size_n, instance_seed, method): visits, time_s, wl_broken."""
    runs = pd.read_csv(os.path.join(_ROOT, "exp02a_results_rerun",
                                    "exp02a_per_instance.csv"))
    runs = runs[runs["status"] == "OK"]
    # GA carries side-probe seeds at 50 SKUs; the table uses the primary seed.
    runs = runs[(runs["method"] != "GA") | (runs["solver_seed"] == GA_PRIMARY_SEED)]
    keep = ["size_n", "instance_seed", "method", "visits", "time_s", "wl_broken",
            "cap_broken"]
    runs = runs[keep]

    cg = pd.read_csv(os.path.join(_ROOT, "exp02a_results", "exp02a_cg_setpart.csv"))
    cg = cg[cg["status"] == "OK"]
    cg = cg[["size_n", "instance_seed", "visits", "time_s", "wl_broken", "cap_broken"]]
    cg["method"] = "CG-SetPart"

    lpt = pd.read_csv(os.path.join(_ROOT, "exp02a_results",
                                   "exp02a_feasible_start.csv"))
    lpt = lpt.rename(columns={"size": "size_n", "seed": "instance_seed"})
    lpt = lpt[["size_n", "instance_seed", "visits", "time_s", "wl_broken",
               "cap_broken"]]
    lpt["method"] = "LPT start"

    df = pd.concat([runs, cg[runs.columns], lpt[runs.columns]], ignore_index=True)
    df["visits"] = df["visits"].astype(float)
    return df


def t_ci(x: np.ndarray) -> tuple:
    """95% t confidence interval of the mean; (nan, nan) when n < 2."""
    n = len(x)
    if n < 2:
        return (np.nan, np.nan)
    m, se = float(np.mean(x)), stats.sem(x)
    h = se * stats.t.ppf(0.975, n - 1)
    return (m - h, m + h)


def time_entry(size: int, measured: float) -> tuple:
    """Table 5 time entry: budget if the method reached it, else measured."""
    budget = BUDGET[size]
    if measured >= budget * 0.98:
        return budget, "budget"
    return round(measured, 1), "measured"


def main() -> None:
    df = load_visits()
    wide = df.pivot_table(index=["size_n", "instance_seed"], columns="method",
                          values="visits")

    rows = []
    for size in sorted(df["size_n"].unique()):
        sub = wide.loc[size]
        ref = sub[REFERENCE]
        for method in ORDER:
            if method not in sub.columns:
                continue
            v = sub[method].dropna()
            if method == REFERENCE:
                gap = pd.Series([0.0])
            else:
                paired = sub[[method, REFERENCE]].dropna()
                gap = (100.0 * (paired[method] - paired[REFERENCE])
                       / paired[REFERENCE])
            m = df[(df["size_n"] == size) & (df["method"] == method)]
            lo, hi = t_ci(v.values)
            t_val, t_kind = time_entry(size, float(m["time_s"].mean()))
            rows.append({
                "size_n": size, "method": method, "n": len(v),
                "mean_visits": round(float(v.mean()), 1),
                "ci95_lo": round(lo, 1), "ci95_hi": round(hi, 1),
                "ci_informative": len(v) >= 5,
                "mean_gap_vs_ref_pct": round(float(gap.mean()), 2),
                "time_entry_s": t_val, "time_kind": t_kind,
                "time_measured_s": round(float(m["time_s"].mean()), 1),
                "wl_viol_frac": round(float((m["wl_broken"] > 0).mean()), 3),
                "cap_viol_frac": round(float((m["cap_broken"] > 0).mean()), 3),
            })
    out = pd.DataFrame(rows)
    out_path = os.path.join(_ROOT, "exp02a_results_rerun", "table5_rebuilt.csv")
    out.to_csv(out_path, index=False)

    # ---- paired tests -----------------------------------------------------
    pairs = [(m, REFERENCE) for m in ORDER if m != REFERENCE]
    pairs += [("CG-SetPart", b) for b in ["Heuristic", "SA-C", "GA", "LPT start"]]
    prows = []
    for size in list(sorted(df["size_n"].unique())) + ["pooled"]:
        sub = wide if size == "pooled" else wide.loc[[size]]
        for a, b in pairs:
            if a not in sub.columns or b not in sub.columns:
                continue
            p = sub[[a, b]].dropna()
            if len(p) < 2:
                continue
            d = p[a].values - p[b].values
            # Exact signed-rank test, as the manuscript states; zsplit handles
            # tied pairs, and the normal approximation is the last resort.
            try:
                w_p = stats.wilcoxon(p[a], p[b], mode="exact").pvalue
            except ValueError:
                try:
                    w_p = stats.wilcoxon(p[a], p[b], zero_method="zsplit").pvalue
                except ValueError:
                    w_p = np.nan
            t_p = stats.ttest_rel(p[a], p[b]).pvalue
            prows.append({
                "size_n": size, "method_a": a, "method_b": b, "n": len(p),
                "a_wins": int((d < 0).sum()), "ties": int((d == 0).sum()),
                "mean_gap_pct": round(float(100.0 * (d / p[b].values).mean()), 2),
                "wilcoxon_p": (round(float(w_p), 6) if np.isfinite(w_p) else ""),
                "paired_t_p": round(float(t_p), 6),
            })
    pw = pd.DataFrame(prows)
    pw_path = os.path.join(_ROOT, "exp02a_results_rerun", "table5_pairwise.csv")
    pw.to_csv(pw_path, index=False)

    pd.set_option("display.width", 200)
    print("=== TABLE 5 (rebuilt) ===")
    print(out.to_string(index=False))
    print("\n=== PAIRED TESTS ===")
    print(pw.to_string(index=False))
    print(f"\nwrote {out_path}\nwrote {pw_path}")


if __name__ == "__main__":
    main()
