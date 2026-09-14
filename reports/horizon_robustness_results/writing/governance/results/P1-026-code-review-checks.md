VERDICT: REVISE

Abbreviations: CA = `W/tools/compare_anchors.py`, CC = `W/tools/check_claims.py`, cg = `W/tools/check_governance.py`, AS = `W/evidence/ANCHOR_SPEC.md`, DS = `W/evidence/DOCUMENT_VALUES_SPEC.md`, ra = `L/fixtures/check_governance/run_all.py`, rf = `.../compare_tracked_outside_edited_twice/run_fixture.py`. I read files only; I ran nothing and wrote nothing.

## Part A findings

**ORCH items**
- **F-045: confirmed, extended.** CA:151 strips the backticked values and CA:143-144 turns them into keys. A plain `for` list with backticked arms also yields no restriction (CA:156-161), so the row falls back to all five arms.
- **Q-012: confirmed.** Expanding the edited spec by hand gives A 147 (AS:37-53), B 20 (AS:59-65), C 27 (AS:71-79), D 9 (AS:85-91). The counts are right only because the backticks were removed; the F-045 code defect remains.
- **F-046: confirmed, extended.** Other zero-key paths that report nothing:
  - a row with no backtick fragment (CA:139-140);
  - a missing section (CA:189-190);
  - a restriction whose token is not in the pattern (CA:171);
  - Section E rows dropped (CA:213-217, 228).
  - Fix: fail on any row or section that yields zero keys.
- **F-047: confirmed (CA:421), extended.** No code compares `semantics` across A, B and merged (DS:54). The `documents_bad_quote` spec says "index of the last retained order" (fixture DS:8), yet its merged value uses the length formula (fixture `document_values.json:5`).

**New findings**
1. **MAJOR; CA:241, 249.** A Section E mismatch can pass without a closed card.
   - In `^Resolution:\s*\S`, `\s*` crosses newlines, so an empty `Resolution:` followed by any later text counts as resolved.
   - `key in text` is a substring test, so a card naming `drift.holdout.hist_tv_max.like_for_like` (AS:62) waives `drift.holdout.hist_tv_max`.
   - Fix: use `[ \t]*` and match the whole key.
2. **MAJOR; CA:455, 396-401, 491.** `--documents` ignores the optional flag. "UNAVAILABLE" in all three files agrees as text and skips the source checks, for any key. Fix: allow it only where DS:45 allows it.
3. **MAJOR; CA:493-496.** `source.path` is not limited to the allowed sources (DS:13-18). An `IJPR_CSLAP_*` file (banned by U5) or an absolute path passes.
4. **MAJOR; CA:256-273.** `value_float` is never checked against `value_exact`, yet Section E (CA:341) and the trace (CC:159) read `value_float`.
5. **MAJOR; CC:158-169.** Document values carry no `value_float` (DS:7; plan:1236-1244).
   - Decimal document values can never trace, and "284,862" fails `int()`.
   - The pass fixture hides this with a `value_float` the spec does not define (`check_claims/pass/.../document_values.json:2`).
   - Fix: normalise as CA:387-393 does, then compare as a Decimal.
6. **MAJOR; CC:42, 114.** The prefix exemptions have no word boundary, so "mean = 3.231630", "origin = 243151", "baseline 3.85" and "decline 2.36" are all exempt.
7. **MAJOR, a gap in the brief (ORCH decides); CC:41, 129.** The brief's own regex and exemptions hide real numbers:
   - the `-` lookbehind hides "3.35" in "3.23-3.35", and hides negatives;
   - the `/` lookbehind hides denominators, which contradicts "k/3 counts as two integers";
   - the 0-10 exemption hides the pass counts (AS:37, 99), so a false "3 of 3" passes.
   - Proposal: small integers must trace when the claim cites a `count` or `bool` key.
8. **MAJOR; CC:313, 325, 339, 351.** `--schema` passes on `[]` and `{}`; the pass fixture's `anchors.json` is `{}`. The entry schemas require only `value_exact` (CC:329, 343), not `sources`, `unit`, `computation`, `line`, `quoted_text` or `extracted_by` (AS:19; plan:1223, 1243-1244, 1275-1279).
9. **MINOR.**
   - A token may match any cited entry, so swapped attributions pass (CC:245).
   - Units are never read, so a pp value written with "%" passes.
   - The year exemption covers any capitalised word before a year (CC:148).
   - Keys outside the spec are not flagged (AS:3), and CC:222 accepts `extra.*` keys that were never cross-checked.
   - An escaped `\|` splits table cells (CA:123; AS:44).
10. **MAJOR; fixtures.**
   - The fixture specs contain no `<ARM>` row, `for` clause, `.suffix` or slash row, so the parser is untested. That is how F-045 and F-046 slipped through.
   - Missing fixtures: a `--documents` pass, Section E waiver pass and fail cases, UNAVAILABLE, and semantics.
   - Existing fixtures fail or pass for their stated reasons. ra covers all 13 Part A pairs plus both Part B fixtures (`p1checks_run_all.txt:12, 45, 51-63`). One name differs from the brief: `argument_interp_only`.

**Safety: confirmed.** Neither CA:30-36 nor CC:29-36 imports subprocess, os or shutil, and every file access is a read (CA:54, 75, 240, 248, 501; CC:53, 71, 93).

**Q-014:** I confirm the ordering: (a) is more conservative, because it fails closed on a wrong `--root`. My choice is (a).

## Part B fix confirmation (F-040, F-042, F-043, F-044)
- **F-040: FIXED** (cg:1048-1053).
  - The expected output differs from what the old code would print, which would have reported the exact_lines check failing on `stub.md:1` instead.
  - Suggestion: put "WAIVED LINE ONE" and its hash in `stub.md`, so that only the location check fails.
- **F-042: NOT FIXED.**
  - The runner fix is in place (rf:46).
  - The suite's check compares file names only (ra:157, 246-247). An unfixed runner would rewrite the existing `check_governance.cpython-310.pyc` (`p1checks_summary.json:45-48`) in place, and the check would not notice.
  - Fix: compare size, mtime_ns and sha256.
- **F-043: FIXED** (ra:74-83, 86-98, 108-111, 220-233).
  - Residual MINOR: the single-quote pattern has no proof, and a bare `"git"` argument is not flagged.
- **F-044: FIXED** (cg:642-652, 689; `ballot_round_null/expected.txt:1`).
  - Residual MINOR: invalid ballots, and DRs that return early at cg:606-611, are not flagged. They cannot crash.

**Regressions: none.**
- F-027 (cg:602-611, 704-713), F-028 (cg:1063-1065), F-038 (cg:669-677, 694-700) and F-039 (cg:704, 707) are intact.
- The real-root run shows only the two expected unregistered-script (h) lines (`p1checks_real_allow_pending.txt:1-3`).

## U8 git ban
Confirmed.
- The only git call is cg:1240-1243, guarded by cg:1235. CA, CC and `check_inputs.py` start no process.
- The fixture runners launch only `sys.executable`: ra:118, 186, 197, 208; `run_snapshot_fixture.py:56`; the `compare_match` and `snapshot_file_tampered` `run_fixture.py:48`.
- None of those roots contains a `.git` (Glob found none). rf replaces git with a stub (rf:110), and the data `.py` files only return 0 (`check_x.py:1-2`).

## Required changes for the author fix round
1. Fix F-045, F-046, F-047 and findings 1-6 and 8.
2. Make the F-042 check compare file content (size, mtime_ns, sha256), not just names.
3. Add the fixtures listed in finding 10, one per fix, with fixture specs written in the real spec's syntax.
4. ORCH decides finding 7 by amending the brief; the author then implements it.
