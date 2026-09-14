## Report

**Files changed** (all within the six allowed output paths):
- `W/tools/compare_anchors.py` — rewritten
- `W/tools/check_claims.py` — rewritten
- `L/fixtures/check_governance/run_all.py` — F-042/F-057 fixes
- `L/fixtures/check_governance/waiver_output_file_outside/reports/.../results/stub.md` and `.../gates/TEST-G4.json` — F-040 suggestion
- `L/fixtures/compare_anchors/**` — `pass` and `documents_bad_quote` rebuilt (richer spec syntax; new required fields); 12 new fixture dirs
- `L/fixtures/check_claims/**` — `pass` and `schema_bad` fixed (schema-complete anchors/document_values); 8 new fixture dirs

`W/tools/recompute_anchors.py` and everything under `W/evidence/` were not touched.

**Changes 1–19** (`compare_anchors.py` = CA, `check_claims.py` = CC, `run_all.py` = RA):
1. F-045: CA:207 `find_for_clause_split`, CA:222 `extract_key_patterns`, CA:238 `local_restriction` — split on backtick-depth parity before scanning for keys.
2. F-046: CA:261 `expand_pattern`, CA:293 `required_keys_for_section`, CA:332 `parse_section_e` — zero-key rows, missing sections, unresolved placeholders, mismatched restriction tokens and unparseable Section E rows all emit `SPEC ERROR` and fail the check (CA:472–478 short-circuits before any file comparison).
3. F-055 (spec cells): CA:182 `split_table_row` protects `\|` before splitting.
4. F-048: CA:375 `whole_key_present`, CA:388 `section_e_waived` — `[ \t]*\S` same-line match; whole-key regex.
5. F-049: CA:307 (optional also covers "names UNAVAILABLE"), CA:510 (anchors mode), CA:742 (documents mode, previously ignored the flag entirely).
6. F-050: CA:123/143/156 (anchor `sources[]`, glob-matched, flattened one level), CA:598/625/781 (document `source.path`, checked *before* any filesystem read — CA:781 comment documents this ordering).
7. F-051: CA:440 `value_float_ok`, applied at CA:521.
8. F-055 (unknown keys): CA:531.
9. F-047: CA:671 `semantics_consistent`, CA:684 `check_tail_unused` (single matching formula only), called at CA:774.
10. Q-015: CA:641 `normalize_document_value` (`~` → whitespace); per-file source checks were already independent, so differing A/B lines already passed.
11. F-052: CC:236 `normalize_document_number`, CC:257 `value_matches_token` (Decimal compare).
12. F-053/Q-016(a): CC:176–214 `find_numeric_tokens`, CC:127 `_prefix_exempt`, CC:143 `is_exempt_small_int`.
13. F-055 (units): CC:219 `token_unit_hint`.
14. F-055 (year): CC:157 `is_exempt_year`, tightened `NAME_CITATION_RE`.
15. F-055 (extra. keys): CC:329.
16. F-054: CC:423 (`minItems`/`minProperties`), CC:453 `ANCHOR_ENTRY_SCHEMA`, CC:482 `MERGED_DOC_VALUE_ENTRY_SCHEMA`, CC:496 `TAIL_UNUSED_ENTRY_SCHEMA`, CC:526 `document_values_family_errors`.
17. F-042: RA:132 `_pycache_signature` (size/mtime_ns/sha256), wired at RA:188 (before) and RA:284 (after).
18. F-057: RA:82–83 (bare-last-element patterns), RA:118/125 (single-quoted command-string and bare-list-element proof sources), RA:260 (added to `proofs`).
19. F-040 suggestion: `stub.md` now holds `WAIVED LINE ONE`, `TEST-G4.json.output_sha256` matches it — location check remains the sole failure.

**Fixtures added** (20, all captured from real runs): `documents_pass`, `section_e_waiver_closed`, `section_e_waiver_empty_resolution`, `section_e_waiver_superstring_key`, `unavailable_optional_ok`, `unavailable_required`, `semantics_mismatch`, `tail_formula_mismatch`, `source_path_disallowed`, `value_float_inconsistent`, `spec_zero_key_row`, `unknown_anchor_key` (compare_anchors); `schema_empty`, `claims_prefix_boundary`, `claims_range_end`, `claims_ratio_denominator`, `claims_small_count`, `claims_unit_pp_vs_pct`, `claims_extra_key`, `claims_document_decimal_pass` (check_claims). `pass`/`documents_bad_quote`/`pass`(claims)/`schema_bad` were rebuilt in place, not renamed. `<ARM>` for-clauses (plain and backticked), `for H in`, `.suffix` continuation and an escaped `\|` all now live in the compare_anchors `pass` spec (reused by 7 sibling fixtures); a Section E slash row is exercised there and in the three waiver fixtures.

`run_all.py` result: **`FIXTURES OK (94)`** (33 Part A fixture invocations + 8 check_inputs + 46 check_governance + 5 procedural/no-git-scan/pycache checks; all four no-git-scan proofs fire, including the two new F-057 ones).

**Real-root outputs, verbatim:**

`--allow-pending`:
```
IN FLIGHT 31
VIOLATION (h): reports/horizon_robustness_results/writing/tools/check_claims.py exists on disk but is not registered in check_scripts.json
VIOLATION (h): reports/horizon_robustness_results/writing/tools/compare_anchors.py exists on disk but is not registered in check_scripts.json
GOVERNANCE VIOLATIONS (2)
```
(matches seq26's noted pre-existing unregistered-script lines; exit 1)

`--probe`:
```
family fable: retry after 2026-09-14T19:27:48Z
family haiku: excluded
family opus: available
family sonnet: available
MODEL FAMILIES AVAILABLE (2: opus, sonnet)
```
(exit 0)

**Git statement:** No git command of any kind was run. All inspection was read-only file access (Read/Grep/Bash `find`/`cat`); no bash invocation contained `git`.

**Q-cards:**

**Q-017 (class E).** DOCUMENT_VALUES_SPEC's "Allowed sources" bullet 2 lists one full path (`reports/.../CAMPAIGN_PREDECLARATION.md`) followed by three bare filenames (`DATA_PROVENANCE.md`, `analysis_audit.md`, `EXPERIMENT_REVIEW_HANDOFF.md`) with no restated directory. I implemented `parse_document_allowed_sources` (CA:598) so a bare fragment inherits the nearest preceding full-path fragment's directory within the same bullet — mirroring ANCHOR_SPEC's own `.suffix` continuation convention — so `source.path` values like `reports/horizon_robustness_results/DATA_PROVENANCE.md` pass. **Decisive test:** ORCH re-reads the real spec's intent (is the shared prefix implied, or must each fragment be self-contained?). **Options:** (a) inherit-prefix (implemented, conservative — accepts fewer paths than a literal-only reading would reject); (b) require each bullet fragment to be a complete path (would currently reject those three real filenames outright). **Conservative default:** (a), already implemented; flagging for confirmation since it affects real-root behavior once run.
