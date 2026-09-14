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

User decisions made after the go are recorded in `reports/horizon_robustness_results/writing/governance/user_decisions.md`: U5, U6 and U7.

# Brief: P0-W10 conformance fix confirmation (F-031 to F-034, Q-011, and the P0-W8 records)

**Identity:** `plan-reviewer`/sonnet, role `critic`. ORCH, which counts as family opus, built the artifacts under review, so the fix confirmer must be non-opus (DR-001 A-003, U7).

**Read-only.** Write nothing and return your findings in reply.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. `W` = `reports/horizon_robustness_results/writing`; `L` = `.unlazy/horizon-writing`.

## Read

1. **Source reviews.** `W/governance/results/P0-017-code-rereview-checks.md` (seq 17) and `W/governance/results/P0-018-conformance-recheck.md` (seq 18, your earlier report).
2. **Findings.** `W/governance/findings.jsonl`: the latest line for each id from F-001 to F-035.
3. **Verdicts.** `W/governance/verdicts.jsonl`.
4. **Check-script registry.** `W/governance/check_scripts.json`.
5. **Dispatch log.** `W/governance/dispatch_log.jsonl`, seq 17 to the latest.
6. **Q-card and format rule.** `W/governance/questions/Q-011.md`, and the "Fix confirmer role" paragraph in `W/governance/GOVERNANCE_FORMATS.md` §2.
7. **Required gates.** `W/governance/required_gates.json`, entry P0:G4.
8. **Gate record and outputs.** `W/governance/gates/P0-G5.json`, `L/gate_outputs/P0-G5.txt`, `L/gate_outputs/P0-G5.r1.txt`, `L/gate_outputs/nc_P0-G5_probe_sonnet_missing.txt`, and `L/fixtures/check_governance/probe_sonnet_missing/expected.txt`.
9. **Environment record.** `W/governance/environment.md`, whole file, including the section "Known limitation of the change detector".
10. **Checker.** The module docstring of `W/tools/check_governance.py`, as revised by fix round 2 (seq 19).
11. **Plan.** `WRITING_ORCHESTRATION_PLAN_20260914.md`, lines 256-270 (read-only wave protocol), 294-306 (§4.5 loops) and 443-472 (P0 steps).

## Answer

1. **Fix confirmation.** For each of F-031, F-032, F-033 and F-034, answer FIXED or NOT FIXED, with a locator:
   - F-031: P0:G4 `required_evidence` now requires a code-reviewer `VERDICT: PASS`, consistent with formats §19 R.
   - F-032: `P0-G5.json` has been re-recorded. Its `output_sha256` equals the SHA-256 of `P0-G5.txt`. Its negative-control fixture exists, and the stored negative-control output equals that fixture's `expected.txt`.
   - F-033: the environment.md disclosure is accurate against plan line 262 and against the revised checker docstring. Say whether a disclosure without an addendum is conformant.
   - F-034: the header now cites step 3 only.
2. **Q-011.** Is resolution (a) consistent with plan §4.5 BCL step 5 and with formats §1? Is Class E the right class, or did the question need a panel?
3. **P0-W8 records.** Check each of the following against the two reports:
   - F-001 to F-003 and F-005 to F-012 carry `fix_confirmed_by` code-reviewer/opus seq 17, and seq 17 marked each of them FIXED.
   - F-004 has no `fix_confirmed_by`, and its remainder is F-022.
   - F-013 to F-021 carry `fix_confirmed_by` plan-reviewer/sonnet seq 18.
   - F-022 to F-030 match seq 17 defects D1 to D8.
   - V-001 is well formed under formats §11.
   - `check_scripts.json` `review_status` is accurate.

   List every mismatch.
4. **New gaps.** Report any new conformance gap in these records.

## Output (at most 600 words)

```
VERDICT: PLAN_SOLID | PLAN_NEEDS_REVISION
## Fix confirmation (F-031 … F-034)
## Q-011
## P0-W8 records
## New gaps (blocking)
## Nice-to-have
```
