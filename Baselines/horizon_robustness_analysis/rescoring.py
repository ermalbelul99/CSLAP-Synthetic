"""Cross-horizon scoring of layouts that are already frozen. No optimization.

A layout trained for horizon n is scored on the other declared horizons m at
the SAME origin, using that row's own reference target b and its own ceiling
u = min(1, b + delta). Nothing here re-solves, repairs a layout, resets b or
enlarges delta/nu. Every produced record is a secondary cross-horizon
evaluation and is never substituted for primary same-horizon scoring.

The transfer result shows how a horizon-specific layout behaves on a different
future length. It does not certify those horizons and must not be used to pick
a winning n after its future has been seen.
"""

from __future__ import annotations

import json
from pathlib import Path

from Baselines.horizon_robustness.metrics import evaluate_layout
from Baselines.horizon_robustness.orders import complete_window
from Baselines.horizon_robustness.protocol import ContractError, REPO_ROOT, canonical_json, digest, horizon_grid
from Baselines.horizon_robustness.runner import _load_dataset, _write_new
from Baselines.horizon_robustness.uncertainty import build_training_problem


ARTIFACT_DIR = "cross_horizon"


def _read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as exc:
        raise ContractError("CORRUPT_ARTIFACT", str(path)) from exc


def plan_cross_horizon(manifest):
    """Enumerate (row, secondary horizon) work without touching any data.

    Only eligible primary rows contribute. The secondary grid is the declared
    horizon grid of that dataset's full catalogue, excluding the trained n.
    """
    plan = []
    for row in manifest["rows"]:
        if row["eligibility"] or row["solve_mode"] != "visits":
            continue
        for horizon in horizon_grid(_catalogue_size(row)):
            if horizon != row["n"]:
                plan.append(dict(case_id=row["case_id"], trained_n=row["n"], scored_n=horizon))
    return plan


def _catalogue_size(row):
    if row["dataset_id"] == "BERNER":
        return 21874
    return int(row["dataset_id"].split("_")[1].replace("sku", ""))


def score_campaign(directory, *, root=REPO_ROOT, loader=None, horizons=None, limit=None):
    """Score every frozen layout on the other declared horizons at its origin.

    Existing artifacts are reused, never rewritten. A horizon whose future
    window does not exist in the source stream is recorded as
    INSUFFICIENT_FUTURE rather than silently skipped.
    """
    directory = Path(directory)
    manifest = _read(directory / "manifest.json")
    loader = _load_dataset if loader is None else loader
    output = directory / ARTIFACT_DIR
    cache, demands, produced = {}, {}, []

    for row in manifest["rows"]:
        if row["eligibility"] or row["solve_mode"] != "visits":
            continue
        frozen_path = directory / "cases" / f"{row['case_id']}.frozen.json"
        case_path = directory / "cases" / f"{row['case_id']}.json"
        if not frozen_path.exists() or not case_path.exists():
            continue
        frozen, case = _read(frozen_path), _read(case_path)
        if case.get("status") != "COMPLETE":
            continue
        assignment = tuple(frozen["assignment"])
        if digest(assignment) != frozen["layout_hash"] or frozen["case_id"] != row["case_id"]:
            raise ContractError("CORRUPT_ARTIFACT", "frozen layout certificate is inconsistent")
        if list(assignment) != case["solve_result"]["assignment"]:
            raise ContractError("CORRUPT_ARTIFACT", "frozen layout differs from its case result")

        grid = horizons if horizons is not None else horizon_grid(_catalogue_size(row))
        targets = [h for h in grid if h != row["n"]]
        if not targets:
            continue
        if row["dataset_id"] not in demands:
            demands[row["dataset_id"]] = loader(row["dataset_id"], root)
        demand = demands[row["dataset_id"]]
        key = (row["dataset_id"], row["origin"], row["n"], row["arm"], row["delta"], row["nu"], row["tightening"],
               row.get("rule", "upper_only"))
        if key not in cache:
            history = complete_window(demand.orders, 0, row["origin"])
            problem = build_training_problem(demand.catalogue, history, row["n"], row["arm"],
                                             row["delta"], row["nu"], row["tightening"],
                                             rule=row.get("rule", "upper_only"))
            if problem.input_hash != row["input_hash"]:
                raise ContractError("REBUILT_INPUT_CHANGED", "rebuilt problem differs from the frozen quote")
            cache[key] = problem
        problem = cache[key]

        for horizon in targets:
            path = output / f"{row['case_id']}__n{horizon}.json"
            if path.exists():
                produced.append(_read(path))
                continue
            record = dict(source_case_id=row["case_id"], dataset_id=row["dataset_id"],
                          catalogue_size=_catalogue_size(row), origin=row["origin"], arm=row["arm"],
                          seed=row["seed"], delta=row["delta"], nu=row["nu"],
                          tightening=row["tightening"], rule=row.get("rule", "upper_only"),
                          trained_n=row["n"], scored_n=horizon,
                          layout_hash=frozen["layout_hash"], input_hash=row["input_hash"],
                          manifest_hash=manifest["manifest_hash"],
                          evaluation=None, status="PENDING")
            stop = row["origin"] + horizon
            if stop > len(demand.orders):
                record["status"] = "INSUFFICIENT_FUTURE"
            else:
                future = complete_window(demand.orders, row["origin"], stop)
                history = complete_window(demand.orders, 0, row["origin"])
                if len(future) != horizon or future[0].chronology_key <= history[-1].chronology_key:
                    raise ContractError("SOURCE_ADJACENCY", "secondary future is not the exact next segment")
                evaluation = evaluate_layout(problem, assignment, future, horizon=horizon)
                if evaluation["evaluation_kind"] != "secondary_cross_horizon":
                    raise ContractError("DATA_CONTRACT_ERROR", "cross-horizon record is not marked secondary")
                evaluation["future_boundaries"].update(
                    stream_adjacency_verified=True,
                    membership_provenance="verified_exact_slice_of_rebuilt_source_stream")
                record.update(evaluation=evaluation, status="COMPLETE")
            record["artifact_hash"] = digest({k: v for k, v in record.items() if k != "artifact_hash"})
            _write_new(path, record)
            produced.append(record)
            if limit is not None and len(produced) >= limit:
                return produced
    return produced


def load_cross_horizon(directory):
    """Read stored secondary evaluations, verifying each certificate.

    Each record is stamped with the campaign it came from AFTER its certificate
    is verified. Secondary evaluations from different campaigns can share a
    (dataset, n) cell under different implementation versions and must never be
    pooled as one sample.
    """
    directory = Path(directory)
    out = []
    for path in sorted((directory / ARTIFACT_DIR).glob("*.json")):
        record = _read(path)
        if record.get("artifact_hash") != digest({k: v for k, v in record.items() if k != "artifact_hash"}):
            raise ContractError("CORRUPT_ARTIFACT", f"{path.name} no longer matches its certificate")
        if record["status"] == "COMPLETE":
            record["campaign"] = directory.name
            # Records written before exploratory revision 2 carry no rule key;
            # they are upper-only by construction (their manifests had no rule).
            record.setdefault("rule", "upper_only")
            out.append(record)
    return out


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args(argv)
    produced = score_campaign(args.campaign, limit=args.limit)
    complete = sum(1 for r in produced if r["status"] == "COMPLETE")
    print(canonical_json(dict(records=len(produced), complete=complete,
                              insufficient_future=sum(1 for r in produced if r["status"] == "INSUFFICIENT_FUTURE"))))


if __name__ == "__main__":
    main()
