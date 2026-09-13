"""Complete-order ingestion and deterministic chronological slicing."""

from collections import Counter
from dataclasses import asdict
import re

from .catalogue import (clean_cell, load_synthetic_catalogue,
                        read_source_rows, synthetic_product_id)
from .protocol import ContractError, INDUSTRIAL_SOURCE, REPO_ROOT, digest
from .schema import Order, OrderedDemand


def chronology_key(order_id):
    match = re.fullmatch(r"(?:[A-Za-z][A-Za-z_-]*)?(\d+)", str(order_id))
    if not match:
        raise ContractError("DATA_CONTRACT_ERROR", "order ID must have one reliable terminal integer key")
    return int(match.group(1))


def aggregate_orders(rows, catalogue, industrial=False):
    """Rows are original synthetic lines or already cleaned industrial lines."""
    p_index = {p: i for i, p in enumerate(catalogue.product_ids)}
    s_index = {s: i for i, s in enumerate(catalogue.station_ids)}
    grouped, observations, key_to_id, order_keys = {}, {}, {}, {}
    audit = Counter()
    for row in rows:
        audit["retained_input_rows"] += 1
        order_id = clean_cell(row.get("ORDER"))
        product_id = clean_cell(row.get("PRODUCT"))
        if order_id is None or product_id is None:
            raise ContractError("DATA_CONTRACT_ERROR", "unclean missing order/product ID")
        if order_id not in order_keys:
            key = chronology_key(order_id)
            if key in key_to_id and key_to_id[key] != order_id:
                raise ContractError("DATA_CONTRACT_ERROR", "different order IDs have the same chronology key")
            key_to_id[key], order_keys[order_id] = order_id, key
        product_id = product_id if industrial else synthetic_product_id(product_id)
        if product_id not in p_index:
            raise ContractError("OUT_OF_CATALOGUE", "an ordered product is not in the pre-known catalogue")
        p = p_index[product_id]
        counts = grouped.setdefault(order_id, Counter())
        if industrial:
            if counts[p]:
                audit["duplicate_product_order_rows_removed"] += 1
            counts[p] = 1
            station_id = row.get("STATION")
            if station_id not in s_index:
                raise ContractError("DATA_CONTRACT_ERROR", "unclean station outside retained geometry")
            observations.setdefault(order_id, set()).add((p, s_index[station_id]))
        else:
            counts[p] += 1
            # Synthetic per-line station and quantity labels are not model inputs.
    orders = tuple(Order(order_id, order_keys[order_id], tuple(sorted(grouped[order_id].items())),
                         tuple(sorted(observations.get(order_id, ()))))
                   for order_id in sorted(grouped, key=order_keys.__getitem__))
    audit["complete_orders"] = len(orders)
    audit["workload_lines"] = sum(o.total_lines for o in orders)
    audit["observed_products"] = len({p for o in orders for p, count in o.lines})
    return OrderedDemand(catalogue, orders, tuple(sorted((k, str(v)) for k, v in audit.items())))


def load_synthetic(instance, root=REPO_ROOT):
    catalogue = load_synthetic_catalogue(instance, root)
    path = next(s.path for s in catalogue.source_files if s.path.endswith("_orders.csv"))
    return aggregate_orders(read_source_rows(path, root), catalogue)


def load_industrial(root=REPO_ROOT, geometry=None, known_reference=None, fixed=None):
    from .industrial import load_article_data
    return load_article_data(root, geometry, known_reference, fixed)


def complete_window(orders, start, stop):
    if not isinstance(orders, tuple) or type(start) is not int or type(stop) is not int or not 0 <= start < stop <= len(orders):
        raise ContractError("DATA_CONTRACT_ERROR", "window must contain complete existing orders")
    return orders[start:stop]


def line_counts(orders, product_count):
    counts = [0] * product_count
    for order in orders:
        for p, count in order.lines:
            if p >= product_count:
                raise ContractError("OUT_OF_CATALOGUE", "workload product outside catalogue")
            counts[p] += count
    return tuple(counts)


def weighted_supports(orders):
    return tuple(sorted(Counter(o.support for o in orders).items()))


def history_hash(orders):
    # Station observations are decision-bearing for the historical reference.
    return digest([asdict(o) for o in orders])
