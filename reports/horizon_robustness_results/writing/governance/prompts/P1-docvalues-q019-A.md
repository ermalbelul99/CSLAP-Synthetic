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

# Brief: P1 document values, blind extraction of four new keys (Q-019)

**Identity:** `optimization-coder`/sonnet, role `extractor`, blind extraction A. Ignore your role file's solver defaults: this task reads documents only. Return everything in your reply and write nothing.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`

## Blindness

- Do not open anything under `reports/horizon_robustness_results/writing/governance/` except this brief.
- Do not open `reports/horizon_robustness_results/writing/evidence/independent/`.
- Do not open these files under `reports/horizon_robustness_results/writing/evidence/`: `document_values.json`, `claims.json`, `claims.md`, `interpretation_errata.md`, `requirements_map.json`.
- Do not read anything under `C:\Users\ebelul\AppData\Local\Temp\2\`.

## The four keys

After your wave, ORCH adds these rows to the Keys table of `reports/horizon_robustness_results/writing/evidence/DOCUMENT_VALUES_SPEC.md`, worded exactly as here:

| Key | Unit | What to extract |
|---|---|---|
| `pred.upperonly.delta` | share | the band half-width δ declared as the primary setting of the upper-only campaigns, before the two-sided amendment |
| `pred.twosided.delta_aspiration` | share | in the two-sided amendment, the δ that is run as the aspiration |
| `pred.twosided.delta_fallback` | share | in the two-sided amendment, the δ described as the user's stated fallback |
| `pred.exploratory.origin` | count | the order index of the first deployment origin, the origin at which the exploratory campaigns were run |

## Task

1. Read `DOCUMENT_VALUES_SPEC.md` for the entry format, the units and the allowed sources. It does not list the four keys yet.
2. Find each value in the allowed sources, starting with `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md`. If an allowed source states a value in more than one place, cite the most specific defining line and list the other lines in NOTES.
3. Set `value_exact` to the number as a plain decimal string: no thousands separators, no `%` sign, no unit, no `δ =`. For example, a source that writes `λ = 0.5` gives `"0.5"`, and one that writes `12,345` gives `"12345"`.
4. Set `source.quoted_text` to a verbatim substring of the cited line that contains the number. Compute `source.sha256` over the whole file, read-only, for example with `python -B`.
5. If the allowed sources do not state a value, set `value_exact` to `"UNAVAILABLE"` and explain in NOTES.

## Return in reply

One fenced json block holding exactly the four keys, each with an entry in the spec's format. Then NOTES of at most 150 words: for each key, every line you considered and why you chose the one you cite.

**Rules:** write nothing, run no git command, run Python only with `-B`, and never read `IJPR_CSLAP_*` or `C&OR_CSLAP.tex`.
