"""Allowlisted source manifests and exogenous full-catalogue construction.

The default industrial path uses the shared article loader under the explicit
assumed-snapshot amendment of 2026-09-09. Lower-level roster functions preserve
the earlier diagnostic policy; they are not the industrial campaign entry point.
"""

from collections import Counter
import csv
import hashlib
from pathlib import Path
import re

from .protocol import (ContractError, INDUSTRIAL_SOURCE, REPO_ROOT, allowed_source,
                       canonical_json)
from .schema import CatalogueManifest, SourceFile


EXCLUDED_STATIONS = frozenset(("01.Z8", "01.15", "01.GED"))
STATIC_CLASS = frozenset(("01.E4", "01.31", "01.30"))


def natural_id(value):
    return tuple((0, int(part)) if part.isdigit() else (1, part)
                 for part in re.split(r"(\d+)", str(value)) if part)


def source_file(path, root=REPO_ROOT):
    rel = allowed_source(path, root)
    target = Path(root).resolve() / rel
    sha = hashlib.sha256()
    with target.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            sha.update(block)
    return SourceFile(rel, sha.hexdigest(), target.stat().st_size)


def read_source_rows(path, root=REPO_ROOT):
    rel = allowed_source(path, root)
    with (Path(root) / rel).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        if not reader.fieldnames or any(name is None for name in reader.fieldnames):
            raise ContractError("DATA_CONTRACT_ERROR", "missing CSV schema")
        for row in reader:
            if None in row:
                raise ContractError("DATA_CONTRACT_ERROR", "CSV row has unexpected columns")
            yield row


def synthetic_instances(root=REPO_ROOT):
    found = []
    for directory in (Path(root) / "exp02a_instances").iterdir():
        if not directory.is_dir():
            continue
        match = re.fullmatch(r"syn_(\d+)sku_seed(\d+)", directory.name)
        if not match:
            raise ContractError("SOURCE_NOT_ALLOWED", "unexpected benchmark directory")
        size, seed = map(int, match.groups())
        for suffix in ("products", "stations", "orders"):
            rel = f"exp02a_instances/{directory.name}/syn_{size}sku_{suffix}.csv"
            allowed_source(rel, root)
            if not (Path(root) / rel).is_file():
                raise ContractError("DATA_CONTRACT_ERROR", "incomplete benchmark instance")
        found.append((size, seed, directory.name))
    counts = Counter(size for size, seed, name in found)
    if counts != Counter({50: 12, 500: 10, 1000: 4, 2000: 3}):
        raise ContractError("DATA_CONTRACT_ERROR", "original 29-instance benchmark inventory differs")
    return tuple(name for size, seed, name in sorted(found))


def synthetic_product_id(value):
    value = str(value).strip()
    match = re.fullmatch(r"(?:PROD_)?(\d+)", value)
    if not match:
        raise ContractError("DATA_CONTRACT_ERROR", "malformed synthetic product ID")
    return str(int(match.group(1)))


def load_synthetic_catalogue(instance, root=REPO_ROOT):
    match = re.fullmatch(r"syn_(\d+)sku_seed(\d+)", str(instance))
    if not match:
        raise ContractError("SOURCE_NOT_ALLOWED", "invalid synthetic instance ID")
    size = int(match.group(1))
    paths = {suffix: f"exp02a_instances/{instance}/syn_{size}sku_{suffix}.csv"
             for suffix in ("products", "stations", "orders")}
    sources = tuple(source_file(paths[key], root) for key in ("products", "stations", "orders"))
    products = tuple(sorted((synthetic_product_id(row["PRODUCT_ID"])
                            for row in read_source_rows(paths["products"], root)), key=natural_id))
    station_rows = sorted(read_source_rows(paths["stations"], root), key=lambda row: natural_id(row["STATION_ID"]))
    stations = tuple(str(row["STATION_ID"]).strip() for row in station_rows)
    try:
        capacities = tuple(int(row["CAPACITY"]) for row in station_rows)
    except ValueError as exc:
        raise ContractError("DATA_CONTRACT_ERROR", "station capacities must be integers") from exc
    if len(products) != size:
        raise ContractError("DATA_CONTRACT_ERROR", "catalogue size does not match original instance")
    return CatalogueManifest(str(instance), "synthetic", products, stations, capacities, sources,
                             audit=(("reference_policy", "historical_LPT_not_raw_line_station"),
                                    ("workload_unit", "original_pick_line_multiplicity"),
                                    ("slot_labels", "interchangeable_slots_numbered_within_station")))


def clean_cell(value):
    if value is None:
        return None
    value = str(value).strip()
    return None if value in ("", "NULL", "null", "NaN", "nan", "N/A") else value


def canonical_station(value):
    value = clean_cell(value)
    return "01.E4" if value == "01.GE4" else value


def retained_industrial_rows(rows, audit=None):
    """Clean raw observations without any global station reassignment."""
    audit = audit if audit is not None else Counter()
    for row in rows:
        audit["raw_rows"] += 1
        product, order = clean_cell(row.get("PRODUCT")), clean_cell(row.get("ORDER"))
        station = canonical_station(row.get("STATION"))
        if product is None or order is None or station is None:
            audit["null_rows_removed"] += 1
            continue
        if station in EXCLUDED_STATIONS:
            audit["excluded_station_rows"] += 1
            continue
        audit["retained_raw_rows"] += 1
        yield {"PRODUCT": product, "ORDER": order, "STATION": station}


def industrial_roster(rows):
    """Catalogue/station membership only, explicitly exogenous by assumption."""
    memberships = {}
    audit = Counter()
    for row in retained_industrial_rows(rows, audit):
        memberships.setdefault(row["PRODUCT"], set()).add(row["STATION"])
    products = tuple(sorted(memberships, key=natural_id))
    stations = tuple(sorted({s for candidates in memberships.values() for s in candidates}, key=natural_id))
    audit["catalogue_products"] = len(products)
    audit["retained_stations"] = len(stations)
    audit["products_with_ambiguous_station"] = sum(len(v) != 1 for v in memberships.values())
    return products, stations, {p: tuple(sorted(v, key=natural_id)) for p, v in memberships.items()}, dict(audit)


def industrial_catalogue_from_roster(products, stations, memberships, source,
                                     geometry=None, known_reference=None, fixed=None, audit=None):
    """Accept known geometry, or only the unambiguous exported-roster surrogate.

    geometry maps station ID to slot count. known_reference/fixed map SKU ID to
    station ID and must genuinely be prior-known metadata, not future labels.
    No ambiguous location is selected here based on future frequency/chronology.
    """
    if geometry is None:
        ambiguous = sum(len(v) != 1 for v in memberships.values())
        if ambiguous:
            raise ContractError("MISSING_GEOMETRY", f"{ambiguous} products have multiple observed stations; a declared slot-count manifest is needed")
        geometry = dict(Counter(v[0] for v in memberships.values()))
        geometry_note = "unambiguous_export_roster_counts_assumed_static"
    else:
        geometry_note = "explicit_slot_count_manifest_assumed_static"
    if set(geometry) != set(stations):
        raise ContractError("DATA_CONTRACT_ERROR", "geometry must include exactly all retained stations")
    station_index = {s: i for i, s in enumerate(stations)}
    product_index = {p: i for i, p in enumerate(products)}
    if known_reference is not None and set(known_reference) != set(products):
        raise ContractError("DATA_CONTRACT_ERROR", "pre-known reference must cover full catalogue")
    try:
        reference_indices = tuple(station_index[known_reference[p]] for p in products) if known_reference else ()
        fixed_indices = tuple(sorted((product_index[p], station_index[s]) for p, s in (fixed or {}).items()))
    except KeyError as exc:
        raise ContractError("DATA_CONTRACT_ERROR", "metadata references an unknown product/station") from exc
    notes = dict(audit or {})
    notes.update(geometry_policy=geometry_note, workload_unit="retained_distinct_product_order_pair",
                 catalogue_limitation="export_roster_not_verified_complete_physical_inventory")
    return CatalogueManifest("berner", "industrial", products, stations,
                             tuple(geometry[s] for s in stations), (source,), fixed_indices,
                             known_reference=reference_indices, geometry_provenance="assumed_exogenous",
                             roster_provenance="assumed_exogenous",
                             audit=tuple(sorted((str(k), str(v)) for k, v in notes.items())))


def load_industrial_catalogue(root=REPO_ROOT, geometry=None, known_reference=None, fixed=None):
    from .industrial import load_article_data
    return load_article_data(root, geometry, known_reference, fixed).catalogue


def industrial_reconciliation_audit(root=REPO_ROOT):
    """Compare declared row cleaning to legacy whole-export station filtering.

    This preserves the pre-amendment audit, not the campaign preprocessing. Its
    deterministic tie approximation is NOT the authoritative shared loader.
    Return aggregate discrepancies, not product identities or demand features.
    """
    from .orders import chronology_key

    valid_triples, new_pairs, latest, new_stations = set(), set(), {}, set()
    raw_count = 0
    for row in read_source_rows(INDUSTRIAL_SOURCE, root):
        raw_count += 1
        p, o, raw_s = clean_cell(row.get("PRODUCT")), clean_cell(row.get("ORDER")), clean_cell(row.get("STATION"))
        if p is None or o is None or raw_s is None:
            continue
        key = chronology_key(o)
        valid_triples.add((p, o, raw_s))
        # The legacy loader's same-order tie is unspecified. Record any such
        # ambiguity rather than claiming this deterministic tie reproduces it.
        candidate = (key, raw_s)
        if p not in latest or candidate > latest[p]:
            latest[p] = candidate
        s = canonical_station(raw_s)
        if s not in EXCLUDED_STATIONS:
            new_pairs.add((o, p))
            new_stations.add(s)
    old_pairs, old_stations = set(), set()
    tie_stations = {}
    for p, o, s in valid_triples:
        key = chronology_key(o)
        if key == latest[p][0]:
            tie_stations.setdefault(p, set()).add(s)
        target = canonical_station(latest[p][1])
        if target not in EXCLUDED_STATIONS:
            old_pairs.add((o, p))
            old_stations.add(target)
    old_products = {p for o, p in old_pairs}
    new_products = {p for o, p in new_pairs}
    return {
        "raw_rows": raw_count, "declared_products": len(new_products), "declared_stations": len(new_stations),
        "declared_product_order_pairs": len(new_pairs), "legacy_products": len(old_products),
        "legacy_stations": len(old_stations), "legacy_product_order_pairs": len(old_pairs),
        "pairs_added_by_declared_cleaning": len(new_pairs - old_pairs),
        "pairs_removed_by_declared_cleaning": len(old_pairs - new_pairs),
        "products_added_by_declared_cleaning": len(new_products - old_products),
        "products_removed_by_declared_cleaning": len(old_products - new_products),
        "legacy_latest_order_station_ties": sum(len(stations) > 1 for stations in tie_stations.values()),
        "legacy_geometry_counts_diagnostic_only": dict(sorted(Counter(canonical_station(latest[p][1]) for p in old_products).items())),
        "legacy_tie_rule_for_audit": "lexicographically_greatest_raw_station_at_maximum_numeric_order",
    }
