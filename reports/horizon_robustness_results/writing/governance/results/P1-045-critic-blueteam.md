# Blue-Team Findings (BCL Round 2)

**F-BT1 — MAJOR — C-17 / Q-020.** Strongest case for option (a): do not reclassify the no-margin held-out misses as a "genuine failure."

Current C-17 wording puts NOM/HIST+ACT's band misses under "Empirical limitation," separate from the "Demonstrated boundary condition" bucket that already covers the TV certificate's failure and the universal set-departure. The evidence supports folding the no-margin misses into the boundary-condition reading, not into "failure":
- C-04 (anchors `ho.min_slack.NOM.*` ≈ 0.019997–0.019999, `ho.min_slack.HIST_ACT.*` same order): every no-margin layout was trained with essentially zero spare slack against δ = 0.02.
- C-21 (`ho.departures.NOM.*`, `ho.departures.TIGHT.*` vs `ho.departures.HIST_ACT.*`, `ho.departures.HIST_ACT_T.*`): 12–13 of 24 stations departed NOM/TIGHT's modelled range, against 2–4 for the margin+scenario arms.
- C-23: the robust guarantee is stated as conditional on future membership in the declared uncertainty set; nothing in the study claims compliance outside it.

Given zero training slack and a future that demonstrably left the (narrow, single-scenario) uncertainty set NOM was built against, the miss is the mechanical, theory-predicted consequence of set departure, not an unexplained defect of "the no-margin policy." Calling it a "genuine failure" would itself overstate the negative: it implies the policy fell short of something it was modelled to deliver, when C-23 already scopes the guarantee away from that case. Proposed addition to C-17: "The no-margin misses are consistent with the same demonstrated boundary condition as the TV-certificate failure: the no-margin layouts carried no training slack (C-04) and departed the modelled range at three to six times the rate of the margin arms (C-21)." This keeps forbidden wording ("margin decides the pass") out and stays within C-03/C-04/C-21's own qualifiers.

**F-BT2 — MINOR — C-01, non-overlapping seed ranges.** The statement notes "the two margin arms' seed ranges do not overlap," but none of the four `allowed_wording` bullets states this plainly for either comparison; a drafter copying a bullet loses the fact. Evidence: `ho.maxdev.NOM.min/.max` = 2.939–3.144 vs `ho.maxdev.HIST_ACT.min/.max` = 2.069–2.179; `ho.maxdev.TIGHT.min/.max` = 1.209–1.756 vs `ho.maxdev.HIST_ACT_T.min/.max` = 1.026–1.160. Proposed addition: "In both the margin and no-margin conditions, the scenario-and-activation arm's seed range for largest station deviation lies entirely below the matching arm's range, with no overlap across all three seeds."

**F-BT3 — MINOR — C-30, practitioner-relevant policy undersold.** C-30 carries only one `allowed_wording` bullet, itself hedged, and omits a fact already in the statement: the reserved margin (one percentage point) was smaller than the incumbent's own largest historical block deviation (1.63–1.83 pp, C-08), yet the tightened layouts still satisfied the band on every held-out seed (`ho.pass.TIGHT.count`, `ho.pass.HIST_ACT_T.count` = 3/3). This contrast is the practically interesting part of the finding and is presently buried in the statement rather than offered as a citable sentence. Proposed addition: "On this case the reserve was smaller than the incumbent's own largest historical station deviation, yet the margin arms still satisfied the band on every held-out seed; the check against historical dispersion is informative, not a proof that the margin was sufficient by design."

No change proposed for C-04 (minimum-slack mechanism) or C-03 (3/3 vs 0/3): both are already stated plainly and at full strength, and C-04's own forbidden-wording list correctly blocks the causal overreach that would otherwise follow from linking it too tightly to C-03.

---

```
F-059 FIX: FIXED
```
1. Yes. `P1-anchors-B-retry.md:68` assigns `Temp\2\p1b_retry\`; `P1-anchors-rev-A.md` step 2 assigns `Temp\2\p1a_rev\`; `P1-anchors-rev-B.md` step 2 assigns `Temp\2\p1b_rev\`; each brief states the directory "is yours alone."
2. Yes. `P1-anchors-B-retry.md:74,76-80` bans `Temp\2\claude\` and A's repo outputs; `P1-anchors-rev-A.md` Isolation bans `W/evidence/independent/`, `W/governance/results/`, `Temp\2\claude\`, and B's private dirs `p1b_rev`/`p1b_retry`; `P1-anchors-rev-B.md` Isolation bans A's `W/evidence/anchors.json`, `W/tools/recompute_anchors.py`, `W/governance/results/`, `Temp\2\claude\`, and A's private dir `p1a_rev`.
3. Yes, all three. `P1-036-anchors-B-retry.md:20-25` (out_B.json, anchors_B.py, SHA-256s, ORCH-verified); `P1-037-anchors-rev-A.md:1-6` ("Nothing was written outside p1a_rev," two SHA-256s); `P1-038-anchors-rev-B.md:1-9` ("written only under...p1b_rev," two SHA-256s).
4. Yes, a residual gap. The isolation rules were hand-written per brief, not a standing rule; `PLAN_ADDENDA.md` has no rule on private working directories or scratchpad isolation (checked, no matches). Rule to carry forward: every DBR/parallel-builder brief (including P2-search-A/B and P3 derivations) must, by default, assign each builder a distinct private working directory and explicitly forbid reading the ORCH scratchpad tree, any other builder's repository outputs, and any other builder's private directory — not reconstructed ad hoc each wave.

```
F-067 FIX: FIXED
```
1. Yes. `ANCHOR_SPEC.md:92` now reads "12 members: the 11 historical block scenarios plus the single history scenario [0, 243151)," matching both builders: `P1-037-anchors-rev-A.md:17-18` ("12 of them, 11 block windows...plus history") and `P1-038-anchors-rev-B.md:17` ("eleven block entries...plus one trailing history").
2. No. Key name `ho.incumbent.training_slack.hist_act` and its computed value (`1117947199/71202343420`, reported identically by both revised builders) are unchanged; only the descriptive clause was corrected.

```
F-068 FIX: FIXED
```
1. Yes. `independent/document_values_A.json:122-131` and `document_values_B.json:122-131` now hold byte-identical entries matching the agreed re-extraction in `P1-033-docvalues-reextract-A.md` and `P1-034-docvalues-reextract-B.md` (source line 532, sha256 `e5a65a053a8a…`, value ending "...tolerance the site operates to."), verified programmatically equal.
2. Yes. Diffing current independent files against `P1-033...prior-independent.json` / `P1-034...prior-independent.json` shows exactly one changed key (`comp.supp.workload.definition`) in each, 33 keys unchanged in both.
3. Yes. `L/gate_outputs/p1fix2_diag_compare_documents.txt` shows the pre-fix MISMATCH; `L/gate_outputs/p1_docvalues_install_documents.txt` reads "DOCUMENT VALUES CROSS-CHECK PASSED (34 keys)" after the install. The merged `document_values.json:267-288` entry also matches.
