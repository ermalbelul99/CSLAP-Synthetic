# Overleaf upload checklist

Everything in this folder goes into an Overleaf project started from the **Taylor & Francis
Interact (APA reference style)** template. `interact.cls`, `apacite` and the T&F support files come
from that template — do not copy them from this repository.

## Upload

```
IJPR_CSLAP_v2.tex          -> replace the template's main.tex (or set it as the main document)
IJPR_CSLAP.bib             -> replace the template's .bib
Images_CSLAP/*.png         -> upload as a folder named exactly Images_CSLAP
```

Seven figures, all referenced by the text:

| File | Used in |
|---|---|
| `r4_number_of_lines_per_station.png`, `r5_pct_change_lines_per_station.png` | heuristic workload figure |
| `Hexaly_number_of_lines_per_station.png`, `Hexaly_pt_relative_change_number_of_lines_per_station.png` | set-variable workload figure |
| `CG_SetPart_number_of_lines_per_station.png`, `CG_SetPart_pt_relative_change_number_of_lines_per_station.png` | column-generation workload figure |
| `reassignment_ksweep_curve.png` | bounded-reassignment curve |

The two TikZ figures (conveyor schematic, heuristic flowchart) are drawn in the tex and need no
uploads; `tikz` ships with Overleaf.

## Before compiling

Fill the placeholders left in the tex, both marked `TODO`:

- four ORCIDs in the title block (search `ORCID`),
- the CIFRE grant number in *Funding details* (search `TODO-CIFRE-NUMBER`).

## Open items that block submission

Search the tex for `TODO(before submission)`. As of this bundle there are five, two of them
substantive:

1. **Table 5 and its protocol paragraph** must be repopulated from the matched-budget re-run
   (`RERUN_IJPR_BENCHMARK.md` in the repository root).
2. **Table 9 (out-of-sample weeks)** has no backing result file and the delivered order data has no
   date column. Supply the artifact or remove the subsection, the table and the rolling-window
   managerial insight.

The other three mark figures quoted from runs whose logs were not kept: the extended-budget probe,
the industrial column-generation iteration and column counts, and the pricing-model build timings.
Each currently reads as a qualitative statement and can be restored with numbers after the re-run.

## After compiling, check

- no undefined references or citations in the log,
- every float placed exactly where it is referenced (all use `[H]`),
- 13 display items, within the 15 IJPR allows,
- abstract 199 words, within 200,
- total word count within 12,000 including abstract, tables, captions and references.
