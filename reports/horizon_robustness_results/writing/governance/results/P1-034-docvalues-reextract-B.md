```json
{
  "comp.supp.workload.definition": {
    "value_exact": "the workload budget $T_s$ is $110\\%$ of a station's complete legacy load, the $10\\%$ being the tolerance the site operates to.",
    "unit": "text",
    "source": {
      "path": "IJSSOL_CSLAP_v1_supplementary.tex",
      "line": 532,
      "sha256": "e5a65a053a8aacfad25d24692c452902e8ed727c27a029b143864efd1c11eab8",
      "quoted_text": "the workload budget $T_s$ is $110\\%$"
    }
  }
}
```

NOTES: Supplement lines considered: 280 (penalty on load(s) above T_s), 296 (workload L_p/V), 309 (workload cap), 439 (workload rows), 522 and 523 (table rows for legacy load and budget), 526 (tabnote: workload normalised by V_s), 532 and 533 (prose), 542 (residual budget), 616 (tabnote repeating the 110% budget). I chose 532 and 533 because they hold the only prose clause that states the budget rule. Rows 522 and 523 are table cells, not clauses, and line 522 does not run on into line 532. I dropped the leading "and" and kept the final period. A Python check confirmed the value is verbatim. The sha256 is the file's hash, which compare_anchors.py:803 checks. Main text not searched; the brief limits the key to the supplement.
