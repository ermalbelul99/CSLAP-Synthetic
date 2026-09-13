# Analysis audit

Regenerated 2026-09-13T17:55:44Z from immutable campaign artifacts, in 41.96 s, by analysis version `2026-09-13-r3`. No optimizer is imported by this path.

Reproduce with:

```powershell
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' tools/horizon_robustness/make_analysis.py
```

## Campaigns included

| Campaign | Stage | Manifest hash | Implementation hash | Rows | Unique solves | Quoted solver s |
|---|---|---|---|---:|---:|---:|
| `ho3_20260913` | holdout | `d4d4ed6c9772565a…` | `4e359efde84f6c4a…` | 12 | 12 | 21600 |
| `pilot_20260910b` | pilot | `8d36ea49ad1b9158…` | `36ed25e9052df5e9…` | 8 | 8 | 6840 |
| `screen_20260910` | screen | `64178e37f4df73a8…` | `d437a20660533119…` | 360 | 153 | 66600 |
| `ts_b01_20260912` | sensitivity | `13e5bf8bc5d31a71…` | `5e1ee22fe31372d8…` | 12 | 8 | 14400 |
| `ts_b03_20260912` | sensitivity | `756a6ad746b42eda…` | `5e1ee22fe31372d8…` | 12 | 8 | 14400 |
| `ts_d02_20260912` | screen | `4d0b6fbe8eaca292…` | `5e1ee22fe31372d8…` | 60 | 28 | 25500 |

Excluded as superseded (preserved on disk, never analysed): `pilot_20260910`, `twosided_berner_d01_20260912`, `twosided_berner_d03_20260912`, `twosided_screen_d02_20260912`.

## Denominator audit

Every authorized manifest row lands in exactly one bin. A row that produced no layout carries `None` for every future metric, never zero.

| Bin | Rows |
|---|---:|
| Authorized rows | 464 |
| Ineligible by protocol | 0 |
| No record at all | 0 |
| Returned no allocation | 52 |
| Allocation returned but not scored | 0 |
| Scored on its future horizon | 412 |
| **Accounted** | **464** |

Accounting complete: yes.

### Status detail

| Status | Rows |
|---|---:|
| `COMPLETE` | 412 |
| `NO_INCUMBENT_LIMIT` | 51 |
| `NUMERICAL_ISSUE` | 1 |

## Pseudoreplication rules applied

* A pair is formed only inside one exactly matched cell (dataset, origin, n, seed, δ, ν, λ, solve mode), and only when both members were scored.
* Solver seeds measure algorithm variability. They are averaged within an instance and never counted as extra future streams.
* Horizons at one origin share data and are reported separately, never pooled.
* Individual stations are not independent observations; joint compliance is per cell.
* `stratum_summary` and `paired_stratum_summary` use the INSTANCE as the unit; `paired_instances` states how many instances each difference rests on.
* Every table row carries `rule`. Upper-only and two-sided rows are summarised separately and never pooled. `frontier_<axis>_pooled_by_rule` pools campaigns only inside one (rule, implementation hash) and names every campaign it merged.

## Predeclared primary-summary rule

Primary summaries read `cases/<case_id>.json` only. Deliberate retries are inventoried separately and never substituted for a primary attempt. This rule was fixed before any result was inspected.

## Tables

| Table | Rows | Columns | Content hash |
|---|---:|---:|---|
| `tables/case_frame.csv` | 464 | 86 | `c479cacc595eb9d0…` |
| `tables/cross_horizon.csv` | 800 | 27 | `70fd6934113fd3ba…` |
| `tables/dispersion_survey.csv` | 90 | None | `74d52002a50ff8bf…` |
| `tables/drift_survey.csv` | 15 | None | `a2b5814516fe8953…` |
| `tables/frontier_delta.csv` | 456 | 24 | `462099829ea54d50…` |
| `tables/frontier_delta_pooled_by_rule.csv` | 456 | 26 | `9220c353de2a2c99…` |
| `frontier_nu` | — | — | not produced: only one nu value (['0.01']) is present; no frontier is defined |
| `frontier_tightening` | — | — | not produced: only one tightening value (['0.5']) is present; no frontier is defined |
| `tables/instance_summary.csv` | 456 | 32 | `5903e4e4d796cb9a…` |
| `min_slack_diagnostic` | — | — | not produced: no rows produced by the current campaigns |
| `tables/min_slack_diagnostic_cplex.csv` | 6 | None | `1f0d3fa701e159d1…` |
| `tables/paired_cases.csv` | 688 | 38 | `9d046da9302c14b7…` |
| `tables/paired_stratum_summary.csv` | 212 | 52 | `702c9d9b51759288…` |
| `tables/resources.csv` | 464 | 23 | `4c8918477db5f001…` |
| `tables/slack_survey.csv` | 360 | None | `85dcab154e204a0a…` |
| `tables/slack_survey_cross_arm.csv` | 24 | None | `abe3575ef1e38571…` |
| `tables/station_profile_industrial.csv` | 1464 | 34 | `b4437fd35342e087…` |
| `tables/station_profile_synthetic.csv` | 225 | 34 | `119abce4a8f90259…` |
| `tables/status_by_cell.csv` | 456 | 13 | `892f774929b313c7…` |
| `tables/stratum_summary.csv` | 156 | 28 | `8a7ab697036dd9fb…` |
| `tables/two_sided_novelty_survey.csv` | 72 | None | `9ee2156215fad231…` |

## Diagnostic records

Produced outside the campaign runner; each carries its own content hash.

| Record | Kind | Hash |
|---|---|---|
| `diagnostics\berner_recheck_HISTACT_20260910T141951Z.json` | numerical_formulation_recheck | `caac830d1deaefb1…` |
| `diagnostics\min_slack_20260910T160712Z.json` | predeclared_min_slack_diagnostic | `c436936e5e4d0dfa…` |

## Figures

Each figure prints its own denominator and has the CSV above as its table view.

* `figures/cross_horizon_transfer.png` — cross_horizon_transfer
* `figures/ho3_20260913/joint_compliance_by_horizon.png` — ho3_20260913/joint_compliance_by_horizon
* `figures/ho3_20260913/station_profile_industrial.png` — ho3_20260913/station_profile_industrial
* `figures/ho3_20260913/status_breakdown.png` — ho3_20260913/status_breakdown
* `figures/ho3_20260913/visits_versus_excess.png` — ho3_20260913/visits_versus_excess
* `figures/joint_compliance_by_horizon.png` — joint_compliance_by_horizon
* `figures/pilot_20260910b/cross_horizon_transfer.png` — pilot_20260910b/cross_horizon_transfer
* `figures/pilot_20260910b/joint_compliance_by_horizon.png` — pilot_20260910b/joint_compliance_by_horizon
* `figures/pilot_20260910b/station_profile_industrial.png` — pilot_20260910b/station_profile_industrial
* `figures/pilot_20260910b/status_breakdown.png` — pilot_20260910b/status_breakdown
* `figures/pilot_20260910b/visits_versus_excess.png` — pilot_20260910b/visits_versus_excess
* `figures/pooled/two_sided__5e1ee22f/frontier_delta.png` — pooled/two_sided__5e1ee22f/frontier_delta
* `figures/station_profile_industrial.png` — station_profile_industrial
* `figures/status_breakdown.png` — status_breakdown
* `figures/ts_b01_20260912/cross_horizon_transfer.png` — ts_b01_20260912/cross_horizon_transfer
* `figures/ts_b01_20260912/joint_compliance_by_horizon.png` — ts_b01_20260912/joint_compliance_by_horizon
* `figures/ts_b01_20260912/station_profile_industrial.png` — ts_b01_20260912/station_profile_industrial
* `figures/ts_b01_20260912/status_breakdown.png` — ts_b01_20260912/status_breakdown
* `figures/ts_b01_20260912/visits_versus_excess.png` — ts_b01_20260912/visits_versus_excess
* `figures/ts_b03_20260912/cross_horizon_transfer.png` — ts_b03_20260912/cross_horizon_transfer
* `figures/ts_b03_20260912/joint_compliance_by_horizon.png` — ts_b03_20260912/joint_compliance_by_horizon
* `figures/ts_b03_20260912/station_profile_industrial.png` — ts_b03_20260912/station_profile_industrial
* `figures/ts_b03_20260912/status_breakdown.png` — ts_b03_20260912/status_breakdown
* `figures/ts_b03_20260912/visits_versus_excess.png` — ts_b03_20260912/visits_versus_excess
* `figures/ts_d02_20260912/cross_horizon_transfer.png` — ts_d02_20260912/cross_horizon_transfer
* `figures/ts_d02_20260912/joint_compliance_by_horizon.png` — ts_d02_20260912/joint_compliance_by_horizon
* `figures/ts_d02_20260912/station_profile_industrial.png` — ts_d02_20260912/station_profile_industrial
* `figures/ts_d02_20260912/status_breakdown.png` — ts_d02_20260912/status_breakdown
* `figures/ts_d02_20260912/visits_versus_excess.png` — ts_d02_20260912/visits_versus_excess
* `figures/visits_versus_excess.png` — visits_versus_excess

## Retries and reruns

No deliberate retry was executed in any included campaign.
