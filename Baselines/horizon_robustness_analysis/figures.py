"""Static report figures over campaign tables. Reads analysis output only.

Design parameters follow the project's validated categorical palette. Every
figure obeys the same rules:

* one value axis, never two y-scales;
* categorical hues assigned in fixed slot order and never cycled;
* a legend whenever two or more series appear, plus direct labels at four or
  fewer series, so identity never depends on color alone;
* every panel prints its own denominator, because a rate over an unstated
  denominator is the failure mode this study must not commit;
* recessive grid and axis ink, thin marks, text in ink tokens not series color.

Four arms exceed the three-slot all-pairs cap, so any scatter is faceted into
small multiples with one hue per panel rather than plotted as four overlapping
colored clouds. Each figure has a CSV counterpart in ``tables/``: that is the
accessible table view, and it is authoritative where a mark is ambiguous.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Validated categorical slots, light surface, fixed order.
SERIES = {"NOM": "#2a78d6", "TIGHT": "#eb6834", "HIST": "#1baf7a", "HIST+ACT": "#eda100",
          "HIST+ACT-T": "#8f5ad8"}   # fifth categorical slot, revision 3
MARKERS = {"NOM": "o", "TIGHT": "s", "HIST": "^", "HIST+ACT": "D", "HIST+ACT-T": "v"}
STATUS_COLORS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
ARM_ORDER = ("NOM", "TIGHT", "HIST", "HIST+ACT", "HIST+ACT-T")

STATUS_ROLE = {
    "COMPLETE": "good", "DIAGNOSTIC_COMPLETE": "good",
    "REJECTED_CANDIDATE": "serious", "SCORING_FAILED": "serious",
    "NO_INCUMBENT_LIMIT": "warning", "RESOURCE_LIMIT": "warning",
    "WALL_CUTOFF": "warning", "SOLVER_BUDGET_CUTOFF": "warning",
    "INSUFFICIENT_HISTORY": "warning", "INSUFFICIENT_FUTURE": "warning",
}

# Several distinct statuses share one status role, and a status colour is
# reserved and must not be re-stepped into a series hue. Texture is the
# accessibility channel that separates them, so each status inside a role gets
# its own hatch: identity never rests on colour alone.
HATCHES = ("", "///", "...", "\\\\\\", "xxx")


def _two_sided(rows):
    """True when every row was scored under the two-sided rule (cap AND floor).

    Rows come from one campaign at a time, so a mixed set never occurs in
    practice; a mixed or empty set falls back to the upper-only wording.
    """
    return bool(rows) and all(r.get("rule") == "two_sided" for r in rows)


def _style(ax, *, xlabel="", ylabel="", title=""):
    ax.set_facecolor(SURFACE)
    ax.figure.set_facecolor(SURFACE)
    ax.grid(True, axis="y", color=GRID, linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=8, length=3, width=0.8)
    ax.set_xlabel(xlabel, color=INK_SECONDARY, fontsize=9)
    ax.set_ylabel(ylabel, color=INK_SECONDARY, fontsize=9)
    if title:
        ax.set_title(title, color=INK, fontsize=10, loc="left", pad=8)
    return ax


def _save(fig, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return str(path)


def _role(status):
    return STATUS_ROLE.get(status, "critical")


# --------------------------------------------------------------------------

def violation_by_horizon(frame, path, *, title="Future joint station-cap compliance"):
    """Compliance rate per horizon multiple and arm, with denominators printed.

    A bar is drawn only over the number of SCORED cells in that cell; the count
    of authorized rows and of rows that returned no allocation is written above
    each group, so a high rate over a thin denominator cannot look like success.
    """
    cells = {}
    for row in frame:
        if row["catalogue_size"] is None:
            continue
        multiple = round(row["n"] / row["catalogue_size"], 3)
        bucket = cells.setdefault((multiple, row["arm"]), dict(scored=0, passed=0, rows=0, missing=0))
        bucket["rows"] += 1
        if row["scored"]:
            bucket["scored"] += 1
            bucket["passed"] += bool(row["joint_pass"])
        elif not row["eligibility"]:
            bucket["missing"] += 1
    multiples = sorted({k[0] for k in cells})
    if not multiples:
        return None
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    width = 0.8 / len(ARM_ORDER)
    for index, arm in enumerate(ARM_ORDER):
        xs, ys, labels = [], [], []
        for position, multiple in enumerate(multiples):
            bucket = cells.get((multiple, arm))
            if not bucket or not bucket["scored"]:
                continue
            xs.append(position + (index - (len(ARM_ORDER) - 1) / 2) * width)
            ys.append(100.0 * bucket["passed"] / bucket["scored"])
            labels.append(f"{bucket['passed']}/{bucket['scored']}")
        if not xs:
            continue
        bars = ax.bar(xs, ys, width * 0.92, label=arm, color=SERIES[arm], zorder=3,
                      edgecolor=SURFACE, linewidth=1.4)
        # A measured 0% and an absent group would otherwise be the same picture.
        # Give a measured zero its own visible baseline stub.
        zeros = [x for x, y in zip(xs, ys) if y == 0]
        if zeros:
            ax.scatter(zeros, [0] * len(zeros), marker="_", s=110, linewidth=2.4,
                       color=SERIES[arm], zorder=4)
        for bar, label in zip(bars, labels):
            ax.annotate(label, (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                        textcoords="offset points", xytext=(0, 3), ha="center",
                        fontsize=6.5, color=INK_SECONDARY)
    ax.set_xticks(range(len(multiples)))
    ax.set_xticklabels([f"n = {m:g}·P" for m in multiples])
    # Without an explicit range a single drawn group leaves the tick off-centre.
    ax.set_xlim(-0.5, len(multiples) - 0.5)
    ax.set_ylim(0, 112)
    _style(ax, xlabel="Future horizon, as a multiple of the catalogue size",
           ylabel=("Cells passing every station band, cap and floor (%)" if _two_sided(frame)
                   else "Cells passing every station cap (%)"), title=title)
    for position, multiple in enumerate(multiples):
        rows = sum(v["rows"] for k, v in cells.items() if k[0] == multiple)
        missing = sum(v["missing"] for k, v in cells.items() if k[0] == multiple)
        ax.annotate(f"{rows} rows; {missing} no layout", (position, 107), ha="center",
                    fontsize=6.5, color=MUTED)
    if ax.get_legend_handles_labels()[0]:  # a campaign with no scored cell draws no bar
        ax.legend(frameon=False, fontsize=8, ncols=4, loc="lower center",
                  bbox_to_anchor=(0.5, -0.28), labelcolor=INK_SECONDARY)
    fig.text(0.02, -0.30, "Bar labels are passing/scored cells. An absent bar means no scored "
                          "cell in that group, not a zero rate.", fontsize=6.5, color=MUTED)
    return _save(fig, path)


def visits_versus_excess(frame, path, *, title="Protection cost against realized cap excess"):
    """Faceted scatter: one arm per panel, one hue per panel.

    Four arms exceed the three-slot all-pairs colour cap, so the arms are
    faceted instead of overplotted. Shared axes keep the panels comparable.
    """
    points = {arm: [] for arm in ARM_ORDER}
    for row in frame:
        if row["scored"] and row["mean_visits"] is not None and row["worst_excess_pp"] is not None:
            points[row["arm"]].append((row["worst_excess_pp"], row["mean_visits"], row["joint_pass"]))
    drawn = [arm for arm in ARM_ORDER if points[arm]]
    if not drawn:
        return None
    fig, axes = plt.subplots(1, len(drawn), figsize=(3.0 * len(drawn), 3.4), sharex=True, sharey=True)
    axes = [axes] if len(drawn) == 1 else list(axes)
    for ax, arm in zip(axes, drawn):
        xs = [p[0] for p in points[arm]]
        ys = [p[1] for p in points[arm]]
        edges = [SERIES[arm] if p[2] else "#d03b3b" for p in points[arm]]
        ax.scatter(xs, ys, s=34, marker=MARKERS[arm], facecolor=SERIES[arm], edgecolor=edges,
                   linewidth=1.2, alpha=0.85, zorder=3)
        _style(ax, xlabel=("Worst station band breach (pp)" if _two_sided(frame)
                           else "Worst station excess (pp)"), ylabel="", title=arm)
        ax.axvline(0, color=AXIS, linewidth=0.9, zorder=2)
        ax.annotate(f"n = {len(xs)} scored", (0.97, 0.04), xycoords="axes fraction",
                    ha="right", fontsize=6.5, color=MUTED)
    axes[0].set_ylabel("Mean future station visits per order", color=INK_SECONDARY, fontsize=9)
    fig.suptitle(title, color=INK, fontsize=10, x=0.02, y=1.06, ha="left")
    fig.text(0.02, -0.06, ("A red ring marks a cell that violated at least one station cap or floor. "
                           if _two_sided(frame) else
                           "A red ring marks a cell that violated at least one station cap. ")
                          + "Excess at or below 0 pp is compliant.", fontsize=6.5, color=MUTED)
    return _save(fig, path)


def frontier(rows, path, *, axis, title=None):
    """Frontier over a declared grid, keeping unresolved and missing cells visible."""
    grouped = {}
    for row in rows:
        grouped.setdefault(row["arm"], []).append(row)
    series = [arm for arm in ARM_ORDER if arm in grouped]
    if not series:
        return None
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(6.6, 5.2), sharex=True,
                                      gridspec_kw=dict(height_ratios=(2, 1)))
    positions, labels = {}, []
    values = sorted({r["value"] for r in rows}, key=float)
    for index, value in enumerate(values):
        positions[value] = index
        labels.append(value)
    for arm in series:
        # One point per axis value: cells at the same value (several datasets or
        # horizons) are AGGREGATED with an explicit denominator, never threaded
        # through as separate points of one line (13 Sep 2026 review).
        merged = {}
        for e in grouped[arm]:
            m = merged.setdefault(e["value"], dict(passes=0, scored=0, cells=0))
            m["passes"] += e["joint_pass"]; m["scored"] += e["scored_cells"]; m["cells"] += e["cells"]
        entries = [dict(value=v, **merged[v]) for v in sorted(merged, key=float)]
        xs = [positions[e["value"]] for e in entries]
        rates = [(100.0 * e["passes"] / e["scored"]) if e["scored"] else None for e in entries]
        drawn_x = [x for x, y in zip(xs, rates) if y is not None]
        drawn_y = [y for y in rates if y is not None]
        top.plot(drawn_x, drawn_y, marker=MARKERS[arm], color=SERIES[arm], linewidth=2,
                 markersize=6, label=arm, zorder=3)
        for x, y, e in zip(xs, rates, entries):
            if y is not None:
                top.annotate(f"{e['passes']}/{e['scored']}", (x, y), textcoords="offset points",
                             xytext=(0, 6), fontsize=6.5, color=INK_SECONDARY, ha="center")
        if drawn_x:
            top.annotate(arm, (drawn_x[-1], drawn_y[-1]), textcoords="offset points",
                         xytext=(6, 0), fontsize=7.5, color=INK_SECONDARY, va="center")
        unresolved = [e["cells"] - e["scored"] for e in entries]
        bottom.plot(xs, unresolved, marker=MARKERS[arm], color=SERIES[arm], linewidth=1.6,
                    markersize=5, zorder=3)
    top.set_xticks(range(len(labels)))
    top.set_ylim(-4, 108)
    _style(top, ylabel=("Cells passing every band, cap and floor (%)" if _two_sided(rows)
                        else "Cells passing every cap (%)"),
           title=title or f"{axis} frontier: compliance and unresolved cells")
    _style(bottom, xlabel={"delta": "δ (absolute share allowance)",
                           "nu": "ν (activation mass budget)",
                           "tightening": "λ (tightening fraction)"}.get(axis, axis),
           ylabel="Cells with no scored result")
    bottom.set_xticks(range(len(labels)))
    bottom.set_xticklabels(labels)
    top.legend(frameon=False, fontsize=8, ncols=len(series), loc="lower center",
               bbox_to_anchor=(0.5, -0.18), labelcolor=INK_SECONDARY)
    fig.text(0.02, -0.02, "One point per value per arm: passes/scored cells over every matched cell at that "
                          "value. The lower panel is the denominator audit: cells that produced no scored "
                          "result are never dropped from the frontier.", fontsize=6.5, color=MUTED)
    return _save(fig, path)


def station_profile(rows, path, *, title="Station target, ceiling and realized future share"):
    """Per-station dumbbell: historical target b_s, ceiling u_s, realized share."""
    if not rows:
        return None
    ordered = sorted(rows, key=lambda r: -r["target"])
    labels = [r["station"] for r in ordered]
    positions = list(range(len(ordered)))
    fig, ax = plt.subplots(figsize=(7.4, max(3.2, 0.26 * len(ordered) + 1.4)))
    for position, row in zip(positions, ordered):
        ax.plot([row["target"] * 100, row["future_share"] * 100], [position, position],
                color=GRID, linewidth=2.4, zorder=2, solid_capstyle="round")
    ax.scatter([r["target"] * 100 for r in ordered], positions, s=30, marker="o",
               color=MUTED, zorder=4, label="Historical target b")
    ax.scatter([r["cap"] * 100 for r in ordered], positions, s=44, marker="|",
               color=INK_SECONDARY, linewidth=1.4, zorder=4, label="Ceiling u = min(1, b+δ)")
    floors = [r.get("floor") for r in ordered]
    two_sided = all(f is not None for f in floors)
    if two_sided:
        # Two-sided rule: the floor is a constraint too, so it is drawn with the
        # same glyph as the ceiling in the NOM series hue to keep it distinct.
        ax.scatter([f * 100 for f in floors], positions, s=44, marker="|",
                   color=SERIES["NOM"], linewidth=1.4, zorder=4, label="Floor f = max(0, b−δ)")
    breached = [r["future_share"] * 100 for r in ordered]
    colors = [STATUS_COLORS["critical"] if not r["feasible"] else SERIES["HIST"] for r in ordered]
    ax.scatter(breached, positions, s=36, marker="D", color=colors, zorder=5,
               label="Realized future share")
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=7)
    ax.invert_yaxis()
    _style(ax, xlabel="Share of retained future workload (%)", ylabel="", title=title)
    ax.grid(True, axis="x", color=GRID, linewidth=0.6, zorder=0)
    ax.grid(False, axis="y")
    below = sum(1 for r in ordered if r.get("below_floor"))
    above = sum(1 for r in ordered if not r["feasible"] and not r.get("below_floor"))
    legend_offset = -0.16 - 0.4 / max(1, len(ordered) * 0.26)
    ax.legend(frameon=False, fontsize=7.5, ncols=4 if two_sided else 3, loc="lower center",
              bbox_to_anchor=(0.5, legend_offset), labelcolor=INK_SECONDARY)
    # Below the legend (the title owns the top edge); the saved bounding box
    # expands to include it, so a negative axes coordinate is safe.
    if two_sided:
        note = (f"{len(ordered)} included stations; {above} above ceiling, {below} below floor. "
                "A red diamond marks a station outside its band.")
    else:
        note = (f"{len(ordered)} included stations; {above} above ceiling. "
                "A red diamond marks a station over its ceiling.")
    ax.annotate(note, (0, legend_offset - 0.06), xycoords="axes fraction", ha="left", va="top",
                fontsize=6.5, color=MUTED, annotation_clip=False)
    return _save(fig, path)


def status_breakdown(frame, path, *, title="Computational outcome of every authorized row"):
    """Stacked status bars per catalogue-size stratum, over authorized rows."""
    strata = {}
    for row in frame:
        key = row["catalogue_size"] or 0
        strata.setdefault(key, {}).setdefault(row["status"], 0)
        strata[key][row["status"]] += 1
    if not strata:
        return None
    sizes = sorted(strata)
    statuses = sorted({s for v in strata.values() for s in v},
                      key=lambda s: (["good", "warning", "serious", "critical"].index(_role(s)), s))
    # Give each status inside one status role its own hatch.
    used = {}
    texture = {}
    for status in statuses:
        role = _role(status)
        texture[status] = HATCHES[used.get(role, 0) % len(HATCHES)]
        used[role] = used.get(role, 0) + 1
    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    bottoms = [0] * len(sizes)
    for status in statuses:
        heights = [strata[size].get(status, 0) for size in sizes]
        ax.bar(range(len(sizes)), heights, 0.62, bottom=bottoms, label=status,
               color=STATUS_COLORS[_role(status)], edgecolor=SURFACE, linewidth=1.4,
               hatch=texture[status], zorder=3)
        for index, (height, base) in enumerate(zip(heights, bottoms)):
            if height:
                ax.annotate(str(height), (index, base + height / 2), ha="center", va="center",
                            fontsize=7, color=INK)
        bottoms = [b + h for b, h in zip(bottoms, heights)]
    ax.set_xticks(range(len(sizes)))
    ax.set_xticklabels([f"{s} products\n({sum(strata[s].values())} rows)" for s in sizes], fontsize=8)
    ax.set_xlim(-0.5, len(sizes) - 0.5)
    _style(ax, xlabel="", ylabel="Authorized manifest rows", title=title)
    ax.yaxis.get_major_locator().set_params(integer=True)   # rows are counts, not fractions
    ax.legend(frameon=False, fontsize=7.5, ncols=3, loc="upper left",
              bbox_to_anchor=(0, -0.18), labelcolor=INK_SECONDARY)
    fig.text(0.02, -0.22, "Every authorized row appears exactly once; each segment is labeled with "
                          "its own count. Statuses sharing a status colour are separated by texture.",
             fontsize=6.5, color=MUTED)
    return _save(fig, path)


def cross_horizon_transfer(rows, path, *, title="Transfer of a frozen layout to other horizons"):
    """Compliance of layouts trained at one horizon multiple and scored at another.

    Grouping is by catalogue-RELATIVE horizon multiple (n/P), never by absolute
    n, so a 50-product layout trained at n = 50 (= P) sits with a 2000-product
    layout trained at n = 2000 (= P), not with one trained at n = 50 (= P/40).
    Each bar prints passes/cells, and the legend is built from every panel so an
    arm missing from the first panel still appears.
    """
    rows = [r for r in rows if r.get("trained_multiple") and r.get("scored_multiple")]
    if not rows:
        return None
    order = {"1/2": 0, "1": 1, "2": 2}
    trained = sorted({r["trained_multiple"] for r in rows}, key=lambda m: order.get(m, 9))
    fig, axes = plt.subplots(1, len(trained), figsize=(3.1 * len(trained), 3.5), sharey=True)
    axes = [axes] if len(trained) == 1 else list(axes)
    handles = {}
    for ax, train in zip(axes, trained):
        subset = [r for r in rows if r["trained_multiple"] == train]
        scored = sorted({r["scored_multiple"] for r in subset}, key=lambda m: order.get(m, 9))
        for index, arm in enumerate(ARM_ORDER):
            xs, ys, labels = [], [], []
            for position, target in enumerate(scored):
                cells = [r for r in subset if r["scored_multiple"] == target and r["arm"] == arm]
                if not cells:
                    continue
                passed = sum(bool(c["joint_pass"]) for c in cells)
                xs.append(position + (index - 1.5) * 0.2)
                ys.append(100.0 * passed / len(cells))
                labels.append(f"{passed}/{len(cells)}")
            if not xs:
                continue
            bars = ax.bar(xs, ys, 0.185, color=SERIES[arm], edgecolor=SURFACE, linewidth=1.1, zorder=3)
            handles.setdefault(arm, bars[0])
            zeros = [x for x, y in zip(xs, ys) if y == 0]
            if zeros:
                ax.scatter(zeros, [0] * len(zeros), marker="_", s=90, linewidth=2.2,
                           color=SERIES[arm], zorder=4)
            for bar, label in zip(bars, labels):
                ax.annotate(label, (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                            textcoords="offset points", xytext=(0, 2), ha="center",
                            fontsize=5.8, color=INK_SECONDARY, rotation=90)
        ax.set_xticks(range(len(scored)))
        ax.set_xticklabels([f"{m}·P" for m in scored], fontsize=7.5)
        ax.set_xlim(-0.5, len(scored) - 0.5)
        ax.set_ylim(0, 118)
        _style(ax, xlabel="Scored horizon", ylabel="", title=f"trained at {train}·P")
    axes[0].set_ylabel("Cells passing every cap (%)", color=INK_SECONDARY, fontsize=9)
    fig.suptitle(title, color=INK, fontsize=10, x=0.02, y=1.06, ha="left")
    ordered = [arm for arm in ARM_ORDER if arm in handles]
    fig.legend([handles[a] for a in ordered], ordered, frameon=False, fontsize=7.5,
               ncols=len(ordered), loc="lower center", bbox_to_anchor=(0.5, -0.10),
               labelcolor=INK_SECONDARY)
    fig.text(0.02, -0.16, "Bar labels are passes/cells. Secondary scoring of already frozen "
                          "layouts on overlapping futures: it shows transfer, is NOT independent "
                          "replication, and must not be used to choose a horizon after seeing it.",
             fontsize=6.5, color=MUTED)
    return _save(fig, path)
