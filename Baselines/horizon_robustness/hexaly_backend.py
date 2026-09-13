"""Hexaly whole-catalogue set-partition adapter for the frozen study contract.

Only the installed public API is used; importing this module does not load a
solver. Native INFEASIBLE means an invalid candidate, whereas INCONSISTENT is
Hexaly's proof status for the submitted numerical model, not an exact-arithmetic
certificate. Every native feasible incumbent is independently recomputed.

API/status references (checked against the installed 13.0 Python wrapper):
https://www.hexaly.com/docs/last/pythonapi/optimizer/hxsolutionstatus.html
https://www.hexaly.com/docs/last/pythonapi/optimizer/hxsolution.html
https://www.hexaly.com/docs/last/pythonapi/optimizer/hxparam.html
"""

from fractions import Fraction
import importlib
import math
import time

from .protocol import ACTIVATION_ARMS, ContractError, canonical_json, digest
from .reference import slot_assignment
from .schema import SolveResult, SolveStatus, TrainingProblem
from .uncertainty import ROW_FORMULATION, integer_cap_rows
from .validation import EXCLUDED_INDUSTRIAL_STATIONS, validate_assignment


_INT32_MAX = 2**31 - 1
_INT64_MAX = 2**63 - 1
_TOLERANCE = Fraction(1, 100_000_000)
_REPRESENTATION = "whole_catalogue_set_partition"


def _load_hexaly():
    return importlib.import_module("hexaly.optimizer")


def _arguments(problem, seed, threads, time_limit, solve_mode, warm_start, log_output):
    if not isinstance(problem, TrainingProblem):
        raise ContractError("DATA_CONTRACT_ERROR", "problem must be a TrainingProblem")
    for label, value, minimum in (("seed", seed, 0), ("threads", threads, 1)):
        if type(value) is not int or not minimum <= value <= _INT32_MAX:
            raise ContractError("DATA_CONTRACT_ERROR", f"{label} must be a supported integer >= {minimum}")
    if (type(time_limit) not in (int, float) or not 0 <= time_limit <= _INT32_MAX
            or int(time_limit) != time_limit):
        raise ContractError("DATA_CONTRACT_ERROR", "Hexaly 13 time_limit must be whole seconds in [0,2^31-1]")
    if solve_mode not in ("visits", "min_slack") or type(log_output) is not bool:
        raise ContractError("DATA_CONTRACT_ERROR", "unknown solve mode or non-boolean log_output")
    catalogue = problem.catalogue
    if catalogue.p > _INT32_MAX:
        raise ContractError("DATA_CONTRACT_ERROR", "catalogue exceeds native set indexing range")
    if catalogue.kind == "industrial" and EXCLUDED_INDUSTRIAL_STATIONS.intersection(catalogue.station_ids):
        raise ContractError("DATA_CONTRACT_ERROR", "industrial catalogue must already exclude the three forbidden zones")
    # Integer weights and every possible sum must fit Hexaly's signed int64.
    maximum_visits = sum(w * min(len(support), catalogue.s) for support, w in problem.weighted_supports)
    if solve_mode == "visits" and maximum_visits >= _INT64_MAX:
        raise ContractError("DATA_CONTRACT_ERROR", "complete visit objective exceeds safe native int64 range")
    start = problem.reference.assignment if warm_start is None else warm_start
    catalogue.check_storage(start, problem.reference.fixed)
    catalogue.check_storage(start, catalogue.exogenous_fixed)
    return start


def _share(value):
    """Convert coefficients only; do not allow positive workload to underflow."""
    result = float(value)
    if not math.isfinite(result) or (value != 0 and result == 0):
        raise ContractError("DATA_CONTRACT_ERROR", "share coefficient is outside supported floating-point range")
    return result


def _build_model(optimizer, problem, solve_mode):
    model, catalogue = optimizer.model, problem.catalogue
    stations = tuple(model.set(catalogue.p) for _ in range(catalogue.s))
    model.constraint(model.partition(stations))
    for s, capacity in enumerate(catalogue.capacities):
        stations[s].name = f"station_{s}"
        model.constraint(model.count(stations[s]) == capacity)
    members = {}

    def member(p, s):
        key = (p, s)
        if key not in members:
            members[key] = model.contains(stations[s], p)
        return members[key]

    for p, s in problem.reference.fixed:
        model.constraint(member(p, s))
    if catalogue.allowed_stations:
        for p, allowed in enumerate(catalogue.allowed_stations):
            if len(allowed) < catalogue.s:
                model.constraint(model.or_(member(p, s) for s in allowed))
    # Fixed and movable touches enter the same OR: one visit per station/order.
    # The diagnostic objective has no visit term. Avoid building millions of
    # unused touch expressions (and unnecessary int64 weights) in that mode.
    visits = None
    if solve_mode == "visits":
        visits = model.sum(
            weight * model.or_(member(p, s) for p in support)
            for support, weight in problem.weighted_supports for s in range(catalogue.s))
    inactive = problem.reference.inactive
    nu = Fraction(problem.nu) if problem.arm in ACTIVATION_ARMS and inactive else Fraction(0)
    activation = tuple(model.or_(member(p, s) for p in inactive) for s in range(catalogue.s)) if nu else ()
    # g_s: every inactive product at station s, so activation mass cannot avoid
    # it. Needed only by the two-sided lower rows / lower deviations.
    trapped = (tuple(model.and_(member(p, s) for p in inactive) for s in range(catalogue.s))
               if nu and problem.two_sided else ())
    b = tuple(Fraction(c, problem.reference.total_lines) for c in problem.reference.station_line_counts)
    caps = problem.rational_caps(optimization=True)
    deviations, row_count, checked = [], 0, []
    if solve_mode == "visits":
        # Exact integer-count rows. Their coefficients and thresholds are whole
        # numbers, so Hexaly's float feasibility tolerance cannot admit a layout
        # that violates the true share ceiling. The feasible set is unchanged.
        rows, _ = integer_cap_rows(problem)
        for row in rows:
            s, scenario = row["station"], problem.effective_scenarios[row["scenario"]]
            multiplier = row["multiplier"]
            terms = [(multiplier * count) * member(p, s) for p, count in scenario.counts] if multiplier else []
            if row["activation_coefficient"]:
                terms.append(row["activation_coefficient"] * activation[s])
            if row.get("all_inactive_coefficient"):
                terms.append(row["all_inactive_coefficient"] * trapped[s])
            row_count += 1
            if not terms:
                # Left side is identically zero and the threshold is nonnegative.
                continue
            expression = model.sum(terms)
            if row["sense"] == ">=":
                model.constraint(expression >= row["threshold"])
            else:
                model.constraint(expression <= row["threshold"])
            checked.append(expression)
    else:
        two_sided = problem.two_sided
        for scenario in problem.effective_scenarios:
            # Sparse counts are never expanded to a dense product/scenario matrix.
            coefficients = tuple((p, _share(Fraction(count, scenario.total_lines))) for p, count in scenario.counts)
            for s in range(catalogue.s):
                share = model.sum(coefficient * member(p, s) for p, coefficient in coefficients)
                endpoints = [share]
                if nu:
                    endpoints.append(_share(1 - nu) * share + _share(nu) * activation[s])
                for endpoint in endpoints:
                    row_count += 1
                    deviations.append(endpoint - _share(b[s]))
                if two_sided:
                    # Downward excursions: eta must cover b_s - share and, with
                    # activation, b_s - ((1-nu)*share + nu*g_s), the drained
                    # endpoint unless every inactive product is at s.
                    row_count += 1
                    deviations.append(_share(b[s]) - share)
                    if nu:
                        row_count += 1
                        deviations.append(_share(b[s]) - (_share(1 - nu) * share + _share(nu) * trapped[s]))
    if solve_mode == "min_slack":
        # Exact epigraph elimination: for each fixed partition the smallest eta
        # satisfying all A <= b+eta and activation rows is this maximum.
        objective = model.max([0.0, *deviations])
    else:
        objective = visits
    model.minimize(objective)
    model.close()
    # Hexaly can only report an expression's type once the model is closed.
    # A row that came back as a double would mean the integer restatement did
    # not survive model building, so refuse rather than solve it unnoticed.
    non_integer = sum(1 for expression in checked if not expression.is_int())
    if non_integer:
        raise ContractError("NUMERICAL_RANGE",
                            f"{non_integer} workload rows are not integer-typed after model build")
    return stations, objective, {
        "product_count": str(catalogue.p), "station_count": str(catalogue.s),
        "set_decisions": str(len(stations)), "fixed_product_count": str(len(problem.reference.fixed)),
        "weighted_support_count": str(len(problem.weighted_supports)),
        "weighted_order_count": str(sum(w for support, w in problem.weighted_supports)),
        "scenario_count": str(len(problem.effective_scenarios)), "finite_row_count": str(row_count),
        "membership_expression_count": str(len(members)),
        "native_expression_count": str(model.nb_expressions), "effective_nu_exact": str(nu),
        "slack_formulation": "eliminated_epigraph_maximum" if solve_mode == "min_slack" else "not_applicable",
        "row_formulation": ROW_FORMULATION if solve_mode == "visits" else "rational_shares_original_model",
        "integer_typed_rows": f"{len(checked)}/{len(checked)}" if solve_mode == "visits" else "not_applicable",
    }


def _extract_assignment(stations, product_count, audit):
    sets = [list(station.value) for station in stations]
    audit["native_partition"] = canonical_json(sets)
    assignment = [-1] * product_count
    for s, products in enumerate(sets):
        for p in products:
            if type(p) is not int or not 0 <= p < product_count:
                raise ValueError("native set contains a product outside the catalogue")
            if assignment[p] != -1:
                raise ValueError("native partition duplicates a product")
            assignment[p] = s
    if any(s < 0 for s in assignment):
        raise ValueError("native partition omits catalogue products")
    return tuple(assignment)


def _finite_number(value):
    if type(value) not in (int, float):
        return None
    try:
        return value if math.isfinite(value) else None
    except OverflowError:
        return None


def _optional_native_number(solution, method, audit):
    try:
        raw = getattr(solution, method)(0)
        audit[method + "_raw"] = str(raw)
        return _finite_number(raw)
    except Exception as exc:
        # Optional bounds are allowed to be unavailable; retain the API failure.
        audit[method + "_error"] = f"{type(exc).__name__}: {exc}"
        return None


def _native_status(name):
    return {"OPTIMAL": SolveStatus.OPTIMAL_WITHIN_TOLERANCE,
            "FEASIBLE": SolveStatus.FEASIBLE,
            "INFEASIBLE": SolveStatus.NO_INCUMBENT_LIMIT,
            "INCONSISTENT": SolveStatus.PROVEN_INFEASIBLE}.get(name, SolveStatus.SOLVER_ERROR)


def solve(problem, *, seed=11, threads=1, time_limit=120, solve_mode="visits",
          warm_start=None, log_output=False) -> SolveResult:
    """Solve only the supplied frozen training problem and release native state.

    Hexaly 13 supports integer seconds (zero is useful for initial-layout checks).
    Warm starts must be structurally valid; workload-infeasible starts are allowed
    as search hints and never accepted without post-solve validation. min_slack
    minimizes the epigraph's equivalent maximum expression, using no policy cap.
    SolveResult.model_hash is the shared training hash; the audit solve_identity
    includes solve_mode and must be used when distinguishing diagnostic solves.
    """
    started = time.perf_counter()
    start = _arguments(problem, seed, threads, time_limit, solve_mode, warm_start, log_output)
    audit = {"warm_start": "reference" if warm_start is None else "supplied",
             "warm_start_hash": digest(start), "numerical_coefficients": "IEEE754_binary64_shares_int64_visit_weights",
             "model_validation_tolerance": "1e-8", "native_tolerance_configuration": "no_public_feasibility_or_integrality_setting_in_Hexaly_13",
             "native_time_limit_seconds": str(int(time_limit)),
             "solve_identity": digest({"model_hash": problem.model_hash, "solve_mode": solve_mode}),
             "optimality_provenance": "native_status_only_not_an_exact_arithmetic_certificate"}
    version, native, status = "unavailable", "NOT_STARTED", SolveStatus.SOLVER_ERROR
    assignment = objective = bound = gap = None
    bound_provenance = "unavailable"
    build_seconds = solve_seconds = 0.0
    phase, solve_started = "import", None
    try:
        hx = _load_hexaly()
        version = str(hx.version.version)
        phase = "create_optimizer"
        with hx.HexalyOptimizer() as optimizer:
            phase = "build"
            optimizer.param.seed = seed
            optimizer.param.nb_threads = threads
            optimizer.param.time_limit = int(time_limit)
            optimizer.param.verbosity = 1 if log_output else 0
            if not log_output:
                optimizer.param.log_writer = None
            stations, native_objective, model_audit = _build_model(optimizer, problem, solve_mode)
            audit.update(model_audit)
            for station in stations:
                station.value.clear()
            for p, s in enumerate(start):
                stations[s].value.add(p)
            build_seconds = time.perf_counter() - started
            phase = "solve"
            solve_started = time.perf_counter()
            optimizer.solve()
            solve_seconds = time.perf_counter() - solve_started
            phase = "extract"
            solution = optimizer.solution
            name = solution.status.name
            native = str(solution.status)
            audit["native_status_name"] = name
            audit["native_status_code"] = str(solution.status.value)
            status = _native_status(name)
            raw_bound = _optional_native_number(solution, "get_objective_bound", audit)
            # Native int64 endpoints are sentinel/uninformative bounds. Never
            # replace them with zero or with the incumbent's objective value.
            if raw_bound is not None and -_INT64_MAX < raw_bound < _INT64_MAX and name != "INCONSISTENT":
                bound = raw_bound
                bound_provenance = "Hexaly_HxSolution.get_objective_bound(0)"
            if name in ("FEASIBLE", "OPTIMAL"):
                try:
                    candidate = _extract_assignment(stations, problem.catalogue.p, audit)
                except ValueError as exc:
                    audit["validation_error"] = str(exc)
                    status = SolveStatus.NUMERICAL_ISSUE
                else:
                    candidate_objective = _finite_number(native_objective.value)
                    audit["native_objective_raw"] = str(native_objective.value)
                    if candidate_objective is None:
                        audit["validation_error"] = "native feasible incumbent has a nonfinite objective"
                        status = SolveStatus.NUMERICAL_ISSUE
                    else:
                        checked = validate_assignment(problem, candidate, objective=candidate_objective,
                                                      solve_mode=solve_mode,
                                                      min_slack=candidate_objective if solve_mode == "min_slack" else None)
                        audit["validation"] = canonical_json(checked)
                        audit["validation_hash"] = digest(checked)
                        if not checked["valid"]:
                            status = SolveStatus.NUMERICAL_ISSUE
                        elif bound is not None and Fraction(str(bound)) - Fraction(str(candidate_objective)) > _TOLERANCE:
                            audit["validation_error"] = "native minimization bound exceeds incumbent objective"
                            status = SolveStatus.NUMERICAL_ISSUE
                            bound, bound_provenance = None, "rejected_inconsistent_native_bound"
                        else:
                            assignment, objective = candidate, candidate_objective
                            slots = slot_assignment(problem.catalogue, assignment, problem.reference)
                            audit["slot_assignment"] = canonical_json(slots)
                            native_gap = _optional_native_number(solution, "get_objective_gap", audit)
                            if bound is not None and native_gap is not None and native_gap >= 0:
                                gap = native_gap
            elif name == "INCONSISTENT":
                audit["infeasibility_provenance"] = "native_INCONSISTENT_submitted_numerical_model"
            elif name == "INFEASIBLE":
                audit["termination_detail"] = "no_native_feasible_incumbent_at_configured_limit_not_a_proof"
            else:
                audit["status_error"] = "unrecognized native solution status"
    except ContractError:
        raise  # Unsupported numerical/API inputs must not masquerade as a solve.
    except Exception as exc:
        if phase == "solve" and solve_started is not None:
            solve_seconds = time.perf_counter() - solve_started
        elif solve_started is None:
            build_seconds = time.perf_counter() - started
        status = SolveStatus.RESOURCE_LIMIT if isinstance(exc, MemoryError) else SolveStatus.SOLVER_ERROR
        assignment = objective = bound = gap = None
        bound_provenance = "unavailable_after_error"
        audit["error_phase"] = phase
        audit["error_type"] = type(exc).__name__
        audit["error_message"] = str(exc)
        if hasattr(exc, "error_code"):
            audit["native_error_code"] = str(exc.error_code)
        if native == "NOT_STARTED":
            native = f"ERROR:{phase}:{type(exc).__name__}"
    return SolveResult(backend="hexaly", backend_version=version, status=status, native_status=native,
                       input_hash=problem.input_hash, model_hash=problem.model_hash,
                       seed=seed, threads=threads, time_limit=float(time_limit),
                       assignment=assignment, objective=objective, bound=bound, gap=gap,
                       build_seconds=build_seconds, solve_seconds=solve_seconds,
                       representation=_REPRESENTATION, solve_mode=solve_mode,
                       bound_provenance=bound_provenance, audit=tuple(sorted(audit.items())))
