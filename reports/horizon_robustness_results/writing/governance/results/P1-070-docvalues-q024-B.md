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
  }
}
```

NOTES: I considered lines 177 and 192 (units only), 212 (points to the industrial section), 453 (synthetic 10% slack) and 603 (tabnote). The defining clause is in line 584. It starts at "each", after ", and ", and ends with the sentence-final period, per Q-024. The whole sentence sits on that one line. The apostrophe is ASCII; I checked the substring with `python -B` on the raw bytes. The supplement states the same definition at lines 532-533, starting "the workload budget $T_s$ is $110\%$".
