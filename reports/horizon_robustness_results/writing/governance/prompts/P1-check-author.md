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
- **U5.** IJSSOL v1 is the only baseline.
- **U6.** Its supplement is part of the baseline.
- **U7.** Votes are weighted, haiku is excluded, and fable is retried only after a 12-hour window.
- **U8.** No git commands of any kind; tooling gates have a fix-round budget.

# Brief: P1 check-author wave (plan P1 step 1; INV-11, INV-13) plus carry-over checker fixes

**Identity:** `general-purpose`/sonnet, role `check_author`.

**Paths:**
- Repository root: `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`
- `W` = `reports/horizon_robustness_results/writing`
- `L` = `.unlazy/horizon-writing`
- Python: `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe` (stdlib, jsonschema, pandas)

## Git ban (user decision U8, absolute)

- You run no git command of any kind: not `status`, `log`, `rev-parse`, `init`, `add`, `commit` or `config`.
- Nothing you write may execute git.
- The one git call that may exist anywhere is the existing read-only status call inside `check_governance.py`, and you must not add another.

## Read first

- The plan, P1 and Appendix D.
- `W/evidence/ANCHOR_SPEC.md`
- `W/evidence/DOCUMENT_VALUES_SPEC.md`
- `W/governance/GOVERNANCE_FORMATS.md`
- For Part B:
  - `W/governance/results/P0-024-code-rereview3-narrow.md` (defects N7 to N10);
  - the latest lines for F-040, F-042, F-043 and F-044 in `W/governance/findings.jsonl`.

## Allowed outputs

- **Part A:**
  - `W/tools/compare_anchors.py`
  - `W/tools/check_claims.py`
  - `L/fixtures/compare_anchors/**`
  - `L/fixtures/check_claims/**`
- **Part B:**
  - `W/tools/check_governance.py`
  - `L/fixtures/check_governance/**`

## Part A: the P1 evidence checkers

**Root argument.** Both scripts accept `--root DIR`, which defaults to the repository root. From `W/tools/` that root is `Path(__file__).resolve().parents[4]`. Confirm it by checking that `<root>/reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` exists, and do not use git for this.

**No empty passes.** A check never passes on zero items.

**No writes, no subprocesses.** The scripts write nothing and start no subprocess.

### `compare_anchors.py`

#### Default mode

Compares `W/evidence/anchors.json` (A) with `W/evidence/independent/anchors_B.json` (B).

1. **Required keys.** Both files must contain every key named in ANCHOR_SPEC sections A–D.
   - The `<ARM>`, `<SEED>`, `<H>`, `<DELTA>` and `<n>` patterns expand as the spec defines. `<n>` takes the values 10937, 21874 and 43748.
   - Keys under `extra.` are ignored.
   - A key missing from either file is a problem.
   - A key present with `"UNAVAILABLE"` is allowed only if the spec marks it *optional*. Both files must then say UNAVAILABLE.
2. **Value agreement.** For every key:
   - If both `value_exact` strings parse as integers or rationals `p/q`, they must be equal as `Fraction`s.
   - Otherwise, both `value_float` values must agree within a relative tolerance of 1e-12 (absolute 1e-15 when either value is 0).
   - Values that are JSON strings (lists and maps) must be equal after `json.loads` with keys sorted.
3. **Section E cross-check.** Round A's value to the number of decimals shown, and compare it with the displayed value.
   - A mismatch passes only if both of these hold:
     - a file `W/governance/questions/Q-*.md` mentions that anchor key and contains a line starting `Resolution:` with non-empty text;
     - `W/evidence/interpretation_errata.md` mentions the key.
   - Otherwise it is a problem.
4. **Problem lines.** Print each problem as `MISMATCH <key>: <detail>`.
5. **Result.** Print `ANCHORS CROSS-CHECK PASSED (<n> keys)` and exit 0, or print `ANCHORS CROSS-CHECK FAILED (<k>)` and exit 1.

#### `--documents` mode

Compares `W/evidence/independent/document_values_A.json` with `document_values_B.json`, and checks the merged `W/evidence/document_values.json`.

1. **Required keys.** Every key in DOCUMENT_VALUES_SPEC must appear in A, B and the merged file. The derived `prov.tail_unused` must appear in the merged file only.
2. **Value agreement.** `value_exact` in A and B must be equal after whitespace normalisation.
   - Numbers compare as numbers after removing thousands separators, `{,}`, `\,` and `%`.
   - Text values compare as exact strings.
   - The merged file's value must equal the agreed value.
   - The merged file's `extracted_by` must hold two identities of different families.
3. **Source checks.** For each file (A, B, merged) and each key that is not UNAVAILABLE:
   - `source.path` must exist;
   - `source.sha256` must match the file's current bytes;
   - `source.quoted_text` must be a substring of line `source.line` (1-based) of that file.
4. **Derived value.** `prov.tail_unused` must equal its recorded computation.
5. **Result.** Print `DOCUMENT VALUES CROSS-CHECK PASSED (<n> keys)` and exit 0, or print the problems and `DOCUMENT VALUES CROSS-CHECK FAILED (<k>)` and exit 1.

### `check_claims.py`

The claims schema follows plan Appendix D. `W/evidence/claims.json` is either a list of claim objects or `{"claims": [...]}`; support both.

#### Default mode: numeric trace

For each claim:

1. **Sources.** Every `sources[].path` exists, and every `sources[].sha256` matches the current file. If the path is pinned in `W/governance/source_manifest.json`, it must also equal the manifest hash.
2. **Keys.** Every `anchor_keys[]` exists in `W/evidence/anchors.json`, and every `document_value_keys[]` exists in `W/evidence/document_values.json`.
3. **Numeric tokens.** Scan `statement`, every `allowed_wording[]` and every `required_qualifiers[].text` for numeric tokens.
   - A token matches the regex `(?<![A-Za-z§#\-/])\d[\d,]*(?:\.\d+)?`.
   - These tokens are ignored:
     - integers from 0 to 10;
     - tokens immediately preceded by `§`, `Q-`, `C-`, `F`, `H`, `D`, `U`, `P`, `S`, `n = `, `line ` or `lines `;
     - four-digit years from 1900 to 2099 that sit inside parentheses or follow a citation name.
   - After removing thousands separators, every remaining token must equal the rounding, to the token's shown decimals, of `value_float` or of the integer `value_exact`, for at least one of the claim's anchor or document values.
   - Units: `pct` and `pp` values are compared in the unit as stored. A ratio `k/3` counts as two integers.
4. **Failure lines.** Print each failure as `UNTRACED <claim id>: <token>`.
5. **Result.** Print `CLAIMS TRACE PASSED (<n> claims, <m> tokens)` and exit 0, or print `CLAIMS TRACE FAILED (<k>)` and exit 1.

#### `--schema` mode

Validate with jsonschema: `claims.json` (Appendix D), `requirements_map.json`, `document_values.json` and `anchors.json`.

- Every claim needs a non-empty `id`, `type`, `endpoint_status` and `statement`.
- Every `required_qualifiers[]` item is `{text, discharge ∈ {sentence, scope_paragraph}}`.
- Every `forbidden_wording[]` item is a string, or `{text, conditional_on: {q_card, outcome}}`.

Print `CLAIMS SCHEMA PASSED` and exit 0, or print the errors and exit 1.

#### `--coverage` mode

- Every row of `W/evidence/requirements_map.json` has a `maps_to` value, and that value resolves:
  - either to an existing claim `id`;
  - or to `forbidden:<claim id>:<n>`, where `<n>` is a 0-based index into that claim's `forbidden_wording`.
- Row ids are unique, and there is at least one row.
- The file must also contain the rows from the plan's P1 step 4 sources. For each of these files, at least one row's `source` must mention it:
  - `WRITING_EXECUTION_PLAN_REVIEWED_20260914.md`
  - `CAMPAIGN_PREDECLARATION.md`
  - `PLAN_REVIEW_LEDGER_20260914.md`

Print `REQUIREMENTS COVERED (<n> rows)` and exit 0, or print the unresolved rows and exit 1.

#### `--argument` mode (used in P4)

1. Find the DR in `W/governance/decisions/` whose json block has `"q_card": "Q-ARGUMENT"`. Its `outcome` is an option letter.
2. Load `W/positioning/argument_option_<letter>.json`, whose schema is in plan Appendix D. These fields must be present and non-empty:
   - `option`;
   - `research_question`;
   - `spine`;
   - `contributions`, a list of `{text, claim_ids}` where `claim_ids` has length ≥ 1;
   - `displays`, a list of strings;
   - `objections`, a list of strings.
3. Check all of the following:
   - `spine` is non-empty;
   - `contributions` is non-empty;
   - every contribution has at least one `claim_ids` entry, and every id exists in `claims.json`;
   - no contribution's claim ids are all of type `interpretation` or `recommendation`.
4. Print `ARGUMENT TRACE PASSED` and exit 0, or print the problems and exit 1.

### Part A fixtures

Build miniature trees that mirror the real layout. Keep each fixture under 50 keys and 20 lines per file.

| Fixture | Contents | Expected exit |
|---|---|---|
| `compare_anchors/pass/` | | 0 |
| `compare_anchors/mismatch/` | one value perturbed by 1e-6 | 1 |
| `compare_anchors/missing_key/` | a key absent from one file | 1 |
| `compare_anchors/section_e_unresolved/` | a displayed-value mismatch with no Q-card | 1 |
| `compare_anchors/documents_bad_quote/` | quoted text not on the stated line | 1 under `--documents` |
| `check_claims/pass/` | | 0 in every mode |
| `check_claims/untraced/` | | 1 in the default mode |
| `check_claims/schema_bad/` | | 1 under `--schema` |
| `check_claims/coverage_bad/` | | 1 under `--coverage` |
| `check_claims/argument_interpretation_only/` | | 1 under `--argument` |

**Fixture format.** Each fixture directory carries `meta.json` (`{"tool", "args", "exit_code"}`) and a byte-exact `expected.txt`, the same format the governance fixtures use.
- A fixture exercised in several modes carries one pair per mode: `meta_<mode>.json` and `expected_<mode>.txt`.
- The tools are `compare_anchors` and `check_claims`.

## Part B: carry-over fixes to `check_governance.py` (findings F-040, F-042, F-043, F-044; U8 and A-005)

Add a short comment naming the finding at each change.

1. **F-040 (N7).** `waiver_valid()` applies the same `gate_output_file_ok` location check to the record's `output_file` before reading it. Failing the check is a violation. Add a fixture `waiver_output_file_outside` that must fail.
2. **F-042 (N8).** Every runner that loads a checker in-process sets `sys.dont_write_bytecode = True` before `exec_module`. Nothing the fixture suite runs may leave a `__pycache__` under `W/`.
   - Add a check to `run_all.py`, reported as its own `ok:` line: record whether `W/tools/__pycache__` exists before the suite, and fail if the suite created any new file there.
   - Do not delete the existing `.pyc`; ORCH removes it.
3. **F-043 (N9).** Change the no-git scan in `run_all.py` in three ways:
   - build its patterns by string concatenation, so the scanner's own source no longer contains them, and remove the self-exemption;
   - add patterns for git issued as a command string, where a string literal starts with `git` followed by a space, whether single- or double-quoted, as in `os.system(...)` or `shell=True`;
   - extend the proof so that a planted file containing only a command-string git call is flagged. The planted file is never executed.
4. **F-044 (N10).** A ballot whose `round` is present but not an integer, including null and booleans, produces `VIOLATION (d): <DR file> ballot seq=<seq> has a non-integer round`. That ballot is excluded from final-round selection and from the tally, and nothing crashes. Add a fixture `ballot_round_null`: a single-question DR subject to U7 with one null round among integer rounds. It must fail with exactly that violation and no traceback.

## One fixture suite

Extend `L/fixtures/check_governance/run_all.py` so that it also discovers every `meta*.json` under `L/fixtures/compare_anchors/*/` and `L/fixtures/check_claims/*/`.
- Invocation convention: `python <tool> --root <fixture> <args>`.
- Compare the output byte-exact with the matching `expected*.txt`.
- The single command `run_all.py` must cover every Part A and Part B fixture.

## Runs (only these)

- **Fixture suite:** `L/fixtures/check_governance/run_all.py`.
- **Your own scripts:** only against your own fixtures.
- **Real root, read-only:**
  - `check_governance.py --allow-pending`;
  - `check_governance.py --phase P0 --allow-pending`;
  - `check_governance.py --probe`.
- **Never** run `compare_anchors.py` or `check_claims.py` against the real root; the real evidence files do not exist yet.
- **Never** run `--snapshot` or `--compare` on the real root, and never run any git command, repository test, solver, survey script or data loader.

## Return in reply (at most 700 words)

- **Files written or changed.**
- **CLI usage and tokens:** the exact usage and output tokens of `compare_anchors.py` and `check_claims.py`.
- **Part A fixtures:** the fixture table with the exit codes you observed.
- **Part B changes:** `file:line` for changes 1 to 4, and the fixtures you added.
- **Fixture suite:** the `run_all.py` result line, and the `ok:` lines for the no-git scan and the bytecode check.
- **Real-root output, verbatim:**
  - `--allow-pending`;
  - `--phase P0 --allow-pending`;
  - `--probe`.
- **Git statement:** confirm that you ran no git command.
- **Ambiguities,** as Q-cards.
