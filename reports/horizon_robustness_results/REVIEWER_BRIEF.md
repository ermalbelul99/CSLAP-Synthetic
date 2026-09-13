> **Superseded (13 September 2026).** This brief was written on 11 September for
> the first independent examination and is kept as a record of that request. It
> is not protocol authority, and some of its assertions were later withdrawn or
> corrected; the current state is in `EXPERIMENT_REVIEW_HANDOFF.md`, the
> independent reviews of 11 and 13 September, and the ledger.

# Brief for the original assistant: independent examination of the E2/R1 work

Paste this whole file as your prompt.

---

## 1. Who you are and what changed

You are resuming the CSLAP horizon-robustness project at
`C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. Since your last checkpoint of
9 September 2026, a delegated agent executed the remaining experimental and
analysis work — E2 (execution) and R1 (analysis) — and stopped there. **R2 and the
research-direction decision were deliberately left to you and the user.**

Your job now has two parts:

1. **Audit** what that agent did, independently. Do not accept its summary.
2. **Reach your own conclusion** on H1–H4 and on whether the undated approach
   should be retained, revised, or set aside for the dated alternative.

The user will then bring your conclusion back to the delegated agent for
discussion. So state your reasoning explicitly enough to be argued with, and be
specific about what you think needs more work.

## 2. Constraints that still bind you

* Empirical data remains restricted to `exp02a_instances/` (exactly 29 instances)
  and `Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv`. No ISCF,
  no dated BERNER variant, no substitute benchmark.
* `reports/horizon_robustness_plan/INDUSTRIAL_AMENDMENT_20260909.md` supersedes
  older industrial preprocessing instructions.
* Do not modify the submitted deterministic-CSLAP article (`IJPR_CSLAP_v4.tex`)
  or its supplementary file.
* δ = 0.01 means one percentage point. ν is an activation-mass budget, not a
  probability. Ceilings are upper-only. Robust feasibility is conditional on the
  realized future belonging to the declared uncertainty set.
* If you want to change the scientific protocol, propose it — do not apply it.

## 3. Read in this order

| File | Why |
|---|---|
| `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md` | the delegated agent's own account, 11 sections |
| `reports/horizon_robustness_results/PILOT_FINDINGS.md` | pilot + the solver-free δ_min survey (§7) |
| `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` | what was fixed in advance, and when |
| `reports/horizon_robustness_results/analysis_audit.md` | denominators, pseudoreplication rules |
| `reports/horizon_robustness_results/MATHEMATICAL_SCOPE.md` §10 | the integer-count restatement |
| `.unlazy/horizon-cslap/status.log` | append-only execution history, including corrections |
| `reports/horizon_robustness_results/artifact_index.json` | machine-readable inventory with content hashes |

## 4. Verify before you trust — exact commands

All from the repository root. **None of these launches a solver.** Re-run them
rather than reading the claimed outputs.

```powershell
# Software correctness: expect 190 OK
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' -m unittest `
  tests.horizon_robustness.test_contracts tests.horizon_robustness.test_data `
  tests.horizon_robustness.test_reference tests.horizon_robustness.test_uncertainty `
  tests.horizon_robustness.test_uncertainty_lp tests.horizon_robustness.test_metrics `
  tests.horizon_robustness.test_industrial tests.horizon_robustness.test_horizon_nesting `
  tests.horizon_robustness.test_integer_rows tests.horizon_robustness.test_cplex `
  tests.horizon_robustness.test_execution tests.horizon_robustness.test_runner `
  tests.horizon_robustness.test_runner_native tests.horizon_robustness.test_analysis `
  tests.horizon_robustness.test_rescoring

# Hexaly-specific: expect 21 OK
& 'C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe' -m unittest `
  tests.horizon_robustness.test_hexaly

# Campaign accounting, authorization, and full independent revalidation
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  tools/horizon_robustness/verify_campaign.py --all --authorization
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  tools/horizon_robustness/verify_campaign.py --revalidate     # slow: rebuilds 319 problems

# Regenerate every table, figure and audit from stored artifacts
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' `
  tools/horizon_robustness/make_analysis.py

# Integrity
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' tools/horizon_robustness/check_protected_sources.py
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' tools/horizon_robustness/check_anonymisation.py
```

## 5. What was executed

| Campaign | Manifest | Implementation | Rows | Unique solves | Native s | Outcome |
|---|---|---|---:|---:|---:|---|
| `pilot_20260910` | `7878826c…` | `c17ef16e…` | 8 | 8 | 6,840 | **SUPERSEDED** — see §7 below |
| `pilot_20260910b` | `8d36ea49…` | `36ed25e9…` | 8 | 8 | 6,840 | 6 COMPLETE, 1 NO_INCUMBENT, 1 NUMERICAL_ISSUE |
| `screen_20260910` | `64178e37…` | `d437a206…` | 360 | 153 | 66,600 | 312 COMPLETE, 48 NO_INCUMBENT_LIMIT |

Across the two non-superseded campaigns: **368 authorized rows, 318 scored, 50
unallocated, 0 missing, `accounting_complete = 1`.** Plus 636 cross-horizon
secondary evaluations and a 360-row solver-free δ_min survey, both at zero solver
cost. **Stage D (δ, ν, λ frontiers) was never executed.**

Budget: 20.88 h of the ~30 h authorized; ~9.1 h unspent; zero retries.
Gates: 45 met, 7 unmet, 0 abandoned.

## 6. The delegated agent's claims — treat each as a hypothesis to test

It was explicit that these are provisional. Your job is to decide whether they
survive.

**C1 — H1 supported.** Nominal is the worst arm in every catalogue-size family.
Over 90 authorized cells per arm: NOM 7 passes, TIGHT 30, HIST 34, HIST+ACT 36.
Conditional on returning a layout: 8 % / 33 % / 52 % / 55 %.

**C2 — H2 mixed, and this is the pivotal claim.** Paired with TIGHT as baseline,
the robust advantage shrinks to zero and reverses as synthetic catalogues grow: on
the 2000-product family TIGHT passes 9/9 where HIST passes 7/9. On BERNER the
robust advantage is large at all three horizons (−1.24 / −1.04 / −0.87 pp worst
excess versus TIGHT).

**C3 — a prediction that was made before the campaign and then held.** A
zero-cost δ_min survey found required slack at 1.7–3.1× a multinomial noise scale
on every synthetic instance, but 20.6–35.7× on BERNER, *rising* with horizon. From
this the agent predicted that tightening would suffice where variation is
finite-sample noise and only the scenario hull would help where there is real
drift. The 18.5-hour campaign then showed exactly that.

**C4 — H3 supported only where testable.** `Z_H = ∅` on all 29 synthetic
instances, so HIST+ACT is literally the same model as HIST there (the runner
shares one solve). On BERNER, 715 inactive products, 181 activating. HIST+ACT
passes 2 of 3 horizons; NOM, TIGHT, HIST and the frozen incumbent pass 0 of 3, at
~11–13 % fewer visits than the incumbent.

**C5 — H4 model-side prediction holds.** Robust arms get easier to solve and to
satisfy as n grows (30/30 layouts returned at n = 2P versus 18/30 at n = P/2), and
δ_min upper bounds fall monotonically with n, matching the proven nesting result.

## 7. What the delegated agent got wrong or had to fix — verify these too

It disclosed the following. Check that the disclosure is complete and that the
fixes are sound.

* **Operator error that invalidated the first pilot.** It created analysis modules
  inside `Baselines/horizon_robustness/` *while a campaign was running*, changing
  the implementation hash, so every subsequent worker refused to solve. The
  directory is preserved with `SUPERSEDED.md` and excluded from all analysis.
* **A numerical escalation.** Hexaly returned a valid BERNER layout violating the
  exact robust rows by 1.06e-06 against a 1e-8 tolerance. On the user's
  instruction the tolerance was **not** widened; instead the fixed-cap rows were
  restated in exact integer counts. **Scrutinise this.** It is the only change
  touching how the optimization model is written. Check the floor argument, the
  ν = 1 and clipped-cap boundary cases, and whether it really is solution-set
  preserving. `MATHEMATICAL_SCOPE.md` §10, `tests/horizon_robustness/test_integer_rows.py`.
* **Four analysis defects it found in its own code**, the worst being that every
  aggregation was keyed without the campaign, so unexecuted screening rows
  silently overwrote real pilot results.
* **A withdrawn phrase.** It initially described a δ_min interval as "leaning
  infeasible"; the interval straddles δ, so the correct status is UNRESOLVED with
  no direction. Check no such language survives anywhere.

## 8. Where to be most adversarial

These are the places the delegated agent itself flagged as weakest.

1. **Solver non-optimality contaminates every visit-cost number.** HIST is
   strictly more constrained than NOM, and TIGHT's cap is strictly inside NOM's,
   so at optimality both must have training objectives ≥ NOM. They do not —
   inversions up to 0.52 % were measured. Compliance figures are exact properties
   of returned layouts and are unaffected, but **any claim about the *cost* of
   protection below ~0.5 % is inside the noise.** Decide whether C1–C4 survive if
   all visit-cost evidence is discarded.
2. **The 50-product family is decided by non-returns.** All 48
   `NO_INCUMBENT_LIMIT` results are there. Neither Hexaly nor CPLEX produced an
   infeasibility certificate anywhere, and the min-slack interval straddles δ.
   Does treating those as failures bias the comparison for or against the robust
   arms?
3. **BERNER carries H3 alone, with one origin and one seed.** Is that enough to
   say anything about activation protection? The agent's own question 3 in §11
   asks whether H3 should be declared untestable under this design.
4. **b is defined from the incumbent**, so the incumbent begins with the whole of
   δ as headroom while any optimizer spends it. The agent suspects this asymmetry
   explains much of the violation pattern. If so, how much of C1 is an artifact of
   the target's construction rather than evidence about robustness?
5. **Retrospective snapshot conditioning.** The industrial catalogue, incumbent,
   capacities and frozen mask are reconstructed from the whole export and assumed
   pre-known. The incumbent itself violates a station on the future window. Is
   that drift, or an artifact of the reconstruction?
6. **C3 is a prediction-then-confirmation argument.** That is rhetorically strong.
   Check that the prediction was genuinely recorded before the campaign — the
   timestamps are in `.unlazy/horizon-cslap/status.log` — and that the noise-scale
   quantity is not circular. It uses a uniform 1/S share rather than the actual
   b_s, and the agent labelled it an order-of-magnitude reference only.

## 9. What was deliberately not done

* **Stage D** (δ, ν, λ frontiers) — never authorized, never run. So there is no
  empirical tolerance frontier, and R1:G2 is legitimately unmet.
* **No seed or origin replication.** One origin, seed 11 only, throughout.
* **No certified lower bound above δ anywhere**, so nothing is proven infeasible.
* **R2 entirely** — no manuscript, no final report, no verdict, no edit to the
  submitted article.

## 10. What to produce

1. **An audit verdict**: does the evidence package hold up? List anything you
   find that is wrong, overstated, unsupported, or missing.
2. **Your own reading of H1–H4**, with the competing explanations you find most
   threatening, and explicitly state where you differ from C1–C5.
3. **A recommendation on the research direction** — retain the undated approach,
   revise it (and how), or move to the dated alternative — with the reasoning that
   would change your mind.
4. **A prioritised list of what still needs work**, separating: (a) things that
   must be fixed before anything is written up, (b) experiments worth buying with
   the ~9 h of unspent budget or a new authorization, and (c) open scientific
   questions.
5. Flag anything where you think the delegated agent's judgment was wrong, not
   just its arithmetic.

Take the evidence on its own terms. If you conclude the approach is not supported,
say so plainly — a negative or mixed result is a valid outcome here and the
delegated agent was instructed not to pre-empt it.
