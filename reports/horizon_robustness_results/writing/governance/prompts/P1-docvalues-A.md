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

User decisions after the go: read `reports/horizon_robustness_results/writing/governance/user_decisions.md`. Under U5, IJSSOL v1 is the only baseline; never read or use any `IJPR_CSLAP_*` or `C&OR_CSLAP.tex` file.

User decision U8 (14 Sep 2026) also applies: run no git command of any kind (no status, log, rev-parse, init, add, commit or config), and write nothing that runs git. Votes follow U7 weights (opus 2, fable 2, sonnet 1; no haiku).

# Brief: P1 document values, extractor A (double-blind reproduction)

**Identity:** `optimization-coder`/sonnet, or `general-purpose`/fable if dispatched after fable's `retry_after` (user decision U7 excludes haiku). Role: `extractor`. Return your result in your reply and write nothing to disk. Ignore your role file's solver-implementation defaults; this task reads documents only.

**Disagreement rule:** if your extraction and the other extractor's disagree, ORCH resolves the value under plan §4.2 (a blind re-derivation by another identity). No vote decides it.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`

## Blindness

A second extractor is doing the same work independently. Do not open:
- `reports/horizon_robustness_results/writing/evidence/document_values.json`
- `reports/horizon_robustness_results/writing/evidence/independent/`
- `reports/horizon_robustness_results/writing/governance/results/`

## Task

1. Read `reports/horizon_robustness_results/writing/evidence/DOCUMENT_VALUES_SPEC.md` completely.
2. For every key in the spec, find the value in the allowed sources. Record the exact 1-based line number and a verbatim substring of that line.
3. Compute the SHA-256 of each source file with a read-only command, for example:

   ```
   C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <path>
   ```

4. If a key has no clear source, set `value_exact` to `"UNAVAILABLE"` and explain which files and passages you searched.

## Return in reply, in this order

1. `OUTPUT`: one fenced json block containing the complete object `{key: entry}`.
2. `NOTES`, at most 250 words: ambiguities (for example, two candidate lines for the same value), whether `prov.stream_end` is an index or a length and why, and any Q-cards.
