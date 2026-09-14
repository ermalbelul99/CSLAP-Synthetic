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

# Addendum to the P1 requirements-map brief (decisions made after the brief was staged)

Read `reports/horizon_robustness_results/writing/governance/prompts/P1-map.md` and follow it, with the changes below. Where the two conflict, this addendum wins.

## 1. How the map is checked (gate P1:G5, `check_claims.py --coverage`)

- **Row ids.** Every row has a unique `req_id`, and the file has at least one row.
- **`maps_to`.** Every `maps_to` must resolve to one of:
  - an existing claim `id` in `W/evidence/claims.json`;
  - `forbidden:<claim id>:<n>`, where `<n>` is a 0-based index into that claim's `forbidden_wording`.
- **Sources.** At least one row's `source` must name each of:
  - `WRITING_EXECUTION_PLAN_REVIEWED_20260914.md`
  - `CAMPAIGN_PREDECLARATION.md`
  - `PLAN_REVIEW_LEDGER_20260914.md`
- **Checking your work.** Run `W/tools/check_claims.py --coverage` and `W/tools/check_claims.py --schema` on your output before you return. Use `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe -B`.

## 2. UNMAPPED rows

Keep the brief's rule: never invent a claim id. A row with `"maps_to": "UNMAPPED"` makes P1:G5 fail by design. That is intended: ORCH routes each such row back to the claim-register builder. List every UNMAPPED row in your reply, together with the claim or forbidden wording that would cover it.

## 3. Cards

Read every card in `W/governance/questions/`, not only those named in P1-map.md. Their `Resolution:` lines can decide whether a requirement is already covered. For example:
- Q-008 decides the forbidden drift wordings;
- Q-009 decides the 412 scored cases against the reviewed plan's 413;
- Q-015 and Q-016 decide text and number rules.

## 3a. Q-cards raised by the register builder

The register builder (reply `W/governance/results/P1-040-register.md`) raised three Q-cards, which ORCH files as the next cards in `W/governance/questions/`:
- the test-suite count (Class E);
- missing document values for δ 0.01 and 0.03, the upper-only δ and the exploratory origin (Class E);
- the classification of negative results in C-17 (Class J).

While a card is open, the register carries its conservative default: no test count stated; those values in words; C-17 as written. If a requirement depends on one of these cards, map it to the claim that carries the default, and name the card in your reply. Do not mark such a row UNMAPPED only because its card is open.

## 4. Text

The `text` field is a verbatim excerpt, or a faithful excerpt of at most 40 words, of the requirement at `source`. Give `source` as `<document> <section> line <n>`.

## 5. Git, tools and isolation

- Run no git command (U8), and run Python with `-B`.
- Write only `W/evidence/requirements_map.json`.
- Do not read anything under `C:\Users\ebelul\AppData\Local\Temp\2\claude\`.
