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

# Blue-team critic: additional item, fix confirmation of finding F-059 (plan §4.5 BCL step 5; Q-011; DR-001 A-003)

You are `general-purpose`/sonnet in role `critic`. ORCH built the artifacts behind F-059, and ORCH counts as family opus, so a non-opus critic must confirm the fix. That is you.

## Read

- `W/governance/findings.jsonl`: the latest line of F-059. It is CONFIRMED by the independent confirmer, seq 35.
- `W/governance/results/P1-028-anchors-B-failed.md` and `W/governance/results/P1-035-confirm-Q016-F059.md`.
- The fix, as dispatched:
  - `W/governance/prompts/P1-anchors-B-retry.md` (seq 36);
  - `W/governance/prompts/P1-anchors-rev-A.md` (seq 37);
  - `W/governance/prompts/P1-anchors-rev-B.md` (seq 38).
- The replies:
  - `W/governance/results/P1-036-anchors-B-retry.md`;
  - `W/governance/results/P1-037-anchors-rev-A.md`;
  - `W/governance/results/P1-038-anchors-rev-B.md`.
- `W/governance/dispatch_log.jsonl`: the entries for seq 36, 37 and 38.

Do not open any `*.script.py` or `*.output.json` file, and do not open `P1-W2-agent-scratch/`.

## Answer (add to your reply, at most 200 words)

```
F-059 FIX: FIXED | NOT FIXED
```

Answer each question with locators:
1. Did each later builder brief name a private working directory?
2. Did each forbid reading the other builder's files and the orchestrator's scratchpad?
3. Did each reply report working in its private directory, with hashes for saved files?
4. Is any residual gap left open for later DBR dispatches (P2 and P3 derivations)? If so, state the rule the briefs should carry from now on.

## Second item: fix confirmation of F-067 (same seat, same reasons)

ORCH built `W/evidence/ANCHOR_SPEC.md`. Finding F-067 says its section D row `ho.incumbent.training_slack.hist_act` called the HIST_ACT training set "the historical block scenarios", while the stored set also includes the whole-history scenario.

Read:
- the latest line of F-067 in `W/governance/findings.jsonl`;
- that row of `W/evidence/ANCHOR_SPEC.md`;
- the scenario labels reported in `P1-037-anchors-rev-A.md` and `P1-038-anchors-rev-B.md`.

Add to your reply, at most 80 words:

```
F-067 FIX: FIXED | NOT FIXED
```

Answer both with locators:
1. Does the row now describe the scenario set both builders report?
2. Does the edit change any key name or the value to be computed?
