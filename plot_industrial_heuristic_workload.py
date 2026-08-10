"""Redraw Figure 11: per-station load of the heuristic layout against the legacy one.

The two panels the manuscript ships (Images_CSLAP/r4_number_of_lines_per_station.png
and r5_pct_change_lines_per_station.png) predate the current campaign and had no
generator in the repository, so they could not be tied to any particular run. This
script draws both from results_industrial_heuristic_per_station.csv, which
``run_industrial_heuristic_alone.py`` writes in the same run that produces the
Table 6 heuristic row, so the figure and the table now agree by construction.

Panel style follows nb_code.py's ``plot_final``: paired bars, legacy versus new,
stations ordered by legacy load.

Reproduce
---------
cd CSLAP-Synthetic
python run_industrial_heuristic_alone.py
python plot_industrial_heuristic_workload.py
"""

from __future__ import annotations

import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mtick  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_CSV = os.path.join(BASE_DIR, "Heuristic_Connex_Set_Project", "data",
                       "BERNER_ORDER_LINES_09-12.csv")


def station_alias_map(raw_csv: str = RAW_CSV, with_counts: bool = False):
    """Site station codes to the published anonymous labels ``S_1``..``S_26``.

    Company A's own codes (``01.02``, ``01.E4``) must not appear in the paper.
    The anonymisation convention is the one nb_code.py cell 14 established and
    plot_cg_industrial_lines.py reproduces for the column-generation panel:
    number the stations by FIRST APPEARANCE in the deduplicated order-line
    stream, after each multi-station product is collapsed onto the station of
    its latest order and ``01.GE4`` is renamed ``01.E4``. It is rebuilt here
    from the raw file rather than hard-coded so that every panel of Figure 11
    carries the same label on the same station.

    With ``with_counts``, also returns each station's legacy order-line count on
    that same universe, which is how the two stations the solvers never see get
    their bars in the lines-per-station panel.
    """
    df = pd.read_csv(raw_csv, sep=";")[["PRODUCT", "ORDER", "STATION"]]
    df = df.drop_duplicates().dropna()
    uc = df.groupby("PRODUCT")["STATION"].nunique().reset_index(name="k")
    df = df.merge(uc, on="PRODUCT", how="left")
    multi = df[df["k"] > 1]["PRODUCT"].unique()
    fix = (df[df["PRODUCT"].isin(multi)].sort_values("ORDER", ascending=False)
           .drop_duplicates("PRODUCT")[["PRODUCT", "STATION"]])
    df = df.merge(fix, on="PRODUCT", how="left", suffixes=("", "_fx"))
    df["STATION"] = df["STATION_fx"].where(df["STATION_fx"].notna(), df["STATION"])
    df = df[df["STATION"] != "01.Z8"]
    df.loc[df["STATION"] == "01.GE4", "STATION"] = "01.E4"
    seen = list(dict.fromkeys(df["STATION"]))
    alias = {s: f"S_{i}" for i, s in enumerate(seen, start=1)}
    if with_counts:
        return alias, df.groupby("STATION").size().to_dict()
    return alias


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--per-station", type=str,
                   default="results_industrial_heuristic_per_station.csv")
    p.add_argument("--out-dir", type=str, default="Images_CSLAP")
    p.add_argument("--raw-csv", type=str, default=RAW_CSV,
                   help="order lines the S_i anonymisation is derived from")
    p.add_argument("--no-anonymise", action="store_true",
                   help="label the axes with the site's own station codes")
    p.add_argument("--no-inactive", action="store_true",
                   help="omit the stations no solver evaluates from the lines panel")
    args = p.parse_args(argv)

    path = os.path.join(BASE_DIR, args.per_station)
    if not os.path.exists(path):
        print(f"[error] {path} not found; run run_industrial_heuristic_alone.py first",
              file=sys.stderr)
        return 1
    # STATION_ID must be read as text. Every code on this site looks numeric to
    # the type inferencer, and one of them, 01.E4, is valid scientific notation:
    # inferred as float it becomes 10000.0 on the axis, while 01.02, 01.10 and
    # 01.30 lose their leading zero and trailing digit.
    df = pd.read_csv(path, dtype={"STATION_ID": str})
    # Ascending by legacy load, the order the previously shipped panel and the
    # column-generation panel of the same figure both use.
    df = df.sort_values("lines_original", ascending=True)
    stations = df["STATION_ID"].to_numpy()

    alias, raw_counts = None, None
    if os.path.exists(args.raw_csv):
        alias, raw_counts = station_alias_map(args.raw_csv, with_counts=True)
    if not args.no_anonymise:
        if alias is None:
            print(f"[error] {args.raw_csv} not found; the S_i labels are derived "
                  f"from it. Pass --no-anonymise to plot the site's own codes.",
                  file=sys.stderr)
            return 1
        unmapped = [s for s in stations if s not in alias]
        if unmapped:
            print(f"[error] no anonymous label for {unmapped}; the mapping and "
                  f"the per-station results disagree", file=sys.stderr)
            return 1
        stations = np.array([alias[s] for s in stations])
    idx = np.arange(len(stations))
    width = 0.35
    out_dir = os.path.join(BASE_DIR, args.out_dir)

    # Panel 1 covers the inactive stations too. 01.GED and 01.15 hold 5 and 11
    # order lines, sit outside the 24 the solvers and Table 6 evaluate, and are
    # never re-slotted, so both of their bars carry the legacy count. They are
    # plotted because the site has them and the previously published panel did:
    # a reader counting stations should find all 26. Panel 2 stays on the 24
    # evaluated ones -- a relative change is undefined for a station no method
    # can touch, and these two would only add two flat bars at 0.0%.
    lines_o = df["lines_original"].to_numpy(dtype=float)
    lines_h = df["lines_heuristic"].to_numpy(dtype=float)
    stations_p1 = list(stations)
    if raw_counts is not None and not args.no_inactive:
        evaluated = set(df["STATION_ID"])
        extra = sorted(((s, c) for s, c in raw_counts.items() if s not in evaluated),
                       key=lambda t: t[1])
        for sid, cnt in reversed(extra):
            label = alias[sid] if (alias and not args.no_anonymise) else sid
            stations_p1.insert(0, label)
            lines_o = np.insert(lines_o, 0, float(cnt))
            lines_h = np.insert(lines_h, 0, float(cnt))
        if extra:
            print("[info] inactive stations added to the lines panel: "
                  + ", ".join(f"{alias.get(s, s) if not args.no_anonymise else s}"
                              f" ({c} lines)" for s, c in extra))

    # Panel 1: raw lines per station, legacy vs heuristic. No capacity line here:
    # TIME_CAPACITY is expressed in speed-adjusted units and the two are not
    # comparable on one axis. Utilisation against capacity is the right panel.
    idx1 = np.arange(len(stations_p1))
    plt.figure(figsize=(10, 5))
    ax = plt.gca()
    ax.bar(idx1 - width / 2, lines_o, width, label="Original", alpha=0.6)
    ax.bar(idx1 + width / 2, lines_h, width, label="Heuristic", alpha=0.6)
    plt.xlabel("Station Name")
    plt.ylabel("Number of lines")
    plt.title("Number of Lines per Station")
    plt.xticks(idx1, stations_p1, rotation=45)
    plt.legend()
    plt.tight_layout()
    p1 = os.path.join(out_dir, "r4_number_of_lines_per_station.png")
    plt.savefig(p1, dpi=150)
    plt.close()

    # Panel 2: relative change in load per station, drawn in the style of the
    # figure the manuscript shipped previously -- a single bar colour, a signed
    # value label on every bar, percent-formatted ticks and a light horizontal
    # grid -- so the reader compares this campaign against the earlier one
    # without also absorbing a change of chart convention. The +10% tolerance
    # line is the one addition: feasibility is the claim this panel now carries.
    pct = df["pct_change"].to_numpy(dtype=float)
    plt.figure(figsize=(14, 6))
    ax = plt.gca()
    ax.bar(idx, pct, 0.6, color="tab:blue")
    ax.axhline(0.0, color="grey", lw=1.0)
    ax.axhline(10.0, color="red", ls="--", lw=1.0, label="+10% operational slack")
    for i, v in zip(idx, pct):
        ax.annotate(f"{v:.1f}%", xy=(i, v), textcoords="offset points",
                    xytext=(0, 4 if v >= 0 else -12), ha="center", fontsize=8)
    pad = 0.10 * (pct.max() - pct.min())
    ax.set_ylim(pct.min() - pad, max(pct.max(), 10.0) + pad)
    ax.yaxis.set_major_locator(mtick.MaxNLocator(nbins=8, steps=[1, 2, 2.5, 5, 10]))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.grid(axis="y", ls="--", lw=0.5, alpha=0.4)
    ax.set_axisbelow(True)
    plt.xlabel("Station Name")
    plt.ylabel("Change in Lines (%)")
    plt.title("Relative Change in Number of Lines per Station")
    plt.xticks(idx, stations, rotation=45)
    plt.legend(loc="lower left")
    plt.tight_layout()
    p2 = os.path.join(out_dir, "r5_pct_change_lines_per_station.png")
    plt.savefig(p2, dpi=150)
    plt.close()

    # Feasibility on this site is each station against +10% of its OWN legacy
    # load, on the speed-adjusted quantity -- the convention of Table 6 and of
    # Baselines/report_industrial_deviation.py. Comparing against the raw legacy
    # load (no tolerance) is a different, stricter test and must not be used here.
    d = df[df["load_original"] > 0]
    dev = 100.0 * (d["load_heuristic"] - d["load_original"]) / d["load_original"]
    over = int((dev > 10.0 + 1e-9).sum())
    print(f"[out] {p1}\n[out] {p2}")
    print(f"[check] {over} of {len(d)} stations exceed the +10% tolerance "
          f"(0 means the layout is deployable); utilisation deviation spans "
          f"[{dev.min():+.1f}%, {dev.max():+.1f}%]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
