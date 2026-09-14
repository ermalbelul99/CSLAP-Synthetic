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

User decisions after the go are recorded in `reports/horizon_robustness_results/writing/governance/user_decisions.md`.
- **U5:** use only IJSSOL v1; never read IJPR files.
- **U6:** the IJSSOL supplement is part of the companion.

# Brief: P3 notation bridge, model delta and term whitelist (plan P3 step 1)

**Identity:** `general-purpose`/opus, role `builder`.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. Below, `W` = `reports/horizon_robustness_results/writing`.

**Skills to read first.** Apply them under the reviewed plan's §5 overrides 1–3: this is a static assignment with robust feasibility rows, not a two-stage model, and the skills are not a source of theorems.
- `.claude/skills/mathematical-formulation/SKILL.md`
- `.claude/skills/robust-modeling/SKILL.md`
- `.claude/skills/algorithm-documentation/SKILL.md`

**Inputs.**
- Companion model: `IJSSOL_CSLAP_v1.tex` §3 (lines 134–257: sets, objective, workload, abstraction, MILP, set variables). Also read every symbol the supplement `IJSSOL_CSLAP_v1_supplementary.tex` defines.
- Extension: `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md`, `CAMPAIGN_PREDECLARATION.md` §§8–9, and the reviewed plan §3 and §6 Step 2 (the mathematical preflight).
- Code identifiers, read-only: `Baselines/horizon_robustness/` (`schema.py`, `protocol.py`, `validation.py`, uncertainty/backend modules).
- `W/evidence/claims.json`: the "Model relation" claim and the mechanism claims.

**Allowed outputs.**
- `W/math/notation_bridge.md`
- `W/math/model_delta.md`
- `W/math/term_whitelist.md`

## Deliverables

1. **`notation_bridge.md`.** One table with the columns: symbol in the companion (with `file:line`) | meaning | symbol in the extension | meaning | code identifier (with `file:line`) | status (`inherited` / `changed` / `new` / `context only`). Then a collision audit:
   - Companion C_s is line capacity; slots are ζ_s.
   - V_s and T_s are context only.
   - q (patterns in the companion's column generation versus demand vectors in the extension), λ, n (horizon versus other uses), δ, ν, the scenario index k, b_s (targets), the band endpoints, and the activation set Z.

   Propose one unambiguous symbol for every collision, and give the reason.
2. **`model_delta.md`.** Three sections, each with locators:
   - *Retained:* the visit objective, assignment, slot capacity and linking rows.
   - *Replaced, not supplemented:* the fixed workload budget rows are replaced by normalised share-policy rows.
   - *Added:* targets, band, tightening, scenario and activation sets, horizons and origin.

   Then state the equivalence exactly: under uniform scaling of workload, a share band corresponds to a budget. Cite `MATHEMATICAL_SCOPE.md` for it, and state exactly what it does not imply (from `MATHEMATICAL_SCOPE.md` and the reviewed plan §3).
3. **`term_whitelist.md`.** List the technical terms and stored metric names that prose rules must not flag, each with its technical sense and a locator. At minimum: "robust", "robust counterpart", "tightening", "margin", "scenario", "activation", "novelty" (`station_novelty_count`), "framework" (only for the counterpart, if it is used at all), "significant" (only in a non-statistical sense, marked *conditional on the canon*), "band", "share", "drift", "held-out".

**Return in reply** (at most 400 words): the collisions found and the symbols proposed; anything in the companion or supplement that conflicts with the extension's model; Q-cards.
