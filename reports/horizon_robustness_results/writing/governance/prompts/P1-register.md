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

User decisions after the go are in `reports/horizon_robustness_results/writing/governance/user_decisions.md`. U5: IJSSOL v1 is the only baseline, and no `IJPR_CSLAP_*` file is used. U6: the IJSSOL v1 supplement is part of the baseline.

User decision U8 (14 Sep 2026) also applies: run no git command of any kind (no status, log, rev-parse, init, add, commit or config), and write nothing that runs git. Votes follow U7 weights (opus 2, fable 2, sonnet 1; no haiku).

# Brief: P1 claim register (plan P1 steps 5–6)

**Identity:** `general-purpose`/opus, role `builder`.
**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`
**Abbreviations:** `W` = `reports/horizon_robustness_results/writing`, `R` = `reports/horizon_robustness_results`.

## Inputs (read completely unless noted)

1. Plan `R/WRITING_ORCHESTRATION_PLAN_20260914.md`: §1 facts F1–F21, §3, §5 INV-3 and INV-5, the whole of P1, and Appendix D.
2. `R/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md`: all of it, especially §2 (critical corrections), §3 and §6 Step 4 (the allowed and forbidden claims).
3. `R/WRITING_PLAN_20260914.md` §1: claims C1–C8 and the "must not make" list.
4. `W/evidence/anchors.json` and `W/evidence/document_values.json`. These are the only permitted sources of numbers. Every number you write must be one of their values at a stated rounding.
5. `R/EXPERIMENT_REVIEW_HANDOFF.md` §§9–13, `R/CAMPAIGN_PREDECLARATION.md` §§8–9, `R/MATHEMATICAL_SCOPE.md`, `R/DATA_PROVENANCE.md`.
6. `IJSSOL_CSLAP_v1.tex` and `IJSSOL_CSLAP_v1_supplementary.tex`, only where a claim relates the extension to the companion.
7. `W/governance/user_decisions.md` and `W/governance/questions/` (cards Q-001 to Q-009).

## Allowed outputs

- `W/evidence/claims.json`
- `W/evidence/claims.md`
- `W/evidence/interpretation_errata.md`

## Task

1. Build `claims.json` following Appendix D.
   - Required fields for every claim: `id` (`C-01`, `C-02`, …), `type`, `endpoint_status`, `statement`, `allowed_wording[]` (at least one), `required_qualifiers[]` (each `{text, discharge}`), `forbidden_wording[]` (strings, or `{text, conditional_on: {q_card, outcome}}`), `sources[]` (`{path, sha256, locator}`), `anchor_keys[]`, `document_value_keys[]`, `unit`, `denominator`, `display_rounding`, `scope_boundary`, `supersedes[]`.
   - It must include **every row of the plan's P1 step 5 claims table** (16 rows) with the content that table requires.
   - It must also include C1–C8 of the first plan, as corrected by every row of the reviewed plan's §2 table. Merge a C1–C8 claim with a table row where they coincide; do not duplicate.
2. Write `statement` and `allowed_wording` as plain, exact sentences, suitable for later drafting.
   - Put the scope on the claim once, through `required_qualifiers`.
   - The "conservative" form is the smallest wording that still states the observation. Do not stack hedges.
3. Every number in `statement`, `allowed_wording` and qualifier texts must equal an anchor or document value named in that claim's keys, at its `display_rounding`. `check_claims.py` enforces this.
   - Section references (`§11`), card ids, `n = P` and integers 0–10 are exempt.
   - Treat percentages carefully: an anchor of unit `pct` is already in percent.
4. **Drift claim.** Its `forbidden_wording` entries "substantial", "despite" and "beyond the historical maximum" carry `conditional_on: {q_card: "Q-008", outcome: "w_greater_than_w_star"}`. Their allowed wording states the like-for-like comparison using the `drift.holdout.*` anchors. The Q-008 test is decided by ORCH from those anchors; if Q-008 already has a Resolution line, use it.
5. `claims.md`: one readable section per claim, containing statement, type and status, allowed wording, qualifiers, forbidden wording, and sources with locators.
6. `interpretation_errata.md` must contain:
   - handoff §8 line 696 ("None of these launches a solver") against `test_cplex.py:67`;
   - handoff §13.3 line 1205 and §12.6 line 1162;
   - "413 layouts" (reviewed plan line 60) against the anchors' scored-layout count (Q-009; show both numbers);
   - every other rejected wording you find.

   Give each entry the source locator, the rejected text verbatim, why it is rejected, and the replacing claim id.

## Return in reply (at most 400 words)

- counts by claim type;
- the ids that implement each P1 step 5 table row;
- every place where anchors or document values were `UNAVAILABLE`, and how the claim handles it;
- Q-cards for anything you could not settle.
