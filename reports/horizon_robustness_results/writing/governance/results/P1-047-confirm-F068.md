F-068 VERIFICATION: CONFIRMED
F-068 FIX: FIXED

1. **Verification.** Confirmed. The preserved prior files hold the earlier, disagreeing seq 29/30 entries while the merged file already held the re-extracted, agreed entry.
- `P1-033-docvalues-reextract-A.prior-independent.json` → `comp.supp.workload.definition.value_exact`: "the workload budget T_s is 110% of a station's complete legacy load, the 10% being the tolerance the site operates to" (no LaTeX markup, quoted_text differs).
- `P1-034-docvalues-reextract-B.prior-independent.json` → value_exact: "Workload is load sum_p L_p/V_s (lines normalised by the station's processing rate V_s); the workload budget T_s is 110%..." (extra leading clause).
- `L/gate_outputs/p1fix2_diag_compare_documents.txt:1` shows the resulting MISMATCH between these two A/B values, confirming the independent files disagreed while the merged file (installed from the agreed re-extraction) did not reflect either.

2. **Fix.** Yes. `W/evidence/independent/document_values_A.json` and `document_values_B.json` now both hold, verbatim, `value_exact: "the workload budget $T_s$ is $110\%$ of a station's complete legacy load, the $10\%$ being the tolerance the site operates to."`, `source.line: 532`, matching both replies (`P1-033-...md`, `P1-034-...md`) exactly. Key-by-key `python -B` diff of prior vs. current for both A and B: 33 keys each, identical key sets, only `comp.supp.workload.definition` changed in either file. `L/gate_outputs/p1_docvalues_install_documents.txt:1` confirms "DOCUMENT VALUES CROSS-CHECK PASSED (34 keys)" post-install (merged file's 34th key, `prov.tail_unused`, is a derived key per `DOCUMENT_VALUES_SPEC.md:56`, not part of independent extraction — no discrepancy).

3. **Source.** Yes. `IJSSOL_CSLAP_v1_supplementary.tex:532-533` joined per the Q-015 rule ("join consecutive lines with a single space, cite the first line") reproduces the installed text verbatim, LaTeX markup intact. Locator line 532 is correct (first line of the clause). Matches `DOCUMENT_VALUES_SPEC.md:13` and the `comp.supp.workload.definition` row at line 52.

4. **Scope.** No. The key-by-key diff (item 2) found exactly one changed key in each file; no other key shows a gap between preserved and current independent files.
