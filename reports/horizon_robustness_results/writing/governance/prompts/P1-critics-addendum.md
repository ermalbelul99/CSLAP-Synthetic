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

# Addendum for the three P1 step 8 critics (results integrity, red team, blue team)

Read your own brief first: `P1-critic-results-integrity.md`, `P1-critic-redteam.md` or `P1-critic-blueteam.md`, all under `reports/horizon_robustness_results/writing/governance/prompts/`. Follow it, with the changes below. Where the two conflict, this addendum wins.

This dispatch is BCL round 2. Where your brief says "BCL round <k>", read k = 2.

## 1. Decisions since your brief was staged

- **U7 and U8.** U7 weights votes and excludes haiku; U8 bans every git command. See `W/governance/user_decisions.md`.
- **Cards.** Read every card in `W/governance/questions/`. These are resolved: Q-001 to Q-003, Q-005 to Q-007, Q-009 to Q-017, and Q-008 for its test. Q-004 waits for P2. Q-008's replacement wording is Class J and goes to SCI-5.
- **Cards from the register builder** (reply `W/governance/results/P1-040-register.md`):
  - **Q-018 (E), test-suite count.** No count is stated while it is open.
  - **Q-019 (E), four missing document values.** The upper-only δ, the two-sided sensitivity δ of 0.01 and 0.03, and the exploratory origin are written in words for now. Blind extraction of these values runs in parallel with you. Do not raise the missing numerals as a finding.
  - **Q-020 (J), classification of negative results in C-17.** Option (a) is as written. Option (b) classifies the no-margin HIST+ACT misses as a genuine failure. It goes to a weighted vote after this round, and the ballots will read your arguments. Red team and blue team: each state the strongest case for your side, with evidence. Results integrity: say which option the anchors support.
- **Resolutions to apply as evidence** (not to reopen without new evidence):

| Card | Resolution |
|---|---|
| Q-002 | The companion's unseen-week result is not comparable. |
| Q-003 | Pooled-reference bias; stored and like-for-like values go together. |
| Q-005 | Incumbent headroom by training scenario set: 0 on the single history scenario (`ho.incumbent.training_slack.history`), about 0.0157 on the HIST+ACT set (`ho.incumbent.training_slack.hist_act`). The old key `ho.incumbent.training_slack` no longer exists. |
| Q-007 | Exact alias join. |
| Q-008 | w by order count, about 0.0900, exceeds w\*, about 0.0028, so "beyond the historical maximum" stays forbidden. |
| Q-009 | 412 scored cases and 188 distinct layouts; "413" matches no population. |
| Q-012 | The arms actually run per campaign. |
| Q-013 | The tail semantics are a length, so 19,837 orders are unused. |
| Q-015 | Text values are verbatim; δ is a share. |
| Q-016 | Numeric-token trace rules. |
| Q-017 | Allowed document sources. |

## 2. Evidence status

- **Anchors.** `W/evidence/anchors.json` and `W/evidence/independent/anchors_B.json` come from two independent computations, both re-run by ORCH. They agree on all 204 required keys of `ANCHOR_SPEC.md`, including the two Q-005 keys. `anchors.json` also carries a few `extra.*` context keys that only builder A computed; they are not cross-checked and never trace a number.
- **Spec wording.** Finding F-067 corrected one `ANCHOR_SPEC.md` section D row: the HIST+ACT training set has 12 members (11 block scenarios plus the history scenario). No key or value changed.
- **Document values.** `W/evidence/document_values.json` merges two blind extractions that agree on all 33 keys, plus `prov.tail_unused`.
- **Gates.** Gates P1:G1 to P1:G5 are recorded after the final checker review, so do not treat a missing gate record as a finding.
- **Where to spend your effort.** `check_claims.py` traces every number mechanically: word boundaries, range ends, ratios, small counts, `pp` against `%`, and `extra.` keys that cannot trace. Your review should concentrate on meaning, scope, framing and completeness, not on re-tracing digits.

## 3. Red-team seat

If this dispatch runs as `scientific-reviewer`/fable, the plan's seat applies unchanged. If it runs as `scientific-reviewer`/sonnet, U7's reseat applies. The fable retry window ends at 2026-09-14T19:27:48Z.

## 4. Isolation and tools

- Write nothing.
- Run no git command, and use Bash only for read-only inspection, with `python -B` where you need Python.
- Do not read anything under `C:\Users\ebelul\AppData\Local\Temp\2\claude\` or `C:\Users\ebelul\AppData\Local\Temp\2\p1*\`.
- Never read `IJPR_CSLAP_*` files.
