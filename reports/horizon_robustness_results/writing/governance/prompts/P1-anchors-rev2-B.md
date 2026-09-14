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

# Brief: anchors builder B, targeted revision 2 (findings F-078, F-079, F-080; revision of dispatch seq 38)

**Identity:** `optimization-coder`/sonnet, role `builder`. This task reads stored results only; ignore your role file's solver and coding defaults. You return your work in your reply and write nothing inside the repository.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. Below, `W` = `reports/horizon_robustness_results/writing` and `R` = `reports/horizon_robustness_results`.

## Why this revision

The BCL round 2 critics found three gaps in the anchor specification. ORCH added rows for them to `W/evidence/ANCHOR_SPEC.md`, each marked with its finding:
- **Section A, F-078:** `ho.breach.<ARM>.<SEED>.cap_worst` and `.floor_worst`. The predeclared secondary endpoint needs breach magnitudes in both directions.
- **Section A, F-079:** `ho.saving.single_run.margin.min.pct`, `ho.saving.single_run.margin.max.pct`, `ho.saving.single_run.no_margin.min.pct` and `ho.saving.single_run.no_margin.max.pct`.
- **Section C, F-080:** `uo.berner.layouts.<ARM>.count` and `ts.berner.d01|d02|d03.layouts.<ARM>.count`, the distinct layouts behind each screen pass count.

That is 44 new required keys. Read those rows and the Conventions section.

## Task

1. Read your own script, `W/evidence/independent/recompute_anchors_B.py`. It is your seq 38 revision, byte for byte. You may also read your own output, `W/evidence/independent/anchors_B.json`.
2. Copy the script into your private directory, `C:\Users\ebelul\AppData\Local\Temp\2\p1b_rev2\`, and revise it there. Create the directory if it is missing; it is yours alone.
3. The revised script must emit the 44 new keys as normal entries in the spec's entry format: `value_exact` (an exact rational or integer), `value_float`, `unit`, `display_rounding` (the same as your existing keys of the same unit), `sources` with a selector for every case record or table row used, and `computation`.
   - **`cap_worst` and `floor_worst`:** discover the stored per-station future shares and band limits in the `ho3_20260913` case records, and compute exactly where exact fields exist. Fail loudly if the larger of the two differs from the same row's existing `.worst`, or if a side's magnitude is positive while its `.cap_count` or `.floor_count` is zero (or the reverse).
   - **Single-run savings by margin:** use the same exact formula as `ho.saving.single_run.*`. Fail loudly if the existing overall minimum and maximum are not the minimum and maximum over the two subsets.
   - **Layout counts:** count distinct `layout_hash` values over the BERNER rows of each campaign and arm in `R/tables/case_frame.csv`, and report the horizons those rows cover in `computation`.
   - **Everything else:** leave every other key byte-identical in value and in entry.
   - **If a quantity cannot be computed from the allowed inputs,** do not guess. Emit the key as `"UNAVAILABLE"`, and in your reply name the fields you looked for.
4. Run the revised script with `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe -B`. Save the script as `p1b_rev2\anchors_B_rev2.py` and its stdout as `p1b_rev2\out_B_rev2.json`.

## Isolation

Do not open any of these:
- anything under `W/governance/` except this brief (the findings and replies there contain values);
- `W/evidence/anchors.json` or `W/tools/recompute_anchors.py` (builder A's files);
- `W/evidence/claims.json`, `claims.md`, `interpretation_errata.md` or `requirements_map.json`;
- anything under `C:\Users\ebelul\AppData\Local\Temp\2\claude\`;
- anything under `C:\Users\ebelul\AppData\Local\Temp\2\p1a_rev\` or `p1a_rev2\`.

Read only ANCHOR_SPEC's allowed inputs, `ANCHOR_SPEC.md` itself and the two files named in step 1. Never import or run a repository module. Read case records only, never raw order data. Run no git command.

## Return in reply (at most 300 words)

- Path and SHA-256 of `anchors_B_rev2.py` and of `out_B_rev2.json`.
- The key count (it was 204).
- The 44 keys added, grouped by finding, with the values of the directional breach keys for NOM and HIST_ACT, and every single-run and layout-count value.
- The case-record fields you used for future shares and band limits.
- A statement that every other entry is unchanged, checked by comparing `out_B_rev2.json` with `W/evidence/independent/anchors_B.json` key by key.
