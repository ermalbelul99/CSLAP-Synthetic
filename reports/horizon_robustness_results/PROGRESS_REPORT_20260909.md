# Robust CSLAP extension: completed work and remaining plan

Checkpoint: 9 September 2026. This is an implementation/progress report, **not the final robustness study**. The latest user instruction is to complete current leftovers, report, and stop before further execution. No benchmark or industrial optimization campaign has been run.

## 1. Executive status

The data, mathematical model, independent evaluator, both solver backends, and resumable campaign runner are implemented and verified. The interrupted runner/helper work is finished. All subagents are closed; no unfinished delegated task remains. GPT-5.6 Terra was used for the resumed delegated work. Completed agents were not restarted. Returned code was inspected and corrected locally where its tests did not establish the required behavior.

There are **173 passing software tests** across the appropriate environments: 152 shared/CPLEX tests, including runner/process integration, plus 21 Hexaly-specific tests. These include tiny real native solves, not just mocks. They establish implementation correctness on the tested cases; they do not establish improvement on future benchmark/industrial orders.

The execution ledger has **38 met, 11 unmet, 0 abandoned gates**. The unmet gates belong to empirical execution, analysis, the final scientific report and their integration. At the acceptance-inventory level, A01–A23 are verified; A24–A28 remain open for the full study. The current implementation checkpoint is complete; the original research objective is not. These counts are not a percentage of scientific success.

## 2. Scientific protocol retained

The primary path uses a reliable order sequence without dates. A layout is fixed using history and evaluated on the **next n complete orders**, with matched n-order historical blocks. The declared horizon grid is ceil(P/2), P, 2P; the engineering pilot uses n=P only. Order-ID chronology remains an explicit assumption, not something proved by sorting IDs. Calendar duration, throughput, queues and physical service limits are outside this study.

Every product in the declared closed catalogue occupies a location, including products with zero historical orders. Products outside that catalogue are an assumption violation, not a request for spare slots. Total products equal total modeled slots. For BERNER, an order export cannot prove that it includes physical SKUs never ordered anywhere in that export; the reconstructed exported roster is assumed to be the pre-known catalogue.

At an origin, the incumbent's complete historical workload defines the fixed target b. Future comparisons never reset b to the incumbent's future distribution. Workload ceilings are upper-only, min(1,b+delta). Proportional scaling of all workload leaves these shares unchanged. Upper-only constraints are **not** a symmetric promise that every station stays close to b on its lower side; that distinction is explicit in the evaluator and mathematical notes.

The planned primary delta is **0.01, or one percentage point**, not the old paper's relative 10% slack. It is a predeclared research setting, not an empirically established operationally acceptable allowance. Its sensitivity grid is 0, 0.0025, 0.005, 0.01, 0.02, 0.05. The separate activation-mass budget nu has the same grid and primary value, but a different meaning. No value has been selected from held-out performance.

Implemented comparisons are NOM, ordinary TIGHT, historical-scenario HIST, and HIST+ACT. Minimum-slack optimization diagnoses the allowance required by the declared uncertainty set; it does not silently enlarge future evaluation ceilings. Synthetic reference construction uses the approved historical capacity-respecting LPT policy; industrial reference construction uses the assumed pre-known reconstructed incumbent.

## 3. Industrial preprocessing: preserved and audited

The original `data_loader_industrial.py::load_industrial_data()` is called unchanged. Global product-to-station reconciliation precedes exclusions; GE4/E4 renaming and the original frozen-product mask are retained. The two excluded real stations (`01.GED`, `01.15`) and junk code `01.Z8` enter neither optimization nor evaluation, including the workload denominator. Publication aliases remain separate; the excluded stations are S_25 and S_26 respectively.

Other frozen products remain inside the model and occupy their incumbent slots. Their changing historical/future workload and station visits are counted. Complete retained orders, including small and fixed-only orders, are evaluated. The legacy order-size filter determines the decision pool; it is not a reason to remove those orders' later workload.

| Audited retained system | Count |
|---|---:|
| Products / modeled slots | 21,874 / 21,874 |
| Included stations | 24 |
| Frozen / movable products | 5,899 / 15,975 |
| Complete orders | 284,862 |
| Distinct product-order workload pairs | 1,486,608 |

Two subtle discrepancies were resolved and regression-tested. Seven whitespace-only raw station cells are repaired by the original loader; dropping them first loses seven pairs. Ten duplicate entries arise after reconciliation; robust workload uses distinct pairs, while the original entry-count-based freeze rule is preserved. For one product, that legacy frequency rule changes its freeze classification compared with distinct-order frequency. The original mask is not silently corrected or re-estimated per origin.

**Important qualification:** the catalogue, incumbent, capacities, fixed mask and retention rule are reconstructed from the whole export and assumed pre-known. This is a retrospective, snapshot-conditioned experiment, not evidence that those metadata were actually available at each historical origin. Conditional on that frozen snapshot, demand estimation, b and scenarios are prefix-only. See [DATA_PROVENANCE.md](DATA_PROVENANCE.md) and the [industrial amendment](../horizon_robustness_plan/INDUSTRIAL_AMENDMENT_20260909.md).

## 4. What is implemented

| Initial-plan component | Current result |
|---|---|
| C0: protocol and schemas | Exact source allowlist, immutable full-catalogue contracts, decimal parameters, hashes and explicit statuses. |
| D1, D2R, DI: data/reference | Complete-order chronology, source-specific workload semantics, full slot allocation, fixed-product handling and audited article-compatible industrial adapter. |
| M1: uncertainty | Matched historical scenarios, inactive-product activation set, exact finite robust counterpart and historical activation diagnostics. |
| M2: validation/evaluation | Independent raw-history and layout checks; exact future share comparisons; full fixed workloads, visits, decreases, activation and station-envelope diagnostics. |
| S1, S2: solvers | CPLEX and Hexaly backends for visits and minimum slack, complete allocation outputs, native status/bound retention and independent incumbent validation. |
| E1: runner | Dry quotes, runtime/source/model attestation, file-based native IPC, per-case scoring, safe cache reuse, immutable recovery/retries and bounded process-tree execution. |

The runner's final review corrected hidden horizon expansion, lost per-window evaluations, oversized Windows command-line payloads, incomplete cache identities, invalid-candidate acceptance, non-atomic writes and child-cleanup failures. Minimum-slack cache keys include exact target fractions; activation-decimal hashing no longer collapses distinct exact values through float rounding.

Native solves and future evaluations have separate identities. Each layout is durably saved before its exact next-n segment is selected for scoring. Completed successes and failures are reused on ordinary resume. Deliberate retries need distinct IDs and reasons; corrupt records or an interrupted launch with unknown process identity fail closed. The CLI supervisor covers loading, building, solving and scoring with the overall wall/RSS limits. The lower-level Python runner alone checks parent deadlines between phases; campaigns should use the supervised interface.

Entry points and artifact formats are documented in [RUNNER_USAGE.md](RUNNER_USAGE.md). The code lives in `Baselines/horizon_robustness/`; its tests are in `tests/horizon_robustness/`. No Node, new packages or license changes were needed. The unlazy skill was followed with manual ownership/evidence ledgers and inspected Python checks under the user's Node waiver; no Node hook/framework was installed.

## 5. Verification and pilot readiness

The 173 tests include exact small-instance enumeration, an independently parameterized uncertainty LP with 96 numerical comparisons, proportional scaling, zero-history/frozen products, invalid layouts, objective completeness, exact future boundaries, negative/native-status controls, recovery, malformed artifacts, PID reuse and resource limits. Real four-product CPLEX and Hexaly subprocesses each passed the entire native-input-to-scoring boundary. A short-lived sleeping-process-tree fixture verified actual timeout cleanup.

The latest shared/CPLEX suite passed 152 tests in 10.574 seconds. Its captured-output SHA-256 is `bc67be90af8a760721a49270ff9dd95d22df0aa52cc0051bc74accb0c8065a24`. The Hexaly suite passed 21 tests in 49.691 seconds; output SHA-256 is `73cc1aa1a91ef02eb210af7d49583475648fdd0655144cceb381f507bd562388`. Both ran from the repository root using the supplied Python environments. CPLEX's intentionally impossible fixture prints infeasible-row messages; these are expected negative controls, not failed tests.

A real-data **dry quotation**, without optimization, independently confirms:

| Pilot dataset | Historical origin | Future n | Methods / solves | Native cap per solve |
|---|---:|---:|---|---:|
| 50 products, seed1001 | 1,737 | 50 | NOM + HIST+ACT / 2 | 120 s |
| 500 products, seed1001 | 16,830 | 500 | NOM + HIST+ACT / 2 | 300 s |
| 2000 products, seed1001 | 47,345 | 2000 | NOM + HIST+ACT / 2 | 1,200 s |
| Full retained BERNER | 199,403 | 21,874 | NOM + HIST+ACT / 2 | 1,800 s |

All four are eligible. Total configured native time is **6,840 seconds = 1.9 hours over eight solves**. Loading/preparing this diagnostic quote took 166.203 seconds; that is not solver performance. The proposed three-hour overall cutoff, 32-GiB memory ceiling and 600-second per-attempt extra build allowance must accompany eventual authorization. Regenerate the manifest from the final code before approval; the diagnostic quotation is not an approved run.

The 92 protected empirical-source, submitted-manuscript and original-plan files were rehashed: **zero changes**. The shared industrial loader is also unchanged. No ISCF or other unapproved data was introduced.

## 6. What can and cannot be concluded now

The mathematical notes establish scale invariance, the exact finite robust counterpart, the implications of upper-only ceilings, and uncertainty-set nesting for matched integer-multiple horizons. Their guarantee is conditional: a validated robust layout respects the station ceilings **if the realized future workload vector belongs to the declared uncertainty set**. This is not an assurance that every future belongs to it, nor a probability/95% coverage claim. Smaller-block protection implies larger-block historical-set protection on the declared nested grid; it does not imply monotone held-out feasibility.

We have **not** established any of H1–H4: better held-out feasibility, advantage beyond ordinary tightening, practical value of inactive-product activation, or the empirical horizon trade-off. Industrial model buildability/runtime at full scale is also untested. There is no justified winning method, final tolerance, benefit percentage or publishability conclusion yet. The date-based alternative remains deferred, not ruled out; dates would not by themselves remove the need to restrict future uncertainty. See [MATHEMATICAL_SCOPE.md](MATHEMATICAL_SCOPE.md).

## 7. Remaining original-plan TODOs, in order

1. **Authorize and run E2's engineering pilot.** Regenerate the final-code manifest, confirm its resource ceiling, then run the eight quoted solves. Measure full-model building, native runtime, memory, validation and scoring. Record every failure/resource limit. Do not reduce the industrial SKU universe to make a run fit.
2. **Quote and authorize screening/core campaigns.** Use the approved 29 synthetic instances and full BERNER system only. Screening uses first origin/seed11, three horizons and four arms. The core uses the agreed origins/seeds11,22,33. Preserve explicit ineligible cases, shared-model reuse and all computational statuses. Broader budgets are not yet quoted or authorized.
3. **Run the separately quoted sensitivities and diagnostics.** Delta, activation nu and tightening frontiers vary one axis at a time. Perform minimum-slack diagnostics with honest bound/status qualifications. Add the planned cross-horizon evaluations of already frozen layouts; they need scoring support and artifacts, not new optimization. No future-selected parameter replaces the primary setting.
4. **Implement and execute R1's analysis/reporting layer.** Build reproducible paired tables and useful figures from immutable case/supervisor results. Audit missing-result denominators, solver seeds, nested windows and station-level dependence; do not treat these as independent future replications. Preserve negative, infeasible and unresolved frontier cases. Apply the existing station anonymization to industrial figures.
5. **Complete R2's scientific report/manuscript.** Evaluate H1–H4 against actual run/table evidence. Separate computational failures from scientific negative findings. State closed-catalogue, chronology, snapshot-conditioning, upper-only and uncertainty-set assumptions; explain what the chosen tolerances can and cannot justify. Do not modify the submitted deterministic-CSLAP article to imply results already exist.
6. **Make the follow-up decision together.** Decide whether the undated extension is supported, needs a revised uncertainty family, or warrants the dated-data path. A dated path or other methodological/data expansion is a new decision, not an automatic fallback run.

No remaining task has been abandoned or disguised as completed. The next action is campaign authorization, not additional unfinished agent work.
