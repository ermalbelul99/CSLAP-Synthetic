"""EXP-02c analysis: what does the community bound scale with?

Reads every capsweep shard and answers, in order:

A. Is the visit curve monotone in beta? If it is, beta has no interior optimum and
   the only thing that can define a "best" value is the workload cap. Everything
   below depends on this, so it is checked first rather than assumed.
B. Where is the feasibility frontier beta_max = max{beta : max_overload <= 1}?
C. Does beta_max scale with station capacity zeta (H1) or catalogue size N (H2)?
   The design crosses zeta in {20,25,50,100} with N in {500,1000}, so log zeta and
   log N are orthogonal and the regression

       log beta_max = a + b log zeta + c log N

   identifies both. H1 predicts b ~ 1, c ~ 0; H2 predicts b ~ 0, c ~ 1.
D. Do the beta levels differ at all, per cell? Friedman over the shared grid, then
   Holm-corrected Wilcoxon against the published nominal bound of 15.
E. Out-of-sample policy comparison. Policies are fitted on the TUNING half only
   (seeds 2001-2005) and scored on the TEST half (2006-2010):
       nominal    beta = 15                     the published rule
       capacity   beta = round(alpha_hat*zeta)  alpha_hat fitted on tuning
       catalogue  beta = beta_hat (absolute)    best fixed value on tuning
       oracle     beta = beta_max per instance  best in hindsight, not a policy
   Both fitted policies use the SAME criterion - the largest bound that keeps
   every tuning instance feasible - so the comparison isolates what the bound is
   indexed on, which is the question, and not how it was chosen.

Every visit figure is reported beside its feasibility. A beta that lowers visits
by breaking the workload cap is not an improvement, and ranking on visits alone
is the flaw this experiment exists to remove.

Usage
-----
cd CSLAP-Synthetic
python Baselines/analyze_capacity_sweep.py
python Baselines/analyze_capacity_sweep.py --out-dir capsweep_results
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

# Feasible means no station over its own time capacity.
_FEAS_TOL: float = 1.0
_NOMINAL_BETA: int = 15
_TUNING_SEEDS = frozenset(range(2001, 2006))


# --------------------------------------------------------------------------- #
#  LOAD                                                                       #
# --------------------------------------------------------------------------- #
def load(out_dir: str) -> pd.DataFrame:
    paths = sorted(glob.glob(os.path.join(out_dir, "capsweep_shard*.csv")))
    single = os.path.join(out_dir, "capsweep.csv")
    if os.path.exists(single):
        paths.append(single)
    if not paths:
        raise FileNotFoundError(f"no capsweep CSVs under {out_dir}")
    df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    for col in ("visits", "max_overload_ratio", "beta", "alpha", "zeta",
                "wl_broken", "cap_broken", "time_s"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["instance"] = (df["size_n"].astype(str) + "_s" + df["n_stations"].astype(str)
                      + "_seed" + df["instance_seed"].astype(str))
    return df


def main_frame(df: pd.DataFrame) -> pd.DataFrame:
    """The analysis frame: successful runs at the pinned tie-break seed."""
    keep = df[(df["status"] == "OK") & (df["hash_seed"] == 0)].copy()
    return keep.sort_values(["size_n", "n_stations", "instance_seed", "beta"])


# --------------------------------------------------------------------------- #
#  A. NOISE FLOOR + MONOTONICITY                                              #
# --------------------------------------------------------------------------- #
def noise_floor(df: pd.DataFrame) -> float:
    """Mean per-instance spread of visits across tie-break seeds, in percent."""
    rep = df[(df["status"] == "OK") & (df["beta"] == _NOMINAL_BETA)]
    spreads: List[float] = []
    for _inst, g in rep.groupby("instance"):
        vals = g["visits"].to_numpy(dtype=float)
        vals = vals[np.isfinite(vals)]
        if vals.size >= 2 and vals.mean() > 0:
            spreads.append(100.0 * float(np.std(vals, ddof=1)) / float(vals.mean()))
    return float(np.mean(spreads)) if spreads else float("nan")


def monotonicity(df: pd.DataFrame) -> Dict[str, float]:
    """How often visits fall as beta rises, and by how much end to end."""
    from scipy import stats
    rhos: List[float] = []
    n_mono = n_tot = 0
    end_to_end: List[float] = []
    for _inst, g in df.groupby("instance"):
        g = g.sort_values("beta")
        v = g["visits"].to_numpy(dtype=float)
        b = g["beta"].to_numpy(dtype=float)
        if v.size < 3 or not np.all(np.isfinite(v)):
            continue
        n_tot += 1
        # .statistic only exists on newer scipy; index 0 works on both.
        rhos.append(float(stats.spearmanr(b, v)[0]))
        if np.all(np.diff(v) <= 0):
            n_mono += 1
        end_to_end.append(100.0 * (v[-1] - v[0]) / v[0])
    return {
        "n_instances": n_tot,
        "frac_strictly_nonincreasing": n_mono / n_tot if n_tot else float("nan"),
        "mean_spearman_beta_vs_visits": float(np.mean(rhos)) if rhos else float("nan"),
        "mean_pct_visits_change_lowest_to_highest_beta": (
            float(np.mean(end_to_end)) if end_to_end else float("nan")),
    }


# --------------------------------------------------------------------------- #
#  B. FEASIBILITY FRONTIER                                                    #
# --------------------------------------------------------------------------- #
def frontier(df: pd.DataFrame) -> pd.DataFrame:
    """Per instance: the largest feasible beta, and whether feasibility is nested."""
    rows: List[Dict[str, object]] = []
    for inst, g in df.groupby("instance"):
        g = g.sort_values("beta")
        feas = g["max_overload_ratio"] <= _FEAS_TOL
        betas = g["beta"].to_numpy(dtype=float)
        n_feas = int(feas.sum())
        beta_max = float(betas[feas.to_numpy()].max()) if n_feas else float("nan")
        # Nested = every beta at or below the frontier is also feasible. If it is
        # not, "the largest feasible bound" is a weaker recommendation and the
        # write-up has to say so.
        nested = bool(np.all(feas.to_numpy()[betas <= beta_max])) if n_feas else False
        first = g.iloc[0]
        visits_at = dict(zip(g["beta"].astype(int), g["visits"]))
        rows.append({
            "instance": inst,
            "size_n": int(first["size_n"]), "n_stations": int(first["n_stations"]),
            "zeta": int(first["zeta"]), "instance_seed": int(first["instance_seed"]),
            "split": str(first["split"]),
            "beta_max": beta_max,
            "alpha_max": beta_max / float(first["zeta"]) if n_feas else float("nan"),
            "n_feasible_levels": n_feas, "n_levels": int(len(g)),
            "feasibility_nested": nested,
            "visits_at_beta_max": visits_at.get(int(beta_max), float("nan"))
            if n_feas else float("nan"),
            "visits_at_nominal": visits_at.get(_NOMINAL_BETA, float("nan")),
            "nominal_feasible": bool(
                (g.loc[g["beta"] == _NOMINAL_BETA, "max_overload_ratio"]
                 <= _FEAS_TOL).all())
            if (g["beta"] == _NOMINAL_BETA).any() else False,
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
#  C. H1 vs H2                                                                #
# --------------------------------------------------------------------------- #
def _ols(y: np.ndarray, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
    """(coefficients, standard errors, R^2) for y = X b, X including intercept."""
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = len(y) - X.shape[1]
    sigma2 = float(resid @ resid) / dof
    cov = sigma2 * np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - float(resid @ resid) / ss_tot if ss_tot > 0 else float("nan")
    return beta, se, r2


def scaling_test(fr: pd.DataFrame) -> Dict[str, object]:
    """Regress log beta_max on log zeta and log N; H1 => b~1,c~0, H2 => b~0,c~1.

    Only estimable where the frontier EXISTS. If most instances have no feasible
    beta at all, neither rule predicts anything and the honest answer is that the
    question does not arise - so the coverage is reported first and the verdict is
    withheld rather than read off a handful of surviving cells.
    """
    from scipy import stats
    d = fr.dropna(subset=["beta_max"])
    d = d[d["beta_max"] > 0]

    n_cells_total = fr.groupby(["size_n", "zeta"]).ngroups
    n_cells_with_frontier = d.groupby(["size_n", "zeta"]).ngroups if len(d) else 0
    coverage = len(d) / len(fr) if len(fr) else 0.0
    if len(d) < 20 or n_cells_with_frontier < 4:
        return {
            "estimable": False,
            "n": int(len(d)), "n_instances_total": int(len(fr)),
            "coverage": coverage,
            "n_cells_with_frontier": int(n_cells_with_frontier),
            "n_cells_total": int(n_cells_total),
            "verdict": ("NOT ESTIMABLE - the feasibility frontier does not exist "
                        "on most instances, so neither scaling rule has a quantity "
                        "to predict"),
            "cell_table": d.groupby(["size_n", "zeta"]).agg(
                beta_max=("beta_max", "mean"),
                alpha_max=("alpha_max", "mean")).reset_index() if len(d) else None,
        }
    y = np.log(d["beta_max"].to_numpy(dtype=float))
    lz = np.log(d["zeta"].to_numpy(dtype=float))
    ln = np.log(d["size_n"].to_numpy(dtype=float))
    X = np.column_stack([np.ones_like(y), lz, ln])
    coef, se, r2 = _ols(y, X)
    dof = len(y) - X.shape[1]
    tcrit = float(stats.t.ppf(0.975, dof))

    # Dispersion of each candidate invariant across the eight cells. The rule
    # whose quantity varies less across cells is the better-supported rule.
    cell = d.groupby(["size_n", "zeta"]).agg(
        beta_max=("beta_max", "mean"), alpha_max=("alpha_max", "mean")).reset_index()
    cv_alpha = float(cell["alpha_max"].std(ddof=1) / cell["alpha_max"].mean())
    cv_beta = float(cell["beta_max"].std(ddof=1) / cell["beta_max"].mean())
    return {
        "estimable": True,
        "coverage": coverage,
        "n_cells_with_frontier": int(n_cells_with_frontier),
        "n_cells_total": int(n_cells_total),
        "n": int(len(y)), "dof": dof, "r2": r2,
        "b_log_zeta": float(coef[1]),
        "b_log_zeta_ci": (float(coef[1] - tcrit * se[1]), float(coef[1] + tcrit * se[1])),
        "c_log_N": float(coef[2]),
        "c_log_N_ci": (float(coef[2] - tcrit * se[2]), float(coef[2] + tcrit * se[2])),
        "cv_alpha_max_across_cells": cv_alpha,
        "cv_beta_max_across_cells": cv_beta,
        "verdict": ("H1 (capacity rule)" if cv_alpha < cv_beta else "H2 (catalogue rule)"),
        "cell_table": cell,
    }


# --------------------------------------------------------------------------- #
#  D. PER-CELL SIGNIFICANCE                                                   #
# --------------------------------------------------------------------------- #
def per_cell_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Friedman over beta within each cell, then Holm-corrected Wilcoxon vs 15."""
    from scipy import stats
    rows: List[Dict[str, object]] = []
    for (size_n, n_stations), g in df.groupby(["size_n", "n_stations"]):
        wide = g.pivot_table(index="instance", columns="beta", values="visits")
        wide = wide.dropna(axis=0, how="any")
        if wide.shape[0] < 3 or wide.shape[1] < 3:
            continue
        fried_p = float(stats.friedmanchisquare(
            *[wide[c].to_numpy() for c in wide.columns])[1])
        if _NOMINAL_BETA not in wide.columns:
            continue
        ref = wide[_NOMINAL_BETA].to_numpy(dtype=float)
        raw: List[Tuple[float, float]] = []
        others = [c for c in wide.columns if c != _NOMINAL_BETA]
        for c in others:
            arr = wide[c].to_numpy(dtype=float)
            if np.allclose(arr, ref):
                raw.append((c, 1.0))
            else:
                raw.append((c, float(stats.wilcoxon(arr, ref)[1])))
        # Holm step-down across the comparisons made inside this cell.
        order = np.argsort([p for _c, p in raw])
        m = len(raw)
        holm: Dict[float, float] = {}
        running = 0.0
        for rank, idx in enumerate(order):
            c, p = raw[idx]
            running = max(running, (m - rank) * p)
            holm[c] = min(1.0, running)
        for c in others:
            sub = g[g["beta"] == c]
            rows.append({
                "size_n": size_n, "n_stations": n_stations,
                "zeta": int(g["zeta"].iloc[0]),
                "beta": int(c), "alpha": float(c) / float(g["zeta"].iloc[0]),
                "n_instances": int(wide.shape[0]),
                "friedman_p": fried_p,
                "mean_pct_delta_vs_nominal": float(
                    100.0 * np.mean((wide[c].to_numpy() - ref) / ref)),
                "wilcoxon_p_holm": holm[c],
                "mean_overload": float(sub["max_overload_ratio"].mean()),
                "frac_feasible": float((sub["max_overload_ratio"] <= _FEAS_TOL).mean()),
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
#  E. POLICIES                                                                #
# --------------------------------------------------------------------------- #
def _largest_all_feasible(df_tune: pd.DataFrame, key) -> float:
    """Largest value of `key(row)` at which EVERY tuning instance stays feasible.

    `key` maps a run row to the policy's index value (an absolute beta, or an
    alpha). Returns NaN when no value keeps every tuning instance feasible.
    """
    d = df_tune.copy()
    d["_k"] = key(d)
    ok: List[float] = []
    n_inst = d["instance"].nunique()
    for k, g in d.groupby("_k"):
        # A candidate only counts when it is actually exercised on every instance.
        if g["instance"].nunique() != n_inst:
            continue
        if bool((g["max_overload_ratio"] <= _FEAS_TOL).all()):
            ok.append(float(k))
    return max(ok) if ok else float("nan")


def fit_policies(df: pd.DataFrame) -> Dict[str, float]:
    """Fit alpha_hat and beta_hat on the TUNING half only."""
    tune = df[df["split"] == "tuning"]
    alpha_hat = _largest_all_feasible(tune, lambda d: d["alpha"].round(4))
    beta_hat = _largest_all_feasible(tune, lambda d: d["beta"])
    return {"alpha_hat": alpha_hat, "beta_hat": beta_hat}


def score_policies(df: pd.DataFrame, fitted: Dict[str, float],
                   fr: pd.DataFrame) -> pd.DataFrame:
    """Score every policy on the TEST half, visits AND feasibility together."""
    test = df[df["split"] == "test"]
    fr_test = fr[fr["split"] == "test"].set_index("instance")
    grids = {inst: sorted(g["beta"].astype(int).tolist())
             for inst, g in test.groupby("instance")}

    def pick(inst: str, want: float) -> Optional[int]:
        """Largest grid level at or below `want` (a policy can only use the grid)."""
        cand = [b for b in grids[inst] if b <= want]
        return max(cand) if cand else (min(grids[inst]) if grids[inst] else None)

    policies: Dict[str, Dict[str, Optional[int]]] = {
        "nominal (beta=15)": {},
        f"capacity (beta=round({fitted['alpha_hat']:.3g}*zeta))": {},
        f"catalogue (beta={fitted['beta_hat']:.0f})": {},
        "oracle (per-instance beta_max)": {},
    }
    names = list(policies)
    for inst, g in test.groupby("instance"):
        zeta = float(g["zeta"].iloc[0])
        policies[names[0]][inst] = pick(inst, _NOMINAL_BETA)
        policies[names[1]][inst] = pick(inst, round(fitted["alpha_hat"] * zeta)) \
            if np.isfinite(fitted["alpha_hat"]) else None
        policies[names[2]][inst] = pick(inst, fitted["beta_hat"]) \
            if np.isfinite(fitted["beta_hat"]) else None
        bm = fr_test["beta_max"].get(inst, float("nan"))
        policies[names[3]][inst] = int(bm) if np.isfinite(bm) else None

    lookup = test.set_index(["instance", "beta"])
    oracle_visits = {inst: fr_test["visits_at_beta_max"].get(inst, float("nan"))
                     for inst in grids}

    rows: List[Dict[str, object]] = []
    for name, choice in policies.items():
        visits, feas, excess, betas = [], [], [], []
        for inst, b in choice.items():
            if b is None:
                continue
            try:
                row = lookup.loc[(inst, float(b))]
            except KeyError:
                continue
            v = float(row["visits"])
            visits.append(v)
            feas.append(float(row["max_overload_ratio"]) <= _FEAS_TOL)
            betas.append(b)
            ov = oracle_visits.get(inst, float("nan"))
            if np.isfinite(ov) and ov > 0:
                excess.append(100.0 * (v - ov) / ov)
        rows.append({
            "policy": name,
            "n_instances": len(visits),
            "mean_beta": float(np.mean(betas)) if betas else float("nan"),
            "mean_visits": float(np.mean(visits)) if visits else float("nan"),
            "frac_feasible": float(np.mean(feas)) if feas else float("nan"),
            "mean_pct_excess_vs_oracle": float(np.mean(excess)) if excess else float("nan"),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
#  LATEX EMISSION                                                             #
# --------------------------------------------------------------------------- #
def emit_latex(df: pd.DataFrame, fr: pd.DataFrame, floor: pd.DataFrame,
               path: str) -> None:
    """Write the appendix table straight from the measurements.

    One row per warehouse geometry. Visits are reported as the paired change from
    the smallest bound to the largest, and feasibility as the overload of the
    LEAST overloaded setting available, so the table answers "how much can beta
    buy" and "can any beta be afforded" side by side.
    """
    lines: List[str] = []
    for (size_n, n_stations, zeta), g in df.groupby(["size_n", "n_stations", "zeta"]):
        betas = sorted(g["beta"].unique())
        lo, hi = betas[0], betas[-1]
        wide = g.pivot_table(index="instance", columns="beta", values="visits")
        wide = wide.dropna(axis=0, how="any")
        d_lo_hi = float(100.0 * np.mean(
            (wide[hi].to_numpy() - wide[lo].to_numpy()) / wide[lo].to_numpy()))
        ov = g.groupby("beta")["max_overload_ratio"].mean()
        fl = floor[(floor["size_n"] == size_n) & (floor["zeta"] == zeta)]
        ov_floor = float(fl["overload_floor"].iloc[0]) if len(fl) else float("nan")
        n_feas = int((g["max_overload_ratio"] <= _FEAS_TOL).sum())
        lines.append(
            f"{size_n:,} & {n_stations} & {zeta} & {int(lo)}--{int(hi)} & "
            f"${d_lo_hi:+.1f}$\\% & {ov_floor:.2f} & {ov[hi]:.2f} & "
            f"{n_feas}/{len(g)} \\\\"
        )

    body = "\n".join(lines)
    tex = f"""% Generated by Baselines/analyze_capacity_sweep.py -- do not edit by hand.
\\begin{{table}}[H]
\\centering
\\tbl{{Community bound across warehouse geometries: 80 instances, ten per cell,
with the bound $\\beta$ swept from 2 to the station slot capacity $\\zeta$. The
visit column is the mean paired change from the smallest bound to the largest, so
a negative value means the largest bound saves visits. Overload is the busiest
station's load as a multiple of its own time capacity; a value above 1 is a
breach. The floor column is the least overloaded setting available anywhere in
the sweep.}}
{{\\small\\setlength{{\\tabcolsep}}{{4pt}}\\begin{{tabular}}{{@{{}}rrrccccc@{{}}}}
\\toprule
$N$ & $|S|$ & $\\zeta$ & $\\beta$ range & $\\Delta$ visits & Overload floor &
Overload at $\\beta=\\zeta$ & Feasible runs \\\\
\\midrule
{body}
\\bottomrule
\\end{{tabular}}}}
\\tabnote{{The overload floor is attained at the smallest bound in every cell, at
which the clustering is effectively switched off, and it still exceeds 1
everywhere. No setting of the bound makes the layout feasible on six of the eight
geometries, and the two exceptions are the widest-station cells.}}
\\label{{tab:capsweep}}
\\end{{table}}
"""
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(tex)
    print(f"[out] LaTeX table -> {path}")


# --------------------------------------------------------------------------- #
#  REPORT                                                                     #
# --------------------------------------------------------------------------- #
def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description="EXP-02c analysis.")
    p.add_argument("--out-dir", type=str, default="capsweep_results")
    args = p.parse_args(argv)

    raw = load(args.out_dir)
    df = main_frame(raw)
    print(f"[load] {len(raw)} rows, {len(df)} OK rows at hash_seed=0, "
          f"{df['instance'].nunique()} instances")
    bad = raw[raw["status"] != "OK"]
    if len(bad):
        print(f"[warn] {len(bad)} non-OK rows: "
              f"{bad['status'].value_counts().to_dict()}")

    nf = noise_floor(raw)
    print(f"\n=== A. tie-break noise floor === {nf:.3f}% of visits")
    mono = monotonicity(df)
    print("=== A. monotonicity of visits in beta ===")
    for k, v in mono.items():
        print(f"  {k}: {v}")

    fr = frontier(df)
    print("\n=== B. feasibility frontier (mean per cell) ===")
    cellb = fr.groupby(["size_n", "n_stations", "zeta"]).agg(
        n=("instance", "count"),
        beta_max=("beta_max", "mean"), alpha_max=("alpha_max", "mean"),
        nested=("feasibility_nested", "mean"),
        nominal_feasible=("nominal_feasible", "mean")).reset_index()
    print(cellb.to_string(index=False))

    # The overload FLOOR: the least overloaded setting available in each cell. If
    # the floor is already above 1, no clustering threshold can make the layout
    # feasible, and the overload is coming from somewhere other than beta.
    print("\n=== B2. overload floor per cell (min over beta of the mean overload) ===")
    ov = (df.groupby(["size_n", "zeta", "beta"])["max_overload_ratio"].mean()
          .reset_index())
    floor = (ov.loc[ov.groupby(["size_n", "zeta"])["max_overload_ratio"].idxmin()]
             .rename(columns={"beta": "argmin_beta",
                              "max_overload_ratio": "overload_floor"}))
    floor["any_feasible_setting"] = floor["overload_floor"] <= _FEAS_TOL
    print(floor.to_string(index=False))

    st = scaling_test(fr)
    print("\n=== C. what does the frontier scale with? ===")
    print(f"  frontier exists on {st['n']}/{st['n_instances_total']} instances "
          f"({100 * st['coverage']:.1f}%), in {st['n_cells_with_frontier']} of "
          f"{st['n_cells_total']} cells")
    if not st.get("estimable", False):
        print(f"  VERDICT: {st['verdict']}")
    else:
        print(f"  log beta_max = a + b*log(zeta) + c*log(N),  n={st['n']}, "
              f"R2={st['r2']:.3f}")
        print(f"  b (log zeta) = {st['b_log_zeta']:+.3f}  95% CI "
              f"[{st['b_log_zeta_ci'][0]:+.3f}, {st['b_log_zeta_ci'][1]:+.3f}]   "
              f"(H1 predicts 1, H2 predicts 0)")
        print(f"  c (log N)    = {st['c_log_N']:+.3f}  95% CI "
              f"[{st['c_log_N_ci'][0]:+.3f}, {st['c_log_N_ci'][1]:+.3f}]   "
              f"(H1 predicts 0, H2 predicts 1)")
        print(f"  CV across cells: alpha_max {st['cv_alpha_max_across_cells']:.3f} vs "
              f"beta_max {st['cv_beta_max_across_cells']:.3f}")
        print(f"  VERDICT: {st['verdict']}")

    tests = per_cell_tests(df)
    print("\n=== D. per-cell tests vs nominal beta=15 ===")
    if len(tests):
        print(tests.to_string(index=False))

    fitted = fit_policies(df)
    print(f"\n=== E. policies fitted on the tuning half ===\n  {fitted}")
    scores = score_policies(df, fitted, fr)
    print("\n=== E. scored on the held-out test half ===")
    print(scores.to_string(index=False))

    emit_latex(df, fr, floor, os.path.join(args.out_dir, "capsweep_table.tex"))

    fr.to_csv(os.path.join(args.out_dir, "capsweep_frontier.csv"), index=False)
    cellb.to_csv(os.path.join(args.out_dir, "capsweep_cells.csv"), index=False)
    tests.to_csv(os.path.join(args.out_dir, "capsweep_tests.csv"), index=False)
    scores.to_csv(os.path.join(args.out_dir, "capsweep_policies.csv"), index=False)
    print(f"\n[out] wrote frontier / cells / tests / policies CSVs to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
