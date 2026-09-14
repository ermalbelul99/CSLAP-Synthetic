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

# Brief: second-chair locator check (plan §4.3 chair verification, item 1)

**Identity:** `general-purpose`/`sonnet`, role `second_chair`. You are read-only: write nothing, and return your report in reply.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`

A voter's ballot rests on the premise below. Your job is to check that premise against the plan text. You are not asked for an opinion on the addendum.

> **Premise under check:** "Plan §4.4 defines identity as agent type plus model family (plan line 56) and states that panels mix at least two families (plan line 250). In P1 step 8, a `results-integrity-reviewer`/opus critic reviewing a claim register built by `general-purpose`/opus therefore breaks the 'at least two families' requirement, and the plan contains no provision under which that critic seat is valid."

**Read** `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md`:
- lines 50–60 (definitions);
- §4.3 and §4.4, about lines 170–300, including the panel table and the default-seat table;
- §4.5, the BCL definition;
- P1 step 5 (the register builder) and P1 step 8 (the critics), about lines 520–590.

Also read `reports/horizon_robustness_results/writing/governance/reseat_log.md`.

**Answer each question separately, quoting the plan lines you rely on:**
1. What does line 250's "Panels mix at least two families" apply to: decision panels (ADP), BCL critic sets, or both?
2. Under line 56, do `results-integrity-reviewer`/opus and `general-purpose`/opus have the same identity?
3. What families does the P1 step 8 critic set span, after the reseats in `reseat_log.md`?
4. Does any plan text forbid a critic from sharing only a model family, and not the full identity, with the builder of the artifact under review?
5. Verdict on the premise: `TRUE`, `FALSE`, or `PARTLY TRUE`, with one sentence of reasoning.

Keep the reply under 400 words.
