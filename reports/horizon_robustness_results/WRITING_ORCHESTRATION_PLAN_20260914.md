# Orchestration plan: agent-written bounded comparative paper on the undated CSLAP extension

14 September 2026, revision 4. This revision follows seven review reports: one execution dry run, three red-team
rounds and three plan-gate rounds. Every finding was checked against the files before it was adopted or
rejected, and `PLAN_REVIEW_LEDGER_20260914.md` records each decision. This document is the execution contract for
the multi-agent run that starts at the user's go. It is an internal planning document, not manuscript prose.

## 0. Authority, precedence and user decisions

**User decisions of 14 September 2026.**
* **U1.** The extension is **not** prepared for Taylor & Francis. Publisher guidelines are not constraints for now.
  **Agents write the manuscript.** The goal is a well-crafted journal article written with submission in mind.
* **U2.** The submitted `IJSSOL_CSLAP_v1.tex` is supplied so that the extension stays **aligned** with the companion
  in content boundary, notation and **style**.
* **U3.** The user compiles on Overleaf. Agents concentrate on writing quality, gaps and the logical flow of the
  narrative, following the project's writing skills and agents.
* **U4.** After the go, agents execute. Questions are resolved inside the project by sub-agent debate and majority
  vote. ORCH evaluates sub-agent opinions critically rather than adopting them.

**Precedence.**
1. The user decisions above.
2. This document, for execution.
3. `WRITING_EXECUTION_PLAN_REVIEWED_20260914.md` (the *reviewed plan*), for scientific scope, claim corrections,
   forbidden claims, literature anchors, the mathematical preflight and the §5 role and skill overrides, except
   the items superseded below.
4. `WRITING_PLAN_20260914.md`, only where neither of the above speaks.

Corrections made after the go go to `W/governance/PLAN_ADDENDA.md`, and each needs a DR.

**Reviewed-plan items superseded by U1–U4.**

| Reviewed-plan item | Replaced by |
|---|---|
| §1 venue and policy gate; AI-drafting restriction | U1. The AI-use record stays truthful (§3). |
| §5 "prefer GPT-5.6 Terra" | Claude models through `Agent` overrides; P0 probes which families are available (§4.4). |
| §5 "at most three parallel assignments" | INV-9 |
| §5 override 5: REVISE_METHOD, REVISE_CODE and MORE_TESTING mean "stop and report"; three cycles, then back to the user | Those verdicts mean "weaken or scope out the claim". The run stops only at hard stops (§3). Cycles follow §4 and §6, with disclosure in the handoff. |
| §5 override 9: "current official venue rules" | No venue under U1. Style is calibrated against the companion (P5a). |
| §6 Step 2 gate: user approves framing, outline, venue and workflow | D4 |
| §6 Step 4: author-led drafting | P7 agent drafting |
| §6 Step 5: PDF compilation and inspection | U3. Static LaTeX checks only; PDFs are read only if the user returns one. |

Any other conflict: the stricter scientific constraint applies, and a Q-card is raised (§4).

**Abbreviations.**
* `W` = `reports/horizon_robustness_results/writing/` (new, tracked by git).
* `R` = `reports/horizon_robustness_results/`.
* `L` = `.unlazy/horizon-writing/`: the gate ledger, gitignored through `.unlazy/.gitignore`. Durable records are
  mirrored under `W/governance/`.
* `PY` = `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe`.
* `COMP` = `IJSSOL_CSLAP_v1.tex`.
* `ORCH` = the main Claude Code session. It dispatches every sub-agent, chairs every panel, saves every returned
  report and verifies every sub-agent claim. Sub-agents cannot spawn sub-agents.
* **Model family** = an `Agent` override name (`opus`, `fable`, `sonnet`, `haiku`) that is currently marked
  available (§4.4).
* **Identity** = agent type plus model family, within a phase.

---

## 1. Facts verified before the go

| # | Fact | Evidence | Consequence |
|---|---|---|---|
| F1 | There is no LaTeX engine and no Node.js on this host. The companion compiles on Overleaf only. | `Get-Command`; `manuscript_checks/README.md:57-59` | Static LaTeX checks only. Gates are Python scripts, each with a recorded exit code and output hash. |
| F2 | Root `COMP` (SHA-256 `441F7FD2…`, commit `aca7beb`, 13 Sep 17:56) differs from the baseline copy (`FBCF4731…`) by 302 insertions and 159 deletions. The two `.bib` copies are identical (`E3A949CA…`). | hashes, `git diff --no-index --stat` | D2 |
| F3 | Seven evidence and analysis files are modified but uncommitted. The two 14 Sep plans are untracked. | `git status` | D1 |
| F4 | `check_protected_sources.py` hashes only the files listed in `.unlazy/horizon-cslap/preserved_sources.json`. That list contains no IJSSOL file and nothing under `R/`. | ledger scan | INV-2: `check_inputs.py` is the only guard for the companion and for `R/`. |
| F5 | `make_analysis.py` writes through repository-rooted constants (lines 23, 31-33, 252, 369). Its `_aliases()` (line 47) reads the full export, including the forbidden tail. The scratchpad prefix (135 characters) plus campaign paths (up to 163) exceeds the 259-character limit. | source read; path lengths | INV-4: nothing is regenerated. Recorded reproductions are cited instead. |
| F6 | `tests/horizon_robustness/test_cplex.py:67` calls the native CPLEX `solve`. Handoff §8 line 696 claims the listed tests launch no solver. | source read | No tests are run. Recorded runs are cited. Line 696 goes to the errata. |
| F7 | The handoff contains two readings the reviewed plan rejects: §13.3 line 1205 and §12.6 line 1162. | read | Errata only. |
| F8 | `COMP:569` reports 26 stations and evaluates 24. | grep | The paper says "the 24 evaluated stations". |
| F9 | The export header is `PRODUCT;ORDER;QTY;STATION;BOX_ID`, with no date column. Chronology comes from numeric order IDs (`DATA_PROVENANCE.md:27`). | header read | The undated premise is a fact. On-site dates are `% AUTHOR-CONFIRM`. |
| F10 | In the held-out rows of `case_frame.csv`, `minimum_required_slack` is 0.019997–0.019999 for NOM and HIST+ACT, and 0.009992–0.009999 for TIGHT and HIST+ACT-T. Every solve has gap ≈ 0.985 and bound 11,517. | recomputed three times | Every returned layout consumes its whole training allowance, which becomes a display. Costs compare time-capped returned layouts. Gap and bound go in the supplement. |
| F11 | Largest absolute station deviation per seed, in pp (seeds 11/22/33): NOM 3.006/2.939/3.144; TIGHT 1.756/1.209/1.357; HIST+ACT 2.081/2.179/2.069; HIST+ACT-T 1.026/1.160/1.039. | recomputed three times | Report seed ranges. HIST+ACT-T (1.03–1.16) and TIGHT (1.21–1.76) do not overlap. |
| F12 | Upper-only rule, BERNER, δ = 0.01: HIST+ACT 2/3, TIGHT 0/3 (handoff 973-979). Two-sided rule: TIGHT 3/3, exploratory and held out. | read | Needs a reconciling claim and a reader question. |
| F13 | Companion style: British spelling; no em dashes in prose; lists at `COMP:82`, `90`, `635` and `728`, all in sections §XIX-A G7 forbids; percentage points spelled out; one-decimal percentages. The AI declaration (`COMP:750-751`) states language refinement only. | grep | P5a conflicts; §3 |
| F14 | Kit mismatches: IJPR specifications; `academic-writer.md:78` Option C (Wilcoxon); `academic-writer.md:28` Wilcoxon and 95 % CIs; read-only Bash in `results-integrity-reviewer.md:52`; `academic-researcher` and `positioning-reviewer` cannot write files and have no web or hash capability respectively; no project `dataviz` skill; `structure-review` targets an absent agent. | scans | Appendix A; §6 assignments |
| F15 | `manuscript_checks/ck.py` defines checks T0–T16 (docstring lines 10-26). Several are tied to the companion: T0 requires [H]; T2 reads `claims.tsv`; T3 is a rename; T4 and T13 compare with the companion baseline; T6 is companion-specific; T9 runs `git diff`; T10 checks the companion's method taxonomy; T1 and T14 carry companion lists. | read | P7 classifies every check. |
| F16 | `drift_survey.py:12-18` measures each historical block against the pooled history of the **same** prefix, so each block is inside its own reference. The future is measured against a reference that does not contain it. For block mass fraction w, TV(block, pooled) = (1 − w)·TV(block, rest) exactly. The stored reading "future 0.194956 above historical maximum 0.194411" reverses once w exceeds **w\* = 1 − 0.194411/0.194956 ≈ 0.0028**. With 11 tiling blocks of 21,874 orders in a 243,151-order prefix, w ≈ 0.09, and the corrected maximum is about 0.21. | source read; algebra; `drift_survey.csv:17` | Q-008 decisive test (P1). "Beyond the historical maximum", "substantial" and "despite" are forbidden unless that test supports them. |
| F17 | `dispersion_survey.py:11-13` also measures each block's station share against a pooled share whose history contains the block. The stored dispersion values cover only the exploratory origin 199,403: 1.6982 pp at n = P/2, 1.6291 at n = P, 1.4747 at n = 2P (rows 89-91). Like-for-like, with order-count w of 0.055 and 0.110, n = P/2 and n = P become about 1.80 and 1.83 pp. No held-out row exists. | source read; arithmetic | Margin-rule row: exploratory prefix only; both stored and like-for-like values; nothing about "this deployment". |
| F18 | Exact fields sit under `validation` with `*_exact` names (for example `minimum_required_slack_exact`). `case_frame.csv` carries `mean_visits_exact`. | JSON scan | Field names are discovered in P1, never assumed. |
| F19 | The predeclared endpoint label is "Replication endpoint (primary)" (`CAMPAIGN_PREDECLARATION.md:456`). | read | INV-5 label rule |
| F20 | `analysis_audit.md:35` scores 412 layouts; the reviewed plan (line 60) says 413. | read | Q-009 |
| F21 | During plan review on 14 Sep 2026, a `fable` dispatch failed with HTTP 429, out of usage credits. | dispatch result | §4.4 family-availability rule; H9 |

---

## 2. Decisions needed with the go

Reply "go with defaults", or name departures.

| ID | Decision | Default (recommended) | Alternative |
|---|---|---|---|
| D1 | Evidence baseline | **One local commit** before P0: the 7 modified files, the two 14 Sep plans, this plan and the review ledger, on `daily-robustness-cplex-run`. Then one local commit of `W/` at the ends of P4, P7 and P9. No push. | No commits; P0 hash-freezes the working tree. |
| D2 | Companion reference | Root `COMP`, its supplement and its `.bib` at `HEAD`. The baseline copy is recorded as pre-revision. | The user names or supplies the submitted files. |
| D3 | Blocked public pages | ORCH may retrieve **public** URLs through Apify web-fetch when a plain fetch returns 403, saved under `W/literature/fetched/`. Never used for private or repository content. | Blocked pages go to `retrieval_requests.md`. |
| D4 | Pauses | **Run end to end**, stopping only at hard stops. After P4, write `W/CHECKPOINT_A.md` and continue. | Pause after P4 for review before prose. |
| D5 | Plan-gate closure | Accept revision 4 without a fourth gate round. The final gate's only blocking gap was fixed exactly as that reviewer specified, and P0 step 7 runs `plan-reviewer` against this document again before any other work. | Run a fourth `plan-reviewer` round before the go. |

---

## 3. Ownership and hard stops

**Agents own the whole writing scope.** This covers:
* the evidence freeze, recomputation, and the claim, requirement and document-value registers;
* literature and derivations;
* the novelty and argument decisions, by panel;
* the canon and the blueprint;
* the evidence package;
* the manuscript, supplement, bibliography, title, abstract and captions;
* every review, gap hunt and prose pass;
* the handoff.

§4 resolves every question inside this scope.

**`% AUTHOR-CONFIRM` placeholders (non-blocking).**
* The author block, contributions, funding, conflicts, acknowledgements and data availability.
* The companion's reference text.
* Operational site statements that no project document records, such as whether the ±δ share rule is the
  operator's rule, or whether dates exist on site.

**AI declaration.** It states truthfully that AI agents drafted the manuscript under the authors' direction, with
the tools and models taken from `ai_use_record.md`, and that the authors verify the work and take responsibility.
Copying the companion's declaration, or any template, is forbidden.

**Hard stops. A vote never decides these.** ORCH stops the affected work, writes a package and asks the user.

| ID | Hard stop |
|---|---|
| H1 | Any solver, campaign or test run; evidence regeneration through the data loaders; choosing or re-choosing λ, δ, ν or a horizon; any read of retained orders at index ≥ 265,025. |
| H2 | Editing a protected source: every root-level `.tex` and `.bib` (companion, IJPR and the others); `manuscript_checks/baseline/`; predeclarations; campaign artifacts; `R/tables/`; `R/figures/`; manifests; solver and analysis code; tests; `manuscript_checks/`; handoff and review documents; this plan and the review ledger. Corrections go to `PLAN_ADDENDA.md`. |
| H3 | Submission, preprint or posting, or contact with any editor or journal. |
| H4 | The R2 verdict (declaring the study complete, publishable or accepted), or closing the `REPORT`/`R2` gates in `.unlazy/horizon-cslap/`. |
| H5 | Git operations beyond D1; software installation; non-public content sent to external services. |
| H6 | Novelty failure, triggered in the NOV-5 final round by (i) a chair-verified blocking objection against distinctness, or (ii) at least 2 valid ballots for option (c). |
| H7 | A pinned hash changes; recomputed evidence contradicts a headline claim; or a scientific BLOCKING finding is still open after the P8 delta round. |
| H8 | In any phase, a required runnable gate still fails after that phase's last BCL round **and** one targeted fix round. |
| H9 | Fewer than three model families are available (§4.4), so the identity rules cannot be satisfied. |

---

## 4. Question resolution and debate protocol

### 4.1 Q-cards

An agent that meets an ambiguity returns a Q-card (Appendix C) rather than guessing. ORCH files it under
`W/governance/questions/`.

Every card names a **decisive test**. When that test is a read or a recomputation, ORCH runs it before any vote,
and the card becomes Class E. The classes are:

| Class | Meaning |
|---|---|
| E | Settled by evidence |
| J | Judgment within scope |
| H | Hard stop |

On Class J cards, ORCH orders the options from most to least conservative. "Conservative" means *the smallest
wording that still states what was observed*. A non-ORCH agent confirms the ordering. Cards without such an order
are marked `UNORDERED`.

A rule written for a specific card in §6 overrides §4.3.

### 4.2 Class E: facts are checked, never voted

1. ORCH runs the decisive test.
2. If the result disagrees with an agent's claim, a different identity from another family re-derives it blind.
3. Two agreeing independent derivations close the card.
4. A persistent disagreement on a headline claim is H7. Otherwise the conservative reading is used and the card is
   listed in the handoff.

**Tolerances:**

| Comparison | Tolerance |
|---|---|
| Counts and exact rationals | Exact |
| Floats | 1e-12 relative |
| Against externally displayed values | Their displayed precision |

### 4.3 Class J: adversarial debate panel (ADP)

**Panel sizes.** A DR without a named panel is an ADP-3 decision.

| Size | Used for | Rounds |
|---|---|---|
| ADP-3 | Reversible, local choices: display details, internal wording, search scope, ck_ext classifications, rule-settled canon formatting, overlap justifications, blueprint and option imports | Round 1; round 2 only if round 1 is not unanimous |
| ADP-5 | Consequential choices: claim wording, novelty, argument, blueprint base, content-affecting canon conflicts, gap dispositions, readiness | Rounds 1 and 2 mandatory; round 3 without a strict majority |

**Round 1 (blind).**
* **Brief.** Each voter gets the Q-card, a common core evidence pack, one **primary evidence slice** of its own
  (for example tables only; companion and literature; predeclarations and handoff; a practitioner brief), and
  Appendix A.
* **Ballot (Appendix B).** Each voter returns:
  * its position, the three strongest reasons, and a locator for each;
  * a **steelman** of every option it rejects;
  * its confidence, and what would change its mind;
  * an optional blocking objection;
  * an optional **missing option**, which ORCH adds in round 2.
* **Role seats.** A red-team seat argues against the leading option. On wording and novelty cards, a blue-team
  seat writes the strongest defensible version. Both roles rotate by identity.

**Chair verification after each round** (recorded in the DR).
1. **Locators.** ORCH opens every locator. A ballot whose decisive premise is false is invalid.
   * A second chair (general-purpose, another family) re-checks that locator blind.
   * The voter is re-polled once with the correction.
   * A second invalid ballot is discarded.
   * The denominator is the number of valid ballots.
2. **Blocking objections.** Each one is verified. A verified objection strikes its option. An unverified one is
   recorded as dissent.
3. **Out-of-scope demands.** Requests for new solves, extra seeds, significance tests or confidence intervals over
   three optimizer seeds, a λ frontier, or graph builds are rejected. If a voter says a claim cannot stand without
   such work, the claim is **weakened**.
4. **Duplicates (round 1 only).** Two ballots with the same decisive premise and the same locator are duplicates.
   * The one with the higher `dispatch_log` sequence is replaced by a new voter of another family.
   * At most one replacement per panel. After that, duplicates count as one valid ballot.

**Round 2 (debate).** Voters see the anonymised arguments but not the counts. Each rebuts or concedes every
strongest opposing reason, names what changed its mind (or "none"), and votes again. If the ballot sets are
identical across rounds, a diversity note is logged.

**Decision rule.**
1. A strict majority of valid ballots wins.
2. With two options and no majority, go to step 4.
3. With three or more options and no majority, run a **top-two runoff**. Runoff slot ties are broken in this order:
   * by conservative order;
   * on `UNORDERED` cards, by round-1 valid ballots;
   * then by final-round counts;
   * then by ORCH's recorded pick.
4. Still no majority:
   * **Ordered cards** adopt the most conservative option.
   * **`UNORDERED` cards** go to a new ADP-3 with other voters.
   * **If that fails too**, the option with the most round-1 valid ballots wins, or ORCH's recorded pick if those
     tie. The card is listed in the handoff.

**Prose is never voted on.** It goes through the OCL rubric (§4.5).

**Decision record.** `W/governance/decisions/DR-###.md` (Appendix B). Unanimity does not waive chair verification.

### 4.4 Identity, seats, families and read-only enforcement

**Builders and reseating.** A builder never votes on, reviews, or confirms a fix to its own artifact. This covers
panel seats, BCL critics, independent confirmers and second chairs. To fill a seat after a collision, or when a
family is unavailable, try in this order and record the choice in the DR and the dispatch log:
1. The same agent type with an available family that built none of the artifacts under review in this phase.
2. Otherwise, another agent type with the needed tools, from such a family.

**ORCH-built artifacts.** When ORCH built the artifact (a register merge, the comparison matrix, a consolidation),
a finding against it is rejected only by an independent confirmer or by an ADP-3.

**Family mix.** Panels mix at least two families.

**Family availability.** The P0 probe marks families available. When a dispatch fails with a usage-limit or
unavailable-model error (F21), ORCH:
1. marks the family unavailable in `state.json`;
2. re-dispatches the same seat under the reseat rule;
3. logs both attempts.

A family can be re-probed at the next phase start. With fewer than three families available, the run hits H9.

**Read-only waves.**
1. ORCH writes the prompts, the dispatch-log entries and `state.json` `in_flight`.
2. It runs `check_governance.py --snapshot`, which hashes `W/` and `L/` and records `git status --porcelain`.
3. No writer runs during the wave.
4. When every agent has returned, `--compare` runs. Any change is reverted, and the affected ballot or report is
   voided.
5. Only then does ORCH save the results.

`check_inputs.py` separately covers the pinned `.claude/` files and the pinned code.

**Panels** (defaults; builders and unavailable families are substituted).

| Panel | Seats (agent type → family) | Rotating roles |
|---|---|---|
| **SCI-5** | results-integrity-reviewer → opus; scientific-reviewer → fable; formulation-reviewer → sonnet; positioning-reviewer → opus; general-purpose "practitioner reader" → haiku | red, blue |
| **NOV-5** | positioning-reviewer → opus; scientific-reviewer → sonnet; formulation-reviewer → fable; results-integrity-reviewer → opus; general-purpose "handling editor" → haiku | red, blue |
| **MATH-3** | formulation-reviewer → opus; code-reviewer → fable; general-purpose independent deriver → haiku | red |
| **PRES-3** | narrative-reviewer → opus; academic-prose-auditor → fable; results-integrity-reviewer → sonnet | red |
| **PRES-5** | PRES-3, plus scientific-reviewer → haiku and positioning-reviewer → sonnet | red, blue |
| **REF-3** | general-purpose referees, independent reports: optimization and robust optimization → opus; warehouse and logistics application → fable; empirical methodology and reproducibility → sonnet | none |

**Default seats.**

| Seat | Default |
|---|---|
| CRT reader 1 | general-purpose/haiku, fresh |
| CRT reader 2 | general-purpose/sonnet, fresh |
| RTP author | scientific-reviewer or general-purpose, from an available family that built none of the package's main artifacts |
| Independent confirmer | By artifact: results-integrity-reviewer (numbers, claims), formulation-reviewer (mathematics), positioning-reviewer (literature), narrative-reviewer (structure); family different from the builder |
| Blue-team critic | general-purpose from an available family that built none of the artifacts under review in this phase |
| Extra literature search | academic-researcher from an unused family |
| `code-reviewer` | Family different from the script author |
| Second chair | general-purpose, family different from the voters under check |

### 4.5 Loops

**BCL (builder–critic).**
1. The builder writes.
2. Critics return findings (Appendix E).
3. Each finding is confirmed or rejected, by ORCH or, for artifacts ORCH built, by an independent confirmer.
4. The builder fixes the confirmed findings.
5. The critic that raised a finding, or another critic, confirms the fix.

Add a blue-team critic where over-hedging is a risk. Each BCL ends when every BLOCKING and MAJOR finding is either
fixed and confirmed or rejected with evidence, and the phase gates pass. Default is 2 rounds, 3 where stated.
Remaining disputes go to an ADP. A runnable gate still failing after the last round gets one targeted fix round
(H8).

**DBR (double-blind reproduction).**
* Two identities from different families run **in parallel as read-only agents**. Each returns its script, output
  or derivation **in the reply** and writes nothing.
* ORCH saves both, re-runs every returned script and confirms the output is byte-identical.
* **Numeric pairs:** a match within §4.2 closes the pair; a mismatch goes to §4.2.
* **Non-numeric pairs:** the phase step's own resolution applies (P2 searches merge by DOI; P3 derivation
  differences go to MATH-3; P5b blueprints go to the NOV-5 base vote).

**OCL (prose option clash).**
1. Two or three writers from different families return alternatives in their replies, and ORCH saves them as
   `W/drafts/<passage>/<writer>.tex`.
2. Two non-author PRES-3 seats score each alternative on the rubric (Appendix G).
3. The highest total is adopted **whole**. A third judge breaks ties. Alternatives are never merged.
4. The red-team seat lists objections for the integrator.

The adoption is recorded in a DR.

**RTP (red-team pre-mortem).** Before the checkpoint and the handoff, the RTP author writes the strongest reasons to
reject the package, each with a locator. Every point must be fixed, rejected with evidence, or disclosed.

**CRT (cold-reader test).** Readers get the minimal preamble (Appendix A2) only.
* **Reader 1** follows reviewer-first §III verbatim: "Title → Abstract → Introduction → Mathematical model → Method
  overview → Main table/figure → Industrial or empirical validation → Conclusion". Headings and captions are a
  labelled addition. Reader 1 states the question, the result, and how the paper knows it.
* **Reader 2** reads everything and lists undefined terms, logical jumps and unanswered reader questions.
* **In P5b** the brief contains only the diagonal skeleton and the spine test.

Every mismatch with the spine, and every listed confusion, becomes a finding.

---

## 5. Global invariants

* **INV-1.** No solver, campaign, test, or new empirical data.
* **INV-2.** Protected sources are read-only. `PY W/tools/check_inputs.py` → `INPUTS UNCHANGED` covers every file
  pinned in P0:
  * every root-level `.tex` and `.bib`, and `manuscript_checks/`;
  * all of `R/` except `R/writing/`;
  * `tools/horizon_robustness/`, `Baselines/horizon_robustness/`, `Baselines/horizon_robustness_analysis/` and
    `tests/horizon_robustness/`;
  * the `.claude/` agent and skill files used;
  * this plan and the review ledger.
* **INV-3.** Numbers:
  * **Anchors** keep the exact artifact fields (F18); floats are for display only.
  * **Document-only values** go in `W/evidence/document_values.json` with `path:line`, extracted by DBR. Examples:
    companion percentages, predeclared parameters, provenance counts, audit counts, the 284,862 stream end.
  * **Keys.** Every register, table, figure, macro and manuscript number has a key in `anchors.json`,
    `numbers.json` or `document_values.json`, together with its source hash. Manuscript numbers are macros. Ratios
    are computed at full precision.
  * **Numeral scope** for manuscript checks: digit strings in prose outside `\cite`, `\ref`, `\eqref`, `\label`,
    mathematics, number macros, and table and TikZ bodies. The integers one to ten written as words are exempt.
* **INV-4.** Evidence writers never run.
  * **Reads.** The generator reads only `R/tables/*.csv`, case JSONs of the named campaigns, `anchors.json` and
    `document_values.json`.
  * **Imports.** stdlib, numpy, pandas, matplotlib and jsonschema only.
  * **Enforcement.** `check_determinism.py --imports` checks imports and every literal path passed to `open`,
    `read_csv`, `read_json` and `Path`.
  * **Scope.** Builders do not compute or display significance tests or confidence intervals over three optimizer
    seeds.
* **INV-5.** Claim discipline:
  * **Mapping.** Every claim-bearing sentence maps to a claim ID. No forbidden wording. Evidence status is always
    identifiable, and separated evidence is never pooled.
  * **Scope-once.** The experimental unit, the protocol, and what the study cannot identify are stated once at the
    head of Results and once in Limitations. The abstract and the conclusion each carry one qualifier clause (one
    held-out origin, three optimizer seeds). A required qualifier counts as discharged by its section's scope
    paragraph or by the claim's first assertion.
  * **Label rule.** The paper's own voice never says "replicated" or "independent replication". The predeclared
    label "Replication endpoint" may be quoted once, immediately followed by the qualifier that it tests the same
    policy at a later origin of the same stream, whose history contains the exploratory origin's data.
* **INV-6.** All manuscript text follows `W/governance/STYLE_CANON.md`.
* **INV-7.** No reused companion paragraphs. Inherited definitions are re-expressed briefly and cited.
  `overlap_scan.py` lists shared word n-grams with n ≥ 8. Equations, data-availability and disclosure blocks, and
  defined terms are whitelisted. Each remaining hit is rewritten or justified in an ADP-3 DR.
* **INV-8.** Privacy:
  * Station labels come only from the alias columns (`S_k`) or the Q-007 map.
  * Figures are written with matplotlib `svg.fonttype = 'none'` and `pdf.fonttype = 42`.
  * The writing anonymisation check scans SVG `<text>` and fails on any figure whose SVG has no text element.
  * Only public URLs leave the machine.
* **INV-9.** Ownership:
  * One writer per owned path set at a time.
  * `academic-writer`/opus integrates and owns the tagged source `W/manuscript/` and **drafts every manuscript
    section**. Critics named in P7 review but do not draft.
  * Anyone else edits `W/manuscript/` only through an **ownership handoff** logged in `state.json`: release, edit,
    `check_edit_invariants.py`, return.
  * Blind builders and OCL writers return content, and ORCH writes the files.
  * At most five read-only agents run at a time.
* **INV-10.** Records:
  * **Dispatch log.** Every dispatch appends to `W/governance/dispatch_log.jsonl`: sequence, timestamp, phase,
    wave, identity, self-reported model, prompt file, input hashes, allowed outputs, result file, status, and
    retries with their failure reasons.
  * **Prompts** go to `W/governance/prompts/`.
  * **Returned reports** are saved verbatim to `W/governance/results/` after the read-only `--compare` and before any
    verification, together with any agent-written scratch scripts.
  * **`ai_use_record.md`** is updated at every phase end.
* **INV-11.** Honest gates:
  * **Runnable gates.** A runnable gate is met only with exit code 0, its token present, and its hash recorded.
  * **Fixtures.** Every new check script accepts `--root <dir>` and has a fixture under `L/fixtures/<script>/` that
    seeds one fault and must fail.
  * **Exemptions.** Repository scripts (`check_protected_sources.py`, `verify_campaign.py`) are exempt, with the
    reason recorded.
  * **No empty passes.** No check passes while scanning zero items.
  * **`check_governance.py`** carries from P0 the full rule table. It fails when any of the following holds.
    * **(a)** A BLOCKING or MAJOR finding lacks a verification or a fix confirmer, or its verifier or confirmer has
      the builder's identity.
    * **(b)** ORCH rejected a finding against an ORCH-built artifact without an independent confirmer.
    * **(c)** A named non-ORCH voter, critic, verifier or confirmer has no dispatch-log entry with a saved result.
    * **(d)** A DR lacks ballots, chair checks, two families, or builder exclusion.
    * **(e)** A gate lacks its exit code and hash.
    * **(f)** A `PLAN_ADDENDA.md` entry has no DR.
    * **(g)** A phase rule (P3:G2, P5:G1, P5:G3, P8:G1, P9:G2) is unmet.
    * **(h)** A check script's author identity also built an artifact the script checks, or its reviewer shares the
      author's family.
    * **(i)** An absolute path created by the run is longer than 240 characters.
  * **Changes to the table** require a DR and a new `code-reviewer` review.
* **INV-12.** Reviewers and voters with Bash use it read-only.
* **INV-13.** Every check script is written by an identity other than the builder of the artifact it checks, and is
  reviewed by `code-reviewer` of a different family from its author. This includes `W/math/tools/` and the export
  script. Evidence generators belong to their builders.

---

## 6. Phases

**Execution model.** Phases run in sequence. Writers run one per path set; read-only and blind dispatches run in
parallel waves.

**Resume protocol.** Run it at every phase start, after every wave, and after any context compaction:
1. Read `L/PLAN.md`, the tails of `L/status.log` and `dispatch_log.jsonl`, `state.json`, `PLAN_ADDENDA.md`, and the
   open cards and DRs.
2. Run `check_inputs.py` and `check_governance.py`, if they exist.
3. Re-probe families marked unavailable.
4. Re-dispatch, once, each in-flight dispatch that has no saved result, after inspecting its partial outputs.

**Budget watch.** When a phase exceeds 1.5 times its estimate, record a note in the checkpoint or the handoff.

### P0 — Bootstrap and freeze (≈8–10 dispatches)

1. If D1 is authorised, make the baseline commit (Appendix F) and record `HEAD`.
2. Create `W/` (§7) and `L/` (`PLAN.md` from `.claude/skills/unlazy/templates/PLAN.md`, `GATES.md`, `gates/`,
   `fixtures/`, `status.log`). Write `W/governance/DISPATCH_PREAMBLE.md` (Appendix A),
   `W/governance/PREAMBLE_MINIMAL.md` (Appendix A2), an empty `PLAN_ADDENDA.md` and `state.json`.
3. **Model probe.** Send one tiny dispatch per override (opus, fable, sonnet, haiku). Record availability and each
   self-reported model in `state.json` and `W/governance/environment.md`, along with the interpreters, packages,
   the absence of TeX and Node, and D3. Seat defaults for the remaining steps follow the reseat rule (§4.4).
4. **Pins.** Write `W/governance/source_manifest.json`, with SHA-256, size and git blob id, covering:
   * every file in `R/` except `R/writing/`, including every case record of `ho3_20260913`, `ts_b01_20260912`,
     `ts_d02_20260912`, `ts_b03_20260912` and `screen_20260910`, and all of `R/tables/`;
   * every root-level `.tex` and `.bib`, and `manuscript_checks/` including `baseline/`;
   * `tools/horizon_robustness/`, `Baselines/horizon_robustness/`, `Baselines/horizon_robustness_analysis/` and
     `tests/horizon_robustness/`;
   * this plan and `PLAN_REVIEW_LEDGER_20260914.md`;
   * every `.claude/` agent and skill file used.
5. **Check-author wave.** `general-purpose`/sonnet writes `W/tools/check_inputs.py` and
   `W/tools/check_governance.py` (the full INV-11 rule table, including `--snapshot`, `--compare` and `--probe`),
   with fixtures. One fixture seeds an ORCH self-rejection, another a script-author collision. `code-reviewer`/fable
   reviews both.
6. **Existing checks.** Read the repository check scripts and record their tokens. Run `check_protected_sources.py`
   (scope as in F4) and `verify_campaign.py --all --authorization`; the loader is reached only through
   `--revalidate` (`verify_campaign.py:179`). Run no tests, no `--revalidate` and no regeneration. Cite recorded
   runs in `W/evidence/verification_inventory.md`.
7. **Plan conformance (BCL, 1 round).**
   * `plan-reviewer`/opus checks that `L/PLAN.md` and `L/GATES.md` implement this document and every adopted row of
     the review ledger. Appendix A redirects its escalation to ORCH.
   * `general-purpose`/haiku dry-runs the P1 briefs and confirms the argument-option format of Appendix D.
   * Corrections go to `PLAN_ADDENDA.md`, each with a DR.

Gates:
* **P0:G1** — CHECK `PY W/tools/check_inputs.py` → EXPECT `INPUTS UNCHANGED`.
* **P0:G2** — `check_protected_sources.py` → EXPECT the recorded token (fixture exempt).
* **P0:G3** — `verify_campaign.py --all --authorization` → EXPECT the recorded tokens (fixture exempt).
* **P0:G4** — CHECK `PY W/tools/check_governance.py` → EXPECT `GOVERNANCE CONSISTENT`.
* **P0:G5** — CHECK `PY W/tools/check_governance.py --probe` → EXPECT `MODEL FAMILIES AVAILABLE` (at least three
  families; otherwise H9).

### P1 — Evidence, document values, claims and requirements (≈16–20 dispatches)

**Builder identities in P1:** general-purpose/opus (anchors A, register); general-purpose/fable (anchors B, one
document-value extraction); general-purpose/haiku (the other extraction, the map); general-purpose/sonnet (check
scripts only).

1. **Check-author wave.** `general-purpose`/sonnet writes `compare_anchors.py` (with `--documents`) and
   `check_claims.py` (with `--schema`, `--coverage` and `--argument`, using the Appendix D argument-option format),
   plus fixtures. `code-reviewer`/fable reviews them.

2. **Anchors (DBR).** `general-purpose`/opus (A) and `general-purpose`/fable (B) each return a script that prints
   JSON, together with its output. ORCH saves A's pair as `W/tools/recompute_anchors.py` and
   `W/evidence/anchors.json`, and B's under `W/evidence/independent/`, then re-runs both.

   **Sources:**
   * tables: `R/tables/case_frame.csv`, `station_profile_industrial.csv`, `drift_survey.csv`,
     `dispersion_survey.csv` and the status tables;
   * case records: `ho3_20260913`, `ts_b01_20260912`, `ts_d02_20260912`, `ts_b03_20260912` and `screen_20260910`.

   **Required anchors:**
   * **Held-out outcomes:**
     * pass counts, and exact mean visits with every ratio between them;
     * savings against the incumbent as arm-level means over seeds (13.0–16.0 %), together with the single-run
       range;
     * the largest deviation per seed, with its range;
     * breach magnitudes by direction for the no-margin arms;
     * `minimum_required_slack` per case;
     * `gap` and `bound`;
     * incumbent visits and deviation.
   * **Drift and dispersion (F16, F17):**
     * the drift row (max, mean, p90, last, future), with the like-for-like correction: w\*, w by order count, and
       the corrected values;
     * the dispersion rows at 199,403, with their like-for-like values.
   * **Context:**
     * the F12 reconciliation quantities (margin size under each rule; breach directions in the two-sided cells),
       replacing the earlier "floor-breach counts" wording;
     * the analysed and superseded campaign lists;
     * scored versus non-returned denominators.

   **Cross-check scope.** Compare with the reviewed plan's held-out anchor table (lines 77-87) and the numeric
   statements of its §2 corrections table (lines 91-105), at displayed precision. A mismatch passes only with a
   closed Class E card **and** an errata entry.

3. **Document values (DBR).** `general-purpose`/haiku and `general-purpose`/fable each return extractions with
   `path:line`. ORCH writes `W/evidence/document_values.json` (recording both identities in `extracted_by[]`) and
   compares them. The extractions cover:
   * the companion's 13.7 %, 6.6 %, 7.4 % and its 110 % budget definition;
   * the predeclared δ, λ, ν, seeds, origin, horizon and budget;
   * 21,874 products, 24 evaluated stations, 5,899 and 15,975, and the stream end 284,862;
   * the unused tail, 284,862 − 265,025 = 19,837;
   * audit counts.

4. **Requirements map.** `general-purpose`/haiku writes `W/evidence/requirements_map.json`: one row per requirement,
   mapped to a claim ID or to a forbidden entry. Sources:
   * the reviewed plan's §2 table, its §3 data contract and "what carries over", and its §6 Step 4 lists;
   * `CAMPAIGN_PREDECLARATION.md` §5 and §9.4;
   * every adopted claim-bearing row of `PLAN_REVIEW_LEDGER_20260914.md`.

5. **Claim register.** `general-purpose`/opus writes `W/evidence/claims.json` (Appendix D) and `claims.md`,
   starting from C1–C8 of the first plan with the reviewed plan's corrections. Every row carries an explicit display
   rounding. Required rows:

| Claim | Type / status | Required content | Forbidden wording |
|---|---|---|---|
| Scenario trade-off | observation; additional descriptive | Seed ranges of largest deviation (F11) and of visits; +2.355907 % mean visits against TIGHT at the canon's rounding; returned-layout qualifier | identical profile to the incumbent; protection against other futures; a separate activation effect |
| Margin reading | observation; predeclared primary and secondary | 3/3 against 0/3, with the no-margin breach magnitudes (HIST+ACT 0.069–0.179 pp) | "isolated mechanism" as a causal law; "scenarios add nothing" |
| Mechanism | observation | Returned layouts use their whole training allowance (F10) | |
| Solver returns | scope | Time-capped layouts, gap ≈ 0.985, bound 11,517; costs compare returned layouts; supplement plus one main-text sentence | "optimal"; "cost of protection" as an exact quantity |
| Drift | context; additional descriptive | Product-level comparison with the F16 like-for-like correction per Q-008; the incumbent satisfied the band on that window | "difficult", "demanding", "stress test", "not an easy case", calibrated extremeness; "substantial", "despite" and "beyond the historical maximum" unless the Q-008 test supports them |
| Protocol | contribution relative to the companion | Order-indexed, horizon-conditioned protocol with a later held-out deployment; the held-out training prefix contains the exploratory origin's data and futures; INV-5 label rule | "novel methodology" unless P4 establishes it; "rolling-origin experiment"; "replicated" and "independent replication" in the paper's own voice |
| Margin rule | central limitation | No validated selection rule. On the exploratory prefix the incumbent's largest historical block deviation was 1.63 pp at n = P (1.70 at n = P/2) against a reference that contains the block, about 1.83 and 1.80 pp like-for-like; either way larger than the 1 pp reserved margin (F17) | "margins must come from station-level dispersion"; any dispersion statement about the held-out prefix |
| Target definition and incumbent headroom | assumption | Targets are the incumbent's historical shares (handoff §11 Q2), stated before any result; Q-005 | |
| Upper-only versus two-sided | interpretation | Margin sizes by rule and breach directions (F12) | |
| Model relation | definition | Visit objective and assignment retained; budget rows **replaced** by share-policy rows; shares are a constraint; equivalence to budgets under uniform scaling only | |
| Band shape | premise | Absolute band; a relative band was not studied | |
| Savings in context | context | 13.0–16.0 % by arm (arm-level means over three seeds; the single-run range is anchored) on the held-out window; not comparable with the companion's 6.6–7.4 % (different extract, stream, reference and restriction) | "improves on the companion's out-of-sample saving" |
| Synthetic evidence role | scope | Two-sided evidence covers four instances | "29 instances" in any two-sided statement |
| Unused tail | disclosure | 19,837 retained orders unused | |
| Trapped-activation correction | derivation | Zero impact on recorded results (handoff §6.8); supplement | |
| Negative results | limitation | Classified by reviewer-first §XII | |

6. **Errata.** `W/evidence/interpretation_errata.md` collects:
   * F6 line 696 and F7;
   * the layout count, showing both 412 (audit) and 413 (reviewed plan) until Q-009 closes;
   * every other rejected wording.

   `verification_inventory.md` separates checks re-run here from checks cited.

7. **Pre-seeded Q-cards.**
   * **Q-001:** resolved by F8.
   * **Q-002 (E):** what the companion's dated evaluation claims.
   * **Q-003 (E):** the in-reference effect, with the F16/F17 derivation.
   * **Q-004 (E/J):** the motivation for share preservation, resolved after P2.
   * **Q-005 (E):** incumbent headroom, from the stored `reference_evaluation` and `validation` fields; stated
     qualitatively if those are insufficient.
   * **Q-006:** resolved by F9, with `% AUTHOR-CONFIRM`.
   * **Q-007 (E):** the alias map, joining `station_index` to `reference_evaluation.assignment` indices.
   * **Q-008:** drift wording.
     * **Decisive test (Class E):** is the block mass fraction w greater than w\* ≈ 0.0028? Use w by line mass if
       the stored artifacts give it; otherwise w by order count (≈ 0.09), disclosed.
     * **If w > w\*:** the stored "beyond the maximum" reading is an artifact of the reference, and the Drift row's
       conditional forbidden wordings stay forbidden.
     * **Then:** SCI-5 chooses among wordings that state the tested observation.
   * **Q-009 (E):** 412 versus 413 layouts.

8. **BCL-2 on register, map and document values.** Critics: `results-integrity-reviewer`/opus,
   `scientific-reviewer`/fable (red team), and the blue team `general-purpose`/sonnet, which built none of these
   artifacts. Disputed wordings go to SCI-5.

Gates:
* **P1:G1** — CHECK `PY W/tools/compare_anchors.py` → EXPECT `ANCHORS CROSS-CHECK PASSED`.
* **P1:G2** — CHECK `PY W/tools/compare_anchors.py --documents` → EXPECT `DOCUMENT VALUES CROSS-CHECK PASSED`.
* **P1:G3** — CHECK `PY W/tools/check_claims.py` → EXPECT `CLAIMS TRACE PASSED`.
* **P1:G4** — CHECK `PY W/tools/check_claims.py --schema` → EXPECT `CLAIMS SCHEMA PASSED`.
* **P1:G5** — CHECK `PY W/tools/check_claims.py --coverage` → EXPECT `REQUIREMENTS COVERED`.
* **P1:G6** — CHECK `PY W/tools/check_governance.py` → EXPECT `GOVERNANCE CONSISTENT`.

### P2 — Literature and positioning (≈9–12 dispatches)

1. **Check-author wave.** `general-purpose`/haiku writes `check_sources.py` (with `--anchors`) and a fixture.
   `code-reviewer`/sonnet reviews it.

2. **Searches (DBR, parallel).** The two researchers **return** search logs and candidate records in their replies
   (they have no Write tool). ORCH saves `search_log_A.md` and `search_log_B.md`.
   * **Route A:** `academic-researcher`/opus searches by keyword and database (WebSearch, the Crossref and OpenAlex
     public APIs, publisher pages).
   * **Route B:** `academic-researcher`/fable searches the citation graph: backward from the companion keys
     `xie2021`, `tarczynski2023`, `mirzaei2021`, `vanheusden2022workload`, `boysen2023` and `vanGils2018` and from
     the anchors, then forward through OpenAlex.
   * **Anchors (primary versions):**
     * Winkelmann, Tolkmitt, Ulrich and Römer, *FSMJ* 37, 558–598 (2025), DOI 10.1007/s10696-024-09549-7, including
       §5.2 eqs (10)–(12) and §5.4;
     * Dündar, *Alphanumeric Journal* 13(1), 1–12 (2025), DOI 10.17093/alphanumeric.1670030;
     * Tashman (2000), DOI 10.1016/S0169-2070(00)00065-0.
   * **Topics:**
     * workload balancing in pick-and-pass, zone and robotic picking;
     * robust and data-driven storage assignment;
     * constraint tightening and safety margins;
     * data-driven uncertainty-set coverage;
     * scenario and sampled-constraint methods;
     * assignment and re-slotting under changing demand;
     * out-of-sample evaluation protocols;
     * absolute versus relative balance measures;
     * sources for Q-004.

3. **Merge.** ORCH merges by DOI into `W/literature/source_register.json` (Appendix D) and adds two further entries:
   * `own_submitted`: the companion, with ORCH-computed local SHA-256, `citation_level: full`, reference text marked
     `% AUTHOR-CONFIRM`, never described as published;
   * `software`: Hexaly and CPLEX as needed, with vendor URLs.

4. **Verification.** `academic-researcher`/sonnet returns a verification report per entry. ORCH records
   `metadata_verified`, `access` and `citation_level`:

   | `access` | `citation_level` |
   |---|---|
   | `FULL_TEXT` | `full` |
   | `ABSTRACT_ONLY` | `existence` (the work exists and addresses a topic) |
   | `UNRESOLVED` | `none` (never cited) |

   The `own_submitted` and `software` entries are confirmed by `positioning-reviewer`/haiku, working from ORCH's
   saved hash output and from the pages saved under `W/literature/fetched/`, because it has no Bash or web tools.

5. **Comparison matrix.** ORCH writes `W/literature/comparison_matrix.md`: the 8–15 closest works, seven dimensions,
   and the comparability limits. `positioning-reviewer`/sonnet confirms it independently.

6. **BCL-2.** Critic: `positioning-reviewer`/opus. Routed gaps get one extra search by `academic-researcher`/haiku,
   after which Q-004 is resolved.

7. If Winkelmann et al. §5.2 or §5.4 cannot be read in the journal version, describe only what was verified and
   list the gap in the handoff.

Gates:
* **P2:G1** — CHECK `PY W/tools/check_sources.py` → EXPECT `SOURCE REGISTER VALID`.
* **P2:G2** — CHECK `PY W/tools/check_sources.py --anchors` → EXPECT `ANCHORS ACCOUNTED`.
* **P2:G3** — `check_governance.py` → EXPECT `GOVERNANCE CONSISTENT`.

### P3 — Mathematical preflight, notation bridge, term whitelist (≈9–12 dispatches)

1. **Notation, model delta, whitelist.** `general-purpose`/opus works under the `mathematical-formulation`,
   `robust-modeling` and `algorithm-documentation` skills, with the reviewed plan's §5 overrides 1–3. It writes:
   * `W/math/notation_bridge.md`, with a collision audit: C_s is line capacity while ζ_s counts slots; V_s and T_s
     are context only; q, λ, n and the scenario indices are checked for clashes.
   * `W/math/model_delta.md`: what is retained, replaced and added, and the equivalence under uniform scaling.
   * `W/math/term_whitelist.md`: technical terms and stored metric names that prose rules must not flag, such as
     "robust", "robust counterpart", "tightening", "scenario", "novelty" (`station_novelty_count`), "framework" for
     the counterpart, and "significant" in its non-statistical sense if the canon allows it.

2. **Derivations (DBR, parallel, returned in reply).** `general-purpose`/fable and `general-purpose`/sonnet each
   return:
   * **(a)** both endpoints of the hull and activation set, including the lower trapped-activation indicator and
     the edge cases of preflight item 4;
   * **(b)** the integer-count restatement, with exact rational thresholds;
   * **(c)** the conditional U-membership guarantee, the sufficient TV bound, and why neither certifies the
     realised futures;
   * **(d)** set inclusion across nested horizons.

   ORCH saves the two returns as `derivation_A.md` and `derivation_B.md`. Differences go to MATH-3.

3. **Edge cases.** `general-purpose`/haiku writes `W/math/tools/enumerate_edge_cases.py` under INV-11 and INV-13. It
   brute-forces tiny fixtures with `fractions.Fraction` against `validation.py`, imported read-only (that module
   imports no solver, lines 9-14). A mutated-threshold fixture must fail. `code-reviewer`/sonnet reviews it.

4. **Method notes.** `general-purpose`/opus writes `W/math/method_notes.md`. Preflight items 1–8 are each answered
   or left explicitly open. The trapped-activation correction is marked for the supplement.

5. **BCL-2.** Critics: `formulation-reviewer`/fable, against the companion's model sections; `code-reviewer`/haiku,
   on the math-to-code mapping.

Gates:
* **P3:G1** — CHECK `PY W/math/tools/enumerate_edge_cases.py` → EXPECT `EDGE CASES AGREE`.
* **P3:G2** — CHECK `PY W/tools/check_governance.py` → EXPECT `GOVERNANCE CONSISTENT`. Requires either agreeing
  derivations or MATH-3 DRs, plus formulation PASS and code PASS.

### P4 — Overlap, novelty, argument, checkpoint (≈16–20 dispatches)

1. **Overlap.** `general-purpose`/sonnet writes `W/positioning/companion_overlap.md`.

2. **Two cases, returned in reply** (ORCH writes the files):
   * "section of the companion": `general-purpose`/opus → `case_section.md`;
   * "distinct paper": `academic-writer`/opus → `case_distinct.md`.

3. **Argument options, returned in reply.** ORCH writes `argument_option_X.md` plus the JSON sidecar
   `argument_option_X.json` (Appendix D). The three options:
   * **A**, methodological: `general-purpose`/fable;
   * **B**, operational and managerial: `academic-writer`/fable;
   * **C**, comparative evidence: `general-purpose`/sonnet, under the Option C override.

   Each option states the research question and spine (§I), the contribution hierarchy (§VI) with claim IDs, the
   displays it needs, and its strongest objections. A cold reader (`general-purpose`/haiku, minimal preamble)
   summarises each abstract plan in one sentence, and ORCH compares that summary with the option's spine.

4. **NOV-5 novelty.** This card's own rule overrides §4.3. Options: (a) full article, (b) research note, (c) not
   distinct.
   * H6 as in §3.
   * An (a)/(b) split with no majority resolves to (b), which gives a leaner P5b budget.
   * "Nobody else has measured this" is inadmissible.
   * The handling editor records journals plausibly in scope, for style calibration only.

5. **NOV-5 argument** (`UNORDERED`). One option wins. Named elements may be imported from the others, each by an
   ADP-3 DR.

6. **Checkpoint.** Update `ai_use_record.md`, run RTP, write `W/CHECKPOINT_A.md` (at most 3 pages), and continue
   under D4.

Gates:
* **P4:G1** — CHECK `PY W/tools/check_claims.py --argument` → EXPECT `ARGUMENT TRACE PASSED`. Checks:
  * the chosen option's JSON exists and is named in the DR;
  * its spine is non-empty;
  * every contribution has at least one claim ID;
  * every claim ID exists;
  * no contribution rests only on claims of type interpretation or recommendation.
* **P4:G2** — `check_governance.py` → EXPECT `GOVERNANCE CONSISTENT`.

### P5 — Style canon and architecture, before any prose (≈20–26 dispatches)

**P5a. Style canon**

1. **Measure the companion.** ORCH runs a one-off, read-only measurement of `COMP`: words per section, paragraph
   lengths, floats, list sites, spelling variants, number and percentage formats, citation commands. Script and
   output are saved under `W/governance/results/`. This is a measurement, not a gate.

2. **Write the canon.** `general-purpose`/opus writes `W/governance/STYLE_CANON.md` in five parts.

   **Part 1 — the companion's style:** measured values, plus short verbatim examples with locators.

   **Part 2 — project rules, unioned and ranked, each with its source:**
   * reviewer-first §II–§XIX-A, §XXI, §XXIII;
   * `academic-writer`: banned words, transitions, punctuation, table pruning;
   * `clean-scientific-writer`: metaphor, table reciting, notation;
   * `academic-prose-auditor`: classes A–E;
   * `narrative-reviewer` §§1–5;
   * the adapter, R1–R8;
   * `humanizer-writer`, subordinate to the adapter;
   * OR-writing cross-cutting rules, without MSLAP/Savoye anchors or journal modes;
   * the exposition rules of `experimental-results-presentation`, `mathematical-formulation` and
     `algorithm-documentation`, excluding significance tests and CIs over three seeds;
   * the surviving `ck.py` rules.

   **Part 3 — conflicts.**
   * *Content-affecting conflicts 1–4: one batched ADP-5 (PRES-5).* Each voter returns one position per conflict,
     and voters may confirm or amend the proposed resolutions.
     1. Lists in contributions, Results and Conclusions: the companion uses them; §XIX-A G7 forbids them.
     2. Numbers in text: `academic-writer.md:64` versus §XI.2 and §XVII. Proposed: arm-level summaries once in the
        text, seeds in the table.
     3. The rule-of-three ban. Proposed: it applies to adjective triplets only.
     4. Hedging (`humanizer-writer` rule 24) versus required qualifiers. Proposed: the INV-5 scope-once rule.
   * *Formatting conflicts 5–8: settled by rule in one DR, then confirmed by one batched ADP-3 (PRES-3).*
     5. Numbers and percentages follow the companion (U2); "percentage points" is written out, and "pp" appears
        only in table notes, if at all.
     6. `--` is allowed in tables, TikZ, ranges and mathematics (adapter R6).
     7. [H] is not forced (U1); the companion's float macros are kept.
     8. `interact` is a placeholder class (U1).

   **Part 4 — soft section budgets,** derived from the measurement.

   **Part 5 — the P3 term whitelist,** frozen before P7.

3. **BCL-2.** Critics: `narrative-reviewer`/sonnet and `academic-prose-auditor`/fable. It closes with a PRES-3
   sign-off DR on completeness.

**P5b. Architecture blueprint** (reviewer-first §XXI Pass 7)

0. **Check-author wave.** `general-purpose`/haiku writes `check_blueprint.py` and a fixture; `code-reviewer`/fable
   reviews it. A paragraph *requires* a boundary when any of its claim IDs carries a required qualifier with
   `discharge: sentence`.

1. **Two blind blueprints (DBR, parallel, returned in reply).** `academic-writer`/opus and `general-purpose`/sonnet
   each return a blueprint (Appendix D), which ORCH writes as `blueprint_A` and `blueprint_B`, each as `.json` and
   `.md`. A blueprint contains:
   * the spine and research question from P4;
   * sections, each with purpose, soft budget and placement, plus the staged-design table;
   * a paragraph **plan** for each section. Each paragraph lists its topic claim, claim IDs, planned macros
     (`\hr` + group + arm + metric, letters only), displays, sources, uses and introduces, interpretation, and
     boundary (`discharged_by_scope_paragraph` is allowed);
   * the display plan, one message per display. It must include:
     * the held-out table with a minimum-slack column;
     * the per-station overlay of target, training envelope, realised share and band for the four arms (F10);
     * the §9.3 secondary metrics.

     The optional displays (δ response, horizon transfer) must be decided explicitly;
   * the diagonal skeleton, the limitations map (§XII), the evidence-role map (§XIII) and the discussion scope
     (§XIV);
   * a **spine test**: a drafted contribution paragraph and an abstract sentence plan.

2. **Mandatory reader questions:**
   * Why undated? (F9)
   * Why shares rather than budgets? (equivalence under uniform scaling; Q-004)
   * Does the incumbent have headroom? (Q-005)
   * Does the upper-only screen contradict the held-out result? (F12)
   * Why 13–16 % here versus 6.6–7.4 % in the companion?
   * What should a practitioner do? A tested policy still needing validation (§XIV): reserve part of the band, and
     check station-level history against the reserve before adopting a layout.
   * Why an absolute band?
   * What do three seeds mean?
   * What happened to the unused tail?
   * What do the synthetic instances show under the two-sided rule?
   * What does "cost" mean for time-capped layouts?
   * What does the study rule out, and what does it not?

3. **Base choice.** NOV-5 votes on the **base** blueprint. From the other blueprint, only display-plan entries and
   reader-question mappings may be imported, each by an ADP-3 DR. The base's architect writes `blueprint.json`.

4. **BCL-3.** Critics: `plan-reviewer`/fable (PLAN_SOLID; escalation goes to ORCH and SCI-5),
   `narrative-reviewer`/opus (passes 1–6 on the plan), `scientific-reviewer`/haiku (red team). CRT reader 1 then
   reads a skeleton-only brief.

Gates:
* **P5:G1** — `check_governance.py` → EXPECT `GOVERNANCE CONSISTENT`. Requires the canon DRs for conflicts 1–8 and
  the PRES-3 completeness sign-off.
* **P5:G2** — CHECK `PY W/tools/check_blueprint.py` → EXPECT `BLUEPRINT CHRONOLOGY PASSED`. Checks:
  * nothing is used before it is introduced;
  * every claim ID exists;
  * required boundaries are present;
  * every display has a message;
  * every mandatory question is mapped;
  * every limitation is located;
  * macro names follow the convention.
* **P5:G3** — `PLAN_SOLID`, or, after BCL-3, a SCI-5 DR that records the dissent.

### P6 — Evidence package, no new solves (≈10–14 dispatches)

1. **Build.** `general-purpose`/opus writes `W/tools/build_evidence.py` under INV-4 and INV-8, using the
   `experimental-results-presentation` skill (tables and figures only, with no significance tests or CIs). Outputs:
   * `numbers.json` and `numbers.tex`;
   * `tables/`: `\tbl` bodies plus CSV;
   * `figures/`: PDF, SVG with text, and PNG at 300 dpi;
   * `reproduce.md`.

   It covers the blueprint's displays and macros exactly, with at least:
   * the study-design table: six analysed campaigns, four superseded directories excluded, scored versus
     non-returned denominators;
   * the complete held-out table: seeds, compliance, breaches by direction, worst breach, largest deviation, minimum
     slack, visits, and the same-future incumbent;
   * cost against deviation for every returned seed layout, with no fitted frontier;
   * the station overlay with band in three seed facets (never a best seed or an averaged layout);
   * ex post envelope and TV diagnostics, with the F16 and F17 corrections;
   * the supplementary outcomes, including solver gap and bound.

2. **Check-author wave.** `general-purpose`/sonnet writes:
   * `check_determinism.py` (with `--imports`);
   * `check_numbers.py` (with `--coverage`);
   * `check_anonymisation_writing.py`, which imports `SITE_CODE`, `scan_text` and `scan_file` from
     `tools/horizon_robustness/check_anonymisation.py`, scans SVG `<text>` and PDF text, and fails on a figure with
     no text.

   `code-reviewer`/fable reviews them.

3. **BCL-2.**
   * `code-reviewer`/haiku reviews the generator.
   * `results-integrity-reviewer`/opus checks the outputs against `claims.json`, `anchors.json` and
     `document_values.json`.
   * `narrative-reviewer`/fable reviews economy of presentation and §XIX.
   * Disputes go to PRES-3.

4. **Visual inspection.** ORCH and `results-integrity-reviewer`/sonnet open every PNG at print size.

Gates:
* **P6:G1** — `check_determinism.py` → EXPECT `EVIDENCE DETERMINISTIC`.
* **P6:G2** — `check_determinism.py --imports` → EXPECT `GENERATOR IMPORTS ALLOWED`.
* **P6:G3** — `check_numbers.py` → EXPECT `NUMBERS TRACE PASSED`.
* **P6:G4** — `check_numbers.py --coverage` → EXPECT `DISPLAY AND MACRO COVERAGE PASSED`.
* **P6:G5** — `check_anonymisation_writing.py` → EXPECT `WRITING ANONYMISATION PASSED`.
* **P6:G6** — `check_governance.py` → EXPECT `GOVERNANCE CONSISTENT`.

### P7 — Drafting (≈70–90 dispatches)

**Before drafting (check-author wave).**
* **`ck_ext.py`.** `general-purpose`/sonnet writes `W/checks/ck_ext.py`, a copy of `manuscript_checks/ck.py`
  retargeted to `W/manuscript/`, together with `ck_ext_decisions.md`. The classification of T0–T16:

  | Action | Checks |
  |---|---|
  | **Drop** | T3 (rename), T4 and T13 (companion-baseline numerics), T6 (plateau derivation), T9 (git diff), T10 (companion method taxonomy) |
  | **Adapt** | T0 (per canon conflict 7), T1 (entities from the blueprint), T2 (`claims.json`, scope-once discharge, label rule), T5 (soft budgets), T8 (keep the comment, email and supplement-reference checks; drop journal boilerplate), T14 (notation from `notation_bridge.md` and `introduces[]`) |
  | **Keep** | T7, T11, T12, T15, T16 (notes only) |

  Every kept check fails on zero items and has a fixture. Token: `CK_EXT ALL PASSED`. PRES-3 reviews the
  classification; `code-reviewer`/opus reviews the code.
* **Other scripts.** `general-purpose`/haiku writes `check_manuscript_claims.py` (INV-3 numeral scope, INV-5 label
  rule), `check_latex_static.py`, `check_edit_invariants.py`, `overlap_scan.py` and `export_manuscript.py`, each with
  fixtures. `code-reviewer`/fable reviews them. `check_latex_static.py` checks:
  * environments are balanced;
  * every `\ref` and `\eqref` resolves;
  * cited keys are eligible, with `existence`-level keys listed for `positioning-reviewer`;
  * macros are defined;
  * graphics exist;
  * no command is undefined relative to the companion preamble.

**Integrator.** `academic-writer`/opus drafts every section, owns the **tagged source** `W/manuscript/`, and keeps the
tagging comments permanently:
* `main.tex`, following the companion's class and preamble conventions (the class comes from Overleaf);
* `supplement.tex`;
* `sections/*.tex`;
* `references.bib`, with eligible register entries only, reusing the companion's entry text and keys for the same
  works, copied rather than edited.

**Order.** `academic-writer`/opus drafts each item below. The names in each line are the **BCL-2 critics**; they do
not draft.
1. **Spine texts** from P5b: contribution paragraph and abstract plan. Provisional.
2. **Sections:**
   1. Decision problem and information boundary. Critic: `formulation-reviewer`/fable.
   2. Share-policy model, uncertainty sets, tightening, counterpart. Critics: `formulation-reviewer`/fable,
      `code-reviewer`/sonnet.
   3. Data, preprocessing, protocol and staged design, with the scope paragraph and non-comparability. Critic:
      `results-integrity-reviewer`/opus.
   4. Comparative evidence, held-out first, exploratory context identified. Critics:
      `results-integrity-reviewer`/opus and blue team `general-purpose`/fable.
   5. Interpretation, set-coverage diagnostics, operational meaning, limitations. Critics:
      `scientific-reviewer`/sonnet (red team) and blue team `general-purpose`/fable.
3. **Related work (§VII).** Critic: `positioning-reviewer`/opus. **Introduction (§V).** Critics:
   `positioning-reviewer`/opus and `narrative-reviewer`/sonnet.
4. **Conclusion; abstract, title and keywords; supplement; declarations** (`% AUTHOR-CONFIRM`).
5. **Revisit the spine texts.**

**Contested passages (OCL).** `academic-writer`/opus and `clean-scientific-writer`/fable each return an alternative:
* the introduction's first two paragraphs;
* the contribution paragraph;
* section 5's central interpretive paragraph;
* the abstract.

**Section rules.**
* Each claim-bearing paragraph ends with `% claims: C-..`. A deviation from the plan carries a `% deviation:` note.
* A section is **provisionally frozen** in `state.json` when its gate passes. P8 may reopen it.
* No prose audit is run per section.

Gates:
* **P7:G1** — `ck_ext.py all` → EXPECT `CK_EXT ALL PASSED`.
* **P7:G2** — `check_manuscript_claims.py` → EXPECT `MANUSCRIPT CLAIMS PASSED`.
* **P7:G3** — `check_latex_static.py` → EXPECT `LATEX STATIC PASSED`.
* **P7:G4** — `overlap_scan.py` → EXPECT `OVERLAP DISPOSITIONED`.
* **P7:G5** — `check_governance.py` → EXPECT `GOVERNANCE CONSISTENT`.

### P8 — Whole-manuscript convergence: gaps, logic flow, prose (≈40–60 dispatches)

**Rounds.**

| Round | What runs |
|---|---|
| Round 1 | Steps 1–7 in full |
| Round 2 | Steps 3–7 in full. Steps 1–2 re-run only if round 1 left an open BLOCKING or MAJOR structural or referee gap, and then only to confirm those fixes and flag new BLOCKING issues, using the same referee personas in fresh dispatches. |
| Delta round | Only the regions that changed |
| Targeted fix round | Only if an automated check is still failing |

**Steps.**

1. **Architecture audit.** `narrative-reviewer`/opus applies reviewer-first §XXI passes 1–7 plus the
   `paper-self-review` `SECTION-CHECKLIST.md`.

2. **Mock peer review.** The REF-3 referees receive `PREAMBLE_MINIMAL.md`, the manuscript, the supplement and web
   access, but never the registers or plans. Each uses `sparring-partner-review`, `paper-self-review` and OR-writing
   [A]/[D], and writes a summary, major and minor issues with locators, and a recommendation. ORCH consolidates the
   issues into `W/review/<round>/gap_register.md`:

   | Class | Meaning | Action |
   |---|---|---|
   | G-WRITE | Text fix | Integrator |
   | G-EVIDENCE | Answerable from existing artifacts | Generator update, then `check_determinism.py`, `check_numbers.py --coverage`, and a blueprint display update |
   | G-LIMITATION | Needs new work | Limitation or future work; never executed |
   | G-REJECT | Referee is wrong | Evidence recorded |

   `results-integrity-reviewer`/sonnet confirms the classifications. Disputes, and any G-LIMITATION a referee calls
   fatal, go to SCI-5.

3. **Science wave**, in parallel:
   * `results-integrity-reviewer`/opus: numbers and claims;
   * `formulation-reviewer`/fable: mathematics and notation;
   * `positioning-reviewer`/sonnet: every citation, against its locator and `citation_level`;
   * `scientific-reviewer`/sonnet: overclaiming and forbidden claims (red team);
   * `general-purpose`/haiku: over-hedging and buried findings (blue team).

4. **Integrator revision.** `academic-writer`/opus applies only confirmed findings and dispositioned gaps. Changing
   the spine or hierarchy requires a NOV-5 DR.

5. **Prose wave**, after the science findings are closed. `academic-prose-auditor`/fable (classes A–E, with the
   whitelist) and `narrative-reviewer`/sonnet (§§2–5, adapter in Detect-only mode) run. `clean-scientific-writer`/opus
   then applies fixes under an ownership handoff, guarded by `check_edit_invariants.py` → `EDIT INVARIANTS PASSED`.

6. **CRT.** Both readers, fresh.

7. **Automated suite:** `ck_ext.py all`, `check_manuscript_claims.py`, `check_numbers.py` (with `--coverage`),
   `overlap_scan.py`, `check_anonymisation_writing.py`, `check_latex_static.py`, `check_governance.py`.

**Convergence.** All of the following must hold in the same round:
* `scientific-reviewer` `STATUS: ACCEPTED`, read as soundness only;
* `NARRATIVE_VERDICT: ACCEPTED` from **both** narrative-reviewer identities, the architecture one (opus) and the
  prose one (sonnet);
* `academic-prose-auditor` `PROSE_VERDICT: ACCEPTED`;
* `VERDICT: PASS` from results integrity, formulation and positioning;
* no open BLOCKING or MAJOR gap;
* the automated suite green;
* CRT consistent with the spine.

**After the delta round.**
* Disputes go to ADPs.
* A failing automated check gets the targeted fix round; if it still fails, H8.
* An open scientific BLOCKING item is H7.
* Anything else is recorded as `P8_CONVERGED_WITH_DISCLOSURES`, with the list of open items, in `state.json`.

Gate **P8:G1**: the automated suite passes, and `check_governance.py` confirms the convergence or disclosure state.

### P9 — Final verification, export, handoff (≈8–10 dispatches)

1. **Re-run checks.** On the tagged source, run the automated suite plus `check_inputs.py`,
   `check_protected_sources.py`, `check_anonymisation.py` and `verify_campaign.py --all --authorization`.
2. **Export.** ORCH runs `PY W/tools/export_manuscript.py`, which writes `W/export/`: comments stripped into
   `claim_trace.json`, plus `numbers.tex`, the tables and the figures. Then run
   `check_latex_static.py --root W/export`. The tagged source stays in place, and every claim check keeps running
   on it.
3. **Readiness vote.** SCI-5 votes `READY_FOR_JOINT_REVIEW` or `NOT_READY`, with reasons. This is not a submission
   verdict (H4).
4. **Handoff.** Run RTP, then write `W/review_handoff.md`, covering:
   * Overleaf upload of `W/export/`, with the class supplied by the template;
   * files, hashes and commands;
   * every DR, finding and gap with its disposition;
   * the `% AUTHOR-CONFIRM` list and open cards;
   * disclosures, limitations and budget notes;
   * the AI-use record;
   * the conclusions for the joint examination.
5. **Overleaf returns.** On compile errors or a returned PDF, the integrator fixes the tagged source under INV-9,
   steps 1–2 re-run, and ORCH reads the PDF for layout findings.

Gates:
* **P9:G1** — the suite passes on the tagged source, and `check_latex_static.py` passes on the export.
* **P9:G2** — `check_governance.py` → EXPECT `GOVERNANCE CONSISTENT`, including the readiness DR and the RTP
  dispositions.

---

## 7. Output tree

```
reports/horizon_robustness_results/writing/
  CHECKPOINT_A.md  review_handoff.md  numbers.json  numbers.tex  reproduce.md
  governance/   DISPATCH_PREAMBLE.md  PREAMBLE_MINIMAL.md  PLAN_ADDENDA.md  STYLE_CANON.md
                source_manifest.json  environment.md  state.json  ai_use_record.md  dispatch_log.jsonl
                prompts/  results/  questions/  decisions/  gates/
  evidence/     anchors.json  document_values.json  claims.json  claims.md  requirements_map.json
                interpretation_errata.md  verification_inventory.md  independent/
  literature/   search_log_A.md  search_log_B.md  source_register.json  comparison_matrix.md
                retrieval_requests.md  fetched/
  math/         notation_bridge.md  model_delta.md  term_whitelist.md  derivation_A.md  derivation_B.md
                method_notes.md  tools/
  positioning/  companion_overlap.md  case_section.md  case_distinct.md
                argument_option_A.md/.json  argument_option_B.md/.json  argument_option_C.md/.json
  architecture/ blueprint_A.json/.md  blueprint_B.json/.md  blueprint.json  blueprint.md
  tools/        check_inputs.py  check_governance.py  recompute_anchors.py  compare_anchors.py  check_claims.py
                check_sources.py  check_blueprint.py  build_evidence.py  check_determinism.py  check_numbers.py
                check_anonymisation_writing.py  check_manuscript_claims.py  check_latex_static.py
                check_edit_invariants.py  overlap_scan.py  export_manuscript.py
  checks/       ck_ext.py  ck_ext_decisions.md
  tables/  figures/  drafts/
  manuscript/   main.tex  supplement.tex  references.bib  sections/        (tagged source)
  export/       main.tex  supplement.tex  references.bib  sections/  numbers.tex  tables/  figures/  claim_trace.json
  review/       round1/  round2/  delta/  fix/
.unlazy/horizon-writing/  PLAN.md  GATES.md  gates/  fixtures/  status.log
```

Nothing is copied under the session scratchpad. Absolute paths created by the run stay under 240 characters (INV-11
rule (i)); repository paths start at 43 characters.

---

## 8. Budget and cadence

About 205–275 agent dispatches, with no solver time. Under D4 the run pauses only at hard stops and ends at the joint
review.

| Phase | Dispatches |
|---|---|
| P0 | 8–10 |
| P1 | 16–20 |
| P2 | 9–12 |
| P3 | 9–12 |
| P4 | 16–20 |
| P5 | 20–26 |
| P6 | 10–14 |
| P7 | 70–90 |
| P8 | 40–60 |
| P9 | 8–10 |

---

## Appendix A — Dispatch preamble (prepended verbatim to every builder, critic and voter prompt)

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

## Appendix A2 — Minimal preamble (cold readers, mock referees, model probe)

```
You are reading a draft research article, or a plan of one, as an independent reader. Write nothing
to disk; return your report. Use Bash, if you have it, for read-only commands only. Never run
solvers, tests or repository scripts. Do not open files other than those named in your brief,
except public web sources. Report exactly what the text says and what it leaves unclear; do not
guess what the authors meant.
```

## Appendix B — Ballot and decision record

```
BALLOT  Q-###  voter: <agent type>/<family>  round: <1|2|3|runoff>  seat: <plain|red|blue>  slice: <evidence slice>
POSITION: <option id>   (batched cards: one POSITION per sub-question)
REASONS: 1. ... [locator]  2. ... [locator]  3. ... [locator]
STEELMAN: for each rejected option, its strongest reason and why it fails [locator]
REBUTTALS (round >= 2): <opposing reason> -> <rebuttal or concession> [locator]
WHAT CHANGED MY MIND (round >= 2): <argument> | none
RED/BLUE CASE (role seats): ...
BLOCKING OBJECTION: none | <checkable claim> [locator]
PROPOSED MISSING OPTION (round 1): none | <option>
CONFIDENCE: low | medium | high
WOULD CHANGE MY MIND: <specific evidence>
```

```
DR-###  Q-###  panel: <ADP-3|ADP-5, roster: identities, slices>  rounds: <k>  runoff: yes/no
Options (conservative order or UNORDERED; ordering confirmed by: <identity>): ...
Ballots: verbatim, by round, with dispatch_log sequence numbers
Chair verification: locator checks; second-chair re-checks; invalid/discarded/replaced ballots and
  why (max one replacement per panel); blocking objections verified/unverified; rejected
  out-of-scope demands; reseats and unavailable families
Outcome: <option> by <valid votes>/<valid ballots> | runoff | conservative default | fallback | ORCH recorded pick
Dissent: ...   Panel-diversity note: ...
Reversible: yes/no   Affected files: ...   Listed in handoff: yes/no
```

## Appendix C — Q-card

```
Q-###  raised by: <identity/ORCH>  phase: P#  date:
Question:
Why it changes acceptance:
Decisive test (read/recompute/none):
Class: E | J | H
Options, most to least conservative (or UNORDERED): (a) ... (b) ...
Ordering confirmed by: <identity>
Conservative default: <smallest wording that still states what was observed>
Card-specific decision rule (if any):
Resolution: <test result | DR-### | hard-stop package>
```

## Appendix D — Schemas (jsonschema-enforced)

**`claims.json` entry**

| Field | Content |
|---|---|
| `id` | claim identifier |
| `type` | assumption \| definition \| derivation \| observation \| interpretation \| limitation \| recommendation \| context \| disclosure \| scope \| premise |
| `endpoint_status` | predeclared_primary \| predeclared_secondary \| additional_descriptive \| exploratory \| not_applicable |
| `statement` | the claim text |
| `allowed_wording[]` | permitted phrasings |
| `required_qualifiers[]` | each with `discharge`: sentence \| scope_paragraph |
| `forbidden_wording[]` | each optionally `conditional_on`: a Q-card and outcome |
| `sources[]` | `path`, `sha256`, `locator` |
| `anchor_keys[]`, `document_value_keys[]` | links to anchors and document values |
| `unit`, `denominator`, `display_rounding`, `scope_boundary`, `supersedes[]` | presentation and scope |

**`requirements_map.json` entry**

| Field | Content |
|---|---|
| `req_id` | requirement identifier |
| `source` | document and locator |
| `text` | requirement text |
| `maps_to` | a claim ID or `forbidden:<claim>:<n>` |

**`document_values.json` entry**

| Field | Content |
|---|---|
| `key` | value identifier |
| `value_exact` | exact value |
| `unit` | unit |
| `source` | `path`, `line`, `sha256`, `quoted_text` |
| `extracted_by[]` | the two identities |

**`source_register.json` entry**

| Field | Content |
|---|---|
| `id`, `class` | identifier; literature \| own_submitted \| software |
| `doi`, `local_sha256`, `authors`, `title`, `venue`, `year`, `volume_pages` | bibliographic data |
| `verification_url`, `verified_on`, `metadata_verified` | verification record |
| `access` | FULL_TEXT \| ABSTRACT_ONLY \| UNRESOLVED \| LOCAL |
| `citation_level` | full \| existence \| none |
| `found_by` | A \| B \| both \| ORCH |
| `dimensions` | `objective`, `uncertain_quantity`, `balancing_target`, `catalogue_assumption`, `horizon`, `information_boundary`, `validation_type` |
| `locators[]`, `relevance_note`, `bib_key` | where supported, relevance, citation key |

**`argument_option_X.json`**

| Field | Content |
|---|---|
| `option` | option letter |
| `research_question` | |
| `spine` | the one-sentence spine |
| `contributions[]` | each `{text, claim_ids[]}` |
| `displays[]` | displays the option needs |
| `objections[]` | strongest objections |

**`anchors.json` / `numbers.json` entry**

| Field | Content |
|---|---|
| `key` | value identifier |
| `value_exact` | rational string or integer |
| `value_float` | float value |
| `unit`, `display_rounding` | presentation |
| `sources[]` | `path`, `sha256`, `selector` |
| `computation` | how the value was derived |

**`blueprint.json`**

| Element | Fields |
|---|---|
| section | `id`, `purpose`, `budget_words`, `placement`, `reader_questions[]` |
| paragraph | `id`, `topic_claim`, `claim_ids[]`, `macros[]`, `displays[]`, `source_ids[]`, `uses[]`, `introduces[]`, `interpretation`, `boundary` |
| display | `id`, `message`, `claim_ids[]`, `placement`, `required` |
| top level | `mandatory_reader_questions` (question → section ids), `macro_convention` |

**`state.json`**

| Field | Content |
|---|---|
| `phase`, `wave` | current position |
| `families` | family → available \| unavailable, with timestamp |
| `in_flight[]` | dispatch sequences |
| `sections` | id → drafting \| provisional_frozen \| reopened |
| `ownership` | path set → holder |
| `p8_status`, `open_items[]` | convergence state |
| `export_hash` | hash of the export |

## Appendix E — Finding

```
F-###  raised by: <identity>  artifact: <path>  built by: <identity|ORCH>  location: <line/section>
Severity: BLOCKING | MAJOR | MINOR
Claim: <what is wrong>  Evidence: <locator + quote/computation>
Proposed fix: ...
Verification: CONFIRMED | REJECTED (<evidence>)  by: <ORCH | independent confirmer identity>
Fix confirmed by: <identity>
```

## Appendix F — Baseline commit message (D1)

The trailer follows the orchestrating session's attribution instruction at commit time (currently Claude Opus 5).

```
results: freeze horizon-robustness evidence and writing plans

Commit the corrected delta figure, the held-out drift row and its survey
code, the handoff and audit updates of 14 September, both writing plans,
the orchestration plan and its review ledger, so the agent run starts
from pinned hashes.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

## Appendix G — OCL rubric (0–3 per criterion; judges quote the text they score)

| Criterion | What earns 3 |
|---|---|
| Spine | The paragraph's role in the one-sentence spine is recoverable from its first sentence. |
| Chronology | No forward leak; every term and symbol was introduced earlier (§II). |
| Unit | One idea per paragraph; a results paragraph goes from assertion to evidence, interpretation and boundary (§XI). |
| Claim fidelity | Correct claim IDs, qualifiers discharged, no forbidden wording, numbers as macros. |
| Canon | No banned pattern (classes A–E, adapter, banned lists, whitelist respected); the companion's register. |
| Reader load | A specialist follows it in one pass (§XVIII). |
