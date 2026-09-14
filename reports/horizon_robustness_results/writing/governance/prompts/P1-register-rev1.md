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

# Brief: claim register revision 1 (BCL round 2 findings, cards Q-018 to Q-024, SCI-5 decision on Q-020)

**Identity:** `general-purpose`/opus, role `builder`. You built the register in dispatch seq 40, and this is its revision.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. Below, `W` = `reports/horizon_robustness_results/writing` and `R` = `reports/horizon_robustness_results`.

## Allowed outputs

- `W/evidence/claims.json`
- `W/evidence/claims.md` (regenerated from claims.json)
- `W/evidence/interpretation_errata.md`

Write nothing else. Run no git command (U8). Run Python only with `-B`. Do not read anything under `C:\Users\ebelul\AppData\Local\Temp\2\`, and never read `IJPR_CSLAP_*` files.

## Read first

1. Your reply `W/governance/results/P1-040-register.md`, and both of your briefs: `W/governance/prompts/P1-register.md` and `P1-register-addendum.md`. Everything in them still applies unless this brief changes it.
2. The BCL round 2 critic replies: `W/governance/results/P1-043-critic-results-integrity.md`, `P1-044-critic-redteam.md`, `P1-045-critic-blueteam.md`.
3. `W/governance/findings.jsonl`: the latest line of each finding named below. The `verification.evidence` field holds ORCH's check of the finding, including corrections to the critic's wording.
4. Cards Q-018 to Q-024 in `W/governance/questions/`, and the decision record for Q-020 named at the end of this brief.
5. The evidence as it now stands:
   - `W/evidence/anchors.json`, now 248 required keys;
   - `W/evidence/document_values.json`, now 38 keys;
   - `W/evidence/ANCHOR_SPEC.md` and `DOCUMENT_VALUES_SPEC.md`, whose new rows name their findings.

## Rules that protect other artifacts

- **Forbidden-wording indices.** `W/evidence/requirements_map.json` refers to forbidden entries by position (`forbidden:<claim id>:<n>`). Append new forbidden wordings at the **end** of a claim's list. Never reorder, rewrite or delete an existing entry. If an existing entry must go, leave it in place and list it in your reply.
- **Claim ids.** Keep every existing id. A new claim takes the next free id.
- **Numbers.** Every number still traces under the rules of your addendum §2 (`W/tools/check_claims.py` implements them).
  - Cite the new keys when you use their values.
  - Where Q-019 values are now document values (`pred.upperonly.delta`, `pred.twosided.delta_aspiration`, `pred.twosided.delta_fallback`, `pred.exploratory.origin`), you may write the numbers instead of words.

## Required changes

Name the finding or card in each changed claim's `scope_boundary` (for example "Revised for F-079 and Q-023").

1. **C-01 (F-069, F-072, F-084).**
   - Add C-09's headroom qualifier as a required qualifier wherever C-01 compares an arm with the incumbent (discharge `sentence`).
   - Give the per-seed visit ranges of the no-margin arms too (`ho.visits.NOM.*`, `ho.visits.HIST_ACT.*`), and state that those ranges overlap while the margin arms' ranges do not.
   - Add an allowed wording stating, for both comparisons, that the scenario-and-activation arm's seed range of largest deviation lies entirely below the matching arm's range.
   - Append the forbidden wording "closer to target than the incumbent".
2. **C-02 and C-13 (F-070).** Append near-synonym forbidden wordings:
   - C-02: "reproduces the exploratory finding", "corroborates the earlier result", "bears out the primary endpoint".
   - C-13: "roughly double", "nearly double", "about double the companion's saving".
3. **C-03 (F-078, blocking).** State the breach magnitudes by direction for the no-margin arms from `ho.breach.<ARM>.<SEED>.cap_worst` and `.floor_worst`, as the predeclared secondary endpoint requires. Update the scope boundary, which still says a magnitude per direction is not anchored.
4. **C-13 (F-079, Q-023).**
   - Give each arm's saving together with its pass count.
   - Quote single-run ranges only split by margin, from `ho.saving.single_run.margin.*` and `ho.saving.single_run.no_margin.*`.
   - For the companion's in-sample 13.7%, set it aside on the evaluation stream and the workload restriction only, not on the extract (Q-023). For the unseen-week 6.6% and 7.4%, the extract reason stays (Q-002).
5. **C-10, C-18, C-19 and C-20 (F-080).**
   - At each BERNER screen, NOM and TIGHT have one layout scored at three nested horizons, while HIST and HIST+ACT have three layouts. Cite the layout-count keys (`uo.berner.layouts.<ARM>.count`, `ts.berner.d01|d02|d03.layouts.<ARM>.count`).
   - Never set a horizon pass count of one arm against another's as like counts.
6. **C-15 and C-07 (F-081).** The tail orders were used by no solve, score or survey, but the snapshot reconstruction read the whole export (C-27). Replace "were not used" and "unexamined in this study" with wording that says exactly that.
7. **C-08 (F-082).** δ, and so the reserved margin λδ, was chosen using the historical block-deviation statistic (predeclaration §8.2). State that no rule linking the margin to that statistic was tested, instead of saying the margin was not set from it.
8. **C-30 (F-083, F-073).**
   - Say that the check of the reserve against the site's historical station-level variation did not predict compliance here: the reserve was smaller than the incumbent's largest historical block deviation, yet both margin arms satisfied the band on every held-out seed.
   - Offer that contrast as an allowed wording.
   - Add C-08's exploratory-prefix qualifier.
9. **C-04, C-06 and C-31 (F-085).** Add a required qualifier labelling each as an additional descriptive analysis, not a predeclared endpoint.
10. **C-21 (F-086).** For NOM and TIGHT, whose modelled set is a single point, every one of the 24 stations lies above or below it by construction. Say so, and do not compare those counts with the scenario arms' counts.
11. **C-05 (F-087).** Name the objective of the gap and bound: the training visit count, not future visits.
12. **Errata (F-088, Q-018).**
    - Add a RESTRICTED entry for handoff §9.2 item 4: its "bound 0, gap 1.0 throughout" statement describes other runs and is contradicted by the held-out records, which carry a bound of 11,517 and a gap of about 0.985.
    - Update E-29 to the Q-018 resolution.
13. **C-26 (map rows RQ-027 and RQ-029; F-090).** Add the scope of the large-order filter: it selects only the movable decision pool, and orders of every size stay in the evaluation stream, workloads and visits. Add the one-product duplicate and freeze-mask edge case (`R/DATA_PROVENANCE.md` line 27) as a disclosure qualifier.
14. **C-17 and C-03 (Q-020, DR-002).** SCI-5 adopted option (d) by strict weighted majority, 7 of 8, in round 2 (`W/governance/decisions/DR-002.md`). Apply it as follows:
    - Keep HIST+ACT's held-out misses in C-17 as an empirical limitation that answers all five reviewer-first §XII questions (skill lines 592 to 598): what failed; under which conditions; why it might happen, with the explanation marked hypothetical; and which experiment would resolve it, named and not run.
    - Remove NOM's held-out misses from C-17's negative-result classification. Report them under C-03 as the contrast given by the unprotected (0,0) control. C-03 keeps NOM's 0 of 3 and its breach magnitudes in full.
    - Keep the held-out misses separate from the exploratory campaigns; they are never pooled (C-24).
    - The blue seat's round 2 wording in `W/governance/results/P1-065-SCI5-Q020-r2-positioning-reviewer-opus.md` is a candidate, not a mandate. Every number in your wording must trace.
    - Keep the existing forbidden wordings "the method fails", "robust optimisation fails", "proves that historical scenarios cannot protect" and "a boundary condition of robust optimisation in general"; append any new ones at the end.

## Checks before you return

- Run `W/tools/check_claims.py` (default trace) and `W/tools/check_claims.py --schema` with `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe -B`. Both must pass.
- `--coverage` will still fail until the map revision that follows you; report its output and do not try to fix the map.

## Return in reply (at most 700 words)

- For each numbered change: the claim ids and fields changed, with the new text of every changed statement, allowed wording and qualifier.
- Every appended forbidden wording, with its new index.
- Any existing forbidden entry that should go, left in place.
- The verbatim output lines of the trace and `--schema` runs, and the `--coverage` output.
- Any Q-card.
