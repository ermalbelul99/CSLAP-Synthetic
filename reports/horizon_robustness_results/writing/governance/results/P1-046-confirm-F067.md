```
F-067 VERIFICATION: CONFIRMED
```

**Case records read** (campaign `ho3_20260913`, field `reference_evaluation.validation.scenario_shares`, each entry carrying `label`/`start`/`stop`; corroborated by `reference_evaluation.validation.minimum_required_slack_exact`):

- HIST_ACT (arm `HIST+ACT`, seed 11): `R/campaigns/ho3_20260913/cases/2e860f825ae72ec360457d268c9ea33588ed0064905ed0d6c334547672559434.json`
- HIST_ACT_T (arm `HIST+ACT-T`, seed 11): `R/campaigns/ho3_20260913/cases/6cec2e7c136a799699d1c28910ee8d132c50959415bf2fd16e330e06a4fcb98f.json`
- NOM contrast (arm `NOM`, seed 11): `R/campaigns/ho3_20260913/cases/c8660e8c29794d83551bb918672fd095e94f6bc9d67692a8e30ebd316bef1df9.json`

Arm-to-case_id mapping taken from `R/campaigns/ho3_20260913/manifest.json` `rows[].arm`/`.seed`/`.case_id`.

**Scenario labels found:**

- HIST_ACT case: 12 entries — `block` [2537,24411), [24411,46285), [46285,68159), [68159,90033), [90033,111907), [111907,133781), [133781,155655), [155655,177529), [177529,199403), [199403,221277), [221277,243151) (11 blocks), plus `history` [0, 243151). `minimum_required_slack_exact` = 1117947199/71202343420.
- HIST_ACT_T case: identical 12 entries (same 11 `block` windows plus `history` [0, 243151)), same `minimum_required_slack_exact` = 1117947199/71202343420.
- NOM contrast case: 1 entry only — `history` [0, 243151). `minimum_required_slack_exact` = 0.

**Old wording ("the historical block scenarios"):** incomplete. It names only the 11 `block`-labeled entries and omits the 12th entry, labeled `history`, [0, 243151), which is stored in the same `scenario_shares` list and used identically in both rows read.

**Corrected row match:** yes. `W/evidence/ANCHOR_SPEC.md` §D row `ho.incumbent.training_slack.hist_act` now reads "12 members: the 11 historical block scenarios plus the single history scenario [0, 243151)" — this is exactly the set found in both case records, and matches F-067's claim (findings.jsonl line 141/142) verbatim in structure and boundary values.
