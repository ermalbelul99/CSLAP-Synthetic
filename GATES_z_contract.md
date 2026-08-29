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
  EVIDENCE: exit=0 expect-matched sha256:6a5a33b7e95c 31.2s

- [x] Z2: station shares form a complete carve-up of each day - they sum to exactly 1.000 on every training day of every fold
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z2
  EXPECT: Z2 PASS shares-sum-to-one
  EVIDENCE: exit=0 expect-matched sha256:2faf76c0e76e 31.3s

- [x] Z3: the allowance identity holds exactly - total permission is 1 + z*sum(sigma), so it always exceeds 100% of the day and aggregate infeasibility is impossible by construction
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z3
  EXPECT: Z3 PASS allowance-identity
  EVIDENCE: exit=0 expect-matched sha256:89a86a5330b0 36.9s

- [x] Z4: no leakage - mu and sigma computed from training days reproduce exactly when test data is withheld entirely
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z4
  EXPECT: Z4 PASS no-leakage
  EVIDENCE: exit=0 expect-matched sha256:ae6dbcb44086 31.1s

- [x] Z5: the contract discriminates in BOTH directions - the incumbent passes at z=6.07 and FAILS at z=2, so the oracle is not vacuous
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z5
  EXPECT: Z5 PASS discriminates-both-ways
  EVIDENCE: exit=0 expect-matched sha256:4e0ac593f8fc 31.6s

- [x] Z6: NEGATIVE CONTROL - a deliberately concentrated layout (highest-volume products piled onto the largest station) is rejected at every declared z, proving the constraint still prevents the pathology it exists for
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z6
  EXPECT: Z6 PASS concentration-rejected
  EVIDENCE: exit=0 expect-matched sha256:b78fcff425ff 61.5s

- [x] Z7: the budget arithmetic leaves room for the declared Gamma range - protection at Gamma=4 fits inside the slack at every declared z
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks_z.py z7
  EXPECT: Z7 PASS gamma-range-affordable
  EVIDENCE: exit=0 expect-matched sha256:75839ea59934 31.2s

- [x] Z8: PHASE 2 - the backend receives a per-(day, station) right-hand side derived from the share band, never a frozen per-station scalar
  EVIDENCE: milp_hexaly_robust gained rhs_lines (n_days x n_stations, in LINES) and logs contract=share-band(lines); the workload row, the Bertsimas-Sim per-unit deviations a[p,s], the big-M and the as-run verdict all switch units together, and the legacy revealed-peak path is retained for reproducibility. Probe on fold 0 at z=6, 90 s: gamma=0 obj 17479 and gamma=2 obj 23193, BOTH with days_breached=0/38 -- the first time any Gamma>=2 has produced a feasible layout in this study (under the revealed-peak ceiling it never did, because protection at Gamma=1 already needed ~110% of the available slack).

- [ ] Z9: PHASE 3 - beta tightens the share allowance and no longer uses the homogeneous-speed formula that produced a flat ceiling of 13 against revealed ceilings spanning 0.015 to 87
  EVIDENCE: pending

- [ ] Z10: PHASE 6 - the pilot cell completes and its layout honours the contract on every training day
  EVIDENCE: pending

- [ ] Z11: PHASE 7 - all twelve grid cells complete and write six arms each
  EVIDENCE: pending

- [ ] Z12: every solved layout satisfies its own contract on the training days it was optimised against
  EVIDENCE: pending

- [ ] Z13: manual - Gamma arms are compared only within a fixed z; no reported comparison varies z and Gamma together
  EVIDENCE: pending

- [ ] Z14: Gamma_bind and Gamma_cover are reported per station, so the paper states WHERE protection is useful rather than only whether an arm won
  EVIDENCE: pending

- [ ] Z15: the incumbent arm still reproduces its known-good reference, confirming the evaluation path is intact
  EVIDENCE: pending

- [ ] Z16: manual - no row claims a proven infeasibility, since Hexaly is a local-search solver and cannot certify one
  EVIDENCE: pending

- [ ] Z17: every cell writes a complete six-arm results row set with no fold missing
  EVIDENCE: pending

- [ ] Z18: scoring is scoped per z so the daily_metrics layout-collision defect cannot recur
  EVIDENCE: pending
