"""Regenerate every table, figure and audit from immutable campaign artifacts.

This never optimizes and never reads a solver. It can be re-run at any time to
reproduce the whole analysis layer from the stored case records:

    C:\\ermal\\Virtual_Environment_CPLEX_1\\Scripts\\python.exe \\
        tools/horizon_robustness/make_analysis.py

A campaign directory containing SUPERSEDED.md is excluded from every table and
figure by default; ``--include-superseded`` lists it in the audit instead of
silently ignoring it.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from Baselines.horizon_robustness.protocol import canonical_json, digest  # noqa: E402
from Baselines.horizon_robustness_analysis import ANALYSIS_VERSION, analysis, figures  # noqa: E402
from Baselines.horizon_robustness_analysis.rescoring import load_cross_horizon  # noqa: E402

CAMPAIGNS = ROOT / "reports" / "horizon_robustness_results" / "campaigns"
RESULTS = ROOT / "reports" / "horizon_robustness_results"
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"


def campaign_paths(include_superseded=False):
    out, excluded = [], []
    for manifest in sorted(CAMPAIGNS.glob("*/manifest.json")):
        directory = manifest.parent
        if (directory / "SUPERSEDED.md").exists() and not include_superseded:
            excluded.append(directory.name)
            continue
        out.append(directory)
    return out, excluded


def _aliases():
    try:
        from Baselines.horizon_robustness.industrial import article_station_labels
        return article_station_labels(ROOT)
    except Exception as exc:                       # pragma: no cover - environment dependent
        print(f"note: publication aliases unavailable ({type(exc).__name__}: {exc})")
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-superseded", action="store_true")
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args(argv)

    started = time.time()
    directories, excluded = campaign_paths(args.include_superseded)
    if not directories:
        print("NO ELIGIBLE CAMPAIGN FOUND", file=sys.stderr)
        return 1

    frame, campaigns, cross = [], [], []
    for directory in directories:
        campaign = analysis.load_campaign(directory, lean=True)
        campaigns.append(campaign)
        frame.extend(analysis.case_frame(campaign))
        cross.extend(load_cross_horizon(directory))

    written = {}

    def emit(name, rows, **kwargs):
        if not rows:
            written[name] = dict(path=None, rows=0, note="no rows produced by the current campaigns")
            return []
        written[name] = analysis.write_csv(rows, TABLES / f"{name}.csv")
        return rows

    emit("case_frame", frame)
    emit("status_by_cell", analysis.status_table(frame))
    emit("resources", analysis.resource_table(frame))
    pairs = emit("paired_cases", analysis.paired_rows(frame))
    instances = emit("instance_summary", analysis.instance_summary(frame))
    emit("stratum_summary", analysis.stratum_summary(instances))
    emit("paired_stratum_summary", analysis.paired_stratum_summary(pairs))
    emit("min_slack_diagnostic", analysis.min_slack_table(frame))
    cross_rows = emit("cross_horizon", analysis.cross_horizon_table(cross))
    frontiers, pooled_frontiers = {}, {}
    for axis in ("delta", "nu", "tightening"):
        values = {row[axis] for row in frame}
        if len(values) > 1:
            frontiers[axis] = emit(f"frontier_{axis}", analysis.frontier_table(frame, axis))
            # Pooled across campaigns only inside one (rule, implementation hash);
            # revision 2 ran each two-sided delta as its own campaign.
            pooled_frontiers[axis] = emit(f"frontier_{axis}_pooled_by_rule",
                                          analysis.rule_frontier_table(frame, axis))
        else:
            written[f"frontier_{axis}"] = dict(
                path=None, rows=0,
                note=f"only one {axis} value ({sorted(values)}) is present; no frontier is defined")

    aliases = _aliases()
    stations = []
    if aliases:
        for campaign in campaigns:
            for row in analysis.station_table(campaign, dataset_ids={"BERNER"}, aliases=aliases):
                row["campaign"] = campaign["campaign"]
                stations.append(row)
        emit("station_profile_industrial", stations)
    else:
        # Never fall back to raw site codes: no aliases means no industrial table.
        written["station_profile_industrial"] = dict(
            path=None, rows=0,
            note="publication station aliases unavailable; industrial table withheld rather "
                 "than published with internal site codes")
    synthetic_stations = []
    for campaign in campaigns:
        for row in analysis.station_table(campaign, dataset_ids={"syn_50sku_seed1001", "syn_500sku_seed1001"}):
            row["campaign"] = campaign["campaign"]
            synthetic_stations.append(row)
    emit("station_profile_synthetic", synthetic_stations)

    produced_figures = {}
    if not args.no_figures:
        # Figures are produced PER CAMPAIGN, never from the pooled frame. Two
        # campaigns can run under different implementation versions and share
        # (dataset, n) cells, so one pooled plot would mix versions and count a
        # condition twice. The largest screening campaign is the publication set
        # in figures/; every other campaign gets an engineering set in
        # figures/<campaign>/, clearly labelled in its own titles.
        publication = max((c for c in campaigns if c["stage"] == "screen"),
                          key=lambda c: len(c["manifest"]["rows"]), default=None)
        for campaign in campaigns:
            name = campaign["campaign"]
            rows = [r for r in frame if r["campaign"] == name]
            two_sided = bool(rows) and all(r["rule"] == "two_sided" for r in rows)
            is_publication = publication is not None and name == publication["campaign"]
            folder = FIGURES if is_publication else FIGURES / name
            label = f" — {name}" + ("" if is_publication else " (engineering, not publication)")
            key = "" if is_publication else f"{name}/"
            produced_figures[key + "joint_compliance_by_horizon"] = figures.violation_by_horizon(
                rows, folder / "joint_compliance_by_horizon.png",
                title=("Future joint station-band compliance, cap and floor" if two_sided
                       else "Future joint station-cap compliance") + label)
            produced_figures[key + "visits_versus_excess"] = figures.visits_versus_excess(
                rows, folder / "visits_versus_excess.png",
                title=("Protection cost against realized band breach" if two_sided
                       else "Protection cost against realized cap excess") + label)
            produced_figures[key + "status_breakdown"] = figures.status_breakdown(
                rows, folder / "status_breakdown.png",
                title="Computational outcome of every authorized row" + label)
            for axis, frontier_rows in frontiers.items():
                mine = [r for r in frontier_rows if r["campaign"] == name]
                # One value is a point, not a frontier: no figure for it.
                if mine and len({r["value"] for r in mine}) > 1:
                    produced_figures[key + f"frontier_{axis}"] = figures.frontier(
                        mine, folder / f"frontier_{axis}.png", axis=axis,
                        title=f"{axis} frontier: compliance and unresolved cells" + label)
            campaign_stations = [s for s in stations if s.get("campaign") == name]
            if campaign_stations:
                def rank(row):
                    return (row["arm"] != "HIST+ACT", row["n"] != 21874, row["delta"] != "0.01",
                            row["seed"], row["origin"], row["arm"], row["n"])
                keep = min(campaign_stations, key=rank)
                cell = [s for s in campaign_stations
                        if (s["origin"], s["n"], s["arm"], s["seed"], s["delta"])
                        == (keep["origin"], keep["n"], keep["arm"], keep["seed"], keep["delta"])]
                produced_figures[key + "station_profile_industrial"] = figures.station_profile(
                    cell, folder / "station_profile_industrial.png",
                    title=f"BERNER station shares — {keep['arm']}, n={keep['n']}, "
                          f"δ={keep['delta']}"
                          + (", two-sided" if keep.get("rule") == "two_sided" else "") + label)
            mine_cross = [r for r in cross_rows if r.get("campaign") == name]
            if mine_cross:
                produced_figures[key + "cross_horizon_transfer"] = figures.cross_horizon_transfer(
                    mine_cross, folder / "cross_horizon_transfer.png",
                    title="Transfer of a frozen layout to other horizons" + label)
        # A pooled frontier figure only where pooling actually merged campaigns
        # (otherwise it would duplicate a per-campaign figure), one folder per
        # (rule, implementation hash) so versions are never drawn together.
        for axis, pooled_rows in pooled_frontiers.items():
            groups = {}
            for r in pooled_rows:
                groups.setdefault((r["rule"], r["implementation_hash"] or "unknown"), []).append(r)
            for (rule, impl), rows in sorted(groups.items()):
                values = sorted({r["value"] for r in rows}, key=Fraction)
                if len(values) < 2 or len({r["campaigns"] for r in rows}) < 2:
                    continue
                # A response curve needs the SAME (dataset, horizon) cells at every
                # value; cells present at only some values would bend the curve
                # (13 Sep 2026 review). Keep matched cells only and say how many.
                present = {}
                for r in rows:
                    present.setdefault((r["dataset_id"], r["n"]), set()).add(r["value"])
                matched = {cell for cell, seen in present.items() if len(seen) == len(values)}
                rows = [r for r in rows if (r["dataset_id"], r["n"]) in matched]
                if not rows:
                    continue
                datasets = sorted({d for d, _ in matched})
                tag = f"pooled/{rule}__{impl[:8]}"
                produced_figures[f"{tag}/frontier_{axis}"] = figures.frontier(
                    rows, FIGURES / tag / f"frontier_{axis}.png", axis=axis,
                    title=f"{axis} response over {len(matched)} matched cell(s) of "
                          f"{', '.join(datasets)}: rule {rule}, implementation {impl[:8]} "
                          f"(engineering, not publication)")

    # Tables produced by the separate diagnostic tools are inventoried here too,
    # so artifact_index.json is a complete list rather than only what this script
    # writes. They are recorded with their own content hash.
    import hashlib
    for name in ("slack_survey", "slack_survey_cross_arm", "min_slack_diagnostic_cplex",
                 "dispersion_survey", "two_sided_novelty_survey", "drift_survey"):
        path = TABLES / f"{name}.csv"
        if path.exists():
            data = path.read_bytes()
            written[name] = dict(path=str(path), rows=max(0, data.count(b"\n") - 1),
                                 columns=None, sha256=hashlib.sha256(data).hexdigest(),
                                 produced_by="separate diagnostic tool, not make_analysis.py")
        else:
            written[name] = dict(path=None, rows=0, note="diagnostic not run")

    diagnostics = []
    diagnostic_dir = RESULTS / "diagnostics"
    if diagnostic_dir.exists():
        for path in sorted(diagnostic_dir.glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8-sig"))
            diagnostics.append(dict(path=str(path.relative_to(RESULTS)),
                                    kind=record.get("kind"),
                                    record_hash=record.get("record_hash")))

    totals = analysis.campaign_totals(frame)
    index = dict(
        generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        analysis_version=ANALYSIS_VERSION,
        elapsed_seconds=round(time.time() - started, 2),
        campaigns=[dict(name=c["campaign"], stage=c["stage"],
                        manifest_hash=c["manifest"]["manifest_hash"],
                        implementation_hash=c["manifest"]["runtime"].get("implementation_hash"),
                        rows=len(c["manifest"]["rows"]),
                        unique_solves=c["manifest"]["unique_solve_count"],
                        quoted_solver_seconds=c["manifest"]["solver_seconds"]) for c in campaigns],
        excluded_superseded_campaigns=excluded,
        totals=totals, tables=written,
        figures={k: v for k, v in produced_figures.items() if v},
        figures_not_produced=[k for k, v in produced_figures.items() if not v],
        cross_horizon_records=len(cross), diagnostics=diagnostics)
    (RESULTS / "artifact_index.json").write_text(canonical_json(index), encoding="utf-8")
    _audit(index, frame, campaigns)
    print(canonical_json(dict(campaigns=len(campaigns), rows=len(frame),
                              tables=sum(1 for v in written.values() if v.get("path")),
                              figures=len(index["figures"]), totals=totals)))
    print("ANALYSIS REGENERATED")
    return 0


def _audit(index, frame, campaigns):
    totals = index["totals"]
    lines = [
        "# Analysis audit",
        "",
        f"Regenerated {index['generated_utc']} from immutable campaign artifacts, in "
        f"{index['elapsed_seconds']} s, by analysis version `{index['analysis_version']}`. "
        "No optimizer is imported by this path.",
        "",
        "Reproduce with:",
        "",
        "```powershell",
        "& 'C:\\ermal\\Virtual_Environment_CPLEX_1\\Scripts\\python.exe' "
        "tools/horizon_robustness/make_analysis.py",
        "```",
        "",
        "## Campaigns included",
        "",
        "| Campaign | Stage | Manifest hash | Implementation hash | Rows | Unique solves | Quoted solver s |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for entry in index["campaigns"]:
        lines.append(f"| `{entry['name']}` | {entry['stage']} | `{entry['manifest_hash'][:16]}…` | "
                     f"`{(entry['implementation_hash'] or '')[:16]}…` | {entry['rows']} | "
                     f"{entry['unique_solves']} | {entry['quoted_solver_seconds']} |")
    if index["excluded_superseded_campaigns"]:
        lines += ["", "Excluded as superseded (preserved on disk, never analysed): "
                  + ", ".join(f"`{n}`" for n in index["excluded_superseded_campaigns"]) + "."]
    lines += [
        "",
        "## Denominator audit",
        "",
        "Every authorized manifest row lands in exactly one bin. A row that produced no "
        "layout carries `None` for every future metric, never zero.",
        "",
        "| Bin | Rows |",
        "|---|---:|",
        f"| Authorized rows | {totals['authorized_rows']} |",
        f"| Ineligible by protocol | {totals.get('ineligible', 0)} |",
        f"| No record at all | {totals.get('no_record', 0)} |",
        f"| Returned no allocation | {totals.get('no_allocation', 0)} |",
        f"| Allocation returned but not scored | {totals.get('allocation_but_unscored', 0)} |",
        f"| Scored on its future horizon | {totals.get('scored', 0)} |",
        f"| **Accounted** | **{totals['accounted']}** |",
        "",
        f"Accounting complete: {'yes' if totals['accounting_complete'] else 'NO — INVESTIGATE'}.",
        "",
        "### Status detail",
        "",
        "| Status | Rows |",
        "|---|---:|",
    ]
    for key, value in sorted(totals.items()):
        if key.startswith("status:"):
            lines.append(f"| `{key.split(':', 1)[1]}` | {value} |")
    lines += [
        "",
        "## Pseudoreplication rules applied",
        "",
        "* A pair is formed only inside one exactly matched cell "
        "(dataset, origin, n, seed, δ, ν, λ, solve mode), and only when both members were scored.",
        "* Solver seeds measure algorithm variability. They are averaged within an instance and "
        "never counted as extra future streams.",
        "* Horizons at one origin share data and are reported separately, never pooled.",
        "* Individual stations are not independent observations; joint compliance is per cell.",
        "* `stratum_summary` and `paired_stratum_summary` use the INSTANCE as the unit; "
        "`paired_instances` states how many instances each difference rests on.",
        "* Every table row carries `rule`. Upper-only and two-sided rows are summarised "
        "separately and never pooled. `frontier_<axis>_pooled_by_rule` pools campaigns only "
        "inside one (rule, implementation hash) and names every campaign it merged.",
        "",
        "## Predeclared primary-summary rule",
        "",
        "Primary summaries read `cases/<case_id>.json` only. Deliberate retries are inventoried "
        "separately and never substituted for a primary attempt. This rule was fixed before any "
        "result was inspected.",
        "",
        "## Tables",
        "",
        "| Table | Rows | Columns | Content hash |",
        "|---|---:|---:|---|",
    ]
    for name, entry in sorted(index["tables"].items()):
        if entry.get("path"):
            lines.append(f"| `tables/{name}.csv` | {entry['rows']} | {entry['columns']} | "
                         f"`{entry['sha256'][:16]}…` |")
        else:
            lines.append(f"| `{name}` | — | — | not produced: {entry.get('note', 'no rows')} |")
    if index.get("diagnostics"):
        lines += ["", "## Diagnostic records", "",
                  "Produced outside the campaign runner; each carries its own content hash.", "",
                  "| Record | Kind | Hash |", "|---|---|---|"]
        for entry in index["diagnostics"]:
            lines.append(f"| `{entry['path']}` | {entry['kind']} | `{(entry['record_hash'] or '')[:16]}…` |")
    lines += ["", "## Figures", "",
              "Each figure prints its own denominator and has the CSV above as its table view.", ""]
    for name, path in sorted(index["figures"].items()):
        lines.append(f"* `{Path(path).relative_to(RESULTS).as_posix()}` — {name}")
    for name in index["figures_not_produced"]:
        lines.append(f"* {name} — not produced (no qualifying rows)")
    retries = [r for r in frame if r["retry_count"]]
    lines += ["", "## Retries and reruns", ""]
    if retries:
        for row in retries:
            lines.append(f"* `{row['case_id'][:12]}…` ({row['dataset_id']}, {row['arm']}, n={row['n']}): "
                         f"{row['retry_count']} retry artifact(s), excluded from primary summaries.")
    else:
        lines.append("No deliberate retry was executed in any included campaign.")
    (RESULTS / "analysis_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
