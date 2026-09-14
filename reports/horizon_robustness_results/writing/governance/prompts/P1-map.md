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

User decision U8 (14 Sep 2026) also applies: run no git command of any kind (no status, log, rev-parse, init, add, commit or config), and write nothing that runs git. Votes follow U7 weights (opus 2, fable 2, sonnet 1; no haiku).

# Brief: P1 requirements map (plan P1 step 4)

**Identity:** `general-purpose`/opus, role `builder` (U7 excludes haiku; the coverage check author is general-purpose/sonnet).
**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`
**Shorthand:** `W` = `reports/horizon_robustness_results/writing`, `R` = `reports/horizon_robustness_results`.

## Inputs

- `W/evidence/claims.json`: the claim register, which exists when you start.
- `R/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md`:
  - §2 "Critical corrections before writing": every table row.
  - §3 "Non-negotiable data and information contract": every bullet.
  - §3 "What carries over, what changes": every table row.
  - §6 Step 4: the "Allowed" and "Forbidden" sentences.
- `R/CAMPAIGN_PREDECLARATION.md`:
  - §5 "Reporting commitments that do not depend on the outcome": every bullet.
  - §9.4 "Reporting rules": every bullet.
- `R/PLAN_REVIEW_LEDGER_20260914.md`: every adopted row whose revision-3 or revision-4 location names a claims row, a `Q-`card, F10–F20, INV-5, or "claims". These are the claim-bearing rows.

## Allowed output

`W/evidence/requirements_map.json`

## Task

Write a JSON list with one object per requirement:

```json
{"req_id": "RQ-001", "source": "<document> <section> line <n>", "text": "<verbatim or faithful excerpt, at most 40 words>", "maps_to": "<claim id>" | "forbidden:<claim id>:<index>"}
```

A requirement is satisfied either by a claim that states it or scopes it, or by a forbidden-wording entry that blocks the error it describes. Use the 0-based index into that claim's `forbidden_wording`.

When a requirement has no suitable claim or forbidden entry, set `maps_to` to `"UNMAPPED"` and explain it in your reply. Never invent a claim id.

## Return in reply (at most 300 words)

- Row counts per source.
- Every `UNMAPPED` row, with the missing claim or forbidden wording that would cover it, so ORCH can route it to the register builder.
