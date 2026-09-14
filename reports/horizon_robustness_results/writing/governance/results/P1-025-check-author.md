## Report

**Files written or changed** (all six within the allowed paths; nothing else touched):
- `reports/horizon_robustness_results/writing/tools/compare_anchors.py` (new)
- `reports/horizon_robustness_results/writing/tools/check_claims.py` (new)
- `.unlazy/horizon-writing/fixtures/compare_anchors/{pass,mismatch,missing_key,section_e_unresolved,documents_bad_quote}/**` (new)
- `.unlazy/horizon-writing/fixtures/check_claims/{pass,untraced,schema_bad,coverage_bad,argument_interp_only}/**` (new)
- `reports/horizon_robustness_results/writing/tools/check_governance.py` (edited: F-040, F-044)
- `.unlazy/horizon-writing/fixtures/check_governance/run_all.py` (rewritten: F-042, F-043, + generic Part A discovery)
- `.unlazy/horizon-writing/fixtures/check_governance/compare_tracked_outside_edited_twice/run_fixture.py` (edited: F-042)
- `.unlazy/horizon-writing/fixtures/check_governance/{waiver_output_file_outside,ballot_round_null}/**` (new)

**CLI usage and tokens.**
`compare_anchors.py`: `usage: compare_anchors.py [-h] [--root ROOT] [--documents]`. Tokens: `MISMATCH <key>: <detail>`, `ANCHORS CROSS-CHECK PASSED (<n> keys)` / `FAILED (<k>)`, `DOCUMENT VALUES CROSS-CHECK PASSED (<n> keys)` / `FAILED (<k>)`.
`check_claims.py`: `usage: check_claims.py [-h] [--root ROOT] [--schema | --coverage | --argument]`. Tokens: `UNTRACED <claim id>: <token/detail>`, `CLAIMS TRACE PASSED (<n> claims, <m> tokens)` / `FAILED (<k>)`, `CLAIMS SCHEMA PASSED` / `SCHEMA ERROR <file> <path>: <msg>`, `REQUIREMENTS COVERED (<n> rows)`, `ARGUMENT TRACE PASSED`.

Both derive their required-key list at runtime by parsing `ANCHOR_SPEC.md`/`DOCUMENT_VALUES_SPEC.md` under `--root` (not hardcoded), so a small fixture spec drives a small check. Neither writes anything or starts a subprocess.

**Part A fixtures (exit codes observed):**
| Fixture | Exit |
|---|---|
| compare_anchors/pass | 0 |
| compare_anchors/mismatch | 1 |
| compare_anchors/missing_key | 1 |
| compare_anchors/section_e_unresolved | 1 |
| compare_anchors/documents_bad_quote (`--documents`) | 1 |
| check_claims/pass (default/`--schema`/`--coverage`/`--argument`) | 0/0/0/0 |
| check_claims/untraced (default) | 1 |
| check_claims/schema_bad (`--schema`) | 1 |
| check_claims/coverage_bad (`--coverage`) | 1 |
| check_claims/argument_interp_only (`--argument`) | 1 |

**Part B changes:**
1. F-040/N7 — `check_governance.py:1044-1063`, `waiver_valid()` now calls `gate_output_file_ok(output_file)` before `load_gate_output_text`; failing it is `VIOLATION (waiver)`. Fixture `waiver_output_file_outside` added.
2. F-042/N8 — `.../compare_tracked_outside_edited_twice/run_fixture.py:42-48` sets `sys.dont_write_bytecode = True` before `exec_module`; `run_all.py:153-157,243-249` records `W/tools/__pycache__` state before the suite and fails on any *new* file there (pre-existing `.pyc` untouched).
3. F-043/N9 — `run_all.py:68-79` rebuilds `GIT_ARG_PATTERNS` by string concatenation (no longer literal in source) and adds two command-string patterns; `:87-95` `scan_for_git_calls` drops the self-exemption; `:104-113,192-215` the proof now plants two runtime-built files (argument-list and command-string shapes), scans, asserts both fire, deletes them, never executes them.
4. F-044/N10 — `check_governance.py:636-652,686-690`, ballots with a present-but-non-integer `round` (including null/bool) are reported as `VIOLATION (d): <DR file> ballot seq=<seq> has a non-integer round` and excluded from final-round selection and the tally; no crash. Fixture `ballot_round_null` added (mixed null/int rounds, U7-weighted).

**Fixture suite:** `python run_all.py` → `FIXTURES OK (72)`, exit 0. Relevant `ok:` lines:
```
ok: check_governance/no_git_scan (proof fires: _no_git_scan_proof_arglist_*.py)
ok: check_governance/no_git_scan (proof fires: _no_git_scan_proof_cmdstring_*.py)
ok: check_governance/no_git_scan (fixtures are git-free)
ok: check_governance/no_new_pycache (pre-existing: True)
```
All pre-existing fixtures (F-036/F-037/F-038/F-039 regressions, waivers, `ballot_missing_round`) still pass unchanged.

**Real-root output, verbatim:**
`--allow-pending`:
```
IN FLIGHT 25
VIOLATION (h): reports/horizon_robustness_results/writing/tools/check_claims.py exists on disk but is not registered in check_scripts.json
VIOLATION (h): reports/horizon_robustness_results/writing/tools/compare_anchors.py exists on disk but is not registered in check_scripts.json
GOVERNANCE VIOLATIONS (2)
```
`--phase P0 --allow-pending`: identical output. `--probe`:
```
family fable: retry after 2026-09-14T19:27:48Z
family haiku: excluded
family opus: available
family sonnet: available
MODEL FAMILIES AVAILABLE (2: opus, sonnet)
```
The two `(h)` violations are expected: `check_scripts.json` registration is ORCH's step, not an allowed output here.

**Git statement.** I ran no git command in any form (no status/log/rev-parse/init/add/commit/config), from this session or from any script I wrote or edited. The only git call anywhere in the touched files is the pre-existing read-only one inside `check_governance.py`'s `run_git_status` (unchanged, `--snapshot`/`--compare` only, never invoked by me).

**Ambiguities (Q-cards):**
- **Q-ARM-SCOPE** (class E). ANCHOR_SPEC.md's `ts.berner.<DELTA>.pass.<ARM>.count` row has no local arm restriction, unlike the paired `uo.berner.pass.<ARM>.count` row (explicitly NOM/TIGHT/HIST/HIST_ACT). Why it matters: determines whether HIST_ACT_T is a required key there. Decisive test: check whether real extraction B ever populates a `ts.berner.*.HIST_ACT_T` value. Options: (a) full 5-arm Conventions fallback [implemented, conservative-broad]; (b) inherit the 4-arm restriction from the paired row.
- **Q-ROOT-MARKER-SCOPE** (class J). Whether the `WRITING_ORCHESTRATION_PLAN_20260914.md` root-confirmation applies only to the default (unspecified) `--root`, or unconditionally. Implemented unconditionally; every fixture carries a one-line stub. Low risk, easy to relax later.
- **Q-TAIL-UNUSED-SCHEMA** (class J). No exact JSON shape is given for the derived `prov.tail_unused` entry; I accept either `stream_end − tail_start` or `stream_end + 1 − tail_start` read from sibling merged entries, with no required `computation` field format.
