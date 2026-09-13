# Gates: horizon robustness study plan

OWNS: reports/horizon_robustness_plan/**

Scope: A review-ready research and implementation plan, not implementation or empirical validation.

These are manual document-review gates. Proposed software tests and research findings are not completed by checking this ledger. No experimental CHECK commands are authorized by this planning task.

Tooling exception: Node is not installed. The user explicitly authorized disregarding that part of the skill on 2026-09-08. The automated Node ledger lint was not completed; semantic review and read-only PowerShell document checks were used instead. No Node installation, Python replacement checker, solver import, license checkout or empirical experiment was performed.

- [x] P1: The closed catalogue, complete allocation, and treatment of historically inactive products have explicit mathematical and data contracts.
  EVIDENCE: Manual review of PLAN Sections 2.1, 3.4 and 5.3-5.4 and AGENT_HANDOFF IC1/A02/A05/A11: every known product occupies one slot, zero historical counts do not remove products, future activation has a positive uncertainty allowance, and out-of-catalogue arrivals are assumption violations. The exported-roster provenance limitation is explicit.

- [x] P2: The allowed datasets, chronological split, historical reference, and leakage boundaries are unambiguous.
  EVIDENCE: Manual review of PLAN Sections 3-4 and handoff IC1-IC3/A01/A03/A04/A06/A07: exact source allowlist, numeric complete-order chronology, source-specific multiplicities, training-only reference/fixed mask, and static-metadata exception are declared. Read-only generator/loader inspection informed the per-line synthetic-station and full-export industrial-station leakage warnings. Industrial reconciliation remains a future data gate, not an asserted result.

- [x] P3: Horizon choices, workload ceilings, and uncertainty allowances are separately specified and justified.
  EVIDENCE: PLAN Sections 2.4-2.5, 4 and 5.3 distinguish percentage-point tolerance, complete-order horizon and activation stress. The proposed one-point reference and grids are labelled conventions, not operational acceptance or confidence levels. A read-only directory inventory independently confirmed benchmark size counts 12/10/4/3; no workloads or empirical robustness outcomes were computed.

- [x] P4: The proposed robust model has an implementable counterpart, an honest guarantee, and stated failure conditions.
  EVIDENCE: Manual algebraic review of PLAN Sections 5.1-5.6: endpoint/hull maximization gives finite linear rows; a separate linear mixture representation supports future oracle verification; empty inactive sets, fixed inactive locations, tightening equivalence, low-dimensional coverage and arbitrary-mix impossibility are addressed. This is review of a mathematical proposal, not a claim that a solver implementation has passed tests.

- [x] P5: The proposed evaluation can distinguish genuine protection from looser limits, ordinary tightening, and solver effects.
  EVIDENCE: PLAN Sections 6-7 and handoff A12/A18/A25/A26 specify NOM/TIGHT/HIST/HIST+ACT, unchanged future ceilings, matched backends/resources, tightening sensitivities, explicit missing-solution denominators and paired instance-level reporting. Historical/future incumbent rescaling is prohibited; seeds and nested windows are not independent demand replications.

- [x] P6: Solver roles, execution environments, independent validation, and experiment approval boundaries are explicit.
  EVIDENCE: PLAN Sections 8-9 and handoff IC4/IC6/Stages 1-4 specify both supplied Python paths, CPLEX reference and Hexaly performance roles, status handling and independent validation. Get-Item found both interpreters; no imports or licenses were tested. PowerShell arithmetic independently confirmed the proposed synthetic core budget of 1392 solves/139.2 capped solver-hours and optional industrial addition of 48 solves/24 hours. These are planning estimates with campaign approval required, not execution measurements.

- [x] P7: The implementation handoff assigns dependencies, ownership, interface contracts, and observable acceptance outcomes.
  EVIDENCE: AGENT_HANDOFF Sections 1-6 provide a dependency tree, exclusive proposed file ownership, six stable interfaces, acceptance inventory A01-A28, branch integration checks, four-pass review, sequential/no-Node fallback and staged execution boundaries. No future leaf is marked verified and no future test command was run.

- [x] P8: The plan preserves the submitted study and excluded data, retains the calendar fallback, and separates research failure from software completion.
  EVIDENCE: PLAN Sections 3.1, 9 and 11 and handoff A27-A28 prohibit modifying submitted artifacts or importing excluded empirical sources, require evidence-qualified negative/positive conclusions, and retain the dated path for a separately agreed change of question. Final git status shows only the new planning folder beyond the pre-existing untracked entries; local document links and code fences were checked without solver execution.

Final planning review: 8 met, 0 unmet, 0 abandoned. These counts concern the planning deliverable only. Implementation, numerical proofs by test, empirical support and user approval of the proposed protocol remain future work, not hidden completed gates.
