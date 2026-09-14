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

User decisions after the go are in `reports/horizon_robustness_results/writing/governance/user_decisions.md` (U5, U6).

# Brief: P3 blind derivation <A|B> (plan P3 step 2, DBR)

**Identity:** `general-purpose`/`<family>`, role `builder`. Return your derivation in reply; write nothing.

## Blindness

A second deriver is working independently. Do not open any of these:
- anything under `reports/horizon_robustness_results/writing/math/` except `notation_bridge.md` and `model_delta.md`;
- any file under `Baselines/`;
- any file under `tests/`.

Derive from the mathematics, not from the implementation.

## Allowed reading

- `reports/horizon_robustness_results/writing/math/notation_bridge.md` and `model_delta.md` (use their symbols);
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md`;
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` §§8–9;
- the reviewed plan §3 and §6 Step 2 (the preflight items);
- `IJSSOL_CSLAP_v1.tex` §3 and its supplement, for the base model.

`MATHEMATICAL_SCOPE.md` may contain an older upper-only exposition. Where you find one, derive the two-sided version and say so.

## Derive, with every step justified

**(a) Hull and activation set.** For the historical-hull plus activation uncertainty set (block scenarios; activation budget ν on inactive products Z):

1. Give the exact worst-case **upper** and **lower** station-share envelopes for a fixed assignment.
2. Include the lower trapped-activation indicator for the case where **all** inactive products are assigned to a single station.
3. Treat these edge cases explicitly:
   - empty Z;
   - ν = 0 and ν at full activation;
   - fixed inactive products;
   - band endpoints clipped at 0 and 1.
4. State the resulting robust feasibility rows for the two-sided band [max(0, b_s − δ), min(1, b_s + δ)], with and without tightening λ.

**(b) Integer-count restatement.** Restate the fixed-cap share rows as integer-count rows, with floor and ceiling thresholds given as exact rationals. State the conditions under which the restatement is exactly equivalent, and why a finite-precision solver return is not an exact certificate.

**(c) What is and is not guaranteed.**
1. State the conditional U-membership guarantee exactly (feasible for every demand vector in U).
2. State the sufficient total-variation bound: a layout within δ − ρ of pooled-history targets stays within δ on any demand whose product mix is within ρ of pooled history in total variation. Prove it.
3. Explain why neither result certifies the realised futures in this study.

**(d) Nested horizons.** Give the set-inclusion relations between matched nested horizons and their assumptions. State why they imply no monotonicity of realised compliance or of time-capped returned cost.

## Return in reply

One markdown document with sections (a) to (d). Use LaTeX math inline. Number every equation. Mark every assumption as **Assumption k**.

At the end, add a list headed "Points where I was unsure", each with a Q-card.

Maximum length: 3,500 words.
