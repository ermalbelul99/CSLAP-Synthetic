VERDICT: REVISE

The artifacts are in `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results\writing\evidence\`. Every number I spot-checked matches its anchor, so these findings concern meaning, denominators and coverage.

F: severity BLOCKING; claims.json; C-03 scope_boundary; "a magnitude per direction is not anchored and is not stated"; the predeclaration (lines 459-460) lists "the breach magnitudes in both directions" as a secondary endpoint, and plan line 507 requires "breach magnitudes by direction for the no-margin arms", but ANCHOR_SPEC §A holds only the direction-free `.worst`, so a predeclared quantity is silently dropped; fix: add `ho.breach.<ARM>.<SEED>.cap_worst` and `.floor_worst`, computed from the stored per-station share, cap and floor fields with no solve, and report them in C-03.

F: severity MAJOR; claims.json; C-13 statement and allowed_wording 1; "13.0–16.0% … single runs 12.0–17.5%"; both upper ends come from NOM, which missed the band on every seed (`ho.saving.NOM.pct` 16.0 with `ho.pass.NOM.count` 0), and the maximum is NOM seed 33: (3.847124−3.172488)/3.847124 = 17.536%; single runs of the margin arms span only 11.98–15.10% (TIGHT s11: (3.847124−3.266024)/3.847124 = 15.10%); fix: give each arm's saving with its pass count, and anchor a margin-arm single-run range before quoting one.

F: severity MAJOR; claims.json; denominators of C-10, C-18, C-19 and C-20; "three BERNER horizons"; in case_frame.csv, the BERNER rows of screen_20260910, ts_b01, ts_d02 and ts_b03 give NOM and TIGHT 3 rows each but only 1 distinct layout_hash, while HIST and HIST+ACT have 3 layouts; the TIGHT `min_slack` anchors are also identical across n; fix: write "one TIGHT layout scored at three nested horizons" against "three HIST+ACT layouts", and do not set 3/3 against 1/3 as like counts.

F: severity MAJOR; claims.json; C-15 allowed_wording and C-07 qualifier 3; "were not used" and "unexamined in this study"; handoff lines 887-888 say the snapshot is rebuilt "from the *whole* export", DATA_PROVENANCE.md:5 notes "Future-dependent retention", and plan F5 (line 68) says `_aliases()` "reads the full export, including the forbidden tail"; fix: "used by no solve, score or survey; the orders entered only the snapshot reconstruction (C-27)".

F: severity MAJOR; claims.json; C-08 statement; "the margin was neither set from this statistic"; predeclaration lines 353-357 chose δ = 0.02 because the 1.70 pp statistic shows "±1 is violated by the warehouse's own history", and the reserved margin is ρ = λδ; fix: "δ, and so ρ = λδ, was chosen using this statistic; no rule linking ρ to it was tested".

F: severity MAJOR; claims.json; C-30; "examine the station-level variation in the site's own history against that reserve"; on this case the check fails (`disp.explor.n_P.max_abs` 1.63, like-for-like 1.83, both above 1 pp) yet `ho.pass.TIGHT.count` = 3; the claim also joins exploratory-prefix dispersion to the held-out outcome without C-08 qualifier 1; fix: say the check did not predict compliance here, or drop it, and add that qualifier.

F: severity MAJOR; claims.json; C-01; per-seed visit ranges are given only for the margin arms; the no-margin ranges overlap: NOM 3.172–3.266, HIST+ACT 3.239–3.278 (`ho.visits.*.s11/s22/s33`); plan line 546 requires seed ranges of visits; fix: give both ranges and state the overlap; also forbid "closer to target than the incumbent", because two HIST+ACT-T seeds (1.026 and 1.039) lie below `ho.maxdev.incumbent` 1.157.

F: severity MINOR; claims.json; qualifiers of C-04, C-06 and C-31; none carries a visible "additional descriptive" label, although the reviewed plan (line 99) says these readings "must be identified" (RQ-007, RQ-008); fix: add C-01's qualifier sentence.

F: severity MINOR; claims.json; C-21; "12 or 13 for NOM and TIGHT"; with a single-point modelled set, above plus below is 24 on every seed (11+13, 12+12); fix: say "all 24 stations by construction", and do not compare these counts with the scenario arms' 2 to 4.

F: severity MINOR; claims.json; C-05; "a bound of 11,517"; in the held-out rows of case_frame.csv, `objective` equals `historical_visit_count` (743,791–788,928), so the gap and bound refer to training visits; fix: name that objective.

F: severity MINOR; interpretation_errata.md; one missing entry and a stale E-29; handoff lines 871-873 ("Its bound on the visits objective is 0 and its gap is 1.0 throughout") contradict the held-out records, and C-05 cites that item; E-29 is still UNRECONCILED although Q-018 is resolved; fix: add a RESTRICTED entry for that item and update E-29.

F: severity MINOR; document_values.json; comp.budget.definition and handoff.q2.incumbent_headroom; the first value, "110% of legacy load", paraphrases companion line 584, against DOCUMENT_VALUES_SPEC.md:13 "Never paraphrase"; the headroom sentence starts on line 1028 ("Because b is the"), not 1029; fix: re-extract verbatim and cite line 1028.

F: severity MINOR; requirements_map.json; RQ-021, RQ-053, RQ-027, RQ-029; C-14 does not state the authorised data scope, and the margin shown beside the drift survey is in C-31, not C-06; RQ-027 and RQ-029 are still UNMAPPED because C-26 lacks the large-order filter and the edge case at DATA_PROVENANCE.md:27; fix: remap RQ-021, add C-31 to RQ-053, and extend C-26.

F: severity MINOR; claims.json; C-13 reasons for setting aside the in-sample 13.7% ("extract … reference layout … differ"); companion lines 568-579 give the same counts as C-26 (21,874; 24; 15,975; 5,899), and Q-002's reasons cover the unseen weeks only; Q-card (Class E): does the in-sample table tab:industrial use the same export? Decisive test: companion supplement §S6 against the source hash at DATA_PROVENANCE.md:23. Conservative default: cite only the stream and the workload restriction.

**Q-020:** the anchors support option (b) for HIST+ACT, scoped to this case.
- **Misses, per campaign and never pooled:** 0/3 held-out seeds (`ho.pass.HIST_ACT.count`); 0/3, 1/3 and 0/3 exploratory layouts (`ts.berner.d01/d02/d03.pass.HIST_ACT.count`).
- **The immediate cause of the misses is anchored, not uncertain:**
  - every returned layout used its whole allowance (`ho.min_slack.HIST_ACT.*` 0.019997–0.019999);
  - the future fell below the modelled set at 3, 4 and 4 stations (`ho.departures.HIST_ACT.*.below`).
- **Category:** reviewer-first §XII line 574 reserves "empirical limitation" for cases where the mechanism is uncertain, while line 586, "did not work as intended", fits.
- **What stays as written:** NOM is the unprotected control, not a method; the departure from the modelled set stays a boundary condition; "the method fails" stays forbidden.
