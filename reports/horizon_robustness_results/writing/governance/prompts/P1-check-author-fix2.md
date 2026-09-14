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

Do not read anything under `C:\Users\ebelul\AppData\Local\Temp\2\claude\` (the orchestrator's session scratchpad and task files). Run Python with `-B`. Run no git command.

# Brief: P1 check-author targeted fix round 2 (plan H8 targeted round) for `compare_anchors.py`, `check_claims.py` and `check_governance.py`

**Identity:** `general-purpose`/sonnet, role `check_author`.
- You wrote these scripts in seq 25 and seq 31.
- `code-reviewer`/opus reviewed them in seq 26 and seq 32, and will re-review this round narrowly.
- This is the plan's single targeted fix round for the P1 tooling gates. Keep the changes narrow.

**Paths:**
- Repository root: `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`.
- `W` = `reports/horizon_robustness_results/writing`; `L` = `.unlazy/horizon-writing`.
- Python: `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe -B`.

## Git ban (U8, absolute)

- Run no git command.
- Write nothing that executes git.

## Allowed outputs

- `W/tools/compare_anchors.py`
- `W/tools/check_claims.py`
- `W/tools/check_governance.py`
- `L/fixtures/compare_anchors/**`
- `L/fixtures/check_claims/**`
- `L/fixtures/check_governance/**`

Do not touch `W/tools/recompute_anchors.py`, `W/evidence/**` or anything else.

## Read

1. `W/governance/results/P1-032-code-rereview1.md`, the seq 32 review (VERDICT: REVISE).
2. `W/governance/findings.jsonl`, the latest line for each of F-046, F-050, F-055, F-058 and F-060 to F-066.
3. `W/governance/prompts/P1-check-author.md` and `W/governance/prompts/P1-check-author-fix1.md`. Everything in them still applies unless this brief changes it.
4. `W/governance/questions/Q-015.md` and `W/governance/questions/Q-016.md`.

## Required changes

Add a short comment naming the finding at each change.

1. **F-060 (F-046 remainder), `compare_anchors.py`.** In the DOCUMENT_VALUES_SPEC Keys table, any of the following prints `SPEC ERROR <detail>` and fails the check, as in sections A to D:
   - a row whose key cell yields no backtick key;
   - a row whose key pattern carries a placeholder.
2. **F-061 (F-050 remainder).**
   - **Anchors mode:** every entry in `anchors.json` and `anchors_B.json` that is not UNAVAILABLE must have a non-empty flattened `sources` list. Each source needs `path`, `sha256` and `selector`. A missing or empty list is `MISMATCH <key> (A|B): no sources`.
   - **`check_claims.py --schema`:** also validate `W/evidence/independent/anchors_B.json` with the anchors entry schema. Validate `W/evidence/independent/document_values_A.json` and `document_values_B.json` with the document-value entry schema.
3. **F-062.** A `for` restriction on a row whose key pattern has no placeholder is a `SPEC ERROR`. Test the restriction token before the early return.
4. **F-063.** In both scripts, an `extracted_by` identity without a `family` is discarded before families are counted. Two distinct non-null families are required.
5. **F-055 (year remainder), `check_claims.py`.** A four-digit year is exempt only in these forms:
   - the whole parenthesised content is the year (`(2021)`);
   - the year closes a citation in parentheses (`(Smith, 2021)`, `(Smith et al., 2021)`, `(Smith and Jones, 2021)`);
   - the year follows a capitalised surname in narrative citation form (`Smith (2021)`, `Smith et al. (2021)`).

   `(2000 rows)` and `in 2000 blocks` must count as numbers.
6. **F-064.** Rounding for the trace uses `ROUND_HALF_UP`, for both the entry value and the token. For `value_float` entries, compare `Decimal(repr(value_float))` quantized half-up, not Python's `round`. `13.65` must trace to `13.7`.
7. **F-065.** In a range `a–b unit` or `a-b unit`, the unit restriction (`%`, `\%`, `pp`) applies to both ends.
8. **F-058, `check_governance.py`.** A ballot whose `round` is present but not an integer produces its violation in every case where it is currently skipped:
   - when the DR returns early because the weighted rule does not apply;
   - when the ballot itself is invalid.

   Nothing may crash.

## Fixtures (F-066 plus one per change)

Each fixture gets a `meta*.json`/`expected*.txt` pair. `run_all.py` covers all of them and reports the new count.

| Fixture | Expected |
|---|---|
| `compare_anchors/documents_spec_bad_row` | fail, `SPEC ERROR` |
| `compare_anchors/anchors_missing_sources` | fail |
| `compare_anchors/anchors_source_disallowed` | fail, anchors mode |
| `compare_anchors/spec_restriction_no_placeholder` | fail, `SPEC ERROR` |
| `compare_anchors/extracted_by_null_family` | fail |
| `check_claims/schema_anchors_B_bad` | fail under `--schema` |
| `check_claims/schema_empty_object` | fail under `--schema`; `{}` files |
| `check_claims/claims_year_in_rows` | fail; "(2000 rows)" untraced |
| `check_claims/claims_half_up_pass` | pass; 13.65 traces 13.7 |
| `check_claims/claims_range_unit_lower` | fail; lower end with the wrong unit |
| `check_claims/claims_separated_integer_pass` | pass; "284,862" traces |
| `check_governance/ballot_round_null_early` | fail with the non-integer round violation; no traceback |

Also make these two changes to existing fixtures:
- In `compare_anchors/section_e_waiver_superstring_key`, the card names only the longer key, so the card-side whole-key check is what fails.
- Give `spec_zero_key_row` a sibling fixture that reaches the restriction-token path.

## Runs (only these)

- `L/fixtures/check_governance/run_all.py`.
- Your scripts, run against your own fixtures.
- On the real root, read-only: `check_governance.py --allow-pending` and `check_governance.py --probe`.

Never run `compare_anchors.py` or `check_claims.py` against the real root. Never run git, repository tests, solvers or data loaders. Do not read anything under `C:\Users\ebelul\AppData\Local\Temp\2\claude\`.

## Return in reply (at most 600 words)

- The files changed.
- For each of changes 1 to 8: `file:line`.
- The fixture list and the `run_all.py` result line.
- The real-root outputs, verbatim.
- A statement on git use.
- Any Q-cards.
