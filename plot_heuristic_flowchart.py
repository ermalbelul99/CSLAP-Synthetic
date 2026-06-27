"""Greedy clustering heuristic flowchart (CSLAP, Chapter 3 sec:cslap-heuristic).

Reproduces the four-phase logical flow of the heuristic (preprocessing ->
community-formation loop -> post-processing -> station-assignment loop) as a
self-contained PNG, faithful to the TikZ diagram in the C&OR manuscript
(Computers_and_Operations_Research_manuscript.tex, fig:heuristic_flowchart).
No LaTeX / TikZ dependency.
"""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon

OUT = os.path.join(
    r"c:\Users\ebelul\OneDrive - SAVOYE\Desktop\PhD_Work_2023-2026",
    "Thesis_Manuscript", "figures", "ch3", "heuristic_flowchart.png",
)

RED, BLUE, GREEN, EDGE = "#fde0e0", "#e0e8fb", "#e0f3e0", "#333333"


def box(ax, xy, w, h, text, fc, rounded=True):
    style = "round,pad=0.02,rounding_size=0.12" if rounded else "square,pad=0.02"
    p = FancyBboxPatch((xy[0] - w / 2, xy[1] - h / 2), w, h, boxstyle=style,
                       linewidth=1.2, edgecolor=EDGE, facecolor=fc, zorder=2)
    ax.add_patch(p)
    ax.text(xy[0], xy[1], text, ha="center", va="center", fontsize=8.5, zorder=3)


def diamond(ax, xy, w, h, text):
    x, y = xy
    pts = [(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)]
    ax.add_patch(Polygon(pts, closed=True, linewidth=1.2, edgecolor=EDGE,
                         facecolor=GREEN, zorder=2))
    ax.text(x, y, text, ha="center", va="center", fontsize=8.5, zorder=3)


def arrow(ax, p0, p1, label=None, lpos=None, rad=0.0):
    a = FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=12,
                        linewidth=1.2, color=EDGE,
                        connectionstyle=f"arc3,rad={rad}", zorder=1)
    ax.add_patch(a)
    if label:
        lx, ly = lpos if lpos else ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        ax.text(lx, ly, label, ha="center", va="center", fontsize=8,
                color=EDGE, zorder=4,
                bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none"))


def main() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 9.2))
    BW, BH = 4.6, 0.95          # box width/height
    DW, DH = 3.2, 1.25          # diamond width/height

    # node centres
    start  = (0, 9.5)
    pre    = (0, 8.0)
    init   = (0, 6.6)
    dec1   = (0, 5.1)
    form   = (4.4, 5.1)
    post   = (0, 3.5)
    rank   = (0, 2.1)
    dec2   = (0, 0.6)
    assign = (4.4, 0.6)
    end    = (0, -0.95)

    box(ax, start, BW, BH, "Input data ($P,O$) &\nDynamic thresholds", RED)
    box(ax, pre, BW, BH, "Step 1: Preprocessing\nFilter noise & generate valid pairs", BLUE, False)
    box(ax, init, BW, BH, r"Initialize community set $\mathcal{C}\leftarrow\emptyset$", BLUE, False)
    diamond(ax, dec1, DW, DH, "Candidate\npairs left?")
    box(ax, form, BW, BH, "Step 2: Community Formation\nGreedy expansion of top pair\nup to capacity MNOPPC", BLUE, False)
    box(ax, post, BW, BH, "Step 3: Post-Processing\nAssign residuals & low-freq SKUs", BLUE, False)
    box(ax, rank, BW, BH, "Rank communities by\ncumulative frequency", BLUE, False)
    diamond(ax, dec2, DW, DH, "Communities\nunassigned?")
    box(ax, assign, BW, BH, r"Step 4: Station Assignment""\n"r"Place/split by capacity $\zeta_s$", BLUE, False)
    box(ax, end, BW, BH, "Final physical\nstation assignment", RED)

    # straight downward arrows
    arrow(ax, (0, start[1] - BH / 2), (0, pre[1] + BH / 2))
    arrow(ax, (0, pre[1] - BH / 2), (0, init[1] + BH / 2))
    arrow(ax, (0, init[1] - BH / 2), (0, dec1[1] + DH / 2))
    arrow(ax, (0, dec1[1] - DH / 2), (0, post[1] + BH / 2), "No", (0.35, (dec1[1] - DH / 2 + post[1] + BH / 2) / 2))
    arrow(ax, (0, post[1] - BH / 2), (0, rank[1] + BH / 2))
    arrow(ax, (0, rank[1] - BH / 2), (0, dec2[1] + DH / 2))
    arrow(ax, (0, dec2[1] - DH / 2), (0, end[1] + BH / 2), "No", (0.35, (dec2[1] - DH / 2 + end[1] + BH / 2) / 2))

    # decision -> right loop boxes (Yes) and back
    arrow(ax, (dec1[0] + DW / 2, dec1[1]), (form[0] - BW / 2, form[1]), "Yes", (1.9, dec1[1] + 0.25))
    arrow(ax, (form[0], form[1] + BH / 2), (dec1[0], dec1[1] + DH / 2 + 0.02), rad=0.32)  # loop back up to dec1 top
    arrow(ax, (dec2[0] + DW / 2, dec2[1]), (assign[0] - BW / 2, assign[1]), "Yes", (1.9, dec2[1] + 0.25))
    arrow(ax, (assign[0], assign[1] + BH / 2), (dec2[0], dec2[1] + DH / 2 + 0.02), rad=0.32)

    ax.set_xlim(-3.0, 7.2)
    ax.set_ylim(-1.8, 10.2)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
