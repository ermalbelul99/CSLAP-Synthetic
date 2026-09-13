# Industrial provenance audit (before optimization)

## Current decision and measured shared-loader result — 9 September 2026

The user's industrial preprocessing clarification resolves the earlier 26/24-station question. The controlling contract is `reports/horizon_robustness_plan/INDUSTRIAL_AMENDMENT_20260909.md`. The shared article loader is now invoked unchanged. Its complete retained incumbent, aggregate capacities, catalogue and frozen mask are explicitly assumed pre-known, not presented as prospectively verified metadata. Future-dependent retention during snapshot reconstruction is acknowledged too. Historical demand estimation is prefix-only conditional on that frozen snapshot and retention rule.

A direct read-only run through the shared loader and new adapter measured:

| Quantity | Measured value |
|---|---:|
| Included catalogue products / modeled slots | 21,874 / 21,874 |
| Included stations | 24 |
| Frozen / movable products | 5,899 / 15,975 |
| Complete retained orders | 284,862 |
| Shared `op_full` list entries | 1,486,618 |
| Distinct retained product-order pairs, matching `pl_full` | 1,486,608 |
| Duplicate list entries removed for robustness workload | 10 |
| Publication station aliases | 26 |
| Included wholly fixed stations on this export | 0 |

All 24 included stations have publication aliases. The existing map assigns `01.GED` to S_25 and `01.15` to S_26. These two stations and the junk code `01.Z8` enter neither the modeled catalogue nor workloads, visits or denominators. The 21,874 included products exclude the products allocated to those removed stations; do not subtract another three locations from this modeled catalogue.

Source SHA-256: `c488e8aac63a052570551602b58e781aebf9aa93819dc943fdbaa6244ebb7048`. Shared loader SHA-256: `0c0c38f7b76ba8d41ef156649919b74642fd4c6f1ed45c0eab8f061242ad4142`. pandas version used: 2.2.3. The earlier approximate reconciliation below reported seven fewer pairs; it is preserved as an audit of the rejected approach, not substituted for these measured authoritative-loader results.

The seven-pair difference is now explained, not an unresolved counting discrepancy: exactly seven raw station cells contain a single space. The original loader does not treat these strings as missing and repairs their station through its global product reconciliation. All seven distinct affected product-order pairs survive that loader, and none also appears in a nonblank raw row. The rejected row-first cleaner stripped these strings and dropped the rows prematurely. This accounts for 1,486,601 versus 1,486,608 pairs. A shared-loader fixture regression test checks this repair-before-filter behavior.

The shared complete-order dictionary uses integer keys and its ordering agrees with numeric chronology. This checks the implementation's sequence, not the operational truth of order-ID chronology. Independent reconstruction of the large-order entry-frequency rule reproduces the fixed pool exactly. Seven duplicate entries occur in large orders, involving seven products. For ONE product this changes its freeze classification compared with distinct-order frequency: the original loader leaves it movable, while a distinct-order interpretation would freeze it. The 5,899/15,975 article partition is preserved; robustness workload still uses distinct pairs. The article's phrase "at most five orders" therefore has a one-product implementation edge case on this export.

In-memory adapter tests exercise the actual shared loader on fixture rows, including global reconciliation before exclusion, station renaming, a fully fixed station absent from the loader's large-order station list, full small-order evaluation, duplicate-pair counting and threshold crossing, exact fixed-mask preservation, zero-history slot allocation, changing frozen future demand through the complete evaluator, and corrupted-payload rejection. No industrial optimization has been run. An independent read-only agent review confirmed the retrospective-selection qualification and identified the fixed-only station/list-count edge cases now covered by the adapter and audit.

## Superseded audit — 8 September 2026

The following records the pre-amendment approach and its then-pending question. It is NOT the current preprocessing contract or an outstanding geometry request.

Former status: slot geometry and cleaning reconciliation required a documented decision. This was not a robustness result. Only the approved BERNER_ORDER_LINES_09-12.csv was read.

Declared cleaning: null removal, GE4/E4 alias, excluded station-row filtering, then distinct product-order workload. Read-only audit found 1,669,346 raw rows; 1,574,906 retained raw rows; 94,433 excluded rows; 7 null rows; 21,875 catalogue products; 25 retained station labels; 1,424 products with multiple observed stations.

An isolated audit of the legacy full-export station reconciliation found 21,874 products, 24 canonical station labels, and 1,486,601 distinct product-order pairs. Declared cleaning yields 1,486,604 pairs: three added pairs involving one added product, none removed. The extra retained station is 01.Z2. The article reports 26 stations; neither raw-label count above is silently equated to that reported geometry.

The legacy audit chooses the lexicographically greatest raw station on the largest numeric order for a product. One product has a same-last-order station tie, whereas the legacy loader's tie rule is unspecified. This uncertainty is reported rather than concealed as exact reproduction.

The legacy whole-export mapping is used only inside the reconciliation diagnostic. It is not supplied as a historical reference or as training labels. Its aggregated station counts could be considered only as an explicitly accepted exogenous geometry surrogate; the declared catalogue also requires accounting for the extra product/01.Z2 slot. No geometry adjustment or source-cleaning change is authorized by this audit alone.

A user question requests pre-known station slot counts, or permission to propose a documented surrogate. Until that is resolved, the industrial optimization branch stays unverified. All catalogue and reference code continues to fail explicitly on ambiguous geometry; synthetic work continues independently.

Reproduction entry point: Baselines.horizon_robustness.catalogue.industrial_reconciliation_audit(). Full output remains available in the execution tool transcript; no future optimization outcomes were read or used.
