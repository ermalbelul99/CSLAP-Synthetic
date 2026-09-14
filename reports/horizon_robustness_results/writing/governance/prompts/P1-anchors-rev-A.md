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

# Brief: anchors builder A, targeted revision for card Q-005 (revision of dispatch seq 27)

**Identity:** `general-purpose`/opus, role `builder`. You return your work in your reply and write nothing inside the repository.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. Below, `W` = `reports/horizon_robustness_results/writing`.

## Why this revision

`W/evidence/ANCHOR_SPEC.md` section D no longer has the key `ho.incumbent.training_slack`. Two explicit keys replace it:
- `ho.incumbent.training_slack.history`: the NOM and TIGHT rows, whose training scenario set is the single history scenario;
- `ho.incumbent.training_slack.hist_act`: the HIST_ACT and HIST_ACT_T rows, whose training scenario set is the historical block scenarios.

Read the two rows in section D and card `W/governance/questions/Q-005.md`.

## Task

1. Read your own script, `W/tools/recompute_anchors.py`. It is your seq 27 script, byte for byte. You may also read your own output, `W/evidence/anchors.json`.
2. Copy the script into your private directory, `C:\Users\ebelul\AppData\Local\Temp\2\p1a_rev\`, and revise it there. Create the directory if it is missing; it is yours alone.
3. The revised script must:
   - no longer emit `ho.incumbent.training_slack`;
   - no longer emit `extra.ho.incumbent.training_slack.hist_act_scenarios`, because it now duplicates a required key;
   - emit `ho.incumbent.training_slack.history` and `ho.incumbent.training_slack.hist_act` as normal entries in the spec's entry format:
     - `value_exact` as an exact rational;
     - `value_float`;
     - `unit` `share`;
     - `display_rounding` 6;
     - `sources`, listing the 6 case records each value comes from, each with its selector;
     - `computation`.
   - fail loudly if the value differs across the 6 rows of either key, and name the scenario labels (`label`, `start`, `stop`) used by those rows in `computation`;
   - leave every other key byte-identical in value and in entry.
4. Run the revised script with `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe -B`. Save the script as `p1a_rev\anchors_A_rev.py` and its stdout as `p1a_rev\out_A_rev.json`.

## Isolation

Do not open any of these:
- anything under `W/evidence/independent/`;
- anything under `W/governance/results/`;
- anything under `C:\Users\ebelul\AppData\Local\Temp\2\claude\`;
- anything under `C:\Users\ebelul\AppData\Local\Temp\2\p1b_rev\` or `p1b_retry\`.

Read only ANCHOR_SPEC's allowed inputs, plus the two files named in step 1. Never import or run a repository module. Run no git.

## Return in reply (at most 250 words)

- Path and SHA-256 of `anchors_A_rev.py`.
- Path and SHA-256 of `out_A_rev.json`.
- The key count.
- The keys you removed and added, with the two values and the scenario labels.
- A statement that every other entry is unchanged. Check it by comparing `out_A_rev.json` with `W/evidence/anchors.json` key by key.
