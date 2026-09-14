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

# Brief: P0 step 7, dry run of the P1 briefs

**Identity:** `general-purpose`/haiku, role `critic`. **Read-only.** Return your report in reply.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. `W` = `reports/horizon_robustness_results/writing`.

**Read:**
- The P1 briefs in `W/governance/prompts/`: `P1-check-author.md`, `P1-anchors-A.md`, `P1-anchors-B.md`, `P1-docvalues-A.md`, `P1-docvalues-B.md`, `P1-register.md`, `P1-map.md`.
- The specs they rely on: `W/evidence/ANCHOR_SPEC.md` and `W/evidence/DOCUMENT_VALUES_SPEC.md`.
- The plan's P1 section and Appendix D in `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md`.
- The Q-cards in `W/governance/questions/`.

**Probe feasibility, read-only.** Using read-only commands only:
- print the column names of `reports/horizon_robustness_results/tables/case_frame.csv`, `station_profile_industrial.csv`, `drift_survey.csv` and `dispersion_survey.csv`;
- print the top-level and `evaluation` / `reference_evaluation` key names of one `reports/horizon_robustness_results/campaigns/ho3_20260913/cases/*.json`.

These show whether the anchor keys can actually be computed. Do not compute the anchors themselves.

**Report:**
1. **Blockers.** Each one: brief; what stops execution; evidence; fix.
2. **Guess points.** Each one: brief; the decision an agent would have to invent; suggested default.
3. **Spec keys that look uncomputable** from the allowed inputs, with the fields you saw.
4. **Contradictions** between the briefs, the specs and the plan. Examples to look for: identities after the reseats in `W/governance/reseat_log.md`, blindness rules, allowed outputs, key names.
5. **Argument-option format.** Is the Appendix D `argument_option_X.json` format complete enough for `check_claims.py --argument` as specified in `P1-check-author.md`?

At most 600 words. Every item carries evidence.
