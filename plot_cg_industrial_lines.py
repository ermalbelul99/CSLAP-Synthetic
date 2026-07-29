r"""Rebuild the two per-station line charts for the CG industrial layout,
mirroring the Hexaly figures (nb_code.py cells 48-64): lines per station
(Original vs Our Solution, ascending by Original) and relative change per
station. Verifies visually the ~0 utilization std claim."""
from __future__ import annotations
import json, os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, "..", "..", "..", "LaTeX_Articles_We_Have_Drafted", "Images_CSLAP")
CSV = os.path.join(BASE, "Heuristic_Connex_Set_Project", "data", "BERNER_ORDER_LINES_09-12.csv")

# --- plot universe: same as nb_code Cell 48 (only 01.Z8 excluded, GE4->E4) ---
df = pd.read_csv(CSV, sep=";")[["PRODUCT", "ORDER", "STATION"]].drop_duplicates().dropna()
uc = df.groupby("PRODUCT")["STATION"].nunique().reset_index(name="k")
df = df.merge(uc, on="PRODUCT", how="left")
multi = df[df["k"] > 1]["PRODUCT"].unique()
fix = (df[df["PRODUCT"].isin(multi)].sort_values("ORDER", ascending=False)
       .drop_duplicates("PRODUCT")[["PRODUCT", "STATION"]])
df = df.merge(fix, on="PRODUCT", how="left", suffixes=("", "_fx"))
df["STATION"] = df["STATION_fx"].where(df["STATION_fx"].notna(), df["STATION"])
df = df.drop(columns=["STATION_fx", "k"])
df = df[df["STATION"] != "01.Z8"]
df.loc[df["STATION"] == "01.GE4", "STATION"] = "01.E4"

# --- new assignment: CG JSON + static fixed + original for the rest ---------
# Default to the FAIR match-hexaly layout (the one reported in the paper,
# util-std 2.41); override with a path argument if needed.
_assign_file = sys.argv[1] if len(sys.argv) > 1 else \
    "industrial_cg_setpart_assignment_matchhexaly.json"
with open(os.path.join(BASE, _assign_file)) as fh:
    cg = json.load(fh)
sys.path.insert(0, BASE)
from data_loader_industrial import load_industrial_data
data = load_industrial_data(CSV)
newmap = dict(data["static_assignment"])
newmap.update(cg)  # CG decisions win for solver products
df["STATION_NEW"] = df["PRODUCT"].map(newmap)
df["STATION_NEW"] = df["STATION_NEW"].where(df["STATION_NEW"].notna(), df["STATION"])

orig = df.groupby("STATION").size()
new = df.groupby("STATION_NEW").size()
all_st = sorted(set(orig.index) | set(new.index))
tab = pd.DataFrame({"orig": orig.reindex(all_st).fillna(0),
                    "new": new.reindex(all_st).fillna(0)}).astype(int)
tab["rel"] = np.where(tab["orig"] > 0, 100.0 * (tab["new"] - tab["orig"]) / tab["orig"], 0.0)

# anonymize S_i in appearance order of the plot universe (as nb_code did)
order_seen = list(dict.fromkeys(df["STATION"]))
smap = {s: f"S_{i}" for i, s in enumerate(order_seen, start=1)}
tab["label"] = [smap.get(s, s) for s in tab.index]
tab = tab.sort_values("orig")

print(tab.to_string())
print(f"\nrel change: mean={tab.rel.mean():.3f}% std={tab.rel.std(ddof=0):.3f}% "
      f"min={tab.rel.min():.3f}% max={tab.rel.max():.3f}%")
print(f"total lines orig={tab.orig.sum()} new={tab.new.sum()}")

x = np.arange(len(tab)); wdt = 0.38
fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
ax.bar(x - wdt / 2, tab["orig"], wdt, label="Original", color="#6fa8d0")
ax.bar(x + wdt / 2, tab["new"], wdt, label="Our Solution", color="#f4b26a")
ax.set_xticks(x); ax.set_xticklabels(tab["label"], rotation=45)
ax.set_ylabel("Number of lines"); ax.set_xlabel("Station Name")
ax.set_title("Number of Lines per Station")
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(IMG, "CG_SetPart_number_of_lines_per_station.png"))

fig2, ax2 = plt.subplots(figsize=(14, 6), dpi=100)
ax2.bar(x, tab["rel"], 0.55, color="#4a90c4")
for xi, v in zip(x, tab["rel"]):
    ax2.annotate(f"{v:.1f}%", (xi, v), textcoords="offset points",
                 xytext=(0, 6 if v >= 0 else -14), ha="center", fontsize=9)
ax2.axhline(0, color="gray", lw=1)
ax2.set_ylim(-60, 60)
ax2.set_yticks(range(-60, 61, 20))
ax2.set_yticklabels([f"{t}%" for t in range(-60, 61, 20)])
ax2.grid(axis="y", ls="--", alpha=0.4)
ax2.set_xticks(x); ax2.set_xticklabels(tab["label"], rotation=45)
ax2.set_ylabel("Change in Lines (%)"); ax2.set_xlabel("Station Name")
ax2.set_title("Relative Change in Number of Lines per Station")
fig2.tight_layout()
fig2.savefig(os.path.join(IMG, "CG_SetPart_pt_relative_change_number_of_lines_per_station.png"))
print("saved both PNGs to Images_CSLAP/")
