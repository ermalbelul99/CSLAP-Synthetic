"""Article-compatible industrial snapshot, explicitly assumed pre-known.

The shared loader reconstructs static metadata from the complete export. This
adapter does NOT claim that reconstruction is historical-only. Once frozen, the
snapshot is independent of the historical demand windows used for optimization.
See reports/horizon_robustness_plan/INDUSTRIAL_AMENDMENT_20260909.md.
"""

from collections import Counter
from contextlib import redirect_stdout
from dataclasses import replace
import hashlib
import io
from pathlib import Path

from .catalogue import EXCLUDED_STATIONS, STATIC_CLASS, clean_cell, natural_id, source_file
from .protocol import ContractError, INDUSTRIAL_SOURCE, REPO_ROOT, allowed_source, canonical_json
from .schema import CatalogueManifest


SNAPSHOT_POLICY = "article_reconstructed_snapshot_assumed_pre_known_20260909"
FIXED_POLICY = "article_snapshot_fixed_only"


def _id(value):
    value = clean_cell(value)
    if value is None:
        raise ContractError("DATA_CONTRACT_ERROR", "shared loader returned an empty identifier")
    return value


def _mapping(mapping):
    result = {_id(p): _id(s) for p, s in mapping.items()}
    if len(result) != len(mapping):
        raise ContractError("DATA_CONTRACT_ERROR", "shared loader identifier normalization collided")
    return result


def catalogue_from_article(payload, source, loader_sha256="fixture"):
    """Freeze the complete assignment/geometry and the loader's exact mask.

    Aggregate capacities come from the complete incumbent, checked against every
    entry in st_full. A fully fixed included station absent from st_full (whose
    implementation enumerates large-order stations) is retained, not discarded.
    """
    fixed = _mapping(payload["static_assignment"])
    movable = _mapping(payload["warm_start_assignment"])
    if set(fixed) & set(movable):
        raise ContractError("DATA_CONTRACT_ERROR", "shared fixed and movable pools overlap")
    reference = {**fixed, **movable}
    products = tuple(sorted(reference, key=natural_id))
    expected_products = {_id(p) for p in payload["pl_full"]}
    if set(products) != expected_products:
        raise ContractError("DATA_CONTRACT_ERROR", "shared reference omits full-stream catalogue products")
    solver_products = {_id(p) for p in payload["pr_solver"]}
    if solver_products != set(movable) or len(solver_products) != len(payload["pr_solver"]):
        raise ContractError("DATA_CONTRACT_ERROR", "shared solver pool differs from movable incumbent")
    stations = tuple(sorted(set(reference.values()), key=natural_id))
    if EXCLUDED_STATIONS.intersection(stations) or "01.GE4" in stations:
        raise ContractError("DATA_CONTRACT_ERROR", "shared snapshot contains an excluded or unrenamed station")
    occupancy = Counter(reference.values())
    supplied_capacities = {}
    for entry in payload["st_full"]:
        station = _id(entry["STATION_ID"])
        capacity = entry["CAPACITY"]
        if station in supplied_capacities or station not in occupancy or capacity != occupancy[station]:
            raise ContractError("DATA_CONTRACT_ERROR", "shared full station geometry conflicts with incumbent")
        supplied_capacities[station] = capacity
    missing_stations = sorted(set(stations) - set(supplied_capacities), key=natural_id)
    if any(s in set(movable.values()) for s in missing_stations):
        raise ContractError("DATA_CONTRACT_ERROR", "shared full station list omits a movable station")
    p_index = {p: i for i, p in enumerate(products)}
    s_index = {s: i for i, s in enumerate(stations)}
    notes = {
        "snapshot_policy": SNAPSHOT_POLICY,
        "fixed_policy": FIXED_POLICY,
        "loader_source_sha256": loader_sha256,
        "workload_unit": "retained_distinct_product_order_pair",
        "excluded_station_policy": "absent_from_slots_workload_visits_and_denominator",
        "excluded_stations": canonical_json(sorted(EXCLUDED_STATIONS)),
        "catalogue_limitation": "complete_export_roster_assumed_pre_known_not_verified_physical_inventory",
        "reference_provenance": "whole_export_reconstruction_assumed_pre_known_not_prospective_evidence",
        "freeze_provenance": "whole_export_article_mask_assumed_pre_known_not_prefix_frequency_estimate",
        "fixed_products": str(len(fixed)),
        "movable_products": str(len(movable)),
        "included_fixed_only_stations_missing_from_legacy_st_full": canonical_json(missing_stations),
        "slot_labels": "interchangeable_slots_numbered_within_station_not_recovered_physical_bin_ids",
    }
    return CatalogueManifest(
        "berner", "industrial", products, stations, tuple(occupancy[s] for s in stations), (source,),
        tuple(sorted((p_index[p], s_index[s]) for p, s in fixed.items())),
        known_reference=tuple(s_index[reference[p]] for p in products),
        geometry_provenance="assumed_exogenous", roster_provenance="assumed_exogenous",
        audit=tuple(sorted(notes.items())),
    )


def demand_from_article(payload, catalogue):
    """Use full orders, including small/fixed-only orders, never op_solver."""
    from .orders import aggregate_orders, line_counts

    reference = dict(zip(catalogue.product_ids,
                         (catalogue.station_ids[s] for s in catalogue.known_reference)))

    def rows():
        for order, products in payload["op_full"].items():
            for product in products:
                product = _id(product)
                if product not in reference:
                    raise ContractError("OUT_OF_CATALOGUE", "shared full order contains an unknown product")
                yield {"ORDER": _id(order), "PRODUCT": product, "STATION": reference[product]}

    demand = aggregate_orders(rows(), catalogue, industrial=True)
    measured = dict(zip(catalogue.product_ids, line_counts(demand.orders, catalogue.p)))
    expected = {_id(p): int(count) for p, count in payload["pl_full"].items()}
    if measured != expected:
        raise ContractError("DATA_CONTRACT_ERROR", "distinct product-order counts differ from shared pl_full")
    if len(demand.orders) != len(payload["op_full"]):
        raise ContractError("DATA_CONTRACT_ERROR", "complete included orders were lost")
    return replace(demand, audit=demand.audit + (("industrial_snapshot_policy", SNAPSHOT_POLICY),))


def audit_article_payload(payload, catalogue):
    """Independently reconcile the two counting conventions and freeze threshold."""
    from .orders import chronology_key

    large_entry_counts, large_pair_counts = Counter(), Counter()
    complete_pairs = 0
    keys = []
    for order, products in payload["op_full"].items():
        identifiers = [_id(p) for p in products]
        support = set(identifiers)
        complete_pairs += len(support)
        keys.append(chronology_key(_id(order)))
        if len(support) > 5:
            large_entry_counts.update(identifiers)
            large_pair_counts.update(support)
    if len(keys) != len(set(keys)) or keys != sorted(keys):
        raise ContractError("DATA_CONTRACT_ERROR", "shared complete order keys do not match increasing numeric chronology")
    reference = {p: catalogue.station_ids[s] for p, s in zip(catalogue.product_ids, catalogue.known_reference)}
    expected_fixed = {p for p, s in reference.items()
                      if large_entry_counts[p] == 0 or (s in STATIC_CLASS and large_entry_counts[p] <= 5)}
    actual_fixed = {catalogue.product_ids[p] for p, s in catalogue.exogenous_fixed}
    if expected_fixed != actual_fixed:
        raise ContractError("DATA_CONTRACT_ERROR", "shared fixed pool fails independent large-order frequency reconciliation")
    distinct_rule = {p for p, s in reference.items()
                     if large_pair_counts[p] == 0 or (s in STATIC_CLASS and large_pair_counts[p] <= 5)}
    return dict(
        shared_order_keys_match_numeric_chronology=True,
        loader_order_key_types=sorted({type(key).__name__ for key in payload["op_full"]}),
        retained_orders=len(keys), retained_distinct_pairs=complete_pairs,
        retained_list_entries=sum(map(len, payload["op_full"].values())),
        duplicate_entries_in_large_orders=sum(large_entry_counts.values()) - sum(large_pair_counts.values()),
        products_with_duplicated_large_order_pairs=sum(large_entry_counts[p] != large_pair_counts[p] for p in reference),
        products_whose_freeze_classification_differs_under_distinct_order_rule=len(expected_fixed ^ distinct_rule),
        fixed_pool_independently_reconciled=True,
    )


def read_article_payload(root=REPO_ROOT):
    """Invoke the original module unchanged, hashing both source and loader."""
    import data_loader_industrial as shared

    relative = allowed_source(INDUSTRIAL_SOURCE, root)
    source = source_file(relative, root)
    loader_hash = hashlib.sha256(Path(shared.__file__).read_bytes()).hexdigest()
    # The original routine's progress print is not a structured data result.
    with redirect_stdout(io.StringIO()):
        payload = shared.load_industrial_data(str(Path(root).resolve() / relative))
    if source_file(relative, root) != source:
        raise ContractError("SOURCE_CHANGED", "industrial export changed during snapshot reconstruction")
    return payload, source, loader_hash


def load_article_data(root=REPO_ROOT, geometry=None, known_reference=None, fixed=None):
    payload, source, loader_hash = read_article_payload(root)
    catalogue = catalogue_from_article(payload, source, loader_hash)
    # Preserve the old optional arguments only as explicit equality checks. A
    # conflicting surrogate must not silently select a different preprocessing.
    expected_geometry = dict(zip(catalogue.station_ids, catalogue.capacities))
    expected_reference = {p: catalogue.station_ids[s]
                          for p, s in zip(catalogue.product_ids, catalogue.known_reference)}
    expected_fixed = {catalogue.product_ids[p]: catalogue.station_ids[s]
                      for p, s in catalogue.exogenous_fixed}
    for supplied, expected in ((geometry, expected_geometry), (known_reference, expected_reference),
                               (fixed, expected_fixed)):
        if supplied is not None and supplied != expected:
            raise ContractError("DATA_CONTRACT_ERROR", "override conflicts with approved article snapshot")
    return demand_from_article(payload, catalogue)


def article_station_labels(root=REPO_ROOT):
    """Reuse publication aliases; excluded stations remain display-only labels."""
    from plot_industrial_heuristic_workload import station_alias_map

    relative = allowed_source(INDUSTRIAL_SOURCE, root)
    labels = station_alias_map(str(Path(root).resolve() / relative))
    if len(set(labels.values())) != len(labels) or "01.Z8" in labels or "01.GE4" in labels:
        raise ContractError("DATA_CONTRACT_ERROR", "publication station aliases are inconsistent")
    return dict(labels)
