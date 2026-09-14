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

# Brief: P1 narrow code re-review 2 of the evidence checkers (fix confirmation after targeted fix round 2)

**Identity:** `code-reviewer`/opus, role `code_review`.
- You reviewed these scripts in seq 26 and seq 32.
- The author is `general-purpose`/sonnet: seq 25, seq 31, and the fix-round-2 dispatch named in its report.

**Read-only and static.** Return everything in your reply. ORCH runs the fixtures and records their outputs.

**Scope:** narrow. Review only what targeted fix round 2 changed, and check it for regressions. A `VERDICT: PASS` from you lets ORCH register `compare_anchors.py` and `check_claims.py` and record P1:G1 and P1:G2.

**Root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. `W` = `reports/horizon_robustness_results/writing`; `L` = `.unlazy/horizon-writing`.

## Read

1. Your seq 32 review: `W/governance/results/P1-032-code-rereview1.md`.
2. `W/governance/findings.jsonl`: the latest line for each of F-046, F-050, F-055, F-058 and F-060 to F-066.
3. The fix-round-2 brief `W/governance/prompts/P1-check-author-fix2.md` and its report `W/governance/results/P1-*-check-author-fix2.md`.
4. The changed code: `W/tools/compare_anchors.py`, `W/tools/check_claims.py`, `W/tools/check_governance.py` and `L/fixtures/check_governance/run_all.py`.
5. The new and changed fixtures under `L/fixtures/compare_anchors/`, `L/fixtures/check_claims/` and `L/fixtures/check_governance/`.
6. ORCH's recorded runs: `L/gate_outputs/p1fix2_*.txt` and the summary json. These include real-root diagnostic runs of `compare_anchors.py`.
   - `p1fix2_diag_compare_documents.txt` fails on `comp.supp.workload.definition`. That was an evidence gap, not a checker defect: ORCH had merged an agreed re-extraction without installing it into the independent files (finding F-068). After the install, `L/gate_outputs/p1_docvalues_install_documents.txt` passes on 34 keys.
   - Say whether the checker's behaviour on that failure was correct: right key, right message, non-zero exit.

## Answer

1. For each of changes 1 to 8 in the fix-round-2 brief, and for each finding F-046, F-050, F-055 (year item), F-058 and F-060 to F-066: FIXED or NOT FIXED, with `file:line`.
2. Check the year rule against these examples. Each must count, or be exempt, as the brief says:
   - "(2021)"
   - "(Smith et al., 2021)"
   - "Smith (2021)"
   - "(2000 rows)"
   - "in 2000 blocks"
   - "(Smith, 2021; Jones, 2019)": the author's rule requires the year to be followed immediately by `)`. Say whether 2021 here is exempt, and whether the resulting behaviour matches the brief's intent (citation years exempt, other four-digit numbers counted).
2a. **Changed pre-existing fixtures.** The author edited 12 existing `compare_anchors` fixtures (adding `sources` and spec fixes for F-060 and F-061), the F-066 card in `section_e_waiver_superstring_key`, and 3 existing `check_claims` `--schema` fixtures (adding `independent/` files). Changing a fixture to fit new behaviour can hide a regression. For each changed fixture, confirm that the edit only adds what F-060 or F-061 now require, and that it still fails or passes for its original reason. ORCH's list of changed fixture files is in `L/gate_outputs/p1fix2_changed_files.txt`. Two fixtures matter most, because they are the negative controls of the gates your PASS unlocks:
   - `compare_anchors/mismatch` (P1:G1) was changed. Confirm that it still fails because of the value mismatch, and not only because of the new missing-sources rule.
   - `compare_anchors/documents_bad_quote` (P1:G2) is not in the list. Confirm that it still fails for its original reason under the changed `--documents` path.
3. Check rounding and range units:
   - Does "13.65" trace to "13.7"?
   - Is "0.069–0.179 pp" unit-restricted at both ends?
4. Real specs: do they still expand to A 147, B 20, C 27 and D 10 keys (204 in all; D grew from 9 when Q-005 split the incumbent slack key into `.history` and `.hist_act`), and to 33 document keys, with no `SPEC ERROR`?
5. For each new fixture: does it fail or pass for exactly its stated reason?
6. Is any check still vacuous? Is there any regression in rules confirmed in seq 26 or seq 32? Does U8 still hold?

## Return in reply (at most 700 words)

```
VERDICT: PASS | REVISE
## Fix confirmation
## Examples (year, rounding, range units)
## Spec expansion, fixtures, regressions, U8
## New defects (severity; file:line; claim; evidence; fix)
## Required changes (if REVISE)
```
