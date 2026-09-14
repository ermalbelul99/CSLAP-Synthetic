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

# Brief: independent confirmer for card Q-016 and finding F-059 (plan §4.2; DR-001 A-003)

**Identity:** `general-purpose`/sonnet, role `confirmer`.

Both items concern artifacts that ORCH built:
- Q-016 changes a check-author brief;
- F-059 concerns the DBR builder briefs.

ORCH counts as family opus, so the confirmer must be non-opus.

**Read-only.** Write nothing, and return your answer in reply.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. Below, `W` = `reports/horizon_robustness_results/writing`.

## Item 1: Q-016, ordering of the Class J options

### Read

- `W/governance/questions/Q-016.md`.
- `W/governance/results/P1-026-code-review-checks.md`, finding 7.
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md`:
  - §4.2, on ordering Class J options;
  - P1 step 5, the claim-register table and its required numbers;
  - INV-3 and INV-4, if present.
- `W/evidence/ANCHOR_SPEC.md`, sections A and E.

### Answer

1. Is option (a) more conservative than option (b), in the sense that more of the claim register's numbers must trace? Answer CONFIRMED or REORDERED, with reasons and locators.
2. Under option (a), does any number that a P1 step 5 claim needs still escape tracing? Does any text become impossible to trace, such as section numbers, card ids, citation years or "three seeds"? Give example sentences and the result you expect under option (a).
3. State your choice: (a) or (b).

## Item 2: F-059, blindness of the DBR anchor builders

### Read

- `W/governance/findings.jsonl`, latest line of F-059.
- `W/governance/results/P1-028-anchors-B-failed.md`.
- `W/governance/results/P1-W2-agent-scratch/MANIFEST.json`.
- The briefs as dispatched:
  - `W/governance/prompts/P1-anchors-A.md`;
  - `W/governance/prompts/P1-anchors-B.md`;
  - `W/governance/dispatch_log.jsonl`, entries for seq 27 and seq 28.
- The plan's DBR rule: `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` §4.5, "DBR (double-blind reproduction)".

Do not open the files inside `P1-W2-agent-scratch/` other than its `MANIFEST.json`.

### Answer

1. Is the finding valid for the briefs as dispatched? Answer CONFIRMED or REJECTED. A valid finding means the briefs let both blind builders use a shared location outside the repository, did not forbid reading it, and so left blindness unprovable. Give locators.
2. Does the recorded evidence show that either builder actually read the other's files? Answer yes, no or unknown, with a reason.

## Return in reply (at most 450 words)

```
Q-016 ORDERING: CONFIRMED | REORDERED
Q-016 CHOICE: (a) | (b)
F-059: CONFIRMED | REJECTED
F-059 CROSS-READ SHOWN: yes | no | unknown
## Reasons (with locators)
## Q-016 coverage examples
```

**Rules:** write nothing, run no git, and never read `IJPR_CSLAP_*` files. Do not read anything under `C:\Users\ebelul\AppData\Local\Temp\2\claude\`.
