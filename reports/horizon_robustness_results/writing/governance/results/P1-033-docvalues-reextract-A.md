Confirmed. Line 532 holds the clause start, line 533 continues it.

Path relative to repo root (as required by `document_source_path_ok`, which rejects absolute paths): `IJSSOL_CSLAP_v1_supplementary.tex`.

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

NOTES (words: 113): Grepped "workload|budget" in the supplement. Candidates: table row (line 523, "Workload budget $T_s$ & 110% of the legacy load") — a bare table cell, not a defining clause; algorithm-section uses of $T_s$/"workload cap" (lines 280, 296, 309) — operational uses, never definitions; sup:instance prose (lines 530-534) — the sentence "the workload budget $T_s$ is 110% of a station's complete legacy load, the 10% being the tolerance the site operates to" is the supplement's actual defining clause, giving both the formula relation and the site-rule rationale, closest to the spec's own worked example ("110% of legacy load"). Chose the prose clause, dropped the leading "and" (conjunction to the unrelated frozen-product clause), cited its first line, 532.

**File read (no writes, no git):** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\IJSSOL_CSLAP_v1_supplementary.tex` (lines 260-329, 425-544), `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results\writing\evidence\DOCUMENT_VALUES_SPEC.md`, `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results\writing\tools\compare_anchors.py` (to confirm sha256 is over the whole file, computed via `python -B`).
