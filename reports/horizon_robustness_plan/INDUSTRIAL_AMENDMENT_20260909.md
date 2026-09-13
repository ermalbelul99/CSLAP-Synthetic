# Industrial preprocessing amendment — 9 September 2026

Authority: the user's explicit instruction to reproduce `data_loader_industrial.py::load_industrial_data()` before industrial tests. This amendment supersedes the earlier plan's row-first exclusions, ambiguous-geometry blocker, historical reconstruction of the industrial incumbent, and history-recomputed industrial freeze mask. All synthetic rules, horizons, tolerance settings, methods and reporting requirements remain unchanged. The original plan is retained as the prior contract, not silently rewritten.

## Retained system and decision pool

Use the shared article loader unchanged, on the allowlisted BERNER export only. It reconciles multi-station products using the last observed order before excluding `01.Z8`, `01.15` and `01.GED`, and renames `01.GE4` to `01.E4`. The two real excluded stations are absent from optimization, workloads, visits and the total-work denominator. Do not confuse their 1 and 2 locations with their plotted 5 and 11 order lines.

Merge `static_assignment` with `warm_start_assignment` to reconstruct the complete included incumbent. Preserve the loader's frozen set exactly: low-frequency products on its three static-shelving classes, plus products removed entirely by its large-order filter. Do not recompute that set at each cutoff. Frozen products remain in the full catalogue, storage occupancy, historical and future workload, and order-station visits. Their assignments are fixed; their demand is not fixed. An included station with no movable products still participates in all share constraints and evaluation.

The order-size filter determines the decision pool, not the evaluated stream: use `op_full`, including small orders. The robustness workload unit remains one distinct retained product-order pair, consistent with `pl_full`; deduplicate repeated list entries introduced by station reconciliation, and report this explicitly. Do not reuse `TIME_CAPACITY`, `SPEED` or the article's relative 10% allowance in the share-based study.

## Information boundary and limits of the evidence

This is a retrospective experiment conditional on an assumed pre-known warehouse snapshot. The included catalogue, aggregate slot geometry, complete incumbent and frozen mask are reconstructed from the full export by the article loader and then held fixed as exogenous metadata. Their availability before any cutoff is an assumption, not an established fact. In particular, the loader's last-station reconciliation and full-export frequency-derived mask are not history-only estimators.

Every training demand count, target share, order support, inactive-product set and uncertainty scenario is computed from the historical prefix only, conditional on that snapshot. Mutation tests must hold the snapshot AND its product/station retention rule fixed when changing future observations. Full-export reconciliation also determines which earlier lines and orders survive exclusion; this selection is part of the retrospective conditioning. Re-running snapshot reconstruction on an altered future can change the snapshot and retained history and is not claimed to be leakage-free. A genuinely prospective deployment would require the actual pre-cutoff inventory, incumbent and frozen mask as inputs.

The shared freeze threshold counts reconciled list entries, not always distinct orders. Preserve that mask unchanged, independently of deduplication for robustness workload. Audit whether any duplicate crosses the threshold; do not silently reinterpret the mask. The loader's maximum-order station tie has no explicit tie-break, so record the loader and input hashes and the installed pandas version. Reliable chronology remains an assumption; audit that this export's numeric ORDER dtype and downstream numeric sequence agree.

All included catalogue products receive slots even when unobserved in history. The export does not establish the existence or absence of additional never-ordered physical SKUs: completeness of this catalogue is the study's closed-universe assumption. Slot labels are interchangeable within a station unless actual location IDs are supplied; station freezing plus reserved reference slot labels preserves the modeled frozen locations without claiming to recover physical bin IDs.

## Display labels and verification

Published labels come from `plot_industrial_heuristic_workload.py::station_alias_map()`, separately from optimization indices. The label map may contain 26 stations, while the modeled system has 24; the two excluded stations may appear only as explicitly excluded/frozen reference bars, never enter computed percentages. Internal site codes must not appear in publication graphics.

Before industrial optimization, verify the shared loader's catalogue, capacities, fixed/variable partition, complete orders and aliases independently against the adapter; test a fixed product becoming active in the future, same-station fixed/movable visit deduplication, excluded-station denominator removal, and zero-history full-catalogue assignment. Record measured counts rather than treating article figures as self-verifying assertions. The study and root completion gates remain open until their remaining implementation, experiments and reporting outcomes are met.
