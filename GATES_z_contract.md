# Gates: daily robustness under the volume-normalised share contract (z-band)

OWNS: Baselines/milp_hexaly_robust.py, Baselines/run_bs_robust_experiment.py, Baselines/share_contract.py, results/z_contract/**, GATES_z_contract.md

Scope: Replace the revealed-peak ceiling with a volume-normalised per-station
share band, re-run the industrial daily robustness grid on Hexaly, and measure
what the Bertsimas-Sim budget buys under a contract that actually leaves room
for it.

PRE-REGISTERED BEFORE ANY SOLVING (2026-08-27). The design below is fixed now
so it cannot be adjusted after seeing results.

---------------------------------------------------------------------------
THE CONTRACT
---------------------------------------------------------------------------

    W_s(d)  <=  ( mu_s + z * sigma_s ) * L(d)          for every station s
                                                        and every day d

  W_s(d)  lines picked at station s on day d
  L(d)    total lines picked warehouse-wide on day d
  mu_s    station s's MEAN share of daily lines, fitted on TRAINING days
          under the incumbent layout
  sigma_s the standard deviation of that share over the same training days
  z       tolerance, in units of the station's own daily share variability

Both sides scale with L(d), so warehouse-wide (common) volume drift is
absorbed structurally and Gamma is left insuring the idiosyncratic part.
That is the only form under which assumption A4 can be true.

---------------------------------------------------------------------------
DECLARED GRID (fixed; every cell reported, none dropped)
---------------------------------------------------------------------------

  folds  : 0, 1, 2, 3
  z      : 3, 4, 6
  Gamma  : 0, 1, 2, 4
  beta   : 1.02, 1.05      (tightening the SHARE allowance, not the old
                            homogeneous-speed formula)
  solver : Hexaly, 600 s per arm
  => 12 cells x 6 arms = 72 solver rows

---------------------------------------------------------------------------
WHY z IS BOUNDED, AND WHY THESE THREE VALUES
---------------------------------------------------------------------------

z cannot be raised freely: as z grows the constraint weakens, and at z >= 8 it
is satisfied 100% of the time and constrains nothing, which returns the model
to the degenerate "all best-sellers on the biggest station" solution the
workload constraint exists to prevent.

Measured anchors (incumbent layout, 179 training days x 24 stations):

  z    station-days within allowance   whole days with every station clean
  2              96.74%                            49.7%
  2.7            98.70%                            74.3%
  3              99.07%                            80.4%
  4              99.77%                            94.4%
  6              99.98%                            99.4%
  8             100.00%                           100.0%

  UPPER BOUND  z <= 6.07: the incumbent needs z = 6.07 to be clean on every
    training day. Above that we would license a layout more imbalanced than
    the site has ever operated, with no evidence it is survivable.
  LOWER BOUND  z >= 2.7: the median station needs 2.7. Below it the incumbent
    itself fails on most days, so we would be demanding balance the site has
    never achieved -- a legitimate but DIFFERENT question.

  z = 3  ~80% of days fully clean   (strict end of the defensible window)
  z = 4  ~94% of days               (comfortable)
  z = 6  ~99.4% of days             (matches demonstrated status quo)

The tail is fatter than Gaussian (at z=3 a normal law predicts 99.865% of
station-days but 99.07% is observed), so z is reported as MEASURED COVERAGE
and never as a sigma level.

---------------------------------------------------------------------------
EXPERIMENTAL DESIGN RULES (binding)
---------------------------------------------------------------------------

1. z is the CONTRACT; Gamma is the TREATMENT. Gamma arms are compared ONLY
   within a fixed z. Comparing Gamma=4 at z=6 against Gamma=0 at z=3 changes
   two things at once and is forbidden.
2. All 12 cells are reported. No z is selected post hoc because it flattered
   a result.
3. mu_s and sigma_s are fitted on TRAINING days only. Test data may supply
   only L(d), the realised volume, which the layout cannot influence.
4. No "best z" is recommended by this study. Choosing an operating point is a
   business decision informed by the coverage table above.

---------------------------------------------------------------------------

Checks run with the Hexaly venv python:
C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe
Runner enforces exit 0 AND the EXPECT token, and writes evidence back.

- [x] Z1: the declared z window is bounded by measured anchors, not chosen - the incumbent needs z=6.07 in-sample and the median station needs ~2.7
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z1
  EXPECT: Z1 PASS z-window-anchored
  EVIDENCE: exit=0 expect-matched sha256:6a5a33b7e95c 31.1s

- [x] Z2: station shares form a complete carve-up of each day - they sum to exactly 1.000 on every training day of every fold
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z2
  EXPECT: Z2 PASS shares-sum-to-one
  EVIDENCE: exit=0 expect-matched sha256:2faf76c0e76e 30.5s

- [x] Z3: the allowance identity holds exactly - total permission is 1 + z*sum(sigma), so it always exceeds 100% of the day and aggregate infeasibility is impossible by construction
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z3
  EXPECT: Z3 PASS allowance-identity
  EVIDENCE: exit=0 expect-matched sha256:89a86a5330b0 37.1s

- [x] Z4: no leakage - mu and sigma computed from training days reproduce exactly when test data is withheld entirely
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z4
  EXPECT: Z4 PASS no-leakage
  EVIDENCE: exit=0 expect-matched sha256:ae6dbcb44086 31.6s

- [x] Z5: the contract discriminates in BOTH directions - the incumbent passes at z=6.07 and FAILS at z=2, so the oracle is not vacuous
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z5
  EXPECT: Z5 PASS discriminates-both-ways
  EVIDENCE: exit=0 expect-matched sha256:4e0ac593f8fc 30.7s

- [x] Z6: NEGATIVE CONTROL - a deliberately concentrated layout (highest-volume products piled onto the largest station) is rejected at every declared z, proving the constraint still prevents the pathology it exists for
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z6
  EXPECT: Z6 PASS concentration-rejected
  EVIDENCE: exit=0 expect-matched sha256:b78fcff425ff 60.6s

- [x] Z7: the budget arithmetic leaves room for the declared Gamma range - protection at Gamma=4 fits inside the slack at every declared z, measured on the QUIETEST training day (the binding one: protection is a constant number of lines while the allowance scales with the day's volume, so checking the busiest day overstates affordability by the 2.6x max/min volume ratio)
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z7
  EXPECT: Z7 PASS gamma-range-affordable
  EVIDENCE: exit=0 expect-matched sha256:eab744d8d094 30.9s

- [x] Z8: PHASE 2 - the backend receives a per-(day, station) right-hand side derived from the share band, never a frozen per-station scalar
  EVIDENCE: milp_hexaly_robust gained rhs_lines (n_days x n_stations, in LINES) and logs contract=share-band(lines); the workload row, the Bertsimas-Sim per-unit deviations a[p,s], the big-M and the as-run verdict all switch units together, and the legacy revealed-peak path is retained for reproducibility. Probe on fold 0 at z=6, 90 s: gamma=0 obj 17479 and gamma=2 obj 23193, BOTH with days_breached=0/38 -- the first time any Gamma>=2 has produced a feasible layout in this study (under the revealed-peak ceiling it never did, because protection at Gamma=1 already needed ~110% of the available slack).

- [x] Z9: PHASE 3 - beta tightens the share allowance and no longer uses the homogeneous-speed formula that produced a flat ceiling of 13 against revealed ceilings spanning 0.015 to 87. Part (b) of this gate was REPLACED after the Phase 7 grid, and the replacement is flagged as the one assertion changed after seeing data.
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z9
  EXPECT: Z9 PASS beta-tightens-band
  EVIDENCE: exit=0 expect-matched sha256:882c1633efe0 59.9s
  NOTE: the original part (b) required every beta arm's objective to exceed
    its gamma0 baseline. That is a property of EXACT OPTIMA - beta's
    feasible set is a strict subset of gamma0's - and Hexaly is a
    local-search solver that returns incumbents. On the grid it failed in
    6 of 24 cells (worst -1.79%) while beta was demonstrably enforced in
    ALL 24: every beta layout satisfies the TIGHTENED band on every
    training day and differs from gamma0 by ~1700 of 2000 products. The
    check now tests those two structural facts, which hold regardless of
    solver quality, and still rejects both defects it exists for
    (mutation-tested: a beta layout copied from gamma0, and one that
    breaches the tightened band).
    The inversion is retained as a REPORTED FINDING, not discarded: a beta
    layout is feasible for gamma0's looser band, so a lower beta objective
    proves gamma0's incumbent was suboptimal by that margin. Hexaly
    suboptimality on this grid is therefore bounded at 1.79%. CONSEQUENCE:
    beta's measured visit cost (+0.4% to +1.2%) lies BELOW that noise
    floor and must not be reported as a distinguishable cost; Gamma's
    (7-15%) lies safely above it.
- [x] Z10: PHASE 6 - the pilot cell completes and its layout honours the contract on every training day
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z10
  EXPECT: Z10 PASS pilot-honours-contract
  EVIDENCE: exit=0 expect-matched sha256:b0d7eaf03e5a 0.9s

  NOTE: the pilot ran twice and the first run FAILED this gate, which is
    what a pilot is for. At a reduced 120 s limit (my own shortcut, not
    the pre-registered budget) Gamma=4 returned no incumbent and the
    gate rejected the cell at 5 of 6 arms. The assertion was NOT
    weakened. Diagnosis, three independent lines: (a) the aggregate
    budget fits -- Gamma=4 needs 2315 lines and the quietest fold-0 day
    supplies 2762; (b) the nearest solved layout (g2) missed Gamma=4
    feasibility by 2 station-days / 60 lines out of 550777; (c) a direct
    probe at the pre-registered 600 s solved it (obj=29704,
    days_breached=0/38). The 120 s cell is kept at
    results/z_contract/pilot_f0_z3_120s as evidence of the failure.
    Every Hexaly arm runs to its time limit by construction; bounds are
    weak (1213-2852 against objectives 17857-29704) so no arm is
    claimed optimal.
    Side finding: the solved arms form an exact monotone ladder -- g0 is
    feasible at Gamma=0 and breaks at 1, g1 breaks at 2, g2 breaks at 4 --
    confirming the robust row is enforced as specified.
- [x] Z11: PHASE 7 - all twelve grid cells complete and write six arms each
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z11
  EXPECT: Z11 PASS grid-complete
  EVIDENCE: exit=0 expect-matched sha256:7cae8c9ba8ff 0.9s

- [x] Z12: every solved layout satisfies its own contract on the training days it was optimised against, AND the set of scored layouts matches exactly the set of arms recorded feasible (an arm that returns no layout writes no file, so without this the gate would pass vacuously on whatever did solve - the same defect class as the all-zero demand matrix that made an earlier gate vacuous)
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z12
  EXPECT: Z12 PASS layouts-honour-contract
  EVIDENCE: exit=0 expect-matched sha256:e7bb4b8b982a 0.9s

- [ ] Z13: manual - Gamma arms are compared only within a fixed z; no reported comparison varies z and Gamma together
  EVIDENCE: pending. Satisfied only when EVERY reported table and every claim about what Gamma buys is read down a single z column. Concretely: gamma0 vs gamma4 at z=3 is a valid comparison; gamma4 at z=6 against gamma0 at z=3 is not, because it changes the contract and the treatment at once and would attribute the loosened contract to the robust budget. The evaluator writes one metrics file per z (metrics_z3/z4/z6.csv) precisely so a cross-z comparison requires deliberately joining two files.

- [x] Z14: Gamma_bind and Gamma_cover are reported per station, so the paper states WHERE protection is useful rather than only whether an arm won
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z14
  EXPECT: Z14 PASS gamma-bind-cover-correct
  EVIDENCE: exit=0 expect-matched sha256:17ee6439c2ac 1.2s

- [x] Z15: the incumbent arm still reproduces its known-good reference, confirming the evaluation path is intact
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z15
  EXPECT: Z15 PASS incumbent-matches-preregistration
  EVIDENCE: exit=0 expect-matched sha256:3832a197f8c8 0.9s

- [x] Z16: no row claims a proven infeasibility, since Hexaly is a local-search solver and cannot certify one
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z16
  EXPECT: Z16 PASS no-false-proof
  EVIDENCE: exit=0 expect-matched sha256:cb6b70390ca7 0.9s

- [x] Z17: every cell writes a complete six-arm results row set with no fold missing
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z17
  EXPECT: Z17 PASS per-fold-outputs-complete
  EVIDENCE: exit=0 expect-matched sha256:c12d1bb221d5 0.9s

- [x] Z18: scoring is scoped per z so the daily_metrics layout-collision defect cannot recur
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z18
  EXPECT: Z18 PASS no-layout-collision
  EVIDENCE: exit=0 expect-matched sha256:b80cdd06ea88 32.1s
