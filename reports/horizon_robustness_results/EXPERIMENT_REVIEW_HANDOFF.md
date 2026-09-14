# Experiment review handoff

Status: **Complete.** The screening campaign finished on 11 September 2026 and
every section is evidenced against final artifacts. This file is written so another agent can
audit the experimental work without relying on any conversational summary.

**Read these first, in this order:** `PILOT_FINDINGS.md` (what was measured and
what it does and does not show), `CAMPAIGN_PREDECLARATION.md` (what was fixed in
advance, and the diagnostic stop decision), `analysis_audit.md` (denominators and
pseudoreplication rules), then §6 and §10 below (code changes, and the
provisional reading with its competing explanations).

Scope: **E2** (execution) and **R1** (analysis). **R2 is deliberately untouched** —
no robustness manuscript, no publication-style final report, no edit to the
submitted deterministic-CSLAP article or its supplement, and no final verdict on
whether the undated approach succeeds, fails or is publishable. Those remain open
for the joint review by the user and the original assistant.

---

## 1. Completed scope

### 1.1 Done

* **Baseline independently reproduced.** The inherited claim of 152 shared/CPLEX
  + 21 Hexaly tests was re-run and confirmed before any new work.
* **Engineering pilot (Stage A) executed** under an explicit resource approval, at
  the quoted ceilings. First attempt invalidated by an operator error and
  preserved as superseded; second attempt complete. See `PILOT_FINDINGS.md`.
* **Industrial buildability measured for the first time** — the previously
  untested question from the 9 September checkpoint. The full 21,874-product,
  24-station model builds in 309–338 s and peaks at 2.93 GB, under a tenth of the
  quoted ceiling.
* **A numerical-policy escalation raised and resolved** without weakening any
  declared tolerance, via an exactly equivalent integer-count restatement of the
  fixed-cap rows, verified by layout-by-layout enumeration and a bounded
  industrial recheck.
* **Predeclared minimum-slack diagnostics executed** — 6 CPLEX solves, 4 cases
  constructively resolved, 2 left explicitly unresolved. Qualification (11 Sep):
  those six runs predate the witness-saving version of the diagnostic tool, so
  their layouts were logged but not saved and the runs are **not replayable**;
  the bounds stand as logged results, and the tool now saves every witness.
* **R1 analysis layer implemented and tested** — flat case frame, status and
  denominator audit, paired comparison, three-level aggregation, frontier tables,
  min-slack table, station tables, resource table, cross-horizon rescoring, and
  five figures, all regenerating from immutable artifacts with no optimizer.
* **Exploratory revision 2 executed** (12 September): the two-sided rule
  implemented without changing any upper-only hash, predeclared, quoted, approved
  separately, run as three campaigns (44 solves, 54,300 s configured), every
  layout revalidated and cross-horizon rescored, and reported separately in §12.
* **Exploratory revision 3 executed** (13 September): the held-out factorial on
  the unexamined tail of the BERNER stream, predeclared, quoted, approved
  separately, run (12 solves, 21,600 s), revalidated, and reported separately in
  §13; its predeclared replication endpoint is met and its factorial reading
  attributes compliance to the reserved margin, not to the scenarios.
* **Verification tooling** for campaign accounting, authorization, independent
  revalidation, publication anonymisation and protected-source integrity.
* **Test suite grown from 173 to 241** (218 shared/CPLEX + 23 Hexaly), with every
  new behaviour covered and negative controls where absence is being asserted.

### 1.2 Not done, and explicitly so

* **Stage B screening COMPLETED** on 11 September 2026: 360/360 cases,
  153/153 unique solves, exactly 66,600 s charged against 66,600 s quoted,
  21.46 h elapsed inside the 100,000 s wall cutoff. It was launched to be handed
  off mid-run but finished within the session, so no resume was required and no
  retry was used. §8.1 keeps the resume command for future extension.
* **Stage F cross-horizon transfer completed**: 624 secondary evaluations of
  already-frozen screening layouts plus 12 from the pilot, none
  `INSUFFICIENT_FUTURE`, no new optimization.
* **Stage D (δ, ν, λ frontiers) not executed for the upper-only rule.**
  Sensitivities were within the ~30 h authorization in principle, but screening
  was prioritised on the user's instruction and the upper-only frontiers were
  never quoted or launched. They are *not executed* — not omitted for looking
  unpromising, and not exhausted out of budget. The ≈9.1 unspent hours were later
  committed, with a further separate approval, to exploratory revision 2 (§12),
  which ran a δ sensitivity for the two-sided rule on BERNER only (0.01 / 0.02 /
  0.03). The ν and λ frontiers remain unrun under both rules, the λ frontier by
  the user's explicit decision.
* **No seed replication, no second origin.** Outside the authorized budget.
* **No certified lower bound above δ anywhere**, so nothing is proven
  unattainable.
* **R2 untouched by design** — no manuscript, no final report, no edit to the
  submitted article, no verdict on the research direction.

## 2. Protocol and configuration revisions

**No scientific parameter changed in the upper-only study** (exploratory
revision 2, below, changed the rule and the primary δ for its own campaigns
only). The primary scientific question, the two
approved data sources, the horizon design `{ceil(P/2), P, 2P}`, δ = 0.01 and its
grid, ν = 0.01 and its grid, the λ grid, the four arms, the uncertainty family,
the closed-catalogue and frozen-product policies, the upper-only ceilings and the
future evaluation rules are all exactly as in `PLAN.md` as amended by
`INDUSTRIAL_AMENDMENT_20260909.md`. `configs/horizon_robustness/protocol.json` was
unmodified throughout the upper-only study; exploratory revision 2 (below) is
the only change ever made to it.

Two **execution-contract** revisions were made, both recorded as revision 1.3 in
`.unlazy/horizon-cslap/PLAN.md`, and neither touching the science:

1. **E2 ownership corrected** from `results/horizon_robustness/**` to
   `reports/horizon_robustness_results/campaigns/**` and `.../manifests/**`. The
   implemented runner writes campaigns there; the handoff table named a directory
   the code never used.
2. **R1 ownership moved** from `Baselines/horizon_robustness/analysis.py` to a
   separate package `Baselines/horizon_robustness_analysis/`. Reason in §6.

A predeclared campaign design for stages B–F is in
[`CAMPAIGN_PREDECLARATION.md`](CAMPAIGN_PREDECLARATION.md), written before any
stage-B execution.

**Exploratory revision 2 (12 September 2026) — the two-sided rule.** After the
upper-only confirmatory study was complete and independently reviewed, the user
stated the intended business rule as *every station stays within ±δ of its
historical share* and asked that the slack be chosen from the data rather than
imposed. `TrainingProblem` gained a `rule` field (`upper_only` | `two_sided`)
with floors f_s = max(0, b_s − δ) alongside the existing ceilings. The rule is
serialised and hashed **only when two-sided**, so every upper-only input, model,
manifest-row, case and certificate hash is byte-identical to before the change;
the four arms' hashes were pinned before the edit and are asserted by
`tests/horizon_robustness/test_two_sided.py::HashStabilityTests`.
`configs/horizon_robustness/protocol.json` **was** changed for this revision and
for nothing else: `0.03` joined the δ grid and `rules` / `two_sided_delta = 0.02`
were introduced. The δ choice (0.02 primary because the warehouse's own history
violates ±1; 0.01 kept as the aspiration; 0.03 as the fallback), the five-dataset
subset, the budget and the reporting rules were predeclared in
`CAMPAIGN_PREDECLARATION.md` §8 before any two-sided solve. Two-sided results are
reported **separately** from the upper-only study, are never pooled with it, and
carry `rule = two_sided` in every table row.

**Exploratory revision 3 (predeclared 13 September 2026) - the held-out factorial.** After the 13 September independent review, and with the user's decision of the same day, a two-by-two on the unexamined tail of the BERNER stream was predeclared in `CAMPAIGN_PREDECLARATION.md` section 9: scenarios and activation on or off, crossed with a reserved optimisation margin on or off, giving NOM, TIGHT, HIST+ACT and the new arm HIST+ACT-T (HIST+ACT's model optimised inside the tightened band). One deployment origin at order index 243,151, the focal horizon n = P, the two-sided rule at delta = 0.02, nu = 0.01, lambda = 0.5, seeds 11/22/33, 12 solves. Its purpose is to isolate the margin mechanism that revision 2 could only be consistent with. It has its own quote and needs its own launch approval; nothing in sections 1-8 or in section 12 changes because of it. The code it needs (the arm, a `holdout` quote stage with the explicit origin, and `holdout_origin` in the protocol) was added after every stored layout had been revalidated under the 13 September repairs, and the four upper-only arms' hashes remain pinned.

## 3. Campaign, manifest, table and figure index

The machine-readable inventory is [`artifact_index.json`](artifact_index.json),
regenerated by the analysis command in §8. It lists every campaign with its
manifest and implementation hashes, every table with row/column counts and a
content hash, every figure, and every campaign excluded as superseded.

### 3.1 Campaigns

| Directory | Stage | Manifest hash | Implementation | Rows | Unique solves | Quoted native s | State |
|---|---|---|---|---:|---:|---:|---|
| `campaigns/pilot_20260910/` | pilot | `7878826ca850…` | `c17ef16e9900…` | 8 | 8 | 6,840 | **SUPERSEDED**, preserved, excluded from all analysis |
| `campaigns/pilot_20260910b/` | pilot | `8d36ea49ad1b…` | `36ed25e9052d…` | 8 | 8 | 6,840 | complete |
| `campaigns/screen_20260910/` | screen | `64178e37f4df…` | `d437a2066053…` | 360 | 153 | 66,600 | complete (11 Sep, inside the session; no resume, no retry) |
| `campaigns/twosided_screen_d02_20260912/` | screen, `two_sided`, δ = 0.02, 5 datasets | `4d0b6fbe8eac…` | `5e1ee22fe313…` | 60 | 28 | 25,500 | **SUPERSEDED** — launch attempt 1 crashed before its first solve (path length, §7.5); 0 solver s; preserved |
| `campaigns/twosided_berner_d01_20260912/` | sensitivity δ, `two_sided`, δ = 0.01, BERNER | `13e5bf8bc5d3…` | `5e1ee22fe313…` | 12 | 8 | 14,400 | **SUPERSEDED** — same failure; 0 solver s; preserved |
| `campaigns/twosided_berner_d03_20260912/` | sensitivity δ, `two_sided`, δ = 0.03, BERNER | `756a6ad746b4…` | `5e1ee22fe313…` | 12 | 8 | 14,400 | **SUPERSEDED** — same failure; 0 solver s; preserved |
| `campaigns/ts_d02_20260912/` | screen, `two_sided`, δ = 0.02, 5 datasets | `4d0b6fbe8eac…` | `5e1ee22fe313…` | 60 | 28 | 25,500 | complete (12 Sep 08:51 UTC): 58 COMPLETE, 2 NO_INCUMBENT_LIMIT; 25,500 s charged; 31,879 s elapsed |
| `campaigns/ts_b01_20260912/` | sensitivity δ, `two_sided`, δ = 0.01, BERNER | `13e5bf8bc5d3…` | `5e1ee22fe313…` | 12 | 8 | 14,400 | complete (12 Sep 14:13 UTC): 12 COMPLETE; 14,400 s charged; 19,338 s elapsed |
| `campaigns/ts_b03_20260912/` | sensitivity δ, `two_sided`, δ = 0.03, BERNER | `756a6ad746b4…` | `5e1ee22fe313…` | 12 | 8 | 14,400 | complete (12 Sep 19:36 UTC): 12 COMPLETE; 14,400 s charged; 19,361 s elapsed |
| `campaigns/ho3_20260913/` | holdout (revision 3), `two_sided`, delta = 0.02, BERNER, origin 243,151, n = P, 4 arms x 3 seeds | `d4d4ed6c9772…` | `4e359efde84f…` | 12 | 12 | 21,600 | complete (13 Sep 17:41 UTC): 12 COMPLETE; 21,600 s charged; 29,066 s elapsed; no retry |

### 3.2 Manifests

`manifests/pilot_20260910.json`, `manifests/pilot_20260910b.json`,
`manifests/screen_20260910.json`; revision 2:
`manifests/twosided_screen_d02_20260912.json`,
`manifests/twosided_berner_d01_20260912.json`,
`manifests/twosided_berner_d03_20260912.json`.

### 3.3 Tables (`tables/`)

`case_frame`, `status_by_cell`, `resources`, `paired_cases`, `instance_summary`,
`stratum_summary`, `paired_stratum_summary`, `cross_horizon`,
`station_profile_industrial`, `station_profile_synthetic`,
`min_slack_diagnostic_cplex`, `slack_survey`, `slack_survey_cross_arm`,
`dispersion_survey`, `two_sided_novelty_survey`, `drift_survey`, and — since exploratory revision 2 put a second δ value on
disk — `frontier_delta` (per campaign) and `frontier_delta_pooled_by_rule`
(pooled across campaigns only inside one rule and implementation hash, naming
every campaign it merged). Every table row carries `rule`; the case frame also
carries `implementation_hash`, `cap_violation_count` and
`floor_violation_count`, and the station tables carry `floor`,
`floor_residual` and `below_floor` (empty for upper-only rows). Each row count
and content hash is in `artifact_index.json`. The ν and λ frontier tables
remain *not produced*, with the reason, because those sensitivities never ran.

### 3.4 Figures (`figures/`)

`joint_compliance_by_horizon`, `visits_versus_excess`, `status_breakdown`,
`station_profile_industrial`, `cross_horizon_transfer`, and `frontier_delta`
wherever a campaign has more than one δ value. The publication set in
`figures/` is drawn from the largest screening campaign (`screen_20260910`,
upper-only); every other campaign, the two-sided ones included, has an
engineering set under `figures/<campaign>/` labelled as such in its own titles,
and `figures/pooled/<rule>__<implementation>/` holds frontier figures pooled
across campaigns of one rule and implementation. Two-sided figures say "band,
cap and floor" and "band breach" where upper-only ones say "cap" and
"excess", and the two-sided station profile draws the floor beside the
ceiling. Every figure prints its own denominator and has a CSV counterpart as
its accessible table view.

### 3.5 Diagnostics (`diagnostics/`)

`berner_recheck_HISTACT_*.json` (numerical formulation recheck) and
`min_slack_*.json` (predeclared min-slack diagnostic), each with its own content
hash.

### 3.6 Governing documents written this session

`CAMPAIGN_PREDECLARATION.md`, `PILOT_FINDINGS.md`, `analysis_audit.md`,
`artifact_index.json`, `campaigns/pilot_20260910/SUPERSEDED.md`, and
`MATHEMATICAL_SCOPE.md` §10; later in the session `CAMPAIGN_PREDECLARATION.md`
§8 (exploratory revision 2), `REVIEWER_BRIEF.md`, the original assistant's
`INDEPENDENT_REVIEW_20260911.md`, and the three
`campaigns/twosided_*/SUPERSEDED.md` records.

## 4. Expected versus completed / ineligible / failed / unresolved counts

Authoritative source: [`analysis_audit.md`](analysis_audit.md), "Denominator
audit". Every authorized manifest row falls into exactly one of: ineligible by
protocol, no record at all, returned no allocation, allocation returned but not
scored, scored on its future horizon. The audit asserts
`accounting_complete`; `tools/horizon_robustness/verify_campaign.py --all` fails
if any row is unaccounted or if an unallocated row carries a metric value.

As regenerated on 13 September 2026 over the six non-superseded campaigns
(upper-only pilot and screening; two-sided screen and two BERNER δ sensitivities;
the revision-3 held-out factorial):

| Bin | Rows |
|---|---:|
| Authorized rows | 464 |
| Ineligible by protocol | 0 |
| No record at all | 0 |
| Returned no allocation | 52 |
| Allocation returned but not scored | 0 |
| Scored on its future horizon | 412 |
| **Accounted** | **464** |

`accounting_complete = 1`, and `verify_campaign.py --all` passes **strictly** over
all ten campaign directories, the four superseded ones included:
`CAMPAIGN ACCOUNTING VERIFIED (10 campaign(s))`.

The 52 unallocated rows are 48 upper-only screening `NO_INCUMBENT_LIMIT` results,
the pilot's 1 `NO_INCUMBENT_LIMIT` and 1 `NUMERICAL_ISSUE`, and the two-sided
screen's 2 `NO_INCUMBENT_LIMIT` (the shared HIST/HIST+ACT solve of the 50-product
warehouse at n = P/2). None carries a metric value. **All 48 screening `NO_INCUMBENT_LIMIT` results are in the 50-product
family**, where the robust arms returned a layout in only 12 of 36 cells; every
other family returned 100 %.

**Expected versus completed.** Pilot expected 8, completed 8. Screening expected
360 rows / 153 unique solves, completed 360 / 153. All 360 screening rows were
eligible: no `INSUFFICIENT_HISTORY` or `INSUFFICIENT_FUTURE` at the first origin
for any approved dataset. Stage F expected and produced 624 secondary
evaluations. Stage D (δ, ν, λ frontiers) was **not executed** — screening was prioritised and the frontiers were never quoted or launched, so the campaign schedule, not the budget (≈9.1 configured solver-hours were left unspent), did
not reach them.

**Exploratory revision 2 (12 September).** Expected 84 rows / 44 unique solves over
three campaigns, completed 84 / 44: 82 `COMPLETE`, 2 `NO_INCUMBENT_LIMIT`, all rows
eligible, no retry, no cutoff. Its Stage F produced the expected 164 secondary
evaluations (116 + 24 + 24), none `INSUFFICIENT_FUTURE`. Its first launch attempt
produced three directories with 0 solves and 84 `CAMPAIGN_ERROR` rows (§7.5),
preserved and superseded; they are accounted by the verifier and excluded from
every table.

**Exploratory revision 3 (13 September).** Expected 12 rows / 12 unique solves,
completed 12 / 12, all `COMPLETE`, no retry, no cutoff; every layout independently
revalidated. Its predeclared endpoints are read in §13.

**Gate ledger:** 48 met, 4 unmet, 0 abandoned across the 18 leaf and node gate
files, plus the two root gates in `GATES.md` unmet: 48 met / 6 unmet in all
(45 / 7 as written on 11 September; the change is R1:G2). All four E2 gates were
re-met over the ten campaign directories on 13 September, and R1:G2 is met on
the only frontier ever executed (the two-sided δ axis), with its scope stated in
the gate file: the ν and λ axes have no executed frontier under either rule. The
gates that remain unmet are R2:G1 and R2:G2 (deliberately outside this
delegation), the two REPORT node gates and the two root gates that depend on
them. None is abandoned.

## 5. Source, implementation and runtime identities

**Empirical sources.** Only the two allowlisted entries were read:
`exp02a_instances/` (exactly the 29 approved instances) and
`Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv`
(SHA-256 `c488e8aac63a052570551602b58e781aebf9aa93819dc943fdbaa6244ebb7048`).
No ISCF data, no dated BERNER alternative and no substitute benchmark was
introduced. `Baselines.horizon_robustness.protocol.allowed_source` rejects
anything else, and `verify_campaign.py --all` re-resolves every source path
recorded in every manifest row through that allowlist.

**Protected files.** The 92 preserved empirical-source, submitted-manuscript and
original-plan files in `.unlazy/horizon-cslap/preserved_sources.json` were
re-hashed on 10 September 2026: **92/92 unchanged**. Re-run with
`tools/horizon_robustness/check_protected_sources.py`. The shared industrial
loader `data_loader_industrial.py` is among them and is unchanged; the adapter
calls it, it was not replaced by an approximate cleaner.

**Runtime.** Both interpreters are the approved ones, unmodified, with no package
installed, upgraded or removed and no licence change:

| | CPLEX environment | Hexaly environment |
|---|---|---|
| Interpreter | `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe` | `C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe` |
| Python | 3.10.11 | 3.10.11 |
| Solver | cplex 22.1.1.0 | hexaly 13.0.20241205 |
| numpy / pandas / scipy / psutil | 2.2.1 / 2.2.3 / 1.15.3 / 6.1.1 | 2.2.1 / 2.2.3 / 1.15.3 / 6.1.1 |

**Implementation identity.** Every manifest pins `runtime.implementation_hash`, a
SHA-256 over the SHA-256 of every `*.py` in `Baselines/horizon_robustness/`. Six
values appear in this session's artifacts:

| Implementation hash | Meaning |
|---|---|
| `c17ef16e9900d5bbac77b57c85b094d0118b5ce9890e2e283e8b256c73072658` | code as inherited on 10 Sep 2026, identical to the 9 Sep checkpoint |
| `36ed25e9052df5e9e194ce83cca3cb1dfdf907948bb1feea408e636f8614a044` | after the `runner._diagnose` child-log fix (§6.1); the pilot ran under this |
| `d437a20660533119d9e58e7d8ff16e900f5db97d004e6aacb88d106866d8a2af` | after the exact integer-count row restatement (§6.6); the upper-only screening ran under this |
| `5e1ee22fe31372d86e4c549f747604b9d3b46524182a516efb7f247833b261f8` | after the two-sided rule extension (§2, revision 2), hash-preserving for every upper-only input; the three two-sided campaigns ran under this |
| `aceb839d6b1ef020bf74e92c0f14682892c926e25baaacac81fe4e6b2fa0e732` | after the 13 September repairs (§6.8): trapped-activation lower endpoint, two-sided min-slack helper, upper-only scoring regression, lower-direction novelty. No campaign ran under it; every stored layout of every campaign revalidates under it |
| `4e359efde84f6c4a031409dfa814c0672c8428f08e3922860edaaee02fc13e5b` | after the exploratory revision 3 code (section 2): shared arm sets, the HIST+ACT-T arm, holdout_origin and the holdout quote stage. The four upper-only arms' hashes are unchanged; the revision-3 quote is bound to this hash |

Results produced under different implementation hashes are **never mixed inside
one comparison**. In particular the pilot's two robust-arm rows predate the
integer restatement and are superseded for comparison purposes, while remaining
on disk under their own hash.

Per-campaign manifest hashes are in §3.1. Each is bound to a specific
implementation hash, and `run` refuses to execute a manifest whose sources,
runtime or implementation no longer match.

**Source hashes.** Every manifest row carries the SHA-256 and byte size of each
source file it used, and `verify_campaign.py --all` re-resolves each recorded
path through the allowlist. Nothing outside the two approved sources appears in
any manifest.

## 6. Code changes and their reasons

Every change is listed. None alters the scientific model, the data pipeline, the
evaluation rules or any declared parameter.

### 6.1 `Baselines/horizon_robustness/runner.py` — bounded child-log excerpt

`_log_tail` and `_diagnose` were added, and `_terminal_solve` now publishes the
diagnosed record. When a native attempt returns no result, its immutable
`terminal.json` gains `child_log_tail` with up to 4,000 characters of the child's
stderr and stdout.

*Why.* The first pilot run lost seven of eight solves and the only trace of the
cause lived in a raw `stderr.txt` beside the attempt. A campaign audit must be
able to diagnose a failed attempt from the JSON record alone.

*Verification.* `tests/horizon_robustness/test_runner.py::RunnerTests::`
`test_failed_child_keeps_a_bounded_log_excerpt_in_its_terminal_record` (positive)
and `..._successful_attempt_carries_no_log_excerpt` (negative control). The
positive test was additionally run with `_diagnose` patched to the identity
function and confirmed to fail, so it is not a test that cannot fail.

*Affected artifacts.* This change altered the implementation hash, so the pilot
manifest was regenerated. No prior campaign result was recomputed or discarded by
it.

### 6.2 New package `Baselines/horizon_robustness_analysis/`

`analysis.py`, `figures.py` and `rescoring.py`, plus `__init__.py`.

*Why it is not inside the solver package.* `runner.runtime_metadata()` derives the
campaign implementation identity from **every** `*.py` in
`Baselines/horizon_robustness/`, and a worker fails closed when that identity no
longer matches its frozen request. Analysis code changes constantly during
reporting and can never affect a native solve, so keeping it in the solver package
would mean that editing a table or a figure invalidates every frozen manifest and
blocks an ordinary resume. This is not a hypothetical: it is exactly what
destroyed the first pilot run (§7). The alternative — narrowing the hash to a
declared module list — would have weakened an existing provenance guarantee, so
the lower-risk option was taken and the `AGENT_HANDOFF` ownership row for R1 was
revised instead.

*Verification.* `tests/horizon_robustness/test_analysis.py` (14 controls) and
`tests/horizon_robustness/test_rescoring.py` (6 controls).

### 6.3 Analysis defects found and fixed during self-review

All three were found by re-reading the analysis layer before trusting it, each is
covered by a test, and none affected a solver run.

| Defect | Consequence if unfixed | Test |
|---|---|---|
| Horizon multiple computed by integer division | `n = P/2` reported as multiple `0`, merging the half-horizon stratum into a meaningless bucket | `test_half_horizon_is_not_collapsed_to_zero` |
| A lower bound of 0 accepted as informative in the min-slack diagnostic | η ≥ 0 holds by construction, so Hexaly's trivial 0 bound would be reported as `BOUNDED` and overstate the diagnostic | `test_zero_lower_bound_is_not_reported_as_bounded` |
| Ineligible cells skipped in `instance_summary` | a whole (dataset, horizon) combination silently vanishes from the table — precisely the omission the protocol forbids | `test_ineligible_cell_survives_instance_summary_with_its_reason` |
| **Every aggregation keyed without the campaign** | **the worst of the four.** Two campaigns can hold the same (dataset, origin, n, seed, parameter) cell under *different implementation versions*. The screening campaign's not-yet-executed `MISSING_RECORD` rows silently **overwrote the pilot's real scored results**, so `paired_stratum_summary` reported zero paired instances while genuine pairs existed. It also mixed implementation versions, which the protocol forbids. Fixed by making the campaign part of every grouping key; `both_scored` pairs went from 0 to 4. | `CrossCampaignIsolationTests`, with a verified negative control — restoring the campaign-blind key makes the test fail |

### 6.4 Figure defects found by rendering and looking

Rendered output was inspected, not assumed. Fixed: a subtitle overlapping the
title; two distinct statuses (`MISSING_RECORD`, `PROCESS_ERROR`) drawn in the same
reserved red with no secondary encoding, now separated by texture; fractional tick
marks on integer row counts; a single-group bar chart whose x-range left its tick
off-centre; and — most consequentially — a measured **0 %** bar being visually
identical to an **absent** group, now given its own baseline stub. That last one
matters because the screening run contains many genuine 0 % cells.

### 6.5 New verification and analysis tools

| Tool | Purpose |
|---|---|
| `tools/horizon_robustness/make_analysis.py` | regenerate every table, figure, `analysis_audit.md` and `artifact_index.json` from stored artifacts, with no optimizer |
| `tools/horizon_robustness/verify_campaign.py` | E2 accounting, authorization and independent revalidation checks |
| `tools/horizon_robustness/check_anonymisation.py` | refuse any internal site code in a published table or figure; verifies its own detector against a positive control |
| `tools/horizon_robustness/check_protected_sources.py` | re-hash all 92 protected files |
| `tools/horizon_robustness/check_scoring_regression.py` | re-score stored layouts (returned and incumbent) with the live scoring code and compare every field with the immutable record; `SCORING REGRESSION CHECK PASSED` only on exact agreement (13 Sep) |
| `tools/horizon_robustness/two_sided_novelty_survey.py` | re-score the two-sided BERNER cases under the repaired scorer and report departures from the modelled set in both directions; also asserts the stored fields are reproduced (13 Sep) |
| `tools/horizon_robustness/slack_survey.py` | solver-free reference-layout upper bounds on δ_min |

A convergence probe (re-solving built models at 10/25/50 % of their caps, to
justify a uniform cap reduction) was written and then **offered to the user and
declined**. It was deleted unused and never executed, so **no convergence
measurement exists** and the declared per-solve caps 120/300/600/1200/1800 s are
kept exactly as pre-registered.

### 6.6 Exact integer-count restatement of the fixed-cap rows

`Baselines/horizon_robustness/uncertainty.py` gained `integer_cap_rows()` and the
version tag `exact_integer_counts_v2` (v3 since the 13 September repair of the
lower activation row, §6.8); both backends build those rows in `visits`
mode.

*Why.* The pilot's BERNER HIST+ACT case returned a structurally valid partition
whose exact robust residual was +1.0555e-06, about 100× the declared 1e-8 model
tolerance, so it was rejected as `NUMERICAL_ISSUE`. Hexaly builds in float64 with
an internal feasibility tolerance near 1e-6 and exposes no way to tighten it
(`no_public_feasibility_or_integrality_setting_in_Hexaly_13`). This is the
escalation IC6 anticipates. It was referred to the user, who directed that the
tolerance not be widened and that an exactly equivalent integer restatement be
investigated before any safety margin.

*What it does.* Multiplying a share row by its scenario line total, and the
activation endpoint additionally by ν's denominator, makes both left sides
integers; the right sides are then replaced by their floors. For integer `z`,
`z <= r` and `z <= floor(r)` have identical solution sets, so the feasible set,
δ, the ceilings and the exact validator are all unchanged. The gain is purely
numerical: an integer row cannot be violated exactly by a solver whose
feasibility tolerance is below 1.0. Derivation in `MATHEMATICAL_SCOPE.md` §10.

*Scope limits, as instructed.* Applied to the fixed-cap visits model in **both**
backends so they are compared on identical rows. Minimum-slack diagnostics remain
on the **original rational model**. No tightened model exists, so no bound or
infeasibility from a tightened model is ever used as a certificate for the
original problem.

*Verification.* `tests/horizon_robustness/test_integer_rows.py` enumerates every
storage-feasible layout of small fixtures and requires the integer rows and the
unchanged exact validator to agree layout by layout — all four arms, δ = 0,
clipped caps, exact-floor thresholds, non-empty and empty `Z_H`, ν = 0, ν = 1,
ν-monotone nesting of the accepted set, and int64 range guards with a negative
*and* a positive control. Two initial fixtures admitted no feasible layout at all,
which would have made the assertions vacuous; non-degeneracy guards caught that
and the fixtures were replaced. Hexaly expression types are checked with
`is_int()` after `model.close()`, the build refuses any non-integer row, and the
audit records `row_formulation` and `integer_typed_rows`.

*Bounded industrial recheck.* The same BERNER case, same 1800 s cap:
`exact_validation_valid = true`, `model_feasible_exact = true`, 480/480 rows
integer-typed, exact residual **−1.208e-06** (strictly inside, versus +1.0555e-06
outside), objective improved from 661,527 to 644,839, largest integer left side
1.068e08 against a 9.22e18 limit. Artifact:
`diagnostics/berner_recheck_HISTACT_*.json`. The 1e-5 optimization-only safety
margin fallback was therefore **not** needed and is **not** applied.

*Affected artifacts.* The implementation hash changed, so manifests are
regenerated. `campaigns/pilot_20260910b/` is preserved unchanged under the older
hash; its two robust-arm rows are superseded for comparison purposes.

### 6.7 Exploratory revision 2: the two-sided rule, and the rule-aware analysis layer

*Solver package (implementation hash `5e1ee22f…`).* `schema.TrainingProblem`
gained `rule` with `rational_floors`; `uncertainty.integer_cap_rows` emits
sense-tagged lower rows `Σ x·L ≥ ceil(f_s·T_k)` and, with activation,
`(M−N)·Σ x·L ≥ ceil(M·f_s·T_k)`; both backends honour the row sense and add the
lower excursion to the min-slack objective; `validation` and `metrics` compute
floors, floor residuals, `cap_violation_count` and `floor_violation_count`, with
`joint_pass` over the larger of the two breaches; the runner and the quote carry
`rule` only when two-sided, so upper-only serialisation and hashing are
unchanged (§2). Tests: `test_two_sided.py` (18) and `test_two_sided_hexaly.py`
(2): pinned upper-only hashes, floor arithmetic, layout-by-layout agreement of
the integer floor rows with the exact validator, two-sided ⊆ upper-only nesting,
native two-sided solves on both solvers matching enumeration, and min-slack on
both sides.

*Analysis layer (outside the hash).* Every table carries `rule`; the case frame
carries `implementation_hash`; the status table is keyed by campaign and rule;
`rule_frontier_table` pools campaigns only inside one (rule, implementation
hash) and names every campaign it merged; cross-horizon records are stamped
with their rule (older records default to upper-only); figures word themselves
by rule and the station profile draws floors. Tests: `RuleColumnTests` and
`RuleFrontierPoolingTests` in `test_analysis.py`, two rule controls in
`test_rescoring.py`.

*Tooling defects found and fixed.* `verify_campaign.py --campaign` resolved a
bare name against the working directory and reported the missing file as a
corrupt artifact; it now resolves names under the campaigns root and says
"no campaign manifest". The station-profile note had overprinted the title in
every station-profile figure since before this session, the publication one
included; it is anchored below the legend. The compliance figure's legend is
guarded for a campaign with no scored cell. The dispersion survey is now in the
artifact index.

### 6.8 Repairs after the 13 September independent review

The original assistant's `INDEPENDENT_REVIEW_20260913.md` found one general-model
defect and three secondary ones; all four are confirmed and repaired, none touches
a recorded result, and the argument for that is checked rather than asserted.

* **Lower activation endpoint.** The two-sided model assumed activation mass can
  always be placed outside a station, giving the lowest share (1−ν)·A_sk. When
  *every* inactive product sits at station s the mass is trapped there and the
  lowest share is A_sk. Corrected in the validator's envelope, the integer row
  builder (`exact_integer_counts_v3`: the lower activation row gains the term
  N·T_k·g_s with g_s = 1 exactly when all inactive products are at s), both
  backends (an AND indicator per station), and the min-slack helper. Tested by
  an **independent vertex oracle** that enumerates the uncertainty set's
  vertices directly for every layout of three fixtures, by the reviewer's
  counterexample (validator now accepts the layout with envelope 9/10, 19/200),
  and by native solves on both solvers whose optimum is checked against
  enumeration. **Zero impact on recorded results**: synthetic inactive sets are
  empty, and BERNER's frozen inactive products span several stations in every
  layout (20 stations hold inactive products in the two-sided HIST+ACT layouts),
  so g_s = 0 for every feasible layout of every executed model. Every stored
  certificate revalidates unchanged under the repaired code (§8).
* **Min-slack helper** covered only upward excursions; it now matches the
  validator's two-sided requirement on every layout (reviewer's six-product
  example: 0.2, not 0.1). Revision 2 never ran the min-slack mode, so no stored
  result depends on it. The CPLEX backend's pre-solve check also refused a
  reference layout below a floor; it now treats floor rows like cap rows.
* **Upper-only scoring regression.** Zeros standing in for absent floor
  residuals had clipped `maximum_residual` at zero and would have flagged every
  interior upper-only layout as borderline in any *future* upper-only scoring.
  No stored upper-only evaluation was produced under that code. Fixed, with a
  regression test and with `tools/horizon_robustness/check_scoring_regression.py`,
  which re-scores stored layouts with the live code and compares every field.
* **Lower-direction novelty.** Two-sided evaluations now report stations whose
  realized share fell below the lowest share the uncertainty set allowed
  (`station_novelty_count_lower`, `maximum_novelty_shortfall`). Stored
  evaluations predate this; `tables/two_sided_novelty_survey.csv` supplies it
  for the two-sided BERNER cases by re-scoring under the repaired code.
* **Reporting.** Pooled frontier figures use matched cells only; single-value
  campaigns get no "frontier" figure; §12 counts and wording corrected;
  dispersion wording corrected to "deviation from pooled history"; analysis
  version recorded in the artifact index.

### 6.9 Exploratory revision 3 code (13 September)

Applied only after every stored layout had been revalidated under the 13
September repairs, so the two hashes stay separable in the record.

* `protocol.py`: shared arm sets (`ARMS`, `SCENARIO_ARMS`, `ACTIVATION_ARMS`,
  `TIGHTENED_ARMS`) replace the literal string comparisons that were repeated
  across six modules, and `holdout_origin()` names the deployment origin of a
  held-out validation (first origin + 2P) and refuses a stream too short for it.
* The arm `HIST+ACT-T`: HIST+ACT's scenarios and activation, optimised inside
  the tightened band on both sides exactly as TIGHT tightens the nominal model,
  scored at the declared band. Its input and model hashes differ from HIST+ACT's
  and TIGHT's; the four upper-only arms' pinned hashes are unchanged.
* `runner.py`: the `holdout` quote stage - one explicit deployment origin per
  dataset, primary parameters, any approved seed subset, optional `--horizons`
  subset of the grid; the `horizons` config key exists only for this stage so
  every earlier manifest still rebuilds byte-identically.
* Analysis layer: a fifth categorical series for the new arm.
* Tests: `TightenedScenarioArmTests`, `HoldoutStageTests`, and native
  HIST+ACT-T solves on both solvers checked against enumeration; 234
  shared/CPLEX and 26 Hexaly tests pass.

## 7. Resource use, approvals, retries and deviations

### 7.1 Approvals obtained

On 10 September 2026 the user authorized: the engineering pilot exactly as quoted
(6,840 s configured native time over 8 solves, 3-hour overall wall cutoff, 32-GiB
process-tree RSS ceiling, 600 s per-attempt build allowance, sequential); stages
B–F at approximately **30 sequential solver-hours total**, screening-only scope
with no seed replication and no second origin; and permission to **propose** a
uniform per-solve cap reduction supported by pilot convergence evidence, subject
to separate approval before use.

On 12 September 2026 the user approved the three two-sided campaigns of
exploratory revision 2 exactly as quoted, launched sequentially: 44 unique
solves, 54,300 s configured native time (15.08 h), wall cutoffs 45,000 s /
27,000 s / 27,000 s, the same 32-GiB ceiling and 600 s build allowance. This
takes cumulative solver time to about 36 h, roughly 6 h beyond the original
~30 h; the user accepted that explicitly ("no problem on timing for now as long
as we put solid ground on this study"). No convergence-based cap reduction was
used.

On 13 September 2026 the user approved exploratory revision 3's held-out factorial
exactly as quoted: 12 solves, 21,600 s configured native (6.0 h), wall cutoff
38,000 s, taking cumulative solver time to about 42 h.

### 7.2 The invalidated first pilot — an operator error, disclosed

`campaigns/pilot_20260910/` ran under manifest `7878826c…` and returned 1
`COMPLETE` and 7 `PROCESS_ERROR` in 425.4 s. **Cause: the driver created
`analysis.py` and `rescoring.py` inside `Baselines/horizon_robustness/` while the
campaign was executing.** That changed the implementation hash, so every
subsequent worker recomputed a runtime differing from its frozen request and
refused to solve with `WORKER_INPUT_CHANGED`.

This was an operator error, not a runner defect: the provenance guard failed
closed instead of solving a model whose code identity had drifted from the
approved quote. The directory is **preserved unchanged** with a `SUPERSEDED.md`
explaining the cause, is excluded from every table and figure, and is listed as
excluded in `analysis_audit.md`. Its one completed case is **not** used in any
analysis, because no result should be drawn from a run whose implementation
identity was mutated mid-flight.

No retry was used to repair it. The whole campaign directory was superseded and
the work rerun in `campaigns/pilot_20260910b/`, which is the correct granularity:
repairing individual cases would have mixed two implementation identities inside
one campaign.

### 7.3 Resource accounting

Every solver second spent in this session, including reruns and diagnostics.

| Item | Native s | Charged to | Outcome |
|---|---:|---|---|
| Pilot attempt 1 (invalidated) | 6,840 charged cap; ≈120 s measured native; 425 s elapsed | Stage A | 1 COMPLETE, 7 PROCESS_ERROR; superseded, excluded from analysis |
| Pilot attempt 2 (`pilot_20260910b`) | 6,840 charged cap; 6,846 s measured native; 8,074 s elapsed | Stage A | 6 COMPLETE, 1 NO_INCUMBENT_LIMIT, 1 NUMERICAL_ISSUE |
| CPLEX 50-product diagnosis | 480 | Stage B–F | 4 solves; visits NO_INCUMBENT, min_slack bounded |
| BERNER numerical recheck | 1,800 | Stage B–F | formulation verified; exact validation passes |
| Predeclared min-slack diagnostics | 6,300 | Stage B–F | 6 solves; 4 ATTAINABLE, 2 UNRESOLVED |
| Stage B screening | 66,600 charged cap; 66,603 s measured native + 3,928 s model build; 77,243 s elapsed | Stage B–F | 153 solves; 312 COMPLETE, 48 NO_INCUMBENT_LIMIT |
| **Stage B–F total consumed** | **75,180 s (20.88 h)** | of ~30 h | ≈ 9.1 h unspent |
| Revision 2 launch attempt 1 (three superseded directories, §7.5) | 0 native s, 0 charged; about 30 min of wall time in quote rebuilds | separate 12 Sep approval | crashed before any solve; nothing spent |
| Revision 2 two-sided campaigns (`ts_d02`, `ts_b01`, `ts_b03`) | 54,300 charged cap (25,500 + 14,400 + 14,400); 54,441 s measured native + 9,297 s model build; 70,579 s elapsed (19.6 h) | separate 12 Sep approval | 44 solves; 82 COMPLETE, 2 NO_INCUMBENT_LIMIT; no retry, no cutoff |
| Revision 3 held-out factorial (`ho3_20260913`) | 21,600 charged cap; 21,678 s measured native + 5,035 s model build; 29,066 s elapsed (8.1 h) | separate 13 Sep approval | 12 solves; 12 COMPLETE; no retry, no cutoff |

Stage F (cross-horizon, 624 secondary evaluations) and both δ_min surveys consumed
**no solver time**. No retry was executed in any campaign, so nothing was spent
twice except the invalidated first pilot, which is reported rather than written
off.

With revisions 2 and 3 included, cumulative charged solver time for stages B–F
plus the two-sided campaigns and the held-out factorial is 151,080 s (41.97 h):
the original ~30 h plus the separate 12 and 13 September approvals, which
anticipated about 36 h and 42 h. Peak process-tree RSS on the industrial
models was 4.25 GB.

Stage A's two attempts are charged to the separately approved pilot allocation,
not to the ~30 h. The first attempt's 6,840 s is real time spent and is reported
rather than written off.

Peak process-tree RSS never approached the 32-GiB ceiling: 0.06 GB at 50
products, 0.85 GB at 2,000, and about 3.33 GiB on the full industrial model in
screening (2.93 GB in the pilot). Charged figures are configured caps; measured
native and elapsed times are kept distinct throughout.

### 7.4 Deviations from the original plan, and why

| Deviation | Reason | Authority |
|---|---|---|
| Analysis code outside the solver package | an analysis edit would otherwise invalidate every frozen manifest and block resume | driver; contract revision 1.3 |
| E2 output path corrected to `campaigns/` | the handoff named a directory the runner never used | driver; contract revision 1.3 |
| Exact integer-count rows in `visits` mode | float feasibility tolerance rejected a valid industrial layout | user instruction, 10 Sep 2026 |
| Min-slack caps 900/1200 s, above campaign caps | a diagnostic's value is the tightness of its interval; the 120 s probe left an interval two orders of magnitude wide | predeclared in §7.3c before running |
| Diagnostics stopped at 6,300 s of a 6 h reserve | lower bounds advanced too slowly to close, and industrial attainability was already established at zero cost | user asked for reassessment; recorded in §7.3d |
| No convergence probe, caps unchanged | offered and declined | user decision |
| No seed or origin replication | outside the authorized budget | user decision |

### 7.5 The two-sided launch attempt 1 — a path-length operator error, disclosed

The three revision-2 campaigns were first launched on 12 September 2026 into
directories named `twosided_screen_d02_20260912`, `twosided_berner_d01_20260912`
and `twosided_berner_d03_20260912`. Each supervised child rebuilt and verified
its quote, took the campaign lock, wrote the manifest and invocation records,
and then crashed while publishing its **first** solve request:

    FileNotFoundError: [Errno 2] ...\solves\<64-hex>\attempts\primary\request.json.partial-<32-hex>

That path is exactly 260 characters. The host (Windows Server 2019, long paths
not enabled) enforces the classic `MAX_PATH` limit of 259 usable characters and
reports the overflow as "not found". The completed campaigns used 15-character
directory names, which place the same file at 247 characters; the 28-character
names overflowed by one. The threshold was reproduced outside the campaign tree
the same day (259 characters opens, 260 fails with errno 2).

Consequences and handling:

* **No solver time was spent.** No worker process was spawned in any of the
  three runs. Each directory holds a complete `PROCESS_ERROR` terminal record
  listing every quoted case as `CAMPAIGN_ERROR`, and
  `verify_campaign.py --all --partial` accounts them fully.
* All three directories are preserved unchanged and carry a `SUPERSEDED.md`,
  so `make_analysis.py` excludes them and nothing is drawn from them.
* The identical manifests were relaunched under the same approval and the same
  implementation hash into 15-character directories (`ts_d02_20260912`,
  `ts_b01_20260912`, `ts_b03_20260912`). The solver package was **not** edited
  to add long-path support: that would have changed the implementation hash and
  invalidated the approved manifests for no scientific gain.
* Operational rule for future operators on this host: campaign directory names
  of at most 15 characters, and short `--retry-id` values.

## 8. Exact commands to re-run checks and regenerate analyses without optimizing

All commands are run from the repository root. **None of these launches a
solver**; the analysis path never imports an optimizer.

```powershell
# Software correctness, shared/CPLEX environment
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' -m unittest `
  tests.horizon_robustness.test_contracts tests.horizon_robustness.test_data `
  tests.horizon_robustness.test_reference tests.horizon_robustness.test_uncertainty `
  tests.horizon_robustness.test_uncertainty_lp tests.horizon_robustness.test_metrics `
  tests.horizon_robustness.test_industrial tests.horizon_robustness.test_horizon_nesting `
  tests.horizon_robustness.test_cplex tests.horizon_robustness.test_execution `
  tests.horizon_robustness.test_runner tests.horizon_robustness.test_runner_native `
  tests.horizon_robustness.test_analysis tests.horizon_robustness.test_rescoring

# Hexaly-specific correctness, Hexaly environment
& 'C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe' -m unittest `
  tests.horizon_robustness.test_hexaly

# E2 accounting, authorization and independent revalidation
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  tools/horizon_robustness/verify_campaign.py --all --authorization
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  tools/horizon_robustness/verify_campaign.py --revalidate

# Regenerate every table, figure and audit from immutable artifacts
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  tools/horizon_robustness/make_analysis.py

# Publication-anonymisation and protected-source checks
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  tools/horizon_robustness/check_anonymisation.py
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  tools/horizon_robustness/check_protected_sources.py

# Solver-free upper bounds on delta_min (reads data, imports no optimizer)
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  tools/horizon_robustness/slack_survey.py
```

`verify_campaign.py --revalidate` rebuilds each training problem from raw history
and re-runs the independent validator on the stored assignment, so it reads the
approved sources; it still launches no solver.

Add `--partial` to the accounting check while a campaign is unfinished. It
reports the exact number of authorized rows not yet executed and prints
`CAMPAIGN ACCOUNTING INCOMPLETE`, a string that deliberately does **not** contain
the E2:G1 expectation token, so an incomplete campaign can never satisfy that
gate. Every other assertion runs in both modes.

### 8.1 Resuming the screening campaign

```powershell
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  -m Baselines.horizon_robustness.runner run `
  reports/horizon_robustness_results/manifests/screen_20260910.json `
  --approved-manifest-hash 64178e37f4df73a897ecaa78aa88a21a2991adb889227dcb088cbb376d6cf76e `
  --output reports/horizon_robustness_results/campaigns/screen_20260910 `
  --solver-budget-seconds 66600 --wall-cutoff-seconds 100000
```

Four things the next operator must know:

1. **Resume is safe and does not repeat work.** Completed successes *and*
   failures are reused; only unreached rows are solved.
2. **There is a fixed ~22-minute start-up cost.** `run` re-executes the full
   quote over all 30 datasets to verify that sources, runtime and implementation
   still match the approved manifest. That happens on every invocation, including
   every resume, before the first solve. It is a deliberate provenance check, not
   a defect.
3. **At most one case will need a deliberate retry.** The solve in flight when the
   campaign stopped leaves an attempt directory with no native result; the runner
   records it `INTERRUPTED` and refuses to relaunch it silently. Redo exactly that
   case with `--retry-id <id> --retry-reason "<reason>"`. Do **not** use a retry to
   revisit a case whose result you dislike.
4. **The manifest is bound to implementation hash**
   `d437a20660533119d9e58e7d8ff16e900f5db97d004e6aacb88d106866d8a2af`. Any edit to
   a `*.py` file under `Baselines/horizon_robustness/` changes that hash, and every
   worker will then refuse to solve with `WORKER_INPUT_CHANGED`. **Do not edit the
   solve-path package while the campaign is running or between resumes** unless
   you intend to supersede the campaign and regenerate the manifest. This is not
   hypothetical; it destroyed the first pilot attempt.

### 8.2 Resuming the two-sided campaigns (exploratory revision 2)

The three revision-2 manifests are bound to implementation hash
`5e1ee22fe31372d86e4c549f747604b9d3b46524182a516efb7f247833b261f8`. They were
launched on 12 September 2026 as one sequential chain — screen δ = 0.02, then
BERNER δ = 0.01, then BERNER δ = 0.03 — with supervisor stdout/stderr under
`logs/`; after the first attempt failed on path length (§7.5) the chain was
relaunched into the 15-character directories below. Keep every campaign
directory name at most 15 characters on this host. Everything in §8.1 applies: resume is safe and repeats nothing, the
start-up quote rebuild is about 7 minutes for these subsets, at most one
`INTERRUPTED` case per stop needs a deliberate retry, and **no `*.py` under
`Baselines/horizon_robustness/` may be edited while any of the three is
unfinished**. If the chain stops, resume the unfinished campaigns in order:

```powershell
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  -m Baselines.horizon_robustness.runner run `
  reports/horizon_robustness_results/manifests/twosided_screen_d02_20260912.json `
  --approved-manifest-hash 4d0b6fbe8eaca292a46c675c86468dd8d37d3faabdcf78f9ce2f3a1e7752617b `
  --output reports/horizon_robustness_results/campaigns/ts_d02_20260912 `
  --solver-budget-seconds 25500 --wall-cutoff-seconds 45000

& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  -m Baselines.horizon_robustness.runner run `
  reports/horizon_robustness_results/manifests/twosided_berner_d01_20260912.json `
  --approved-manifest-hash 13e5bf8bc5d31a714c5e6ae8ef904b1e8f07724c3b24c55358c3da39aee0694a `
  --output reports/horizon_robustness_results/campaigns/ts_b01_20260912 `
  --solver-budget-seconds 14400 --wall-cutoff-seconds 27000

& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  -m Baselines.horizon_robustness.runner run `
  reports/horizon_robustness_results/manifests/twosided_berner_d03_20260912.json `
  --approved-manifest-hash 756a6ad746b42eda2d38b5026d0dcd67b34318a5f322b2e112abc8fd0444eeec `
  --output reports/horizon_robustness_results/campaigns/ts_b03_20260912 `
  --solver-budget-seconds 14400 --wall-cutoff-seconds 27000
```

The upper-only screening manifest stays bound to `d437a206…`. That campaign is
complete, so its hash now matters only to `verify_campaign.py --revalidate`,
which rebuilds every model with the current code and checks it against the
frozen certificates; revision 2 preserves the upper-only hashes precisely so that
this check keeps passing.

### 8.3 Resuming the revision-3 holdout campaign

Bound to implementation hash `4e359efde84f6c4a031409dfa814c0672c8428f08e3922860edaaee02fc13e5b`;
everything in 8.1 and 8.2 applies (no package edit while it runs, short retry ids).

```powershell
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  -m Baselines.horizon_robustness.runner run `
  reports/horizon_robustness_results/manifests/holdout_20260913.json `
  --approved-manifest-hash d4d4ed6c9772565a5caa1f03529f3e3e9cf50aa9b9463bf84ccbe6220b1a1bba `
  --output reports/horizon_robustness_results/campaigns/ho3_20260913 `
  --solver-budget-seconds 21600 --wall-cutoff-seconds 38000
```

## 9. Numerical and model validity checks, and known limitations

### 9.1 What is checked, and how

* **Independent validation.** Every accepted layout is revalidated from raw
  history against a freshly rebuilt training problem, in exact `Fraction`
  arithmetic, by code that shares nothing with the solvers. Visit counts and
  model residuals must reproduce bit-for-bit
  (`verify_campaign.py --revalidate`).
* **Exact future scoring.** Future feasibility compares integer line counts
  against the rational target plus the rational allowance, at zero tolerance. A
  floating-point tolerance never becomes operational slack.
* **Model rows.** Declared absolute residual tolerance 1e-8, unchanged. After the
  integer restatement the rows are integer-valued on both sides, so the exact
  residual is bounded away from the tolerance rather than sitting on it.
* **Provenance.** Each manifest pins source, catalogue, history, input, model,
  runtime and implementation hashes; a worker whose recomputed runtime differs
  from its frozen request refuses to solve. This is not theoretical — it fired,
  correctly, on the first pilot attempt (§7.2).
* **Layout freezing.** The complete layout certificate is durably written before
  the scorer is given any future segment, and the future segment is verified to be
  the exact next complete-order slice of the rebuilt source stream.
* **Anonymisation.** No internal site code may appear in a published table or
  figure; the checker verifies its own detector against a positive control.

### 9.2 Known limitations

1. **`NO_INCUMBENT` is not infeasibility, anywhere in this package.** No
   infeasibility certificate was obtained for any case. Where CPLEX also found
   nothing, that too is a limit, not a proof.
2. **δ_min intervals that straddle δ = 0.01 are UNRESOLVED**, with no directional
   reading. An earlier note in the execution log described one such interval as
   "leaning infeasible"; that phrasing is withdrawn and corrected in the log.
3. **Upper bounds cannot prove infeasibility.** The two zero-cost diagnostics
   (reference-layout slack, and cross-arm slack from returned layouts) bound
   δ_min from above only.
4. **Hexaly supplies no usable lower bound.** Its bound on the visits objective is
   0 and its gap is 1.0 throughout, so optimality is never established and
   "objective" always means "best incumbent at the cap".
4b. **Visit comparisons are between returned incumbents, not optima.** A true
   minimum cannot improve when constraints are tightened, yet several screening
   cells show a more-constrained arm with a lower training objective. This is the
   time-limited-incumbent artifact PLAN §7 anticipates, not a paradox and not a
   quantified noise floor. Achieved future-visit differences are still real; they
   are simply not statements about optimal objectives.
5. **`Z_H = ∅` on the synthetic instances tested**, so HIST+ACT is the *same
   model* as HIST there and H3 rests entirely on the industrial case.
6. **The synthetic generator is stationary.** Measured station-direction "novelty"
   on synthetic data is finite-sample variation, not demand drift. Those instances
   are a control on finite-sample and solver-cost effects, not evidence about
   robustness to real drift.
7. **Retrospective snapshot conditioning.** The industrial catalogue, incumbent,
   capacities, frozen mask and retention rule are reconstructed by the shared
   loader from the *whole* export and then assumed pre-known. Demand estimation is
   prefix-only conditional on that snapshot. This is not a demonstrated
   prospective reconstruction.
8. **Order-ID chronology is an assumption.** Sorting does not establish that
   creation, release, picking and delivery sequences agree.
9. **One origin and one seed** under the authorized budget, so no origin or seed
   replication exists and BERNER is descriptive with a single eligible origin.
10. **Paired differences are correlated.** Horizons at one origin share data;
    seeds measure algorithm variability, not additional futures; stations are not
    independent. No binomial confidence statement is attached to any of it.

## 10. Provisional observations and competing explanations

*Upper-only rule only. The two-sided results of exploratory revision 2 are in §12
and are never pooled with these.*

**Everything here is provisional and belongs to the joint review.** It is a
reading of the evidence with the alternatives that would defeat it. It is not a
verdict on the research direction, and nothing below declares the approach
successful, unsuccessful or publishable.

### 10.1 Headline, over all 90 authorized cells per arm

| Arm | Returned a layout | Passed joint compliance | Conditional compliance |
|---|---:|---:|---:|
| NOM | 90 / 90 | 7 | 8 % |
| TIGHT | 90 / 90 | 30 | 33 % |
| HIST | 66 / 90 | 34 | 52 % |
| HIST+ACT | 66 / 90 | 36 | 55 % |

**Both denominators must be read together.** The robust arms fail to return any
layout in 24 of 90 cells, all of them in the 50-product family. Counting those as
failures, the unconditional ordering is unchanged: 7 / 30 / 34 / 36.

Cross-horizon re-scoring of the same frozen layouts on the other declared
horizons (624 screening evaluations, plus 12 from the pilot) shows the same
ordering: NOM 7 %, TIGHT 33 %, HIST 45 %, HIST+ACT 48 %. It reuses layouts on
overlapping futures, so it is a transfer check, **not** independent replication
and not a new sample.

### 10.2 H1 — supported

Nominal optimization is the worst arm in every catalogue-size family. Paired
against NOM with the instance as the unit, every single stratum × horizon cell
shows a negative mean worst-excess difference for the robust arms, and the robust
arm is never worse on average anywhere.

### 10.3 H2 — mixed, and this is the most important result

Ordinary tightening is a strong competitor. Paired with **TIGHT as the baseline**,
the robust advantage collapses as the synthetic catalogue grows:

| Family | n | robust arm − TIGHT, worst excess | instances better / worse / equal |
|---|---|---:|---|
| 500 | 500 | −0.035 pp | 3 / 4 / 3 |
| 500 | 1000 | −0.008 pp | 3 / 3 / 4 |
| 1000 | 2000 | 0.000 pp | 0 / 0 / 4 |
| 2000 | 1000 | **+0.019 pp** (worse) | 0 / 1 / 2 |
| 2000 | 2000 | 0.000 pp | 0 / 0 / 3 |
| 2000 | 4000 | **+0.041 pp** (worse) | 0 / 1 / 2 |
| **BERNER**, HIST | 10937 / 21874 / 43748 | −0.808 / −0.823 / −0.513 pp | 1 / 0 / 0 each |
| **BERNER**, HIST+ACT | 10937 / 21874 / 43748 | **−1.239 / −1.040 / −0.867 pp** | 1 / 0 / 0 each |

On the 2000-product family TIGHT passes **9 of 9** where HIST passes 7 of 9. So on
stationary synthetic data, much of the apparent robustness gain **is** explained
by ordinary tightening — a genuine negative result for H2 on that data. On the
industrial case the advantage is large and consistent at all three horizons.

**A consistent, but not pre-registered, reading.** The solver-free δ_min survey
found that synthetic required slack sits at 1.7–3.1× a crude sampling-noise scale
while BERNER sits at 20.6–35.7× and *rises* with horizon. That is consistent with
persistent drift rather than noise, and with the reading that **tightening
suffices where the only variation is finite-sample noise, while the scenario hull
matters where there is real composition drift.** An earlier draft called this a
prediction confirmed by the campaign; the independent review checked the log
chronology and that framing is **withdrawn**: the survey completed before
screening launched, but its interpretation was written after launch, and the
noise statistic is not a calibrated drift test. It is corroborating description,
not a prediction, and it rests on one warehouse.

### 10.4 H3 — supported, and only where it could be

BERNER is the only case with a non-empty `Z_H`, so it is the only case where HIST
and HIST+ACT are different models at all. There:

| n | NOM | TIGHT | HIST | HIST+ACT | Incumbent |
|---|---|---|---|---|---|
| 10,937 | 6 viol | 2 viol | 2 viol | **0 viol (pass)** | 1 viol |
| 21,874 | 4 viol | 2 viol | 3 viol | 1 viol (+0.089 pp) | 1 viol |
| 43,748 | 6 viol | 2 viol | 4 viol | **0 viol (pass)** | 1 viol |

HIST+ACT passes 2 of 3; every other arm and the frozen incumbent pass 0 of 3. At
n = P/2 it reaches full compliance at **2.7836 future visits per order against the
incumbent's 3.1251**, and at 2P **2.9824 against 3.4248** — roughly 11–13 % fewer
visits *and* strictly better compliance than the incumbent on the real warehouse.
Realized activation mass rises with horizon (0.00249, 0.00366, 0.00676) and stays
under the declared ν = 0.01 at all three.

### 10.5 H4 — the model-side prediction holds

Robust arms become both easier to solve and easier to satisfy as n grows: at
n = 2P all 30 robust cells returned a layout, against 18 of 30 at n = P/2 and
n = P. Measured δ_min upper bounds fall monotonically with n. Both match the
proven nesting property U_large ⊆ U_small. The held-out compliance rate also
rises with n for every arm.

### 10.6 Competing explanations that must not be discarded

* **The returned layouts are not optima.** HIST is strictly more constrained
  than NOM, and TIGHT's cap is strictly inside NOM's, so at optimality both must
  have training objectives ≥ NOM. They do not — inversions up to 0.52 % were
  observed. That demonstrates suboptimality of particular incumbents; it is **not**
  a universal noise floor, and achieved future-visit differences are real
  differences between returned layouts. What it does mean: no visit-cost figure
  here is a statement about exact optimal objectives, and which layout an
  algorithm returns — hence its future compliance — can itself change with seed
  or computational effort.
* **The 50-product family is decided by non-returns, not by performance.** All 48
  `NO_INCUMBENT_LIMIT` results are there, and neither solver produced an
  infeasibility certificate anywhere. The min-slack diagnostic left that family's
  δ_min interval straddling δ = 0.01, i.e. UNRESOLVED.
* **One origin, one seed, one warehouse.** No seed or origin replication was in
  budget, so nothing here separates algorithm variability from deployment
  variability, and BERNER contributes a single eligible origin.
* **Snapshot conditioning.** The industrial incumbent, catalogue, capacities and
  frozen mask are reconstructed from the whole export and assumed pre-known.
* **Stationary synthetic data.** The benchmark contains no drift by construction,
  so its non-results are evidence about finite-sample behaviour, not about
  robustness to real drift.


## 11. Questions for the original assistant and the user

*The questions raised by the two-sided results are in §12.7; the held-out factorial of revision 3 is in §13.*

1. **Is δ = 0.01 the right primary tolerance for this uncertainty set?** The
   pilot suggests the historical-hull requirement scales with block sampling
   noise, so the same δ is easy at 21,874 products and possibly unattainable at
   50. A tolerance that is horizon- and scale-dependent by construction may be the
   wrong instrument — but changing it is a scientific decision, not mine.
2. **Should b be defined from the incumbent at all?** Because b is the
   incumbent's own historical share, the incumbent starts with the full δ of
   headroom while any optimizer spends it. That asymmetry, not the robustness
   model, may explain much of the observed violation pattern. Worth deciding
   before more compute is spent.
3. **Is the `Z_H = ∅` collapse acceptable for H3?** On synthetic data HIST+ACT is
   literally the same model as HIST, so H3 can only ever be tested on one
   industrial case with one eligible origin. Is that sufficient to report on H3 at
   all, or should H3 be declared untestable under this design?
4. **Does the integer restatement need independent review?** I claim it is exactly
   equivalent and I have enumerated small fixtures to check it, but it is the one
   change in this package that touches how the optimization model is written. A
   second reader should confirm the floor argument and the ν = 1 and clipped-cap
   boundary cases.
5. **How should a partially executed screening be reported?** Instances are
   reached in manifest order, which is outcome-independent, but a partial campaign
   still has a non-random instance mix by catalogue size. My reporting treats it as
   partial and refuses to generalize; confirm that is what you want.
6. **Is the incumbent's own BERNER violation a data-quality signal?** The frozen
   industrial incumbent breaches one station by +0.3361 pp on the future window.
   That may be genuine drift, or an artifact of the assumed-pre-known snapshot
   reconstruction. It bears directly on how much weight the industrial case can
   carry.

## 12. Exploratory revision 2 — two-sided results (provisional, reported separately)

Everything in this section was produced under the two-sided rule (`rule = two_sided`,
implementation hash `5e1ee22f…`) and is **never pooled** with the upper-only study of
§10. The design, the choice of δ = 0.02 as primary, the subset and the reporting rules
were predeclared in `CAMPAIGN_PREDECLARATION.md` §8 before any two-sided solve; no
headline below was chosen after seeing a future. One seed, one origin, three horizons
that share that origin, TIGHT at λ = 0.5, ν = 0.01. Cells are joint two-sided compliance
on the real next-*n* orders: every station's realized share inside
`[max(0, b_s − δ), min(1, b_s + δ)]`. A miss lists cap/floor breach counts, the worst
breach in percentage points, and mean future station visits per order; the incumbent
layout is scored two-sided on the same future as context, not as the comparator.

### 12.1 Accounting

| Campaign | δ | Rows | Unique solves | Charged native s | Measured native s | Build s | Elapsed s | Outcomes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `ts_b01_20260912` | 0.01 | 12 | 8 | 14,400 | 14,448 | 2,969 | 19,338 | 12 `COMPLETE` |
| `ts_d02_20260912` | 0.02 | 60 | 28 | 25,500 | 25,545 | 3,341 | 31,879 | 58 `COMPLETE`, 2 `NO_INCUMBENT_LIMIT` |
| `ts_b03_20260912` | 0.03 | 12 | 8 | 14,400 | 14,447 | 2,988 | 19,361 | 12 `COMPLETE` |
| **Total** | | **84** | **44** | **54,300** | **54,441** | **9,297** | **70,579** | |

Every row is accounted, every layout independently revalidated against a rebuilt
two-sided model, every charged second equals its quote, no retry was used and no
wall cutoff fired (§8.2, ledger). The two `NO_INCUMBENT_LIMIT` cells are the shared
HIST/HIST+ACT solve of the 50-product warehouse at n = P/2: no allocation inside the
120 s cap, which is **not** infeasibility.

### 12.2 BERNER, the three δ values side by side

Each cell: pass/miss · cap breaches/floor breaches · worst breach (pp, three decimals so a miss of a few thousandths is visible) · mean visits per order.

| Horizon n | Arm | δ = 0.01 (aspiration) | **δ = 0.02 (primary)** | δ = 0.03 (fallback) |
|---|---|---|---|---|
| 10,937 | NOM | miss · 4/6 · 0.313 pp · 2.71 | miss · 5/6 · 0.381 pp · 2.70 | miss · 3/3 · 2.612 pp · 2.62 |
| 10,937 | TIGHT | **pass** · 0/0 · 0.000 pp · 2.67 | **pass** · 0/0 · 0.000 pp · 2.70 | **pass** · 0/0 · 0.000 pp · 2.70 |
| 10,937 | HIST | miss · 2/4 · 0.188 pp · 2.76 | miss · 1/2 · 0.409 pp · 2.71 | miss · 3/1 · 0.286 pp · 2.66 |
| 10,937 | HIST+ACT | miss · 0/1 · 0.004 pp · 2.74 | miss · 0/1 · 0.019 pp · 2.68 | miss · 1/0 · 0.063 pp · 2.71 |
| 10,937 | *incumbent (context)* | miss · 1 breach(es) · 0.350 pp · 3.13 | **pass** · 0 breach(es) · 0.000 pp · 3.13 | **pass** · 0 breach(es) · 0.000 pp · 3.13 |
| 21,874 | NOM | miss · 3/4 · 0.449 pp · 2.85 | miss · 4/7 · 0.389 pp · 2.83 | miss · 1/2 · 2.486 pp · 2.73 |
| 21,874 | TIGHT | miss · 1/0 · 0.082 pp · 2.81 | **pass** · 0/0 · 0.000 pp · 2.84 | **pass** · 0/0 · 0.000 pp · 2.83 |
| 21,874 | HIST | miss · 3/4 · 0.376 pp · 2.86 | miss · 0/3 · 0.072 pp · 2.79 | miss · 1/1 · 0.025 pp · 2.76 |
| 21,874 | HIST+ACT | miss · 0/2 · 0.270 pp · 2.87 | miss · 0/2 · 0.252 pp · 2.84 | miss · 0/1 · 0.043 pp · 2.75 |
| 21,874 | *incumbent (context)* | miss · 1 breach(es) · 0.336 pp · 3.29 | **pass** · 0 breach(es) · 0.000 pp · 3.29 | **pass** · 0 breach(es) · 0.000 pp · 3.29 |
| 43,748 | NOM | miss · 2/4 · 0.464 pp · 2.94 | miss · 4/5 · 0.451 pp · 2.93 | miss · 1/2 · 1.767 pp · 2.84 |
| 43,748 | TIGHT | miss · 1/0 · 0.230 pp · 2.90 | **pass** · 0/0 · 0.000 pp · 2.94 | **pass** · 0/0 · 0.000 pp · 2.92 |
| 43,748 | HIST | miss · 4/7 · 0.398 pp · 2.94 | miss · 0/3 · 0.167 pp · 2.92 | miss · 1/0 · 0.059 pp · 2.84 |
| 43,748 | HIST+ACT | miss · 1/0 · 0.013 pp · 2.97 | **pass** · 0/0 · 0.000 pp · 2.90 | miss · 0/1 · 0.019 pp · 2.86 |
| 43,748 | *incumbent (context)* | miss · 1 breach(es) · 0.138 pp · 3.42 | **pass** · 0 breach(es) · 0.000 pp · 3.42 | **pass** · 0 breach(es) · 0.000 pp · 3.42 |

| Arm | Passes at δ = 0.01 | at 0.02 | at 0.03 | Mean visits/order, 3 horizons, at 0.01 / 0.02 / 0.03 |
|---|---:|---:|---:|---|
| NOM | 0/3 | 0/3 | 0/3 | 2.834 / 2.819 / 2.731 |
| TIGHT | 1/3 | 3/3 | 3/3 | 2.794 / 2.825 / 2.816 |
| HIST | 0/3 | 0/3 | 0/3 | 2.852 / 2.803 / 2.753 |
| HIST+ACT | 0/3 | 1/3 | 0/3 | 2.862 / 2.804 / 2.771 |
| incumbent | 0/3 | 3/3 | 3/3 | 3.279 / 3.279 / 3.279 |

### 12.3 The δ = 0.02 screen on the four synthetic warehouses

| Warehouse | n | NOM | TIGHT | HIST | HIST+ACT | incumbent |
|---|---:|---|---|---|---|---|
| 50-product | 25 | miss 2.42 pp · 3.88 | **pass** · 3.96 | `NO_INCUMBENT_LIMIT` | `NO_INCUMBENT_LIMIT` | miss 2.25 pp · 4.52 |
| 50-product | 50 | miss 1.62 pp · 3.62 | miss 2.04 pp · 3.78 | miss 0.02 pp · 4.36 | miss 0.02 pp · 4.36 | miss 0.02 pp · 4.34 |
| 50-product | 100 | miss 0.25 pp · 3.65 | miss 2.69 pp · 3.72 | miss 0.84 pp · 3.86 | miss 0.84 pp · 3.86 | **pass** · 4.40 |
| 500-product | 250 | miss 0.11 pp · 3.62 | **pass** · 3.67 | **pass** · 3.69 | **pass** · 3.69 | **pass** · 4.41 |
| 500-product | 500 | **pass** · 3.61 | **pass** · 3.63 | **pass** · 3.67 | **pass** · 3.67 | **pass** · 4.39 |
| 500-product | 1,000 | **pass** · 3.64 | **pass** · 3.63 | **pass** · 3.66 | **pass** · 3.66 | **pass** · 4.41 |
| 1000-product | 500 | **pass** · 5.09 | **pass** · 5.14 | **pass** · 5.15 | **pass** · 5.15 | **pass** · 6.32 |
| 1000-product | 1,000 | miss 0.31 pp · 5.06 | **pass** · 5.09 | **pass** · 5.14 | **pass** · 5.14 | **pass** · 6.29 |
| 1000-product | 2,000 | miss 0.04 pp · 5.12 | **pass** · 5.15 | **pass** · 5.17 | **pass** · 5.17 | **pass** · 6.35 |
| 2000-product | 1,000 | **pass** · 6.09 | **pass** · 6.01 | **pass** · 6.02 | **pass** · 6.02 | **pass** · 7.77 |
| 2000-product | 2,000 | **pass** · 6.16 | **pass** · 6.14 | **pass** · 6.18 | **pass** · 6.18 | **pass** · 7.84 |
| 2000-product | 4,000 | **pass** · 6.24 | **pass** · 6.24 | **pass** · 6.25 | **pass** · 6.25 | **pass** · 7.92 |

Synthetic passes over the 12 cells (scored cells in the denominator): NOM 6/12, TIGHT 10/12, HIST 9/11, HIST+ACT 9/11.

### 12.4 Cross-horizon transfer (no new optimisation)

Each frozen two-sided layout re-scored on the other two horizons of its own δ,
still two-sided at that δ. BERNER only; six secondary evaluations per arm and δ.

| Arm | δ = 0.01 | δ = 0.02 | δ = 0.03 |
|---|---:|---:|---:|
| NOM | 0/6 | 0/6 | 0/6 |
| TIGHT | 2/6 | 6/6 | 6/6 |
| HIST | 0/6 | 1/6 | 2/6 |
| HIST+ACT | 1/6 | 1/6 | 4/6 |

Synthetic transfer at δ = 0.02: NOM 12/24, TIGHT 20/24, HIST 19/22, HIST+ACT 19/22.

### 12.5 Provisional observations

1. **At the predeclared primary δ = 0.02, TIGHT passes 3/3 BERNER horizons and no other optimised arm does better than 1/3** (HIST+ACT), with HIST 0/3 and NOM 0/3. The incumbent passes ±2 at 3/3 horizons.
2. **The ±1 aspiration is not met by any arm except TIGHT at n = P/2** (1/3), and the incumbent itself fails ±1 at 3/3 horizons, as the dispersion survey said it would (`PILOT_FINDINGS.md` §7: the incumbent's station shares in single historical blocks deviate from their pooled shares by more than one point). Historical failure of the incumbent motivates the grid; it neither predicts future failure nor bounds what another layout could achieve.
3. **Widening the band to ±3 did not produce compliance for the robust arms.** Their δ = 0.03 layouts miss by 0.02–0.06 pp (HIST+ACT) and 0.02–0.29 pp (HIST), NOM by 1.77–2.61 pp, while TIGHT passes 3/3. Each δ is a different model and a different solve, so the visit-minimising optimiser uses whatever room the band gives it and sits on a band edge on the historical scenarios; the next window's drift then carries at least one station over. TIGHT is the only arm that explicitly reserves the uniform pooled-history half-band ±δ(1−λ) and is then scored at ±δ; HIST and HIST+ACT can create directional headroom of their own, but nothing forces them to. **These cells are consistent with a margin mechanism, not a causal isolation of it from solver and layout effects**: the reward appears to go to the gap between the optimisation band and the scoring band rather than to the width of the band, which is the two-sided face of the upper-only H2 observation in §10.3 (visit minimisation drains stations). Isolating it needs the scenario arms run with the same reserved margin, which is what the held-out factorial of revision 3 is for.
4. **TIGHT's margin has a small, measurable visit cost on BERNER.** Mean visits per order over the three horizons are 2.825 for TIGHT against 2.803 for HIST at δ = 0.02 (+0.8%) and 2.816 against 2.753 at δ = 0.03 (+2.3%), while the incumbent sits at 3.279: every optimised arm saves about 14% of visits relative to the incumbent, and TIGHT gives back a small part of that for its margin. Visit-cost figures compare returned layouts, not optima (§9.2).
5. **The misses of HIST and HIST+ACT are small but they are misses of the declared policy.** At δ = 0.02 their breaches are mostly floors (11 floor against 1 cap breaches over the six cells; HIST at n = P/2 also breaches a cap) of at most 0.409 pp, which is about 20% beyond the two-point allowance; at δ = 0.03 at most 0.286 pp. A pass/miss count hides the magnitudes; the breach magnitudes in §12.2 are the primary reading, and their practical importance is not settled by calling them small.
6. **Transfer across horizons follows the same-horizon picture, with one nuance** (§12.4): a TIGHT layout trained at one BERNER horizon passes the other two at δ = 0.02 (6/6) and δ = 0.03 (6/6); NOM transfers nowhere; HIST+ACT's δ = 0.03 layouts, which miss their own horizon by hundredths of a point, pass 4/6 of the other horizons, a reminder that those misses sit on the edge rather than far outside the band.
7. **Synthetic warehouses behave differently from BERNER**, as in the upper-only study: at δ = 0.02 the 500- and 2000-product warehouses are passed by every arm at nearly every horizon, the 1000-product warehouse by everything but NOM, and the 50-product warehouse — whose own history needs more than ±5 — is failed by almost everything and returns no HIST/HIST+ACT layout at n = P/2.

### 12.6 Competing explanations and limits that must travel with §12.5

* **One seed, one origin.** Every BERNER δ column rests on three cells that share one origin; they are three horizons of one history, not three replicates. Seed and origin replication was outside the authorisation and remains undone.
* **Breach magnitudes of a few hundredths of a point are decided by single stations.** Whether a 0.02 pp floor breach is a property of the arm or of that station on that window cannot be told from one cell; nothing here uses a noise-floor argument to dismiss or promote it.
* **BERNER's drift signature** (`PILOT_FINDINGS.md` §7 and §10.6 above) means a layout tuned to the historical scenario set faces a future that moves more than its history did; the two-sided rule does not change that, and the incumbent's ±2 pass says only that the warehouse's own layout drifted less than the optimised ones drained.
* **The λ frontier was not run** (user decision, 12 September): TIGHT's advantage is shown at λ = 0.5 only, and choosing a λ against these same futures would be tuning against the validation window, which the protocol forbids.
* **No certified lower bound**: nothing here shows ±1 or ±2 unattainable for any arm.
* **Exploratory, not untouched confirmation.** The two-sided policy was fixed before its solves, but after the same future demand had been examined through the upper-only layouts and their two-sided re-scoring. Prefix-only fitting is verified; independent confirmatory evaluation of the chosen policy is not, which is why revision 3 targets the unexamined tail of the stream.
* **The future leaves the modelled set downward in every two-sided BERNER cell** (`tables/two_sided_novelty_survey.csv`, re-scored under the repaired scorer, every stored field reproduced). HIST+ACT's scenario set covers the future from above in 6 of 9 cells (no station above its worst scenario) but not from below: 2–7 stations sit under its lowest modelled share, by up to 0.54 pp. NOM and TIGHT, whose modelled set is the single pooled-history point, have all 24 stations outside it in every cell, TIGHT's shortfall reaching 0.94 pp, and TIGHT passes ±2 regardless: its compliance comes from the reserved margin, not from set membership.
* **The total-variation reading of TIGHT is valid but vacuous here.** A station share can move at most by the total-variation distance between the future product mix and pooled history, so a layout inside ±(δ−ρ) on pooled history stays inside ±δ on any future within ρ. On BERNER the historical blocks sit 0.25 / 0.19 / 0.14 from pooled history in total variation at n = P/2 / P / 2P, and the scored futures (ex post) 0.27 / 0.21 / 0.17, against a reserved margin ρ = λδ = 0.01: fifteen to twenty-seven times larger. Compliance therefore rests on cancellation across the thousands of products inside a station, which the station-level dispersion survey measures (about 1.7 points at most), not on the product-level bound (`tables/drift_survey.csv`). Any date-free margin rule has to be predeclared from station-level dispersion.
* **Departures from the modelled set in the downward direction were not counted by the stored evaluations** (their `station_novelty_count` measured the upper direction only); `tables/two_sided_novelty_survey.csv` re-scores the two-sided BERNER cases under the repaired code and reports both directions.
* **NOM's layouts differ across δ** (different model per δ), so its worst breach rising from 0.45 pp at δ = 0.02 to 2.61 pp at δ = 0.03 is a property of the wider model, not of a fixed layout scored more leniently.

### 12.7 What this section does not claim

No verdict on the research direction, no manuscript, no recommendation of TIGHT as *the* method: these are 36 BERNER cells and 48 synthetic cells (84 in all) under one seed and one origin, reported as predeclared. The upper-only study of §10 stands unchanged and unpooled. Questions this raises for the original assistant and the user: whether the margin mechanism in §12.5(3) should be tested by a predeclared λ frontier on a *held-out* origin; whether ±2 with a tightened optimisation band is the business rule worth carrying forward; and whether seed/origin replication of the BERNER cells is worth its solver time.

## 13. Exploratory revision 3 — the held-out factorial (provisional, reported separately)

Design and endpoints predeclared in `CAMPAIGN_PREDECLARATION.md` §9 before the quote; campaign `ho3_20260913`, manifest `d4d4ed6c9772…`, implementation `4e359efde84f…`. One deployment origin at order 243,151 (the tail no analysis of this study had read), the focal horizon n = 21,874 (future [243,151, 265,025)), the two-sided rule at δ = 0.02, ν = 0.01, λ = 0.5, seeds 11, 22, 33. Never pooled with §10 or §12.

### 13.1 Accounting

| Rows | Unique solves | Charged native s | Measured native s | Build s | Elapsed s | Outcomes |
|---:|---:|---:|---:|---:|---:|---|
| 12 | 12 | 21,600 | 21,678 | 5,035 | 29,066 | 12 `COMPLETE` |

### 13.2 Every cell

Each cell: pass/miss · cap breaches/floor breaches · worst breach (pp) · mean visits per order · stations outside the modelled set above/below.

| Arm (scenarios, margin) | seed 11 | seed 22 | seed 33 | incumbent, same future |
|---|---|---|---|---|
| NOM (0, 0) | miss · 4/5 · 1.006 pp · 3.266 · 11/13 | miss · 4/4 · 0.939 pp · 3.256 · 11/13 | miss · 2/4 · 1.144 pp · 3.172 · 11/13 | **pass** · 0 breach(es) · 0.000 pp · 3.847 |
| TIGHT (0, 1) | **pass** · 0/0 · 0.000 pp · 3.266 · 12/12 | **pass** · 0/0 · 0.000 pp · 3.267 · 11/13 | **pass** · 0/0 · 0.000 pp · 3.276 · 11/13 | **pass** · 0 breach(es) · 0.000 pp · 3.847 |
| HIST+ACT (1, 0) | miss · 1/1 · 0.081 pp · 3.278 · 1/3 | miss · 2/2 · 0.179 pp · 3.239 · 3/4 | miss · 0/2 · 0.069 pp · 3.274 · 0/4 | **pass** · 0 breach(es) · 0.000 pp · 3.847 |
| HIST+ACT-T (1, 1) | **pass** · 0/0 · 0.000 pp · 3.351 · 0/2 | **pass** · 0/0 · 0.000 pp · 3.386 · 1/4 | **pass** · 0/0 · 0.000 pp · 3.304 · 0/4 | **pass** · 0 breach(es) · 0.000 pp · 3.847 |

### 13.3 The predeclared endpoints, read literally

* **Replication endpoint (primary):** TIGHT passes ±2 at n = P on the held-out future for 3 of 3 seeds. Predeclared threshold: at least two of three. **REPLICATED.**
* **Factorial reading (secondary, descriptive), seed-wise:**

| Arm | scenarios | margin | passes | worst breach (pp), max over seeds | largest station deviation from target (pp), max over seeds | mean visits/order | vs incumbent | stations below modelled minimum, mean |
|---|---|---|---:|---:|---:|---:|---:|---:|
| NOM | 0 | 0 | 0/3 | 1.144 | 3.144 | 3.232 | −16.0% | 13.0 |
| TIGHT | 0 | 1 | 3/3 | 0.000 | 1.756 | 3.270 | −15.0% | 12.7 |
| HIST+ACT | 1 | 0 | 0/3 | 0.179 | 2.179 | 3.264 | −15.2% | 3.7 |
| HIST+ACT-T | 1 | 1 | 3/3 | 0.000 | 1.160 | 3.347 | −13.0% | 3.3 |

  Margin main effect (passes with the margin on against off): 6 against 0 of 6 each. Scenario main effect (scenarios on against off): 3 against 3. These are counts over three optimiser seeds at one origin; they describe this deployment and generalise to nothing. Pass counts are not the whole reading: the scenarios and activation, bundled in this factorial, shrink the largest station deviation from 3.14 to 2.18 pp without the margin and from 1.76 to 1.16 pp with it (the incumbent's own largest deviation on this future is 1.16 pp), while HIST+ACT-T costs 2.4% more visits than TIGHT. So the margin decides the pass; the scenarios buy fidelity to the historical shares at a visit cost: a cost-protection trade-off, not evidence that scenario protection is useless. Their separate contributions (scenarios against activation) are not isolated here.

* **The held-out window was not an easy one.** Measured only after the campaign had scored it, its product mix sits 0.195 from the pooled history it was scored against in total variation, against a historical block maximum of 0.194 and mean 0.171 over 11 blocks (`tables/drift_survey.csv`, row `BERNER@holdout`): drift at the top of the historical range, not below it.

### 13.4 What this section does not claim

No verdict on the research direction and no manuscript. One origin, one horizon, three seeds: seeds measure optimiser variability, not demand variability, so nothing here speaks about other deployments or warehouses. The tail was unexamined *in this study*; the submitted article's temporal hold-out came from a different dated extract. No λ or δ was chosen from this future, and none will be.

