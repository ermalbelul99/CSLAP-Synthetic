"""EXP-02d: does beta* ~ 0.4-0.6 * zeta hold on the 29 PUBLISHED instances?

Why this exists
---------------
EXP-02c (``run_capacity_sweep.py``), re-run on the repaired B4ter heuristic,
found the community bound has an interior optimum that tracks the station slot
capacity zeta and not the catalogue size N:

    corr(beta*, zeta) = 0.947      corr(beta*, N) = -0.085
    beta* / zeta ~ 0.4 - 0.6 over zeta in {20, 25, 50, 100}, both N in {500, 1000}

That was measured on the EXP-02c instance family (seeds 2001-2010). The article's
own benchmark is a different family (seeds 1001-1012) and its geometry is fixed:
the generator sets |S| = max(5, N//100), so

    N =   50 -> |S| =  5 -> zeta =  10     beta/zeta = 1.50
    N =  500 -> |S| =  5 -> zeta = 100     beta/zeta = 0.15
    N = 1000 -> |S| = 10 -> zeta = 100     beta/zeta = 0.15
    N = 2000 -> |S| = 20 -> zeta = 100     beta/zeta = 0.15

Three of the four published blocks therefore sit at zeta = 100, where EXP-02c
puts beta* at 40 and measures -1.0% against the nominal beta = 15. Appendix C
already reports the same direction from a coarser grid (mnoppc x2 = 30 gives
-0.72% [-1.11, -0.34] at 500 SKUs, -0.75% at 1000, -1.14% at 2000), but it never
went above x2 and so never reached the optimum.

This runner closes that gap: it sweeps beta indexed on each instance's OWN zeta,
on the 29 published instances, and reports the paired change against the
published nominal setting.

Design
------
D0  Runs go through ``run_exp02a_sensitivity.run_one`` -- the same spawned-child
    path EXP-02a and EXP-02c use, with the same per-size wall-clock caps. Only
    ``mnoppc`` differs between configs; the other three thresholds stay at their
    published post-clamp base values, so any delta is attributable to beta alone.
D1  The `nominal` config re-runs the published setting. It is a REGRESSION GATE,
    not decoration: the repaired heuristic is deterministic, so nominal must
    reproduce ``exp02a_results_repaired/heuristic_benchmark.csv`` exactly. A
    mismatch means something in the chain moved and the sweep is void.
D2  beta is round(alpha * zeta) for alpha in --alphas, clamped to [2, zeta].
    Values that collide with each other or with nominal are de-duplicated per
    instance, so a cell never runs the same beta twice.
D3  zeta is read from the instance's own stations CSV (the CAPACITY column),
    not recomputed from N//|S|, so a non-uniform instance would be handled
    correctly if one is ever added.
D4  PYTHONHASHSEED is pinned by the caller. The repaired heuristic no longer
    depends on it (B4ter removed the set-iteration tie-breaks), but pinning
    keeps the run comparable with every cached campaign.

Usage
-----
    python Baselines/run_beta_zeta_confirm.py --dry-run
    python Baselines/run_beta_zeta_confirm.py
    python Baselines/run_beta_zeta_confirm.py --sizes 2000 --alphas 0.4
    python Baselines/run_beta_zeta_confirm.py --report      # re-aggregate only
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from run_exp02a_sensitivity import base_params, run_one, time_cap  # noqa: E402

_DEFAULT_ALPHAS = (0.3, 0.4, 0.5, 0.6)
_FIELDS = [
    "size_n", "instance_seed", "zeta", "config_id", "alpha", "beta",
    "visits", "time_s", "cap_broken", "wl_broken",
    "n_pstar", "n_pairs_kept", "n_corr_communities", "n_assigned",
    "community_size_max", "status",
]


def read_zeta(inst_dir: str, prefix: str) -> int:
    """Station slot capacity from the instance's own stations CSV (D3)."""
    path = os.path.join(inst_dir, f"{prefix}_stations.csv")
    st = pd.read_csv(path, sep=";")
    caps = st["CAPACITY"].astype(int)
    if caps.nunique() != 1:
        raise ValueError(
            f"{path}: non-uniform CAPACITY {sorted(caps.unique())}; this runner "
            "indexes beta on a single zeta per instance"
        )
    return int(caps.iloc[0])


def discover(instance_dir: str, sizes: Optional[Sequence[int]]) -> List[Dict[str, Any]]:
    """The 29 published instances, or the subset at `sizes`."""
    out: List[Dict[str, Any]] = []
    for name in sorted(os.listdir(instance_dir)):
        d = os.path.join(instance_dir, name)
        if not os.path.isdir(d) or not name.startswith("syn_"):
            continue
        # syn_<N>sku_seed<seed>
        try:
            size_n = int(name.split("sku")[0].removeprefix("syn_"))
            seed = int(name.rsplit("seed", 1)[1])
        except (ValueError, IndexError):
            continue
        if sizes and size_n not in sizes:
            continue
        prefix = f"syn_{size_n}sku"
        out.append({
            "inst_dir": d, "prefix": prefix, "size_n": size_n,
            "instance_seed": seed, "zeta": read_zeta(d, prefix),
        })
    return sorted(out, key=lambda r: (r["size_n"], r["instance_seed"]))


def legacy_beta(size_n: int) -> int:
    """The community bound as it was BEFORE this experiment changed it.

    Pinned locally on purpose. This runner is the evidence that moved the rule
    from N-indexed to zeta-indexed, so its `nominal` arm must keep meaning the
    old rule; importing it from `base_params` would make nominal follow the new
    rule and collapse the comparison this file exists to record.
    """
    return max(5, min(15, size_n // 20))


def beta_grid(size_n: int, zeta: int, alphas: Sequence[float]) -> List[Dict[str, Any]]:
    """nominal + one config per alpha, de-duplicated on the resulting beta (D2)."""
    nominal = legacy_beta(size_n)
    grid = [{"config_id": "nominal", "alpha": float("nan"), "beta": nominal}]
    seen = {nominal}
    for a in alphas:
        b = int(min(zeta, max(2, round(a * zeta))))
        if b in seen:
            continue
        seen.add(b)
        grid.append({"config_id": f"alpha{a:g}", "alpha": a, "beta": b})
    return grid


def already_done(path: str) -> set:
    if not os.path.isfile(path):
        return set()
    df = pd.read_csv(path)
    return set(zip(df.size_n, df.instance_seed, df.beta))


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--instance-dir", type=str, default="exp02a_instances")
    p.add_argument("--out-dir", type=str, default="exp02a_results_betazeta")
    p.add_argument("--sizes", nargs="+", type=int, default=None)
    p.add_argument("--alphas", nargs="+", type=float, default=list(_DEFAULT_ALPHAS))
    p.add_argument("--hash-seed", type=int, default=0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--report", action="store_true",
                   help="re-aggregate an existing run, execute nothing")
    args = p.parse_args(argv)

    out_dir = args.out_dir
    per_inst = os.path.join(out_dir, "beta_zeta_per_instance.csv")

    if args.report:
        return report(per_inst, out_dir)

    insts = discover(args.instance_dir, args.sizes)
    if not insts:
        print(f"no instances under {args.instance_dir}", file=sys.stderr)
        return 2

    plan = [(i, c) for i in insts for c in beta_grid(i["size_n"], i["zeta"], args.alphas)]

    print(f"{len(insts)} instances, {len(plan)} runs")
    by_size: Dict[int, Dict[str, Any]] = {}
    for i in insts:
        by_size.setdefault(i["size_n"], {"zeta": i["zeta"], "n": 0})["n"] += 1
    print(f"\n{'N':>6}{'n':>4}{'zeta':>6}{'cap s':>8}  betas")
    print("-" * 62)
    for n in sorted(by_size):
        z = by_size[n]["zeta"]
        betas = [c["beta"] for c in beta_grid(n, z, args.alphas)]
        print(f"{n:>6}{by_size[n]['n']:>4}{z:>6}{time_cap(n):>8.0f}  "
              f"{betas[0]} (nominal) + {betas[1:]}")
    print()

    if args.dry_run:
        return 0

    os.makedirs(out_dir, exist_ok=True)
    done = already_done(per_inst)
    if done:
        print(f"[resume] {len(done)} runs already recorded, skipping those\n")

    new = not os.path.isfile(per_inst)
    fh = open(per_inst, "a", newline="", encoding="utf-8")
    w = csv.DictWriter(fh, fieldnames=_FIELDS)
    if new:
        w.writeheader()

    try:
        for k, (inst, cfg) in enumerate(plan, 1):
            key = (inst["size_n"], inst["instance_seed"], cfg["beta"])
            if key in done:
                continue
            params = base_params(inst["size_n"], inst["zeta"])
            params["mnoppc"] = cfg["beta"]
            tag = (f"[{k}/{len(plan)}] N={inst['size_n']} seed={inst['instance_seed']} "
                   f"zeta={inst['zeta']} beta={cfg['beta']} ({cfg['config_id']})")
            print(tag, flush=True)
            status, metrics = run_one(
                inst["inst_dir"], inst["prefix"], params,
                time_cap(inst["size_n"]), args.hash_seed,
            )
            row = {f: None for f in _FIELDS}
            row.update({
                "size_n": inst["size_n"], "instance_seed": inst["instance_seed"],
                "zeta": inst["zeta"], "config_id": cfg["config_id"],
                "alpha": cfg["alpha"], "beta": cfg["beta"], "status": status,
            })
            for f in _FIELDS:
                if f in metrics:
                    row[f] = metrics[f]
            w.writerow(row)
            fh.flush()
            print(f"    -> {status} visits={row['visits']} wl={row['wl_broken']}",
                  flush=True)
    finally:
        fh.close()

    print(f"\n[done] -> {per_inst}")
    return report(per_inst, out_dir)


def report(per_inst: str, out_dir: str) -> int:
    """Paired change against the nominal setting, per size."""
    if not os.path.isfile(per_inst):
        print(f"no results at {per_inst}", file=sys.stderr)
        return 2
    df = pd.read_csv(per_inst)
    ok = df[df.status == "OK"]

    base = (ok[ok.config_id == "nominal"]
            .set_index(["size_n", "instance_seed"]).visits)
    rows = []
    for (n, cid), g in ok[ok.config_id != "nominal"].groupby(["size_n", "config_id"]):
        g = g.set_index(["size_n", "instance_seed"])
        common = base.index.intersection(g.index)
        if len(common) == 0:
            continue
        d = 100.0 * (g.visits[common] - base[common]) / base[common]
        K = len(d)
        mu = float(d.mean())
        if K > 1 and d.std(ddof=1) > 0:
            from scipy import stats
            hw = stats.t.ppf(0.975, K - 1) * d.std(ddof=1) / np.sqrt(K)
            lo, hi = mu - hw, mu + hw
            try:
                _, pval = stats.wilcoxon(d)
            except ValueError:
                pval = float("nan")
        else:
            lo = hi = pval = float("nan")
        rows.append({
            "size_n": n, "config_id": cid, "zeta": int(g.zeta.iloc[0]),
            "beta": int(g.beta.iloc[0]),
            "nominal_beta": legacy_beta(int(n)), "K": K,
            "mean_visits": float(g.visits[common].mean()),
            "nominal_visits": float(base[common].mean()),
            "mean_pct_delta": mu, "ci95_lo": lo, "ci95_hi": hi,
            "wilcoxon_p": pval,
            "ci_informative": bool(K >= 5),
            "frac_wl_broken": float((g.wl_broken[common] > 0).mean()),
        })

    agg = pd.DataFrame(rows).sort_values(["size_n", "beta"])
    agg_path = os.path.join(out_dir, "beta_zeta_agg.csv")
    agg.to_csv(agg_path, index=False)

    print("\n" + "=" * 92)
    print("beta indexed on zeta, vs the published nominal beta=15, on the 29 instances")
    print("=" * 92)
    print(f"{'N':>6}{'zeta':>6}{'beta':>6}{'K':>4}{'visits':>12}"
          f"{'nominal':>12}{'delta':>9}{'95% CI':>20}{'p':>8}")
    print("-" * 92)
    for _, r in agg.iterrows():
        ci = (f"[{r.ci95_lo:+.2f}, {r.ci95_hi:+.2f}]"
              if r.ci_informative and np.isfinite(r.ci95_lo) else "n too small")
        pv = f"{r.wilcoxon_p:.3f}" if np.isfinite(r.wilcoxon_p) else "  --"
        print(f"{int(r.size_n):>6}{int(r.zeta):>6}{int(r.beta):>6}{int(r.K):>4}"
              f"{r.mean_visits:>12,.0f}{r.nominal_visits:>12,.0f}"
              f"{r.mean_pct_delta:>+8.2f}%{ci:>20}{pv:>8}")
    print(f"\n[out] {agg_path}")
    print("\nNegative delta = fewer visits than the published setting.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
