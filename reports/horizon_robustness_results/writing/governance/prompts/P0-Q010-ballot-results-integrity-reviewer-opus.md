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

User decisions made after the go are in `reports/horizon_robustness_results/writing/governance/user_decisions.md` (U5, U6).

# Ballot brief: Q-010, ADP-3, round 1 (blind)

**Your seat:** `results-integrity-reviewer/opus`, seat `plain`, evidence slice `S3`. You are **read-only**: write nothing and return one ballot in reply.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. Below, `W` = `reports/horizon_robustness_results/writing`.

## The card

`W/governance/questions/Q-010.md` asks whether to adopt four plan addenda, each drafted in full in `W/governance/questions/Q-010-addenda-draft.md`:
- **A-001**: extensions to the governance formats and rule table.
- **A-002**: carrying user decision U5 into the P9 re-run of the protected-source check.
- **A-003**: reading P1 critic seats at identity level, plus diversity notes.
- **A-004**: the missing P0 deliverables and gate-file corrections.

For each addendum the options are **(a) adopt as drafted**, **(b) adopt with a named amendment**, or **(c) reject**. Conservative order: (a) for A-002 and A-004, because they only carry forward existing decisions and fill gaps; (b) or (a) for A-001; (a) for A-003, which keeps the plan's own roster.

## Common core evidence (everyone reads)

- `W/governance/questions/Q-010-addenda-draft.md`
- Plan `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md`: §0 (precedence, addenda need a DR), §3 (hard stops H7, H8), §4.3, §4.4 (identity, reseat rule, independent confirmers), §5 INV-10, INV-11 and INV-13.
- `W/governance/user_decisions.md`

## Evidence slices (read yours in depth)

| Slice | Read |
|---|---|
| S1: plan and ledger conformance | `W/governance/results/P0-007-conformance-plan-reviewer.md`; `.unlazy/horizon-writing/GATES.md` and `gates/leaf-P*.md` |
| S2: code | `W/governance/results/P0-006-code-review-checks.md`; `W/tools/check_governance.py` |
| S3: records | `W/governance/gates/*.json`; `W/governance/dispatch_log.jsonl`; `W/governance/reseat_log.md`; `.unlazy/horizon-writing/gate_outputs/P0-G2.txt` |

## Ballot (Appendix B format), one block per addendum A-001 to A-004

```
BALLOT  Q-010/<A-00x>  voter: <identity>  round: 1  seat: <plain|red>  slice: <S#>
POSITION: a | b | c
AMENDMENT (if b): <exact replacement text>
REASONS: 1. ... [locator]  2. ... [locator]  3. ... [locator]
STEELMAN: for each rejected option, its strongest reason and why it fails [locator]
RED CASE (red seat only): <strongest case against the leading option> [locators]
BLOCKING OBJECTION: none | <checkable claim that an option breaks an invariant, a hard stop or the evidence> [locator]
PROPOSED MISSING OPTION: none | <option>
CONFIDENCE: low | medium | high
WOULD CHANGE MY MIND: <specific evidence>
```

**Rules**
- Every reason carries a locator.
- A user decision cannot be overridden by any addendum.
- A hard stop may not be converted into a routine exception.
- Keep the reply under 1,200 words.
