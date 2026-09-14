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

User decisions after the go: read `reports/horizon_robustness_results/writing/governance/user_decisions.md`. Under U5, IJSSOL v1 is the only baseline, and no `IJPR_CSLAP_*` file may be read or used.

User decision U8 (14 Sep 2026) also applies: run no git command of any kind (no status, log, rev-parse, init, add, commit or config), and write nothing that runs git. Votes follow U7 weights (opus 2, fable 2, sonnet 1; no haiku).

# Brief: P1 anchors, builder B (double-blind reproduction)

**Identity:** `optimization-coder`/sonnet, or `general-purpose`/fable if dispatched after fable's `retry_after` (user decision U7 excludes haiku; see `governance/reseat_log.md`). Role: `builder`. Return your results in your reply and write nothing to disk. Ignore your role file's solver-implementation defaults: this task only reads stored tables and case records and prints JSON.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`
**Python:** `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe` (pandas and numpy are available)

## Blindness

A second builder is computing the same anchors independently. Do not open:
- `reports/horizon_robustness_results/writing/evidence/anchors.json`
- `reports/horizon_robustness_results/writing/tools/recompute_anchors.py`
- `reports/horizon_robustness_results/writing/evidence/independent/`
- anything under `reports/horizon_robustness_results/writing/governance/results/`

Also do not read the reviewed plan's anchor table until your script has run. Section E of the spec contains the values you will compare against.

## Task

1. Read `reports/horizon_robustness_results/writing/evidence/ANCHOR_SPEC.md` completely. It defines every key, unit, definition, allowed input and value format.
2. Inspect the allowed inputs read-only. Discover the columns and fields each key needs, and record every selector you use.
3. Write one self-contained Python script:
   - standard library, pandas and numpy only;
   - read only the allowed inputs;
   - compute every key in ANCHOR_SPEC sections A–D;
   - print one JSON object `{key: entry}` to stdout, using the spec's entry format, with a `sha256` for every source file;
   - use `fractions.Fraction` wherever the input is an exact field or a count.

   Run it from a temporary location that is not in the repository, printing to stdout only.
4. Run the script and capture its output.
5. Compare your results with section E. Report any mismatch; do not adjust your computation to match.

## Return in reply, in this order

1. `SCRIPT`: one fenced python block containing the complete script.
2. `OUTPUT`: one fenced json block containing the complete stdout JSON.
3. `NOTES`, at most 300 words:
   - the column and field names you discovered;
   - every `UNAVAILABLE` key, with the fields you inspected;
   - any section E mismatches;
   - any Q-card.
