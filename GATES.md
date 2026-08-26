# Gates: daily robustness re-run on Hexaly with scenario-exact per-day rows

OWNS: Baselines/milp_hexaly_robust.py, Baselines/run_bs_robust_experiment.py, results/**, GATES.md

Scope: Re-execute the full daily-robustness protocol (steps 1-6) using the Hexaly
solver instead of CPLEX, with the workload constraint re-encoded as one row per
(station, training day) using that day's actual lines, and prove that the
optimised layouts now respect the daily ceiling on their own training days.

Checks run with the Hexaly venv python:
C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe
Runner: scratchpad/checks.py (exit 0 AND EXPECT must both hold).

- [x] G1: the solver in use is Hexaly, and CPLEX is absent from that environment
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g1
  EXPECT: G1 PASS hexaly-only-env
  EVIDENCE: exit=0 expect-matched sha256:999fc900669f 0.9s

- [x] G2: step-2 diagnostics reproduce all nine reference values, measured from the data file rather than copied
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g2
  EXPECT: G2 PASS diagnostics-9-of-9
  EVIDENCE: exit=0 expect-matched sha256:f04fb50f9d4f 0.9s

- [x] G3: industrial folds reproduce the six acceptance values and A5 holds on all four folds
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g3
  EXPECT: G3 PASS folds-and-a5
  EVIDENCE: exit=0 expect-matched sha256:b74d0bc162f7 0.8s

- [x] G4: the per-day demand matrix L[p,d] reconciles exactly with the fold's own order lines
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g4
  EXPECT: G4 PASS daily-matrix-reconciles
  EVIDENCE: exit=0 expect-matched sha256:35636fbfa489 31.5s

- [x] G5: the per-day constraint set is a real oracle - satisfied by the incumbent at q=max and violated by a known-bad control layout
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g5
  EXPECT: G5 PASS oracle-discriminates
  EVIDENCE: exit=0 expect-matched sha256:a39284b3a024 30.7s

- [x] G6: the Hexaly backend builds stations x training-days workload rows, not one row per station
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g6
  EXPECT: G6 PASS perday-rows-built
  EVIDENCE: exit=0 expect-matched sha256:205d7a2fd1bb 0.9s

- [x] G7: the smoke run on Hexaly emits every required protocol line
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g7
  EXPECT: G7 PASS smoke-lines-present
  EVIDENCE: exit=0 expect-matched sha256:31972546c6ec 0.8s

- [x] G8: all twelve grid cells completed and wrote their DONE line
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g8
  EXPECT: G8 PASS grid-12-of-12
  EVIDENCE: exit=0 expect-matched sha256:e8778005ed93 0.9s

- [x] G9: the load-bearing contract holds - incumbent/train/q=max is 0 violated and ratio exactly 1.000 on all four folds
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g9
  EXPECT: G9 PASS contract-holds
  EVIDENCE: exit=0 expect-matched sha256:b638e6494a96 0.9s

- [x] G10: the fix worked - optimised arms violate zero of their own training days at q=max
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g10
  EXPECT: G10 PASS train-days-clean
  EVIDENCE: exit=0 expect-matched sha256:3423a82a482f 0.9s

- [x] G11: every quantile directory holds a complete 24-row results.csv with no fold missing
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g11
  EXPECT: G11 PASS results-24-rows
  EVIDENCE: exit=0 expect-matched sha256:199eb6eccc1a 0.9s

- [x] G12: scoring is free of the layout-collision defect - each arm scored from its own training quantile
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g12
  EXPECT: G12 PASS no-layout-collision
  EVIDENCE: exit=0 expect-matched sha256:1e6b7e8ad10f 0.9s

- [x] G13: the incumbent arm still reproduces the known-good laptop reference
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g13
  EXPECT: G13 PASS incumbent-matches-reference
  EVIDENCE: exit=0 expect-matched sha256:55bd2558e57d 0.9s

- [ ] G14: manual - the Hexaly infeasibility mapping is honest (Hexaly cannot prove infeasibility, so no row may claim proven infeasibility)
  EVIDENCE: pending

- [x] G15: every solved layout honours its coverage allowance - no arm breaches more training days than q permits
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g15
  EXPECT: G15 PASS coverage-honoured
  EVIDENCE: exit=0 expect-matched sha256:7aefb5190c92 0.9s

- [x] G16: the counting certificate that retired the ceiling-height sweep is reproducible from the fold data alone
  CHECK: C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe C:\Users\ebelul\AppData\Local\Temp\2\claude\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad\checks.py g16
  EXPECT: G16 PASS counting-certificate
  EVIDENCE: exit=0 expect-matched sha256:2fcaf33636f7 31.6s
