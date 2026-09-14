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

# Brief: P0 step 7, plan conformance (BCL, one round)

**Identity:** `plan-reviewer`/opus, role `critic`. **Read-only.** Return your report in reply.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. `W` = `reports/horizon_robustness_results/writing`; `L` = `.unlazy/horizon-writing`.

**Read:**
1. `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` (revision 4, the governing contract)
2. `reports/horizon_robustness_results/PLAN_REVIEW_LEDGER_20260914.md`
3. `L/PLAN.md`, `L/GATES.md`, `L/gates/leaf-P0.md` … `leaf-P9.md`, `L/status.log`
4. `W/governance/GOVERNANCE_FORMATS.md`, `user_decisions.md`, `reseat_log.md`, `state.json`, `PLAN_ADDENDA.md`, `DISPATCH_PREAMBLE.md`, `PREAMBLE_MINIMAL.md`, `ai_use_record.md`
5. `W/governance/gates/P0-G2.json`, `W/governance/gates/P0-G3.json`, and the dispatch log `W/governance/dispatch_log.jsonl`

**Answer, each with locators:**
1. Do `L/PLAN.md`, `L/GATES.md` and the leaf gate files implement every gate of plan §6 P0–P9? Check the exact CHECK commands and EXPECT tokens, and flag anything missing or wrong.
2. Does `GOVERNANCE_FORMATS.md` implement plan Appendices B, C and E and INV-10/INV-11 closely enough for `check_governance.py` rules (a)–(i)? Name any rule that cannot be evaluated from the formats as written.
3. Are user decisions U5 and U6, the P0:G2 waiver and the fable reseats consistent with plan §0 precedence, §3 (H9), §4.4 (reseat rule) and INV-2? Is anything a hard stop that has been treated as routine, or the reverse?
4. Does the record so far satisfy INV-10? Check the dispatch log, saved prompts and results, and state.
5. Is anything required by an adopted ledger row missing from the execution setup?

**Output** (at most 700 words, plain English):

```
VERDICT: PLAN_SOLID | PLAN_NEEDS_REVISION
## GAPS (blocking): <item>: <gap>. evidence: <locator>. fix: <fix>.
## NICE-TO-HAVE
```

Route every escalation to the orchestrator.
