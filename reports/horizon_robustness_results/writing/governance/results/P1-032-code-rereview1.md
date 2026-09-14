VERDICT: REVISE

Abbreviations: CA = `W/tools/compare_anchors.py`, CC = `W/tools/check_claims.py`, cg = `W/tools/check_governance.py`, RA = `L/fixtures/check_governance/run_all.py`, AS/DS = the real specs, fAS = `L/fixtures/compare_anchors/pass/.../ANCHOR_SPEC.md`. I only read files; I ran nothing and wrote nothing.

## Fix confirmation (changes 1-19; F-042, F-045..F-058)
1. FIXED: CA:206-215, 224-226, 240-254.
2. PARTIAL.
   - Sections A-E are fixed: CA:268-283, 296-327, 333-370, 481-485.
   - NOT FIXED for the document-value Keys table. A row with no backtick key, or with a placeholder, is dropped silently (CA:587-590).
   - A restriction on a pattern without placeholders is ignored, because CA:265-266 returns before the check at CA:268.
3. FIXED: CA:181-186.
4. FIXED: CA:374-399.
5. FIXED: CA:309, 509-515, 586, 747-752.
6. Documents FIXED: the path is checked before any file access (CA:624-637, 796-799). Anchors: CA:526 passes when `sources` is absent (CA:158-159).
7. FIXED: CA:439-450, 522-523.
8. FIXED: CA:533-536.
9. FIXED: CA:670-699, 776-778.
10. FIXED: CA:642, 784-811.
11. FIXED: CC:235-267.
12. FIXED: CC:119-215, 339.
13. FIXED: CC:218-226, 350-353.
14. PARTIAL.
    - CC:53 still accepts any capitalised word before a year.
    - CC:166-167 exempts any 1900-2099 integer inside open parentheses, for example "(2000 rows)".
15. FIXED: CC:331.
16. FIXED: CC:426, 438, 457-513, 525-540.
17. FIXED: RA:131-146, 193-194, 289-297.
18. FIXED: RA:82-83, 117-128, 262-263; both new proofs fire (`p1fix1_run_all.txt:91-92`).
19. FIXED: `stub.md:1` equals `exact_lines` (`required_gates.json:17`). I could not recompute the hash.

**Findings:**
- F-042, F-045, F-048, F-049, F-051 to F-054, F-057: FIXED.
- F-046: NOT FIXED in documents mode (change 2).
- F-047: FIXED. The `documents_bad_quote` spec and merged file now agree (fixture DS:11; `document_values.json:3, 5`).
- F-050: FIXED for documents; still passes vacuously for anchors (change 6).
- F-055, item by item:
  - units: FIXED;
  - year: PARTIAL;
  - `extra.` keys: FIXED;
  - unknown keys: FIXED;
  - escaped pipe: FIXED;
  - swapped attribution: disclosed, not fixed (CC:355).
- F-056: FIXED, with the fixture gaps listed below.
- F-058: NOT FIXED, and outside this brief (cg:606-611 still returns before cg:642-652).

## Q-016 token rules (examples)
The rules are implemented exactly:
- "mean = 3.231630": counts. There is no word boundary before "n = " (CC:134), confirmed by `claims_prefix_boundary/expected.txt:1`.
- "3.23-3.35": both count. A digit before the hyphen makes 3.35 an unsigned range end (CC:193-194).
- "3/3 seeds": both count when a count or bool value is cited (CC:145-146, 200-204); otherwise both are exempt (CC:151).
- "Q-008": exempt, because a letter precedes the hyphen (CC:191-192).
- "§5": exempt (CC:136-138).
- "(2021)": exempt (CC:166-167).
- "13.0–16.0 %": the en dash is not a minus (CC:49), so both count. Only 16.0 is limited to pct (CC:222).
- "0.069–0.179 pp": both count. Only 0.179 is limited to pp (CC:224).

Two side effects fail closed (they reject, never pass):
- "3.23 - 3.35" with spaces makes the upper end negative (CC:195-196).
- Lowercase "s11" or "d02" is never exempt (CC:51).

## Spec expansion and fixtures
- **Anchor spec:** A 147, B 20, C 27, D 9, both by hand (AS:37-91) and in the diagnostic run (203 key lines, `p1fix1_diag_compare_anchors.txt:2-204`).
- **Document spec:** 33 keys (`p1fix1_diag_compare_documents.txt:2-34`). Neither real spec gives a SPEC ERROR (`p1fix1_summary.json:40, 48`).
- **Q-017:** CA:601-618 returns exactly the seven paths from DS:16-21. The two bare names on DS:16 have no prefix to inherit (CA:609, 617). Neither A nor B shows a disallowed source (CA:784-798 runs even without the merged file).
- **Real spec syntax:** yes. Plain `for` at fAS:17, backticked at fAS:18, `.suffix` and `\|` at fAS:24, `for H in` at fAS:25, slash row at fAS:43.
- **New fixtures:** all 20 pass or fail for their stated reason. Weak points:
  - In `section_e_waiver_superstring_key`, the card names the bare key at `Q-102.md:9`, so the card-side check is not tested. The failure comes only from `interpretation_errata.md:3`.
  - `spec_zero_key_row` reaches only the empty-domain path (CA:282-283).
  - No fixture covers `{}` files, entry-level schema fields, "284,862", or anchor `sources`.
- **Vacuous passes:** see defects 1, 2 and 4 below.
- **U8:** confirmed.
  - The only git call is cg:1240-1243, guarded by cg:1235.
  - CA (lines 34-41) and CC (lines 32-40) do not import subprocess.
  - RA launches only `sys.executable` (RA:153, 223, 234, 245).
  - The new fixture directories contain no `.py` files, and the no-git scan is clean (`p1fix1_run_all.txt:93`).
- **Regressions:** none. The seq 26 locators are unchanged (cg:602-611, 642-652, 669-677, 694-713, 1048-1053, 1063-1065), and the real run shows only the two (h) lines (`p1fix1_real_allow_pending.txt:1-3`).

## New defects (severity; file:line; claim; evidence; fix)
1. **MAJOR; CA:587-590.** F-046 is not implemented for the document Keys table: a bad row drops its key silently. Fix: print SPEC ERROR and fail.
2. **MAJOR; CA:158-159, 526.** An anchors entry with no `sources` passes. `anchors_B.json` is never schema-checked, because CC:568-572 reads only `anchors.json`. Fix: require non-empty flattened sources for every non-UNAVAILABLE entry in A and B, and add an anchors-mode disallowed-source fixture.
3. **MINOR; CA:265-266.** A restriction on a pattern without placeholders is ignored. Fix: test the restriction token before the early return.
4. **MINOR; CA:763-764 and CC:535-536.** An entry with no `family` counts as a separate family (None), so two identities of one family can pass. Fix: discard None.
5. **MINOR; CC:53, 166-167.** The year exemption is still loose. Fix: exempt a year only directly inside "(...)" or after "Name (et al.)".
6. **MINOR; CC:265.** Decimal quantize rounds half-even, so "13.65" fails to trace "13.7" but traces "13.6". Fix: use `ROUND_HALF_UP`.
7. **MINOR; CC:350.** The lower end of a range is not limited to the unit written after the upper end. Fix: apply that unit to both ends.

## Required changes (if REVISE)
1. Fix defects 1 and 2 (the vacuous passes), each with a fixture.
2. Fix defects 3 and 4.
3. Recommended: fix defects 5-7, and remove the bare key from `Q-102.md:9` so that fixture tests the card-side check.
