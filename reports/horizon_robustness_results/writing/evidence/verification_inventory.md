# Verification inventory (plan P0 step 6; P1 step 6)

This inventory separates checks **re-run in this writing run** from checks **cited from earlier recorded runs**. A cited check was not re-run here, and the manuscript and the handoff must not say that it was.

## Re-run in this run

| Check | Date | Result | Evidence |
|---|---|---|---|
| `W/tools/check_inputs.py`: 3,502 pinned files, 1.7 GB | 14 Sep 2026 | exit 0, `INPUTS UNCHANGED (3502 files)`, 13 s | `.unlazy/horizon-writing/gate_outputs/P0-G1.txt`; gate `P0-G1.json` |
| `tools/horizon_robustness/check_protected_sources.py` (prior-study ledger, 89 entries) | 14 Sep 2026 | exit 1: `MODIFIED IJPR_CSLAP_v4.tex`, `MODIFIED IJPR_CSLAP_v4_supplementary.tex` (user commit `16b6003`); waived by user decision U5 | `gate_outputs/P0-G2.txt`; gate `P0-G2.json`; `W/governance/user_decisions.md` |
| `tools/horizon_robustness/verify_campaign.py --all --authorization` | 14 Sep 2026 | exit 0: `CAMPAIGN ACCOUNTING VERIFIED (10 campaign(s))`, `AUTHORIZATION VERIFIED (10 campaign(s))`, 36 s. No `--revalidate`; this mode never reaches the data loader (`verify_campaign.py:179`) | `gate_outputs/P0-G3.txt`; gate `P0-G3.json` |
| `W/tools/check_governance.py --probe` | 14 Sep 2026 | exit 0: `MODEL FAMILIES AVAILABLE (3: haiku, opus, sonnet)` | `gate_outputs/P0-G5.txt`; gate `P0-G5.json` |
| Negative-control fixtures of `check_inputs.py` and `check_governance.py` | 14 Sep 2026 | every failing fixture exits 1; both pass fixtures exit 0 (their honesty is under code-review finding F7) | `gate_outputs/nc_*.txt` |

## Cited, not re-run (H1 forbids tests, solvers and evidence regeneration)

| Check | Recorded result | Date | Locator |
|---|---|---|---|
| Unit tests | 218 shared/CPLEX + 23 Hexaly pass | 13 Sep 2026 | `EXPERIMENT_REVIEW_HANDOFF.md:58`; `.unlazy/horizon-independent-review-20260913/GATES.md` G2 |
| Protected sources (then 92 files) and accounting (nine campaigns) | pass | 13 Sep 2026 | `.unlazy/horizon-independent-review-20260913/GATES.md` G2 |
| Independent revalidation of the held-out layouts | 12/12 `ho3_20260913` layouts revalidated | 13 Sep 2026 | `.unlazy/horizon-cslap/status.log` line 89 (REVISION3_VERIFIED_AND_REPORTED); handoff §13 |
| Isolated reproduction of derived tables and figures | 43 files byte-identical | 13 Sep 2026 | `.unlazy/horizon-independent-review-20260913/GATES.md` G4 |
| Regeneration after the 14 Sep figure fix and the held-out drift row | regenerated and committed in `7b4d0a8` | 14 Sep 2026 | `.unlazy/horizon-cslap/status.log` line 90 (REVIEW3_SPARRING_AND_WRITING_PLAN) |

## Known errata relevant to verification claims

- Handoff §8 line 696 says none of the listed test commands launches a solver. This is false: `tests/horizon_robustness/test_cplex.py:67` calls native CPLEX `solve(..., time_limit=5)` (plan F6). The P1 errata record this.
