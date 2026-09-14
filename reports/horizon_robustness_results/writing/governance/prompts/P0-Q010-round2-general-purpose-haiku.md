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

# Ballot brief: Q-010, ADP-3, round 2 (debate) for A-001, A-002 and A-003

**Your seat:** `general-purpose/haiku` (seat `red`, slice `S2`), the same seat and evidence slice you had in round 1. You are read-only; return one ballot per addendum in reply.

**Status:** A-004 was adopted unanimously in round 1 and is not re-voted.

**Rules for this round (plan §4.3):**
- The arguments below are anonymised, and no vote counts are shown.
- For each addendum, rebut or concede **each** strongest opposing reason, state what changed your mind (or "none"), then vote.
- You may vote for any option listed, including options that were added in this round.

**Chair notes, from ORCH's locator checks:**
- INV-11 (plan:421) requires both a DR and a new code-reviewer review before rule-table changes, but does not say in which order. Adopting an addendum in a DR does not itself change the checker. Option A-001 (b3) makes the effective date explicit.
- Plan:248 reads "a finding against it is rejected only by an independent confirmer or by an ADP-3". Plan:250 reads "Panels mix at least two families" and sits in the paragraph on panels.
- Second-chair check (seq 12, general-purpose/sonnet, `governance/results/P0-012-Q010-second-chair-general-purpose-sonnet.md`) of the premise "panels mix at least two families (plan:250) makes an opus critic of an opus-built register a violation": **FALSE**. Plan:250 governs decision panels; plan:242 lists panel seats and BCL critics as separate categories; results-integrity-reviewer/opus and general-purpose/opus are different identities (plan:56); the P1 step 8 critic set spans opus and sonnet after the reseat; the builder rule (plan:241) forbids same identity, not a shared family.

## A-001: governance format and rule-table extensions

**Options**
- **(a)** Adopt as drafted.
- **(b1)** Adopt with amendment S1. In item 6, the DR must be panel ADP-3.
- **(b2)** Adopt with amendment S3:
  - Item 2 waiver: a `condition` field must be present and must hold. For protected-source waivers it holds only when `exit_code` is 1 and the stored output consists of exactly one `MODIFIED protected file: <f>` line per covered file, with no other line.
  - Item 10: a correction is matched on (`seq`, `event`). A `completed` event carries `self_reported_model` as a string or as `"not reported"`.
- **(b3)** Adopt with S1, S3 and R. R reads: "The rule-table changes take effect only after the code-reviewer re-review of the fix round returns VERDICT: PASS; until then P0:G4 cannot be recorded MET." R was added this round from a round-1 objection.
- **(c)** Reject. Fix the code first and re-propose after a passing code review.

**Arguments made in round 1**
- *For S1:* plan:248 names only ADP-3 for this route, and the conformance review's own fix says ADP-3. Adding ADP-5 widens the route with no stated reason.
- *For S3:*
  - The P0:G2 waiver record has no `condition` field (`gates/P0-G2.json:14-20`), and `check_governance.py` has no waiver handling.
  - The drafted test "names only the covered files" also passes on an output that names no file at all, for example `DETECTOR BROKEN` with exit 2 (`tools/horizon_robustness/check_protected_sources.py:46-48`). That is an empty pass, which plan:408 forbids.
  - The log has two events per seq, so a correction keyed on seq alone is ambiguous.
  - `self_reported_model` is null on completed events.
- *For (c):*
  - The code review found BLOCKING flaws in the enforcement logic itself: F1, F2, F5 and F6.
  - The new record types depend on a working rule table.
  - INV-11 requires a new code review for changes to that table, so adopting first is premature.
- *For (a):* items 1–10 map one-to-one onto verified defects, and adopting them verbatim is fastest.

## A-002: carry U5 into the P9 re-run of `check_protected_sources`

**Options**
- **(a)** Adopt as drafted.
- **(b1)** Adopt with amendment H: "U5 establishes the baseline files (IJSSOL only) as authority across the entire run under plan §0 precedence. The P9 step 1 re-run applies that authority: protected-source records are UNMET with waiver U5 if the output lists only the IJPR files; any other file triggers H7."
- **(b2)** Adopt with amendment O. The P9 waiver is valid if and only if all three hold:
  - (i) `exit_code` is 1;
  - (ii) the output is exactly the two lines `MODIFIED protected file: IJPR_CSLAP_v4.tex` and `MODIFIED protected file: IJPR_CSLAP_v4_supplementary.tex`, in either order, with no other line;
  - (iii) the `check_inputs.py` record of the same P9 run is MET.

  Any other `MODIFIED` or `MISSING` line, or a `check_inputs` failure, triggers H7. Any other output leaves the record UNMET with no waiver, and H8 applies.
- **(b3)** Adopt with H and O together. Added this round.
- **(c)** Reject.

**Arguments made in round 1**
- *For (a):* the condition is copied from the user's own list of consequences (`user_decisions.md:24-27`). A-001 item 8 lets gate records cite U numbers. Rejecting brings H8 on a matter the user has already decided.
- *For H:* U5 names only P0:G2. Carrying it to P9 is an expansion unless U5's authority is stated to be global.
- *For O:*
  - The drafted test passes when no file is listed, for example on `DETECTOR BROKEN` or on a crash.
  - The prior-study ledger reports both IJPR files as modified whatever their content, so a new edit after P0 would still satisfy the waiver.
  - Under U5, protection rests on `check_inputs.py`, and both files are pinned. Condition (iii) carries out U5 rather than overriding it.
  - The P0 output the user waived is exactly those two lines (sha256 62cf6a5b…).

## A-003: identity-level reading of the P1 critic seats; diversity notes

**Options**
- **(a)** Adopt as drafted.
- **(b)** Adopt with amendment O. Replace note 2 with: "ORCH runs on Opus 5 and counts as family opus for §4.4. An independent confirmer or fix confirmer of an artifact ORCH built must come from an available non-opus family (default-seat table: 'family different from the builder'). If no non-opus family is available for the needed agent type, the finding goes to ADP-3."
- **(c)** Reject.
- **(d)** Reseat the P1 critic `results-integrity-reviewer`/opus to an agent type from a non-opus family under the §4.4 reseat rule. Proposed in round 1.

**Disclosure:** one voter's identity holds the critic seat this addendum confirms.

**Arguments made in round 1**
- *For (a):*
  - The plan's own P1 roster (plan:587-589) pairs a `results-integrity-reviewer`/opus critic with a `general-purpose`/opus register builder.
  - The reseat rule's family test applies only to reseats (plan:241-245).
  - The family-difference language at plan:288 is scoped to the independent-confirmer row.
- *For (b):* note 2 says only that ORCH "prefers" non-opus confirmers, which weakens plan:288's requirement for confirmers. ORCH is Opus 5, and sonnet and haiku are both available.
- *For (c) and (d):* identity includes family (plan:56), and panels mix at least two families (plan:250). The plan contains no exception for planned seats, so two opus seats are a violation.

## Ballot format (one block per addendum)

```
BALLOT  Q-010/<A-00x>  voter: <identity>  round: 2  seat: <plain|red>  slice: <S#>
POSITION: <option id>
REBUTTALS: <opposing reason> -> <rebuttal or concession> [locator]   (one line per strongest opposing reason)
WHAT CHANGED MY MIND: <argument> | none
RED CASE (red seat only): ...
BLOCKING OBJECTION: none | <checkable claim> [locator]
CONFIDENCE: low | medium | high
```

Keep the whole reply under 900 words.


## Re-poll notice for your A-003 ballot (plan §4.3 chair verification item 1)

Your round-1 A-003 ballot (seq 10) was ruled **invalid**: its decisive premise was checked blind by the second chair (see chair notes) and found false. You are re-polled once with this correction. Vote A-003 again among (a), (b), (c), (d) with reasons that do not rest on that premise. A second invalid A-003 ballot is discarded. Your red-seat duty for this round: write the RED CASE against the leading option for each of A-001, A-002 and A-003.
