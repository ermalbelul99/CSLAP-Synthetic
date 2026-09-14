# Anchor specification (P1 step 2)

Both blind builders produce JSON with exactly these keys, and `compare_anchors.py` compares them. Keys marked
*optional* may be `"UNAVAILABLE"` with a reason. Extra keys go under the prefix `extra.`.

## Conventions

**Paths.** Relative to the repository root. `R` = `reports/horizon_robustness_results`.

**Allowed inputs.** Read only these:
- `R/tables/*.csv`
- `R/campaigns/<name>/cases/*.json` for the campaigns named here
- `R/campaigns/<name>/manifest.json`
- `R/analysis_audit.md`, `R/artifact_index.json`

Never import or run any repository module, never read `Heuristic_Connex_Set_Project/`, and never read raw order data.

**Entry format.** Each key maps to:
`{"value_exact": str, "value_float": float|null, "unit": str, "display_rounding": int|null, "sources": [{"path": str, "sha256": str, "selector": str}], "computation": str}`

**`value_exact`.** Use:
- an exact rational `"p/q"` or integer `"n"` when the artifact carries an exact field (for example `*_exact`) or the value is a count;
- otherwise the decimal string exactly as stored in the file.

**Units.** `count`, `visits_per_order`, `share`, `pp` (percentage points = share × 100), `pct` (percent), `tv`, `fraction`, `bool` (`"1"`/`"0"`).

**Arm tokens.** `NOM`, `TIGHT`, `HIST_ACT` (stored `HIST+ACT`), `HIST_ACT_T` (stored `HIST+ACT-T`), `HIST`. Seeds are `s11`, `s22`, `s33`.

**Discovery.** Column and field names are discovered, never assumed. Report every selector you used.

## A. Held-out factorial

Campaign `ho3_20260913`: stage holdout, BERNER, origin 243151, n = 21874, rule two_sided, δ 0.02, ν 0.01, λ 0.5.

| Key pattern | Unit | Definition |
|---|---|---|
| `ho.pass.<ARM>.count` for NOM, TIGHT, HIST_ACT, HIST_ACT_T | count | seeds with joint two-sided pass (of 3) |
| `ho.visits.<ARM>.<SEED>` for NOM, TIGHT, HIST_ACT, HIST_ACT_T | visits_per_order | exact mean future visits per order |
| `ho.visits.<ARM>.mean` for NOM, TIGHT, HIST_ACT, HIST_ACT_T | visits_per_order | exact mean over the three seeds |
| `ho.visits.incumbent` | visits_per_order | incumbent (reference) mean future visits on the same future; confirm it is identical across the 12 rows |
| `ho.visits.HIST_ACT_T_over_TIGHT.pct` | pct | (mean HIST_ACT_T / mean TIGHT − 1) × 100, from exact means |
| `ho.saving.<ARM>.pct` for NOM, TIGHT, HIST_ACT, HIST_ACT_T | pct | (incumbent − arm mean) / incumbent × 100 |
| `ho.saving.single_run.min.pct`, `ho.saving.single_run.max.pct` | pct | min and max over the 12 rows of (incumbent − seed visits) / incumbent × 100 |
| `ho.maxdev.<ARM>.<SEED>` for NOM, TIGHT, HIST_ACT, HIST_ACT_T | pp | max over the 24 evaluated stations of \|future share − target\| × 100 |
| `ho.maxdev.<ARM>.max`, `ho.maxdev.<ARM>.min` for NOM, TIGHT, HIST_ACT, HIST_ACT_T | pp | over the three seeds |
| `ho.maxdev.incumbent` | pp | the same quantity for the incumbent on the same future, from the case records' reference evaluation (exact fields where present) |
| `ho.breach.<ARM>.<SEED>.worst` for NOM, TIGHT, HIST_ACT, HIST_ACT_T | pp | worst excess beyond the band (0 if pass) |
| `ho.breach.<ARM>.<SEED>.cap_count`, `.floor_count` for NOM, TIGHT, HIST_ACT, HIST_ACT_T | count | stations above cap / below floor |
| `ho.breach.<ARM>.<SEED>.cap_worst`, `.floor_worst` for NOM, TIGHT, HIST_ACT, HIST_ACT_T | pp | largest excess above the cap and largest shortfall below the floor over the 24 evaluated stations, × 100, from the case records' stored per-station future shares and band limits (exact fields where present); 0 when no station lies beyond that side; the larger of the two equals `.worst`, and a side is positive exactly when its count is positive (F-078) |
| `ho.saving.single_run.margin.min.pct`, `ho.saving.single_run.margin.max.pct` | pct | min and max over the 6 TIGHT and HIST_ACT_T rows of (incumbent − seed visits) / incumbent × 100 (F-079) |
| `ho.saving.single_run.no_margin.min.pct`, `ho.saving.single_run.no_margin.max.pct` | pct | the same over the 6 NOM and HIST_ACT rows (F-079) |
| `ho.min_slack.<ARM>.<SEED>` for NOM, TIGHT, HIST_ACT, HIST_ACT_T | share | `minimum_required_slack`, exact field if present |
| `ho.gap.<ARM>.<SEED>`, `ho.bound.<ARM>.<SEED>` for NOM, TIGHT, HIST_ACT, HIST_ACT_T | fraction / visits | solver gap and bound as stored |
| `ho.incumbent.joint_pass` | bool | same for all rows |
| `ho.incumbent.worst_excess` | pp | |
| `ho.departures.<ARM>.<SEED>.above`, `.below` for NOM, TIGHT, HIST_ACT, HIST_ACT_T | count | stations above the highest / below the lowest modelled share (both directions); *optional* if absent, with reason |

## B. Drift and dispersion (F16, F17)

| Key | Unit | Definition |
|---|---|---|
| `drift.holdout.hist_tv_max`, `.hist_tv_mean`, `.hist_tv_p90`, `.hist_tv_last`, `.future_tv`, `.blocks`, `.n`, `.origin` | tv / count | row `BERNER@holdout` of `R/tables/drift_survey.csv` |
| `drift.holdout.w_star` | fraction | 1 − hist_tv_max / future_tv |
| `drift.holdout.w_order_count` | fraction | n / origin |
| `drift.holdout.hist_tv_max.like_for_like` | tv | hist_tv_max / (1 − w_order_count) |
| `drift.holdout.hist_tv_max.like_for_like.w_0_05`, `.w_0_10`, `.w_one_eleventh` | tv | hist_tv_max / (1 − w) for those w |
| `disp.explor.<H>.max_abs` for H in n_half, n_P, n_2P | pp | BERNER rows at origin 199403 of `R/tables/dispersion_survey.csv` (n = 10937, 21874, 43748) |
| `disp.explor.<H>.max_abs.like_for_like` for H in n_half, n_P, n_2P | pp | max_abs / (1 − n / 199403) |

## C. Upper-only versus two-sided reconciliation (F12)

| Key | Unit | Definition |
|---|---|---|
| `uo.berner.pass.<ARM>.count` for NOM, TIGHT, HIST, HIST_ACT | count | BERNER upper-only screen (`screen_20260910`, δ 0.01): horizons passed, of 3 |
| `uo.berner.min_slack.TIGHT.<n>` | share | TIGHT `minimum_required_slack` at each BERNER horizon, upper-only |
| `ts.berner.d01.pass.<ARM>.count` for NOM, TIGHT, HIST, HIST_ACT | count | BERNER two-sided, δ 0.01, campaign `ts_b01_20260912`: horizons passed, of 3 (Q-012) |
| `ts.berner.d02.pass.<ARM>.count` for NOM, TIGHT, HIST, HIST_ACT | count | BERNER two-sided, δ 0.02, campaign `ts_d02_20260912`: horizons passed, of 3 (Q-012) |
| `ts.berner.d03.pass.<ARM>.count` for NOM, TIGHT, HIST, HIST_ACT | count | BERNER two-sided, δ 0.03, campaign `ts_b03_20260912`: horizons passed, of 3 (Q-012) |
| `ts.berner.d02.min_slack.TIGHT.<n>` | share | |
| `ts.berner.d02.HIST_ACT.cap_breaches_total`, `.floor_breaches_total` | count | summed over the three horizons |
| `ts.berner.d02.HIST.cap_breaches_total`, `.floor_breaches_total` | count | |
| `uo.berner.layouts.<ARM>.count` for NOM, TIGHT, HIST, HIST_ACT | count | distinct `layout_hash` values over the BERNER rows of `screen_20260910` for that arm (F-080) |
| `ts.berner.d01.layouts.<ARM>.count` for NOM, TIGHT, HIST, HIST_ACT | count | the same for `ts_b01_20260912` (F-080) |
| `ts.berner.d02.layouts.<ARM>.count` for NOM, TIGHT, HIST, HIST_ACT | count | the same for `ts_d02_20260912` (F-080) |
| `ts.berner.d03.layouts.<ARM>.count` for NOM, TIGHT, HIST, HIST_ACT | count | the same for `ts_b03_20260912` (F-080) |
| `ts.synthetic_instances.count` | count | distinct synthetic datasets run two-sided |

## D. Accounting and context

| Key | Unit | Definition |
|---|---|---|
| `acct.campaigns.analysed` | list in `value_exact` as JSON string | non-superseded campaigns used by the analysis; stated in `R/analysis_audit.md` §"Campaigns included" (lines 13-20, six rows); cross-check against `R/tables/case_frame.csv` `campaign` values |
| `acct.campaigns.superseded` | list | superseded directories; `R/analysis_audit.md` line 22 ("Excluded as superseded"), four names |
| `acct.rows.authorized`, `acct.rows.scored`, `acct.rows.no_allocation` | count | over analysed campaigns; `R/analysis_audit.md` §"Denominator audit" (lines 28-36); recompute from `case_frame.csv` where possible |
| `acct.layouts.scored` | count | for Q-009 |
| `alias.join_exact` | bool | 1 if `station_index` in `R/tables/station_profile_industrial.csv` joins one-to-one onto the station indices used in the held-out case records' reference evaluation (Q-007) |
| `alias.map` | JSON string | `{station_index: "S_k"}` |
| `ho.incumbent.training_slack.history` | share | the incumbent's `minimum_required_slack_exact` in `reference_evaluation.validation`, taken from the NOM and TIGHT rows of `ho3_20260913`. Their training scenario set is the single history scenario [0, 243151). Confirm the value is identical across those 6 rows and report the scenario labels (Q-005) |
| `ho.incumbent.training_slack.hist_act` | share | the same field, taken from the HIST_ACT and HIST_ACT_T rows of `ho3_20260913`. Their stored training scenario set has 12 members: the 11 historical block scenarios plus the single history scenario [0, 243151) (F-067). Confirm the value is identical across those 6 rows and report the scenario labels (Q-005) |

## E. Reviewed-plan cross-check (displayed precision)

Values from `WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` lines 80-86 and 96. `compare_anchors.py` compares each at the shown number of decimals.

| Anchor key | Displayed value |
|---|---|
| `ho.pass.NOM.count` / `TIGHT` / `HIST_ACT` / `HIST_ACT_T` | 0 / 3 / 0 / 3 |
| `ho.visits.NOM.mean` | 3.231630 |
| `ho.visits.TIGHT.mean` | 3.269742 |
| `ho.visits.HIST_ACT.mean` | 3.263692 |
| `ho.visits.HIST_ACT_T.mean` | 3.346774 |
| `ho.visits.incumbent` | 3.847124 |
| `ho.maxdev.NOM.max` | 3.143883 |
| `ho.maxdev.TIGHT.max` | 1.756255 |
| `ho.maxdev.HIST_ACT.max` | 2.178584 |
| `ho.maxdev.HIST_ACT_T.max` | 1.159749 |
| `ho.maxdev.incumbent` | 1.156787 |
| `ho.visits.HIST_ACT_T_over_TIGHT.pct` | 2.355907 |
| `drift.holdout.future_tv` | 0.194956 |
| `drift.holdout.hist_tv_max` | 0.194411 |
| `drift.holdout.hist_tv_mean` | 0.171100 |
