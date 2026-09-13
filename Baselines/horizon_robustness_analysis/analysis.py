"""Reproducible paired analysis over immutable campaign artifacts.

This module never optimizes, never rebuilds a layout and never rewrites an
evaluation ceiling. It reads the campaign manifest plus the immutable case
records the runner published, and derives tables/figures from them.

Predeclared primary-summary rule (frozen before any result was inspected):

* A manifest row enters a primary summary only through its PRIMARY case file
  ``cases/<case_id>.json``. Deliberate retries under
  ``cases/<case_id>/retries/<retry_id>.json`` are inventoried and reported
  separately, never substituted for the primary attempt.
* Rows with no case file at all are recovered from the supervisor terminal
  record and reported as missing outcomes with an explicit status. They are
  never dropped and never scored as zero.
* Denominators are the number of authorized manifest rows, not the number of
  rows that happened to produce a layout.

Aggregation levels, in the order the protocol requires:

1. case          one (dataset, origin, n, arm, seed, parameter) row;
2. instance      averaged within a dataset across origins and seeds;
3. stratum       summarized across instances of one catalogue size.

Solver seeds, individual stations and overlapping/nested horizons are NOT
independent future replications and are never pooled as such.
"""

from __future__ import annotations

from collections import Counter, OrderedDict
from dataclasses import asdict
from fractions import Fraction
import json
from pathlib import Path
import statistics

from Baselines.horizon_robustness.protocol import ContractError, REPO_ROOT, digest, horizon_grid

# Values copied into a summary row when the underlying quantity does not exist.
# Never 0: a missing allocation is not a zero-cost, zero-violation observation.
MISSING = None

SCORED_STATUSES = ("COMPLETE", "DIAGNOSTIC_COMPLETE")
ARM_ORDER = ("NOM", "TIGHT", "HIST", "HIST+ACT", "HIST+ACT-T")


def _read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as exc:
        raise ContractError("CORRUPT_ARTIFACT", str(path)) from exc


def _f(value):
    """Exact string -> Fraction; None stays None."""
    return None if value is None else Fraction(value)


def _get(record, *keys, default=None):
    for key in keys:
        if not isinstance(record, dict) or key not in record:
            return default
        record = record[key]
    return record


# --------------------------------------------------------------------------
# Campaign loading
# --------------------------------------------------------------------------

# Product-length arrays inside a case record. A single BERNER evaluation carries
# four of them at 21,874 entries each, so a full screening campaign would hold
# millions of Python objects that no table or figure ever reads. ``lean`` drops
# them AFTER the artifact certificate has been verified against the full record.
_HEAVY = ("assignment", "slot_assignment", "product_ids", "product_line_counts")


def _strip(record):
    for key in ("evaluation", "reference_evaluation", "solve_result"):
        section = record.get(key)
        if isinstance(section, dict):
            for heavy in _HEAVY:
                if heavy in section:
                    section[heavy] = f"<omitted: {len(section[heavy])} entries>" \
                        if isinstance(section[heavy], list) else section[heavy]
    return record


def load_campaign(directory, *, verify_hash=True, lean=False):
    """Load one campaign directory into manifest + per-row records.

    ``verify_hash`` recomputes each case record's own immutable certificate, so
    a silently edited artifact cannot enter an analysis table. ``lean`` then
    releases the product-length arrays, which no table or figure consumes.
    """
    directory = Path(directory)
    manifest = _read(directory / "manifest.json")
    if verify_hash and digest({k: v for k, v in manifest.items() if k != "manifest_hash"}) != manifest.get("manifest_hash"):
        raise ContractError("MANIFEST_CHANGED", "campaign manifest hash does not match its content")

    supervisor = {}
    for terminal in sorted(directory.glob("supervision/*/terminal.json")):
        record = _read(terminal)
        for case in record.get("cases", []):
            supervisor.setdefault(_get(case, "case", "case_id"), []).append((terminal.name, case))

    entries = []
    for row in manifest["rows"]:
        case_id = row["case_id"]
        primary_path = directory / "cases" / f"{case_id}.json"
        retries = []
        for retry in sorted((directory / "cases" / case_id / "retries").glob("*.json")):
            retries.append(dict(retry_id=retry.stem, record=_verified(retry, row, verify_hash, lean)))
        if primary_path.exists():
            record, source = _verified(primary_path, row, verify_hash, lean), "primary_case_file"
        elif supervisor.get(case_id):
            record, source = supervisor[case_id][-1][1], "supervisor_terminal"
        else:
            record, source = None, "missing"
        entries.append(dict(row=row, record=record, record_source=source, retries=retries,
                            frozen_layout=(directory / "cases" / f"{case_id}.frozen.json").exists()))
    return dict(directory=str(directory), manifest=manifest, entries=entries,
                campaign=directory.name, stage=manifest["config"]["stage"])


def _verified(path, row, verify_hash, lean=False):
    record = _read(path)
    if verify_hash:
        expected = digest({k: v for k, v in record.items() if k != "artifact_hash"})
        if record.get("artifact_hash") != expected:
            raise ContractError("CORRUPT_ARTIFACT", f"{path.name} no longer matches its certificate")
        if record.get("case") != row:
            raise ContractError("CORRUPT_ARTIFACT", f"{path.name} belongs to another manifest row")
    return _strip(record) if lean else record


# --------------------------------------------------------------------------
# Flat case frame
# --------------------------------------------------------------------------

def case_frame(campaign):
    """One flat dict per authorized manifest row. Missing values stay None."""
    rows = []
    for entry in campaign["entries"]:
        rows.append(_case_row(campaign, entry["row"], entry["record"], entry["record_source"],
                              len(entry["retries"]), entry["frozen_layout"]))
    return rows


def _case_row(campaign, row, record, record_source, retry_count, frozen_layout):
    solve = _get(record, "solve_result") or {}
    validation = _get(record, "validation") or {}
    policy = _get(record, "policy_validation") or {}
    evaluation = _get(record, "evaluation") or {}
    reference = _get(record, "reference_evaluation") or {}
    native = _get(record, "native_attempt") or {}
    process = _get(native, "process") or {}
    provenance = _get(record, "solve_result_provenance") or {}

    status = _get(record, "status", default="MISSING_RECORD")
    scored = status in SCORED_STATUSES and bool(evaluation)
    out = OrderedDict()
    out.update(
        campaign=campaign["campaign"], stage=row["stage"], dataset_id=row["dataset_id"],
        catalogue_size=None, origin=row["origin"], n=row["n"], arm=row["arm"],
        delta=row["delta"], nu=row["nu"], tightening=row["tightening"], seed=row["seed"],
        rule=row.get("rule", "upper_only"),
        implementation_hash=_get(campaign, "manifest", "runtime", "implementation_hash"),
        backend=row["backend"], solve_mode=row["solve_mode"], time_limit=row["time_limit"],
        case_id=row["case_id"], solve_key=row["solve_key"], eligibility=row["eligibility"],
        record_source=record_source, retry_count=retry_count, frozen_layout=frozen_layout,
        status=status, scored=scored,
        # ---- solver / computational record -------------------------------
        allocation_returned=solve.get("assignment") is not None,
        native_status=solve.get("native_status"), solver_status=solve.get("status"),
        objective=solve.get("objective"), bound=solve.get("bound"), gap=solve.get("gap"),
        bound_provenance=solve.get("bound_provenance"),
        build_seconds=solve.get("build_seconds"), solve_seconds=solve.get("solve_seconds"),
        peak_rss_bytes=process.get("peak_rss_bytes"),
        process_status=process.get("status"), process_elapsed=process.get("elapsed_seconds"),
        reused_solve=provenance.get("reused"), attempt_id=provenance.get("attempt_id"),
        native_contradiction=_get(record, "native_contradiction", "kind"),
        scoring_error=_get(record, "scoring_error"),
        # ---- independent validation --------------------------------------
        validation_valid=validation.get("valid"),
        model_feasible=validation.get("model_feasible"),
        model_feasible_exact=validation.get("model_feasible_exact"),
        maximum_model_excess=_get(validation, "maximum_model_excess"),
        minimum_required_slack=_get(validation, "minimum_required_slack"),
        original_policy_feasible_exact=validation.get("original_policy_feasible_exact"),
        accepted_training_solution=_get(record, "accepted_training_solution"),
        policy_validation_valid=policy.get("valid") if policy else None,
        history_checked=validation.get("history_checked"),
        actual_visit_count=validation.get("actual_visit_count"),
    )
    out["catalogue_size"] = _catalogue_size(row["dataset_id"], evaluation)
    # ---- future evaluation (primary, same horizon) -----------------------
    if scored:
        out.update(
            joint_pass=evaluation.get("joint_pass"),
            violation_count=evaluation.get("violation_count"),
            cap_violation_count=evaluation.get("cap_violation_count"),
            floor_violation_count=evaluation.get("floor_violation_count"),
            worst_excess_pp=evaluation.get("worst_excess_percentage_points"),
            worst_excess_pp_exact=evaluation.get("worst_excess_percentage_points_exact"),
            positive_excess_sum=evaluation.get("positive_excess_sum"),
            maximum_residual=evaluation.get("maximum_residual"),
            borderline=evaluation.get("borderline"),
            mean_visits=evaluation.get("mean_visits"),
            mean_visits_exact=evaluation.get("mean_visits_exact"),
            visit_count=evaluation.get("visit_count"),
            historical_mean_visits=evaluation.get("historical_mean_visits"),
            historical_visit_count=evaluation.get("historical_visit_count"),
            future_total_lines=evaluation.get("total_lines"),
            future_order_count=evaluation.get("order_count"),
            activation_mass=evaluation.get("activation_mass"),
            activation_mass_exact=evaluation.get("activation_mass_exact"),
            effective_nu=evaluation.get("effective_nu"),
            inactive_product_count=evaluation.get("inactive_product_count"),
            realized_inactive_product_count=evaluation.get("realized_inactive_product_count"),
            active_product_fraction=evaluation.get("active_product_fraction"),
            horizon_per_product=evaluation.get("horizon_per_product"),
            station_novelty_count=evaluation.get("station_novelty_count"),
            maximum_novelty_excess=evaluation.get("maximum_novelty_excess"),
            novel_support_order_count=evaluation.get("novel_support_order_count"),
            effective_total_allowance=evaluation.get("effective_total_allowance"),
            layout_hash=evaluation.get("layout_hash"),
            future_hash=evaluation.get("future_hash"),
            stream_adjacency_verified=_get(evaluation, "future_boundaries", "stream_adjacency_verified"),
            station_count=len(evaluation.get("stations", []) or []),
            # ---- frozen incumbent on the same future, same fixed target ---
            reference_joint_pass=reference.get("joint_pass"),
            reference_violation_count=reference.get("violation_count"),
            reference_worst_excess_pp=reference.get("worst_excess_percentage_points"),
            reference_mean_visits=reference.get("mean_visits"),
            reference_visit_count=reference.get("visit_count"),
        )
    else:
        for key in ("joint_pass", "violation_count", "cap_violation_count", "floor_violation_count",
                    "worst_excess_pp", "worst_excess_pp_exact",
                    "positive_excess_sum", "maximum_residual", "borderline", "mean_visits",
                    "mean_visits_exact", "visit_count", "historical_mean_visits",
                    "historical_visit_count", "future_total_lines", "future_order_count",
                    "activation_mass", "activation_mass_exact", "effective_nu",
                    "inactive_product_count", "realized_inactive_product_count",
                    "active_product_fraction", "horizon_per_product", "station_novelty_count",
                    "maximum_novelty_excess", "novel_support_order_count",
                    "effective_total_allowance", "layout_hash", "future_hash",
                    "stream_adjacency_verified", "station_count", "reference_joint_pass",
                    "reference_violation_count", "reference_worst_excess_pp",
                    "reference_mean_visits", "reference_visit_count"):
            out[key] = MISSING
    return out


def _catalogue_size(dataset_id, evaluation):
    if dataset_id == "BERNER":
        return 21874
    try:
        return int(dataset_id.split("_")[1].replace("sku", ""))
    except (IndexError, ValueError):
        # Fall back only to a real array: under `lean` the product roster has
        # been replaced by a placeholder string, whose length means nothing.
        roster = evaluation.get("product_ids")
        return len(roster) if isinstance(roster, list) and roster else None


# --------------------------------------------------------------------------
# Status / accounting tables
# --------------------------------------------------------------------------

def status_table(frame):
    """Return-status breakdown with the authorized-row denominator intact."""
    per = {}
    for row in frame:
        key = (row["campaign"], row["rule"], row["stage"], row["dataset_id"], row["arm"], row["n"])
        bucket = per.setdefault(key, Counter())
        bucket["authorized_rows"] += 1
        bucket[f"status:{row['status']}"] += 1
        bucket["allocation_returned"] += bool(row["allocation_returned"])
        bucket["scored"] += bool(row["scored"])
        bucket["retries"] += row["retry_count"]
        if row["eligibility"]:
            bucket[f"ineligible:{row['eligibility']}"] += 1
    return [dict(campaign=k[0], rule=k[1], stage=k[2], dataset_id=k[3], arm=k[4], n=k[5],
                 **dict(sorted(v.items())))
            for k, v in sorted(per.items())]


def campaign_totals(frame):
    """Whole-campaign accounting; every authorized row lands in exactly one bin."""
    total = Counter()
    for row in frame:
        total["authorized_rows"] += 1
        if row["eligibility"]:
            total["ineligible"] += 1
        elif row["record_source"] == "missing":
            total["no_record"] += 1
        elif row["scored"]:
            total["scored"] += 1
        elif row["allocation_returned"]:
            total["allocation_but_unscored"] += 1
        else:
            total["no_allocation"] += 1
        total[f"status:{row['status']}"] += 1
    bins = ("ineligible", "no_record", "scored", "allocation_but_unscored", "no_allocation")
    total["accounted"] = sum(total[b] for b in bins)
    total["accounting_complete"] = int(total["accounted"] == total["authorized_rows"])
    return dict(sorted(total.items()))


# --------------------------------------------------------------------------
# Paired comparison
# --------------------------------------------------------------------------

PAIR_METRICS = ("joint_pass", "violation_count", "worst_excess_pp", "mean_visits",
                "positive_excess_sum", "activation_mass", "station_novelty_count")

# Sign of a paired difference (arm minus baseline) that counts as "better".
# +1: higher is better; -1: lower is better; None: descriptive, no direction.
# joint_pass is a success indicator, so a POSITIVE difference is the good one;
# the earlier code counted every negative difference as better, which reversed
# that one metric.
METRIC_DIRECTION = {"joint_pass": +1, "violation_count": -1, "worst_excess_pp": -1,
                    "mean_visits": -1, "positive_excess_sum": -1,
                    "activation_mass": None, "station_novelty_count": -1}


def paired_rows(frame, *, baselines=("NOM", "TIGHT")):
    """Pair every arm against each baseline inside one exactly matched cell.

    A cell is (dataset, origin, n, seed, delta, nu, tightening, solve_mode).
    A pair exists only when BOTH members produced a scored evaluation; the
    number of complete and incomplete pairs is reported alongside.
    """
    # The campaign is part of the cell identity. Two campaigns can hold the same
    # (dataset, origin, n, seed, parameter) cell under DIFFERENT implementation
    # versions, and merging them would both mix versions and let a later
    # campaign's not-yet-executed row silently overwrite an earlier real result.
    cells = {}
    for row in frame:
        key = (row["campaign"], row["rule"], row["dataset_id"], row["origin"], row["n"], row["seed"],
               row["delta"], row["nu"], row["tightening"], row["solve_mode"])
        cells.setdefault(key, {})[row["arm"]] = row
    out = []
    for key, arms in sorted(cells.items()):
        for baseline in baselines:
            base = arms.get(baseline)
            for arm, row in sorted(arms.items()):
                if arm == baseline or base is None:
                    continue
                pair = OrderedDict(zip(("campaign", "rule", "dataset_id", "origin", "n", "seed",
                                        "delta", "nu", "tightening", "solve_mode"), key))
                pair.update(catalogue_size=row["catalogue_size"], baseline=baseline, arm=arm,
                            both_scored=bool(row["scored"] and base["scored"]),
                            arm_status=row["status"], baseline_status=base["status"])
                for metric in PAIR_METRICS:
                    a, b = row[metric], base[metric]
                    pair[f"{metric}_arm"] = a
                    pair[f"{metric}_baseline"] = b
                    pair[f"{metric}_diff"] = (float(a) - float(b)) if (a is not None and b is not None) else MISSING
                if pair["mean_visits_baseline"]:
                    pair["visit_cost_pct"] = 100.0 * pair["mean_visits_diff"] / float(pair["mean_visits_baseline"]) \
                        if pair["mean_visits_diff"] is not None else MISSING
                else:
                    pair["visit_cost_pct"] = MISSING
                out.append(pair)
    return out


def instance_summary(frame, *, metrics=PAIR_METRICS):
    """Level 2: average within a dataset across origins and seeds.

    Horizons stay separate because nested windows at one origin are correlated.
    """
    groups = {}
    for row in frame:
        # Ineligible cells stay in their group with an explicit count. Skipping
        # them would delete a (dataset, horizon) combination from the table
        # entirely, which is exactly the silent omission the protocol forbids.
        groups.setdefault((row["campaign"], row["rule"], row["dataset_id"], row["n"], row["arm"],
                           row["delta"], row["nu"], row["tightening"], row["solve_mode"]), []).append(row)
    out = []
    for key, rows in sorted(groups.items()):
        scored = [r for r in rows if r["scored"]]
        entry = OrderedDict(zip(("campaign", "rule", "dataset_id", "n", "arm", "delta", "nu",
                                 "tightening", "solve_mode"), key))
        entry.update(catalogue_size=rows[0]["catalogue_size"], cells=len(rows), scored_cells=len(scored),
                     ineligible_cells=sum(1 for r in rows if r["eligibility"]),
                     eligibility_reasons=";".join(sorted({r["eligibility"] for r in rows if r["eligibility"]})) or None,
                     allocation_returned=sum(bool(r["allocation_returned"]) for r in rows),
                     distinct_origins=len({r["origin"] for r in rows}),
                     distinct_seeds=len({r["seed"] for r in rows}))
        for metric in metrics:
            values = [float(r[metric]) for r in scored if r[metric] is not None]
            entry[f"{metric}_mean"] = statistics.fmean(values) if values else MISSING
            entry[f"{metric}_n"] = len(values)
        entry["joint_pass_count"] = sum(1 for r in scored if r["joint_pass"])
        out.append(entry)
    return out


def horizon_multiple(n, catalogue_size):
    """Exact n/P label. Integer division would collapse the n = P/2 horizon to 0."""
    if not catalogue_size:
        return None
    return str(Fraction(n, catalogue_size))


def stratum_summary(instances):
    """Level 3: across instances of one catalogue size. Instances are the unit."""
    groups = {}
    for row in instances:
        groups.setdefault((row["campaign"], row["catalogue_size"],
                           horizon_multiple(row["n"], row["catalogue_size"]),
                           row["arm"], row["delta"], row["nu"], row["tightening"],
                           row["solve_mode"]), []).append(row)
    out = []
    for key, rows in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0, float(Fraction(kv[0][2])) if kv[0][2] else 0.0, ARM_ORDER.index(kv[0][3]) if kv[0][3] in ARM_ORDER else 9)):
        entry = OrderedDict(campaign=key[0], catalogue_size=key[1], horizon_multiple=key[2],
                            arm=key[3], delta=key[4], nu=key[5], tightening=key[6],
                            solve_mode=key[7],
                            instances=len(rows),
                            instances_with_any_scored_cell=sum(1 for r in rows if r["scored_cells"]),
                            total_cells=sum(r["cells"] for r in rows),
                            total_scored_cells=sum(r["scored_cells"] for r in rows),
                            instances_all_cells_joint_pass=sum(
                                1 for r in rows if r["scored_cells"] and r["joint_pass_count"] == r["scored_cells"]))
        for metric in ("joint_pass", "worst_excess_pp", "mean_visits", "violation_count", "activation_mass"):
            values = [r[f"{metric}_mean"] for r in rows if r[f"{metric}_mean"] is not None]
            entry[f"{metric}_instance_mean"] = statistics.fmean(values) if values else MISSING
            entry[f"{metric}_instance_median"] = statistics.median(values) if values else MISSING
            entry[f"{metric}_instances"] = len(values)
        out.append(entry)
    return out


def paired_stratum_summary(pairs):
    """Paired differences aggregated with the instance as the unit of analysis."""
    per_instance = {}
    for pair in pairs:
        if not pair["both_scored"]:
            continue
        key = (pair["campaign"], pair["catalogue_size"], pair["n"], pair["baseline"], pair["arm"],
               pair["delta"], pair["nu"], pair["tightening"], pair["solve_mode"], pair["dataset_id"])
        per_instance.setdefault(key, []).append(pair)
    collapsed = {}
    for key, group in per_instance.items():
        stratum, dataset = key[:-1], key[-1]
        entry = collapsed.setdefault(stratum, [])
        row = {"dataset_id": dataset}
        for metric in PAIR_METRICS:
            values = [p[f"{metric}_diff"] for p in group if p[f"{metric}_diff"] is not None]
            row[metric] = statistics.fmean(values) if values else None
        entry.append(row)
    out = []
    for stratum, rows in sorted(collapsed.items(), key=lambda kv: (kv[0][0], kv[0][1] or 0, kv[0][2])):
        entry = OrderedDict(zip(("campaign", "catalogue_size", "n", "baseline", "arm", "delta",
                                 "nu", "tightening", "solve_mode"), stratum))
        entry["paired_instances"] = len(rows)
        for metric in PAIR_METRICS:
            values = [r[metric] for r in rows if r[metric] is not None]
            entry[f"{metric}_mean_diff"] = statistics.fmean(values) if values else MISSING
            entry[f"{metric}_median_diff"] = statistics.median(values) if values else MISSING
            direction = METRIC_DIRECTION[metric]
            if direction is None:
                # Descriptive quantity: a difference has no better/worse reading.
                entry[f"{metric}_instances_better"] = MISSING
                entry[f"{metric}_instances_worse"] = MISSING
            else:
                # "better" means the arm moved the metric in its good direction.
                entry[f"{metric}_instances_better"] = sum(1 for v in values if v * direction > 0)
                entry[f"{metric}_instances_worse"] = sum(1 for v in values if v * direction < 0)
            entry[f"{metric}_instances_equal"] = sum(1 for v in values if v == 0)
            entry[f"{metric}_paired_n"] = len(values)
        out.append(entry)
    return out


# --------------------------------------------------------------------------
# Frontiers and diagnostics
# --------------------------------------------------------------------------

def frontier_table(frame, axis):
    """Tolerance / activation / tightening frontier, retaining every case.

    ``axis`` is 'delta', 'nu' or 'tightening'. Infeasible, unresolved and
    missing-allocation cases keep their own bins; nothing is filtered out.
    """
    if axis not in ("delta", "nu", "tightening"):
        raise ContractError("DATA_CONTRACT_ERROR", "unknown frontier axis")
    groups = {}
    for row in frame:
        groups.setdefault((row["campaign"], row["rule"], row["dataset_id"], row["n"], row["arm"], row[axis]), []).append(row)
    out = []
    for key, rows in sorted(groups.items(), key=lambda kv: (*kv[0][:5], Fraction(kv[0][5]))):
        head = OrderedDict(campaign=key[0], rule=key[1], dataset_id=key[2], n=key[3], arm=key[4])
        out.append(_frontier_entry(head, rows, axis, key[5]))
    return out


def rule_frontier_table(frame, axis):
    """Frontier pooled ACROSS campaigns, but only inside one (rule, implementation hash).

    Exploratory revision 2 ran each two-sided delta value as its own campaign, so
    the predeclared side-by-side delta comparison needs rows from several
    campaigns in one table. Pooling is permitted only when the rows share the
    rule AND the implementation hash; different implementation versions and
    different rules stay on separate rows, and every row names the campaigns
    it merged so nothing is pooled silently.
    """
    if axis not in ("delta", "nu", "tightening"):
        raise ContractError("DATA_CONTRACT_ERROR", "unknown frontier axis")
    groups = {}
    for row in frame:
        key = (row["rule"], row["implementation_hash"], row["dataset_id"], row["n"], row["arm"], row[axis])
        groups.setdefault(key, []).append(row)
    out = []
    for key, rows in sorted(groups.items(), key=lambda kv: (*(str(k) for k in kv[0][:5]), Fraction(kv[0][5]))):
        names = sorted({r["campaign"] for r in rows})
        head = OrderedDict(rule=key[0], implementation_hash=key[1], campaigns="+".join(names),
                           campaign_count=len(names), dataset_id=key[2], n=key[3], arm=key[4])
        out.append(_frontier_entry(head, rows, axis, key[5]))
    return out


def _frontier_entry(head, rows, axis, value):
    scored = [r for r in rows if r["scored"]]
    entry = OrderedDict(head)
    entry.update(axis=axis, value=value,
                 catalogue_size=rows[0]["catalogue_size"], cells=len(rows),
                 scored_cells=len(scored),
                 no_allocation=sum(1 for r in rows if not r["allocation_returned"] and not r["eligibility"]),
                 ineligible=sum(1 for r in rows if r["eligibility"]),
                 rejected_candidates=sum(1 for r in rows if r["status"] == "REJECTED_CANDIDATE"),
                 proven_infeasible=sum(1 for r in rows if r["solver_status"] == "PROVEN_INFEASIBLE"),
                 no_incumbent=sum(1 for r in rows if r["solver_status"] == "NO_INCUMBENT_LIMIT"),
                 joint_pass=sum(1 for r in scored if r["joint_pass"]))
    for metric in ("worst_excess_pp", "mean_visits", "activation_mass", "minimum_required_slack"):
        values = [float(r[metric]) for r in rows if r[metric] is not None]
        entry[f"{metric}_mean"] = statistics.fmean(values) if values else MISSING
        entry[f"{metric}_n"] = len(values)
    return entry


def min_slack_table(frame):
    """delta_min diagnostic: bounds with explicit resolved/unresolved status.

    An upper bound comes from a validated layout's own required slack; a lower
    bound comes only from a solver bound with stated provenance. A time limit
    without both is UNRESOLVED, never an infeasibility proof.
    """
    out = []
    for row in frame:
        if row["solve_mode"] != "min_slack":
            continue
        upper = row["minimum_required_slack"] if row["validation_valid"] else None
        lower = row["bound"] if row["bound_provenance"] not in (None, "unavailable") else None
        # eta >= 0 holds by construction, so a bound of 0 carries no information.
        # Hexaly reports exactly that, and calling it "BOUNDED" would overstate the
        # diagnostic: only a strictly positive certified bound can restrict delta_min.
        informative_lower = lower is not None and lower > 0
        if upper is not None and informative_lower:
            resolution = "BOUNDED" if lower <= upper + 1e-9 else "INCONSISTENT_BOUNDS"
        elif upper is not None:
            resolution = "UPPER_BOUND_ONLY"
        elif informative_lower:
            resolution = "LOWER_BOUND_ONLY"
        else:
            resolution = "UNRESOLVED"
        declared = float(Fraction(row["delta"]))
        out.append(OrderedDict(
            campaign=row["campaign"], rule=row["rule"],
            dataset_id=row["dataset_id"], catalogue_size=row["catalogue_size"], origin=row["origin"],
            n=row["n"], arm=row["arm"], nu=row["nu"], seed=row["seed"], status=row["status"],
            solver_status=row["solver_status"], native_status=row["native_status"],
            declared_delta=declared, eta_upper_bound=upper, eta_lower_bound=lower,
            bound_provenance=row["bound_provenance"], resolution=resolution,
            exceeds_declared_delta=(lower > declared) if lower is not None else MISSING,
            layout_meets_declared_delta=(upper <= declared) if upper is not None else MISSING,
            solve_seconds=row["solve_seconds"], gap=row["gap"]))
    return out


def station_table(campaign, *, dataset_ids=None, aliases=None):
    """Station-level target / future share / decrease rows for scored cases.

    ``aliases`` maps internal station IDs to publication labels. Internal
    industrial codes are replaced when an alias exists; a missing alias raises
    rather than leaking a site code into a published table.
    """
    out = []
    for entry in campaign["entries"]:
        row, record = entry["row"], entry["record"]
        if dataset_ids is not None and row["dataset_id"] not in dataset_ids:
            continue
        evaluation = _get(record, "evaluation") or {}
        if not evaluation.get("stations"):
            continue
        for station in evaluation["stations"]:
            label = station["station_id"]
            if aliases is not None:
                if label not in aliases:
                    raise ContractError("DATA_CONTRACT_ERROR", "station has no publication alias")
                label = aliases[label]
            out.append(OrderedDict(
                dataset_id=row["dataset_id"], origin=row["origin"], n=row["n"], arm=row["arm"],
                seed=row["seed"], delta=row["delta"], nu=row["nu"], rule=row.get("rule", "upper_only"),
                station=label, station_index=station["station_index"],
                capacity=station["capacity"], occupancy=station["occupancy"],
                target=station["target"], cap=station["cap"], future_share=station["share"],
                residual=station["residual"], positive_excess=station["positive_excess"],
                floor=station.get("floor"), floor_residual=station.get("floor_residual"),
                below_floor=station.get("below_floor"),
                decrease=station["decrease"], implied_lower_bound=station["implied_lower_bound"],
                historical_share=station["historical_share"],
                fixed_share=station["fixed_share"],
                fixed_historical_share=station["fixed_historical_share"],
                inactive_count=station["inactive_count"], inactive_share=station["inactive_share"],
                worst_modelled_share=station["worst_share"],
                novelty_residual=station["novelty_residual"],
                beyond_worst_scenario=station["beyond_worst_scenario"],
                feasible=station["feasible"], borderline=station["borderline"],
                cap_relative_to_target=station["cap_relative_to_target"]))
    return out


def resource_table(frame):
    """Build/solve time and memory, including cases with no returned layout."""
    return [OrderedDict(
        campaign=r["campaign"], rule=r["rule"],
        dataset_id=r["dataset_id"], catalogue_size=r["catalogue_size"], n=r["n"], arm=r["arm"],
        seed=r["seed"], solve_mode=r["solve_mode"], status=r["status"],
        native_status=r["native_status"], solver_status=r["solver_status"],
        configured_time_limit=r["time_limit"], build_seconds=r["build_seconds"],
        solve_seconds=r["solve_seconds"], process_elapsed=r["process_elapsed"],
        process_status=r["process_status"], peak_rss_bytes=r["peak_rss_bytes"],
        peak_rss_gib=(r["peak_rss_bytes"] / 1024 ** 3) if r["peak_rss_bytes"] else MISSING,
        reused_solve=r["reused_solve"], objective=r["objective"], bound=r["bound"], gap=r["gap"],
        used_full_cap=((r["solve_seconds"] is not None and r["time_limit"] and
                        r["solve_seconds"] >= 0.95 * r["time_limit"]) if r["solve_seconds"] is not None else MISSING))
        for r in frame]


# --------------------------------------------------------------------------
# Cross-horizon transfer (no new optimization)
# --------------------------------------------------------------------------

def cross_horizon_table(records):
    """Flatten stored secondary-horizon evaluations of already frozen layouts."""
    out = []
    for record in records:
        evaluation = record["evaluation"]
        out.append(OrderedDict(
            campaign=record.get("campaign"), rule=record.get("rule", "upper_only"),
            dataset_id=record["dataset_id"], catalogue_size=record.get("catalogue_size"),
            origin=record["origin"], arm=record["arm"], seed=record["seed"],
            trained_n=record["trained_n"], scored_n=record["scored_n"],
            trained_multiple=horizon_multiple(record["trained_n"], record.get("catalogue_size")),
            scored_multiple=horizon_multiple(record["scored_n"], record.get("catalogue_size")),
            same_horizon=record["trained_n"] == record["scored_n"],
            evaluation_kind=evaluation["evaluation_kind"],
            layout_hash=evaluation["layout_hash"], future_hash=evaluation["future_hash"],
            joint_pass=evaluation["joint_pass"], violation_count=evaluation["violation_count"],
            cap_violation_count=evaluation.get("cap_violation_count"),
            floor_violation_count=evaluation.get("floor_violation_count"),
            worst_excess_pp=evaluation["worst_excess_percentage_points"],
            positive_excess_sum=evaluation["positive_excess_sum"],
            mean_visits=evaluation["mean_visits"], visit_count=evaluation["visit_count"],
            activation_mass=evaluation["activation_mass"],
            station_novelty_count=evaluation["station_novelty_count"],
            active_product_fraction=evaluation["active_product_fraction"],
            source_case_id=record["source_case_id"]))
    return out


# --------------------------------------------------------------------------
# Serialization
# --------------------------------------------------------------------------

def write_csv(rows, path):
    """Deterministic CSV over the union of keys, in first-seen order."""
    import csv

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: ("" if row.get(k) is None else row.get(k)) for k in fields})
    return dict(path=str(path), rows=len(rows), columns=len(fields),
                sha256=digest([[("" if r.get(k) is None else r.get(k)) for k in fields] for r in rows]))


def write_markdown(rows, path, *, columns=None, title="", note=""):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = columns or (list(rows[0]) if rows else [])
    lines = ([f"# {title}", ""] if title else []) + ([note, ""] if note else [])
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("|" + "|".join("---" for _ in columns) + "|")
    for row in rows:
        cells = []
        for column in columns:
            value = row.get(column)
            if value is None:
                cells.append("—")
            elif isinstance(value, float):
                cells.append(f"{value:.6g}")
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dict(path=str(path), rows=len(rows), columns=len(columns))
