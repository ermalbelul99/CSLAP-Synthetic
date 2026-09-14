Revision 2 of anchors builder A is done. The script ran cleanly (exit code 0, 0 warnings, 0 section E mismatches) and all 44 new keys were computed exactly, with none returned as `"UNAVAILABLE"`.

**Files**
- `C:\Users\ebelul\AppData\Local\Temp\2\p1a_rev2\anchors_A_rev2.py`, SHA-256 `6F547BB855EAE06166C18C799BADE6140E5AE86AB114E741FE2B18906B23129E`
- `C:\Users\ebelul\AppData\Local\Temp\2\p1a_rev2\out_A_rev2.json`, SHA-256 `F73A7AE30B84A0A95CD32537243682C1DB81174D2F9E3E8CC2007BEBE7784AEE`

**Key count:** 252, up from 208.

**F-078: `ho.breach.<ARM>.<SEED>.cap_worst` and `.floor_worst`** (24 keys, pp, cap / floor)
- NOM: s11 1.006414 / 0.178241; s22 0.939065 / 0.232755; s33 1.143883 / 0.167485.
- HIST_ACT: s11 0.081162 / 0.038837; s22 0.085307 / 0.178584; s33 0 / 0.068550.
- TIGHT and HIST_ACT_T: 0 on both sides for every seed.

The script stops with an error if the larger side differs from the row's `.worst`, or if a side is positive while its count is zero (or the reverse). No row triggered either check.

**F-079: single-run savings by margin** (4 keys, pct)
- `margin.min` 252125/21038 = 11.984267 (HIST_ACT_T s22); `margin.max` 317775/21038 = 15.104810.
- `no_margin.min` 155600/10519 = 14.792281; `no_margin.max` 368925/21038 = 17.536125.
- The existing overall minimum and maximum equal the minimum and maximum over the two subsets.

**F-080: layout counts** (16 keys)
- In all four campaigns (`screen_20260910`, `ts_b01_20260912`, `ts_d02_20260912`, `ts_b03_20260912`), NOM = 1, TIGHT = 1, HIST = 3 and HIST_ACT = 3.
- Each count covers seed 11 at n = 10937, 21874 and 43748. For NOM and TIGHT, the rows at 21874 and 43748 have `reused_solve` True.
- Each `layout_hash` in `case_frame.csv` matches the case record's `evaluation.layout_hash`.

**Fields used for future shares and band limits**
- Per station in `evaluation.stations[0..23]`: `share_exact`, `cap_exact`, `floor_exact`.
- Cross-checks, which stop the script on any mismatch: `residual_exact` (share minus cap), `floor_residual_exact` (floor minus share), and the vectors `residuals_exact`, `floor_residuals_exact` and `breaches_exact`.

**Unchanged entries:** I compared `out_A_rev2.json` with `W/evidence/anchors.json` key by key. All 208 original keys are present with identical entries, and the only differences are the 44 added keys. Separately, the unmodified seq 37 script still reproduces `anchors.json` byte for byte.
