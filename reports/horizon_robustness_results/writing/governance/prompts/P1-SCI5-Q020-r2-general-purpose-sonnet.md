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

# Ballot brief: Q-020, SCI-5 (ADP-5), round 2 (debate)

**Your seat:** `general-purpose/sonnet`, seat 5 of 5, role `plain`, evidence slice S5. You are **read-only**: write nothing and return one ballot in reply.

**Your own round 1 ballot:** `reports/horizon_robustness_results/writing/governance/results/P1-055-SCI5-Q020-r1-general-purpose-sonnet.md` (Argument 2 below). You may reread it.

**Re-poll (plan §4.3 chair verification, item 1).** Your round 1 ballot is Argument 2. Its decisive premise (reason 1) failed verification, as stated under *Chair verification of round 1*. This round 2 ballot is your single re-poll with that correction. Your round 1 ballot counts as invalid unless the second chair finds the premise true.

## The card and the options now open

`W/governance/questions/Q-020.md` asks how claim C-17 should classify the held-out misses of the arms without a reserved margin. Round 1 proposed missing options, which ORCH has added, as plan §4.3 requires. The options now open, in the card's own order:

Options, most to least conservative (or UNORDERED): (b) classify the held-out misses of each arm without a reserved margin (NOM and HIST+ACT) as a genuine failure of that arm's no-margin design; (c) classify only HIST+ACT's held-out misses as a genuine failure of scenario-and-activation protection without a reserved margin, and keep NOM's misses as an empirical limitation, the contrast given by the unprotected (0,0) control [added for round 2]; (e) classify NOM's held-out misses as a demonstrated boundary condition of its single-point modelled set without a margin, and HIST+ACT's as an empirical or experimental limitation [added for round 2]; (a) as written in C-17, with no result classified as a genuine failure; (d) keep HIST+ACT's held-out misses as an empirical limitation stated with all five reviewer-first §XII answers (what failed, under which conditions, the explanation marked hypothetical, the experiment that would resolve it, not run), and remove NOM's misses from the negative-result classification, reporting them under C-03 as the contrast given by the unprotected control [added for round 2]

The order over all five options is ORCH's proposal and is being confirmed by a non-opus confirmer in parallel with you. Only (b) over (a) was confirmed before round 1.

## Round 2 rules (plan §4.3)

- You see the round 1 arguments anonymised, and not the counts.
- Rebut or concede **every** strongest opposing reason, naming the argument number.
- Say what changed your mind, or write "none".
- Vote again among (a) to (e).
- Every reason carries a locator (`path:line`, table and row, or anchor key). ORCH opens every locator; a ballot whose decisive premise is false is invalid.
- A demand for new solves, extra seeds, significance tests, confidence intervals, a λ frontier or a graph build is out of scope and is rejected.
- Write nothing. Run no git command (U8). Use Bash, if you have it, only for read-only inspection with `python -B`. Do not read anything under `C:\Users\ebelul\AppData\Local\Temp\2\`. Never read `IJPR_CSLAP_*` files. Do not open other voters' round 1 ballot files in `W/governance/results/`; use the anonymised arguments below.

`W` = `reports/horizon_robustness_results/writing`. Repository root: `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`.

## Common core evidence (every seat)

- `W/governance/questions/Q-020.md`, and claim C-17 in `W/evidence/claims.json` (every field).
- `.claude/skills/reviewer_first_skill/SKILL_Academic_Manuscript_Architect_and_Critical_Reviewer.md` §XII, lines 558 to 598.
- The BCL round 2 critic replies: `W/governance/results/P1-043-critic-results-integrity.md`, `P1-044-critic-redteam.md`, `P1-045-critic-blueteam.md`.
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` §9.2 and §9.3 (lines 411 to 466).
- `W/evidence/anchors.json`, including the keys added after round 1 (below).

## Chair verification of round 1

- ORCH opened the locators of all five round 1 arguments.
- **Argument 2: its decisive premise failed verification.** It holds that the cause of the HIST+ACT misses is "anchored, not uncertain" because the returned layouts used their whole training allowance and the future fell below the modelled set. Both facts also hold for arms that passed on every seed: `ho.min_slack.TIGHT.*` and `ho.min_slack.HIST_ACT_T.*` (0.009992 to 0.009999, the whole tightened allowance), and `ho.departures.HIST_ACT_T.*.below` (2 to 4 stations). A second chair re-checks this premise blind in parallel with you, and the argument's author is re-polled in this round. Weigh Argument 2 without that premise.
- The other arguments' decisive premises were verified.

## Anchors added after round 1 (finding F-078; two independent builders agree)

Largest breach beyond the band by direction, per seed, in percentage points (`ho.breach.<ARM>.<SEED>.cap_worst` and `.floor_worst`). TIGHT and HIST+ACT-T are 0 on both sides for every seed.

  | Arm | Seed | Above the cap | Below the floor |
  |---|---|---|---|
  | NOM | s11 | 1.006 | 0.178 |
  | NOM | s22 | 0.939 | 0.233 |
  | NOM | s33 | 1.144 | 0.167 |
  | HIST+ACT | s11 | 0.081 | 0.039 |
  | HIST+ACT | s22 | 0.085 | 0.179 |
  | HIST+ACT | s33 | 0.000 | 0.069 |

## Chair's locator notes on the critic arguments (unchanged from round 1)

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

## The round 1 arguments, anonymised

### Argument 1

REASONS:
1. C-23 states the guarantee is conditional on "the realised future product mix" lying in the declared uncertainty set, and explicitly: "nothing in the study establishes that a future lies in that set... observed compliance... is one realisation" (`W/evidence/claims.json` C-23 statement, line 818). A miss under scenario departure is inside this documented conditional scope, not an unmet intent of the tested design.
2. The chair's own correction to the red-team's F4(ii) states that zero training slack does not make a future breach "mechanically certain": outcome "depends on the realised shares (C-21, C-23)" (`<own round 1 brief>:110`). "Genuine failure" (SKILL §XII line 586: "did not work as intended") implies a design defect that fires deterministically when exercised; here the chair-verified premise is that the outcome is realisation-dependent, which is the definition of a boundary-condition/empirical reading, not a design failure.
3. My slice's C-11/C-12 show the model property that actually differentiates the factorial: the margin arms optimise to λδ = 0.01 against the same δ = 0.02 evaluation band, reserving ρ = (1−λ)δ headroom the no-margin arms never carry (`claims.json` C-11 statement, C-12 statement). C-04 shows every arm — margin and no-margin alike — exhausts its own declared training allowance (`ho.min_slack.*` 0.019997–0.019999 vs 0.009992–0.009999, lines 135–154), so "zero slack against own allowance" is common to all four arms and does not, by itself, uniquely explain the no-margin misses; what differs is the structural reserve, which is exactly boundary-condition territory (the assumption is "declared margin ρ≥0 covers the departure"; evidence shows where ρ=0 fails and ρ=0.01 does not).
4. C-01's required qualifier that "historical scenarios and activation are bundled... their separate contributions are not identified" (line 16) and C-03's required qualifier that the factorial "does not isolate the margin from solver and layout effects" (line 101) — quoted verbatim in the results-integrity chair note (brief line 129) — mean the causal account behind HIST+ACT's 0/3 specifically is not isolated. That is the defining condition of C-17's present "empirical limitation" bucket (SKILL §XII line 574: "the mechanism is uncertain"), not "genuine failure," which presupposes we know what was tested failed on its own terms.

STEELMAN: The results-integrity critic (P1-043) argues the immediate cause is anchored, not uncertain — zero training slack (C-04) plus departure below the modelled set (`ho.departures.HIST_ACT.*.below`) — so calling it "empirical limitation" misstates the epistemic status, and reviewer-first line 586 ("did not work as intended") fits. This fails on my slice because the same critic's own closing line, echoed in the chair's note (brief line 129), concedes "what separates the passing arms from the failing ones is the reserved margin," and "C-03's own qualifier says the comparison does not isolate the margin from solver and layout effects" — i.e., the anchored fact (zero slack) is necessary but not sufficient; the full causal picture invoking scenario/activation bundling and solver/layout effects remains unisolated, which keeps the classification in empirical/experimental-limitation territory rather than a clean, intent-based failure.

On the confirmer's reworded (b) ("each arm... that arm's no-margin design," `.../results/P1-048-confirm-Q020-ordering.md:15`): this wording would not change my position. The per-arm framing is an improvement over a single "the no-margin policy," but my objection is not about the singular/plural wording — it is that neither arm's miss meets "did not work as intended" under my slice's evidence: NOM is a deliberately unprotected single-point control (C-11/C-12), and HIST+ACT's miss cannot be attributed to its own design in isolation from margin/solver/layout confounds (C-01, C-03).

BLOCKING OBJECTION: none

PROPOSED MISSING OPTION: (c) treat NOM and HIST+ACT asymmetrically — NOM under "demonstrated boundary condition" (single-point declared set, zero-margin control, per C-11/C-12), HIST+ACT under "empirical limitation"/"experimental limitation" pending isolation of scenario/activation from margin and solver effects (per C-01, C-03) — because the chair's own corrected table (brief lines 113–124) shows HIST+ACT departed its modelled range far less than TIGHT (3–4/0–3 vs 12–13/11–12) yet failed where TIGHT passed, which is a materially different pattern from NOM's and the binary card forces one label onto both.


WOULD CHANGE MY MIND: An anchor isolating the margin's causal contribution from scenario/activation bundling and solver/layout effects specifically for HIST+ACT (already-computed, no new solve) that showed the miss recurs under matched margin with scenarios/activation held fixed; or a DR precedent establishing that reviewer-first's "genuine failure" bucket is meant to apply to deliberately-designed no-margin control/ablation arms, not only to the paper's primary tested method (TIGHT).

### Argument 2

REASONS:
1. The mechanism is anchored, not uncertain, which rules out "empirical limitation" (reviewer-first §XII line 574: reserved for cases where "the mechanism is uncertain") and fits "genuine failure" (line 586, "did not work as intended"): results-integrity's Q-020 finding names two anchored facts — every no-margin held-out layout used essentially its whole training allowance (`ho.min_slack.HIST_ACT.*` 0.019997–0.019999) and the future fell below the modelled set at 3–4 stations (`ho.departures.HIST_ACT.*.below`) [`reports/horizon_robustness_results/writing/governance/results/P1-043-critic-results-integrity.md:35-39`].
2. What separates pass from fail in this factorial is the reserved margin, not set-departure severity: the chair's corrected table shows TIGHT departed its modelled range about as often as NOM (12-13 of 24) yet passed on every seed, while HIST+ACT departed rarely (3-4 of 24) yet failed on every seed [ballot brief, Chair's locator notes, blue-team item table, lines 113-124]. This directly undercuts folding the no-margin misses into "demonstrated boundary condition," which would predict the outcome from set-departure alone and cannot explain TIGHT.
3. The pattern holds within each scenario group, isolating margin from scenario/activation: among no-scenario arms, NOM (no margin) misses 0/3 while TIGHT (margin) passes 3/3; among scenario arms, HIST+ACT (no margin) misses 0/3 while HIST+ACT-T (margin) passes 3/3 (`ho.pass.*.count`, cited in `W/governance/questions/Q-020.md` and C-17 `anchor_keys`). Reading this as a site manager (C-30, my slice): the operationally decisive fact is that designs without a reserved margin did not hold the band on any tested seed, regardless of scenarios/activation; "empirical limitation... mechanism not isolated" undersells that lesson.

STEELMAN: Blue-team's strongest case for (a) is that the robust guarantee is explicitly conditional on the future lying in the declared uncertainty set (C-23), and NOM's declared set is a single point, so departure is expected; naming the miss "genuine failure" could overstate a limitation C-23 already scopes away [`P1-045-critic-blueteam.md:3-10`]. It fails because the magnitude blue-team cites to support it ("departed... at three to six times the rate of the margin arms") does not match the anchors — TIGHT departs at essentially the same rate as NOM yet still passes — so set-departure is not doing the explanatory work blue-team's argument needs; the margin is [ballot brief, Chair's locator notes, blue-team item, lines 113-124].

BLOCKING OBJECTION: none

PROPOSED MISSING OPTION: none, but a reservation on scope: results-integrity's own Q-020 note supports (b) "for HIST+ACT, scoped to this case" and separately keeps "NOM is the unprotected control, not a method" [`P1-043-critic-results-integrity.md:33,39`]. The card's option (b) bundles NOM and HIST+ACT under one genuine-failure classification; [preference statement removed] because NOM's own design (no margin, no scenarios) still missed the band on every seed, and "genuine failure of that arm's no-margin design" does not claim NOM was ever a robustness method — forbidden wording already blocks "the method fails" and "a boundary condition of robust optimisation in general." This is the weakest part of my position.


WOULD CHANGE MY MIND: A locator showing NOM was predeclared solely as a non-evaluated reference arm, exempt from scoring against the compliance band (rather than an arm scored against it like the others) — that would make "genuine failure" the wrong frame for NOM specifically and would push me toward a split classification (not offered here) or, forced to choose, toward (a) with NOM folded into boundary condition and HIST+ACT kept separate.

On the confirmer's rewording (`P1-048-confirm-Q020-ordering.md`): the reworded option ("each arm's ... that arm's no-margin design," replacing the singular "the no-margin policy") does not change my position — [preference statement removed] as the card states it, and the clearer per-arm wording, if adopted, would if anything strengthen my vote: it removes the risk of readers conflating NOM and HIST+ACT into one unified "policy" and makes explicit that each arm's own no-margin design is judged on its own held-out record.

### Argument 3

REASONS:
1. **(b) applies "genuine failure" to arms that are not the method under test.** The skill defines a genuine failure as "The proposed method did not work as intended" [.claude/skills/reviewer_first_skill/SKILL_Academic_Manuscript_Architect_and_Critical_Reviewer.md:584-586].
   - At the held-out origin the frozen policy sets λ = 0.5 [reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md:440].
   - The predeclared primary endpoint concerns TIGHT [CAMPAIGN_PREDECLARATION.md:456-458; claims.json C-02, line 54].
   - NOM (0,0) and HIST+ACT (1,0) are the no-margin levels of a factorial built to ask "does explicitly reserving the margin explain compliance" [CAMPAIGN_PREDECLARATION.md:412-413, 417-423]. When the arms without a factor miss, that miss is the contrast the design measures. It is not the proposed method failing.
   - Even the critic who argues for (b) concedes "NOM is the unprotected control, not a method" [W/governance/results/P1-043-critic-results-integrity.md:39]. Yet (b), in both its card wording and the confirmer's rewording, still names NOM.
2. **The mechanism is uncertain, which is what "empirical limitation" requires** [SKILL:572-574].
   - The two facts offered as the anchored cause also hold for arms that passed. HIST+ACT-T and TIGHT also used essentially their whole tightened allowance, 0.009992 to 0.009999 [claims.json:135].
   - HIST+ACT-T had 2 to 4 stations below its modelled set [W/evidence/anchors.json:113, 123, 133].
   - TIGHT had 12 or 13 stations below and 11 or 12 above its modelled set [anchors.json:44-45, 54-55, 64-65], and still passed 3 of 3 seeds [anchors.json:66].
   - What separates passing from failing arms is the margin. C-03 requires the qualifier that the comparison "does not isolate the margin from solver and layout effects" [claims.json:101], and C-24 repeats it [claims.json:854].
   - A breach magnitude per direction is not anchored [claims.json:127].
   - Calling the misses a failure "of that arm's no-margin design" names the missing margin as the cause. That is the reverse of the forbidden "attributes compliance to the reserved margin" and "margin decides the pass" [claims.json:108, 110].
3. **Positioning against the companion (slice S3).**
   - The companion's abstract says that on held-out weeks "every station remaining inside its workload budget" [IJSSOL_CSLAP_v1.tex:66]. That budget is an upper limit of 110% of legacy load [IJSSOL_CSLAP_v1.tex:584], "the tolerance the site operates to" [IJSSOL_CSLAP_v1_supplementary.tex:533]. The companion already scopes its stability: it "may not carry to more volatile assortments" [IJSSOL_CSLAP_v1.tex:640].
   - The companion used a different extract [CAMPAIGN_PREDECLARATION.md:433-435].
   - If the unprotected nominal level is labelled a "genuine failure", a referee reading both papers can take it as a verdict on the companion's model. This evidence was never designed to deliver that verdict.
   - The reviewed plan places the negative results as "scope and mechanism are examined" and lists the contributions as the margin result and the diagnosis of a misspecified uncertainty set [WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:128-131, 135-137]. A no-margin method is not among them.

STEELMAN:
- **For (b):** both arms missed on 0 of 3 seeds [anchors.json:32, 100] and breached in both directions [claims.json:94]. The predeclaration commits that "A negative or mixed result is reported as such" [CAMPAIGN_PREDECLARATION.md:112]. The skill warns against turning negatives into boundary conditions and prefers maturity to "rhetorical rescue" [SKILL:562, 590].
- **Why it fails:**
  - Option (a) rescues nothing. C-17 does not call these misses a boundary condition; it lists them as negative results [claims.json:609, 612]. C-03 already requires "a small breach is still a miss of the declared policy" [claims.json:102].
  - The reporting commitment governs whether results are disclosed, not which category they belong to. The category "genuine failure" needs a proposed method that did not work as intended, and at this origin neither arm is that method.
  - I also reject the blue-team critic's route of treating the misses as a boundary condition [P1-045-critic-blueteam.md:10]. The chair's table shows set departure does not explain the misses: TIGHT departed as often as NOM and passed. C-21 also requires the qualifier "Leaving the modelled set is not a band violation" [claims.json:757].
- **Confirmer's rewording:** "each arm ... that arm's no-margin design" fixes the singular-policy ambiguity [P1-048-confirm-Q020-ordering.md:15]. It does not change my position, because it still labels the control level NOM a failure and still attributes the misses to the missing margin.

BLUE WORDING: "Empirical limitation: neither arm without a reserved margin, NOM or HIST+ACT, satisfied the two-sided band on any of the three held-out seeds, and both breached it in both directions. A small breach is still a miss of the declared policy. The layouts that passed had also used their whole training allowance and also had stations outside their modelled set, so what produced these misses is not isolated from solver and layout effects. Both arms are the no-margin levels of the predeclared factorial, whose primary endpoint concerned TIGHT, and their misses are reported as found."

Locators for the wording:
- "neither ... satisfied": anchors.json:32, 100
- both directions: claims.json:94
- small breach is still a miss: claims.json:102
- whole allowance used: claims.json:135
- stations outside the modelled set: anchors.json:44-65, 113-133
- not isolated: claims.json:101
- factorial levels and primary endpoint: CAMPAIGN_PREDECLARATION.md:417-423, 456-458
- reported as found: claims.json:618

BLOCKING OBJECTION: none

PROPOSED MISSING OPTION: (c) Classify only HIST+ACT's held-out misses as a genuine failure of scenario-and-activation protection without a reserved margin. NOM's misses stay in the empirical limitation as the contrast from the unprotected control. This separates the case the critic for (b) actually makes [P1-043-critic-results-integrity.md:33-39] from the NOM case, which that critic concedes. [preference statement removed]


WOULD CHANGE MY MIND: I would move to (c) for HIST+ACT if either of these is shown:
- a predeclaration or contribution text that presents HIST+ACT without a margin as a proposed protection method expected to satisfy the two-sided band out of sample, rather than as a factorial level;
- a verified exploratory-stage record that names HIST+ACT without a margin as the recommended policy before its misses were scored.

For NOM, nothing in the anchored evidence would move me, because it is the unprotected control by design [CAMPAIGN_PREDECLARATION.md:419-422].

### Argument 4

REASONS:
1. The miss is anchored, but its cause is not. "Genuine failure" says the method "did not work as intended" (`.claude/skills/reviewer_first_skill/SKILL_Academic_Manuscript_Architect_and_Critical_Reviewer.md:584-586`). "Empirical limitation" is for poor performance when "the mechanism is uncertain" (same file, :572-574). The two anchored facts offered as the cause of the misses also hold for the arms that passed:
   - **Allowance used.** All four arms used almost their whole training allowance. HIST+ACT needed 0.019997 to 0.019999 of 0.02, which is at least 99.98% (`ho.min_slack.HIST_ACT.s11/s22/s33`). TIGHT and HIST+ACT-T needed 0.009992 to 0.009999 of 0.01, which is at least 99.92% (`ho.min_slack.TIGHT.*`, `ho.min_slack.HIST_ACT_T.*`).
   - **Departures below the modelled set.** HIST+ACT had 3, 4 and 4 stations below its set (`ho.departures.HIST_ACT.*.below`). HIST+ACT-T had 2, 4 and 4 and passed on every seed (`ho.departures.HIST_ACT_T.*.below`). Counting both directions, HIST+ACT-T seed 22 has 4 + 1 = 5 departures and passed, while HIST+ACT seed 11 has 3 + 1 = 4 and failed.
   - **Solver gap.** The gap does not separate them either. All 12 held-out rows lie between 0.98452 and 0.98540 (`tables/case_frame.csv`, campaign ho3_20260913, column `gap`).
   - **What remains.** Only the margin factor separates the passing arms from the failing ones. C-03's qualifier says the comparison "does not isolate the margin from solver and layout effects" (`W/evidence/claims.json:101`). So the mechanism is uncertain, and §XII puts that under empirical limitation.

2. Option (b) names NOM, but NOM is the design's control cell, not a proposed method. The predeclared 2×2 defines NOM as (0,0), with no scenarios and no margin (`CAMPAIGN_PREDECLARATION.md:417-423`). The question the design asks is whether reserving the margin "explain[s] compliance" (:412-413). The only pass criterion was set for TIGHT (:456-458). The rest of the factorial reading is "secondary, descriptive" (:459). No held-out compliance intent was declared for NOM or HIST+ACT, so "did not work as intended" has nothing to measure against. Even the critic who argues for (b) concedes that "NOM is the unprotected control, not a method" (`W/governance/results/P1-043-critic-results-integrity.md:39`). The card's (b) still covers NOM (`W/governance/questions/Q-020.md:6`).

3. Option (a) does not soften the negative result, and (b)'s label claims a cause the register does not support.
   - **The miss is already stated in full.** C-03 states 0 of 3 against 3 of 3 and requires "a small breach is still a miss of the declared policy" (`claims.json:96,102`). C-17 requires "Negative and mixed results are reported as found" (`claims.json:618`). This meets the predeclared reporting commitment (`CAMPAIGN_PREDECLARATION.md:112`), so §XII's warning against "rhetorical rescue" (:590) is respected.
   - **"No-margin design" points to a cause.** A "failure of that arm's no-margin design" names the absent margin as the design fault. That comes close to the forbidden wordings "margin decides the pass" and "attributes compliance to the reserved margin" (`claims.json:105-110`).
   - **What (a) lets the paper say.** Under (a), whole-allowance use, departure from the set and the absent margin can each be reported as a hypothetical explanation, as §XII asks (:596-597).

STEELMAN: The strongest case for (b) concerns HIST+ACT, the scenario arm, and does not need NOM.
- **The pattern.** HIST+ACT never met the band on a held-out seed (`ho.pass.HIST_ACT.count` = 0). At the exploratory origin it passed 0, 1 and 0 of 3 horizons across the three δ campaigns, never pooled (`ts.berner.d01/d02/d03.pass.HIST_ACT.count`). Over the same campaigns TIGHT passed 3 of 3 at δ = 0.02 and δ = 0.03 (`ts.berner.d02/d03.pass.TIGHT.count`).
- **The referee's reading.** A referee could say a design that misses this consistently did not work, and that "empirical limitation" understates it.
- **Why it fails.** Consistency shows that the miss is real, and C-03 already reports it at full strength. It does not show that the design is at fault rather than the uncertainty set, which the future demonstrably left (C-21; `ho.departures.HIST_ACT.*`), or time-capped layouts (gap about 0.985).
- **The C-23 point.** C-23 limits the design's guarantee to futures inside the set (`claims.json:818`). "Did not work as intended" therefore claims more than the arm was built to deliver.

The red-team case for (b) rested on two premises the chair has corrected: that breach was "mechanically certain", and that "primary, data-supported" described an arm (chair notes; `CAMPAIGN_PREDECLARATION.md:363`).

The blue-team alternative of folding the misses into the boundary condition also fails, in the other direction. Its "three to six times" premise does not match the anchors (TIGHT 12 to 13 below, NOM 13 below). C-17 as written rightly keeps the misses out of that category (`claims.json:609,612`).

On the confirmer's rewording (`P1-048-confirm-Q020-ordering.md:15`): the card already carries it, and neither wording changes my vote. The reworded text still covers NOM, and "no-margin design" makes the causal implication in reason 3 sharper.

BLOCKING OBJECTION: none

PROPOSED MISSING OPTION: (b′) classify only HIST+ACT's held-out misses as a genuine failure of that arm, and keep NOM as the unprotected (0,0) control reported under empirical limitation. This is the strongest form of the opposing view (`P1-043-critic-results-integrity.md:33-39`), and the card does not offer it. [preference statement removed]


WOULD CHANGE MY MIND: Any of the following, without new solves.
- **A separating quantity.** An anchored quantity that separates all six failing held-out layouts from all six passing ones, other than the margin factor itself, and that is not open to C-03's solver and layout confound.
- **A declared intent.** A predeclared statement, in `CAMPAIGN_PREDECLARATION.md` §8 or §9 or in the reviewed plan, that HIST+ACT at ±δ without a margin was expected to hold the band on the held-out window, which would make "did not work as intended" testable.

For NOM alone, nothing in S1 would move me: its role as the (0,0) control is fixed by the design.

### Argument 5

REASONS: 1. A "genuine failure" needs a proposed method and a stated intention ("The proposed method did not work as intended", reviewer_first_skill §XII line 586). The no-margin cells at the held-out origin have neither. The only predeclared pass threshold is TIGHT's (CAMPAIGN_PREDECLARATION.md:456-458). The per-arm pass counts are a "secondary, descriptive" reading (lines 459-465). NOM is the "Nominal CSLAP extension" (reports/horizon_robustness_plan/PLAN.md:266), which is the (0,0) cell of the factorial (CAMPAIGN_PREDECLARATION.md:422-423). The paper is framed as a "bounded comparative case study" and no arm is proposed as the method (WRITING_EXECUTION_PLAN_REVIEWED_20260914.md:14, 124-131). Saying "did not work as intended" now would set the intention after the held-out window was scored.
2. The evidence fits §XII line 574 as written: poor results "under a tested configuration" with an uncertain mechanism. There is one frozen configuration (δ = 0.02, ν = 0.01, λ = 0.5), one origin and one horizon, and the three seeds "measure optimiser variability, not demand variability" (CAMPAIGN_PREDECLARATION.md:440-442, 464-465). Both candidate causes also hold for arms that passed:
   - the whole allowance was used: TIGHT and HIST+ACT-T 0.009992 to 0.009999 (claims.json:135);
   - stations fell below the modelled set: ho.departures.HIST_ACT_T.s11.below = 2 (anchors.json:113), and see the C-21 qualifier (claims.json:757).
   The remaining separating factor, the margin, is explicitly not isolated "from solver and layout effects" (claims.json:101). Every layout is time-capped (anchors.json:96, ho.gap.HIST_ACT.s33 = 0.98496). So §XII question 4 (line 597), "demonstrated or hypothetical?", gets the answer: hypothetical.
3. Option (a) is not a rhetorical rescue. C-17 already says "neither arm without a margin satisfied the band on any held-out seed" (claims.json:609). C-03 states 0/3 plainly (claims.json:96, 98) and adds "a small breach is still a miss of the declared policy" (claims.json:102). That meets the commitment at CAMPAIGN_PREDECLARATION.md:112. Option (b) adds a verdict, not a disclosure.
STEELMAN: The strongest reason for (b): each no-margin arm ran under a frozen policy and missed on every seed (anchors.json:32, 100). A referee will call 0/3 a failure, and "empirical limitation" can read as softening (P1-044:23; P1-043:33-38). It fails on two counts. First, the results-integrity premise that the cause is "anchored, not uncertain" is false, because both anchored facts also hold for arms that passed (chair note; claims.json:135; anchors.json:113). Second, bluntness does not decide the category; scope does. Line 586 says the design does not work, while the evidence covers one configuration at one origin with no frontier (CAMPAIGN_PREDECLARATION.md:464-466).
RED CASE (red seat only): The case against (b), which I expect to lead: two of three critics back it, and it is the conservative default (Q-020.md:8).
(i) "Failure of that arm's no-margin design" blames the miss on the missing margin. That is the reverse of the forbidden "margin decides the pass" and "attributes compliance to the reserved margin" (claims.json:108-110). It also contradicts C-03's required qualifier (claims.json:101). The handoff's own phrase "So the margin decides the pass" (EXPERIMENT_REVIEW_HANDOFF.md:1203) is exactly the reading the register had to forbid.
(ii) For NOM, "no-margin design" just names the control level. Calling the control's miss a genuine failure mixes up the contrast the factorial is built on (CAMPAIGN_PREDECLARATION.md:462-463) with a result about a method. The results-integrity critic concedes "NOM is the unprotected control, not a method" (P1-043:39).
(iii) HIST+ACT's shortfall is partial and tied to this configuration. The original plan's H1 expected scenario protection to reduce violations relative to NOM (PLAN.md:277). On the held-out window HIST+ACT had 2, 4 and 2 breaches per seed against NOM's 9, 8 and 6. Computation (cap_count + floor_count per seed): HIST+ACT 1+1, 2+2, 0+2; NOM 4+5, 4+4, 2+4 (EXPERIMENT_REVIEW_HANDOFF.md:1186, 1188). At the exploratory origin, reported separately and not pooled, HIST+ACT passed 1/3 at δ = 0.02 (anchors.json:183, ts.berner.d02.pass.HIST_ACT.count). "Did not work as intended" overstates this.
(iv) The confirmer's "each arm" rewording does not change my position. The original singular "the no-margin policy" (P1-048:15) would make point (ii) worse.
BLOCKING OBJECTION: none. Point (i) is serious, but it concerns an implied cause, not a literal forbidden string, so I do not claim it strikes (b).
PROPOSED MISSING OPTION: (c) Keep HIST+ACT's held-out misses as an empirical limitation, and have C-17 answer all five §XII questions (lines 594-598): what failed (the band, 0/3 seeds), under which conditions (one origin, δ = 0.02, λ = 0.5), the explanation (not isolated, so hypothetical), and which experiment would resolve it (named, not run). Remove NOM's misses from the negative-results classification and report them under C-03 as the contrast given by the unprotected control.
WOULD CHANGE MY MIND: Either of two things. (1) A predeclared statement, dated before the held-out solves, that HIST+ACT or either no-margin arm was expected to pass the two-sided band at origin 243,151. (2) A register decision that makes HIST+ACT the paper's proposed method. Either would make line 586 apply to HIST+ACT, though still not to NOM.

## Ballot, round 2 (Appendix B format)

```
BALLOT  Q-020  voter: <agent type>/<family>  round: 2  seat: <plain|red|blue>  slice: <S#>
POSITION: a | b | c | d | e
REBUTTALS AND CONCESSIONS: for each strongest reason that opposes your position: Argument <n>, the reason, then your rebuttal or concession [locator]
WHAT CHANGED MY MIND: none | <what, with locator>
REASONS: 1. ... [locator]  2. ... [locator]  3. ... [locator]
STEELMAN: the strongest reason for the option you rank second, and why it fails [locator]
RED CASE (red seat only): the strongest case against the option you expect to lead [locators]
BLUE WORDING (blue seat only): the strongest defensible C-17 wording for your position, within the evidence [locators]
BLOCKING OBJECTION: none | <checkable claim that an option breaks an invariant, a hard stop or the evidence> [locator]
SECOND PREFERENCE: <option>
CONFIDENCE: low | medium | high
```

Keep the reply under 1,200 words.
