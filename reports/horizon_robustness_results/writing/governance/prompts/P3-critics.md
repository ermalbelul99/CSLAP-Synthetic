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

# Brief: P3 critics, BCL round <k> (plan P3 step 5)

This brief has two variants. ORCH dispatches one per critic.

## Variant F: `formulation-reviewer`/`<family>` (default fable, reseated if unavailable)

**Role:** critic. Read-only; return your review in reply.

**Under review**
- `W/math/notation_bridge.md` and `W/math/model_delta.md`, built by general-purpose/opus
- `W/math/method_notes.md`, built by general-purpose/opus
- `W/math/derivation_A.md` and `W/math/derivation_B.md`

**Reference**
- the companion model, `IJSSOL_CSLAP_v1.tex` §3 and its supplement (U6)
- `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md`
- the reviewed plan's §6 Step 2 preflight items 1–8
- `W/evidence/claims.json`: the Model relation and Mechanism claims

**Check**
1. Every definition, constraint and envelope is mathematically correct and internally consistent with the companion's notation, with every collision resolved.
2. The workload-budget rows are stated as replaced, not supplemented. Share preservation is a constraint, not an objective. The uniform-scaling equivalence is stated no more broadly than it holds.
3. Each derivation step holds, including the lower trapped-activation indicator and every edge case.
4. The integer-count restatement is exactly equivalent under its stated conditions.
5. The TV bound is proved, and neither guarantee is overstated.
6. Each preflight item is either answered correctly or honestly left open.

**Return in reply** (at most 800 words):
- `VERDICT: PASS` or `VERDICT: REVISE`
- Findings, each with: severity (BLOCKING, MAJOR or MINOR); file and section or equation; claim; evidence; proposed fix.

## Variant C: `code-reviewer`/opus (U7 excludes haiku; opus differs from the enumerator author's family, sonnet)

**Role:** critic. Read-only; return your review in reply.

**Under review:** the math-to-code map in `W/math/method_notes.md` §8, against `Baselines/horizon_robustness/` (`validation.py`, uncertainty modules, `schema.py`, `protocol.py`) and `W/math/tools/enumerate_edge_cases.py`.

**Check**
1. Every equation's code locator points to code that implements that equation, including the two-sided floors, the tightening, both activation envelopes and the integer thresholds.
2. Every `NOT IMPLEMENTED` entry is truly absent.
3. The enumerator compares the notes' formulas and the production validator independently: it must not copy the validator's logic into its expected values.
4. The enumerator's `--formula-override` negative control can actually fail.

**Return in reply** (at most 700 words):
- `VERDICT: PASS` or `VERDICT: REVISE`
- Findings, each with: severity; `file:line`; claim; evidence; fix.
