I've made the revision. Nothing was written outside `p1a_rev`, I ran no git, and no `__pycache__` appeared in the repository.

- **Script:** `C:\Users\ebelul\AppData\Local\Temp\2\p1a_rev\anchors_A_rev.py`
  SHA-256 `b77a38ceee6d7345df95f9174d3ad8486ac0d37c715c491a9472bc0d4ca3fdc4`
- **Output:** `C:\Users\ebelul\AppData\Local\Temp\2\p1a_rev\out_A_rev.json`
  SHA-256 `2586c0cfdc3d743d1f9062c27ddfcd1e3f3c14504cc3df4b2179ea478a98b2e6`
- **Run:** exit 0, 0 verification warnings, all 18 section E values match.
- **Key count:** 208, the same as before.

**Removed:** `ho.incumbent.training_slack` and `extra.ho.incumbent.training_slack.hist_act_scenarios`.

**Added** (both unit `share`, display_rounding 6, 6 case-record sources with selectors):
- **`ho.incumbent.training_slack.history`:** value_exact `0`, value_float 0.0.
  - Rows: NOM and TIGHT, seeds s11, s22, s33.
  - Scenarios: `history [0, 243151)`.
- **`ho.incumbent.training_slack.hist_act`:** value_exact `1117947199/71202343420`, value_float 0.015700988834111605.
  - Rows: HIST+ACT and HIST+ACT-T, seeds s11, s22, s33.
  - Scenarios: 12 of them, 11 `block` windows (`[2537, 24411)`, `[24411, 46285)`, ... `[221277, 243151)`) plus `history [0, 243151)`.
  - `model_feasible_exact` is True for HIST+ACT and False for HIST+ACT-T.

The script stops with an error if the value or the scenario set differs across the 6 rows of either key. It does the same if the history set is not exactly `history [0, 243151)`, or if the HIST_ACT set has no `block` scenario. It also checks that each arm's own scenario set matches the incumbent's.

**One point for the spec owner:** section D calls the HIST_ACT training set "the historical block scenarios". The stored set also contains the whole-history scenario as its 12th member, and `computation` lists it as stored.

**Unchanged entries:** I compared `out_A_rev.json` with `W/evidence/anchors.json` key by key. The other 206 entries are identical both as raw bytes and as parsed JSON, in the same order. The two new keys sit where the old two were (positions 206-207). The source paths, source hashes and value_exact values also match the old entries.
