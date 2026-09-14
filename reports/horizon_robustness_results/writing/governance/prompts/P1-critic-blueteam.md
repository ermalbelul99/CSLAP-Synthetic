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

User decision U8 (14 Sep 2026) also applies: run no git command of any kind (no status, log, rev-parse, init, add, commit or config), and write nothing that runs git. Votes follow U7 weights (opus 2, fable 2, sonnet 1; no haiku).

# Brief: P1 step 8, blue-team critic (BCL round <k>)

**Identity:** `general-purpose`/sonnet, role critic (blue team). **Read-only**: write nothing, return everything in reply. Bash only for read-only inspection.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`

**Material:** the same artifacts and evidence as the results-integrity critic:
- `W/evidence/claims.json`, `W/evidence/claims.md`, `W/evidence/requirements_map.json`, `W/evidence/document_values.json`, `W/evidence/anchors.json`
- `W/governance/questions/`
- `R/tables/`
- the reviewed plan §2 and §6 Step 4

## Your job

Argue for the strongest version of each claim that the evidence still supports (plan §4.3; OR-writing skill mode [D]). The red-team critic and the conservative defaults push toward silence; your job is to find where the register has become weaker than the evidence. Look for:

1. **Over-hedging.** Qualifiers repeated in claims where the scope-once rule would discharge them once. Hedges that make a clear observation sound doubtful.
2. **Buried findings.** Examples: the non-overlapping seed ranges; the minimum-slack mechanism showing that every returned layout uses its whole allowance; 3/3 against 0/3; the practitioner-relevant policy. If any of these is stated too weakly, or missing as a positive observation, say so.
3. **Allowed wording.** Is there at least one plain, confident allowed wording for each claim, so a drafter is not forced into the forbidden list?
4. **Correct classification.** Limitations that are really demonstrated boundary conditions (reviewer-first §XII) and should be stated as findings.

For every proposal, cite the evidence that supports the stronger wording. Never propose a claim beyond what the anchors show.

## Return in reply (at most 700 words)

Findings, each with: severity (MAJOR or MINOR), claim id, current wording, proposed wording, evidence.
