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

# Brief: independent confirmer for finding F-089 (plan §4.5; A-003)

**Identity:** `general-purpose`/sonnet, role `confirmer`. ORCH merged `W/evidence/document_values.json` and wrote its specification, and ORCH counts as family opus, so a non-opus confirmer must verify the finding. That is you.

**Read-only.** Write nothing; return everything in your reply. Use Bash only for read-only inspection, with `python -B` where you need Python.

**Root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. `W` = `reports/horizon_robustness_results/writing`; `R` = `reports/horizon_robustness_results`.

## The finding

F-089 (MINOR) says:
- `comp.budget.definition` holds the paraphrase "110% of legacy load" instead of verbatim text, against the Q-015 rule, and the specification row itself invited that form;
- `handoff.q2.incumbent_headroom` cites line 1029, although its sentence starts on line 1028.

ORCH has reworded the specification row, and a blind re-extraction of both keys runs in parallel with you. Your task is to verify the finding as it stood.

## Read

1. The latest line of F-089 in `W/governance/findings.jsonl`.
2. The specification as it stood: `W/governance/results/P1-W8-prior-DOCUMENT_VALUES_SPEC.md`, the **Text values (Q-015)** rule and the rows for both keys.
3. The current entries for both keys in `W/evidence/document_values.json`.
4. `IJSSOL_CSLAP_v1.tex` lines 580 to 586.
5. `R/EXPERIMENT_REVIEW_HANDOFF.md` lines 1026 to 1031.

## Limits

- Run no git command (U8).
- Do not read anything under `C:\Users\ebelul\AppData\Local\Temp\2\`.
- Never read `IJPR_CSLAP_*` files.

## Return in reply (at most 200 words)

```
F-089 VERIFICATION: CONFIRMED | REJECTED | CANNOT VERIFY
```

Then, with locators:
1. Is the stored `comp.budget.definition` value verbatim from its source line, or a paraphrase?
2. Did the prior specification row invite a paraphrase, in conflict with the Q-015 rule?
3. On which line does the headroom sentence start, and which line does the stored entry cite?
