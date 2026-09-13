# Engineering pilot findings — 10 September 2026

Campaign `campaigns/pilot_20260910b/`, manifest hash
`8d36ea49ad1b9158b2b15e3eeaa648feec07bea6c6270b06e960eb781fef277b`,
implementation hash `36ed25e9052df5e9e194ce83cca3cb1dfdf907948bb1feea408e636f8614a044`.
Approved and run as quoted: 8 solves, 6,840 s configured native time, 3-hour
overall wall cutoff, 32-GiB process-tree RSS ceiling, Hexaly, seed 11, one
thread, sequential. Elapsed 8,073.75 s (6,840 s of it configured native solver time).

**Status of everything below: engineering and provisional.** One instance per
catalogue size, one origin, one horizon, one seed. Nothing here tests a
hypothesis; it establishes that the pipeline runs at full industrial scale and
shows where the model's difficulties actually are. A separate campaign under a
**different implementation version** (see §5) supersedes the two robust-arm rows
for any later comparison.

## 1. Computational outcome

| Dataset | P | origin | n | Arm | Status | Native | Objective | Build s | Solve s | Peak RSS |
|---|---:|---:|---:|---|---|---|---:|---:|---:|---:|
| syn_50sku_seed1001 | 50 | 1,737 | 50 | NOM | COMPLETE | FEASIBLE | 6,390 | 0.4 | 119.8 | 0.06 GB |
| syn_50sku_seed1001 | 50 | 1,737 | 50 | HIST+ACT | NO_INCUMBENT_LIMIT | INFEASIBLE | — | 0.5 | 119.5 | 0.06 GB |
| syn_500sku_seed1001 | 500 | 16,830 | 500 | NOM | COMPLETE | FEASIBLE | 60,498 | 3.2 | 299.4 | 0.14 GB |
| syn_500sku_seed1001 | 500 | 16,830 | 500 | HIST+ACT | COMPLETE | FEASIBLE | 61,312 | 4.0 | 299.5 | 0.15 GB |
| syn_2000sku_seed1001 | 2,000 | 47,345 | 2,000 | NOM | COMPLETE | FEASIBLE | 288,663 | 40.6 | 1,200.9 | 0.77 GB |
| syn_2000sku_seed1001 | 2,000 | 47,345 | 2,000 | HIST+ACT | COMPLETE | FEASIBLE | 290,314 | 49.8 | 1,201.0 | 0.85 GB |
| BERNER | 21,874 | 199,403 | 21,874 | NOM | COMPLETE | FEASIBLE | 640,518 | 308.6 | 1,805.2 | 2.72 GB |
| BERNER | 21,874 | 199,403 | 21,874 | HIST+ACT | NUMERICAL_ISSUE | FEASIBLE | — | 337.5 | 1,805.9 | 2.93 GB |

Hexaly consumed its full cap on every solve and never proved optimality; its
objective bound is 0 throughout, so every reported gap is 1.0 and carries no
information. `NO_INCUMBENT_LIMIT` means no feasible point was found at the
configured limit. **It is not infeasibility**, and no infeasibility certificate
was obtained for any case.

**Industrial buildability, previously untested, is now measured.** The full
21,874-product / 24-station model builds in 309–338 s, solves within its cap, and
peaks at 2.72–2.93 GB — under a tenth of the quoted 32-GiB ceiling. It carries
10,346,697 native expressions, 524,976 membership expressions, 480 finite robust
rows and 10 scenarios.

## 2. Future evaluation at δ = 0.01

Every layout was independently validated before scoring, and every future segment
was verified as the exact next complete-order slice of the rebuilt source stream.

| Dataset | Arm | Joint pass | Stations over cap | Worst excess | Mean future visits |
|---|---|---|---:|---:|---:|
| syn_50 | NOM | ✗ | 2 of 5 | +2.0115 pp | 3.8000 |
| syn_500 | NOM | ✗ | 1 of 10 | +1.7092 pp | 3.6600 |
| syn_500 | HIST+ACT | ✗ | 1 of 10 | +0.8510 pp | 3.7060 |
| syn_2000 | NOM | ✗ | 2 | +0.0725 pp | 6.1295 |
| syn_2000 | HIST+ACT | ✓ | 0 | +0.0000 pp | 6.1495 |
| BERNER | NOM | ✗ | 3 of 24 | +2.3232 pp | 2.8425 |

Frozen incumbent on the identical future window, under the identical fixed target
b and ceiling — context, not the headline comparator:

| Dataset | Joint pass | Stations over cap | Worst excess | Mean future visits |
|---|---|---:|---:|---:|
| syn_50 | ✓ | 0 | 0.0000 pp | 4.3400 |
| syn_500 | ✓ | 0 | 0.0000 pp | 4.3940 |
| syn_2000 | ✓ | 0 | 0.0000 pp | 7.8445 |
| BERNER | ✗ | 1 of 24 | +0.3361 pp | 3.2860 |

## 3. What the pilot actually shows

**The problem the extension targets is real.** Nominal optimization cut future
visits by 12.5 % (syn_50), 16.7 % (syn_500), 21.9 % (syn_2000) and 13.5 %
(BERNER) relative to the incumbent, and broke the workload ceiling in every one of
those four cases. On the three synthetic instances the incumbent complied and NOM
did not.

**Where the robust arm could be solved, it helped.** At 500 products it halved the
worst excess (1.7092 → 0.8510 pp) for a 1.26 % visit cost. At 2,000 products it
reached full joint compliance where NOM failed, for a 0.33 % visit cost, and cut
the count of stations exceeding their modelled worst share from 10 to 0.

**Severity falls as the horizon's line count grows.** Worst NOM excess ran
+2.0115, +1.7092 and +0.0725 pp at 50, 500 and 2,000 products. A provisional
mechanism, to be tested rather than assumed: b is defined *from* the incumbent, so
the incumbent sits exactly at b_s with the whole of δ as headroom, while an
optimizer minimising visits subject to r_s ≤ b_s + δ drives stations to the
ceiling and keeps no out-of-sample margin. Both pilot optimized layouts report a
required slack of 0.00998 and 0.00981 against δ = 0.01 — essentially *on* the
ceiling in-sample. Under symmetric block-to-block sampling noise a layout at the
ceiling should breach about half the time, and larger blocks have proportionally
less noise. **Competing explanations that must not be discarded:** the synthetic
generator is stationary, so measured "novelty" there is finite-sample variation
rather than demand drift; and the 2,000-product result is a single instance.

**BERNER is the only case with a non-empty inactive set.** All three synthetic
instances have `Z_H = ∅` at their first origin, so HIST+ACT is *the same model* as
HIST there — the runner's model hash already shares one solve between them. On
BERNER there are **715 historically inactive products, 181 of which receive future
demand, for a realized activation mass of 0.003659**, below the declared stress
level ν = 0.01. So H3 is testable only on the industrial case, and on this window
the primary ν is adequate rather than exceeded.

**BERNER is also the only case where the incumbent itself fails**, breaching one
station by +0.3361 pp, and where only 60.3 % of the catalogue is ordered in the
future window.

## 4. Diagnosis of the 50-product `NO_INCUMBENT_LIMIT`

CPLEX was run on the same model as an implementation check (120 s per solve,
480 s charged):

| Arm | Mode | Result |
|---|---|---|
| HIST, HIST+ACT | visits | `NO_INCUMBENT_LIMIT`; CPLEX also found nothing and returned **no infeasibility certificate** |
| HIST, HIST+ACT | min_slack | η upper bound 0.016744; certified lower bound 0.001400 / 0.001397 |

The interval **straddles δ = 0.01, so this case is UNRESOLVED** and no directional
reading is drawn from it. What is established is only that the best layout found
requires 1.67 pp where the incumbent requires 5.58 pp, so optimization reduces the
required allowance substantially without reaching the declared tolerance within
this budget. Both arms returned bit-identical η, confirming the `Z_H = ∅`
equivalence exactly.

## 5. The `NUMERICAL_ISSUE` and its resolution

BERNER HIST+ACT returned a structurally valid partition with an exactly matching
objective, but two of its 480 robust rows were violated by **+1.0555e-06** in share
units — about 100× the declared 1e-8 model tolerance. Hexaly builds the model in
float64 with an internal feasibility tolerance near 1e-6 and exposes no public
setting to tighten it. This was the escalation point IC6 anticipates, not a
validator defect, and it was referred to the user rather than resolved unilaterally.

On instruction, neither the tolerance nor δ was changed. The fixed-cap rows were
restated in exact integer counts (`MATHEMATICAL_SCOPE.md` §10). The bounded
industrial recheck at the same 1800 s cap now returns
`exact_validation_valid = true`, `model_feasible_exact = true`, all 480 rows
integer-typed, and an exact residual of **−1.208e-06** — strictly inside the
ceiling — with a *better* objective (644,839 versus 661,527).

**Consequence for comparability:** the two BERNER robust results come from
different implementation versions and are never mixed in one comparison. Every
subsequent campaign uses the integer formulation throughout.

## 6. Resource accounting

| Item | Native seconds | Notes |
|---|---:|---|
| Pilot (Stage A, separately approved) | 6,840 configured cap | 8 solves; measured native solve time 6,846.3 s; elapsed 8,073.75 s including load, build and scoring |
| CPLEX 50-product diagnosis | 480 | 4 solves, implementation diagnosis |
| BERNER numerical recheck | 1,800 | 1 solve, formulation verification |

The last two are charged against the ~30-hour stage B–F budget: **2,280 s ≈ 0.63 h
consumed** before any screening solve.

## 7. Addendum — solver-free δ_min survey over all 30 datasets

Run after the pilot at **zero solver cost**
(`tables/slack_survey.csv`, 360 rows, sha256 `844d28a2…`). It records the slack
the *incumbent* layout itself requires under each arm's uncertainty set. Because
the incumbent is always structurally feasible, that is a valid **upper** bound on
δ_min; it can never prove infeasibility.

### 7.1 Required slack tracks sampling noise on synthetic data — and does not on BERNER

`noise_scale_pp` is a crude one-sigma multinomial share-noise scale for a block of
that size, computed with a uniform share 1/S rather than the actual b_s. It is an
order-of-magnitude reference, not a fitted model and not a calibrated drift test.
(Correction 11 Sep 2026: this noise column was first printed a factor of ten too
small; the ratios were computed correctly from the CSV and are unchanged.)

| Family | n/P | η_ref (median) | noise scale | ratio |
|---|---|---:|---:|---:|
| 50 | ½, 1, 2 | 0.0779, 0.0558, 0.0342 | 0.0254, 0.0179, 0.0127 | 3.1×, 3.1×, 2.7× |
| 500 | ½, 1, 2 | 0.0204, 0.0111, 0.0068 | 0.0080, 0.0057, 0.0040 | 2.6×, 2.0×, 1.7× |
| 1000 | ½, 1, 2 | 0.0117, 0.0078, 0.0054 | 0.0042, 0.0030, 0.0021 | 2.8×, 2.6×, 2.6× |
| 2000 | ½, 1, 2 | 0.0067, 0.0043, 0.0031 | 0.0022, 0.0015, 0.0011 | 3.1×, 2.8×, 2.9× |
| **BERNER** | ½, 1, 2 | **0.0170, 0.0163, 0.0147** | 0.000826, 0.000584, 0.000413 | **20.6×, 27.9×, 35.7×** |

Every synthetic instance sits at **1.7–3.1×** the noise scale, stable across four
catalogue sizes and three horizons — what a max-over-blocks-and-stations statistic
of a pure sampling process looks like. **BERNER sits an order of magnitude higher,
and its ratio grows with n.** Its required slack falls only 13 % across a fourfold
horizon increase (0.0170 → 0.0147) where synthetic instances fall about 60 %,
while its noise floor drops as 1/√n. Under pure sampling noise the ratio would
stay roughly constant; a growing ratio is the signature of **persistent
composition drift that averaging does not remove**.

This is descriptive support, in one crude statistic, for what PLAN §6 already
asserted on general grounds:
the stationary synthetic benchmark is a control on finite-sample and solver-cost
effects, **not** a test of robustness to real demand drift, and BERNER is the only
case in the approved data carrying genuine sequence variation.

### 7.2 What this does and does not license

* It is **descriptive**, not a hypothesis test, and rests on one incumbent layout
  per cell.
* η_ref is an **upper** bound. Optimization moves it a lot: on BERNER the robust
  optimizer reached 0.0099988 against the incumbent's 0.0163 — a 39 % reduction —
  so **δ = 0.01 is attainable there**, constructively.
* Reference-feasibility at δ = 0.01 rises steeply with scale on synthetic data
  (0/12 rows at 50 products, 10/12 at 1000, 12/12 at 2000) but is 0/12 for
  BERNER, whose robust rows the incumbent cannot satisfy despite the smallest
  noise floor in the benchmark.
* The practical implication for the campaign is that H1–H3 will be decided mainly
  by the industrial case, and that synthetic non-results should be read as
  "stationary data needs little protection", not as "protection does not work".
