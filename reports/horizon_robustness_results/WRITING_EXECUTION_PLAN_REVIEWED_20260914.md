# Reviewed execution proposal: the undated CSLAP robustness extension

14 September 2026. Internal planning document, not manuscript prose.

This is the original assistant's review and proposed replacement for
`WRITING_PLAN_20260914.md`. The earlier proposal is preserved unchanged for
comparison. If the user approves this document, use it as the execution contract
where the two plans differ. Approval of a plan is not permission to bypass its
later author-review gates. No manuscript drafting or new experiments were
performed in preparing this review.

## 1. Recommendation and remaining decisions

**Scientific recommendation:** retain the undated path for a bounded comparative
case study with a positive margin finding. No further solver campaign is required
for that scope. This is not a general future-feasibility guarantee, an automatic
margin-calibration method, or evidence that dates are unnecessary for every
operational decision. The dated alternative stays deferred, not disproved.

There are three different readiness questions:

1. **Evidence ready for synthesis? Yes.** The held-out primary endpoint was met;
   the margin/scenario comparison and its limitations can be reported.
2. **Independent paper sufficiently differentiated? Plausible, not yet settled.**
   Require a closest-literature and companion-overlap review before committing
   to a strong novelty claim. A reproducible protocol is useful without being
   a novel general methodology.
3. **An AI may autonomously draft the paper now? Not established.** Resolve the
   target venue and its current AI-use policy first, as described below.

The user and original assistant retain the final scientific assessment together.
Writing-agent and sub-agent verdicts are recommendations and checks, not authority
to submit, change the research direction, or certify publication readiness.

### Immediate venue/policy gate

The companion's venue does not automatically choose the extension's venue.
For IJSSOL/Taylor & Francis, current Author Services guidance excludes AI-generated
first drafts of manuscripts or sections and AI creation/conclusion of the article's
argument, while allowing language refinement. Use author-led drafting with
permitted assistance, or obtain policy clarification before proceeding. Reviewing
an AI first draft does not remove that restriction. Source checked
14 September 2026: [Taylor & Francis manuscript-preparation guidance](https://authorservices.taylorandfrancis.com/editorial-policies/using-ai-in-your-research-and-manuscript-preparations/).

Maintain a truthful record of AI assistance, human checks, tools and versions;
never copy a declaration that no AI was used. The publisher also requires
disclosure and author accountability: [Taylor & Francis AI policy](https://taylorandfrancis.com/our-policies/ai-policy/).
Do not contact an editor or submit anything without the user's explicit direction.
This gate restricts drafting; it does not prevent internal evidence preparation,
source checking, or advisory planning within applicable policy.

## 2. Independent assessment of the other agent's claims

Current-turn checks: read the current IJSSOL model and relevant companion sections,
the handoff/predeclarations/provenance, the revised analysis code, actual role
definitions, and primary literature/publisher sources. Recomputed held-out
aggregates from `tables/case_frame.csv`, deviations from
`tables/station_profile_industrial.csv`, and the incumbent deviation from a
held-out case's `reference_evaluation`. Inspected the corrected delta figure.
These are checks of stored evidence, not a fresh replay of all 413 layouts or a
new run of the 260-test suite. Those completion counts remain attributed to the
recorded verification package and previous reviews.

### Strengths to retain

* The held-out design separates the margin factor from the **combined** historical
  scenarios/activation factor. Both margin arms pass all three optimizer seeds;
  neither no-margin arm passes. The primary endpoint required TIGHT to pass at
  least two seeds, and it passes three.
* The revised interpretation correctly recognises that scenario protection can
  improve fidelity even when it does not change the pass/fail classification.
* The snapshot assumption, excluded stations, fixed products, exploratory changes,
  numerical repairs and time-capped solutions have an auditable record.
* The original paper already contains dated unseen-week evaluation. The extension
  must not present out-of-sample testing itself as a new contribution.

Held-out deployment only: origin 243,151; next 21,874 orders; two-sided
delta = 0.02; lambda = 0.5; nu = 0.01; three optimizer seeds.

| Arm | Joint passes | Mean visits/order | Largest absolute station deviation, maximum over seeds (pp) |
|---|---:|---:|---:|
| NOM | 0/3 | 3.231630 | 3.143883 |
| TIGHT | 3/3 | 3.269742 | 1.756255 |
| HIST+ACT | 0/3 | 3.263692 | 2.178584 |
| HIST+ACT-T | 3/3 | 3.346774 | 1.159749 |
| Incumbent, the same future | pass | 3.847124 | 1.156787 |

These are review anchors, not a manually maintained source for manuscript tables.
Generate publication values from the underlying records at full precision.

### Critical corrections before writing

| Issue | Assessment and required correction |
|---|---|
| "Novel undated information contract and rolling-origin protocol" | Distinguish contribution relative to the companion from novelty relative to literature. Rolling-origin evaluation is established. The executed evidence has an exploratory origin and one later held-out origin, not an extensive rolling-origin experiment. Prefer **order-indexed, horizon-conditioned protocol with a later held-out deployment**. |
| "Scenarios add nothing" versus "scenarios buy fidelity" | The second is supported descriptively at this deployment. The bundle reduces the reported maximum deviation; HIST+ACT-T costs **2.355907%**, rounded **2.36%**, more mean future visits than TIGHT. Do not calculate ratios from three-decimal display values. |
| "Matches incumbent fidelity" | Close on this particular maximum-deviation statistic: 1.159749 versus 1.156787 pp. This does not establish identical station profiles, equal performance on every station, or equivalent tail risk. |
| "The mechanism is isolated" | A two-factor, algorithm-level comparison under equal configured solve budgets, not a general causal law. Historical scenarios and activation remain bundled. Time-capped optimizer outcomes do not identify the exact-optimum cost of protection. |
| "Everything in the factorial interpretation is predeclared" | The primary pass endpoint and listed secondary metrics were predeclared. The later maximum-absolute-deviation comparison and drift-context reading must be identified as additional descriptive analyses, not silently promoted to primary endpoints. |
| "TV is too loose, so margins have to come from station dispersion" | Non sequitur. Failure of a sufficient product-level bound does not establish a particular alternative calibration rule. Incumbent station dispersion is layout-specific and does not calibrate every optimized layout. No validated lambda-selection rule was obtained. |
| "The held-out window was not easy" | The new row shows TV 0.194956 versus historical maximum 0.194411 and mean 0.171100 over 11 matched blocks. This is high **product-mix drift**, not proof of workload-feasibility difficulty. Station aggregation can cancel product drift; the incumbent passes. Historical blocks also contribute to the pooled reference against which they are compared. Do not treat this descriptive comparison as a calibrated extremeness test. |
| "Robust arms' misses are downward" | Downward envelope departures occur throughout the relevant industrial diagnostics, but actual policy misses include upper as well as lower breaches. Set departure and band violation are different metrics. |
| "Historical scenarios do not beat tightening on the benchmark" | Too broad. The upper-only synthetic screen is mixed across strata and has unequal scored denominators. Report paired, matched outcomes and non-returns, rather than one universal ranking. |
| "Exact counterpart is validated by a validator" | Software agreement supports implementation correctness; mathematical exactness needs a derivation. Keep the corrected lower activation term, integer restatement and edge cases in the formal review. |
| "There is no other deployment segment" | Too strong: 19,837 retained orders remain after index 265,025, fewer than P but enough for a smaller horizon. This is not an approved replication and not an independent warehouse. Do not inspect or use the remaining tail during writing. |

The delta plot now aggregates one point per delta/arm and labels its denominator;
the earlier threading error is corrected. It is still an engineering figure:
overlapping labels, long internal title and an uninformative zero-only panel need
publication treatment. A small matrix can communicate the three-horizon counts
more clearly. Do not present a sampled response curve as an optimal Pareto frontier.

## 3. Scientific framing and connection to the submitted companion

### The question to organise the paper around

Investigate whether a layout that reduces historical order-station visits can
preserve a prescribed historical workload-share profile on later orders, and
what is gained by explicit margin versus historical scenario/activation
protection when calendar dates are unavailable to the method.

Proposed contribution hierarchy for author approval:

1. A precisely delimited extension of the CSLAP decision problem: historical
   share targets, a closed catalogue, fixed placements and order-count horizons.
2. A comparative investigation distinguishing conditional model protection,
   realized policy compliance, closeness to the target, and visit cost.
3. A bounded held-out positive margin result, with an observed extra
   fidelity/visit-cost trade-off from the scenario/activation bundle.
4. Diagnostic evidence of uncertainty-set misspecification and the failure of
   a particular sufficient TV certificate on these windows.

The exact counterpart and reproducibility package support these contributions;
do not advertise integer rescaling, safety margins, scenario hulls or chronological
splits as newly invented techniques. A negative result is useful here because its
scope and mechanism are examined, not because one failed set disproves robust
optimization generally.

### What carries over, what changes

| Element | Submitted companion | This extension |
|---|---|---|
| Decision and objective | Single-station placement; minimize order-station visits | Retained; historical visits remain the optimization objective |
| Storage | Unit slots; tight catalogue/slot equality | Retained for every included product, including zero-history products |
| Workload restriction | Fixed station workload budgets, expressed using processing rates | **Replaced**, not supplemented, by normalized share-policy restrictions under the user's abstract scaling assumption |
| Future evaluation | Already includes unseen dated weeks and oracle context | Next-n retained complete orders, with explicit information boundary and held-out factorial |
| Robustness question | Performance of a deterministic allocation on unseen orders | Relative merits and limits of tightening and scenario/activation protection of station shares |
| Data | Submitted study's synthetic and industrial premises | Only the authorized 29 synthetic instances and specified BERNER export; extracts/filters and evaluated subsets disclosed |

Write a short, self-contained summary of the inherited model and identify changed
rows explicitly. Do not reproduce the full companion's heuristic/CG exposition,
proofs or results as if newly contributed. Do not call share preservation a new
objective: it is a feasibility policy. Percentage visit savings from different
extracts, horizons and baselines are not directly comparable across papers.

Use the user-specified current inputs, read-only:

* `IJSSOL_CSLAP_v1.tex`
* `IJSSOL_CSLAP_v1_supplementary.tex`
* `manuscript_checks/baseline/IJSSOL_CSLAP_v1.bib`

The root `IJSSOL_CSLAP_v1.bib` currently has the same SHA-256 as the baseline
bibliography. Record that comparison before reuse; do not silently substitute a
later root edit. The submitted files and older IJPR files remain untouched.
Refer to the companion without implying publication or acceptance. Do not put
editorial correspondence/status history into manuscript prose. Authors decide
the citation and any related-manuscript disclosure required for submission.

Build an overlap matrix: inherited question/model/data/text/results versus new
question/model/experiments/inferences. If literature review leaves only a thin
repackaging of the companion, return that finding to the user before drafting;
do not manufacture novelty or automatically merge an extension into a submitted
manuscript. Authorship, funding, data access and acknowledgements require author
confirmation, not automatic copying of boilerplates.

### Non-negotiable data and information contract

* All included products are assumed known before deployment and need slots even
  when their historical count is zero. Unknown future SKU arrivals are outside
  scope. An export cannot prove completeness of never-ordered physical inventory.
* Preserve the shared industrial loader and amendment exactly. The retained
  catalogue has 21,874 products and 24 evaluated stations, with 5,899 fixed and
  15,975 movable products. The companion already uses a 24-station evaluation
  despite 26 reporting aliases; do not portray this as a new exclusion.
* Fixed products contribute changing historical/future workload and visits.
  The two excluded stations and their products contribute to neither numerator
  nor denominator. The large-order filter determines the decision pool, not
  exclusion of small orders from the full evaluation stream.
* Industrial workload counts distinct retained product-order pairs, not units
  ordered or physical processing hours. Synthetic workload preserves its declared
  line multiplicity. Preserve the documented duplicate/freeze-mask edge case.
* The full-export catalogue, incumbent, freeze mask and retention rule are
  **assumed pre-known metadata**. Their reconstruction is retrospective and
  future-dependent. Conditional prefix-only estimation is not proof that the
  whole pipeline had genuinely prospective metadata.
* Reliable numeric-ID chronology is assumed, not created by sorting. Synthetic
  stream order alone does not establish realistic temporal dependence or drift.
* Freeze targets at each deployment origin; never retarget using the scored
  future or the incumbent's future profile. A later deployment can establish its
  own target from its then-available historical prefix, as predeclared.
* Uniform multiplication of workload leaves shares unchanged. Changing horizon
  can change mix and the uncertainty set; scale invariance is **not** invariance
  of the learned layout or a promise across every future n.
* Historical scenario blocks and the primary future use matched n. The grid
  n in {ceil(P/2), P, 2P}, with P meaning catalogue cardinality in this shorthand,
  is a declared sensitivity design, not an operationally optimal universal horizon.

## 4. Literature positioning: verified anchors and required challenge

This is a starting set, not a completed systematic literature review.

* **Winkelmann, Tolkmitt, Ulrich and Römer:** use the journal version,
  *Flexible Services and Manufacturing Journal* 37, 558-598 (2025), online
  20 June 2024, DOI 10.1007/s10696-024-09549-7. Section 5.2, equations (10)-(12),
  imposes upper/lower workload bounds relative to the station average for each
  weekday; Section 5.4 includes out-of-sample simulation. This is a close
  variation-aware pick-and-pass comparison, not merely a deterministic dated
  foil. Contrast its selectable catalogue, objectives and weekday/equal-balance
  targets with our closed catalogue, visit objective and frozen heterogeneous
  historical targets. Do not claim that workload normalization or multiple-demand
  protection is absent there. [Publisher article](https://link.springer.com/article/10.1007/s10696-024-09549-7).
* **Bayram Dündar:** title and scope are now verified, contrary to the earlier
  plan's pending flag. *A robust optimization approach to address correlation
  uncertainty in stock keeping unit assignment in warehouses*, *Alphanumeric
  Journal* 13(1), 1-12 (2025), DOI 10.17093/alphanumeric.1670030. It develops a
  robust linearized QAP for uncertain SKU correlations and picking distance,
  with small-scale evaluation. It precludes a broad claim to inventing robust
  correlated storage assignment, but does not answer this workload-share question.
  Use the canonical accented author spelling in the bibliography.
  [Publisher record and PDF](https://dergipark.org.tr/en/pub/alphanumeric/article/1670030).
* **Tashman (2000):** rolling-origin evaluation has a long-established literature;
  inspect *Out-of-sample tests of forecasting accuracy: an analysis and review*,
  DOI 10.1016/S0169-2070(00)00065-0. The publisher's indexed record explicitly
  discusses rolling-origin design. This review did not retrieve the full publisher
  text; verify a primary full-text copy before attributing a detailed protocol
  prescription. [Publisher record](https://www.sciencedirect.com/science/article/pii/S0169207000000650).

The researcher should follow relevant primary references on robust storage
assignment, uncertainty-set coverage, constraint tightening and allocation under
changing demand, and check recent forward citations. Every comparison must state
objective, uncertain quantity, balancing target, catalogue assumptions, horizon,
information boundary and validation type. Do not require implementation of these
different models as new baselines during writing. Explain comparability limits.

The positioning reviewer must answer: does the combination and evidence support
a distinct contribution after comparison with the closest work? "Nobody else has
measured this" is not an acceptable substitute for that examination.

## 5. Agent and skill execution contract

### Actual available roles, not an assumed plugin registry

The following `.claude/agents/*.md` definitions exist and were inspected:
`academic-researcher`, `academic-writer`, `clean-scientific-writer`,
`results-integrity-reviewer`, `formulation-reviewer`, `positioning-reviewer`,
`plan-reviewer`, `scientific-reviewer`, `narrative-reviewer`,
`academic-prose-auditor`. They are local role instructions; their presence alone
does not register an `Agent` or `Skill` tool in another host.

Only the orchestrator dispatches sub-agents. Read each chosen role and its required
skills completely before use, applying this task-specific scope over imported
defaults. Use available delegation tools with the role attached; if none are
available, perform the same roles sequentially and disclose the fallback. Prefer
the user's requested GPT-5.6 Terra where the runtime supports it; do not silently
substitute a more expensive model or claim a model was used when it was not.

Keep at most three parallel assignments, with disjoint output ownership.
Reviewers are read-only. One integrator owns the final document files. For each
dispatch record task ID, role, model, inputs/hashes, allowed output paths, result
and completion status. Inspect partial artifacts before resuming failed agents;
do not rerun completed work or grant reviewers permission to launch solvers.

### Required overrides to the imported kit

1. The agents contain thesis paths, MSLAP/Savoye objectives and journal defaults
   unrelated to this task. Do not import them. In particular, use **P, O, S,
   zeta_s, L_p, x_ps, z_os and Phi_s** with the companion's meanings. Build a
   symbol map: companion C_s means line capacity, whereas internal robustness
   notes use C_s for slots. Use zeta_s for slots in new exposition; mark V_s/T_s
   as inherited context, not active share-model parameters. Audit collisions
   involving q, lambda, n and scenario indices rather than copying blindly.
2. The `mathematical-formulation` skill's generic advice to change the objective
   and add recourse does not apply. This is static assignment with robust
   feasibility rows and a historical visit objective, not a two-stage model.
3. `robust-modeling` is a review checklist, not a source of unverified theorems.
   Do not import its generic probability bounds or claim that universal station
   and scenario quantifiers fail to commute under coupled uncertainty. Different
   stations may have different worst-case witnesses while all rows share one U.
4. Do not mechanically demand Wilcoxon tests, 95% reliability intervals or extra
   seeds because a results skill lists them. Three seeds describe optimizer
   variability at one future, not a sample of future deployments. Report values
   and ranges; distinguish descriptive averages from inferential estimates.
5. `scientific-writing-loop` is IJPR-oriented and can route failures to coding or
   more tests. Use its reviewer/writer separation only, with the current scope
   and venue policy. `REVISE_METHOD`, `REVISE_CODE` and `MORE_TESTING` mean **stop
   and report**, not launch another workflow. Limit review cycles to three and
   return unresolved substantive disagreements to the user.
6. `structure-review` dispatches **thesis-structure-reviewer, which is absent**.
   Use the available `narrative-reviewer` for article structure and
   `formulation-reviewer` for cross-document notation. `latex-thesis-build` is
   also absent: inspect available LaTeX tools and use their ordinary build route.
7. `research-gap` assumes NotebookLM. The referenced notebook mapping is absent;
   use the web/source-document channel alone unless configured by the user.
   Do not upload private data or unpublished manuscripts to a new external tool.
8. Graphify navigation is optional if an existing usable graph is available;
   otherwise use rg and direct reads. Do not install Node, build a graph or run
   an indexing campaign merely to satisfy a role's graph-first wording. Use
   Python/PowerShell for approved evidence tooling. Missing imported scripts
   are not evidence that the source data or research is missing.
9. Never use the writing agents' supplied "no generative AI" declaration.
   No automated assertions about funding, conflicts, authorship or release rights.
   Use current official venue rules rather than copied IJPR word/float ceilings.
10. `no-ai-slop` has an existing `ACADEMIC_ADAPTER.md`: Detect-only, no numerical
    or citation edits. Use it through the narrative review, not as another
    autonomous writer. Humanizer/style passes must preserve technical terms,
    necessary qualifications and scientific meaning; do not claim AI-detection
    scores or remove uncertainty to make prose sound more confident.

Useful core skills, all present under `.claude/skills/`: `planning-with-files`,
`results-report`, `results-analysis`, `citation-verification`,
`literature-review-citation`, `mathematical-formulation`, `robust-modeling`,
`algorithm-documentation`, `experimental-results-presentation`,
`reviewer_first_skill`, `operations-research-scientific-writing`,
`sparring-partner-review`, `paper-self-review`, `verification-loop`.
The OR skill's internal name is `or-scientific-writing`; its directory has the
longer name. Use `academic-paper` for approved structure/formatting assistance,
not to bypass the first-draft gate. Use prose skills after scientific structure
is stable; invoking every skill on every section is unnecessary.

## 6. Five gated work packages after scope approval

All paths below are relative to `reports/horizon_robustness_results/writing/`,
which is a **proposed new output directory**, unless stated otherwise. Existing
campaigns, generated evidence, predeclarations, ledger history, solver code and
protected companion sources are read-only inputs. Do not retrofit the original
predeclaration or change an implementation hash to make the narrative simpler.

### Step 1: Freeze the evidence and claim boundaries

Owner: orchestrator using `planning-with-files` and `results-report`.
Reviewer: `results-integrity-reviewer` with `results-analysis` in audit mode.

Deliver `task_plan.md`, `claims.md`, `source_manifest.json`,
`verification_inventory.md` and `open_questions.md`. Include the eight prior
claims C1-C8 with the corrections in section 2 above. Each strong claim needs:
type (assumption/theorem/observation/interpretation/recommendation), exact source
path/hash, campaign/rule, evaluated unit, denominator, endpoint status and allowed
wording. Record review dates and distinguish re-run checks from inherited logs.

Do not close R2/REPORT or produce the final STUDY_REPORT as an automatic side
effect of this preparatory package. Report the existing gates accurately.

Gate: no unsupported headline, hidden non-return, pooled incompatible rule, or
unqualified future guarantee. Reviewer PASS must cite the checked artifacts.

### Step 2: Positioning, mathematical preflight and author-approved architecture

Parallel advisory assignments:

* `academic-researcher`: `literature_evidence.md`, using the web channel of
  `research-gap`, `citation-verification` and `literature-review-citation`.
  Return verified source records and claim locations for author assessment;
  not an autonomous final related-work section or invented complete bibliography.
* Orchestrator using `mathematical-formulation`, `robust-modeling` and
  `algorithm-documentation`: `notation_bridge.md` and `method_notes.md`.
  These are internal technical notes for author review, not a manuscript draft.
* Orchestrator: `companion_overlap.md`, `outline.md`, `venue_policy.md` and
  a proposed author-responsibility/AI-use record.

Required mathematical preflight:

1. Exact share denominator and fixed-product terms; unique assignment and slot
   equality; fixed and movable products touching one station count one visit.
2. Upper-only implied lower bounds versus true two-sided policy. Explain why
   the original upper-only screen does not answer full profile preservation.
3. Distinguish delta (evaluation policy), lambda (reserved design margin), nu
   (inactive-product mass), and numerical validation tolerance. At the focal
   policy, evaluation is +/-2 pp and TIGHT trains inside +/-1 pp. None is the
   companion's 10% relative workload allowance.
4. Derive both endpoints of the historical-hull/activation set, including the
   lower trapped-activation indicator when **all** inactive products are assigned
   to a station. Check empty Z, zero/full activation, fixed inactive products and
   clipped zero/one band endpoints. Match the corrected implementation, not the
   older upper-only exposition in MATHEMATICAL_SCOPE.
5. Give floor/ceiling integer-count restatements with exact rational thresholds.
   Do not equate a finite-precision solver return with an exact certificate;
   record range/representation conditions and retain independent revalidation.
6. State separately the conditional U-membership guarantee, the sufficient TV
   margin bound, and their lack of certification of the realized futures.
   Low-dimensional hull restrictions are explanatory, not an impossibility proof
   for all historical-scenario approaches.
7. Review matched nested-horizon set inclusion and its assumptions. It gives no
   monotonicity of realized future compliance or of time-capped returned costs.
8. No new distributional assumptions, recourse, calibration algorithm or proof
   of unattainability may be introduced to repair an empirical limitation.

Reviewers: `positioning-reviewer` on literature/overlap;
`formulation-reviewer` on notes; `plan-reviewer` on the integrated plan, with
`operations-research-scientific-writing` and `sparring-partner-review` for the
argument stress test. Demand reasons, not merely matching verdict labels.

Suggested **article architecture**, not a required nine-section lab chronology:

1. Motivation, companion boundary and closest literature.
2. Decision problem and the information available at deployment.
3. Share-policy model, uncertainty sets, tightening controls and exact counterpart.
4. Data, preprocessing, horizon protocol and staged experimental design.
5. Comparative evidence: held-out factorial as the centrepiece; exploratory
   upper-only/two-sided findings clearly identified as context.
6. Interpretation, set-coverage diagnostics, operational meaning and limitations.
7. Conclusions within the tested scope.

The staged-design table must make the real chronology visible even if the Results
section leads with the strongest evidence. Do not rewrite exploratory choices as
if the entire programme had been predeclared at its beginning.

**Gate:** review findings resolved or explicitly returned; user approves the
scientific framing, outline, target venue and permitted author/agent workflow.
If novelty does not survive the closest-work check, stop here for a decision.

### Step 3: Reproducible evidence package, no new solves

Owner: one evidence-preparation assignment using
`experimental-results-presentation`; integrator owns merges. Produce a small
Python generator under `writing/tools/`, plus `numbers.json`, `numbers.tex`,
`tables/`, `figures/` and `reproduce.md`. No solver-package edits are authorized.

All **repository-derived empirical numbers** in prose/tables/captions must come
from the generator, including companion comparison values through an audited
source registry. This does not require macros for mathematical constants,
equation indices, publication years or ordinary section numbers. Compute from
exact counts/rationals where stored; round only at presentation. Make source
selection deterministic, exclude runtime timestamps from deterministic outputs,
and test that a second generation produces identical content.

Minimum useful outputs:

* Study-design table: exploratory/held-out status, 29 versus four synthetic
  instances, rule, delta, horizon, origin, seeds, budgets, reused solves and
  scored/non-returned denominators. Separate ten audited directories from the
  smaller set of non-superseded campaigns used for scientific analysis.
* Complete held-out table: every seed; joint compliance; upper/lower breaches;
  worst breach; maximum absolute target deviation; visits/order. Include the
  same-future incumbent as context, not as a moving feasibility standard.
* Cost versus target-deviation plot showing all returned seed layouts, not a
  fitted frontier. Distinguish a maximum over seeds from a mean across seeds.
* Station deviations relative to b_s with the policy band: three seed facets
  showing all four arms and the incumbent, or an explicitly labelled seed range.
  Never select the best-looking seed or average assignments into a fictitious
  deployable layout.
* Matched-cell delta response and horizon-transfer evidence if they add a
  distinct message. Captions state separately optimized models and dependent
  horizons; wider bands do not imply monotonically better future compliance.
* Scenario-envelope/TV diagnostics, labelled **ex post**. Keep product-vector
  membership distinct from station-direction witnesses: outside an envelope
  proves non-membership, but inside every envelope does not prove membership.
* Supplementary full outcomes: failed/non-returned cells, numerical qualifications,
  solve reuse, exclusions and non-replayable diagnostics without inventing missing
  witnesses. Do not promote pilot output to confirmatory evidence.

Reviewers: `results-integrity-reviewer`, `formulation-reviewer` where derivations
appear, and `narrative-reviewer` for economical presentation. Gate includes
anonymization of the actual new output paths and visual inspection at print size.
Existing anonymization success does not automatically cover a new directory or
labels rendered inside figures. No private site/station codes in public outputs.

### Step 4: Author-led drafting or a separately approved permissible writing route

Owner: human authors, with one `academic-writer` assignment integrating permitted
editing/formatting. `clean-scientific-writer` is an optional later
prose-editing pass, not a simultaneous owner of the same files.

For IJSSOL, apply section 1's author-draft gate; do not relabel agent output as
author-written. For another venue, document its policy and obtain workflow approval.

New document paths only, initially `writing/manuscript.tex`,
`writing/supplement.tex`, and a separate author-verified bibliography assembled
from verified source records. Final naming/template is chosen at the author
gate; no protected root manuscript or bibliography is overwritten.

Use `academic-paper` for approved structure/LaTeX scaffolding;
`reviewer_first_skill` for contribution hierarchy and claim status;
`paper-self-review` for internal consistency. Run the **adapted**
`scientific-writing-loop`: read-only scientific review, permitted writer revision,
read-only narrative review. Use `academic-prose-auditor` near the end and the
existing `no-ai-slop` academic adapter in Detect-only mode. Preserve necessary
qualifications and the author's scientific meaning through every language edit.

Allowed: "conditional robust feasibility for U" with its assumptions; "optimizer
seed replication" when explicitly qualified. Forbidden: universal future
reliability, an empirically calibrated automatic margin rule, a new exact optimizer,
proven optimal protection cost, or independent-demand replication from three seeds.

Gate: all scientific/model/result/citation blockers resolved; author approval of
the actual argument and disclosures. Agreement among agents is not a proof.

### Step 5: Final handoff for independent assessment, not submission

Reviewers: `scientific-reviewer`, `results-integrity-reviewer`,
`formulation-reviewer`, `positioning-reviewer`, then `narrative-reviewer` for
whole-article structure. Use `verification-loop` only within the approved scope.

Compile the new manuscript and standalone supplement; inspect both PDFs for
equations, references, tables, clipped/overlapping figures, fonts and anonymity.
Check source-to-macro-to-PDF traceability, source hashes, bibliography claims and
unchanged protected files. Use the repository's existing tools after reading
their interfaces, not invented switches:

* `tools/horizon_robustness/verify_campaign.py`
* `tools/horizon_robustness/check_protected_sources.py`
* `tools/horizon_robustness/check_anonymisation.py`
* `tools/horizon_robustness/check_scoring_regression.py`

Account for any verifier that writes reports: redirect to the approved writing
outputs where supported, or obtain permission before overwriting evidence.
Hash-only unchanged inputs can reuse the documented expensive revalidation, with
date and scope disclosed; do not claim it was rerun. A full stored-layout replay
is not a new solve but its time should still be stated before launching. No native
solver tests or new campaigns are implicitly authorized by a writing review.

Deliver `review_handoff.md` containing files and hashes, reproducible commands,
all specialist findings and their disposition, remaining limitations, policy/author
approvals, and the exact conclusions for the original assistant and user to
examine together. Do not declare the study accepted, mark final author gates
complete, submit a paper, or initiate the dated alternative.

## 7. Reading order and return conditions

Read in this order; paths in the first group are under
`reports/horizon_robustness_results/`:

1. This reviewed proposal; `EXPERIMENT_REVIEW_HANDOFF.md` sections 1-13;
   `CAMPAIGN_PREDECLARATION.md` sections 1-9; `INDEPENDENT_REVIEW_20260913.md`.
2. Current companion main/supplement/baseline bibliography listed in section 3.
3. `DATA_PROVENANCE.md`, `MATHEMATICAL_SCOPE.md`, `PILOT_FINDINGS.md`,
   `INDEPENDENT_REVIEW_20260911.md`, `analysis_audit.md`, `artifact_index.json`.
4. `reports/horizon_robustness_plan/INDUSTRIAL_AMENDMENT_20260909.md`,
   `PLAN.md`, `RUNNER_CONTRACT.md`, `BACKEND_CONTRACT.md` and `GATES.md`
   in that same plan directory; later predeclarations/amendments control changes.
5. `.unlazy/horizon-cslap/status.log`, `preserved_sources.json`, `GATES.md`
   and `gates/` in that ledger directory; treat historic entries as historic.
6. Relevant role/skill files from section 5, then the tables and case records
   supporting the assigned task. Case records live under
   `reports/horizon_robustness_results/campaigns/`; plotting/analysis code under
   `Baselines/horizon_robustness_analysis/`; tested model code under
   `Baselines/horizon_robustness/` and `tests/horizon_robustness/`.

Do not treat `REVIEWER_BRIEF.md` or a superseded campaign as current simply because
it is easy to find. Do not assume paths in the previous plan's bare filename list
are all in one directory.

Return to the user instead of continuing if a source/derivation disagrees with the
claim, a protected input changed, substantive novelty cannot be defended, a
publisher-policy conflict remains, or further experimental authority is needed.
Distinguish these from non-blocking limitations already accepted for this scope.

Immediate approval sought: this corrected scope and staged workflow. Initial
delegation should complete Steps 1-2 and return the evidence/positioning/outline
package for author approval. It must not silently proceed to manuscript drafting.

Review approach: the project's sparring-partner-review and OR scientific-writing
skills informed the adversarial claim checks; citation-verification informed the
primary-source and version checks. Their inherited project/venue defaults were
not adopted.
