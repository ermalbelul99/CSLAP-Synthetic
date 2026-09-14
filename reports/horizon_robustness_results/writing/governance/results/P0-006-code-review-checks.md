VERDICT: REVISE

Files: `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results\writing\tools\check_governance.py` (cg), `...\writing\tools\check_inputs.py` (ci), fixtures under `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\.unlazy\horizon-writing\fixtures\`. This review is static: nothing was executed, so the author's reported exit codes are unverified.

## Findings

**F1 BLOCKING (cg:303-316, 322).** Rule (e) accepts a non-MANUAL gate with `status` MET even when `exit_code` is 1 or `token_found` is false. Plan INV-11 (plan:403) says a gate is met only with exit 0 and the token present.

**F2 BLOCKING (cg:253, 273).** Seats with role `replaced` are counted toward panel size, and `replaced_by_seq` is never required. This contradicts GOVERNANCE_FORMATS.md:67 and P0-005:135. A valid ADP-3 panel with one replacement reports 4 seats.

**F3 BLOCKING (cg:486-492, 536).** `--compare` does not detect every repository write:
- If git exits non-zero, the snapshot stores `[]` both times, so the two sides match with no git coverage.
- Porcelain records status, not content, so a second edit to an already-modified or untracked file leaves the line unchanged. `check_inputs` covers only the pinned groups.
- Gitignored paths outside W and L are invisible.

**F4 MAJOR (cg:470-503).** Snapshots can pass while empty, and can be overwritten:
- A wrong `--root` hashes zero files with null git, so compare reports MATCH, which INV-11 forbids. It also creates directories outside the repository (cg:502).
- An existing ID is silently overwritten.
- The ID is not validated, so `..\` escapes `L/snapshots`.
- Compare leaves no receipt, so ORCH's post-wave saves cannot be told apart from agent writes except by run order.

**F5 MAJOR (cg:362-393).** Rule (h) has four gaps:
- It scans only the latest event per seq (cg:385), where the spec requires every event.
- It passes when `check_scripts.json` is absent (cg:364), even though W/tools scripts exist.
- It never matches registry author or reviewer seqs to completed dispatches (unlike rule_c, cg:210-228), so a made-up reviewer passes.
- It compares raw path strings.

**F6 MAJOR (cg:91, 106, 280).** Decision records are keyed by their JSON `id` and gates by their `gate` field, not by file name. A second DR file that reuses a failing DR's id overwrites its rule (d) result, so rule (g) then passes. A duplicate gate name drops a record from rules (e) and (g).

**F7 MAJOR (fixtures).** Several negative controls are not honest:
- `orch_self_rejection` also trips rule (a), because `identity_eq("ORCH","ORCH")` is true (cg:191). It would still exit 1 with `rule_b` deleted.
- `run_snapshot_fixture.py` returns 1 on a checker crash (line 85) and 2 on a setup failure (line 66), and both pass the non-zero negative-control test (cg:312).
- The governance `pass` fixture never exercises rule (b), addenda headings for rule (f), phase gates for rule (g) (it uses TEST:G1/G2), a registry for rule (h), an L tree, or second_chair and replaced seats.
- The inputs `pass` fixture lacks `manuscript_checks/out/`, `__pycache__` and `.pyc`, so it cannot test those exclusions, and there is no MISSING fixture.

**F8 MINOR (cg:51, 131-143).** Log integrity has three weaknesses:
- Unknown `event` values pass.
- With `--allow-pending`, IN FLIGHT seqs are not printed, although the spec says they are reported.
- A malformed JSON line crashes the script instead of producing a VIOLATION.

**F9 MINOR (cg:178).** The ORCH-built clarification is applied only to BLOCKING and MAJOR findings, though the clarification has no severity limit. The verifier's confirmer role and the fix-confirmer's critic role are never checked against the log.

**F10 MINOR (cg:84, 254, 328).** A missing family (None) counts as a distinct family. A missing PLAN_ADDENDA.md passes. The DR JSON regex is not anchored to the start of the file.

**F11 MINOR (cg:487, 537-538).** Plain `git status` can rewrite `.git/index`. Compare does not print the porcelain-difference lines the spec requires.

**F12 MINOR (ci).** Enumeration matches make_manifest.py:25-64 (ci:34-78), `parents[4]` is correct (ci:89), and an empty manifest fails (ci:103). I found no Windows case or separator trap: relative paths come from rglob under the resolved root, and a case-only rename shows as ADDED. Remaining issues:
- Deleting a pinned file together with its manifest entry passes, because `counts` (source_manifest.json:12-22) is never checked.
- `elapsed` is unused (ci:138).

**Safety.** ci writes nothing and runs no subprocess (imports ci:12-17). cg writes only at cg:502-503, runs only `git status` (cg:487-490), and never writes to W.

**Q-card (class E).**
- **Question:** should `--allow-pending` also tolerate a CONFIRMED finding whose fix is not yet confirmed?
- **Why it matters:** such a finding fails even with `--allow-pending` (cg:193-196), yet the resume protocol runs the audit after every wave (plan:437).
- **Decisive test:** run the audit between a critic round and its fix.
- **Options:** extend `--allow-pending`, or keep failing.
- **Conservative default:** extend `--allow-pending` only; without the flag, it remains a violation.

## Required changes for author fix round

1. **F1:** a non-MANUAL gate with status MET requires `exit_code == 0` and `token_found is True`.
2. **F2:** exclude `replaced` seats from the count and from the family set. Require `replaced_by_seq`, and require it to match a completed log seq.
3. **F3:**
   - Fail snapshot and compare when git exits non-zero, and use `git --no-optional-locks`.
   - Store the SHA-256 of every porcelain-listed path outside W and L.
   - For ignored paths, either walk sizes and mtimes (skipping `.git`), or document the gap in the docstring and in an addendum.
4. **F4:**
   - Require `<root>/W/governance` and at least one hashed file.
   - Refuse existing IDs, and validate IDs against `[A-Za-z0-9._-]+`.
   - Print the snapshot SHA-256.
   - Have compare write `<ID>.compare.json` with a timestamp and the result.
5. **F5:**
   - Scan all events.
   - Require the registry once any script exists under W/tools or W/math/tools, with every such script listed.
   - Validate author and reviewer through `check_participant`.
   - Normalise paths.
6. **F6:** key DRs and gates by file name, and flag an id/file-name mismatch or a duplicate as a violation.
7. **F7:**
   - Give each failing fixture an `expected.txt` holding its exact VIOLATION lines, and assert them with a runner.
   - The snapshot runner exits 1 only when compare exits 1 and prints `CHANGED ...note.md`; otherwise it exits 0 and prints `NEGATIVE CONTROL BROKEN`.
   - Extend both `pass` fixtures to cover the gaps listed under F7.
   - Add a `missing/` fixture and snapshot steps for an L write, ADDED and REMOVED.
8. **F8–F11:** fix as stated in each finding.
9. **F12:** check per-group counts against `counts`, and print the manifest SHA-256.
