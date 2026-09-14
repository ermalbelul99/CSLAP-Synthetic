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

# Addendum to the P1 claim-register brief (decisions made after the brief was staged)

Read `reports/horizon_robustness_results/writing/governance/prompts/P1-register.md` and follow it, with the changes below. Where the two conflict, this addendum wins.

## 1. Cards

Read every card in `W/governance/questions/`, not only Q-001 to Q-009. The following cards bear directly on claims:

| Card | What it decides |
|---|---|
| Q-005 | Incumbent headroom by training scenario set. See the key rule below. |
| Q-012 | Which arms each campaign ran. The held-out campaign had no HIST arm; the two-sided screens had no HIST_ACT_T. |
| Q-013 | `prov.tail_unused` is computed from the stream-end semantics. |
| Q-015 | Text values are verbatim. δ is a share; ν and λ are fractions. |
| Q-016 | The numeric-token rules for `check_claims.py`, below. |
| Q-017 | The allowed document sources. |

For Q-002, Q-003, Q-005, Q-007, Q-008 and Q-009, use each card's `Resolution:` line as it stands when you start. If a card is still open, return a Q-card instead of guessing.

**Q-005 keys.**
- The key `ho.incumbent.training_slack` no longer exists. Some cards still name it in their decisive test; do not cite it.
- Cite `ho.incumbent.training_slack.history` for comparisons with NOM and TIGHT (the single history scenario [0, 243151)).
- Cite `ho.incumbent.training_slack.hist_act` for comparisons with HIST+ACT and HIST+ACT-T. Their stored training set has 12 members: 11 historical block scenarios plus the history scenario.

## 2. Numbers must trace (replaces task item 3, second bullet, of P1-register.md)

`check_claims.py` implements Q-016 option (a). A targeted fix round (seq 39) runs in parallel with you and tightens three rules (years, rounding, range units). Write to the tightened rules below; they are stricter than the current script.

**Exempt tokens.** A number is exempt only in these cases:
- It is a section reference (`§11`) or a card id (`Q-008`, `C-03`).
- It follows `n = `, `line ` or `lines ` as a whole word.
- It is a four-digit citation year in exactly one of these forms:
  - the whole parenthesised content is the year: `(2021)`;
  - the year closes a citation in parentheses: `(Smith, 2021)`, `(Smith et al., 2021)`, `(Smith and Jones, 2021)`;
  - the year follows a capitalised surname in narrative form: `Smith (2021)`, `Smith et al. (2021)`.

  Any other four-digit number counts, so `(2000 rows)` and `in 2000 blocks` must trace.

**Hyphens and slashes.**
- A hyphen or slash exempts a number only when a letter comes right before it.
- Both ends of a range count, whether written `3.23-3.35` or `13.0–16.0`.
- Negatives count.
- Both sides of `digits/digits` count. Write "3/3" only when the claim cites the matching count anchor.

**Small integers.** Integers from 0 to 10 must trace whenever the claim cites any anchor or document value of unit `count` or `bool`. Otherwise, write small counts in words ("three seeds") unless they trace.

**Units.**
- A number followed by `%` traces only to a value of unit `pct`.
- A number followed by `pp` traces only to a value of unit `pp`.
- In a range such as `2.1–2.4%` or `1.0-1.5 pp`, the unit applies to both ends.
- Never write a pp difference with `%`, or the reverse.

**`extra.` keys.** An `anchor_keys[]` entry beginning with `extra.` never traces a number. Cite the non-`extra` key.

**Question references.** Refer to numbered questions in the handoff in words, for example "§11, question 2". Never write "Q2", because only hyphenated card ids such as `Q-005` are exempt from tracing. The cards themselves say "§11 Q2" in places; do not copy that form.

**Rounding.** Each number must equal the value of one of the claim's cited keys, rounded half-up to the decimals you show (13.65 shows as 13.7). Separated integers such as `284,862` trace. For document values, the check compares the normalised `value_exact` as a decimal.

## 3. Schema

`check_claims.py --schema` fails on an empty list. Every claim needs a non-empty `id`, `type`, `endpoint_status` and `statement`.

Each item has a fixed shape:
- A `required_qualifiers[]` item is `{text, discharge}`, where `discharge` is `sentence` or `scope_paragraph`.
- A `forbidden_wording[]` item is a string, or `{text, conditional_on: {q_card, outcome}}`.

## 4. Evidence files

`W/evidence/anchors.json` and `W/evidence/document_values.json` are cross-checked by gates P1:G1 and P1:G2. ORCH records those gates after the checker's final re-review.

Before dispatching you, ORCH verified the evidence independently:
- Two independent anchor computations (`anchors.json` and `independent/anchors_B.json`) agree on all 204 required keys of `ANCHOR_SPEC.md`, and both scripts reproduce their outputs when re-run.
- `anchors.json` also carries a few `extra.*` context keys that only builder A computed. They were never cross-checked, which is one more reason they never trace a number.
- Two blind extractions agree on all 33 document values, which ORCH merged; `prov.tail_unused` is derived from them (Q-013).

Use the evidence as follows:
- Use only keys that exist in those files.
- An `extra.*` anchor may be cited as context, never as the trace of a number.
- If the later gate runs change any value, ORCH routes the affected claims back to you.

## 5. Text and quotes

When a claim quotes the companion or the supplement, quote verbatim (Q-015) and give a `path:line` locator.

## 6. Git, tools and self-check

- Run no git command (U8). Run Python with `-B`.
- Do not run `W/tools/check_claims.py`: seq 39 is editing it while you work.
- For a self-check, run the frozen copy `C:\Users\ebelul\AppData\Local\Temp\2\p1reg\check_claims_seq31.py` with `--root C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`, in the default mode and with `--schema`. Its results are advisory: where it is looser than section 2 (years, half-up rounding, range units), section 2 wins. Write nothing into `p1reg`.
- Write only `W/evidence/claims.json`, `W/evidence/claims.md` and `W/evidence/interpretation_errata.md`.
- Do not read anything under `C:\Users\ebelul\AppData\Local\Temp\2\claude\`.
