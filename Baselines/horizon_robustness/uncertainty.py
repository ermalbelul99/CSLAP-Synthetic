"""Historical hull and inactive-product activation, without future inputs.

Scenario counts are sparse on the unchanged catalogue index space: an omitted
product has exactly zero demand, never an omitted assignment obligation.
"""

from collections import Counter
from fractions import Fraction
import math

from .orders import history_hash, line_counts, weighted_supports
from .protocol import ACTIVATION_ARMS, ContractError, Protocol
from .reference import build_reference
from .schema import (CatalogueManifest, Order, OrderedDemand, ReferenceState,
                     Scenario, TrainingProblem)


def _validate_history(history, product_count, n):
    if type(product_count) is not int or product_count <= 0:
        raise ContractError("DATA_CONTRACT_ERROR", "positive integer catalogue size required")
    if type(n) is not int or n <= 0:
        raise ContractError("DATA_CONTRACT_ERROR", "positive integer order horizon required")
    if not isinstance(history, tuple) or not all(isinstance(o, Order) for o in history):
        raise ContractError("DATA_CONTRACT_ERROR", "immutable complete historical orders required")
    previous_key = -1
    order_ids = set()
    for order in history:
        if order.chronology_key <= previous_key or order.order_id in order_ids:
            raise ContractError("DATA_CONTRACT_ERROR", "history must have unique increasing complete orders")
        if any(p >= product_count for p, count in order.lines):
            raise ContractError("OUT_OF_CATALOGUE", "historical product outside known catalogue")
        previous_key = order.chronology_key
        order_ids.add(order.order_id)


def _scenario(history, start, stop, label="block"):
    counts = Counter()
    for index in range(start, stop):
        for p, count in history[index].lines:
            counts[p] += count
    return Scenario(tuple(sorted(counts.items())), sum(counts.values()), start, stop, label)


def make_scenarios(history: tuple[Order, ...], product_count: int,
                   n: int) -> tuple[Scenario, ...]:
    """Return right-aligned disjoint n-blocks, then the pooled whole history.

    Intervals are zero-based and half-open, ordered oldest to newest. A leading
    remainder contributes only to the pooled scenario. At least three complete
    blocks are required, including for nominal/tightening comparison inputs.
    """
    _validate_history(history, product_count, n)
    if len(history) // n < 3:
        raise ContractError("INSUFFICIENT_HISTORY", "at least three complete historical n-blocks required")
    blocks = tuple(_scenario(history, start, start + n)
                   for start in range(len(history) % n, len(history), n))
    return blocks + (_scenario(history, 0, len(history), "history"),)


def build_training_problem(catalogue: CatalogueManifest, history: tuple[Order, ...],
                           n: int, arm: str = "HIST+ACT", delta: str = "0.01",
                           nu: str = "0.01", tightening: str = "0.5",
                           reference: ReferenceState | None = None,
                           rule: str = "upper_only") -> TrainingProblem:
    """Freeze full historical supports, scenarios, reference and declared policy.

    A supplied reference may be reused across arms/horizons at this origin; its
    counts, origin and history hash must match this exact prefix. No diagnostics
    or observations following the prefix select the policy parameters.
    """
    scenarios = make_scenarios(history, catalogue.p, n)
    if reference is None:
        # The constructor validates station observations and hashes this prefix.
        reference = build_reference(catalogue, history)
    else:
        if not isinstance(reference, ReferenceState):
            raise ContractError("DATA_CONTRACT_ERROR", "immutable reference state required")
        OrderedDemand(catalogue, history)  # Also validate historical station observations.
        if (reference.origin != len(history)
                or reference.history_hash != history_hash(history)
                or reference.historical_counts != line_counts(history, catalogue.p)):
            raise ContractError("DATA_CONTRACT_ERROR", "reference does not match the exact historical prefix")
    return TrainingProblem(catalogue=catalogue, reference=reference, n=n,
                           scenarios=scenarios, weighted_supports=weighted_supports(history),
                           arm=arm, delta=delta, nu=nu, tightening=tightening, rule=rule)


# v3 (13 Sep 2026): the lower activation row carries the trapped-activation
# indicator g_s (every inactive product at station s), see integer_cap_rows.
ROW_FORMULATION = "exact_integer_counts_v3"
_INT64_MAX = 2 ** 63 - 1


def integer_cap_rows(problem: TrainingProblem) -> tuple[tuple[dict, ...], Fraction]:
    """Exact integer-count form of the fixed-cap robust workload rows.

    Every historical line count is an integer, so multiplying a share row by its
    scenario's total line count T_k clears the denominators on the left. The
    activation endpoint additionally carries the rational factors (1-nu) and nu,
    which multiplying by nu's denominator M clears as well:

        base        sum_p x_ps L_p^k                    <= u_s T_k
        activation  (M-N) sum_p x_ps L_p^k + N T_k h_s  <= M u_s T_k     (nu = N/M)

    Both left sides are integers. Replacing each right side by its FLOOR is
    therefore an exact restatement, not a relaxation and not a tightening: for
    integer z, ``z <= r`` and ``z <= floor(r)`` have identical solution sets.

    The point of the restatement is numerical, not mathematical. An integer row
    is self-correcting: a solver whose internal feasibility tolerance is smaller
    than 1.0 cannot report a solution that violates it exactly. The scientific
    feasible set, the declared delta, the evaluation ceilings and the independent
    validator are all untouched.

    Returns the rows and the effective nu. Raises rather than silently emitting a
    row whose left side could overflow a 64-bit integer accumulator.
    """
    if not isinstance(problem, TrainingProblem):
        raise ContractError("DATA_CONTRACT_ERROR", "TrainingProblem required")
    caps = problem.rational_caps(optimization=True)
    floors = problem.rational_floors(optimization=True)   # None under upper_only
    inactive = problem.reference.inactive
    nu = Fraction(problem.nu) if problem.arm in ACTIVATION_ARMS and inactive else Fraction(0)
    numerator, denominator = nu.numerator, nu.denominator
    rows = []
    for index, scenario in enumerate(problem.effective_scenarios):
        total = scenario.total_lines
        if type(total) is not int or total <= 0:
            raise ContractError("DATA_CONTRACT_ERROR", "scenario needs a positive integer line total")
        for station, cap in enumerate(caps):
            # Largest attainable left side: every line of the scenario lands here.
            if total > _INT64_MAX or denominator * total > _INT64_MAX:
                raise ContractError("NUMERICAL_RANGE",
                                    "integer workload row would exceed 64-bit range")
            rows.append(dict(scenario=index, station=station, kind="base", sense="<=", multiplier=1,
                             activation_coefficient=0, all_inactive_coefficient=0,
                             threshold=math.floor(cap * total), maximum_left_side=total))
            if numerator:
                rows.append(dict(scenario=index, station=station, kind="activation", sense="<=",
                                 multiplier=denominator - numerator,
                                 activation_coefficient=numerator * total, all_inactive_coefficient=0,
                                 threshold=math.floor(denominator * cap * total),
                                 maximum_left_side=denominator * total))
            if floors is None:
                continue
            # Two-sided rule. The LOWEST share a station can take over the
            # uncertainty set puts the activation mass at another station,
            # unless every inactive product sits at s (g_s = 1), in which case
            # the mass cannot avoid s:
            #   min_q r_s = min( A_sk, (1-nu) A_sk + nu g_s )  >=  f_s.
            # For integer z, z >= r holds exactly when z >= ceil(r), so:
            #   lower base        sum_p x_ps L_p^k                    >= ceil( f_s T_k )
            #   lower activation  (M-N) sum_p x_ps L_p^k + N T_k g_s  >= ceil( M f_s T_k )
            # With g_s = 0 the activation row implies the base row; with g_s = 1
            # the base row is the binding one. Both are always emitted so the
            # rows mirror the validator's envelope exactly. (v3, 13 Sep 2026:
            # the g_s term was missing, making the model over-conservative in a
            # case no executed dataset can produce.)
            floor_value = floors[station]
            rows.append(dict(scenario=index, station=station, kind="lower_base", sense=">=",
                             multiplier=1, activation_coefficient=0, all_inactive_coefficient=0,
                             threshold=math.ceil(floor_value * total), maximum_left_side=total))
            if numerator:
                rows.append(dict(scenario=index, station=station, kind="lower_activation", sense=">=",
                                 multiplier=denominator - numerator, activation_coefficient=0,
                                 all_inactive_coefficient=numerator * total,
                                 threshold=math.ceil(denominator * floor_value * total),
                                 maximum_left_side=denominator * total))
    return tuple(rows), nu


def historical_activation_diagnostics(history: tuple[Order, ...], product_count: int,
                                      n: int) -> tuple[dict, ...]:
    """Describe earlier activation on the history's right-aligned n-block grid.

    Each JSON-compatible record names the prefix ``[0, cut)`` and the next
    ``[next_start, next_stop)`` interval, both inside history. ``inactive_products``
    lists every then-unobserved catalogue index, including never-observed SKUs;
    ``activated_products`` lists those receiving lines in that next block.
    ``activation_mass`` is activation_lines / total_lines in the next block.
    Strict exceedances use exact arithmetic against the frozen protocol grid.
    An empty tuple means there are no eligible earlier cuts, not zero activation.
    """
    _validate_history(history, product_count, n)
    policy = Protocol()
    records = []
    seen = set()
    cursor = 0
    first_cut = len(history) % n + 3 * n
    for cut in range(first_cut, len(history), n):
        for index in range(cursor, cut):
            seen.update(history[index].support)
        cursor = cut
        inactive = [p for p in range(product_count) if p not in seen]
        following = _scenario(history, cut, cut + n)
        activated = [p for p, count in following.counts if p not in seen]
        activation_lines = sum(count for p, count in following.counts if p not in seen)
        mass = Fraction(activation_lines, following.total_lines)
        records.append({
            "cut": cut, "n": n, "next_start": cut, "next_stop": cut + n,
            "prior_complete_blocks": cut // n, "sparse_history": cut // n < 10,
            "product_count": product_count, "inactive_products": inactive,
            "activated_products": activated, "activation_lines": activation_lines,
            "total_lines": following.total_lines, "activation_mass": float(mass),
            "primary_nu": policy.nu, "exceeds_primary_nu": mass > Fraction(policy.nu),
            "nu_exceedances": {nu: mass > Fraction(nu) for nu in policy.nus},
        })
    return tuple(records)


def _rational_worst_shares(problem, assignment):
    problem.catalogue.check_storage(assignment, problem.reference.fixed)
    inactive = problem.reference.inactive
    # Preserve the configured decimal exactly instead of rounding effective_nu
    # through its public float view. The empty-set/arm rules are identical.
    nu = Fraction(problem.nu) if problem.arm in ACTIVATION_ARMS and inactive else Fraction(0)
    h = [0] * problem.catalogue.s
    for p in inactive:
        h[assignment[p]] = 1
    worst = [Fraction(0)] * problem.catalogue.s
    for scenario in problem.effective_scenarios:
        counts = [0] * problem.catalogue.s
        for p, count in scenario.counts:
            counts[assignment[p]] += count
        for s, count in enumerate(counts):
            a = Fraction(count, scenario.total_lines)
            worst[s] = max(worst[s], a, (1 - nu) * a + nu * h[s])
    return tuple(worst)


def _rational_lowest_shares(problem, assignment):
    """Exact lowest attainable share per station over the uncertainty set.

    Activation mass drains a station unless every inactive product sits there
    (then it cannot avoid the station and the historical share is the minimum).
    """
    problem.catalogue.check_storage(assignment, problem.reference.fixed)
    inactive = problem.reference.inactive
    nu = Fraction(problem.nu) if problem.arm in ACTIVATION_ARMS and inactive else Fraction(0)
    stations = set(assignment[p] for p in inactive)
    lowest = [Fraction(1)] * problem.catalogue.s
    for scenario in problem.effective_scenarios:
        counts = [0] * problem.catalogue.s
        for p, count in scenario.counts:
            counts[assignment[p]] += count
        for s, count in enumerate(counts):
            a = Fraction(count, scenario.total_lines)
            trapped = int(bool(inactive) and stations == {s})
            lowest[s] = min(lowest[s], a, (1 - nu) * a + nu * trapped)
    return tuple(lowest)


def worst_shares(problem: TrainingProblem, assignment: tuple[int, ...]) -> tuple[float, ...]:
    """Exact finite counterpart per station, rounded only at the return boundary.

    For each historical vertex, both activation endpoints a=0 and a=nu matter.
    Maximizing a linear station share over the historical hull and the inactive
    simplex attains a vertex; its endpoint values are A and (1-nu)*A+nu*h.
    Fixed inactive products contribute to h. Different stations may attain their
    maxima at different demands, so the returned maxima need not sum to one.
    Storage/fixed infeasibility is rejected; workload infeasibility is measurable.
    """
    return tuple(float(value) for value in _rational_worst_shares(problem, assignment))


def minimum_slack_for_assignment(problem: TrainingProblem, assignment: tuple[int, ...]) -> float:
    """Smallest common nonnegative share allowance eta for this fixed layout.

    This is max_s [worst_share_s - b_s]_+ under the upper-only rule and, under
    the two-sided rule, also max_s [b_s - lowest_share_s]_+ (13 Sep 2026: the
    lower excursion was omitted). Independent of delta and tightening. It is an
    attainable upper bound on the global minimum-slack problem, not an
    optimization over layouts or a certificate of global infeasibility.
    """
    worst = _rational_worst_shares(problem, assignment)
    total = problem.reference.total_lines
    targets = [Fraction(count, total) for count in problem.reference.station_line_counts]
    excess = [value - b for value, b in zip(worst, targets)]
    if problem.two_sided:
        lowest = _rational_lowest_shares(problem, assignment)
        excess += [b - value for value, b in zip(lowest, targets)]
    return float(max(Fraction(0), max(excess)))
