"""Controlled comparison: binary vs set-variable decisions, same machine.

Both columns come from Baselines/run_exp02a_binary_hexaly.py on this laptop, so
engine, constraints, objective encoding, LPT seed, budgets and hardware are all
held fixed. The only difference is how the decision is represented.
"""
import os

import pandas as pd
from scipy import stats

ROOT = ("c:/Users/ebelul/OneDrive - SAVOYE/Desktop/PhD_Work_2023-2026/CSLAP_Problem/"
        "Different_Solution_Approaches/Full_Package_Code_With_All_Approaches/CSLAP-Synthetic")
R = os.path.join(ROOT, "exp02a_results")

b = pd.read_csv(os.path.join(R, "exp02a_binary_hexaly.csv"))
s = pd.read_csv(os.path.join(R, "exp02a_setvar_hexaly_localmachine.csv"))
ref = pd.read_csv(os.path.join(ROOT, "exp02a_results_rerun", "exp02a_per_instance.csv"))

keep = ["size_n", "instance_seed", "visits", "wl_broken", "products_moved", "time_s"]
b = b[b.status == "OK"][keep].rename(columns={
    "visits": "binary", "wl_broken": "b_wl", "products_moved": "b_moved",
    "time_s": "b_time"})
s = s[s.status == "OK"][keep].rename(columns={
    "visits": "setvar", "wl_broken": "s_wl", "products_moved": "s_moved",
    "time_s": "s_time"})
m = b.merge(s, on=["size_n", "instance_seed"])
m["gap"] = 100.0 * (m.binary - m.setvar) / m.setvar

rows = []
for size, g in m.groupby("size_n"):
    d = g.binary.values - g.setvar.values
    try:
        p = stats.wilcoxon(g.binary, g.setvar, mode="exact").pvalue
    except ValueError:
        p = float("nan")
    rows.append({
        "N": size, "n": len(g),
        "binary": round(g.binary.mean(), 1),
        "setvar": round(g.setvar.mean(), 1),
        "gap_%": round(g.gap.mean(), 2),
        "bin_wins": int((d < 0).sum()),
        "ties": int((d == 0).sum()),
        "wilcoxon_p": (round(float(p), 4) if p == p else ""),
        "bin_wl_v": int((g.b_wl > 0).sum()),
        "set_wl_v": int((g.s_wl > 0).sum()),
        "bin_moved": int(g.b_moved.mean()),
        "set_moved": int(g.s_moved.mean()),
    })
out = pd.DataFrame(rows)
pd.set_option("display.width", 220)
print("=== CONTROLLED (both columns, this machine, identical harness) ===")
print(out.to_string(index=False))

d = m.binary.values - m.setvar.values
print(f"\npooled n={len(m)}  binary wins {int((d < 0).sum())}  "
      f"mean gap {m.gap.mean():+.2f}%  "
      f"wilcoxon p={stats.wilcoxon(m.binary, m.setvar, mode='exact').pvalue:.2e}")

# Did the 8-core control reproduce the 32-core reference for set-variable?
r = ref[(ref.status == "OK") & (ref.method == "Hexaly")][
    ["size_n", "instance_seed", "visits"]].rename(columns={"visits": "setvar_ref"})
c = s.merge(r, on=["size_n", "instance_seed"])
c["d"] = 100.0 * (c.setvar - c.setvar_ref) / c.setvar_ref
print("\n=== hardware check: set-variable, 8-core local vs 32-core reference ===")
print(c.groupby("size_n").agg(
    n=("d", "size"), local=("setvar", "mean"), reference=("setvar_ref", "mean"),
    mean_diff_pct=("d", "mean"), identical=("d", lambda x: int((x == 0).sum())),
).round(2).to_string())

out.to_csv(os.path.join(R, "exp02a_binary_vs_setvar_controlled.csv"), index=False)
m.to_csv(os.path.join(R, "exp02a_binary_vs_setvar_perinstance.csv"), index=False)
print("\nwrote exp02a_binary_vs_setvar_controlled.csv + _perinstance.csv")
