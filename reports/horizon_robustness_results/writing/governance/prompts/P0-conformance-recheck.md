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

User decisions made after the go are in `reports/horizon_robustness_results/writing/governance/user_decisions.md` (U5, U6).

# Brief: P0 conformance re-check (fix confirmation for F-013 to F-021, and the P0:G6 verdict)

**Identity:** `plan-reviewer`/sonnet, role `critic` and fix confirmer. Gaps F-013 to F-021 were raised by `plan-reviewer`/opus in dispatch seq 7. They concern artifacts that ORCH built. ORCH counts as family opus, so the fix confirmer must be non-opus (DR-001 A-003, user decision U7); fable is unavailable until its `retry_after`. You are read-only: write nothing, and return your findings in reply.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. `W` = `reports/horizon_robustness_results/writing`; `L` = `.unlazy/horizon-writing`.

## Read

1. Your earlier report: `W/governance/results/P0-007-conformance-plan-reviewer.md`.
2. The decision on those gaps, `W/governance/decisions/DR-001.md`, and the adopted `W/governance/PLAN_ADDENDA.md`.
3. The governance files as they now stand:
   - `W/governance/GOVERNANCE_FORMATS.md` (v2)
   - `W/governance/required_gates.json`
   - `W/governance/check_scripts.json`
   - `W/governance/verdicts.jsonl`, if present
   - `W/governance/dispatch_log.jsonl`, including the correction events
   - `W/governance/findings.jsonl`
   - `W/governance/state.json`
4. The ledger files: `L/gates/leaf-P0.md` … `leaf-P9.md` and `L/GATES.md`.
5. The P0 deliverables `W/governance/environment.md` and `W/evidence/verification_inventory.md`, checked against plan P0 steps 3 and 6.
6. `W/tools/check_governance.py` after the fix round, and the fix-round report `W/governance/results/P0-*-fix-round*.md`.
7. The gate records `W/governance/gates/P0-*.json` and their outputs under `L/gate_outputs/`.

## Answer

1. For each of F-013 to F-021, give FIXED or NOT FIXED, with the locator of the fix or the evidence that it is still missing.
2. Do `environment.md` and `verification_inventory.md` fully cover plan P0 steps 3 and 6? This includes the "re-run versus cited" separation, with correct locators.
3. Report any new conformance gap introduced by the fixes.
4. User decision U7 (`W/governance/user_decisions.md`, section U7) must be applied consistently in all of these:
   - `state.json`: `families` (haiku excluded; fable `retry_after`), `required_families`, `vote_weights`, `u7_from_seq`;
   - `W/governance/u7_rosters.md`: no haiku seat; weights and majority thresholds correct;
   - the U7 section of `reseat_log.md`;
   - the U7 re-tally note in `DR-001.md`: outcomes recomputed correctly with weights opus 2, sonnet 1, without the haiku ballots;
   - `environment.md`;
   - every staged brief under `W/governance/prompts/P1-*`, `P2-*` and `P3-*`: no haiku identity.

   List every inconsistency with its locator.

## Output (at most 600 words)

```
VERDICT: PLAN_SOLID | PLAN_NEEDS_REVISION
## Fix confirmation (F-013 … F-021)
## P0 deliverables
## New gaps (blocking)
## Nice-to-have
```
