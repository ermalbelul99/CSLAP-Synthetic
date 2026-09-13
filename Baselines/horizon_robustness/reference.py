"""Historical-only reference layouts, fixed masks and pooled target shares."""

from collections import Counter

from .catalogue import STATIC_CLASS, natural_id
from .orders import history_hash, line_counts
from .protocol import ContractError
from .schema import OrderedDemand, ReferenceState


def historical_preferences(history):
    """Last complete historical order; same-order station ties use lowest index."""
    preferences = {}
    for order in history:
        within_order = {}
        for p, s in order.observations:
            within_order[p] = min(s, within_order.get(p, s))
        preferences.update(within_order)
    return preferences


def lpt_assignment(catalogue, counts):
    assignment = [-1] * catalogue.p
    remaining = list(catalogue.capacities)
    loads = [0] * catalogue.s
    for p, s in catalogue.exogenous_fixed:
        assignment[p], remaining[s] = s, remaining[s] - 1
        loads[s] += counts[p]
    pending = sorted((p for p in range(catalogue.p) if assignment[p] < 0),
                     key=lambda p: (-counts[p], natural_id(catalogue.product_ids[p])))
    for p in pending:
        candidates = [s for s in catalogue.eligible_stations(p) if remaining[s] > 0]
        if not candidates:
            raise ContractError("REFERENCE_CONSTRUCTION_FAILED", "historical LPT cannot fill constrained slots; not a proof of model infeasibility")
        s = min(candidates, key=lambda s: (loads[s], natural_id(catalogue.station_ids[s])))
        assignment[p], remaining[s] = s, remaining[s] - 1
        loads[s] += counts[p]
    result = tuple(assignment)
    catalogue.check_storage(result, catalogue.exogenous_fixed)
    return result


def minimum_preference_assignment(catalogue, preferences):
    """Exact minimum reassignment with lexicographically smallest station vector.

    For unrestricted movable products, the maximum achievable number of retained
    preferences is sum_s min(remaining preferred products, remaining slots).
    A sequential lexicographic choice preserves that optimum in O(P*S) time.
    Exogenous fixed assignments are imposed before that computation. This is the
    actual retained-system geometry in the approved industrial formulation.
    """
    if catalogue.allowed_stations and any(set(v) != set(range(catalogue.s)) for v in catalogue.allowed_stations):
        raise ContractError("REFERENCE_CONSTRUCTION_FAILED", "restricted product-station compatibility needs separately verified reference reconciliation")
    if any(type(p) is not int or p < 0 or p >= catalogue.p or type(s) is not int or s < 0 or s >= catalogue.s
           for p, s in preferences.items()):
        raise ContractError("DATA_CONTRACT_ERROR", "preference outside full universe")
    assignment = [-1] * catalogue.p
    remaining = list(catalogue.capacities)
    for p, s in catalogue.exogenous_fixed:
        assignment[p], remaining[s] = s, remaining[s] - 1
    preferred_count = [0] * catalogue.s
    for p, s in preferences.items():
        if assignment[p] < 0:
            preferred_count[s] += 1
    matches_left = sum(min(c, r) for c, r in zip(preferred_count, remaining))
    product_order = sorted(range(catalogue.p), key=lambda p: natural_id(catalogue.product_ids[p]))
    station_order = sorted(range(catalogue.s), key=lambda s: natural_id(catalogue.station_ids[s]))
    for p in product_order:
        if assignment[p] >= 0:
            continue
        preferred = preferences.get(p)
        before = matches_left
        if preferred is not None:
            before -= min(preferred_count[preferred], remaining[preferred])
            preferred_count[preferred] -= 1
            before += min(preferred_count[preferred], remaining[preferred])
        for s in station_order:
            if remaining[s] == 0:
                continue
            future_matches = before - min(preferred_count[s], remaining[s]) + min(preferred_count[s], remaining[s] - 1)
            gain = int(s == preferred)
            if gain + future_matches == matches_left:
                assignment[p] = s
                remaining[s] -= 1
                matches_left -= gain
                break
        if assignment[p] < 0:
            raise ContractError("REFERENCE_CONSTRUCTION_FAILED", "preference reconciliation invariant failed")
    result = tuple(assignment)
    catalogue.check_storage(result, catalogue.exogenous_fixed)
    return result


def fixed_mask(catalogue, history, reference_assignment):
    fixed = dict(catalogue.exogenous_fixed)
    snapshot_fixed = dict(catalogue.audit).get("fixed_policy") == "article_snapshot_fixed_only"
    if catalogue.kind == "industrial" and not snapshot_fixed:
        large_frequency = Counter(p for order in history if len(order.support) > 5 for p in order.support)
        for p, s in enumerate(reference_assignment):
            frequency = large_frequency[p]
            if frequency == 0 or (frequency <= 5 and catalogue.station_ids[s] in STATIC_CLASS):
                fixed[p] = s
    return tuple(sorted(fixed.items()))


def build_reference(catalogue, history):
    """Accept only the history tuple, not a dataset object containing the future."""
    if not isinstance(history, tuple) or not history:
        raise ContractError("DATA_CONTRACT_ERROR", "nonempty immutable historical prefix required")
    OrderedDemand(catalogue, history)  # chronology and catalogue consistency
    counts = line_counts(history, catalogue.p)
    preferences = historical_preferences(history)
    if catalogue.known_reference:
        assignment = catalogue.known_reference
        provenance = dict(catalogue.audit).get("reference_provenance", "pre_known_complete_inventory_reference")
    elif catalogue.kind == "industrial":
        assignment = minimum_preference_assignment(catalogue, preferences)
        provenance = "constructed_historical_reference_not_verified_incumbent"
    else:
        assignment = lpt_assignment(catalogue, counts)
        provenance = "historical_capacity_respecting_LPT"
    fixed = fixed_mask(catalogue, history, assignment)
    station_counts = [0] * catalogue.s
    for p, s in enumerate(assignment):
        station_counts[s] += counts[p]
    audit = {
        "historical_observed_products": sum(c > 0 for c in counts),
        "historical_inactive_products": sum(c == 0 for c in counts),
        "fixed_products": len(fixed),
        "movable_products": catalogue.p - len(fixed),
        "changed_historical_preferences": sum(assignment[p] != s for p, s in preferences.items()),
        "missing_historical_preferences": catalogue.p - len(preferences),
        "same_order_station_tie": "lowest_stable_station_index",
    }
    return ReferenceState(assignment, fixed, counts, tuple(station_counts), len(history), history_hash(history),
                          provenance, tuple(sorted((k, str(v)) for k, v in audit.items())))


def slot_assignment(catalogue, assignment, reference=None):
    """One unique slot per SKU; reserve reference slots for fixed products."""
    fixed = reference.fixed if reference is not None else catalogue.exogenous_fixed
    catalogue.check_storage(assignment, fixed)
    station_slots = catalogue.slot_ids or tuple(tuple(f"{s}::slot::{i + 1:06d}" for i in range(capacity))
                                                 for s, capacity in zip(catalogue.station_ids, catalogue.capacities))
    reserved = {}
    if reference is not None:
        base = slot_assignment(catalogue, reference.assignment)
        reserved = {p: base[p] for p, s in fixed}
    occupied = set(reserved.values())
    available = [iter(slot for slot in slots if slot not in occupied) for slots in station_slots]
    slots = [None] * catalogue.p
    for p in sorted(range(catalogue.p), key=lambda p: natural_id(catalogue.product_ids[p])):
        slots[p] = reserved[p] if p in reserved else next(available[assignment[p]])
    return tuple(slots)
