"""Dry quotes, bounded native workers and immutable per-window evaluations.

Import/quote never optimize. Industrial snapshot reconstruction is explicitly
retrospective; training is prefix-only conditional on that fixed retained system.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import uuid
import psutil

from .metrics import evaluate_layout
from .orders import complete_window, load_industrial, load_synthetic
from .protocol import (ARMS, CPLEX_PYTHON, HEXALY_PYTHON, REPO_ROOT, REVISION, ContractError,
                       holdout_origin,
                       Protocol, allowed_source, canonical_json, digest, eligible,
                       horizon_grid, share_text, time_cap)
from .schema import SolveResult, TrainingProblem
from .uncertainty import build_training_problem
from .validation import validate_assignment

DEFAULT_OUTPUT = "reports/horizon_robustness_results/campaigns"
DEFAULT_DATASETS = ("syn_50sku_seed1001", "syn_500sku_seed1001", "syn_2000sku_seed1001", "BERNER")
_BACKENDS = {"hexaly": HEXALY_PYTHON, "cplex": CPLEX_PYTHON}
_ARMS = ARMS


def _json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as exc:
        raise ContractError("CORRUPT_ARTIFACT", str(path)) from exc


def _write_new(path, value):
    """Flush sibling temporary file, atomically publish without replacing."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial-" + uuid.uuid4().hex)
    with temporary.open("xb") as handle:
        handle.write(canonical_json(value).encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, path)
    except FileExistsError as exc:
        raise ContractError("IMMUTABLE_ARTIFACT", path.name) from exc
    finally:
        temporary.unlink(missing_ok=True)


def _contained(base, relative):
    base = Path(base).resolve()
    value = (base / relative).resolve()
    try:
        value.relative_to(base)
    except ValueError as exc:
        raise ContractError("OUTPUT_NOT_ALLOWED", "path escapes campaign root") from exc
    return value


def _output_root(output, root=REPO_ROOT):
    base = (Path(root) / DEFAULT_OUTPUT).resolve()
    return _contained(base, Path(output).resolve() if output is not None else ".")


def _positive(value, name, zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 or (not zero and value == 0):
        raise ContractError("INVALID_RESOURCE", f"{name} must be finite and {'nonnegative' if zero else 'positive'}")


def _dataset_id(dataset):
    if dataset == "BERNER":
        return
    match = re.fullmatch(r"syn_(50|500|1000|2000)sku_seed\d+", str(dataset))
    if not match:
        raise ContractError("SOURCE_NOT_ALLOWED", "unapproved dataset ID")
    allowed_source(f"exp02a_instances/{dataset}/syn_{match[1]}sku_orders.csv")


def _load_dataset(dataset, root=REPO_ROOT):
    _dataset_id(dataset)
    return load_industrial(root) if dataset == "BERNER" else load_synthetic(dataset, root)


def runtime_metadata(backend):
    """Actual interpreter/package versions; no native optimizer import."""
    if backend not in _BACKENDS:
        raise ContractError("DATA_CONTRACT_ERROR", "unsupported backend")
    packages = [backend, "numpy", "pandas", "scipy", "psutil"] + (["docplex"] if backend == "cplex" else [])
    script = ("import importlib.metadata as m,json,sys; print(json.dumps({'python':sys.version,'packages':"
              "{p:m.version(p) for p in " + repr(packages) + "}}))")
    completed = subprocess.run([_BACKENDS[backend], "-c", script], capture_output=True,
                               text=True, check=True, timeout=30, shell=False,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    result = json.loads(completed.stdout)
    result.update(backend=backend, interpreter=str(Path(_BACKENDS[backend]).resolve()),
                  implementation_hash=digest({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                              for p in sorted(Path(__file__).parent.glob("*.py"))}))
    return result


def solve_identity(problem, *, backend, backend_version, implementation_hash,
                   seed=11, threads=1, native_time_limit=120, solve_mode="visits",
                   warm_start=None, runtime_hash=None):
    if backend not in _BACKENDS or solve_mode not in ("visits", "min_slack") or not backend_version or backend_version == "unresolved":
        raise ContractError("DATA_CONTRACT_ERROR", "unpinned backend/mode")
    start = problem.reference.assignment if warm_start is None else tuple(warm_start)
    problem.catalogue.check_storage(start, problem.reference.fixed)
    payload = dict(model_hash=problem.model_hash, backend=backend, backend_version=backend_version,
                   implementation_hash=implementation_hash, runtime_hash=runtime_hash,
                   seed=seed, threads=threads, native_time_limit=native_time_limit,
                   solve_mode=solve_mode, warm_start_hash=digest(start))
    if solve_mode == "min_slack":
        payload["exact_b"] = [str(Fraction(v, problem.reference.total_lines)) for v in problem.reference.station_line_counts]
    return digest(payload)


def _config(datasets, backend, stage, arms, seeds, max_origins, solve_mode,
            delta, nu, tightening, threads, sensitivity, build_allowance_seconds, memory_limit_bytes,
            rule="upper_only", horizons=None):
    policy = Protocol()
    if stage not in ("pilot", "screen", "core", "sensitivity", "holdout") or backend not in _BACKENDS:
        raise ContractError("DATA_CONTRACT_ERROR", "unknown stage/backend")
    if rule not in policy.rules:
        raise ContractError("PROTOCOL_REVISION", "unknown workload rule")
    # Exploratory revision 2: the two-sided rule's primary slack is the
    # data-supported 0.02, not the upper-only study's 0.01.
    primary_delta = policy.two_sided_delta if rule == "two_sided" else policy.delta
    if not datasets or len(set(datasets)) != len(datasets):
        raise ContractError("DATA_CONTRACT_ERROR", "nonempty unique dataset IDs required")
    for dataset in datasets:
        _dataset_id(dataset)
    arms = tuple(arms) if arms is not None else (("NOM", "HIST+ACT") if stage == "pilot" else _ARMS)
    seeds = tuple(seeds) if seeds is not None else ((11, 22, 33) if stage == "core" else (11,))
    max_origins = (2 if stage == "core" else 1) if max_origins is None else max_origins
    if not arms or len(set(arms)) != len(arms) or any(a not in _ARMS for a in arms):
        raise ContractError("DATA_CONTRACT_ERROR", "unknown/duplicate arms")
    if not seeds or len(set(seeds)) != len(seeds) or any(type(s) is not int or s not in policy.seeds for s in seeds):
        raise ContractError("DATA_CONTRACT_ERROR", "unapproved seed grid")
    if type(max_origins) is not int or max_origins not in (1, 2, 3, 4) or type(threads) is not int or threads != 1:
        raise ContractError("DATA_CONTRACT_ERROR", "unapproved resources/origins")
    delta, nu, tightening = map(share_text, (delta, nu, tightening))
    if delta not in policy.deltas or nu not in policy.nus or tightening not in policy.tightening:
        raise ContractError("PROTOCOL_REVISION", "parameter outside approved grid")
    if solve_mode not in ("visits", "min_slack"):
        raise ContractError("DATA_CONTRACT_ERROR", "unknown solve mode")
    if stage != "sensitivity":
        if (delta, nu, tightening, solve_mode, sensitivity) != (primary_delta, "0.01", "0.5", "visits", None):
            raise ContractError("PROTOCOL_REVISION", "primary stages require primary parameters")
        if stage in ("pilot", "screen") and (seeds != (11,) or max_origins != 1):
            raise ContractError("PROTOCOL_REVISION", "pilot/screen require first origin and seed11")
        if stage == "pilot" and any(a not in ("NOM", "HIST+ACT") for a in arms):
            raise ContractError("PROTOCOL_REVISION", "pilot only quotes NOM/HIST+ACT")
    else:
        permitted = {"delta": nu == "0.01" and tightening == "0.5" and solve_mode == "visits",
                     "nu": delta == primary_delta and tightening == "0.5" and solve_mode == "visits",
                     "tightening": delta == primary_delta and nu == "0.01" and solve_mode == "visits" and arms == ("TIGHT",),
                     "min_slack": (delta, nu, tightening, solve_mode) == (primary_delta, "0.01", "0.5", "min_slack")}
        if not permitted.get(sensitivity, False):
            raise ContractError("PROTOCOL_REVISION", "quote one named sensitivity axis at a time")
    if stage == "holdout":
        # Exploratory revision 3: the single deployment origin at the end of the
        # furthest scored future, primary parameters (checked above), any approved
        # seed subset, and optionally a subset of the horizon grid.
        if max_origins != 1:
            raise ContractError("PROTOCOL_REVISION", "holdout uses the single deployment origin")
        if horizons is not None:
            horizons = tuple(horizons)
            if not horizons or len(set(horizons)) != len(horizons) or any(type(n) is not int or n <= 0 for n in horizons):
                raise ContractError("DATA_CONTRACT_ERROR", "holdout horizons must be distinct positive integers")
    elif horizons is not None:
        raise ContractError("PROTOCOL_REVISION", "explicit horizons are a holdout-stage option")
    _positive(build_allowance_seconds, "build allowance", zero=True)
    _positive(memory_limit_bytes, "memory limit")
    if type(memory_limit_bytes) is not int:
        raise ContractError("INVALID_RESOURCE", "memory bytes must be integral")
    config = dict(datasets=list(datasets), backend=backend, stage=stage, arms=list(arms), seeds=list(seeds),
                  max_origins=max_origins, solve_mode=solve_mode, delta=delta, nu=nu, tightening=tightening,
                  threads=threads, sensitivity=sensitivity, build_allowance_seconds=build_allowance_seconds,
                  memory_limit_bytes=memory_limit_bytes)
    if rule != "upper_only":
        # Present only for the two-sided rule, so every existing upper-only
        # manifest still rebuilds byte-identically and remains resumable.
        config["rule"] = rule
    if stage == "holdout" and horizons is not None:
        config["horizons"] = list(horizons)      # absent elsewhere for the same reason
    return config


def _key(problem, case, runtime):
    return solve_identity(problem, backend=case["backend"], backend_version=runtime["packages"][case["backend"]],
                          implementation_hash=runtime["implementation_hash"], runtime_hash=digest(runtime),
                          seed=case["seed"], threads=case["threads"], native_time_limit=case["time_limit"],
                          solve_mode=case["solve_mode"])


def quote(datasets=DEFAULT_DATASETS, *, root=REPO_ROOT, backend="hexaly", arms=None,
          seeds=None, max_origins=None, solve_mode="visits", delta="0.01", nu="0.01",
          tightening="0.5", threads=1, stage="pilot", sensitivity=None,
          build_allowance_seconds=600, memory_limit_bytes=32 * 1024**3, loader=None, metadata=None,
          rule="upper_only", horizons=None):
    """Dry quote; injectable loader/metadata support unit fixtures, not the CLI."""
    config = _config(datasets, backend, stage, arms, seeds, max_origins, solve_mode, delta, nu,
                     tightening, threads, sensitivity, build_allowance_seconds, memory_limit_bytes,
                     rule=rule, horizons=horizons)
    loader = _load_dataset if loader is None else loader
    runtime = runtime_metadata(backend) if metadata is None else json.loads(canonical_json(metadata))
    rule = config.get("rule", "upper_only")
    rows = []
    for dataset in datasets:
        demand = loader(dataset, root)
        catalogue, orders = demand.catalogue, demand.orders
        expected_catalogue_id = "berner" if dataset == "BERNER" else dataset
        if catalogue.dataset_id != expected_catalogue_id:
            raise ContractError("DATA_CONTRACT_ERROR", "loader returned another dataset")
        first = 7 * len(orders) // 10
        if stage == "holdout":
            # Revision 3: the deployment origin is the end of the furthest future
            # the first origin can score; nothing in the study has read beyond it.
            origin_list = (holdout_origin(len(orders), catalogue.p),)
        else:
            origin_list = tuple(first + j * 2 * catalogue.p for j in range(config["max_origins"]))
        grid = (catalogue.p,) if stage == "pilot" else horizon_grid(catalogue.p)
        if config.get("horizons"):
            if any(n not in grid for n in config["horizons"]):
                raise ContractError("PROTOCOL_REVISION", "holdout horizons must lie on the protocol grid")
            grid = tuple(n for n in grid if n in config["horizons"])
        for origin in origin_list:
            history = complete_window(orders, 0, origin) if 0 < origin <= len(orders) else None
            for n in grid:
                reason = eligible(origin, n, len(orders))
                for arm in config["arms"]:
                    for seed in config["seeds"]:
                        case = dict(stage=stage, dataset_id=dataset, catalogue_hash=catalogue.fingerprint,
                                    source_files=[asdict(v) for v in catalogue.source_files],
                                    source_hash=digest([asdict(v) for v in catalogue.source_files]),
                                    history_hash=None, input_hash=None, model_hash=None,
                                    origin=origin, n=n, arm=arm, delta=config["delta"], nu=config["nu"],
                                    tightening=config["tightening"], seed=seed, backend=backend,
                                    solve_mode=solve_mode, threads=threads,
                                    time_limit=5 if catalogue.kind == "fixture" else time_cap(catalogue.p, catalogue.kind),
                                    eligibility=reason, solve_key=None)
                        if rule != "upper_only":
                            # Row identity carries the rule; absent under upper-only
                            # so existing manifests keep their case IDs.
                            case["rule"] = rule
                        if reason is None:
                            problem = build_training_problem(catalogue, history, n, arm, config["delta"],
                                                             config["nu"], config["tightening"], rule=rule)
                            case.update(history_hash=problem.reference.history_hash, input_hash=problem.input_hash,
                                        model_hash=problem.model_hash, solve_key=_key(problem, case, runtime))
                        case["case_id"] = digest(case)
                        case["expected_result"] = f"cases/{case['case_id']}.json"
                        rows.append(case)
    unique = {r["solve_key"]: r["time_limit"] for r in rows if r["solve_key"]}
    manifest = dict(revision=REVISION, artifact_schema=2, kind="dry_quote", config=config,
                    runtime=runtime, rows=rows, unique_solve_count=len(unique),
                    reused_row_count=sum(r["solve_key"] is not None for r in rows) - len(unique),
                    solver_seconds=sum(unique.values()))
    manifest["manifest_hash"] = digest(manifest)
    return manifest


def _live_attempt(attempt):
    pid, created = attempt.get("pid"), attempt.get("create_time")
    if type(pid) is not int or not isinstance(created, (int, float)) or not math.isfinite(created):
        return False
    try:
        return abs(psutil.Process(pid).create_time() - created) < 1e-3
    except psutil.NoSuchProcess:
        return False
    except psutil.AccessDenied as exc:
        raise ContractError("UNKNOWN_PROCESS_OWNER", "cannot establish old child liveness") from exc


def _check_child_marker(path):
    value = _json(path)
    if not isinstance(value, dict) or type(value.get("pid")) is not int or value["pid"] <= 0:
        raise ContractError("CORRUPT_ARTIFACT", "invalid child identity record")
    created = value.get("create_time")
    if created is None and value.get("already_exited") is True:
        return False
    if isinstance(created, bool) or not isinstance(created, (int, float)) or not math.isfinite(created) or created <= 0:
        raise ContractError("CORRUPT_ARTIFACT", "invalid child creation time")
    return _live_attempt(value)


@contextmanager
def _campaign_lock(root):
    """Kernel lock is released on parent death; immutable child records survive."""
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".campaign.lock").open("a+b") as handle:
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write(b"0"); handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ContractError("LIVE_CAMPAIGN", "another parent owns this output directory") from exc
        try:
            for marker in root.glob("solves/*/attempts/*/child.json"):
                if _check_child_marker(marker):
                    raise ContractError("LIVE_ATTEMPT", "old native child remains alive")
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _worker_command(request, result, backend):
    return [_BACKENDS[backend], "-m", "Baselines.horizon_robustness.runner", "worker", str(request), str(result)]


def worker(request_path, result_path):
    request = _json(request_path)
    problem = TrainingProblem.from_dict(request["problem"])
    options = request["options"]
    runtime = runtime_metadata(options["backend"])
    if runtime != request["runtime"] or problem.input_hash != request["input_hash"]:
        raise ContractError("WORKER_INPUT_CHANGED", "worker runtime/problem differs from quote")
    module = __import__(f"Baselines.horizon_robustness.{options['backend']}_backend", fromlist=["solve"])
    result = module.solve(problem, seed=options["seed"], threads=options["threads"],
                          time_limit=options["time_limit"], solve_mode=options["solve_mode"],
                          warm_start=problem.reference.assignment)
    _write_new(Path(result_path), dict(result=result.to_dict(), request_hash=digest(request), runtime=runtime))


def _native_contradiction(problem, result, solve_mode):
    if result is None or result.status.value != "PROVEN_INFEASIBLE":
        return None
    if solve_mode == "min_slack":
        certificate = validate_assignment(problem, problem.reference.assignment, solve_mode="min_slack", min_slack=1)
        rationale = "eta=1 is a feasible bounded epigraph witness"
    elif problem.arm in ("NOM", "TIGHT"):
        certificate = validate_assignment(problem, problem.reference.assignment)
        rationale = "reference shares fit the nonnegative margin"
    else:
        return None
    if certificate["valid"]:
        return dict(kind="NATIVE_INFEASIBILITY_CONTRADICTION", rationale=rationale, certificate=certificate)
    return None


def _attest(envelope, request):
    result = SolveResult.from_dict(envelope["result"])
    problem = TrainingProblem.from_dict(request["problem"])
    options = request["options"]
    expected = {"input_hash": problem.input_hash, "model_hash": problem.model_hash,
                **{k: options[k] for k in ("backend", "seed", "threads", "time_limit", "solve_mode")}}
    if envelope.get("request_hash") != digest(request) or envelope.get("runtime") != request["runtime"] or any(getattr(result, k) != v for k, v in expected.items()):
        raise ContractError("NATIVE_PROVENANCE_MISMATCH", "solver identity differs from frozen request")
    version = request["runtime"]["packages"][options["backend"]]
    if result.backend_version not in (version, version + "-Win64"):
        raise ContractError("NATIVE_VERSION_MISMATCH", "unquoted native version")
    return result


def _log_tail(path, limit=4000):
    """Bounded child-log excerpt, so a failure is auditable from JSON alone."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not text:
        return None
    return text[-limit:] if len(text) > limit else text


def _diagnose(base, value):
    """Attach bounded stdout/stderr tails to an attempt that returned no result."""
    if value.get("solve_result") is not None:
        return value
    diagnostics = {name: _log_tail(base / f"{name}.txt") for name in ("stderr", "stdout")}
    if any(v is not None for v in diagnostics.values()):
        value["child_log_tail"] = {k: v for k, v in diagnostics.items() if v is not None}
        value["child_log_tail_truncated_to_bytes"] = 4000
    return value


def _terminal_solve(root, problem, case, manifest, attempt_id, reason, remaining, executor):
    base = _contained(root, f"solves/{case['solve_key']}/attempts/{attempt_id}")
    terminal = base / "terminal.json"
    if terminal.exists():
        cached = _json(terminal)
        if cached.get("solve_result"):
            old_request = _json(base / "request.json")
            checked = _attest(_json(base / "native.json"), old_request)
            if digest(checked.to_dict()) != digest(cached["solve_result"]) or _key(TrainingProblem.from_dict(old_request["problem"]), case, manifest["runtime"]) != case["solve_key"]:
                raise ContractError("CACHE_MISMATCH", "cache does not attest to quoted model")
        return cached, True
    request = dict(problem=problem.to_dict(), input_hash=problem.input_hash, runtime=manifest["runtime"],
                   options={k: case[k] for k in ("backend", "seed", "threads", "time_limit", "solve_mode")})
    if base.exists():
        if (base / "native.json").exists() and (base / "request.json").exists():
            old_request = _json(base / "request.json")
            recovered = _attest(_json(base / "native.json"), old_request)
            if _key(TrainingProblem.from_dict(old_request["problem"]), case, manifest["runtime"]) != case["solve_key"]:
                raise ContractError("CACHE_MISMATCH", "interrupted attempt has another model")
            value = dict(status="RECOVERED_NATIVE", solve_result=recovered.to_dict(), input_hash=old_request["input_hash"],
                         process=None, attempt_id=attempt_id, reason=reason)
        else:
            value = dict(status="INTERRUPTED", solve_result=None, input_hash=None, process=None,
                         attempt_id=attempt_id, reason=reason, error="incomplete attempt retained; explicit new retry required")
        _write_new(terminal, value)
        return value, True
    base.mkdir(parents=True)
    _write_new(base / "request.json", request)
    deadline = min(case["time_limit"] + manifest["config"]["build_allowance_seconds"], remaining)
    try:
        process = executor(_worker_command(base / "request.json", base / "native.json", case["backend"]),
                           cwd=REPO_ROOT, attempt_dir=base, deadline_seconds=deadline,
                           memory_limit_bytes=manifest["config"]["memory_limit_bytes"])
        value = dict(status=process["status"], solve_result=None, request_hash=digest(request),
                     input_hash=problem.input_hash, process=process, attempt_id=attempt_id, reason=reason)
        if process["status"] == "EXITED" and process["returncode"] == 0:
            result = _attest(_json(base / "native.json"), request)
            value.update(status="NATIVE_RETURNED", solve_result=result.to_dict())
        elif process["status"] == "EXITED":
            value["status"] = "SOLVER_ERROR"
    except Exception as exc:
        value = dict(status="SOLVER_ERROR", solve_result=None, input_hash=problem.input_hash,
                     attempt_id=attempt_id, reason=reason, error=f"{type(exc).__name__}: {exc}")
    _write_new(terminal, _diagnose(base, value))
    return value, False


def _blank(case, status, **extra):
    return dict(case=case, status=status, solve_result=None, validation=None, evaluation=None,
                reference_evaluation=None, accepted_training_solution=False, **extra)


def _save_case(path, record):
    record["artifact_hash"] = digest({k: v for k, v in record.items() if k != "artifact_hash"})
    _write_new(path, record)


def _case_record(path, case):
    record = _json(path)
    required = {"case", "status", "solve_result", "validation", "evaluation", "reference_evaluation", "artifact_hash"}
    if not isinstance(record, dict) or not required.issubset(record) or record["case"] != case or record["artifact_hash"] != digest({k: v for k, v in record.items() if k != "artifact_hash"}):
        raise ContractError("CORRUPT_ARTIFACT", "case record no longer matches its immutable certificate")
    return record


def _score(final_path, problem, case, history, demand, native, reused, attempt_id):
    record = _blank(case, native["status"], solve_result_provenance=dict(
        solve_key=case["solve_key"], native_input_hash=native.get("input_hash"),
        case_input_hash=problem.input_hash, reused=reused, attempt_id=attempt_id,
        equivalence="same exact model/runtime/start; native input hash retained, not rewritten"), native_attempt=native)
    if native.get("solve_result") is None:
        _save_case(final_path, record)
        return record
    solved = SolveResult.from_dict(native["solve_result"])
    if solved.model_hash != problem.model_hash:
        raise ContractError("CACHE_MISMATCH", "cached result has another mathematical model")
    record["solve_result"] = solved.to_dict()
    contradiction = _native_contradiction(problem, solved, case["solve_mode"])
    if contradiction:
        record["native_contradiction"] = contradiction
    if solved.assignment is None:
        record["status"] = solved.status.value
        _save_case(final_path, record)
        return record
    validation = validate_assignment(problem, solved.assignment, objective=solved.objective,
                                     solve_mode=case["solve_mode"], history=history)
    record["validation"] = validation
    if not validation["valid"] or solved.status.value not in ("FEASIBLE", "OPTIMAL_WITHIN_TOLERANCE"):
        record["status"] = "REJECTED_CANDIDATE"
        _save_case(final_path, record)
        return record
    policy_validation = validate_assignment(problem, solved.assignment, history=history)
    record["accepted_training_solution"] = policy_validation["valid"]
    record["policy_validation"] = policy_validation
    record["status"] = "COMPLETE" if case["solve_mode"] == "visits" else "DIAGNOSTIC_COMPLETE"
    frozen = final_path.with_suffix(".frozen.json")
    certificate = dict(case_id=case["case_id"], input_hash=problem.input_hash, assignment=list(solved.assignment),
                       layout_hash=digest(solved.assignment), validation=validation)
    if frozen.exists():
        if _json(frozen) != certificate:
            raise ContractError("FROZEN_LAYOUT_CHANGED", "resume differs from pre-score certificate")
    else:
        _write_new(frozen, certificate)
    try:
        future = complete_window(demand.orders, case["origin"], case["origin"] + case["n"])
        if tuple(demand.orders[:case["origin"]]) != history or len(future) != case["n"] or future[0].chronology_key <= history[-1].chronology_key:
            raise ContractError("SOURCE_ADJACENCY", "future is not the exact next complete-order segment")
        for key, layout in (("evaluation", solved.assignment), ("reference_evaluation", problem.reference.assignment)):
            record[key] = evaluate_layout(problem, layout, future)
            record[key]["future_boundaries"].update(stream_adjacency_verified=True,
                membership_provenance="verified_exact_slice_of_rebuilt_source_stream")
        record["evaluation"]["solver_status"] = solved.status.value
    except Exception as exc:
        record.update(status="SCORING_FAILED", evaluation=None, reference_evaluation=None,
                      scoring_error=f"{type(exc).__name__}: {exc}")
    _save_case(final_path, record)
    return record


def run(manifest, *, approved_manifest_hash, output=None, root=REPO_ROOT,
        solver_budget_seconds, wall_cutoff_seconds, retry_id=None, retry_reason=None,
        loader=None, metadata=None, executor=None):
    """Run this quote only. Explicit retry IDs never replace existing records.

    Native deadlines have a watchdog. Parent preparation/scoring check the
    cutoff at phase boundaries; a current atomic operation can finish later.
    """
    started = time.monotonic()
    _positive(solver_budget_seconds, "solver budget", zero=True)
    _positive(wall_cutoff_seconds, "wall cutoff")
    if approved_manifest_hash != manifest.get("manifest_hash") or digest({k: v for k, v in manifest.items() if k != "manifest_hash"}) != approved_manifest_hash:
        raise ContractError("MANIFEST_CHANGED", "explicit approval hash must match quote")
    if (retry_id is None) != (retry_reason is None) or (retry_id is not None and (not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", retry_id) or retry_id == "primary" or not retry_reason.strip())):
        raise ContractError("RETRY_CONTRACT", "retry requires distinct safe ID and nonempty reason")
    loader = _load_dataset if loader is None else loader
    loaded = {}
    def cached_loader(dataset, dataset_root):
        if dataset not in loaded:
            loaded[dataset] = loader(dataset, dataset_root)
        return loaded[dataset]
    rebuilt = quote(root=root, loader=cached_loader, metadata=metadata, **manifest["config"])
    if rebuilt != manifest:
        raise ContractError("QUOTE_STALE", "sources/runtime/implementation/rows changed")
    if solver_budget_seconds < manifest["solver_seconds"]:
        raise ContractError("INSUFFICIENT_AUTHORIZATION", "budget does not cover quoted native caps")
    root_out = _output_root(output, root)
    if executor is None:
        from .execution import execute
        executor = execute
    invocation, charged, outcomes = uuid.uuid4().hex, 0, []
    with _campaign_lock(root_out):
        manifest_path = root_out / "manifest.json"
        if manifest_path.exists():
            if _json(manifest_path) != manifest:
                raise ContractError("CAMPAIGN_MISMATCH", "output belongs to another manifest")
        else:
            _write_new(manifest_path, manifest)
        _write_new(root_out / "invocations" / (invocation + ".started.json"),
                   dict(approved_manifest_hash=approved_manifest_hash, solver_budget_seconds=solver_budget_seconds,
                        wall_cutoff_seconds=wall_cutoff_seconds, retry_id=retry_id, retry_reason=retry_reason,
                        parent_pid=os.getpid(), parent_create_time=psutil.Process().create_time()))
        for case in manifest["rows"]:
            primary = _contained(root_out, case["expected_result"])
            previous = _case_record(primary, case) if primary.exists() else None
            if previous is not None and (retry_id is None or previous["status"] in ("COMPLETE", "DIAGNOSTIC_COMPLETE")):
                outcomes.append(previous); continue
            final_path = primary if retry_id is None else _contained(root_out, f"cases/{case['case_id']}/retries/{retry_id}.json")
            if final_path.exists():
                outcomes.append(_case_record(final_path, case)); continue
            if case["eligibility"]:
                record = _blank(case, case["eligibility"])
                _save_case(final_path, record); outcomes.append(record); continue
            remaining = wall_cutoff_seconds - (time.monotonic() - started)
            if remaining <= 0:
                record = _blank(case, "WALL_CUTOFF")
                _save_case(final_path, record); outcomes.append(record); continue
            demand = loaded[case["dataset_id"]]
            history = complete_window(demand.orders, 0, case["origin"])
            problem = build_training_problem(demand.catalogue, history, case["n"], case["arm"], case["delta"],
                                             case["nu"], case["tightening"], rule=case.get("rule", "upper_only"))
            if problem.input_hash != case["input_hash"] or problem.reference.history_hash != case["history_hash"] or demand.catalogue.fingerprint != case["catalogue_hash"]:
                raise ContractError("REBUILT_INPUT_CHANGED", "case differs from frozen quote")
            attempt_id = retry_id or "primary"
            if retry_id:
                for old in (root_out / "solves" / case["solve_key"] / "attempts").glob("*"):
                    if (old / "request.json").exists() and not (old / "child.json").exists() and not (old / "native.json").exists():
                        terminal = _json(old / "terminal.json") if (old / "terminal.json").exists() else None
                        if terminal is None or terminal.get("status") == "INTERRUPTED" or (terminal.get("process") or {}).get("cleanup_error"):
                            raise ContractError("UNKNOWN_ATTEMPT_OWNER", "interrupted launch lacks identity; manual process audit required before retry")
            primary_native = root_out / "solves" / case["solve_key"] / "attempts" / "primary" / "terminal.json"
            if retry_id and primary_native.exists() and _json(primary_native).get("solve_result"):
                result = SolveResult.from_dict(_json(primary_native)["solve_result"])
                if result.assignment is not None and result.status.value in ("FEASIBLE", "OPTIMAL_WITHIN_TOLERANCE") and validate_assignment(problem, result.assignment, result.objective, case["solve_mode"], history=history)["valid"]:
                    attempt_id = "primary"
            native_path = root_out / "solves" / case["solve_key"] / "attempts" / attempt_id / "terminal.json"
            remaining = wall_cutoff_seconds - (time.monotonic() - started)
            if remaining <= 0 or (not native_path.exists() and charged + case["time_limit"] > solver_budget_seconds):
                record = _blank(case, "WALL_CUTOFF" if remaining <= 0 else "SOLVER_BUDGET_CUTOFF")
                _save_case(final_path, record); outcomes.append(record); continue
            native, reused = _terminal_solve(root_out, problem, case, manifest, attempt_id, retry_reason, remaining, executor)
            if not reused:
                charged += case["time_limit"]
            if time.monotonic() - started >= wall_cutoff_seconds:
                record = _blank(case, "WALL_CUTOFF", native_attempt=native)
                _save_case(final_path, record)
            else:
                record = _score(final_path, problem, case, history, demand, native, reused, attempt_id)
            outcomes.append(record)
        _write_new(root_out / "invocations" / (invocation + ".finished.json"),
                   dict(approved_manifest_hash=approved_manifest_hash, charged_native_cap_seconds=charged,
                        elapsed_seconds=time.monotonic() - started, wall_cutoff_seconds=wall_cutoff_seconds,
                        deadline_enforcement="native watchdog; parent checks between preparation/scoring phases",
                        statuses=[v["status"] for v in outcomes]))
    return tuple(outcomes)


def supervised_run(manifest, *, approved_manifest_hash, output=None, root=REPO_ROOT,
                   solver_budget_seconds, wall_cutoff_seconds, retry_id=None,
                   retry_reason=None, executor=None):
    """CLI campaign boundary: watchdog covers loading, building AND scoring.

    Resource-limit records for cases not yet written are preserved in the
    supervisor terminal artifact. They do not overwrite recoverable native
    outputs. Termination/log flushing can add a short cleanup interval.
    """
    _positive(solver_budget_seconds, "solver budget", zero=True)
    _positive(wall_cutoff_seconds, "wall cutoff")
    if approved_manifest_hash != manifest.get("manifest_hash") or digest({k: v for k, v in manifest.items() if k != "manifest_hash"}) != approved_manifest_hash:
        raise ContractError("MANIFEST_CHANGED", "explicit approval hash must match quote")
    _config(**manifest["config"])
    if solver_budget_seconds < manifest["solver_seconds"]:
        raise ContractError("INSUFFICIENT_AUTHORIZATION", "insufficient quoted native cap budget")
    root_out = _output_root(output, root)
    if executor is None:
        from .execution import execute
        executor = execute
    with _campaign_lock(root_out / ".supervisor-owner"):
        base = root_out / "supervision" / uuid.uuid4().hex
        options = dict(approved_manifest_hash=approved_manifest_hash, output=str(root_out), root=str(Path(root).resolve()),
                       solver_budget_seconds=solver_budget_seconds, wall_cutoff_seconds=wall_cutoff_seconds,
                       retry_id=retry_id, retry_reason=retry_reason)
        _write_new(base / "request.json", dict(manifest=manifest, options=options))
        command = [str(Path(CPLEX_PYTHON)), "-m", "Baselines.horizon_robustness.runner", "campaign",
                   str(base / "request.json"), str(base / "result.json")]
        process = executor(command, cwd=REPO_ROOT, attempt_dir=base,
                           deadline_seconds=wall_cutoff_seconds,
                           memory_limit_bytes=manifest["config"]["memory_limit_bytes"])
        if process["status"] == "EXITED" and process["returncode"] == 0:
            outcomes = _json(base / "result.json")
        else:
            status = {"TIMEOUT": "WALL_CUTOFF", "MEMORY_LIMIT": "RESOURCE_LIMIT"}.get(process["status"], "CAMPAIGN_ERROR")
            outcomes = []
            for case in manifest["rows"]:
                # Derive paths; never trust a manifest-provided traversal path.
                if not re.fullmatch(r"[0-9a-f]{64}", case["case_id"]):
                    raise ContractError("MANIFEST_CHANGED", "invalid case identity")
                primary = _contained(root_out, f"cases/{case['case_id']}.json")
                if retry_id:
                    if not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", retry_id):
                        raise ContractError("RETRY_CONTRACT", "invalid retry ID")
                    candidate = _contained(root_out, f"cases/{case['case_id']}/retries/{retry_id}.json")
                    if candidate.exists():
                        primary = candidate
                outcomes.append(_case_record(primary, case) if primary.exists() else _blank(case, status, supervisor_process=process))
        _write_new(base / "terminal.json", dict(manifest_hash=approved_manifest_hash, process=process, cases=outcomes))
        return tuple(outcomes)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    qp = sub.add_parser("quote")
    qp.add_argument("--datasets", nargs="+", default=list(DEFAULT_DATASETS))
    qp.add_argument("--stage", choices=("pilot", "screen", "core", "sensitivity", "holdout"), default="pilot")
    qp.add_argument("--horizons", type=int, nargs="+",
                    help="holdout stage only: subset of the protocol horizon grid to quote")
    qp.add_argument("--backend", choices=tuple(_BACKENDS), default="hexaly")
    qp.add_argument("--arms", nargs="+", choices=_ARMS)
    qp.add_argument("--seeds", type=int, nargs="+")
    qp.add_argument("--max-origins", type=int)
    for key, default in (("delta", "0.01"), ("nu", "0.01"), ("tightening", "0.5")):
        qp.add_argument("--" + key, default=default)
    qp.add_argument("--solve-mode", choices=("visits", "min_slack"), default="visits")
    qp.add_argument("--sensitivity", choices=("delta", "nu", "tightening", "min_slack"))
    qp.add_argument("--build-allowance-seconds", type=float, default=600)
    qp.add_argument("--memory-limit-bytes", type=int, default=32 * 1024**3)
    qp.add_argument("--rule", choices=("upper_only", "two_sided"), default="upper_only",
                    help="workload rule; two_sided is exploratory revision 2 with primary delta 0.02")
    rp = sub.add_parser("run")
    rp.add_argument("manifest"); rp.add_argument("--approved-manifest-hash", required=True)
    rp.add_argument("--output"); rp.add_argument("--solver-budget-seconds", type=float, required=True)
    rp.add_argument("--wall-cutoff-seconds", type=float, required=True)
    rp.add_argument("--retry-id"); rp.add_argument("--retry-reason")
    wp = sub.add_parser("worker"); wp.add_argument("request"); wp.add_argument("result")
    cp = sub.add_parser("campaign"); cp.add_argument("request"); cp.add_argument("result")
    args = vars(parser.parse_args(argv))
    command = args.pop("command")
    if command == "worker":
        worker(args["request"], args["result"])
    elif command == "campaign":
        request = _json(args["request"])
        _write_new(Path(args["result"]), run(request["manifest"], **request["options"]))
    elif command == "quote":
        print(canonical_json(quote(**args)))
    else:
        manifest = _json(args.pop("manifest"))
        print(canonical_json([v["status"] for v in supervised_run(manifest, **args)]))


if __name__ == "__main__":
    main()
