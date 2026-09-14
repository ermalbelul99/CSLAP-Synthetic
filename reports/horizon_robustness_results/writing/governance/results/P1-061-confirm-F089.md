F-089 VERIFICATION: CONFIRMED

1. **Paraphrase vs. verbatim.** The stored `comp.budget.definition.value_exact` is `"110% of legacy load"` (`W/evidence/document_values.json`). Its cited source, `IJSSOL_CSLAP_v1.tex:584`, reads "...each station's budget $T_s$ is $110\%$ of the complete legacy load it carried, frozen and movable products together." The stored value drops "the complete," strips the `$…\%$` markup, and truncates the clause — it is a paraphrase, not a verbatim substring, violating the Q-015 rule at `W/governance/results/P1-W8-prior-DOCUMENT_VALUES_SPEC.md:13` ("copied verbatim... Never paraphrase").

2. **Spec row invited it.** `P1-W8-prior-DOCUMENT_VALUES_SPEC.md:34` reads: "quote the defining sentence; the value is the multiplier as text, e.g. \"110% of legacy load\", if stated." This example literally is the paraphrase later stored, and conflicts with the verbatim mandate in the Q-015 rule (line 13). Confirmed.

3. **Headroom line mismatch.** `R/EXPERIMENT_REVIEW_HANDOFF.md:1028` begins the sentence: "2. **Should b be defined from the incumbent at all?** Because b is the..." (continuing on 1029–1030). The stored entry `handoff.q2.incumbent_headroom.source.line` cites `1029`, not `1028` where the sentence starts. Confirmed.
