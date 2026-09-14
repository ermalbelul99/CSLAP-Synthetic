<!-- ORCH storage note, 2026-09-14T12:16Z, after SNAPSHOT MATCH P1-W2.

How this reply was split:
- The agent (general-purpose/opus, seq 27) returned its reply in two messages. Its first message was cut at stdout line 144.
- The final message, below, re-emits stdout lines 144-167, and says lines 168-210 will follow in a further message. No further message came, because the agent completed.
- The first message is not available to ORCH. The task notification carries the final message only.

What this file contains:
- The final message, stored verbatim, except for its OUTPUT continuation JSON block (stdout lines 144-167).
- That block is omitted because it duplicates part of the complete output file, and ORCH marks the omission below.

The complete script and stdout, which the agent saved outside the repository with the hashes it stated, are stored beside this file. ORCH checked both hashes on 2026-09-14T12:15Z:
- P1-027-anchors-A.script.py, sha256 b7563ae441a062b37af2d23043b0ff9d31bac3681712c14d7818a683e3d5a73c
- P1-027-anchors-A.output.json, sha256 2054aab277e6f9abf6241375387b24fad5ed02c3b79e7599fb0e631e96804883

Both files were written to the ORCH session scratchpad, which builder B used as well. See finding F-059. -->

The OUTPUT block in my previous message was cut at stdout line 144 of 210. Here the essentials come first: the full-file reference and NOTES. After them, the OUTPUT continues, re-emitting line 144 whole through the closing brace. The complete stdout is also saved outside the repository at `C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\b64556bb-2417-49e0-8f03-4e398614f9a0\scratchpad\out_A.json`, with sha256 `2054aab277e6f9abf6241375387b24fad5ed02c3b79e7599fb0e631e96804883`. The script is at `...\scratchpad\anchors_A.py`, with sha256 `b7563ae441a062b37af2d23043b0ff9d31bac3681712c14d7818a683e3d5a73c`.

**NOTES**

- **Fields read from case JSON:**
  - `case.{arm,seed,n,origin,rule,delta,stage}`, `status`
  - `evaluation.{mean_visits_exact, visit_count, order_count, joint_pass, cap_violation_count, floor_violation_count, worst_excess_percentage_points_exact, station_novelty_count(_lower)}`
  - `evaluation.stations[*].{share_exact, target_exact, cap_exact, floor_exact, worst_share_exact, lowest_share_exact, beyond_worst_scenario, below_lowest_scenario, station_index, station_id}`
  - `reference_evaluation.*`, including `.validation.minimum_required_slack_exact`
  - `validation.minimum_required_slack_exact`, `solve_result.{gap,bound}`, manifest `rows[].expected_result`
- **Columns read from tables:**
  - `case_frame`: campaign, dataset_id, rule, delta, arm, n, seed, scored, allocation_returned, joint_pass, cap_violation_count, floor_violation_count, minimum_required_slack, layout_hash, solve_key.
  - `drift_survey`: historical_tv_*, future_tv_ex_post, historical_blocks.
  - `dispersion_survey`: max_abs_pp, horizon_multiple.
  - `station_profile_industrial`: station, station_index, target, future_share.
- **UNAVAILABLE keys:** none. The ts_* records lack `lowest_share_exact`, but none of their keys needs it. Upper-only screen records have no `rule` field, so rule comes from case_frame.
- **Section E:** all 18 values match. The cross-checks against case_frame, policy_validation and exact station recounts gave 0 warnings.
- **Conventions:**
  - Values derived from stored decimals are exact rationals of those decimals.
  - `display_rounding` is 6 for continuous values, 4 for stored dispersion values, and null for counts, bools and lists.
  - Bound unit is "visits".
- **Hash observation:** the audit's content hash differs from the file sha256 for `case_frame.csv` (c479cacc… vs 0e9dc1f5…) and `station_profile_industrial.csv` (b4437fd3… vs fabfca65…). `dispersion_survey.meta.json` records 84d80f90…, but the file is 74d52002…. I did not investigate further.

**Q-card 1 (`acct.layouts.scored`, Q-009)**
- **Question:** what counts as a "layout scored"?
- **Why it matters:** the candidates give 188, 189, 190 or 412.
- **Decisive test:** the Q-009 wording.
- **Options:**
  - distinct layout_hash among scored rows: 188
  - distinct solve_key: 189
  - per-campaign sum: 190
  - scored rows: 412
- **Conservative default:** 188.
- **Class:** J.

**Q-card 2 (`ho.incumbent.training_slack`, Q-005)**
- **Question:** which training scenario set is meant?
- **Why it matters:** the history-only set gives 0 by construction. The 12-scenario HIST+ACT set gives 1117947199/71202343420 ≈ 0.015701, which is feasible at δ 0.02 and infeasible at the tightened 0.01.
- **Decisive test:** the Q-005 wording.
- **Default:** cite a value only with its scenario set named.
- **Class:** J.

**OUTPUT (continued, stdout lines 144–210)**

[ORCH: the JSON block that followed here, covering stdout lines 144-167, is omitted. It duplicates part of the complete output file P1-027-anchors-A.output.json.]

I'll emit the remaining lines 168–210 (C and D sections) in my next message, so this one stays under the output limit.
