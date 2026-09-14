```json
{
  "comp.budget.definition": {
    "value_exact": "each station's budget $T_s$ is $110\\%$ of the complete legacy load it carried, frozen and movable products together.",
    "unit": "text",
    "source": {
      "path": "IJSSOL_CSLAP_v1.tex",
      "line": 584,
      "sha256": "441f7fd2e2fa49f96077f1ca2151eaf371bc55aeb1d29d474789d0e9b838b6b8",
      "quoted_text": "each station's budget $T_s$ is $110\\%$ of the complete legacy load it carried, frozen and movable products together."
    }
  },
  "handoff.q2.incumbent_headroom": {
    "value_exact": "Because b is the incumbent's own historical share, the incumbent starts with the full δ of headroom while any optimizer spends it.",
    "unit": "text",
    "source": {
      "path": "reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md",
      "line": 1028,
      "sha256": "5b39596c024a9810bf52288987d476d7b690a1f376826067d8372c710edc6b94",
      "quoted_text": "Because b is the"
    }
  }
}
```

NOTES (≤120 words):

comp.budget.definition — considered: table row L192 "Workload budget of station $s$, in the units of $\sum_p L_p/V_s$" (bare notation, a shortened phrase, rejected); prose L177 introducing $T_s$ with units (still notation, not a computed definition); L212 (operational role, "fixed once installed", not a definition); L584 (sec:industrial) "each station's budget $T_s$ is $110\%$ of the complete legacy load it carried, frozen and movable products together" — chosen, full clause giving the actual value. Cross-checked supplement L532/523 (same 110%-of-legacy-load definition), cited in source per search rule.

handoff.q2.incumbent_headroom — §11 Q2 spans L1028-1032; isolated the one sentence containing "headroom" (L1028-1030, joined single-spaced, cited at L1028), excluding the lead question and the trailing "That asymmetry..." sentence.

**File paths referenced (read-only):**
- `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\IJSSOL_CSLAP_v1.tex`
- `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\IJSSOL_CSLAP_v1_supplementary.tex`
- `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results\EXPERIMENT_REVIEW_HANDOFF.md`
- `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results\writing\evidence\DOCUMENT_VALUES_SPEC.md`

Wrote nothing; ran no git command.
