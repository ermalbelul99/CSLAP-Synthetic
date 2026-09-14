F-078 VERIFICATION: CONFIRMED

- **Predeclaration and plan require it.** `R/CAMPAIGN_PREDECLARATION.md` §9.3 lines 459–460 lists as a predeclared secondary endpoint "the breach magnitudes in both directions" per arm. `R/WRITING_ORCHESTRATION_PLAN_20260914.md` line 507 requires "breach magnitudes by direction for the no-margin arms" among P1 step 2's required anchors.

- **Prior specification lacked it.** `W/governance/results/P1-W8-prior-ANCHOR_SPEC.md` §A lines 47–48: `ho.breach.<ARM>.<SEED>.worst` is direction-free (0 if pass), and `.cap_count`/`.floor_count` are only station counts by direction, not magnitudes. No cap-side or floor-side magnitude field existed. `R/tables/case_frame.csv` header (checked in full) confirms the same gap at the table level: only `worst_excess_pp`/`worst_excess_pp_exact` (direction-free) and `cap_violation_count`/`floor_violation_count` (counts).

- **Computable without a solve.** One held-out case record, `R/campaigns/ho3_20260913/cases/c8660e8c...df9.json` (NOM, seed 11, via manifest.json), stores `evaluation.stations[*]` with `share`/`share_exact` (per-station future share), `cap`/`cap_exact`, and `floor`/`floor_exact` for each of the 24 stations. Cap-side and floor-side magnitudes are directly computable as max(share−cap,0) and max(floor−share,0) from these stored fields — no solver invocation needed.

- **New rows cover the requirement.** Current `W/evidence/ANCHOR_SPEC.md` line 49 adds `ho.breach.<ARM>.<SEED>.cap_worst`, `.floor_worst` (pp) for NOM, TIGHT, HIST_ACT, HIST_ACT_T, explicitly tagged `(F-078)`, sourced from the case records' per-station shares/cap/floor. This covers all four arms, including the required no-margin arms NOM and HIST_ACT (identified as "no-margin" by the companion row at line 51, F-079).
