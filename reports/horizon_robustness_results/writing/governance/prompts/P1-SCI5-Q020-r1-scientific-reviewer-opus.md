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

# Ballot brief: Q-020, SCI-5 (ADP-5), round 1 (blind)

**Your seat:** `scientific-reviewer/opus`, seat 2 of 5, role `red`, evidence slice S2 (predeclaration and handoff). You are **read-only**: write nothing and return one ballot in reply. As the red seat, argue against the option you expect to lead, with evidence.

**Seat record:** Plan SCI-5 default is fable, unavailable until 2026-09-14T19:27:48Z; reseated under §4.4 rule 1 to the same agent type with opus, which built no P1 artifact (U7 item 5). Ballot weight under U7: 2.

## The card

`W/governance/questions/Q-020.md` asks how claim C-17 should classify the held-out misses of the arms without a reserved margin (NOM and HIST+ACT) under the reviewer-first categories. Read the card's options, their conservative order, and the ordering confirmation in `reports/horizon_robustness_results/writing/governance/results/P1-048-confirm-Q020-ordering.md`. If the confirmer proposed clearer wording for an option, vote on the option as the card states it and say whether that wording would change your position.

## Common core evidence (every seat reads)

- `W/governance/questions/Q-020.md`.
- Claim C-17 in `W/evidence/claims.json`: every field.
- `.claude/skills/reviewer_first_skill/SKILL_Academic_Manuscript_Architect_and_Critical_Reviewer.md` §XII, lines 558 to 598: the five categories and what a good limitation answers.
- The BCL round 2 critic replies, for their arguments on Q-020 and C-17: `reports/horizon_robustness_results/writing/governance/results/P1-043-critic-results-integrity.md`, `reports/horizon_robustness_results/writing/governance/results/P1-044-critic-redteam.md`, `reports/horizon_robustness_results/writing/governance/results/P1-045-critic-blueteam.md`. These are arguments, not ballots.
- `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md` §4.3 and Appendix B.
- `W/governance/user_decisions.md` U7.

`W` = `reports/horizon_robustness_results/writing`. Repository root: `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`.

## Rules

- Round 1 is blind: you do not see other ballots.
- Every reason carries a locator (`path:line`, table and row, or anchor key). ORCH opens every locator; a ballot whose decisive premise is false is invalid.
- A demand for new solves, extra seeds, significance tests, confidence intervals, a λ frontier or a graph build is out of scope and is rejected. If you believe the classification cannot stand without such work, say which option is then the weaker claim and vote for it.
- Classify what the evidence shows. Do not rescue a negative result rhetorically, and do not inflate it.
- Write nothing. Run no git command (U8). Use Bash, if you have it, only for read-only inspection with `python -B`. Do not read anything under `C:\Users\ebelul\AppData\Local\Temp\2\`. Never read `IJPR_CSLAP_*` files.

## Ballot (Appendix B format)

```
BALLOT  Q-020  voter: <agent type>/<family>  round: 1  seat: <plain|red|blue>  slice: <S#>
POSITION: a | b
REASONS: 1. ... [locator]  2. ... [locator]  3. ... [locator]
STEELMAN: the rejected option's strongest reason and why it fails [locator]
RED CASE (red seat only): the strongest case against the option you expect to lead [locators]
BLUE WORDING (blue seat only): the strongest defensible C-17 sentence for your position, within the evidence [locators]
BLOCKING OBJECTION: none | <checkable claim that an option breaks an invariant, a hard stop or the evidence> [locator]
PROPOSED MISSING OPTION: none | <option>
CONFIDENCE: low | medium | high
WOULD CHANGE MY MIND: <specific evidence>
```

Keep the reply under 1,000 words.

## Chair's locator notes on the critic arguments

ORCH opened the locators behind the critics' arguments. These notes correct facts only and take no position on Q-020. Weigh each critic argument without the premises corrected here.

- **Red-team critic, F4 (ii).** C-04 shows that the returned no-margin layouts used essentially their whole training allowance, so they had no training slack left. That does not make a future breach "mechanically certain": whether a future window breaches depends on the realised shares (C-21, C-23).
- **Red-team critic, F4.** The phrase "primary, data-supported" in `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` line 363 describes the band δ = 0.02, not an arm. The predeclared primary endpoint concerns TIGHT (claim C-02).
- **Red-team critic, F4.** C-17 as written classifies the no-margin held-out misses as an "empirical limitation" whose mechanism is not isolated. Its "demonstrated boundary condition" item concerns a different result: the realised future departing from every arm's modelled set.
- **Blue-team critic, F-BT1.** "Departed the modelled range at three to six times the rate of the margin arms" does not match the anchors. The departure counts follow the scenario set, not the margin, while the pass counts follow the margin:

  | Arm | Reserved margin | Stations below / above the modelled range, per seed (`ho.departures.*`) | Held-out passes (`ho.pass.*.count`) |
  |---|---|---|---|
  | NOM | no | 13 / 11 | 0 of 3 |
  | TIGHT | yes | 12 to 13 / 11 to 12 | 3 of 3 |
  | HIST+ACT | no | 3 to 4 / 0 to 3 | 0 of 3 |
  | HIST+ACT-T | yes | 2 to 4 / 0 to 1 | 3 of 3 |

  TIGHT departed from its modelled range as often as NOM and still passed on every seed; HIST+ACT departed rarely and failed on every seed. Set departure alone therefore does not account for the no-margin misses. The table constrains the framing of both options.

  One caveat on reading the NOM and TIGHT counts (results-integrity critic, minor finding on C-21): their modelled set is the single pooled-history point, so every one of the 24 stations lies above or below it by construction (below plus above is 24 on every seed). Their counts are therefore not like-for-like with the scenario arms' 2 to 4.
- **Results-integrity critic, Q-020.** It names two anchored facts as the immediate cause of the HIST+ACT misses: the returned layouts used their whole training allowance (`ho.min_slack.HIST_ACT.*`), and the future fell below the modelled set at three or four stations (`ho.departures.HIST_ACT.*.below`). Both facts also hold for arms that passed on every seed:
  - TIGHT and HIST+ACT-T also used essentially their whole, tightened allowance (C-04: 0.009992 to 0.009999);
  - HIST+ACT-T had two to four stations below its modelled set (`ho.departures.HIST_ACT_T.*.below`).

  In this factorial, what separates the passing arms from the failing ones is the reserved margin. C-03's own qualifier says the comparison does not isolate the margin from solver and layout effects.

## Your evidence slice S2 (predeclaration and handoff); read in depth

- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` §5, §8 and §9: what each arm is meant to do, what was declared as success, and what is not tested.
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` §9.2, §12 and §13: known limitations, the two-sided sensitivity results, and stations outside the modelled set.
