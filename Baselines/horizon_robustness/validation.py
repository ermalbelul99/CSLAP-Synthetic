"""Independent allocation and finite-row checks, with no optimizer dependency.

Shares use integer counts and Fraction throughout. Only model rows and reported
solver objectives have an absolute 1e-8 tolerance. Exact feasibility is reported
separately. Supplying raw history audits support compression and scenario data;
without it, validation cannot certify that the supplied supports are exhaustive.
"""

from collections import Counter
from dataclasses import asdict
from fractions import Fraction

from .protocol import ACTIVATION_ARMS, SCENARIO_ARMS, TIGHTENED_ARMS, ContractError, digest
from .schema import Order, TrainingProblem


MODEL_TOLERANCE = Fraction(1, 100_000_000)
EXCLUDED_INDUSTRIAL_STATIONS = frozenset(("01.Z8", "01.15", "01.GED"))


def _assignment_structure(problem, assignment):
    catalogue = problem.catalogue
    violations, occupancy = [], [0] * catalogue.s
    if catalogue.kind == "industrial" and EXCLUDED_INDUSTRIAL_STATIONS.intersection(catalogue.station_ids):
        violations.append("industrial catalogue includes an excluded station; upstream retained universe required")
    if not isinstance(assignment, tuple):
        violations.append("assignment must be a catalogue-aligned immutable station tuple")
        return violations, occupancy
    if len(assignment) != catalogue.p:
        violations.append("assignment length does not cover exactly the full catalogue")
    for p, station in enumerate(assignment):
        if type(station) is not int or not 0 <= station < catalogue.s:
            violations.append(f"product {p}: invalid station index")
            continue
        occupancy[station] += 1
        if p < catalogue.p and catalogue.allowed_stations and station not in catalogue.allowed_stations[p]:
            violations.append(f"product {p}: forbidden station {station}")
    for s, (actual, expected) in enumerate(zip(occupancy, catalogue.capacities)):
        if actual != expected:
            violations.append(f"station {s}: occupancy {actual} != capacity {expected}")
    for p, s in sorted(set(catalogue.exogenous_fixed) | set(problem.reference.fixed)):
        if p >= len(assignment) or assignment[p] != s:
            violations.append(f"product {p}: fixed station {s} changed or missing")
    return violations, occupancy


def _order_counts(orders, product_count, industrial=False):
    """Check complete-order invariants independently of ingestion utilities."""
    if not isinstance(orders, tuple) or not orders:
        raise ContractError("DATA_CONTRACT_ERROR", "nonempty immutable complete-order window required")
    counts, ids, previous = [0] * product_count, set(), -1
    for order in orders:
        if not isinstance(order, Order):
            raise ContractError("DATA_CONTRACT_ERROR", "window contains a non-Order value")
        if (not isinstance(order.order_id, str) or not order.order_id.strip()
                or order.order_id != order.order_id.strip()
                or order.order_id in ids or type(order.chronology_key) is not int
                or order.chronology_key <= previous):
            raise ContractError("DATA_CONTRACT_ERROR", "duplicate or unordered complete orders")
        ids.add(order.order_id)
        previous = order.chronology_key
        if not isinstance(order.lines, tuple) or not order.lines:
            raise ContractError("DATA_CONTRACT_ERROR", "empty workload order")
        previous_product = -1
        for pair in order.lines:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise ContractError("DATA_CONTRACT_ERROR", "invalid product/count pair")
            p, count = pair
            if type(p) is not int or not 0 <= p < product_count:
                raise ContractError("OUT_OF_CATALOGUE", "ordered product outside frozen catalogue")
            if p <= previous_product or type(count) is not int or count <= 0:
                raise ContractError("DATA_CONTRACT_ERROR", "nonpositive count or duplicate/unsorted product")
            if industrial and count != 1:
                raise ContractError("DATA_CONTRACT_ERROR", "industrial workload must count distinct product-order pairs")
            counts[p] += count
            previous_product = p
    return tuple(counts)


def _support_visits(weighted_supports, assignment):
    if (not isinstance(assignment, tuple) or not assignment
            or any(type(s) is not int or s < 0 for s in assignment)):
        raise ContractError("DATA_CONTRACT_ERROR", "complete nonnegative station tuple required")
    if not isinstance(weighted_supports, tuple):
        raise ContractError("DATA_CONTRACT_ERROR", "immutable weighted supports required")
    total, seen = 0, set()
    for entry in weighted_supports:
        if not isinstance(entry, tuple) or len(entry) != 2:
            raise ContractError("DATA_CONTRACT_ERROR", "invalid weighted support")
        support, weight = entry
        if (not isinstance(support, tuple) or not support
                or any(type(p) is not int or p < 0 or p >= len(assignment) for p in support)):
            raise ContractError("DATA_CONTRACT_ERROR", "support product outside assignment")
        if (tuple(sorted(set(support))) != support or support in seen
                or type(weight) is not int or weight <= 0):
            raise ContractError("DATA_CONTRACT_ERROR", "duplicate support or invalid exact support weight")
        seen.add(support)
        total += weight * len({assignment[p] for p in support})
    return total


def _targets_and_caps(problem, optimization=False):
    reference = problem.reference
    total = sum(reference.historical_counts)
    target = tuple(Fraction(c, total) for c in reference.station_line_counts)
    delta = Fraction(problem.delta)
    if optimization and problem.arm in TIGHTENED_ARMS:
        delta *= 1 - Fraction(problem.tightening)
    return target, tuple(min(Fraction(1), b + delta) for b in target)


def _floors(problem, optimization=False):
    """Two-sided lower ceilings max(0, b_s - delta), recomputed here rather than
    read from the schema so the validator stays independent of it. None under
    the upper-only rule."""
    if getattr(problem, "rule", "upper_only") != "two_sided":
        return None
    reference = problem.reference
    total = sum(reference.historical_counts)
    delta = Fraction(problem.delta)
    if optimization and problem.arm in TIGHTENED_ARMS:
        delta *= 1 - Fraction(problem.tightening)
    return tuple(max(Fraction(0), Fraction(c, total) - delta) for c in reference.station_line_counts)


def _finite_rows(problem, assignment):
    """Recompute both uncertainty endpoints directly from the mathematical rows.

    This is deliberately independent of M1's uncertainty functions and of the
    shared contract's floating-point effective_nu / effective_scenarios helpers.
    """
    reference, station_count = problem.reference, problem.catalogue.s
    inactive = [0] * station_count
    fixed = {p for p, s in reference.fixed} | {p for p, s in problem.catalogue.exogenous_fixed}
    for p, count in enumerate(reference.historical_counts):
        if count == 0:
            inactive[assignment[p]] += 1
    nu = Fraction(problem.nu) if problem.arm in ACTIVATION_ARMS and any(inactive) else Fraction(0)
    # Activation mass can avoid station s only if some inactive product lies
    # elsewhere. When EVERY inactive product sits at s, the mass is trapped
    # there and the lowest attainable share of s is A_sk itself, not (1-nu) A_sk.
    # (13 Sep 2026 correction; zero for every feasible layout of the executed
    # datasets, whose fixed inactive products span several stations.)
    total_inactive = sum(inactive)
    trapped = tuple(int(total_inactive > 0 and inactive[s] == total_inactive)
                    for s in range(station_count))
    if problem.arm in ("NOM", "TIGHT"):
        specifications = [(0, reference.origin, "history",
                           tuple((p, c) for p, c in enumerate(reference.historical_counts) if c),
                           sum(reference.historical_counts))]
    else:
        specifications = [(v.start, v.stop, v.label, v.counts, v.total_lines) for v in problem.scenarios]
    rows, envelope = [], [Fraction(0)] * station_count
    lowest = [Fraction(1)] * station_count
    for start, stop, label, counts, total in specifications:
        station_lines, fixed_lines = [0] * station_count, [0] * station_count
        for p, count in counts:
            station = assignment[p]
            station_lines[station] += count
            if p in fixed:
                fixed_lines[station] += count
        shares = tuple(Fraction(c, total) for c in station_lines)
        activated = tuple((1 - nu) * a + nu * int(inactive[s] > 0) for s, a in enumerate(shares))
        worst = tuple(max(a, v) for a, v in zip(shares, activated))
        # Lowest attainable share: activation mass placed at OTHER stations,
        # unless every inactive product is at this one (trapped).
        drained = tuple((1 - nu) * a + nu * trapped[s] for s, a in enumerate(shares))
        least = tuple(min(a, v) for a, v in zip(shares, drained))
        envelope = [max(old, new) for old, new in zip(envelope, worst)]
        lowest = [min(old, new) for old, new in zip(lowest, least)]
        rows.append(dict(start=start, stop=stop, label=label, total_lines=total,
                         station_line_counts=station_lines, fixed_station_line_counts=fixed_lines,
                         shares=shares, activation_shares=activated, worst_shares=worst,
                         drained_shares=drained, least_shares=least,
                         activation_trapped=list(trapped)))
    return rows, tuple(envelope), tuple(inactive), nu, tuple(lowest)


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Fraction)):
        raise ContractError("DATA_CONTRACT_ERROR", f"{name} must be finite numeric data")
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        raise ContractError("DATA_CONTRACT_ERROR", f"{name} must be finite numeric data") from exc


def _finite_float(value):
    """An unrepresentable display value is null; its exact companion is retained."""
    try:
        return float(value)
    except OverflowError:
        return None


def _history_audit(problem, history, violations):
    """Return counts/supports rebuilt from raw orders, not supplied compression."""
    catalogue, reference = problem.catalogue, problem.reference
    counts = _order_counts(history, catalogue.p, catalogue.kind == "industrial")
    supports = tuple(sorted(Counter(tuple(p for p, c in o.lines) for o in history).items()))
    if len(history) != reference.origin:
        violations.append("raw history length differs from origin")
    if digest([asdict(o) for o in history]) != reference.history_hash:
        violations.append("raw history hash mismatch")
    if counts != reference.historical_counts:
        violations.append("raw history product workload differs from reference")
    if dict(supports) != dict(problem.weighted_supports):
        violations.append("raw history supports differ from supplied supports (omission or wrong weight)")
    if problem.arm in SCENARIO_ARMS:
        origin, n = reference.origin, problem.n
        expected = Counter((start, start + n) for start in range(origin % n, origin, n))
        expected[(0, origin)] += 1
        if Counter((v.start, v.stop) for v in problem.scenarios) != expected:
            violations.append("scenario boundaries omit or duplicate complete historical blocks/history")
    for scenario in problem.scenarios:
        if not 0 <= scenario.start < scenario.stop <= len(history):
            violations.append("scenario boundary lies outside raw history")
            continue
        observed = Counter()
        for order in history[scenario.start:scenario.stop]:
            observed.update(dict(order.lines))
        if tuple(sorted(observed.items())) != scenario.counts or sum(observed.values()) != scenario.total_lines:
            violations.append(f"scenario [{scenario.start},{scenario.stop}) differs from raw history")
    return supports


def validate_assignment(problem: TrainingProblem, assignment: tuple[int, ...],
                        objective=None, solve_mode="visits", min_slack=None, history=None) -> dict:
    """Certify structure, all finite workload rows and an optional objective.

    In min_slack mode, min_slack is the incumbent epigraph eta; if omitted,
    objective supplies eta. An epigraph above the layout's necessary slack is
    feasible (it need not be optimal). actual_objective is eta in this mode;
    minimum_required_slack separately reports the tight value for this layout.
    Original policy caps are descriptive only in a min_slack certificate.
    The eta nonnegativity row uses the same absolute model tolerance.
    """
    if not isinstance(problem, TrainingProblem):
        raise ContractError("DATA_CONTRACT_ERROR", "TrainingProblem required")
    violations, occupancy = _assignment_structure(problem, assignment)
    result = dict(valid=False, violations=violations, structural_valid=not violations,
                  solve_mode=solve_mode if isinstance(solve_mode, str) else None,
                  actual_objective=None, actual_visit_count=None,
                  maximum_model_excess=None, maximum_model_residual=None,
                  occupancy=occupancy, station_ids=list(problem.catalogue.station_ids),
                  scenario_shares=[], station_shares=[], model_feasible=None,
                  model_feasible_exact=None, history_checked=False,
                  history_audit="not_supplied_support_completeness_unverified",
                  objective_checked=False, model_tolerance=float(MODEL_TOLERANCE),
                  objective_tolerance=float(MODEL_TOLERANCE))
    if violations:
        return result
    if solve_mode not in ("visits", "min_slack"):
        violations.append("unknown solve_mode")
        return result
    supports = problem.weighted_supports
    if history is not None:
        try:
            supports = _history_audit(problem, history, violations)
            result["history_checked"] = True
            result["history_audit"] = "raw_history_recomputed"
        except ContractError as exc:
            violations.append(str(exc))
            result["history_audit"] = "invalid_raw_history"
    try:
        visits = _support_visits(supports, assignment)
        _support_visits(problem.weighted_supports, assignment)
        if sum(weight for support, weight in problem.weighted_supports) != problem.reference.origin:
            violations.append("support weights omit historical orders")
        appearances = [0] * problem.catalogue.p
        for support, weight in problem.weighted_supports:
            for p in support:
                appearances[p] += weight
        for p, (appearances_p, lines) in enumerate(zip(appearances, problem.reference.historical_counts)):
            if ((appearances_p == 0) != (lines == 0) or appearances_p > lines
                    or (problem.catalogue.kind == "industrial" and appearances_p != lines)):
                violations.append(f"product {p}: support incidence inconsistent with historical workload")
    except ContractError as exc:
        violations.append(str(exc))
        return result
    result["actual_visit_count"] = visits
    targets, policy_caps = _targets_and_caps(problem)
    _, model_caps = _targets_and_caps(problem, optimization=True)
    policy_floors, model_floors = _floors(problem), _floors(problem, optimization=True)
    two_sided = policy_floors is not None
    rows, envelope, inactive, nu, lowest = _finite_rows(problem, assignment)
    required = max(Fraction(0), max(v - b for v, b in zip(envelope, targets)))
    if two_sided:
        # The two-sided slack a layout needs is the larger of its upward and
        # downward excursions over the whole uncertainty set.
        required = max(required, max(b - v for v, b in zip(lowest, targets)))
    result["rule"] = "two_sided" if two_sided else "upper_only"
    result["minimum_required_slack"] = float(required)
    result["minimum_required_slack_exact"] = str(required)
    result["original_policy_feasible_exact"] = (
        all(v <= cap for v, cap in zip(envelope, policy_caps))
        and (not two_sided or all(v >= f for v, f in zip(lowest, policy_floors))))
    if solve_mode == "min_slack":
        try:
            eta = _number(min_slack if min_slack is not None else objective, "min_slack eta")
            if eta < -MODEL_TOLERANCE:
                raise ContractError("DATA_CONTRACT_ERROR", "min_slack eta violates nonnegativity beyond model tolerance")
        except ContractError as exc:
            violations.append(str(exc))
            return result
        model_caps = tuple(b + eta for b in targets)
        if two_sided:
            model_floors = tuple(max(Fraction(0), b - eta) for b in targets)
        actual = eta
        result["actual_objective"] = _finite_float(eta)
    else:
        actual = Fraction(visits)
        result["actual_objective"] = visits
        if min_slack is not None:
            violations.append("min_slack supplied for visits objective")
    result["actual_objective_exact"] = str(actual)
    if objective is not None:
        result["objective_checked"] = True
        try:
            difference = abs(_number(objective, "objective") - actual)
            result["objective_error_exact"] = str(difference)
            if difference > MODEL_TOLERANCE:
                violations.append("objective mismatch with independently recomputed objective")
        except ContractError as exc:
            violations.append(str(exc))
    residuals = tuple(v - cap for v, cap in zip(envelope, model_caps))
    maximum = max(residuals)
    # Two-sided: a floor residual is positive when the LOWEST attainable share
    # falls below the floor. It joins the same maximum so one number still
    # answers "by how much does this layout miss its model rows".
    floor_residuals = (tuple(f - v for v, f in zip(lowest, model_floors)) if two_sided
                       else tuple(Fraction(0) for _ in envelope))
    if two_sided:
        maximum = max(maximum, max(floor_residuals))
    result.update(maximum_model_residual=_finite_float(maximum),
                  maximum_model_residual_exact=str(maximum),
                  maximum_model_excess=float(max(Fraction(0), maximum)),
                  maximum_model_excess_exact=str(max(Fraction(0), maximum)),
                  model_feasible=maximum <= MODEL_TOLERANCE,
                  model_feasible_exact=maximum <= 0, effective_nu=float(nu),
                  effective_nu_exact=str(nu), inactive_counts=list(inactive),
                  worst_scenario_envelope=[float(v) for v in envelope],
                  worst_scenario_envelope_exact=[str(v) for v in envelope],
                  lowest_scenario_envelope=[float(v) for v in lowest],
                  lowest_scenario_envelope_exact=[str(v) for v in lowest],
                  floors=[_finite_float(v) for v in model_floors] if two_sided else None,
                  floors_exact=[str(v) for v in model_floors] if two_sided else None,
                  floor_residuals=[_finite_float(v) for v in floor_residuals] if two_sided else None,
                  floor_residuals_exact=[str(v) for v in floor_residuals] if two_sided else None)
    for index, row in enumerate(rows):
        encoded = {key: value for key, value in row.items()
                   if key not in ("shares", "activation_shares", "worst_shares",
                                  "drained_shares", "least_shares")}
        encoded["index"] = index
        for name in ("shares", "activation_shares", "worst_shares", "drained_shares", "least_shares"):
            encoded[name] = [float(v) for v in row[name]]
            encoded[name + "_exact"] = [str(v) for v in row[name]]
        for name, shares in (("base_residuals", row["shares"]), ("activation_residuals", row["activation_shares"])):
            residual = [a - cap for a, cap in zip(shares, model_caps)]
            encoded[name] = [_finite_float(v) for v in residual]
            encoded[name + "_exact"] = [str(v) for v in residual]
        result["scenario_shares"].append(encoded)
        for s, worst in enumerate(row["worst_shares"]):
            if worst - model_caps[s] > MODEL_TOLERANCE:
                violations.append(f"station {s}, scenario {index}: robust model cap exceeded")
        if two_sided:
            for s, least in enumerate(row["least_shares"]):
                if model_floors[s] - least > MODEL_TOLERANCE:
                    violations.append(f"station {s}, scenario {index}: robust model floor breached")
    result["station_shares"] = [
        dict(station_index=s, station_id=problem.catalogue.station_ids[s], target=float(targets[s]),
             target_exact=str(targets[s]), cap=_finite_float(model_caps[s]), cap_exact=str(model_caps[s]),
             worst_share=float(envelope[s]), worst_share_exact=str(envelope[s]),
             residual=_finite_float(residuals[s]), residual_exact=str(residuals[s]),
             borderline=abs(residuals[s]) <= MODEL_TOLERANCE,
             floor=(_finite_float(model_floors[s]) if two_sided else None),
             floor_exact=(str(model_floors[s]) if two_sided else None),
             lowest_share=float(lowest[s]), lowest_share_exact=str(lowest[s]),
             floor_residual=(_finite_float(floor_residuals[s]) if two_sided else None),
             floor_residual_exact=(str(floor_residuals[s]) if two_sided else None))
        for s in range(problem.catalogue.s)]
    result["valid"] = not violations
    return result
