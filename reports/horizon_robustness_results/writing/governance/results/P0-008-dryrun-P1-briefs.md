Now let me compile my critical review of the P1 briefs. Based on my read-only probes, here is my report:

## Feasibility Review: P0 Dry Run of P1 Briefs

**Blockers.** None absolute.

1. **Blindness enforcement via file structure.** P1-anchors-A (opus) writes to `W/evidence/anchors.json` and `W/tools/recompute_anchors.py`. P1-anchors-B (fable) is blind to `W/evidence/anchors.json` and must write to `W/evidence/independent/`. The plan (line 494) expects ORCH to save both pairs and re-run both scripts. Isolation therefore depends on builders honouring their read blindness and on ORCH enforcing it at dispatch; any filesystem race would break it. Mitigation: the independent directory exists, and dispatch sequencing is specified.

2. **CSV columns and JSON schema verified.** The allowed inputs exist with the expected structure:
   - `case_frame.csv` has 89 columns, including `minimum_required_slack`, `mean_visits_exact`, `reference_mean_visits` and `joint_pass`, all needed for anchors A–D.
   - `station_profile_industrial.csv` has the station index and the future, historical and residual columns needed.
   - The columns of `drift_survey.csv` and `dispersion_survey.csv` match ANCHOR_SPEC sections B–C.
   - The campaign JSON files in `ho3_20260913` carry both `evaluation` and `reference_evaluation` keys, with the required fields.

**Guess points.**

1. **Exact field discovery** (P1-anchors briefs). ANCHOR_SPEC says to use exact fields when the artifact carries `*_exact` names (spec line 21), and also that names are discovered, never assumed (spec line 29). The spec cites `mean_visits_exact` in `case_frame.csv` and validation fields under `reference_evaluation` (line 89; F18 verified). It does not settle whether `reference_evaluation.minimum_required_slack_exact` or `validation.minimum_required_slack_exact` is canonical. A Q-card is needed unless F18 is treated as settled fact.

2. **Is the stream end an index or a length?** (P1-docvalues briefs). DOCUMENT_VALUES_SPEC line 39 defines `prov.stream_end` as "count | index of the last retained order, or the stream length". The derived tail is `prov.tail_unused = prov.stream_end − prov.tail_start`, or `prov.stream_end + 1 − prov.tail_start`, depending on which it is, and the extractor must state its choice. Plan P1 step 3 gives the stream end as 284,862 (line 530), and plan fact F9 says chronology comes from numeric order IDs without stating an index convention. The extractors must decide and state their choice; the plan's expected value of 19,837 implies the canonical interpretation.

3. **Campaign blindness for document values.** P1-docvalues-A (haiku) and P1-docvalues-B (opus) cannot open `W/evidence/independent/`. Both extract from IJSSOL_CSLAP_v1.tex, the predeclarations and the handoff, and both return inline JSON in their replies, so no separate output directories are specified. ORCH merges the results (plan line 526: "recording both identities in `extracted_by[]`"), but no rule says how to merge conflicting `value_exact` values from a shared source.

**Spec keys that look uncomputable.**

1. **`alias.map`** (ANCHOR_SPEC line 88) maps `station_index` to `"S_k"` identifiers from the reference evaluation. Q-007 (resolved) confirms the join exists, but the spec does not say whether `S_k` is a string literal, a numeric index or a derived key. The P1-anchors builders must inspect a case file to find out.

2. **`acct.campaigns.analysed` and `.superseded`** (ANCHOR_SPEC lines 83–84) are specified as JSON lists in `value_exact`, and the plan (line 518) refers to the "analysed and superseded campaign lists". `analysis_audit.md` line 35 names "analysed campaigns", but it is ambiguous whether it lists both kinds or only the analysed ones. Builders must infer this from the ANCHOR_SPEC phrasing.

3. **`disp.explor.<H>.max_abs.like_for_like`** (ANCHOR_SPEC line 65) is defined as `max_abs / (1 − n / 199403)`. `dispersion_survey.csv` rows 89–91 are at origin 199,403, and the plan (F17, line 1180) says no held-out row exists. The `n` in the denominator (10937, 21874, 43748) is each row's own n, not the origin 199,403. Builders must not confuse the two.

**Contradictions.**

1. **Coverage-mode fixture.** P1-check-author (line 151) requires `check_claims.py --coverage` to list at least one row mentioning each of three sources: `WRITING_EXECUTION_PLAN_REVIEWED_20260914.md`, `CAMPAIGN_PREDECLARATION.md` and `PLAN_REVIEW_LEDGER_20260914.md`. P1-register (line 71), however, reads only rows that "relate the extension to the companion", per WRITING_EXECUTION_PLAN §6 Step 4. The coverage test does not enforce that scope, so a register row citing only the companion would pass coverage while violating P1-register's stated input scope. This is not a contradiction if "relates the extension" means "cites the reviewed plan or predeclarations", but the brief does not say.

2. **Argument-option completeness.** P1-check-author line 160 (`--argument` mode) checks that every contribution has at least one `claim_ids` entry. WRITING_ORCHESTRATION_PLAN Appendix D (line 1266) specifies `contributions[]` as `{text, claim_ids[]}` without stating a cardinality. The check enforces `len(claim_ids) >= 1`; the schema should state it explicitly.

**Argument-option format completeness.**

The Appendix D schema for `argument_option_X.json` (plan lines 1259–1268) specifies:
- `option` (letter)
- `research_question`
- `spine` (the one-sentence spine)
- `contributions[]` (each `{text, claim_ids[]}`)
- `displays[]` (the displays the option needs)
- `objections[]` (the strongest objections)

P1-check-author `--argument` mode (lines 161–169) checks that:
- the spine is non-empty;
- the contributions list is non-empty;
- every contribution has at least one claim_id, and every id exists in claims.json;
- no contribution's claim ids are all of type `interpretation` or `recommendation`.

The format is complete for the specified checks. Two minor gaps: the format of `objections[]` is not constrained, so it is undefined whether objections are plain strings or structured; and the `research_question` field is never validated.

All items above carry evidence from the paths specified in the brief.
