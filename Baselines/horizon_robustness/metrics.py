"""Score an already frozen layout on exactly one complete future horizon.

No solver, reference reconstruction or uncertainty adaptation is available here.
All policy pass/fail decisions are rational comparisons with no numerical slack.
Fraction strings accompany share diagnostics for lossless JSON interchange.
"""

from dataclasses import asdict
from fractions import Fraction

from .protocol import ContractError, digest
from .reference import slot_assignment
from .schema import Order, TrainingProblem
from .validation import (MODEL_TOLERANCE, _assignment_structure, _finite_float, _floors,
                         _order_counts, _support_visits, _targets_and_caps,
                         validate_assignment)


def visit_count(orders: tuple[Order, ...], assignment: tuple[int, ...]) -> int:
    """Distinct station touches per complete order; line multiplicity is irrelevant."""
    if not isinstance(assignment, tuple) or not assignment or any(type(s) is not int or s < 0 for s in assignment):
        raise ContractError("DATA_CONTRACT_ERROR", "complete nonnegative station tuple required")
    if orders == ():
        return 0
    _order_counts(orders, len(assignment))
    return sum(len({assignment[p] for p, count in order.lines}) for order in orders)


def support_visit_count(weighted_supports, assignment: tuple[int, ...]) -> int:
    """Count visits in an exact, untruncated weighted support representation."""
    return _support_visits(weighted_supports, assignment)


def evaluate_layout(problem: TrainingProblem, assignment: tuple[int, ...],
                    future: tuple[Order, ...], horizon=None) -> dict:
    """Evaluate a primary (n) or explicit secondary horizon without reoptimization.

    The caller supplies the immediate future segment. The training schema stores
    a history hash, not its last order ID or a full stream: adjacency and missing
    source rows therefore cannot be authenticated by this API. Boundary records
    state that limitation rather than inferring contiguous numerical order IDs.
    Native solve statuses and paired run IDs also belong to the caller's record.
    Industrial inputs must already exclude 01.Z8, 01.15 and 01.GED. All products
    and workloads in the retained catalogue, including frozen stations, count.
    """
    if not isinstance(problem, TrainingProblem):
        raise ContractError("DATA_CONTRACT_ERROR", "TrainingProblem required")
    violations, occupancy = _assignment_structure(problem, assignment)
    if violations:
        raise ContractError("DATA_CONTRACT_ERROR", "; ".join(violations))
    slots = slot_assignment(problem.catalogue, assignment, problem.reference)
    # Freeze the physical allocation identity before inspecting future orders.
    layout_hash = digest(dict(product_ids=problem.catalogue.product_ids,
                              station_ids=problem.catalogue.station_ids,
                              assignment=assignment, slot_assignment=slots))
    validation = validate_assignment(problem, assignment)
    if horizon is None:
        horizon = problem.n
    if type(horizon) is not int or horizon <= 0:
        raise ContractError("DATA_CONTRACT_ERROR", "positive integer scoring horizon required")
    if not isinstance(future, tuple):
        raise ContractError("DATA_CONTRACT_ERROR", "immutable complete future window required")
    if len(future) < horizon:
        raise ContractError("INSUFFICIENT_FUTURE", "future must contain the entire requested horizon")
    if len(future) != horizon:
        raise ContractError("DATA_CONTRACT_ERROR", "future length differs from requested horizon")
    catalogue, reference = problem.catalogue, problem.reference
    product_counts = _order_counts(future, catalogue.p, catalogue.kind == "industrial")
    total = sum(product_counts)
    station_counts, fixed_counts, inactive_lines = [0] * catalogue.s, [0] * catalogue.s, [0] * catalogue.s
    fixed = {p for p, s in reference.fixed} | {p for p, s in catalogue.exogenous_fixed}
    inactive = {p for p, count in enumerate(reference.historical_counts) if count == 0}
    historical_counts = [0] * catalogue.s
    fixed_historical_counts = [0] * catalogue.s
    for p, station in enumerate(assignment):
        station_counts[station] += product_counts[p]
        historical_counts[station] += reference.historical_counts[p]
        if p in fixed:
            fixed_counts[station] += product_counts[p]
            fixed_historical_counts[station] += reference.historical_counts[p]
        if p in inactive:
            inactive_lines[station] += product_counts[p]
    targets, caps = _targets_and_caps(problem)
    floors = _floors(problem)                      # None under the upper-only rule
    two_sided = floors is not None
    shares = tuple(Fraction(c, total) for c in station_counts)
    residuals = tuple(r - cap for r, cap in zip(shares, caps))
    # Two-sided: a floor residual is positive when the realized share fell
    # below b_s - delta. Joint compliance then requires BOTH sides.
    # Under the upper-only rule there are no floors and no floor residuals;
    # feeding zeros here clipped maximum_residual at zero and flagged every
    # interior layout as borderline (13 Sep 2026 regression fix).
    floor_residuals = tuple(f - r for r, f in zip(shares, floors)) if two_sided else None
    cap_sum = sum(caps)
    lower = tuple(max(Fraction(0), 1 - cap_sum + cap) for cap in caps)
    envelope = tuple(Fraction(v) for v in validation["worst_scenario_envelope_exact"])
    lowest = tuple(Fraction(v) for v in validation["lowest_scenario_envelope_exact"])
    inactive_counts = validation["inactive_counts"]
    nu = Fraction(validation["effective_nu_exact"])
    novelty = tuple(r - bound for r, bound in zip(shares, envelope))
    # Lower-direction novelty (two-sided only): the realized share fell below
    # the lowest share the uncertainty set allowed. A witness that the future
    # left the modelled set downward, independent of whether a floor broke.
    shortfall = tuple(bound - r for r, bound in zip(shares, lowest)) if two_sided else None
    activation = Fraction(sum(inactive_lines), total)
    visits = visit_count(future, assignment)
    historical_visits = support_visit_count(problem.weighted_supports, assignment)
    known_supports = {support for support, weight in problem.weighted_supports}
    stations = []
    for s in range(catalogue.s):
        station = dict(station_index=s, station_id=catalogue.station_ids[s],
                       occupancy=occupancy[s], capacity=catalogue.capacities[s],
                       line_count=station_counts[s], fixed_line_count=fixed_counts[s],
                       historical_line_count=historical_counts[s],
                       fixed_historical_line_count=fixed_historical_counts[s],
                       inactive_count=inactive_counts[s], inactive_line_count=inactive_lines[s],
                       feasible=residuals[s] <= 0 and (not two_sided or floor_residuals[s] <= 0),
                       borderline=(abs(residuals[s]) <= MODEL_TOLERANCE
                                   or (two_sided and abs(floor_residuals[s]) <= MODEL_TOLERANCE)),
                       beyond_worst_scenario=novelty[s] > 0,
                       below_lowest_scenario=(shortfall[s] > 0) if two_sided else None,
                       lowest_share=float(lowest[s]), lowest_share_exact=str(lowest[s]),
                       shortfall_residual=(float(shortfall[s]) if two_sided else None),
                       shortfall_residual_exact=(str(shortfall[s]) if two_sided else None),
                       floor=(float(floors[s]) if two_sided else None),
                       floor_exact=(str(floors[s]) if two_sided else None),
                       floor_residual=(float(floor_residuals[s]) if two_sided else None),
                       floor_residual_exact=(str(floor_residuals[s]) if two_sided else None),
                       below_floor=(floor_residuals[s] > 0) if two_sided else False)
        values = dict(share=shares[s], target=targets[s], cap=caps[s], residual=residuals[s],
                      fixed_share=Fraction(fixed_counts[s], total),
                      historical_share=Fraction(historical_counts[s], reference.total_lines),
                      fixed_historical_share=Fraction(fixed_historical_counts[s], reference.total_lines),
                      implied_lower_bound=lower[s], lower_bound_distance=shares[s] - lower[s],
                      decrease=max(Fraction(0), targets[s] - shares[s]),
                      positive_excess=max(Fraction(0), residuals[s]),
                      inactive_share=Fraction(inactive_lines[s], total), worst_share=envelope[s],
                      novelty_residual=novelty[s])
        for key, value in values.items():
            station[key], station[key + "_exact"] = float(value), str(value)
        station["cap_relative_to_target"] = _finite_float(caps[s] / targets[s]) if targets[s] else None
        station["cap_relative_to_target_exact"] = str(caps[s] / targets[s]) if targets[s] else None
        stations.append(station)
    # One "worst excess" answers both sides: the larger of the worst overshoot
    # above a cap and the worst shortfall below a floor.
    if two_sided:
        maximum = max(max(residuals), max(floor_residuals))
        breaches = tuple(max(r, f) for r, f in zip(residuals, floor_residuals))
    else:
        maximum, breaches = max(residuals), residuals
    sources = [asdict(source) for source in catalogue.source_files]
    result = dict(
        revision=problem.revision, dataset_id=catalogue.dataset_id, arm=problem.arm,
        evaluation_universe="full_frozen_retained_catalogue",
        input_hash=problem.input_hash, catalogue_hash=catalogue.fingerprint,
        source_files=sources, source_hash=digest(sources), history_hash=reference.history_hash,
        reference_hash=digest(asdict(reference)), layout_hash=layout_hash,
        future_hash=digest([asdict(order) for order in future]),
        assignment=list(assignment), slot_assignment=list(slots),
        product_ids=list(catalogue.product_ids), station_ids=list(catalogue.station_ids),
        origin=reference.origin, training_horizon=problem.n, horizon=horizon,
        primary_same_horizon=horizon == problem.n,
        evaluation_kind="primary_same_horizon" if horizon == problem.n else "secondary_cross_horizon",
        future_boundaries=dict(start=reference.origin, stop=reference.origin + horizon,
                               interval_convention="zero_based_half_open_complete_orders",
                               order_count=len(future), first_order_id=future[0].order_id,
                               last_order_id=future[-1].order_id,
                               first_chronology_key=future[0].chronology_key,
                               last_chronology_key=future[-1].chronology_key,
                               stream_adjacency_verified=False,
                               membership_provenance="caller_supplied_future_segment"),
        product_line_counts=list(product_counts), station_line_counts=station_counts,
        fixed_station_line_counts=fixed_counts, total_lines=total, order_count=len(future),
        visit_count=visits, mean_visits=float(Fraction(visits, len(future))),
        mean_visits_exact=str(Fraction(visits, len(future))),
        historical_visit_count=historical_visits,
        historical_mean_visits=float(Fraction(historical_visits, reference.origin)),
        historical_mean_visits_exact=str(Fraction(historical_visits, reference.origin)),
        rule="two_sided" if two_sided else "upper_only",
        joint_pass=all(b <= 0 for b in breaches), violation_count=sum(b > 0 for b in breaches),
        cap_violation_count=sum(r > 0 for r in residuals),
        floor_violation_count=(sum(f > 0 for f in floor_residuals) if two_sided else None),
        borderline=any(abs(b) <= MODEL_TOLERANCE for b in breaches),
        borderline_threshold=float(MODEL_TOLERANCE), future_feasibility_tolerance=0,
        delta=problem.delta, nu=problem.nu, inactive_product_count=len(inactive),
        realized_inactive_product_count=sum(product_counts[p] > 0 for p in inactive),
        active_product_count=sum(c > 0 for c in product_counts),
        active_product_fraction=float(Fraction(sum(c > 0 for c in product_counts), catalogue.p)),
        horizon_per_product=float(Fraction(horizon, catalogue.p)),
        activation_exceeds_budget=activation > nu,
        novel_support_order_count=sum(tuple(p for p, c in o.lines) not in known_supports for o in future),
        station_novelty_count=sum(v > 0 for v in novelty),
        station_novelty_count_lower=(sum(v > 0 for v in shortfall) if two_sided else None),
        uncertainty_membership="not_certified_by_station_direction_diagnostics",
        stations=stations, validation=validation,
        allocation_returned=True, solver_status=None, paired_run_ids=None)
    exports = [("station_shares", shares), ("targets", targets), ("caps", caps),
               ("residuals", residuals), ("implied_lower_bounds", lower),
               ("worst_scenario_envelope", envelope), ("novelty_residuals", novelty),
               ("breaches", breaches)]
    if two_sided:
        exports += [("floors", floors), ("floor_residuals", floor_residuals),
                    ("lowest_scenario_envelope", lowest), ("shortfall_residuals", shortfall)]
    for name, values in exports:
        result[name] = [float(v) for v in values]
        result[name + "_exact"] = [str(v) for v in values]
    for name, value in dict(maximum_residual=maximum,
                            maximum_excess=max(Fraction(0), maximum),
                            worst_excess_percentage_points=100 * max(Fraction(0), maximum),
                            positive_excess_sum=sum(max(Fraction(0), v) for v in breaches),
                            effective_total_allowance=sum(cap - b for cap, b in zip(caps, targets)),
                            activation_mass=activation, effective_nu=nu,
                            maximum_novelty_excess=max(Fraction(0), max(novelty))).items():
        result[name], result[name + "_exact"] = float(value), str(value)
    if two_sided:
        value = max(Fraction(0), max(shortfall))
        result["maximum_novelty_shortfall"], result["maximum_novelty_shortfall_exact"] = float(value), str(value)
    return result
