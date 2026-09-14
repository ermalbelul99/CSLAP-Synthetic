VERDICT: PASS

I only read files. I ran nothing and wrote nothing. Abbreviations: cg = `W/tools/check_governance.py`, ci = `W/tools/check_inputs.py`, Fx = `L/fixtures/check_governance`, rf = `Fx/compare_tracked_outside_edited_twice/run_fixture.py`, ra = `Fx/run_all.py`.

## Fix confirmation (F-036..F-041)
- **F-036 (MAJOR): FIXED.** rf starts no process. A stub replaces the git-status function (rf:49-53, 105), and the script exits 1 at the first failed step (rf:114-115, 123-128).
- **F-037: FIXED.** Both runners copy their inputs into `_work` and compare there (`compare_match/run_fixture.py:36-59`; `snapshot_file_tampered/run_fixture.py:36-59`). Their `meta.json` files and old receipts are gone; no `*.compare.json` exists under Fx.
- **F-038 (MAJOR): FIXED.** New checks at cg:651-659 (rule applies, no valid ballot) and cg:675-681 (sub-question with no position); the four rule exemptions are kept (cg:645-646). The real DR-001 still passes (`fixround3_real_allow_pending.txt:1`).
- **F-039: FIXED.** cg:685 and cg:688 now both default a missing round to 1.
- **F-040: NOT FIXED on the waiver path (MINOR).** The MET path is fixed (cg:199-209, 1089-1090). `waiver_valid` still opens `root / output_file` with no location check (cg:1025, then cg:189-190).
- **F-041: FIXED** (ci:157-159, 163-165).

## U8 git ban
- **W/tools** holds only cg and ci. The only git call is the allowed read-only one at cg:1210-1213; ci has no process or git call.
- **L/fixtures** has 48 `.py` files and no `.git` directory. None of them can run git:
  - Four runners start only the Python interpreter (ra:78, 128, 138, 149; `run_snapshot_fixture.py:56-59`; both new `run_fixture.py:48-51`). rf starts nothing.
  - Every tree they pass as `--root` lacks `.git`, so cg:1205-1206 returns before git is reached.
  - The other `.py` files are two-line data that no runner executes (`check_x.py:1-2`, `test_sample.py:1`).
- **The scan is not vacuous.** The planted file (ra:161) contains both `["git"` and `"git",`. ra:165 passes only if that file is flagged, and the recorded run shows it was (`fixround3_run_all.txt:54`).

## Fixture honesty
Each new fixture fails or passes for exactly its stated reason, with a byte-exact expected output that the old code would not have produced:
- **`batched_outcome_key_without_ballots`:** the outcome key is "A-01" but the ballot positions use "A-001" (DR-900.md:37-71). One expected violation.
- **`weighted_no_valid_ballots_post_u7`:** every ballot is invalid (DR-800.md:38-56) and `u7_from_seq` is 2 (state.json:2).
- **`ballot_missing_round`:** the ballots have no round, and 1+2+2 = 5 matches the stored tally (DR-700.md:37-56). Result: CONSISTENT.
- **`output_file_outside_gate_outputs`:** TEST-G1.json:11 points at `results/stub.md`. One expected violation.
- **`counts_null`:** `source_manifest.json:14` holds null; `expected.txt:1-3`.
- **rf:** the stubbed status line never changes, so the CHANGED result can only come from content hashing (cg:1245-1250, 1358-1362).

The runners work under `_work/run-<id>` and delete it in `finally` (rf:132-134; `compare_match/run_fixture.py:58-59`; ra:168-169). No `_work` files remain. N8 below is the one write outside `_work`.

## Regressions and new defects
**No regressions** in F-027 (cg:597-628, 669-707), F-028 (cg:186-196, 1025-1035, 1092-1094), or F-022 and F-029 (cg:1307-1313, 1342-1346). The real-root `--phase P0` run shows only the 4 expected items (`fixround3_real_phase_P0.txt:1-5`).

**Coverage note:** under U8, no fixture now exercises the real git-status parsing (cg:1207-1218). That is an accepted cost of the ban.

**New defects:**
- **N7, MINOR; cg:1025.** This is the F-040 gap above. A waiver record can point `output_file` anywhere. Fix: call `gate_output_file_ok` in `waiver_valid`, and add a waiver fixture.
- **N8, MINOR; rf:42-45.** Loading cg with `exec_module` writes `W/tools/__pycache__/check_governance.cpython-310.pyc` (the file exists now), which is outside `_work`.
  - Why it matters: snapshots hash every file under W (cg:1226-1236), so a fixture run between a real-root snapshot and its compare can report a false CHANGED.
  - Fix: set `sys.dont_write_bytecode = True` before `exec_module`.
- **N9, MINOR; ra:53, 59-63.** The scanner skips its own file, and it misses git run as a command string (`os.system("git ...")`, `shell=True`).
  - Fix: build the patterns by string concatenation, remove the self-exemption, and add a pattern for a string that starts with `"git `.
- **N10, INFO, pre-existing (old cg:645).** A ballot with `"round": null` mixed with integer rounds raises a TypeError at cg:685 instead of being reported as a violation.
  - Fix: report any non-integer round as a violation.

## Required changes (if REVISE)
None; the verdict is PASS. F-036 and F-038 can now be fix-confirmed. ORCH may record N7 to N9 as MINOR findings for a later tooling round under A-005, keeping N7 under F-040.
