**Files (private dir `C:\Users\ebelul\AppData\Local\Temp\2\p1b_rev2\`):**
- `anchors_B_rev2.py` — SHA-256 `2eaf5577379a6f279b3b9500126f6ff4230165f833dfe6c583f9b5f398964e3a`
- `out_B_rev2.json` — SHA-256 `c6db0a4a0af38877a732e0d5875c7ac9f466c1f613e1ebe7c7016fa941b66b3c`

**Key count:** 204 → 248 (44 added, 0 removed, 0 changed).

**F-078 (`ho.breach.<ARM>.<SEED>.cap_worst`/`.floor_worst`, pp):**
NOM: s11 1.006414/0.178241, s22 0.939065/0.232755, s33 1.143883/0.167485.
HIST_ACT: s11 0.081162/0.038837, s22 0.085307/0.178584, s33 0/0.068550.
(TIGHT and HIST_ACT_T all-zero across s11/s22/s33, also emitted.) Fail-loud checks (larger side = `.worst`; side positive iff its count positive) held for all 12 rows without needing a fallback.

**F-079 (single-run savings, pct):**
margin (TIGHT, HIST_ACT_T, 6 rows): min 11.984267 (HIST_ACT_T s22), max 15.104810 (TIGHT s11).
no_margin (NOM, HIST_ACT, 6 rows): min 14.792281 (HIST_ACT s11), max 17.536125 (NOM s33).
Split check held: min(margin_min, no_margin_min) = overall min_pct; max(margin_max, no_margin_max) = overall max_pct.

**F-080 (distinct `layout_hash`, from `case_frame.csv`):** identical across all four campaigns (uo.berner=screen_20260910, ts.berner.d01=ts_b01_20260912, d02=ts_d02_20260912, d03=ts_b03_20260912): NOM=1, TIGHT=1, HIST=3, HIST_ACT=3. All four campaigns' BERNER rows for every arm cover horizons n=[10937, 21874, 43748] (reported per key in `computation`).

**Case-record fields for future shares/band limits:** `evaluation.stations[*].share_exact` (future share), `.cap_exact`, `.floor_exact` (band limits). No UNAVAILABLE keys; all 44 computed from allowed inputs.

**Unchanged verification:** `out_B_rev2.json` compared key by key against `W/evidence/independent/anchors_B.json` (204 shared keys) — 0 differences in `value_exact` or entry content; 0 keys missing.
