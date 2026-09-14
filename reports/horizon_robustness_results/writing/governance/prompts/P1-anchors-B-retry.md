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

# Addendum: anchors builder B, retry of dispatch seq 28 (finding F-059)

**Identity:** `optimization-coder`/sonnet, role `builder`. This is the retry of dispatch seq 28, which failed on an API session limit.

Read `reports/horizon_robustness_results/writing/governance/prompts/P1-anchors-B.md` and follow it, with the overrides below. Where the two conflict, this addendum wins.

## 1. Working directory

Run your script only from `C:\Users\ebelul\AppData\Local\Temp\2\p1b_retry\`. Create that directory if it is missing; it is yours alone.

This replaces line 84 of P1-anchors-B.md, "Run it from a temporary location that is not in the repository". That line left the location open, and in dispatch seq 28 it led to a directory shared with another agent. The directory above is now the only one allowed. Write nothing anywhere else, and write nothing inside the repository, including `__pycache__`.

## 2. Isolation

Do not list, open or read anything under `C:\Users\ebelul\AppData\Local\Temp\2\claude\`. That tree holds the orchestrator's session scratchpad and task files.

Do not open any of these paths in the repository:
- `reports/horizon_robustness_results/writing/evidence/anchors.json`
- `reports/horizon_robustness_results/writing/tools/recompute_anchors.py`
- `reports/horizon_robustness_results/writing/evidence/independent/`
- anything under `reports/horizon_robustness_results/writing/governance/results/`. That folder now holds another builder's outputs and your own earlier failed attempt.

Do not look for or reuse any earlier attempt. Start from `ANCHOR_SPEC.md` and the allowed inputs.

## 3. Output

Your reply must carry the complete script and the complete output.

If the output is too large for one reply:
- save the complete stdout as `C:\Users\ebelul\AppData\Local\Temp\2\p1b_retry\out_B.json`;
- save the script as `C:\Users\ebelul\AppData\Local\Temp\2\p1b_retry\anchors_B.py`;
- in your reply, give each file's path and SHA-256 together with your NOTES. ORCH copies both files.

Never split the JSON across several messages.

## 4. Rules

- Run Python with `-B`: `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe -B`.
- Run no git command (U8).
- Read only the allowed inputs listed in `ANCHOR_SPEC.md`, and never read raw order data.
- Never import or run a repository module.

## Return in reply

- `SCRIPT`: a fenced python block, or the saved path and its SHA-256.
- `OUTPUT`: a fenced json block, or the saved path and its SHA-256.
- `NOTES`: at most 300 words, covering discovered selectors, UNAVAILABLE keys, Section E mismatches and any Q-card.
