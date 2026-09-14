<!-- ORCH storage note, 2026-09-14, after SNAPSHOT MATCH P1-W4.

What this file holds:
- The final reply of builder B's retry (optimization-coder/sonnet, seq 36, retry of seq 28), stored verbatim except for its SCRIPT block.
- The SCRIPT block is omitted. It was the complete script shown inline, and the task notification HTML-escaped it (&lt;, &gt;, &amp;).
- The authoritative script and output are the files the agent saved in its private directory, C:\Users\ebelul\AppData\Local\Temp\2\p1b_retry\. ORCH verified both SHA-256 values against the agent's statement, then copied the files here:
  - P1-036-anchors-B-retry.script.py, sha256 8e61a558167bafae1fa91061a4a61eb4eed8bc3132e117a4f47554424e02387b
  - P1-036-anchors-B-retry.output.json, sha256 d9e910f800e1eeeef2cdba12b6d4f1f9439b3be4fe659ab33a7b2dbbc70bd4d9 (203 keys) -->

Clean run, no stderr, no stray artifacts, no `__pycache__`. All 203 keys computed, all 18 Section-E cross-check anchors match to 6 decimals. Returning per the dispatch format.

---

**SCRIPT**

[ORCH: the complete script shown inline here is omitted. It is stored byte-exact as P1-036-anchors-B-retry.script.py; see the note above.]

**OUTPUT**

Saved (too large for one reply, per the retry addendum): `C:\Users\ebelul\AppData\Local\Temp\2\p1b_retry\out_B.json`
SHA-256: `d9e910f800e1eeeef2cdba12b6d4f1f9439b3be4fe659ab33a7b2dbbc70bd4d9`
(203 keys, 139166 bytes)

Script also saved: `C:\Users\ebelul\AppData\Local\Temp\2\p1b_retry\anchors_B.py`
SHA-256: `8e61a558167bafae1fa91061a4a61eb4eed8bc3132e117a4f47554424e02387b`

**NOTES** (word count kept under budget)

Selectors discovered: two evaluation-record shapes coexist per case JSON. `evaluation` (arm's own future evaluation) and `reference_evaluation` (incumbent's, structurally identical, verified byte-identical across all 12 ho3 rows for mean_visits/maxdev/joint_pass/worst_excess). Per-station truth lives in `stations[i]` with `share_exact`/`target_exact` (used for maxdev, literal |share−target|×100 — distinct from the stored `residual_exact`, which is actually share−cap, not share−target). Breach magnitude = artifact field `worst_excess_percentage_points_exact` (already clipped to 0 on pass). Cap/floor counts = `cap_violation_count`/`floor_violation_count`. Departures = per-station bools `beyond_worst_scenario`/`below_lowest_scenario`. Training slack = top-level `validation.minimum_required_slack_exact` (arm) / nested `reference_evaluation.validation...` (incumbent). Station alias = `station_profile_industrial.csv` columns `station_index`,`station` (e.g. index 0 → "S_19"), one-to-one with case `station_index` 0-23, campaign=ho3_20260913. `acct.layouts.scored` = distinct `layout_hash` among `case_frame.csv` scored==True rows (188), not disambiguated further by spec.

UNAVAILABLE: `ho.incumbent.training_slack` — the candidate field carries two conflicting values across the 12 ho3 rows depending on which `scenario_shares[0]` block got attached (history/origin-scoped vs a narrow block), so no single incumbent value is confidently sourced.

Section E: all 18 cross-check values matched to 6 decimals, no mismatches.

Q-card: which of the two `reference_evaluation.validation` blocks (history-scoped vs block-scoped) is the intended "incumbent training slack," if any — decisive test would be checking the incumbent-construction tool's own record, which builder B was barred from opening. Conservative default used: UNAVAILABLE. Class E.
