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

User decisions made after the go are recorded in `reports/horizon_robustness_results/writing/governance/user_decisions.md`. They are U5, U6, U7 and **U8**. U8 forbids git writes of any kind.

# Brief: P0 narrow code re-review 3 (fix confirmation for F-036 to F-041)

**Identity:** `code-reviewer`/opus, role `code_review`. You raised N1 to N6 in seq 20; they are recorded as F-036 to F-041. The author is `general-purpose`/sonnet, in seq 23.

**Read-only and static.** Your tools are Read, Grep and Glob; return your review in reply. ORCH ran the fixtures and the real-root checks, and the outputs it recorded are listed below.

**Scope.** This review is narrow, as you asked in seq 20. Review only what fix round 3 changed. A `VERDICT: PASS` from you is the evidence P0:G4 requires under DR-001 amendment R.

**Root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. `W` = `reports/horizon_robustness_results/writing`; `L` = `.unlazy/horizon-writing`.

## Read

1. Your seq 20 review: `W/governance/results/P0-020-code-rereview2-checks.md`.
2. `W/governance/findings.jsonl`: the latest line for each of F-036 to F-041.
3. `W/governance/user_decisions.md`, section U8; `W/governance/PLAN_ADDENDA.md` A-005 and A-006.
4. The fix-round-3 brief `W/governance/prompts/P0-fix-round3-check-author.md` and report `W/governance/results/P0-023-fix-round3-check-author.md`.
5. The changed code:
   - `L/fixtures/check_governance/compare_tracked_outside_edited_twice/**`;
   - `L/fixtures/check_governance/run_all.py`;
   - the runners for `compare_match` and `snapshot_file_tampered`;
   - `check_weighted_votes()` and `load_gate_output_text()` (or its caller) in `W/tools/check_governance.py`;
   - the counts block in `W/tools/check_inputs.py`;
   - the new fixtures named in the report.
6. ORCH's recorded outputs: `L/gate_outputs/fixround3_*.txt` and `fixround3_summary.json`.

## Answer

1. For each of F-036 to F-041, give FIXED or NOT FIXED, with the `file:line` of the fix or the evidence that it is missing.
2. **U8 git ban.** Confirm that no file under `L/fixtures/` and no tool under `W/tools/` can execute git, apart from the existing read-only `git --no-optional-locks status` call inside `check_governance.py`. Confirm also that the no-git scan in `run_all.py` is not vacuous: it fires on a planted git argument list.
3. Does each new fixture fail, or pass, for exactly its stated reason? Do the runners write only under `_work/` and clean up afterwards?
4. Did the change introduce any regression in regions already confirmed in seq 20? That includes weighted votes (F-027), output_file handling (F-028) and snapshot/compare (F-022, F-029).
5. Report any new defect, with severity, `file:line`, claim, evidence and fix.

## Return in reply (at most 600 words)

```
VERDICT: PASS | REVISE
## Fix confirmation (F-036..F-041)
## U8 git ban
## Fixture honesty
## Regressions and new defects
## Required changes (if REVISE)
```
