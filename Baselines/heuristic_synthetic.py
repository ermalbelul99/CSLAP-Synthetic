"""
Heuristic for CSLAP (Synthetic Data Adapter)
Lightweight adaptation of the greedy product clustering approach.

Steps:
1. Pair generation from multi-item orders
2. Community formation (greedy clustering)
3. Station assignment (majority-preference)
"""

import numpy as np
import pandas as pd
import os
import time
import argparse
from collections import defaultdict
from itertools import combinations


def read_data(prefix, data_dir):
    orders_df = pd.read_csv(
        os.path.join(data_dir, f"{prefix}_orders.csv"), sep=";"
    )
    stations_df = pd.read_csv(
        os.path.join(data_dir, f"{prefix}_stations.csv"), sep=";"
    )
    products_df = pd.read_csv(
        os.path.join(data_dir, f"{prefix}_products.csv"), sep=";"
    )
    prod_lines = orders_df.groupby("PRODUCT").size().to_dict()
    order_prods = orders_df.groupby("ORDER")["PRODUCT"].apply(list).to_dict()
    stations = stations_df.to_dict(orient="records")
    products = products_df["PRODUCT_ID"].apply(lambda x: f"PROD_{x}").tolist()
    return order_prods, stations, products, prod_lines, orders_df


def _repair_workload(station_ids, members, station_load, wl_ceiling, assignment,
                     prod_lines, speed_of, filtered_pairs, *, swap_partners=50,
                     max_swaps=None):
    """Restore the workload cap by exchanging products between stations.

    Slot capacity is exhausted by construction: the synthetic generator gives
    sum(zeta_s) = |P| exactly, and industrially each station's capacity is the
    number of products it already holds. Every station is therefore full once
    placement ends, and relocating a product to a less loaded station is
    impossible -- there is nowhere to put it. The repair swaps a heavy product
    out of an overloaded station against a lighter one elsewhere, which keeps
    every station's product count unchanged and so preserves slot feasibility
    for free.

    A swap is scored by the co-occurrence weight it breaks,

        cost = aff(p, s) + aff(q, t) - aff(p, t) - aff(q, s),

    with aff(x, s) the summed co-occurrence of x with the products of s over the
    kept pairs only. Minimising it keeps correlated products together while the
    load moves. ``swap_partners`` bounds the candidate scan at each end, in the
    same spirit as the partner sampling of the column generation's swap descent.

    Mutates ``members``, ``station_load`` and ``assignment`` in place; returns
    the number of swaps applied.
    """
    # Index kept pairs by product so affinity is a sparse lookup, not a scan.
    neigh = defaultdict(dict)
    for (a, b), cnt in filtered_pairs.items():
        neigh[a][b] = cnt
        neigh[b][a] = cnt

    def aff(x, sid):
        nx = neigh.get(x)
        if not nx:
            return 0
        m = members[sid]
        # Iterate the smaller side.
        if len(nx) <= len(m):
            return sum(c for y, c in nx.items() if y in m and y is not x)
        return sum(nx.get(y, 0) for y in m if y is not x)

    if max_swaps is None:
        max_swaps = 10 * len(assignment) + 100

    def over(sid):
        return station_load[sid] - wl_ceiling[sid]

    n_swaps = 0
    while n_swaps < max_swaps:
        s = max(station_ids, key=lambda x: (over(x), str(x)))
        if over(s) <= 1e-9:
            break
        sp_s = speed_of(s)
        # Heaviest products of the overloaded station are the useful ones to shed.
        cands_s = sorted(members[s], key=lambda p: (-prod_lines.get(p, 0), str(p))
                         )[:swap_partners]
        best = None
        for t in station_ids:
            if t == s:
                continue
            sp_t = speed_of(t)
            cands_t = sorted(members[t], key=lambda q: (prod_lines.get(q, 0), str(q))
                             )[:swap_partners]
            for p in cands_s:
                lp = prod_lines.get(p, 0)
                for q in cands_t:
                    lq = prod_lines.get(q, 0)
                    if lq >= lp:
                        continue  # must lighten s
                    new_s = station_load[s] - lp / sp_s + lq / sp_s
                    new_t = station_load[t] - lq / sp_t + lp / sp_t
                    if new_t > wl_ceiling[t] + 1e-9:
                        continue
                    if new_s >= station_load[s] - 1e-12:
                        continue
                    cost = (aff(p, s) + aff(q, t)) - (aff(p, t) + aff(q, s))
                    key = (cost, -(station_load[s] - new_s), str(p), str(q))
                    if best is None or key < best[0]:
                        best = (key, p, q, t, new_s, new_t)
        if best is None:
            break  # no admissible exchange remains
        _key, p, q, t, new_s, new_t = best
        members[s].discard(p)
        members[t].discard(q)
        members[s].add(q)
        members[t].add(p)
        assignment[p] = t
        assignment[q] = s
        station_load[s] = new_s
        station_load[t] = new_t
        n_swaps += 1
    return n_swaps


def heuristic_cslap(order_prods, stations, products, prod_lines, orders_df, *,
                    min_freq_preproc=None, min_freq=None, ratio_to_keep=None,
                    mnoppc=None, ratio_denominator="max", placement="preference",
                    wl_tolerance=0.0, repair=True, swap_partners=50, diag=None):
    """
    Greedy product clustering and station assignment.
    Auto-scales parameters to dataset size.

    Keyword-only overrides (the four threshold overrides default to None = keep
    the auto-scaled formula, so the historical behaviour is bit-for-bit
    unchanged when they are omitted):
        min_freq_preproc : product frequency floor for P* (default max(2, N//100))
        min_freq         : pair co-occurrence floor      (default max(2, N//50))
        ratio_to_keep    : pair support ratio floor      (default 0.1)
        mnoppc           : max number of products per community
                           (default max(5, min(15, N//20)))
        ratio_denominator: which endpoint frequency normalises the pair support
                           ratio eta_ij = cnt_ij / denom.
                             "max"   (default) denom = max(cnt_i, cnt_j), the
                                     symmetric confidence measure the article
                                     describes: a pair survives only when its
                                     co-occurrence is a fraction of the MORE
                                     frequent endpoint's own demand.
                             "first" denom = cnt of the lexicographically first
                                     product. This is what the code did before
                                     2026-08; it makes the filter asymmetric and
                                     dependent on product naming. Retained ONLY
                                     to reproduce the pre-fix cached results.
        placement        : station-selection rule of Step 4. Both only ever
                           consider stations that keep slot AND workload
                           feasibility; they differ in which they prefer.
                             "preference" (default) most historically preferred
                                          feasible station, relative load breaking
                                          ties. Degrades gracefully to "any
                                          feasible station, least loaded" when the
                                          history carries no signal.
                             "balance"    least resulting relative load,
                                          historical preference breaking ties.
                           The two are statistically indistinguishable on the 29
                           synthetic instances (paired Wilcoxon p = 0.35), whose
                           station history is random by construction, so the
                           industrial instance decides: there the history is real
                           and "preference" is 2.4% better in station visits.
        wl_tolerance     : the workload ceiling is (1 + wl_tolerance) * T_s.
                           0.0 for the synthetic instances, whose TIME_CAPACITY
                           already contains the 10% operational slack; 0.10 for
                           the industrial instance, whose TIME_CAPACITY is the
                           station's raw legacy load and whose stated tolerance
                           is +10% over it.
        repair           : run the Step-5 swap repair (default True). False
                           reports what workload-aware placement alone achieves
                           (diagnostic). NOTE it does NOT reproduce the historical
                           algorithm: Step 4 filters candidates by workload before
                           the repair ever runs, so the placement itself differs.
                           Steps 1-3 are untouched, which is what the audit gate
                           checks (n_pstar / n_pairs_kept / n_corr_communities).
        swap_partners    : candidates scanned at each end of a swap (default 50).
        diag             : optional dict; when given it is FILLED with structural
                           diagnostics (see the block before `return`). The return
                           value is NOT changed.
    """
    start_time = time.time()
    N = len(products)

    # --- Auto-scale parameters (overridable; None => historical formula) ---
    MIN_FREQ_PREPROC = (max(2, N // 100) if min_freq_preproc is None
                        else int(min_freq_preproc))
    MIN_FREQ = max(2, N // 50) if min_freq is None else int(min_freq)
    RATIO_TO_KEEP = 0.1 if ratio_to_keep is None else float(ratio_to_keep)
    # Community size limit, indexed on the STATION SLOT CAPACITY, not on N.
    #
    # EXP-02c (Baselines/run_capacity_sweep.py, re-run on the repaired heuristic)
    # crosses two catalogue sizes with four station counts so the same zeta grid
    # appears at both. The visit-optimal bound tracks zeta and not N:
    # corr(beta*, zeta) = 0.947 against corr(beta*, N) = -0.085, with beta*
    # identical at both sizes for zeta in {20, 50, 100} and beta*/zeta ~ 0.4-0.6.
    # The previous rule, max(5, min(15, N // 20)), was indexed on N and clamped
    # at 15, which put every benchmark block of 500 SKUs and above at
    # beta/zeta = 0.15 -- below the basin. Applying 0.4*zeta on the 29 published
    # instances moves the gap to the set-variable reference from +3.2 to +2.5
    # (500), +2.5 to +1.4 (1000) and +0.1 to -1.3 (2000); at 50 SKUs zeta = 10 so
    # the floor of 5 binds and that block is bit-identical to the published run.
    #
    # zeta is a scalar here because communities are formed (Step 2) before any
    # station is chosen (Step 4), so the bound is a property of the clustering,
    # not of a station. The mean is taken over stations: on the synthetic family
    # capacities are uniform so every aggregator coincides, and on a
    # heterogeneous site the mean is the aggregator under which a community
    # still fits whole in the stations holding the large majority of slots.
    if mnoppc is not None:
        MNOPPC = int(mnoppc)
    else:
        _caps = [s["CAPACITY"] for s in stations]
        _zeta = (sum(_caps) / len(_caps)) if _caps else 0.0
        MNOPPC = max(5, int(round(0.4 * _zeta)))
    if ratio_denominator not in ("max", "first"):
        raise ValueError(
            f"ratio_denominator must be 'max' or 'first', got {ratio_denominator!r}")
    if placement not in ("balance", "preference"):
        raise ValueError(
            f"placement must be 'balance' or 'preference', got {placement!r}")

    # --- Step 1: Preprocessing & Pair Generation ---
    # Filter products by minimum frequency
    P_star = {p for p, freq in prod_lines.items() if freq >= MIN_FREQ_PREPROC}

    # Generate co-occurrence pairs from multi-item orders
    pair_counts = defaultdict(int)
    for o, prods in order_prods.items():
        filtered = [p for p in set(prods) if p in P_star]
        if len(filtered) < 2:
            continue
        for p1, p2 in combinations(sorted(filtered), 2):
            pair_counts[(p1, p2)] += 1

    # Filter by MIN_FREQ
    pair_counts = {k: v for k, v in pair_counts.items() if v >= MIN_FREQ}

    # Filter by RATIO_TO_KEEP.
    # The pair keys are canonicalised by `sorted()` above, so p1 is the
    # lexicographically first product, NOT the more frequent one. Normalising by
    # its frequency alone (ratio_denominator="first") therefore makes the filter
    # depend on product naming; "max" is the symmetric confidence measure.
    filtered_pairs = {}
    for (p1, p2), cnt in pair_counts.items():
        freq1 = prod_lines.get(p1, 1)
        if ratio_denominator == "max":
            denom = max(freq1, prod_lines.get(p2, 1))
        else:
            denom = freq1
        ratio = cnt / denom
        if ratio >= RATIO_TO_KEEP:
            filtered_pairs[(p1, p2)] = cnt

    # Sort descending
    sorted_pairs = sorted(filtered_pairs.items(), key=lambda x: -x[1])

    # --- Step 2: Community Formation ---
    communities = []
    assigned = set()

    for (pa, pb), cnt in sorted_pairs:
        if pa in assigned or pb in assigned:
            continue

        community = {pa, pb}
        assigned.add(pa)
        assigned.add(pb)

        # Expand community
        while len(community) < MNOPPC:
            best_candidate = None
            best_score = -1

            for (p1, p2), c in sorted_pairs:
                if p1 in assigned and p2 in assigned:
                    continue
                if p1 in community and p2 not in assigned:
                    candidate = p2
                elif p2 in community and p1 not in assigned:
                    candidate = p1
                else:
                    continue

                # Score: total co-occurrence with community members
                score = sum(
                    filtered_pairs.get(tuple(sorted([candidate, m])), 0)
                    for m in community
                )
                if score > best_score:
                    best_score = score
                    best_candidate = candidate

            if best_candidate is None or best_score <= 0:
                break

            community.add(best_candidate)
            assigned.add(best_candidate)

        communities.append(community)

    # Communities born from the correlation step, BEFORE the filler groups of
    # Step 3 are appended (diagnostic only; not used by the algorithm).
    n_corr_communities = len(communities)

    # --- Step 3: Post-processing (unassigned products) ---
    unassigned = [p for p in products if p not in assigned]
    # Group unassigned into communities of MNOPPC
    for i in range(0, len(unassigned), MNOPPC):
        communities.append(set(unassigned[i: i + MNOPPC]))

    # --- Step 4: Workload-aware station assignment ---
    # Sort communities by total frequency (most impactful first). This is also
    # LPT order, which is what makes the balance rule below behave.
    communities.sort(
        key=lambda c: sum(prod_lines.get(p, 0) for p in c), reverse=True
    )

    station_ids = [s["STATION_ID"] for s in stations]
    station_caps = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    # Effective workload ceiling. The synthetic generator already folds the
    # operational slack into TIME_CAPACITY (tolerance 0), whereas the industrial
    # loader stores each station's raw legacy load and the site's tolerance is
    # +10% over it. One parameter reconciles the two conventions.
    wl_ceiling = {sid: time_caps[sid] * (1.0 + wl_tolerance) for sid in station_ids}

    remaining_cap = dict(station_caps)
    station_load = {sid: 0.0 for sid in station_ids}
    members = {sid: set() for sid in station_ids}
    assignment = {}

    def _speed(sid):
        sp = speeds.get(sid, 1.0)
        return sp if sp > 0 else 1.0

    def _cost(p, sid):
        """Workload product p adds to station sid."""
        return prod_lines.get(p, 0) / _speed(sid)

    def _place(p, sid):
        assignment[p] = sid
        members[sid].add(p)
        remaining_cap[sid] -= 1
        station_load[sid] += _cost(p, sid)

    # Compute historical preference (from original STATION in orders_df)
    prod_station_pref = defaultdict(lambda: defaultdict(int))
    for _, row in orders_df.iterrows():
        prod_station_pref[row["PRODUCT"]][row["STATION"]] += 1

    def _select(items, pref_rank):
        """Station for a block of products, or None if none stays feasible.

        Both rules only ever consider stations that keep BOTH constraints: enough
        free slots, and workload within the ceiling. They differ in which of those
        feasible stations they prefer.
        """
        size = len(items)
        feasible = []
        for sid in station_ids:
            if remaining_cap.get(sid, 0) < size:
                continue
            added = sum(_cost(p, sid) for p in items)
            if station_load[sid] + added <= wl_ceiling[sid] + 1e-9:
                feasible.append((sid, (station_load[sid] + added) / wl_ceiling[sid]
                                 if wl_ceiling[sid] > 0 else float("inf")))
        if not feasible:
            return None
        if placement == "preference":
            # Most historically preferred station that stays feasible; relative
            # load breaks ties (and decides when no product has a preference).
            return min(feasible, key=lambda t: (-pref_rank.get(t[0], 0), t[1], str(t[0])))[0]
        # "balance": least resulting relative load, preference breaks ties.
        return min(feasible, key=lambda t: (t[1], -pref_rank.get(t[0], 0), str(t[0])))[0]

    for community in communities:
        pref_rank = defaultdict(int)
        for p in community:
            for sid, cnt in prod_station_pref[p].items():
                pref_rank[sid] += cnt

        block = sorted(community, key=lambda p: (-prod_lines.get(p, 0), str(p)))
        sid = _select(block, pref_rank)
        if sid is not None:
            for p in block:
                _place(p, sid)
            continue
        # No station can take the whole community: split it, heaviest first,
        # under the same rule applied product by product.
        for p in block:
            sid = _select([p], pref_rank)
            if sid is None:
                # No slot-and-workload-feasible station for this single product.
                # Fall back to any station with a free slot; Step 5 repairs the
                # resulting overload. With sum(zeta_s) = |P| one always exists.
                open_sids = [s for s in station_ids if remaining_cap.get(s, 0) > 0]
                if not open_sids:
                    break
                sid = min(open_sids,
                          key=lambda s: ((station_load[s] + _cost(p, s)) / wl_ceiling[s]
                                         if wl_ceiling[s] > 0 else float("inf"), str(s)))
            _place(p, sid)

    # Safety net: no product may be silently dropped. The pre-repair code could
    # leave products unassigned once every station was full, which corrupts the
    # visit count (an unassigned product is simply never counted).
    leftover = [p for p in products if p not in assignment]
    for p in leftover:
        open_sids = [s for s in station_ids if remaining_cap.get(s, 0) > 0]
        if not open_sids:
            break
        _place(p, min(open_sids, key=lambda s: (station_load[s] / wl_ceiling[s]
                                                if wl_ceiling[s] > 0 else float("inf"),
                                                str(s))))

    n_overloaded_before = sum(1 for sid in station_ids
                              if station_load[sid] > wl_ceiling[sid] + 1e-9)

    # --- Step 5: Swap repair ---
    n_swaps = _repair_workload(
        station_ids, members, station_load, wl_ceiling, assignment,
        prod_lines, _speed, filtered_pairs, swap_partners=swap_partners,
    ) if repair else 0

    n_overloaded_after = sum(1 for sid in station_ids
                             if station_load[sid] > wl_ceiling[sid] + 1e-9)

    elapsed = time.time() - start_time

    # --- Evaluate ---
    total_visits = 0
    for o, prods in order_prods.items():
        visited = set()
        for p in prods:
            if p in assignment:
                visited.add(assignment[p])
        total_visits += len(visited)

    # --- Workload distribution tracking ---
    station_counts = defaultdict(int)
    station_actions = defaultdict(float)
    speeds = {s["STATION_ID"]: s["SPEED"] for s in stations}
    
    for p, sid in assignment.items():
        station_counts[sid] += 1
        qty = prod_lines.get(p, 0)
        station_actions[sid] += qty / speeds.get(sid, 1.0) if speeds.get(sid, 1.0) > 0 else 0
        
    station_ids = [s["STATION_ID"] for s in stations]
    station_caps = {s["STATION_ID"]: s["CAPACITY"] for s in stations}
    time_caps = {s["STATION_ID"]: s["TIME_CAPACITY"] for s in stations}
    
    cap_broken = sum(1 for sid in station_ids if station_counts[sid] > station_caps[sid])
    wl_broken = sum(1 for sid in station_ids if station_actions[sid] > time_caps[sid])

    actual_workloads = [station_actions[sid] for sid in station_ids]
    max_workload = float(np.max(actual_workloads)) if actual_workloads else 0.0
    workload_std_dev = float(np.std(actual_workloads)) if actual_workloads else 0.0

    print(f"  Heuristic Done: Visits={total_visits}, "
          f"Time={elapsed:.2f}s, WL_Std={workload_std_dev:.4f}, Max_WL={max_workload:.4f}")

    # --- Optional structural diagnostics (threshold-sensitivity instrumentation) ---
    # Read-only: fills the caller's dict, never touches the returned tuple.
    if diag is not None:
        diag.update({
            # products surviving the MIN_FREQ_PREPROC frequency floor
            "n_pstar": len(P_star),
            # pairs surviving MIN_FREQ *and* RATIO_TO_KEEP
            "n_pairs_kept": len(filtered_pairs),
            # communities formed by the greedy expansion (excl. Step-3 fillers)
            "n_corr_communities": n_corr_communities,
            # products actually placed on a station (from the FINAL assignment)
            "n_assigned": len(assignment),
            # largest community handed to the station-assignment step
            "community_size_max": max((len(c) for c in communities), default=0),
            # effective thresholds actually used (audit of the caller's overrides)
            "min_freq_preproc": MIN_FREQ_PREPROC,
            "min_freq": MIN_FREQ,
            "ratio_to_keep": RATIO_TO_KEEP,
            "mnoppc": MNOPPC,
            "ratio_denominator": ratio_denominator,
            # Step 4/5 audit: how much overload placement left, and how much of
            # it the swap repair removed.
            "placement": placement,
            "wl_tolerance": wl_tolerance,
            "n_swaps": n_swaps,
            "n_overloaded_before": n_overloaded_before,
            "n_overloaded_after": n_overloaded_after,
        })

    return assignment, total_visits, elapsed, max_workload, workload_std_dev, cap_broken, wl_broken


def heuristic_cslap_search(order_prods, stations, products, prod_lines,
                           orders_df, *, alpha_grid=(0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6),
                           beta_min=5, diag=None, **kwargs):
    """Select the community bound by feasibility search, for HETEROGENEOUS sites.

    The rule beta = max(5, round(0.4 * zeta)) is a property of warehouses whose
    stations are interchangeable. It is derived on the EXP-02c family, whose
    stations are uniform, and it validates on all 29 EXP-02a instances: the
    rule's beta is feasible on every one of them and no search is needed.

    It does NOT transfer to a site whose stations differ. On Company A, zeta
    spans 8 to 2,575 slots and the rule returns beta = 266, which is infeasible.
    Worse, feasibility there is not merely non-monotone but DISCONNECTED --
    measured: beta = 15 and 47 certify, 63, 84, 100, 112, 150, 200, 250, 266 and
    300 do not, and 350 certifies again. A community sized for the mean station
    cannot fit the small ones, so the repair has to undo the placement rather
    than tune it, and whether it succeeds stops tracking beta.

    A one-directional guard is therefore the wrong shape: stepping down from the
    rule's beta walks into the infeasible band and lands far below the good
    region it never reaches. This searches an anchored grid instead and returns
    the FEASIBLE layout with fewest visits, so the selection is explicit,
    reproducible, and reportable as part of the method rather than hidden.

    Certification is `n_overloaded_after == 0`, the count the repair reports
    against each station's own budget. Do NOT substitute the returned
    `wl_broken`: on the industrial run that is measured against raw legacy load
    with no tolerance and reads 15 even for a layout inside the site's +10%.

    Cost is one heuristic pass per grid point; `diag["beta_attempts"]` records
    every point so the search can be reported honestly.
    """
    if kwargs.get("mnoppc") is not None:
        raise ValueError("mnoppc is chosen by the search; pass alpha_grid instead")

    caps = [s["CAPACITY"] for s in stations]
    zeta = (sum(caps) / len(caps)) if caps else 0.0
    grid = sorted({max(beta_min, int(round(a * zeta))) for a in alpha_grid})

    attempts, feasible, fallback = [], [], None
    for beta in grid:
        d = {}
        result = heuristic_cslap(order_prods, stations, products, prod_lines,
                                 orders_df, mnoppc=beta, diag=d, **kwargs)
        over = d.get("n_overloaded_after")
        attempts.append({"beta": beta, "n_overloaded_after": over,
                         "visits": result[1], "feasible": over == 0})
        if over == 0:
            feasible.append((result[1], beta, result, d))
        elif fallback is None or (over is not None and over < fallback[0]):
            fallback = (over, beta, result, d)

    if feasible:
        _v, beta_used, result, d = min(feasible, key=lambda t: t[0])
        failed = False
    else:
        _o, beta_used, result, d = fallback
        failed = True

    if diag is not None:
        diag.update(d)
        diag["beta_attempts"] = attempts
        diag["beta_rule"] = max(beta_min, int(round(0.4 * zeta)))
        diag["beta_used"] = beta_used
        diag["beta_search_grid"] = grid
        diag["beta_search_failed"] = failed
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Heuristic CSLAP (synthetic)")
    parser.add_argument("--prefix", type=str, required=True)
    parser.add_argument("--dir", type=str, default="exp02a_instances")
    args = parser.parse_args()

    print(f"Running Heuristic on {args.prefix}...")
    order_prods, stations, products, prod_lines, orders_df = read_data(
        args.prefix, args.dir
    )
    heuristic_cslap(order_prods, stations, products, prod_lines, orders_df)
