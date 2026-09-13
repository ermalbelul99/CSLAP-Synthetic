"""CPLEX reference MILP with complete workload/support accounting.

The commercial dependency is imported only inside solve(). Native status codes
are interpreted explicitly: a time-limit 'infeasible' incumbent status is not a
proof that the model is infeasible. No raw data or future orders are read here.
"""

from fractions import Fraction
import math
from time import perf_counter

from .protocol import ACTIVATION_ARMS, ContractError, canonical_json
from .schema import SolveResult, SolveStatus, TrainingProblem
from .uncertainty import ROW_FORMULATION, integer_cap_rows, minimum_slack_for_assignment
from .validation import validate_assignment


def normalize_status(code, has_incumbent):
    if code in (3, 103):
        return SolveStatus.SOLVER_ERROR if has_incumbent else SolveStatus.PROVEN_INFEASIBLE
    if code in (1, 101, 102):
        return SolveStatus.OPTIMAL_WITHIN_TOLERANCE if has_incumbent else SolveStatus.SOLVER_ERROR
    if code in (5, 6, 109, 110, 115, 116, 117):
        return SolveStatus.NUMERICAL_ISSUE
    if code in (2, 4, 118, 119):
        return SolveStatus.SOLVER_ERROR  # Unbounded/ambiguous is not an infeasibility certificate.
    if has_incumbent:
        return SolveStatus.FEASIBLE
    if code in (111, 112, 1016):
        return SolveStatus.RESOURCE_LIMIT
    if code in (10, 11, 12, 13, 21, 22, 25, 105, 106, 107, 108, 113, 114, 128, 129, 131, 132):
        return SolveStatus.NO_INCUMBENT_LIMIT
    return SolveStatus.SOLVER_ERROR


def finite_native(value):
    """Reject native nonfinite and infinity-sentinel values instead of inventing bounds."""
    if value is None or isinstance(value, bool):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return value if math.isfinite(value) and abs(value) < 1e20 else None


def solve(problem, *, seed=11, threads=1, time_limit=120, solve_mode="visits",
          warm_start=None, log_output=False):
    if not isinstance(problem, TrainingProblem):
        raise ContractError("DATA_CONTRACT_ERROR", "immutable TrainingProblem required")
    if type(seed) is not int or not 0 <= seed <= 2_147_483_647 or type(threads) is not int or threads <= 0:
        raise ContractError("DATA_CONTRACT_ERROR", "valid integer seed and positive thread count required")
    if isinstance(time_limit, bool) or not isinstance(time_limit, (int, float)) or not math.isfinite(time_limit) or time_limit <= 0:
        raise ContractError("DATA_CONTRACT_ERROR", "positive finite time limit required")
    if solve_mode not in ("visits", "min_slack") or type(log_output) is not bool:
        raise ContractError("DATA_CONTRACT_ERROR", "invalid objective mode or logging option")
    if warm_start is not None:
        problem.catalogue.check_storage(warm_start, problem.reference.fixed)
    # Check non-row integrity even if the reference is not robust feasible.
    initial = validate_assignment(problem, problem.reference.assignment)
    # Row violations of the reference (cap exceeded, or floor breached under the
    # two-sided rule) are what a solve or a min-slack diagnostic is for.
    non_row_errors = [v for v in initial["violations"]
                      if "robust model cap exceeded" not in v and "robust model floor breached" not in v]
    if non_row_errors:
        raise ContractError("DATA_CONTRACT_ERROR", "; ".join(non_row_errors))

    base = dict(backend="cplex", backend_version="unavailable", input_hash=problem.input_hash,
                model_hash=problem.model_hash, seed=seed, threads=threads, time_limit=float(time_limit),
                representation="binary_station_assignment_fixed_elimination_exact_supports",
                solve_mode=solve_mode)
    audit = {"numerical_feasibility_tolerance": "1e-9", "integrality_tolerance": "1e-9",
             "support_count": str(len(problem.weighted_supports)),
             "support_order_weight": str(sum(w for support, w in problem.weighted_supports))}
    model, built, started_solve = None, None, None
    started = perf_counter()
    try:
        import cplex
        import docplex
        from docplex.mp.model import Model

        base["backend_version"] = cplex.__version__
        audit["docplex_version"] = docplex.__version__
        model = Model(name="horizon_cslap", log_output=log_output)
        model.parameters.threads = threads
        model.parameters.randomseed = seed
        model.parameters.timelimit = time_limit
        model.parameters.simplex.tolerances.feasibility = 1e-9
        model.parameters.mip.tolerances.integrality = 1e-9
        model.parameters.mip.tolerances.mipgap = 0
        model.parameters.mip.tolerances.absmipgap = 1e-9
        catalogue, reference = problem.catalogue, problem.reference
        fixed = dict(reference.fixed)
        movable = tuple(p for p in range(catalogue.p) if p not in fixed)
        x = {(p, s): model.binary_var(name=f"x_{p}_{s}")
             for p in movable for s in catalogue.eligible_stations(p)}
        for p in movable:
            model.add_constraint(model.sum(x[p, s] for s in catalogue.eligible_stations(p)) == 1)
        for s, capacity in enumerate(catalogue.capacities):
            reserved = sum(station == s for station in fixed.values())
            model.add_constraint(model.sum(x[p, s] for p in movable if (p, s) in x) == capacity - reserved)

        def linear_or(products, station, name):
            if any(fixed.get(p) == station for p in products):
                return 1
            terms = [x[p, station] for p in products if (p, station) in x]
            if not terms:
                return 0
            if len(terms) == 1:
                return terms[0]
            variable = model.binary_var(name=name)
            model.add_constraints(variable >= term for term in terms)
            model.add_constraint(variable <= model.sum(terms))
            return variable

        def linear_and(products, station, name):
            """1 exactly when every product of ``products`` sits at ``station``."""
            if not products or any(fixed.get(p) not in (None, station) for p in products):
                return 0
            terms = []
            for p in products:
                if p in fixed:
                    continue                      # fixed here: factor one
                if (p, station) not in x:
                    return 0                      # can never be here
                terms.append(x[p, station])
            if not terms:
                return 1
            if len(terms) == 1:
                return terms[0]
            variable = model.binary_var(name=name)
            model.add_constraints(variable <= term for term in terms)
            model.add_constraint(variable >= model.sum(terms) - (len(terms) - 1))
            return variable

        # Store the touch expressions for a complete, reproducible warm start.
        touches = {}
        if solve_mode == "visits":
            for k, (support, weight) in enumerate(problem.weighted_supports):
                for s in range(catalogue.s):
                    touches[k, s] = linear_or(support, s, f"visit_{k}_{s}")
            objective = model.sum(weight * touches[k, s]
                                  for k, (support, weight) in enumerate(problem.weighted_supports)
                                  for s in range(catalogue.s))
        else:
            objective = model.continuous_var(lb=0, ub=1, name="eta")
        nu = Fraction(problem.nu) if problem.arm in ACTIVATION_ARMS and reference.inactive else Fraction(0)
        indicators = [linear_or(reference.inactive, s, f"inactive_{s}") if nu else 0
                      for s in range(catalogue.s)]
        # g_s: every inactive product at s (activation mass trapped there).
        trapped = [linear_and(reference.inactive, s, f"trapped_{s}") if nu and problem.two_sided else 0
                   for s in range(catalogue.s)]
        caps = problem.optimization_caps
        if solve_mode == "visits":
            # Same exact integer-count restatement as the Hexaly backend, so the
            # two are compared on identical rows. Integer coefficients and an
            # integer threshold mean a sub-unit feasibility tolerance cannot
            # admit a layout that violates the true share ceiling.
            rows, _ = integer_cap_rows(problem)
            for row in rows:
                s, scenario = row["station"], problem.effective_scenarios[row["scenario"]]
                multiplier = row["multiplier"]
                constant = multiplier * sum(c for p, c in scenario.counts if fixed.get(p) == s)
                load = model.linear_expr(constant=constant)
                if multiplier:
                    load += model.sum((multiplier * count) * x[p, s]
                                      for p, count in scenario.counts if (p, s) in x)
                if row["activation_coefficient"]:
                    load += row["activation_coefficient"] * indicators[s]
                if row.get("all_inactive_coefficient"):
                    load += row["all_inactive_coefficient"] * trapped[s]
                if row["sense"] == ">=":
                    model.add_constraint(load >= row["threshold"])
                else:
                    model.add_constraint(load <= row["threshold"])
            audit["row_formulation"] = ROW_FORMULATION
        else:
            audit["row_formulation"] = "rational_shares_original_model"
            two_sided = problem.two_sided
            for k, scenario in enumerate(problem.effective_scenarios):
                for s in range(catalogue.s):
                    constant = sum(c for p, c in scenario.counts if fixed.get(p) == s) / scenario.total_lines
                    load = model.linear_expr(constant=constant)
                    load += model.sum((count / scenario.total_lines) * x[p, s]
                                      for p, count in scenario.counts if (p, s) in x)
                    target = reference.station_line_counts[s] / reference.total_lines
                    cap = target + objective
                    model.add_constraint(load <= cap)
                    if nu:
                        model.add_constraint(float(1 - nu) * load + float(nu) * indicators[s] <= cap)
                    if two_sided:
                        # Lowest attainable share must stay above b_s - eta: the
                        # historical share itself and, with activation, the drained
                        # endpoint unless every inactive product is at s (g_s = 1).
                        model.add_constraint(load >= target - objective)
                        if nu:
                            model.add_constraint(float(1 - nu) * load + float(nu) * trapped[s]
                                                 >= target - objective)
        model.minimize(objective)
        audit.update(assignment_binaries=str(len(x)), variables=str(model.number_of_variables),
                     constraints=str(model.number_of_constraints), fixed_products=str(len(fixed)))

        candidate = warm_start if warm_start is not None else reference.assignment
        eta = minimum_slack_for_assignment(problem, candidate) if solve_mode == "min_slack" else None
        check = validate_assignment(problem, candidate, solve_mode=solve_mode, min_slack=eta)
        if check["valid"] and x:
            start = model.new_solution()
            for (p, s), variable in x.items():
                start.add_var_value(variable, int(candidate[p] == s))
            for (k, s), expression in touches.items():
                if not isinstance(expression, int):
                    start.add_var_value(expression, int(any(candidate[p] == s for p in problem.weighted_supports[k][0])))
            for s, expression in enumerate(indicators):
                if not isinstance(expression, int):
                    start.add_var_value(expression, int(any(candidate[p] == s for p in reference.inactive)))
            if solve_mode == "min_slack":
                start.add_var_value(objective, min(1, eta + 1e-9))
            model.add_mip_start(start, complete_vars=True)
            audit["warm_start"] = "validated_complete_layout"
        else:
            audit["warm_start"] = "not_used_no_binaries" if not x else "not_used_workload_infeasible"

        built = perf_counter()
        started_solve = perf_counter()
        solution = model.solve(log_output=log_output)
        elapsed = perf_counter() - started_solve
        details = model.solve_details
        native = f"{details.status_code}: {details.status}"
        status = normalize_status(details.status_code, solution is not None)
        bound = finite_native(details.best_bound)
        gap = finite_native(details.mip_relative_gap) if solution is not None else None
        if gap is not None and gap < 0:
            audit["invalid_native_gap"] = str(gap)
            gap = None
        assignment, value = None, None
        if solution is not None:
            proposed = list(reference.assignment)
            extraction_errors = []
            for p in movable:
                values = [(s, solution.get_value(x[p, s])) for s in catalogue.eligible_stations(p)]
                chosen = [s for s, v in values if abs(v - 1) <= 1e-8]
                if len(chosen) != 1 or any(min(abs(v), abs(v - 1)) > 1e-8 for s, v in values):
                    extraction_errors.append(f"nonintegral assignment for product {p}")
                else:
                    proposed[p] = chosen[0]
            proposed = tuple(proposed)
            native_value = finite_native(solution.objective_value)
            certificate = validate_assignment(problem, proposed, objective=native_value,
                                              solve_mode=solve_mode,
                                              min_slack=native_value if solve_mode == "min_slack" else None)
            if native_value is None:
                extraction_errors.append("objective unavailable or nonfinite")
            extraction_errors.extend(certificate["violations"])
            if not extraction_errors and status in (SolveStatus.FEASIBLE, SolveStatus.OPTIMAL_WITHIN_TOLERANCE):
                assignment, value = proposed, native_value
                audit["validation"] = "passed_independent_finite_rows_and_exact_support_objective"
                audit["model_feasible_exact"] = str(certificate["model_feasible_exact"])
                audit["minimum_required_slack"] = certificate["minimum_required_slack_exact"]
            else:
                status = SolveStatus.NUMERICAL_ISSUE
                audit["rejected_incumbent"] = canonical_json(extraction_errors or ["native status does not authorize acceptance"])
                gap = None
        if bound is not None and value is not None and bound > value + 1e-8:
            audit["invalid_native_bound"] = str(bound)
            bound, gap = None, None
        return SolveResult(**base, status=status, native_status=native, assignment=assignment,
                           objective=value, bound=bound, gap=gap, build_seconds=built - started,
                           solve_seconds=elapsed, bound_provenance="native_cplex_best_bound" if bound is not None else "unavailable",
                           audit=tuple(sorted(audit.items())))
    except Exception as exc:
        # Native errors remain explicit failed records, never fabricated infeasibility.
        audit["exception_type"] = type(exc).__name__
        audit["exception_message"] = str(exc)[:500]
        status = SolveStatus.RESOURCE_LIMIT if isinstance(exc, MemoryError) else SolveStatus.SOLVER_ERROR
        now = perf_counter()
        return SolveResult(**base, status=status, native_status=f"exception: {type(exc).__name__}",
                           build_seconds=(built if built is not None else now) - started,
                           solve_seconds=now - started_solve if started_solve is not None else 0,
                           audit=tuple(sorted(audit.items())))
    finally:
        if model is not None:
            model.end()
