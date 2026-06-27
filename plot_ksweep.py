"""Plot the limited-reassignment visits-vs-k trade-off curve from the k-sweep CSV."""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE, "results_reassignment_ksweep.csv"))

FULL_REDUCTION = 145042   # canonical 10h full-optimization reduction (1,062,507 -> 917,465)
TOTAL_CATALOG = 21877     # full SKU catalog (denominator used throughout the manuscript)

restr = df[df["k"] > 0].sort_values("k")
k = restr["k"].values
red = restr["reduction_vs_legacy"].values
pct_moved = 100.0 * k / TOTAL_CATALOG
pct_benefit = 100.0 * red / FULL_REDUCTION

fig, ax = plt.subplots(figsize=(7.0, 4.3))

ax.plot(pct_moved, red, "o-", color="#1f4e79", linewidth=2, markersize=7,
        label="Restricted MILP (1-hour budget)")
for xm, ym, kk in zip(pct_moved, red, k):
    ax.annotate(f"k={kk}", (xm, ym), textcoords="offset points", xytext=(6, -10), fontsize=9)

ax.axhline(FULL_REDUCTION, color="#a00000", linestyle="--", linewidth=1.6,
           label=f"Full re-optimization (~10h): {FULL_REDUCTION:,} visits")

ax.set_xlabel("Inventory relocated (% of catalog)", fontsize=12)
ax.set_ylabel("Station-visit reduction vs. legacy layout", fontsize=12)
ax.set_title("Limited-reassignment trade-off: benefit vs. relocation effort", fontsize=12)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=10, loc="center right")

# secondary axis: % of full benefit captured
secax = ax.secondary_yaxis("right", functions=(lambda y: 100*y/FULL_REDUCTION,
                                               lambda y: y*FULL_REDUCTION/100))
secax.set_ylabel("% of full-optimization benefit captured", fontsize=11)

fig.tight_layout()
out = os.path.join(BASE, "Images_CSLAP", "reassignment_ksweep_curve.png")
fig.savefig(out, dpi=200, bbox_inches="tight")
print("saved", out)
print(restr[["k", "pct_catalog_moved", "reduction_vs_legacy", "wl_broken"]].assign(
    pct_benefit=pct_benefit.round(2)).to_string(index=False))
