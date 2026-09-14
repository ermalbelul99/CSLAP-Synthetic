## Summary

**Files changed** (all within allowed outputs):
- `reports/horizon_robustness_results/writing/tools/compare_anchors.py`
- `reports/horizon_robustness_results/writing/tools/check_claims.py`
- `reports/horizon_robustness_results/writing/tools/check_governance.py`
- `.unlazy/horizon-writing/fixtures/compare_anchors/**` (12 pre-existing fixtures updated with `sources`/spec fixes to avoid regression from the F-061/F-060 behavior changes; `section_e_waiver_superstring_key/.../Q-102.md` edited per F-066; 5 new fixtures added)
- `.unlazy/horizon-writing/fixtures/check_claims/**` (3 pre-existing `--schema` fixtures given `independent/anchors_B.json` + `independent/document_values_{A,B}.json`; 5 new fixtures added)
- `.unlazy/horizon-writing/fixtures/check_governance/**` (1 new fixture added; `run_all.py` untouched, auto-discovers)

**Changes 1–8, file:line:**
1. F-060 — `compare_anchors.py:574-601` (`parse_document_value_keys` now takes `spec_errors`, reports a bad row/placeholder as `SPEC ERROR`), call site `compare_anchors.py:736-749` (`cmd_documents` fails on `spec_errors` before touching any JSON).
2. F-061 — anchors-mode sources: `compare_anchors.py:524-538` (non-empty flattened sources required per non-UNAVAILABLE entry; each source needs path/sha256/selector). `--schema`: `check_claims.py:560-576` (new `DOCUMENT_VALUE_ENTRY_SCHEMA`/`DOCUMENT_VALUES_INDEPENDENT_FILE_SCHEMA`), `check_claims.py:635-655` (`cmd_schema` validates `anchors_B.json`, `document_values_A.json`, `document_values_B.json`).
3. F-062 — `compare_anchors.py:258-270` (`expand_pattern`: restriction-token check now runs before the "no placeholders" early return).
4. F-063 — `compare_anchors.py:796-800` (families set drops falsy `family`), `check_claims.py:588-596` (`document_values_family_errors`, same fix).
5. F-055 year remainder — `check_claims.py:52-58` (new `CITATION_PAREN_RE`), `check_claims.py:156-173` (`is_exempt_year` rewritten: exempt only `(YEAR)` whole-content or a citation list ending `, YEAR)`; both require the year immediately followed by `)`).
6. F-064 — `check_claims.py:229-238` (new `quantize_half_up`, `ROUND_HALF_UP`), `check_claims.py:240-267` (`value_matches_token` quantizes both `Decimal(repr(value_float))` and the token half-up).
7. F-065 — `check_claims.py:218-236` (`token_unit_hint` gains `RANGE_UPPER_UNIT_RE` fallback so a range's trailing unit also hints the lower end).
8. F-058 — `check_governance.py:594-611` (`check_weighted_votes`: non-integer-round check now runs first over every ballot in `data.get("ballots")`, before either early return), `check_governance.py:648-653` (`valid_ballots`/`usable_ballots` reuse that `bad_round_seqs`).

**Fixtures** — 12 new (documents_spec_bad_row, anchors_missing_sources, anchors_source_disallowed, spec_restriction_no_placeholder, extracted_by_null_family, schema_anchors_B_bad, schema_empty_object, claims_year_in_rows, claims_half_up_pass, claims_range_unit_lower, claims_separated_integer_pass, ballot_round_null_early), each verified against its own script before the expected.txt was written. `run_all.py` result:

```
FIXTURES OK (106)
```

(94 pre-existing + 12 new; zero regressions.)

**Real-root outputs (verbatim):**

`check_governance.py --allow-pending`:
```
IN FLIGHT 39
IN FLIGHT 40
VIOLATION (c): finding F-067 verification.by seq=38 has dispatch-log role 'builder', expected one of ['confirmer']
VIOLATION (h): reports/horizon_robustness_results/writing/tools/check_claims.py exists on disk but is not registered in check_scripts.json
VIOLATION (h): reports/horizon_robustness_results/writing/tools/compare_anchors.py exists on disk but is not registered in check_scripts.json
GOVERNANCE VIOLATIONS (3)
```
(exit 1 — pre-existing state: in-flight dispatches, an unrelated finding, and both tool scripts' non-registration in `check_scripts.json`; none of this is caused by this round's edits.)

`check_governance.py --probe`:
```
family fable: retry after 2026-09-14T19:27:48Z
family haiku: excluded
family opus: available
family sonnet: available
MODEL FAMILIES AVAILABLE (2: opus, sonnet)
```
(exit 0.)

**Git statement:** No git command of any kind was run. Bash was used only for read-only inspection (`ls`/`find`/`cat`), Python `-B -c "ast.parse(...)"` syntax checks, and running the checker scripts/`run_all.py` per the allowed runs list — nothing written by any of it executes git.

**Q-cards:** none.
