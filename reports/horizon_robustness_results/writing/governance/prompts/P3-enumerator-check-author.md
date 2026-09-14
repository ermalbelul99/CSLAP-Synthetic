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

User decisions after the go: `reports/horizon_robustness_results/writing/governance/user_decisions.md` (U5, U6).

# Brief: P3 edge-case enumerator (plan P3 step 3; INV-11, INV-13)

**Identity:** `general-purpose`/sonnet, role `check_author` (U7 excludes haiku). Your code reviewer will be `code-reviewer`/opus.
**Root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. `W` = `reports/horizon_robustness_results/writing`; `L` = `.unlazy/horizon-writing`.

**Allowed outputs:**
- `W/math/tools/enumerate_edge_cases.py`
- `L/fixtures/enumerate_edge_cases/**`

## Inputs

- `W/math/method_notes.md`: the merged derivation. Its numbered envelope and count formulas are the formulas under test.
- `W/math/notation_bridge.md`.
- `Baselines/horizon_robustness/validation.py`: read it, and import it read-only. It imports no solver (lines 9–14); confirm this before importing.
- `Baselines/horizon_robustness/schema.py` and `protocol.py`, for the data types the validator expects. Read-only.

## Task

Write a self-contained script (default root `Path(__file__).resolve().parents[5]`, overridable with `--root DIR`) that builds tiny fixtures in memory and checks each formula against the validator:

- **Size:** at most 6 products, 3 stations and 4 scenario blocks.
- **Arithmetic:** exact `fractions.Fraction` throughout.
- **Coverage:** each fixture covers one edge case from preflight item 4:
  - empty inactive set Z;
  - ν = 0;
  - full activation;
  - all inactive products assigned to one station (the lower trapped-activation indicator);
  - fixed inactive products;
  - band endpoints clipped at 0 and at 1;
  - tightening λ = 0 and λ = 0.5.
- **Checks per fixture:**
  - brute-force the worst-case upper and lower station shares over the uncertainty set, enumerating vertices exactly;
  - compare them with the `method_notes.md` formulas;
  - compare both with the production validator's result for the same assignment;
  - check the integer-count restatement against the share rows for every assignment of the fixture.
- **Output:** one line per fixture, `AGREE <name>` or `DISAGREE <name>: <detail>`. Finish with `EDGE CASES AGREE (<n> fixtures)` and exit 0, or `EDGE CASES DISAGREE (<k>)` and exit 1. Zero fixtures must fail.
- **`--formula-override PATH`:** loads a JSON file that replaces one threshold or formula coefficient. It exists for the negative-control fixture `L/fixtures/enumerate_edge_cases/mutated_threshold.json`, which must make the script exit 1.

**Constraints:** no solver import, no data loader, no reading of campaigns or raw data. If the validator's API needs a structure it cannot build without a loader, return a Q-card instead of guessing.

**Return in reply** (at most 400 words):
- the fixtures and what each covers;
- the output on the real root and with `--formula-override`;
- any formula in `method_notes.md` that the validator contradicts, quoting both.
