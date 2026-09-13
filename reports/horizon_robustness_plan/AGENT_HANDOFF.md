# Execution contract: horizon robust CSLAP

Contract revision: 1.0, 2026-09-08. Scientific authority: [PLAN.md](PLAN.md).

Status: execution not started. This is a task breakdown for an agent after joint approval, not evidence that any implementation or experiment exists. If this document and PLAN.md disagree, stop at that conflict and reconcile the contract rather than guessing.

## 1. Scope and working discipline

Deliver a reproducible implementation and an evidence-qualified study of the approved closed-catalogue, order-horizon model. The only empirical sources are the two entries in PLAN Section 3.1. No changes to the submitted article, existing studies, original datasets, solver environments, or unrelated user files are implied.

Use the project `.claude/skills/unlazy` discipline: contracts before work, dependency-based leaves, observable gates, four-pass review, and bottom-up re-verification. The user confirmed Node is not installed and explicitly allowed disregarding that tooling. **Do not install Node, block the study on it, or claim its scripts passed.** Use manual status ledgers plus direct, approved Python test commands; no replacement gate-runner framework is required. A separate Node/Python workflow tool is outside the scientific deliverable.

For execution, create a scoped ledger under `.unlazy/horizon-cslap/` with a copied, revisioned contract, a root `GATES.md`, and individual `gates/leaf-<ID>.md` and branch `gates/node-<ID>.md` files. Leave the existing root ledger untouched. These are ordinary documents and do not require a Node runtime. Keep an append-only status log. Do not install hooks or treat a checked box as evidence of an executed test.

Default to sequential work with explicit ownership and dependencies. Native parallel agents may be used later only with disjoint paths, available coordination, and the skill's parallel/dispatch instructions read at that time. Do not launch overlapping writers or shell-based agent farms. Measured solver runs remain sequential to avoid resource contention.

Every leaf receives four passes: complete its deliverable; reread as a domain expert; hunt correctness/integration/performance defects; polish and repeat until a clean pass. The driver then independently reruns approved tests, reviews manual evidence, and challenges at least one passed gate with a failing control. No inherited CHECK line is executed without inspecting its command and called code, and obtaining the required approval. State/status inspection is not test execution.

Leaf states are WAITING, READY, IN-FLIGHT, VERIFIED and ABANDONED. Branches are OPEN, VERIFIED or ABANDONED. A missing user decision or abandoned outcome is a visible handoff, never successful completion. Before execution approval, all implementation leaves are unstarted; the table below specifies their future dependencies rather than falsely assigning current READY/VERIFIED status.

## 2. Ownership and dependency tree

```text
ROOT: closed-catalogue horizon study
  C0: shared contracts and protocol configuration
  DATA branch
    D1: catalogue, order cleaning and chronology
    D2: historical reference and fixed-product mask
  MODEL branch
    M1: scenarios, activation envelope and slack diagnostic
    M2: independent evaluation and solution certification
  SOLVERS branch
    S1: CPLEX reference backend
    S2: Hexaly set backend
  EXPERIMENT branch
    E1: reproducible runner and campaign quotation
    E2: approved pilot and experiment execution
  REPORT branch
    R1: paired analysis and figures
    R2: separate research report and claim audit
```

All paths below are repository-relative, proposed new files. Test fixtures are owned by the corresponding test leaf, not shared mutable assets. The driver owns only orchestration documents; changing a shared interface belongs to C0 and invalidates dependent verification until rerun.

| Leaf | Needs verified | Exclusive implementation ownership | Main acceptance outcomes |
|---|---|---|---|
| C0 | protocol approval | `Baselines/horizon_robustness/__init__.py`, `schema.py`, `protocol.py` in that package; `tests/horizon_robustness/__init__.py`, `test_contracts.py`; `configs/horizon_robustness/**` | Schema rejects forbidden inputs; fixed protocol is serializable and hashable; units/statuses are explicit. |
| D1 | C0 | `Baselines/horizon_robustness/catalogue.py`, `orders.py`; `tests/horizon_robustness/test_data.py` | Full roster survives zero demand; numerical order grouping and source-specific counting are correct; provenance is explicit. |
| D2 | C0, D1 | `Baselines/horizon_robustness/reference.py`; `tests/horizon_robustness/test_reference.py` | Complete reference layout, fixed mask and pooled shares depend on no future demand; industrial reconciliation is accepted or explicitly blocked. |
| M1 | C0, D1, D2 | `Baselines/horizon_robustness/uncertainty.py`; `tests/horizon_robustness/test_uncertainty.py` | Matched-horizon scenarios, inactive activation and robust counterpart are correct; scalar slack diagnostic is specified. |
| M2 | C0, D1, D2 | `Baselines/horizon_robustness/metrics.py`, `validation.py`; `tests/horizon_robustness/test_metrics.py` | Independent full-product/full-station visit and workload scoring rejects deliberately bad layouts and measures raw residuals. |
| S1 | C0, D2, M1, M2 | `Baselines/horizon_robustness/cplex_backend.py`; `tests/horizon_robustness/test_cplex.py` | Reference MILP and independent uncertainty LP agree with hand-worked cases; statuses and bounds are honest. |
| S2 | C0, D2, M1, M2 | `Baselines/horizon_robustness/hexaly_backend.py`; `tests/horizon_robustness/test_hexaly.py` | Whole-catalogue set partition agrees with reference case objectives/constraints within declared tolerances; no silent support truncation. |
| E1 | D1, D2, M1, M2, S1, S2 | `Baselines/horizon_robustness/runner.py`; `tests/horizon_robustness/test_runner.py` | Allowlisted manifest, immutable train/score boundary, process isolation, resumability and budget quotation work. |
| E2 | E1, branch integration, experiment approval | `results/horizon_robustness/**` | Only approved runs execute; every expected run has a result or explicit failure record; complete assignments/logs are retained. |
| R1 | E2 | `Baselines/horizon_robustness/analysis.py`; `tests/horizon_robustness/test_analysis.py`; `reports/horizon_robustness_results/figures/**`, `tables/**`, `analysis_audit.md` | Paired metrics reproduce from raw outputs; denominators and missing cases are correct; no pseudoreplication. |
| R2 | R1 and all branch gates | `reports/horizon_robustness_results/STUDY_REPORT.md`, `robustness_study.tex`, `references.bib` | Claims trace to proofs or approved evidence; negative findings and the calendar fallback remain visible. |

For clarity, bare filenames in a table cell share the immediately preceding package/directory prefix. Expand them into explicit full relative paths when authoring the execution ledgers. Shared configuration is owned by C0, not rewritten by runner or solver leaves. A new parameter or scope change increments the contract revision before dispatch.

## 3. Stable interface contracts

### IC1: CatalogueManifest

Fields: schema/protocol revision; dataset ID; source allowlist and SHA-256 hashes; full product IDs in stable order; full station IDs; slot IDs/capacities; explicit allowed product-station pairs if any; exogenous fixed assignments; geometry/roster provenance (`verified_exogenous`, `assumed_exogenous`, or `missing`); exact cleaning policy; counts and exclusion log.

Invariants: unique IDs; every slot belongs to one station; total slots equals catalogue size; no zero-demand product disappears; all reference/future IDs resolve in this manifest. A present-day exported roster is allowed only as the explicitly declared closed-catalogue assumption. Provenance does not authorize future demand leakage.

### IC2: OrderedDemand

Fields: original order ID; parsed chronology key; distinct product support; product-line multiplicities; optional raw historical station observations kept outside the optimization workload arrays. Catalogue-aligned sparse counts include conceptual zeros, with stable dense product indexing when required by a backend.

Synthetic workloads count original line multiplicities. BERNER workloads count retained distinct product-order pairs. Visits use distinct supports in both. Sorting and complete-order boundaries are deterministic. No dates, quantities, full-horizon popularity or future station labels are model features.

### IC3: TrainingProblem

Fields: manifest hash; origin t and history hash; n and scenario block boundaries; complete x_ref and slot map; fixed mask; b vector; delta and clipped u; q^H; all weighted historical supports; full-catalogue scenario matrix; Z_H; nominal nu and effective nu; model arm; solver-independent fixed constraints; numerical policy.

The frozen object contains no future orders, future counts, future station mappings or future metrics. All methods at an origin share the same b and reference metadata. NOM/TIGHT cache keys omit n because their mathematical models do not use it; scoring records still identify n. Every key includes all parameters that actually change the optimization problem.

### IC4: SolveResult

Fields: run ID; input hash; backend and installed version; representation; seed and thread configuration; native termination code/text; normalized status; complete assignment and deterministic slot map if present; objective; bound and gap with provenance if available; model build/solve times; memory observations; stdout/stderr locations; independent validation reference.

Normalized statuses: `OPTIMAL_WITHIN_TOLERANCE`, `FEASIBLE`, `PROVEN_INFEASIBLE`, `NO_INCUMBENT_LIMIT`, `RESOURCE_LIMIT`, `NUMERICAL_ISSUE`, `SOLVER_ERROR`, `DATA_CONTRACT_ERROR`. Data eligibility records additionally use `INSUFFICIENT_HISTORY`, `INSUFFICIENT_FUTURE`, and `OUT_OF_CATALOGUE`. Do not collapse them into one missing value. No numeric bound is invented when a solver does not provide one; use a documented null, not infinity as a surrogate certificate.

Validation is separate from native status. An assignment returned at a time limit can be independently feasible; a solver-labelled feasible assignment with a contract violation is rejected. Objective optimality is distinct from robust constraint feasibility.

### IC5: EvaluationResult

Fields: frozen layout hash; origin and horizon; future segment boundaries and hash; complete station shares; target/cap vector; exact line totals; observed visits; raw cap residuals; joint pass indicator; numerical-borderline flags; activation mass; robust worst-share envelope; solver/return status; paired method/reference run IDs.

The evaluator can see future orders only after the allocation is frozen. It cannot call optimization, repair a layout, reset b, enlarge delta or nu, or silently change the product universe. Each result records whether it is primary same-horizon scoring or secondary cross-horizon scoring.

### IC6: Numerical and audit policy

Use integer line counts and exact support weights throughout ingestion. Represent configured decimal tolerances reproducibly. For future feasibility, compare integer counts against the rational historical target plus the rational decimal allowance where practical, so a floating-point tolerance does not become hidden operational slack. Record raw floating-point residuals as well.

For solver-model scenario validation, declare an absolute share residual tolerance of 1e-8 initially and record maximum residuals; compare with exact/rational recomputation on reference cases. If installed solver precision cannot satisfy this, discuss and revision the numerical policy before the campaign rather than silently increasing it. Storage, catalogue membership, fixed assignments and whole-order counts are exact, not tolerance-based. Near-boundary future cases should be identified, not hidden in rounded percentage displays.

Use portable JSON/CSV or other explicitly versioned, documented interchange that both installed Python environments can read; no unsafe pickle interchange. Keep sparse matrices sparse for large inputs. Write run-specific files atomically and never overwrite previous run IDs. No customer raw rows in web requests, public reports, or external logging.

## 4. Acceptance inventory

These are required future checks, not tests run during planning. Give each item a concrete command and/or a manual evidence requirement in the relevant execution ledger after its test exists. Use Python's standard-library `unittest` if pytest is absent; do not add a dependency solely for gate bookkeeping.

| Contract ID | Owner and observing gate | Required observable outcome |
|---|---|---|
| A01 | C0:G1; DATA:G1 | Source allowlist rejects an ISCF or dated alternative path; approved source manifests remain accepted. |
| A02 | D1:G1 | A catalogue item absent from all history appears with zero workload and a required output slot; an unknown future SKU causes an explicit error. |
| A03 | D1:G2 | Numeric IDs 1, 2, 10 are correctly ordered; one order's lines cannot straddle a split; malformed/colliding keys fail. |
| A04 | D1:G3 | Synthetic repeated lines change workload but not duplicate visits; BERNER repeated product-order observations follow the declared deduplication rule. |
| A05 | D2:G1 | Reference construction fills every slot exactly once, includes zeros, respects fixed locations, and has deterministic ties. |
| A06 | D2:G2 | Changing future demand/station rows while holding declared static metadata, origin and n constant leaves reference, b, fixed mask and decision-bearing training fields unchanged; audit source hashes may change. |
| A07 | D2:G3; DATA:G2 | Industrial geometry/fixed-location provenance and preprocessing reconciliation are accepted; no last-future-station shortcut is used. |
| A08 | D2:G4 | Pooled line-weighted b differs correctly from an unweighted block average in a deliberately unequal-volume fixture; sum b is one. |
| A09 | M1:G1 | Scenarios use exactly n complete past orders, include the whole-history vector, and keep the full catalogue indexing. |
| A10 | M1:G2; S1:G2 | The finite robust formula matches a separately written small uncertainty LP, including concentrated inactive-product activation and endpoint cases. |
| A11 | M1:G3 | nu = 0 and empty Z reduce to HIST; nonempty Z has positive possible future workload when nu > 0; fixed h reduces to the analytically tightened scenario caps. |
| A12 | M1:G4 | Delta, nu and n change only their intended contract fields; future scoring limits are identical across method/horizon comparisons. |
| A13 | M2:G1 | Positive proportional rescaling preserves shares; quantity changes do not affect a line-count model; zero-total windows are rejected. |
| A14 | M2:G2 | Fixed products' changing future workload and fully static stations are counted; an order touching fixed and movable items at one station incurs one visit. |
| A15 | M2:G3 | Upper-only feasibility and its implied lower bound agree on a two-station and a many-station hand example. |
| A16 | M2:G4 | Missing/duplicate assignments, overfilled slots, moved fixed products, objective truncation and robust cap violations are detected by failing controls. |
| A17 | S1:G1; S2:G1; SOLVERS:G1 | Approved tiny assignment enumeration, CPLEX and Hexaly agree on optimum visit counts or correctly documented non-optimal statuses, not necessarily identical tied layouts. |
| A18 | S1:G3; S2:G2 | Time limit without incumbent is not labelled proven infeasible; absent bounds remain null; native statuses survive serialization. |
| A19 | S1:G4; MODEL:G2 | The delta_min diagnostic distinguishes valid lower/upper bounds from unknown status and never rewrites the evaluation cap. |
| A20 | S2:G3; SOLVERS:G2 | Set partitions contain the whole catalogue and exact support weights; independent validation passes all returned accepted layouts. |
| A21 | E1:G1 | A dry campaign quotation lists expected unique solves, reused layouts, origins, seeds and cap-based hours without launching a solver. |
| A22 | E1:G2 | An interrupted approved run resumes without overwriting or duplicating completed results; failed runs remain visible. |
| A23 | E1:G3; EXPERIMENT:G1 | The scored layout hash predates future access; evaluator output cannot modify the training payload or allocation. |
| A24 | E2:G1 | Every approved manifest row has an immutable result or explicit failure/eligibility record; no excluded dataset or unapproved run appears. |
| A25 | R1:G1 | Tables reproduce from results, expose missing allocations, and preserve paired observations without counting seeds/stations/nested windows as independent futures. |
| A26 | R1:G2 | Tolerance/activation and tightening frontiers retain negative, infeasible and unresolved cases; no future-selected winner replaces the primary setting. |
| A27 | R2:G1 | Each empirical statement cites a run/table; each mathematical guarantee states its uncertainty-set condition; no unsupported 95% claim appears. |
| A28 | R2:G2; ROOT:G2 | Submitted files and excluded sources are unchanged; calendar fallback and all required handoffs are documented. |

DATA branch integration: D1/D2 contract consistency, full catalogue/geometry conservation, and mutation-based future-leakage controls. MODEL branch integration: scenarios, independent scoring, exact counterpart and minimum-slack formulation agree. SOLVERS branch integration: identical frozen inputs, full objective and comparable resource settings. EXPERIMENT branch integration: provenance through frozen allocation to complete future evaluation and resumable results. REPORT branch integration: reproducible metrics, denominator audit, source/claim audit. ROOT integration: reread the user's latest amendments, reconcile every A-item, reverify branches, and report measured met/unmet/abandoned counts.

## 5. Staged execution and approval points

### Stage 0: protocol and metadata review

Current deliverable: the plan and this handoff. No optimization has been run. Record the user's acceptance or amendment of the primary percentage-point tolerance, activation stress grid, reference policy, fixed-product policy, horizon grid and resource limits. Approval can cover the complete written protocol; do not force separate confirmations for every ordinary implementation detail.

### Stage 1: implementation and correctness

After approval for implementation and its specified tests, implement C0 through S2 with synthetic hand-worked fixtures and source-schema checks. Check installed Python/package versions and license availability only then. Use direct interpreter paths from PLAN Section 8. No environment installation or package upgrade without a separate need and authorization.

Include: a full-occupancy example with a zero-history SKU activated in a future fixture; a fixed inactive SKU causing a robust overload; a b_s = 0 station; unequal order sizes; a station-cap failure masked by a whole-warehouse average; and a deliberately impossible robust case with a verifiable certificate. These fixtures establish correctness, not scientific performance.

### Stage 2: engineering pilot

Produce a pilot quotation before running it. Proposed synthetic instances: the lowest numerical seed in each of the 50-, 500-, and 2000-product families. Use only the first eligible origin, n = P_count, seed 11, delta = 0.01, and arms NOM/HIST+ACT with nu = 0.01. Add the complete BERNER catalogue only if its data/reference gates and horizon eligibility pass; never substitute a top-SKU subset as the industrial case.

Purpose: input/solver integration, memory use, model-build time and runtime estimation. These observations may guide engineering changes, not hidden-future hyperparameter selection. Any outcome-based redesign is explicitly exploratory and creates a new protocol revision. Cross-backend unit comparisons belong to Stage 1; expensive cross-backend pilot repetitions require a quoted budget.

If the pilot cannot fit the full industrial model, report that limit and propose representation improvements. Do not silently remove products, compress by changing demand semantics, reduce supports, loosen constraints or change the scientific dataset.

### Stage 3: approved primary campaign

First-origin/one-seed screening, then the agreed two-origin/three-seed core from PLAN Section 8, subject to eligibility. A campaign config lists which stage is authorized and a total wall-clock/resource ceiling. The runner refuses undisclosed expansion. BERNER with fewer eligible origins is reported with that smaller denominator.

Run the fixed methods and parameters for every approved instance. An optimization infeasibility or no-incumbent result is part of the scientific/computational record, not permission to rerun with easier caps and overwrite the failed run. Record solver retries under distinct IDs and reasons.

### Stage 4: separately quoted sensitivities and diagnostics

Tolerance grid: all declared delta values at nu = 0.01. Activation grid: all declared nu values at delta = 0.01, reusing truly identical models. Tightening frontier: all declared lambda values at the primary delta. Minimum-slack diagnostic: declared cases with certified/unresolved status recorded. Cross-horizon evaluation reuses frozen layouts and does not require new optimization.

Do not automatically run the full delta-by-nu-by-lambda Cartesian product. Quote its cost if a two-dimensional frontier is needed. Select any reduced sensitivity subset by a predeclared size/seed rule, not by future performance. Additional origins j = 2,3 are the declared replication option where eligible and approved.

### Stage 5: analysis and scientific conclusion

Recompute metrics from the immutable layouts and approved future segments; audit denominators, negative cases and numerical boundaries. Write a distinct report/manuscript. Report whether each hypothesis is supported, contradicted, or unresolved, with computational status separate from scientific status. A negative or mixed study can be complete. A claim lacking evidence cannot be marked complete merely because the planned code was written.

## 6. Required handoff contents

Each leaf returns exact owned files, input/output contract hashes, tests executed with interpreter and working directory, exit results, evidence locations, known limitations, and current ledger counts. The driver verifies the evidence afresh rather than trusting this summary.

The final study handoff includes the frozen protocol; source and geometry provenance; all-product allocation outputs; complete run manifests/statuses; independent workload/visit checks; resource accounting; reproducible tables/figures; an explicit assumption/limitation section; and the next decision, if any. Do not state that a future warehouse is universally feasible or that the dated path has been ruled out.
