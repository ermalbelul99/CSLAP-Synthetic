"""Independent accounting/authorization/revalidation checks over campaigns.

Run from the repository root with the approved CPLEX interpreter:

    C:\\ermal\\Virtual_Environment_CPLEX_1\\Scripts\\python.exe \\
        tools/horizon_robustness/verify_campaign.py --all

Every assertion is performed here, and the success marker is printed only after
all of them pass. Any failure exits nonzero with the failing detail, so the
marker cannot appear on a partially checked campaign.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from Baselines.horizon_robustness_analysis.analysis import (  # noqa: E402
    campaign_totals, case_frame, load_campaign)
from Baselines.horizon_robustness.orders import complete_window  # noqa: E402
from Baselines.horizon_robustness.protocol import (  # noqa: E402
    ARMS,
    ContractError, Protocol, allowed_source, digest)
from Baselines.horizon_robustness.runner import _load_dataset  # noqa: E402
from Baselines.horizon_robustness.schema import SolveResult  # noqa: E402
from Baselines.horizon_robustness.uncertainty import build_training_problem  # noqa: E402
from Baselines.horizon_robustness.validation import validate_assignment  # noqa: E402

CAMPAIGN_ROOT = ROOT / "reports" / "horizon_robustness_results" / "campaigns"
APPROVED_DATASET = re.compile(r"^(BERNER|syn_(50|500|1000|2000)sku_seed\d+)$")


class CheckFailure(AssertionError):
    pass


def require(condition, message):
    if not condition:
        raise CheckFailure(message)


def campaign_directories(selection=None):
    if selection:
        # Accept either a path or a bare campaign name under the campaigns root;
        # a missing manifest is reported as such, never as a corrupt artifact.
        candidate = Path(selection)
        if not (candidate / "manifest.json").exists():
            candidate = CAMPAIGN_ROOT / selection
        if not (candidate / "manifest.json").exists():
            raise CheckFailure(f"no campaign manifest at {selection!r} or under {CAMPAIGN_ROOT}")
        return [candidate]
    return sorted(p.parent for p in CAMPAIGN_ROOT.glob("*/manifest.json"))


# --------------------------------------------------------------------------

def check_accounting(directory, *, partial=False):
    """A24: every authorized row resolves to a result or an explicit record.

    ``partial`` tolerates rows a still-running or deliberately handed-off
    campaign has not reached yet. It reports their exact count and makes the
    campaign's incompleteness visible; it never lets an incomplete campaign
    print the strict success marker, so the E2 gate stays unmet until the
    campaign really is fully accounted for.
    """
    campaign = load_campaign(directory)
    frame = case_frame(campaign)
    totals = campaign_totals(frame)
    manifest = campaign["manifest"]
    policy = Protocol()

    require(len(frame) == len(manifest["rows"]),
            f"{directory.name}: frame rows {len(frame)} != manifest rows {len(manifest['rows'])}")
    require(totals["accounting_complete"] == 1,
            f"{directory.name}: {totals['accounted']} of {totals['authorized_rows']} rows accounted")

    for row in manifest["rows"]:
        require(APPROVED_DATASET.match(row["dataset_id"]),
                f"{directory.name}: unapproved dataset {row['dataset_id']}")
        require(row["delta"] in policy.deltas, f"{directory.name}: delta {row['delta']} outside grid")
        require(row["nu"] in policy.nus, f"{directory.name}: nu {row['nu']} outside grid")
        require(row["tightening"] in policy.tightening,
                f"{directory.name}: lambda {row['tightening']} outside grid")
        require(row["seed"] in policy.seeds, f"{directory.name}: seed {row['seed']} outside grid")
        require(row["arm"] in ARMS,      # the protocol's arm set; HIST+ACT-T since revision 3
                f"{directory.name}: unknown arm {row['arm']}")
        for source in row["source_files"]:
            allowed_source(source["path"], ROOT)

    for entry in campaign["entries"]:
        status = (entry["record"] or {}).get("status")
        require(entry["record"] is not None or entry["row"]["eligibility"] or partial,
                f"{directory.name}: row {entry['row']['case_id'][:12]} has no record at all")
        if status in ("COMPLETE", "DIAGNOSTIC_COMPLETE"):
            require(entry["frozen_layout"],
                    f"{directory.name}: scored case {entry['row']['case_id'][:12]} has no frozen layout")
        if entry["row"]["eligibility"]:
            require(status == entry["row"]["eligibility"],
                    f"{directory.name}: ineligible row status {status} != {entry['row']['eligibility']}")

    # A failed or limited solve must never be recorded as a zero-valued result.
    for row in frame:
        if not row["allocation_returned"]:
            for metric in ("joint_pass", "mean_visits", "worst_excess_pp", "violation_count"):
                require(row[metric] is None,
                        f"{directory.name}: unallocated row carries a {metric} value")
    return dict(campaign=directory.name, totals=totals, rows=len(frame),
                not_yet_executed=totals.get("no_record", 0))


def check_authorization(directory):
    """Executed invocations match an approved manifest hash and its ceilings."""
    campaign = load_campaign(directory)
    manifest_hash = campaign["manifest"]["manifest_hash"]
    quoted = campaign["manifest"]["solver_seconds"]
    started = sorted((directory / "invocations").glob("*.started.json"))
    finished = sorted((directory / "invocations").glob("*.finished.json"))
    require(started, f"{directory.name}: no invocation record")
    charged_total = 0
    for path in started:
        record = json.loads(path.read_text(encoding="utf-8-sig"))
        require(record["approved_manifest_hash"] == manifest_hash,
                f"{directory.name}: invocation used a different manifest hash")
        require(record["solver_budget_seconds"] >= quoted,
                f"{directory.name}: invocation budget below the quoted native caps")
        if record.get("retry_id") is not None:
            require(record.get("retry_reason"),
                    f"{directory.name}: retry {record['retry_id']} has no recorded reason")
    for path in finished:
        record = json.loads(path.read_text(encoding="utf-8-sig"))
        require(record["approved_manifest_hash"] == manifest_hash,
                f"{directory.name}: finished record has a different manifest hash")
        charged_total += record["charged_native_cap_seconds"]
        require(record["charged_native_cap_seconds"] <= quoted,
                f"{directory.name}: charged {record['charged_native_cap_seconds']}s exceeds quote {quoted}s")
    for path in sorted((directory / "supervision").glob("*/request.json")):
        record = json.loads(path.read_text(encoding="utf-8-sig"))
        require(record["manifest"]["manifest_hash"] == manifest_hash,
                f"{directory.name}: supervisor ran another manifest")
        require(record["options"]["approved_manifest_hash"] == manifest_hash,
                f"{directory.name}: supervisor approval hash mismatch")
    return dict(campaign=directory.name, invocations=len(started), finished=len(finished),
                quoted_solver_seconds=quoted, charged_native_cap_seconds=charged_total)


def check_revalidation(directory, *, datasets=None):
    """A23/A20: recompute each accepted layout's certificate from raw history.

    The stored assignment is revalidated against a freshly rebuilt training
    problem, and the frozen layout certificate must predate and match the
    scored evaluation.
    """
    campaign = load_campaign(directory)
    demands, checked, skipped = {}, 0, 0
    for entry in campaign["entries"]:
        row, record = entry["row"], entry["record"]
        if record is None or record.get("status") not in ("COMPLETE", "DIAGNOSTIC_COMPLETE"):
            continue
        if datasets and row["dataset_id"] not in datasets:
            skipped += 1
            continue
        frozen = json.loads((Path(directory) / "cases" / f"{row['case_id']}.frozen.json")
                            .read_text(encoding="utf-8-sig"))
        solved = SolveResult.from_dict(record["solve_result"])
        assignment = tuple(solved.assignment)
        require(list(assignment) == frozen["assignment"],
                f"{directory.name}: frozen layout differs from the case result")
        require(digest(assignment) == frozen["layout_hash"],
                f"{directory.name}: frozen layout hash does not match its assignment")
        require(frozen["input_hash"] == row["input_hash"],
                f"{directory.name}: frozen certificate belongs to another model")
        if row["dataset_id"] not in demands:
            demands[row["dataset_id"]] = _load_dataset(row["dataset_id"], ROOT)
        demand = demands[row["dataset_id"]]
        history = complete_window(demand.orders, 0, row["origin"])
        problem = build_training_problem(demand.catalogue, history, row["n"], row["arm"],
                                         row["delta"], row["nu"], row["tightening"],
                                         rule=row.get("rule", "upper_only"))
        require(problem.input_hash == row["input_hash"],
                f"{directory.name}: rebuilt problem differs from the quoted model")
        fresh = validate_assignment(problem, assignment, objective=solved.objective,
                                    solve_mode=row["solve_mode"], history=history)
        require(fresh["valid"], f"{directory.name}: independent revalidation rejected an accepted layout: "
                                f"{fresh['violations'][:3]}")
        require(fresh["actual_visit_count"] == record["validation"]["actual_visit_count"],
                f"{directory.name}: recomputed visit count differs from the stored certificate")
        require(fresh["maximum_model_residual_exact"] == record["validation"]["maximum_model_residual_exact"],
                f"{directory.name}: recomputed model residual differs from the stored certificate")
        evaluation = record.get("evaluation")
        if evaluation:
            require(evaluation["layout_hash"] and evaluation["assignment"] == list(assignment),
                    f"{directory.name}: evaluated layout differs from the frozen layout")
            require(evaluation["future_boundaries"]["stream_adjacency_verified"] is True,
                    f"{directory.name}: future segment adjacency was never verified")
            require(evaluation["future_boundaries"]["start"] == row["origin"],
                    f"{directory.name}: future window does not start at the origin")
        checked += 1
    return dict(campaign=directory.name, revalidated=checked, skipped=skipped)


# --------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", help="one campaign directory; default is every campaign")
    parser.add_argument("--all", action="store_true", help="accounting check (E2:G1)")
    parser.add_argument("--authorization", action="store_true", help="authorization check (E2:G2)")
    parser.add_argument("--revalidate", action="store_true", help="independent revalidation (E2:G3)")
    parser.add_argument("--datasets", nargs="+", help="restrict revalidation to these dataset IDs")
    parser.add_argument("--partial", action="store_true",
                        help="tolerate rows a running or handed-off campaign has not reached; "
                             "reports their count and withholds the strict success marker")
    args = parser.parse_args(argv)
    if not (args.all or args.authorization or args.revalidate):
        parser.error("choose at least one check")

    try:
        directories = campaign_directories(args.campaign)
    except CheckFailure as exc:
        print(f"CHECK FAILED: {exc}", file=sys.stderr)
        return 1
    if not directories:
        print("NO CAMPAIGN FOUND", file=sys.stderr)
        return 1
    try:
        if args.all:
            outstanding = 0
            for directory in directories:
                summary = check_accounting(directory, partial=args.partial)
                outstanding += summary["not_yet_executed"]
                print(json.dumps(summary, sort_keys=True))
            if outstanding:
                # Deliberately NOT the strict marker: an incomplete campaign must
                # not be able to satisfy the E2 accounting gate.
                print(f"CAMPAIGN ACCOUNTING INCOMPLETE: {outstanding} authorized row(s) not yet "
                      f"executed across {len(directories)} campaign(s); every other row is accounted for")
            else:
                print(f"CAMPAIGN ACCOUNTING VERIFIED ({len(directories)} campaign(s))")
        if args.authorization:
            for directory in directories:
                print(json.dumps(check_authorization(directory), sort_keys=True))
            print(f"AUTHORIZATION VERIFIED ({len(directories)} campaign(s))")
        if args.revalidate:
            for directory in directories:
                print(json.dumps(check_revalidation(directory, datasets=args.datasets), sort_keys=True))
            print(f"INDEPENDENT REVALIDATION VERIFIED ({len(directories)} campaign(s))")
    except (CheckFailure, ContractError) as exc:
        print(f"CHECK FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
