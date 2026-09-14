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

# Brief: P1 code re-review 1 of the evidence checkers (fix confirmation after fix round 1)


**Identity:** `code-reviewer`/opus, role `code_review`.
- You reviewed these scripts in seq 26, with VERDICT: REVISE.
- The author is `general-purpose`/sonnet: seq 25 and the fix-round dispatch named in its report.

**Read-only, static.** Return everything in reply. ORCH runs the fixtures and records their outputs.

**Root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. `W` = `reports/horizon_robustness_results/writing`; `L` = `.unlazy/horizon-writing`.

## Read

1. Your seq 26 review: `W/governance/results/P1-026-code-review-checks.md`.
2. `W/governance/findings.jsonl`, the latest line for each of F-042, F-045 to F-058.
3. The cards, all now resolved:
   - `W/governance/questions/Q-012.md`
   - `W/governance/questions/Q-013.md`
   - `W/governance/questions/Q-015.md`
   - `W/governance/questions/Q-016.md`, option (a), pending its non-opus confirmation, which runs in this same wave.
4. The specs as they stand: `W/evidence/ANCHOR_SPEC.md` and `W/evidence/DOCUMENT_VALUES_SPEC.md`.
5. The fix-round brief `W/governance/prompts/P1-check-author-fix1.md` and its report, `W/governance/results/P1-*-check-author-fix1.md`.
6. The changed code:
   - `W/tools/compare_anchors.py`
   - `W/tools/check_claims.py`
   - `W/tools/check_governance.py`
   - `L/fixtures/check_governance/run_all.py`
   - `L/fixtures/compare_anchors/**`, `L/fixtures/check_claims/**` and the changed `check_governance` fixtures.
7. ORCH's recorded runs: `L/gate_outputs/p1fix1_*.txt` and the summary json.

## Answer

1. For each of changes 1 to 19 in the fix-round brief, and each of F-042 and F-045 to F-058, give FIXED or NOT FIXED with `file:line`. F-055 is a bundle, so answer item by item. Its swapped-attribution item is disclosed and not fixed.
2. Q-016 (a): are the token rules implemented exactly? Test these example sentences against the code:
   - "mean = 3.231630"
   - "3.23-3.35"
   - "3/3 seeds"
   - "Q-008"
   - "§5"
   - "(2021)"
   - "13.0–16.0 %"
   - "0.069–0.179 pp"
3. Spec expansion: does the parser now expand the real ANCHOR_SPEC to A 147, B 20, C 27 and D 9 keys, and the real DOCUMENT_VALUES_SPEC to 33 keys? Is there any `SPEC ERROR` on the real specs?

   Also check Q-017 (`W/governance/questions/Q-017.md`). ORCH rewrote the "Allowed sources" list of DOCUMENT_VALUES_SPEC with one full path per bullet. Does `parse_document_allowed_sources` now return exactly these seven paths?
   - `IJSSOL_CSLAP_v1.tex`
   - `IJSSOL_CSLAP_v1_supplementary.tex`
   - the four `reports/horizon_robustness_results/*.md` files
   - `WRITING_EXECUTION_PLAN_REVIEWED_20260914.md`

   ORCH's real-root diagnostic runs are `L/gate_outputs/p1fix1_diag_compare_*.txt`. They are not gates, because `anchors_B.json` and the merged `document_values.json` do not exist yet.
4. Fixtures: does each new fixture pass or fail for exactly its stated reason? Are the fixture specs written in the real spec syntax?
5. Does any check still pass vacuously?
6. U8: are git calls still limited to the read-only status call in `check_governance.py`?
7. Is there any regression in the `check_governance.py` rules confirmed in seq 20, 24 and 26?

A `VERDICT: PASS` from you allows ORCH to register the two scripts and run P1:G1 to P1:G5.

## Return in reply (at most 800 words)

```
VERDICT: PASS | REVISE
## Fix confirmation (changes 1-19; F-042, F-045..F-058)
## Q-016 token rules (examples)
## Spec expansion and fixtures
## New defects (severity; file:line; claim; evidence; fix)
## Required changes (if REVISE)
```
