"""Final analysis: binary vs set-variable, one harness, one machine.

Three questions:
  1. Controlled comparison on the article's machine, both models through the
     same harness at last.
  2. Harness effect: the same set-variable model through this harness versus
     through run_exp02a_multiseed.py, which produced Table 5.
  3. What that does to the column generation's reported margin.
"""
import os

import pandas as pd
from scipy import stats

os.chdir("c:/Users/ebelul/OneDrive - SAVOYE/Desktop/PhD_Work_2023-2026/CSLAP_Problem/"
         "Different_Solution_Approaches/Full_Package_Code_With_All_Approaches/CSLAP-Synthetic")
R = "exp02a_results"


def load(path, name):
    d = pd.read_csv(path)
    d = d[d.status == "OK"][["size_n", "instance_seed", "visits", "time_s", "wl_broken"]]
    return d.rename(columns={"visits": name, "time_s": f"{name}_t",
                             "wl_broken": f"{name}_wl"})


bin_s = load(f"{R}/exp02a_binary_hexaly_server16core.csv", "binary")
set_s = load(f"{R}/exp02a_setvar_hexaly_localmachine_server16core.csv", "setvar")

ref = pd.read_csv("exp02a_results_rerun/exp02a_per_instance.csv")
ref = ref[(ref.status == "OK") & (ref.method == "Hexaly")]
ref = ref[["size_n", "instance_seed", "visits", "time_s"]].rename(
    columns={"visits": "setvar_ms", "time_s": "setvar_ms_t"})

cg = pd.read_csv(f"{R}/exp02a_cg_setpart.csv")
cg = cg[cg.status == "OK"][["size_n", "instance_seed", "visits"]].rename(
    columns={"visits": "cg"})

m = bin_s.merge(set_s, on=["size_n", "instance_seed"]).merge(
    ref, on=["size_n", "instance_seed"]).merge(cg, on=["size_n", "instance_seed"])


def wilcox(a, b):
    try:
        return stats.wilcoxon(a, b, mode="exact").pvalue
    except ValueError:
        return float("nan")


print("=" * 78)
print("1. CONTROLLED: binary vs set-variable, same harness, article's machine")
print("=" * 78)
rows = []
for n, g in m.groupby("size_n"):
    d = g.binary.values - g.setvar.values
    gap = 100.0 * d / g.setvar.values
    rows.append({"N": n, "n": len(g),
                 "binary": round(g.binary.mean(), 1),
                 "setvar": round(g.setvar.mean(), 1),
                 "gap_%": round(gap.mean(), 2),
                 "bin_wins": int((d < 0).sum()), "ties": int((d == 0).sum()),
                 "p": round(wilcox(g.binary, g.setvar), 4),
                 "bin_t": round(g.binary_t.mean()), "set_t": round(g.setvar_t.mean())})
print(pd.DataFrame(rows).to_string(index=False))
d = m.binary.values - m.setvar.values
print(f"\npooled n={len(m)}  binary wins {int((d < 0).sum())}  "
      f"mean gap {(100.0 * d / m.setvar.values).mean():+.2f}%  "
      f"p={wilcox(m.binary, m.setvar):.4f}")

print()
print("=" * 78)
print("2. HARNESS EFFECT: same set-variable model, this harness vs multiseed")
print("=" * 78)
rows = []
for n, g in m.groupby("size_n"):
    d = g.setvar.values - g.setvar_ms.values
    gap = 100.0 * d / g.setvar_ms.values
    rows.append({"N": n, "n": len(g),
                 "this_harness": round(g.setvar.mean(), 1),
                 "multiseed(Table5)": round(g.setvar_ms.mean(), 1),
                 "diff_%": round(gap.mean(), 2),
                 "this_better": int((d < 0).sum()),
                 "p": round(wilcox(g.setvar, g.setvar_ms), 4),
                 "this_t": round(g.setvar_t.mean()), "ms_t": round(g.setvar_ms_t.mean())})
print(pd.DataFrame(rows).to_string(index=False))

print()
print("=" * 78)
print("3. CONSEQUENCE: CG's margin, measured against each set-variable column")
print("=" * 78)
rows = []
for n, g in m.groupby("size_n"):
    vs_ms = 100.0 * (g.cg.values - g.setvar_ms.values) / g.setvar_ms.values
    vs_th = 100.0 * (g.cg.values - g.setvar.values) / g.setvar.values
    rows.append({"N": n, "n": len(g), "cg": round(g.cg.mean(), 1),
                 "vs_multiseed_%": round(vs_ms.mean(), 2),
                 "cg_wins_ms": int((g.cg.values < g.setvar_ms.values).sum()),
                 "vs_this_harness_%": round(vs_th.mean(), 2),
                 "cg_wins_this": int((g.cg.values < g.setvar.values).sum()),
                 "p_vs_this": round(wilcox(g.cg, g.setvar), 4)})
print(pd.DataFrame(rows).to_string(index=False))
print("\n(paper reports CG at -2.0% (1000) and -5.9% (2000) against the multiseed column)")

m.to_csv(f"{R}/final_formulation_analysis_perinstance.csv", index=False)
print(f"\nwrote {R}/final_formulation_analysis_perinstance.csv")
