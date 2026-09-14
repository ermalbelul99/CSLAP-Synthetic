# Writing plan for the robustness extension (14 September 2026)

Prepared by the E2/R1 driver as an enriched version of the original assistant's
13/14 September recommendation, after checking its claims against the artifacts.
This plan is for the **writing agent** (an orchestrating session that dispatches
the project's sub-agents and skills). It is not the manuscript and it declares no
verdict; R2 remains with the user and the writing agent.

Internal context, not for the manuscript: the base article is
`IJSSOL_CSLAP_v1.tex` (International Journal of Systems Science: Operations &
Logistics, `interact` class, bibliography `IJSSOL_CSLAP_v1.bib`). It has been
**submitted** and has **no editorial response yet**; it must be described as
"submitted" or "companion", never as published. `IJPR_CSLAP_v4.tex` is an
earlier draft of the same work and is not the reference version. Neither file,
nor any `.bib` they use, nor any protected source may be edited.

---

## 0. Verdict on the reviewer's recommendation (checked, not assumed)

| Reviewer claim | Check | Result |
|---|---|---|
| 260 tests pass; 10 campaigns accounted; 92/92 protected; anonymisation passes | 234 shared + 26 Hexaly; verify-all over 10 directories; both checks re-run 13 Sep | Confirmed |
| Held-out table: NOM 0/3 (3.144 pp), TIGHT 3/3 (1.756), HIST+ACT 0/3 (2.179), HIST+ACT-T 3/3 (1.160); visits 3.232 / 3.270 / 3.264 / 3.347 | Recomputed from `tables/station_profile_industrial.csv` and the case records | Exact to three decimals |
| HIST+ACT-T costs about 2.36 % more visits than TIGHT | 3.347 / 3.270 | 2.35 %; confirmed |
| Scenarios "add nothing" is too strong; they shrink deviations without margin (3.14 → 2.18 pp) and with it (1.76 → 1.16 pp) | Same table; the incumbent's own largest deviation on that future is 1.157 pp | Confirmed; handoff §13.3 now says so and calls it a cost-protection trade-off |
| Scenarios and activation are bundled in the factorial | Design of §9 (HIST not run) | Confirmed; must be stated |
| The pooled δ figure still threaded three horizons through one line | `figures.frontier` plotted one point per row | Confirmed and **fixed** 14 Sep: one point per value per arm with k/N labels |
| The submitted article already evaluates on unseen weeks | `IJSSOL_CSLAP_v1.tex` §"Robustness on unseen weeks", Table `tab:temporal`: 6.6 % and 7.4 % on held-out weeks against 13.7 % in sample, with an oracle | Confirmed; the extension's novelty is not "testing on future orders" |
| Winkelmann et al., arXiv 2209.03998, is a relevant positioning anchor | Fetched: "Integrated storage assignment for an e-grocery fulfilment centre: accounting for day-of-week demand patterns", Winkelmann, Tolkmitt, Ulrich, Römer, 2022/23; deterministic MILP, day-of-week demand, workload balance across days; no robust optimisation; **dated** | Confirmed and useful: it is the dated, deterministic counterpart of our undated protocol |
| Dündar (dergipark article-file 4745387) | PDF fetched but not text-extractable here | **Unverified**: the writing agent must confirm title and scope before citing |
| The total-variation argument is valid but does not certify these futures | `tables/drift_survey.csv`: product-mix drift 0.12–0.27 against ρ = 0.01 | Confirmed |

**Position.** Agree with moving to writing and with no further campaign for this
scope; agree with the combined narrative (a bounded positive margin result inside
an honest comparative robustness study). Two additions the reviewer did not make:
(a) the extension's methodological novelty over the article's own hold-out is the
**undated information contract and predeclared rolling-origin protocol** (next-*n*
complete orders, closed catalogue, frozen products, deployment origin), not the
act of evaluating out of sample; (b) the study's most transferable finding for
practitioners is negative and should be stated as such: historical block
scenarios plus activation did **not** contain the realised future in the
downward direction in any two-sided industrial cell, and the product-level
total-variation bound is far too loose to be a margin rule, so margin has to be
set from station-level dispersion. Both belong in the contribution list.

---

## 1. What the manuscript can claim, and the evidence behind each claim

Every claim below is traced to an artifact. The writing agent must not add a
numerical claim without a row in this matrix (Step 1 turns it into
`STUDY_REPORT.md` and a generated macro file).

| # | Claim | Kind | Evidence | Boundary |
|---|---|---|---|---|
| C1 | Workload-share preservation can be posed and evaluated on an undated order stream: history prefix, frozen layout, the next *n* complete orders, closed catalogue, frozen products | Methodological | `CAMPAIGN_PREDECLARATION.md` §§1–9; `MATHEMATICAL_SCOPE.md`; runner and validator; handoff §2, §5 | Snapshot-conditioned: catalogue, incumbent and frozen products reconstructed from the full export (`DATA_PROVENANCE.md`, `INDUSTRIAL_AMENDMENT_20260909.md`) |
| C2 | Under the upper-only rule, historical scenarios reduce cap breaches against NOM but do not beat ordinary tightening on the benchmark; on BERNER only HIST+ACT passes 2 of 3 horizons (H1 supported, H2 mixed, H3 only where inactive products exist, H4 descriptive) | Empirical | `campaigns/screen_20260910`, handoff §10, `tables/stratum_summary.csv`, `paired_stratum_summary.csv` | 29 synthetic instances + 1 warehouse, one seed, one origin |
| C3 | Under the two-sided ±2 rule the incumbent passes at every BERNER horizon; among optimised arms only TIGHT passes all three; robust-arm misses are small (≤ 0.41 pp) and downward | Empirical | `campaigns/ts_d02_20260912`, handoff §12.2–12.5 | Exploratory (the futures had been examined under the upper-only rule); 4 synthetic instances only |
| C4 | Widening to ±3 does not restore compliance for the robust arms; narrowing to ±1 fails all but one TIGHT cell and the incumbent | Empirical | `ts_b01`, `ts_b03`, handoff §12.2, `figures/pooled/two_sided__5e1ee22f/frontier_delta.png` | Three BERNER horizons per δ, one seed |
| C5 | On a held-out deployment, explicit margin gives ±2 compliance on all three seeds with ≈15 % fewer visits than the incumbent; without margin no arm complies; scenarios and activation shrink the largest station deviation (3.14 → 2.18 pp without margin, 1.76 → 1.16 pp with it) at ≈2.4 % more visits than TIGHT | Empirical, predeclared | `campaigns/ho3_20260913`, handoff §13, `CAMPAIGN_PREDECLARATION.md` §9 | One origin, one horizon, three optimiser seeds; a bounded case study |
| C6 | The realised future leaves the historical scenario set downward in every two-sided industrial cell; product-mix drift in total variation (0.12–0.27) is far above the reserved margin (0.01), so compliance rests on within-station cancellation, not on set membership | Empirical + mathematical remark | `tables/two_sided_novelty_survey.csv`, `tables/drift_survey.csv`, handoff §12.6 | The TV lemma is exact; it certifies nothing about these futures |
| C7 | The exact finite counterpart of block-scenario + activation uncertainty, with the trapped-activation term and an integer-count restatement, is validated by an independent exact validator; every stored layout revalidates | Mathematical + software | `MATHEMATICAL_SCOPE.md` §10, handoff §6.6, §6.8, `tests/horizon_robustness/test_two_sided.py` (vertex oracle) | No optimality claims: all industrial solves are time-capped returned layouts |
| C8 | Conditional robust feasibility and observed future performance are different quantities; no future reliability probability is established | Interpretive | Handoff §9.2, §12.6, §13.4 | — |

Claims the manuscript must **not** make: universal superiority of any arm; a
future-feasibility guarantee; ±2 or λ = 0.5 as operationally certified values;
a 29-instance two-sided benchmark (only 4 ran two-sided); anything about the
six non-replayable min-slack diagnostics beyond "logged"; anything derived from
the superseded directories.

---

## 2. Connection to the submitted article (the writing agent's first job)

The extension must read as a companion to `IJSSOL_CSLAP_v1.tex`, reuse its
notation and cite its model as the base. Concretely:

* **Notation to reuse** (article §"Products, orders and station visits",
  Table `tab:data`): $P, O, S$; $P_o$; $\zeta_s$; $L_p$; $V_s$, $T_s$, $C_s$;
  station visits as the objective; workload as a hard constraint (§"Workload
  balancing as a hard constraint"). The extension adds: the historical share
  $b_s$, the band $[\max(0,b_s-\delta),\min(1,b_s+\delta)]$, the tightening
  fraction $\lambda$, the activation budget $\nu$, the horizon $n$, the origin
  $t$, and the scenario index $k$. Do not rename anything the article defines.
* **Base model to cite**: the article's set-variable formulation and binary MILP
  (§"Binary mixed-integer linear programme", §"Set-variable reformulation"); the
  extension's rows are added to that feasible set. The solvers are the same
  (Hexaly for the set-variable model, CPLEX for the binary form).
* **What the article already showed and the extension must not re-claim**: the
  out-of-sample evaluation on dated weeks (§"Robustness on unseen weeks",
  Table `tab:temporal`: 13.7 % in sample, 6.6 % and 7.4 % on held-out weeks, an
  oracle at 12.1 % and 10.2 %) and the managerial insight (4) on running a
  layout as a lifecycle. The extension's contribution over that section is
  (i) the undated protocol with a formal information boundary and
  predeclaration, (ii) the workload-share preservation objective replacing a
  fixed budget, (iii) the controlled comparison of margin against scenario
  protection, and (iv) the negative evidence on scenario coverage (C6).
* **Consistency checks the writing agent must run**: the same warehouse figures
  (21,874 products; the article says 26 stations, the extension's retained
  system has 24 after two exclusions, `DATA_PROVENANCE.md` explains why); the
  same anonymisation (aliases only; `check_anonymisation.py`); the same
  data-availability statement (Taylor & Francis "share upon reasonable
  request"); the same author and affiliation block.
* **Salami-slicing defence**: state in the introduction what the article
  contains and what this paper adds, in one paragraph, so an editor who sees
  both can tell them apart; and draft so that §§ on the model and the held-out
  factorial could be folded into the article as a section if an editor asks.

---

## 3. Deeper valuation of the path forward

1. **Contribution ranking for the paper**, in the order a reviewer will weigh
   them: (1) C5, the predeclared held-out factorial with an isolated mechanism;
   (2) C6, the coverage failure of historical scenarios and the vacuity of the
   TV radius; (3) C1, the undated protocol; (4) C7, the exact counterpart and
   validation discipline; (5) C2–C4 as the comparative context. Lead with (1)
   and (2); they are what nobody else has measured on real data.
2. **The honest headline** is a trade-off, not a winner: margin decides
   compliance, scenarios buy fidelity to historical shares at a visit cost; the
   incumbent already sits inside ±2 on both futures, so the gain is the 13–15 %
   visit saving at equal compliance, and NOM's extra point of saving is what
   the band costs.
3. **Target venue** must be decided before the outline: IJSSOL as a companion
   (same class, same conventions, easiest connection) or C&IE / IJPE (the
   `or-scientific-writing` skill's conventions). The writing loop's compliance
   checks are IJPR-flavoured; whichever venue is chosen, the agent must fetch
   that journal's author guidelines and re-point the checks.
4. **What would strengthen the paper without new solves** (all cheap, all from
   existing artifacts): a four-arm station profile on the held-out future (one
   axis, four layouts, the band drawn); the seed-wise held-out table with breach
   magnitudes and deviations; the drift and novelty surveys as one figure
   ("where the future left the model"); the δ response over matched BERNER
   cells (now correct); a study-design table with the three campaigns' scope,
   rule, δ grid, seeds, origins and their exploratory/confirmatory status.
5. **What must stay a limitation**: one warehouse; one held-out deployment;
   seeds are not futures; four synthetic instances two-sided; ν and λ frontiers
   unrun (λ by decision); no lower bound; the snapshot assumption; the
   non-replayable diagnostics; no reliability probability.
6. **If the user wants more evidence later**, the only experiment that would
   change a claim is a second industrial site or a second independent
   deployment segment (none exists in the retained stream). Do not propose λ
   or δ searches on the current futures.

---

## 4. Execution plan for the writing agent

Use `planning-with-files` from the first step so the plan, progress and gaps
live on disk (`reports/horizon_robustness_results/writing/`). Every step has a
gate; nothing proceeds on a failed gate. Sub-agents are dispatched through the
`Agent` tool by the names in `.claude/agents/`; skills through the `Skill` tool;
pipeline commands in `.claude/commands/` are orchestrations of those agents.
The agent kit was imported from a thesis workspace: `CLAUDE.md`,
`Thesis_Manuscript/`, `.claude/plans/thesis-outline-v3.md` and
`notebooklm_notebooks.json` **do not exist here**; do not assume them, and treat
the NotebookLM channel as unavailable unless the user sets it up.

### Step 1 — Freeze the conclusion and the evidence (no writing yet)

* **Deliverable**: `reports/horizon_robustness_results/STUDY_REPORT.md` with the
  claim-to-evidence matrix of §1 expanded (one row per claim, artifact path,
  content hash from `artifact_index.json`, kind, boundary), plus
  `reports/horizon_robustness_results/writing/numbers.tex`, a file of LaTeX
  macros **generated by a script** from `artifact_index.json`, the tables and
  the case records (e.g. `\holdoutTightPasses`, `\holdoutVisitSavingTight`),
  so no number in the manuscript is typed by hand.
* **Agents / skills**: `results-report` (structure), `results-analysis` in
  read-only audit mode (valid/invalid statistics; it will rightly refuse
  significance tests over three seeds), `paper-self-review` (claim audit),
  `results-integrity-reviewer` (every number traces to an artifact),
  `sparring-partner-review` (the argument).
* **Gate**: `results-integrity-reviewer` returns PASS on the matrix; every macro
  in `numbers.tex` regenerates byte-identically from the artifacts.

### Step 2 — Positioning and outline (user review before drafting)

* **Deliverable**: a positioning note (2 pages) and an annotated outline with the
  target venue, the connection paragraph of §2, the contribution list of §3.1,
  and per-section evidence pointers. Suggested structure: 1 Motivation and
  relation to the submitted article; 2 Information contract and normalised
  workload-share formulation; 3 Uncertainty sets, exact counterpart, margin
  control; 4 Protocol: rolling origins, predeclaration, exact validation;
  5 Upper-only screen (comparative context); 6 Two-sided exploration and the
  δ response; 7 Held-out factorial and the cost-protection trade-off; 8 Where
  the future left the model (novelty and drift); 9 Limitations, managerial
  reading, conclusions.
* **Agents / skills**: `research-gap` command (web channel via
  `academic-researcher`; NotebookLM channel absent) for the positioning against
  workload-aware and robust storage assignment; `literature-review-citation`
  and `citation-verification` for every entry (verify Winkelmann et al. 2022/23
  and Dündar before use; reuse keys from `IJSSOL_CSLAP_v1.bib` where the same
  work is cited); `positioning-reviewer` and `plan-reviewer` (plan-consensus
  gate, `PLAN_SOLID`); `or-scientific-writing` for the argument stress-test.
* **Gate**: `plan-reviewer` `PLAN_SOLID`; then **the user approves the outline**.

### Step 3 — Publication-quality evidence package (existing artifacts only)

* **Deliverable**: `reports/horizon_robustness_results/writing/figures/` and
  `tables/` for the manuscript: study-design table; complete held-out results
  with breaches and deviations; visits-versus-deviation; four-arm station
  profile on the held-out future; matched-cell δ response; novelty-and-drift
  figure; supplementary tables preserving every benchmark outcome, failure and
  numerical qualification (NO_INCUMBENT cells, NUMERICAL_ISSUE, superseded
  directories listed as excluded). Update `MATHEMATICAL_SCOPE.md` §10 with the
  corrected two-sided activation counterpart (trapped term) and the TV remark
  with its empirical caveat.
* **Agents / skills**: `experimental-results-presentation`;
  `mathematical-formulation` and `robust-modeling` for the exposition;
  `algorithm-documentation` for the validator, the integer-count rows and the
  runner protocol as algorithm environments; `formulation-reviewer`
  (model-to-code, notation against the article); `results-integrity-reviewer`.
  Figures are produced by scripts under `tools/horizon_robustness/` or the
  analysis package, never by hand; `check_anonymisation.py` must pass on the
  writing folder too.
* **Gate**: `formulation-reviewer` PASS; `results-integrity-reviewer` PASS;
  anonymisation check passes over the writing folder.

### Step 4 — Draft the manuscript and supplement

* **Deliverable**: new files only, e.g. `IJSSOL_CSLAP_robustness_v1.tex`,
  `IJSSOL_CSLAP_robustness_supp_v1.tex`, `IJSSOL_CSLAP_robustness_v1.bib`, in
  the class of the chosen venue; `IJSSOL_CSLAP_v1.tex`, `IJPR_CSLAP_v4.tex` and
  their `.bib` files untouched.
* **Agents / skills**: `academic-paper` (plan and outline modes only, LaTeX
  output) as scaffolding; `academic-writer` and `clean-scientific-writer` for
  the prose; `mathematical-formulation`, `robust-modeling`,
  `algorithm-documentation` for §§2–4; `scientific-writing-loop` command for the
  convergence loop (`scientific-reviewer` → writer → `narrative-reviewer`), with
  its IJPR compliance checks re-pointed to the chosen venue's guidelines;
  `academic-prose-auditor`, `humanizer-writer` and `no-ai-slop` for the final
  prose pass. Formal English in the deliverables; the caveman skills apply only
  to intermediate chatter if the agent uses them at all.
* **Rules**: every number is a macro from `numbers.tex`; percentages and
  percentage points are never mixed; "seed" and "origin" are never called
  replications; "submitted companion article" is the only description of the
  base paper; no verdict language ("validated method", "guarantee").
* **Gate**: `scientific-writing-loop` converges (writer and both reviewers agree);
  `paper-self-review` finds no overclaim against §1.

### Step 5 — Final scientific and reproducibility review

* `structure-review` command on the new manuscript treated as a per-problem
  draft (it expects a thesis; give it the manuscript path explicitly);
  `citation-verification` on the final `.bib`; `results-integrity-reviewer` on
  the compiled PDF against `numbers.tex`; `verification-loop` on the repository
  (tests, `verify_campaign.py --all --authorization --revalidate`,
  `check_anonymisation.py`, `check_protected_sources.py`); a compile of both
  files; and a joint read of the conclusions with the user.
* **Gate**: all checks green; the user reads the conclusions; nothing is
  submitted by the agent.

---

## 5. Inputs the writing agent needs (all present)

* `EXPERIMENT_REVIEW_HANDOFF.md` (§§1–13), `CAMPAIGN_PREDECLARATION.md` (§§1–9),
  `PILOT_FINDINGS.md`, `MATHEMATICAL_SCOPE.md`, `DATA_PROVENANCE.md`,
  `INDUSTRIAL_AMENDMENT_20260909.md`, `INDEPENDENT_REVIEW_20260911.md`,
  `INDEPENDENT_REVIEW_20260913.md`, `analysis_audit.md`, `artifact_index.json`.
* Tables and figures under `tables/` and `figures/` (publication set from the
  upper-only screen; engineering sets per campaign; `figures/pooled/`).
* The ledger `.unlazy/horizon-cslap/status.log` and the gate files for the
  audit trail; `tools/horizon_robustness/` for regeneration.
* The base article and its bibliography, read-only.
