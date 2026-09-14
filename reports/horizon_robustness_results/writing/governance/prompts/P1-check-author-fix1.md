```
You are working on the undated CSLAP robustness extension, an agent-written journal article that
extends the submitted companion IJSSOL_CSLAP_v1.tex. Before anything else:
1. Your task, inputs, allowed output paths and return format are in the brief below. Write only to
   the allowed output paths; if your brief says "return in reply", write nothing. Reviewers and
   voters write nothing. If you have Bash, use it for read-only inspection only.
2. These overrides beat the defaults in your role file:
   - Ignore thesis paths, MSLAP/Savoye objectives and IJPR/journal specifications ([H] floats unless
     the style canon keeps them, word or display ceilings, six themes, fixed section sequence,
     boilerplates). Never write a "generative AI was not used" or "language refinement only"
     declaration, and never copy any AI declaration.
   - Keep every durable style rule: reviewer_first_skill, banned vocabulary and transitions, zero em
     dashes in prose, no metaphorical jargon, table narrative autonomy, prose classes A-E, the
     no-ai-slop academic adapter (Detect only), writing/governance/STYLE_CANON.md and its technical
     term whitelist once they exist.
   - Scope-once rule: the experimental unit and what the experiment cannot identify are stated once
     at the head of Results and once in Limitations; the abstract and conclusion each carry one
     qualifier clause; do not repeat hedges in every sentence.
   - Never call the held-out result "replicated" in the paper's own voice; the predeclared label
     "Replication endpoint" may be quoted once, immediately followed by the qualifier that it tests
     the same policy at a later origin of the same stream, whose history contains the exploratory
     origin's data.
   - Do not build or query a graphify graph. Write in plain English, not caveman.
   - Use the companion's notation (P, O, S, zeta_s, L_p, x_ps, z_os, Phi_s); companion C_s is line
     capacity; slots are zeta_s.
   - Three optimizer seeds at one origin describe optimizer variability, not futures. Do not compute,
     display or demand significance tests, confidence intervals or extra seeds.
   - scientific-reviewer: STATUS: ACCEPTED means scientifically sound, not submission-ready.
     REVISE_METHOD, REVISE_CODE and MORE_TESTING mean "weaken or scope out the claim"; never route to
     coding, experiments or solvers.
   - plan-reviewer: route consensus and escalation to the orchestrator, not to the user.
   - academic-writer: narrative options are methodological, operational/managerial and
     comparative-evidence; never "competitive superiority" or Wilcoxon tests.
3. Never: launch a solver or any test; run make_analysis.py, a survey script or a data loader; read
   retained orders at index >= 265,025; edit protected files (root-level .tex/.bib, companion
   supplement, manuscript_checks, predeclarations, campaigns, reports/horizon_robustness_results
   tables or figures, code, tests, handoff and review documents, the orchestration plan and its
   review ledger); send non-public content to external services; submit or contact any journal.
4. Every factual statement carries a locator: path:line, table and row, or URL with quoted text.
   Every number comes from anchors.json, document_values.json or numbers.json, or is computed by you
   with the computation shown. Manuscript numbers are macros. Unlocated statements are discarded.
5. Claims must match writing/evidence/claims.json, including required qualifiers and forbidden
   wordings.
6. If you meet an ambiguity, do not guess: return a Q-card (question, why it matters, decisive test,
   options, conservative default, class E/J/H).
7. Governing documents, in reports/horizon_robustness_results/: WRITING_ORCHESTRATION_PLAN_20260914.md
   (execution, user decisions U1-U4, superseded items in its section 0),
   WRITING_EXECUTION_PLAN_REVIEWED_20260914.md (scientific scope and forbidden claims), and
   writing/governance/PLAN_ADDENDA.md.
```

User decisions made after the go are recorded in `reports/horizon_robustness_results/writing/governance/user_decisions.md`:
- U5: IJSSOL v1 is the only baseline.
- U6: its supplement is part of that baseline.
- U7: votes are weighted, haiku is excluded, and fable is retried only after a 12-hour window.
- U8: no git commands of any kind, and a fix-round budget for tooling gates.

# Brief: P1 check-author fix round 1 (BCL round 2) for `compare_anchors.py`, `check_claims.py` and the carry-over

**Identity:** `general-purpose`/sonnet, role `check_author`. You wrote these scripts in seq 25. `code-reviewer`/opus reviewed them in seq 26 and will re-review this round.

**Paths:**
- Repository root: `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`
- `W` = `reports/horizon_robustness_results/writing`
- `L` = `.unlazy/horizon-writing`
- Python: `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe`. Use `-B` for every run.

## Git ban (user decision U8, absolute)

- You run no git command of any kind.
- Nothing you write may execute git.
- The only git call allowed anywhere is the existing read-only status call inside `check_governance.py`. Do not add another.

## Allowed outputs (as in seq 25)

- `W/tools/compare_anchors.py`
- `W/tools/check_claims.py`
- `W/tools/check_governance.py`
- `L/fixtures/compare_anchors/**`
- `L/fixtures/check_claims/**`
- `L/fixtures/check_governance/**`

Do not touch `W/tools/recompute_anchors.py`. It is a generator that ORCH saved, not one of your scripts.

## Read

1. The review: `W/governance/results/P1-026-code-review-checks.md` (seq 26, VERDICT: REVISE).
2. `W/governance/findings.jsonl`, taking the latest line of each of F-042, F-045 to F-047, and F-048 to F-058.
3. The cards:
   - `W/governance/questions/Q-012.md`
   - `W/governance/questions/Q-013.md`
   - `W/governance/questions/Q-015.md`
   - `W/governance/questions/Q-016.md`, which sets the token rules. Implement option (a).
4. The specs as they stand now, both edited under Q-012, Q-013 and Q-015:
   - `W/evidence/ANCHOR_SPEC.md`
   - `W/evidence/DOCUMENT_VALUES_SPEC.md`
5. Your seq 25 brief, `W/governance/prompts/P1-check-author.md`. Everything in it still applies unless this brief changes it.

## Required changes

Add a short comment naming the finding at each change.

### `compare_anchors.py`

1. **F-045.** A `for` clause accepts plain values or backticked values. Backtick fragments inside the `for` clause are values, not keys.
2. **F-046.** Each of these is a problem, printed as `SPEC ERROR <detail>`, and the check fails:
   - any table row in sections A to D, or in the document-value Keys table, that yields zero keys;
   - a missing section;
   - a placeholder with no domain;
   - a restriction token that is not in the row's pattern;
   - a Section E row that does not parse.
3. **F-055, spec cells.** An escaped `\|` inside a spec table cell does not split the cell.
4. **F-048.** A Section E card counts as closed only when its `Resolution:` line has non-empty text on the same line (`^Resolution:[ \t]*\S`). The anchor key must appear as a whole key, not a prefix of a longer key, in both the card and `interpretation_errata.md`.
5. **F-049.** `"UNAVAILABLE"` is allowed only for keys whose spec definition says *optional* or names `"UNAVAILABLE"`. This applies in anchors mode and in `--documents`.
6. **F-050.** Source paths are checked as follows:
   - A document `source.path` must be one of DOCUMENT_VALUES_SPEC's allowed sources, given as a relative path. Absolute paths, `..` segments and any `IJPR_CSLAP_*` or `C&OR_CSLAP.tex` file are problems.
   - An anchors `sources[].path` must match ANCHOR_SPEC's allowed inputs. A `sources` entry may be an object or a list of objects, and both builders use both shapes. Flatten one level before checking.
7. **F-051.** Wherever `value_exact` parses as an integer, a rational `p/q` or a decimal, `value_float` must agree with it within a relative 1e-12. Otherwise report `MISMATCH <key>: value_float disagrees with value_exact`.
8. **F-055, unknown keys.** Keys in `anchors.json` or `anchors_B.json` that the spec does not require, and that lack the `extra.` prefix, are problems.
9. **F-047.** `prov.stream_end` must carry `semantics` in A, B and the merged file, with the same value in all three. `prov.tail_unused` must equal exactly the formula for that semantics.
10. **Q-015.** In text comparison, a LaTeX `~` counts as whitespace. A and B may cite different source lines when their values agree and each quote is valid.

### `check_claims.py`

11. **F-052.** Document values carry no `value_float`. Normalise their `value_exact` the same way `compare_anchors.py` does, then compare as a `Decimal` at the token's shown decimals. `"284,862"` must trace.
12. **F-053 and Q-016 (a).** Implement the token rules of Q-016 option (a) exactly:
    - prefixes need a word boundary;
    - hyphen and slash exemptions apply only after a letter;
    - both ends of a range count, and so do negatives;
    - both sides of `digits/digits` count;
    - small integers must trace when the claim cites any count or bool value.
13. **F-055, units.** A token followed by `%` or `\%` traces only to a value with unit `pct`. A token followed by `pp` traces only to a value with unit `pp`.
14. **F-055, year exemption.** Tighten it to a citation pattern: a parenthesised year, or `Name (et al.) year`.
15. **F-055, `extra.` keys.** An `anchor_keys[]` entry that starts with `extra.` cannot trace a number.
16. **F-054, `--schema`.**
    - Empty `[]` or `{}` files fail.
    - Every anchors entry requires `value_exact`, `value_float` (number or null), `unit`, `display_rounding` (integer or null), `sources` (non-empty; objects `{path, sha256, selector}`, or lists of such objects) and `computation`.
    - Every document-value entry requires `value_exact`, `unit` and `source` `{path, line, sha256, quoted_text}`.
    - Each merged `document_values.json` entry requires `extracted_by`, holding two identities of different families.
    - The merged-only `prov.tail_unused` requires `value_exact`, `unit` and `computation`, and no `source`.
    - The requirements map and the claims keep the seq 25 rules.

### Carry-over

17. **F-042.** `run_all.py` compares the full content of `W/tools/__pycache__` before and after the suite: path, size, `mtime_ns` and `sha256`. Any new or changed file fails.
18. **F-057.** Add a proof for the single-quoted command-string pattern. Flag a bare `"git"` or `'git'` element in a list literal.
19. **F-040 suggestion.** In `waiver_output_file_outside`, give `stub.md` the exact waived line and a matching hash, so the location check is the only failure.

## Fixtures

Each fixture has a `meta*.json` / `expected*.txt` pair. `run_all.py` covers them all and reports the new count.

Write the fixture specs in the real spec syntax, including:
- `<ARM>` rows with `for` clauses, one with plain values and one with backticked values;
- `for H in` rows;
- `.suffix` continuation fragments;
- slash rows in Section E;
- an escaped `\|` in a definition cell.

Add at least these fixtures:

| Fixture | Case | Expected |
|---|---|---|
| `documents_pass` | clean `--documents` run | pass |
| `section_e_waiver_closed` | closed card plus errata entry | pass |
| `section_e_waiver_empty_resolution` | empty Resolution line | fail |
| `section_e_waiver_superstring_key` | card names a longer key | fail |
| `unavailable_optional_ok` | UNAVAILABLE on an optional key | pass |
| `unavailable_required` | UNAVAILABLE on a required key | fail |
| `semantics_mismatch` | semantics differ across files | fail |
| `tail_formula_mismatch` | tail value off by one | fail |
| `source_path_disallowed` | an `IJPR_CSLAP_v4.tex` source name; the file need not exist and none is read | fail |
| `value_float_inconsistent` | float disagrees with exact | fail |
| `schema_empty` | empty file | fail |
| `spec_zero_key_row` | a row that yields no keys | fail, `SPEC ERROR` |
| `unknown_anchor_key` | a key outside the spec | fail |
| `claims_prefix_boundary` | "mean = 3.231630" with a wrong value | fail |
| `claims_range_end` | wrong upper end of a range | fail |
| `claims_ratio_denominator` | wrong k/3 denominator | fail |
| `claims_small_count` | a false "3/3" | fail |
| `claims_unit_pp_vs_pct` | a pp value written as % | fail |
| `claims_extra_key` | a number traced only via an `extra.` key | fail |
| `claims_document_decimal_pass` | a decimal document value | pass |

## Runs (only these)

- `L/fixtures/check_governance/run_all.py`
- your scripts against your own fixtures
- on the real root, read-only:
  - `check_governance.py --allow-pending`
  - `check_governance.py --probe`

Never run `compare_anchors.py` or `check_claims.py` against the real root. Never run git, repository tests, solvers or data loaders.

## Return in reply (at most 700 words)

- Files changed.
- For changes 1 to 19: `file:line`.
- The fixtures you added, and the `run_all.py` result line.
- The real-root outputs, verbatim.
- A git statement.
- Q-cards.
