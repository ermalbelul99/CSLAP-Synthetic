# Document-value specification (P1 step 3; INV-3)

Some values exist only in documents, not in stored tables. Two blind extractors each return JSON with exactly these
keys, and `compare_anchors.py --documents` compares them.

**Entry format.** Each key maps to
`{"value_exact": str, "unit": str, "source": {"path": str, "line": int, "sha256": str, "quoted_text": str}}`.
`quoted_text` must be a verbatim substring of that line. When a value is stated across a line break, quote the
line that holds the number.

**Units:** `pct`, `count`, `share`, `fraction`, `seconds`, `pp`, `text`.

**Text values (Q-015).** A `text` value is copied verbatim from the cited source, with LaTeX markup kept as written. Never paraphrase. When the value spans consecutive lines, join them with a single space and cite the first line. The comparison of A and B normalises whitespace only; in LaTeX sources a `~` (non-breaking space) counts as whitespace.

**Allowed sources:**
- `IJSSOL_CSLAP_v1.tex`, `IJSSOL_CSLAP_v1_supplementary.tex`
- `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md`
- `reports/horizon_robustness_results/DATA_PROVENANCE.md`
- `reports/horizon_robustness_results/analysis_audit.md`
- `reports/horizon_robustness_results/EXPERIMENT_REVIEW_HANDOFF.md`
- `reports/horizon_robustness_results/WRITING_EXECUTION_PLAN_REVIEWED_20260914.md`

User decision U5: never read or use any `IJPR_CSLAP_*` or `C&OR_CSLAP.tex` file.

## Keys

| Key | Unit | What to extract |
|---|---|---|
| `comp.products` | count | industrial catalogue size stated in the companion |
| `comp.stations.reported` | count | picking stations stated (26) |
| `comp.stations.evaluated` | count | stations evaluated (24) |
| `comp.saving.in_sample` | pct | in-sample station-visit reduction on the industrial site |
| `comp.saving.heldout.low`, `comp.saving.heldout.high` | pct | the two held-out-week reductions |
| `comp.budget.definition` | text | how the companion defines the per-station workload budget (quote the defining sentence; the value is the multiplier as text, e.g. "110% of legacy load", if stated) |
| `comp.temporal.label` | text | the LaTeX label of the unseen-week evaluation table (Q-002) |
| `comp.temporal.section` | text | the section title of that evaluation (Q-002) |
| `pred.holdout.delta` | share | predeclared held-out band half-width δ on station shares (Q-015) |
| `pred.holdout.nu`, `pred.holdout.lambda` | fraction | predeclared held-out ν and λ (Q-015) |
| `pred.holdout.seeds` | text | seed set as written |
| `pred.holdout.origin`, `.n` | count | |
| `pred.holdout.solves`, `pred.holdout.configured_seconds` | count / seconds | |
| `pred.twosided.delta_primary` | share | |
| `pred.twosided.block_deviation_quoted` | pp | the incumbent block deviation that §8.2 quotes to justify δ = 0.02 |
| `pred.upperonly.delta` | share | the band half-width δ declared as the primary setting of the upper-only campaigns, before the two-sided amendment (Q-019) |
| `pred.twosided.delta_aspiration` | share | in the two-sided amendment, the δ that is run as the aspiration (Q-019) |
| `pred.twosided.delta_fallback` | share | in the two-sided amendment, the δ described as the user's stated fallback (Q-019) |
| `pred.exploratory.origin` | count | the order index of the first deployment origin, the origin at which the exploratory campaigns were run (Q-019) |
| `prov.products`, `prov.stations_evaluated`, `prov.fixed`, `prov.movable` | count | |
| `prov.stream_end` | count | the stream end exactly as the source states it. The entry also carries `"semantics"`, which is either `"length"` (the number of retained orders, indices 0 to stream_end − 1) or `"last_index"` (the index of the last retained order). Take it from the source's own wording and quote that wording in NOTES (Q-013) |
| `prov.tail_start` | count | 265,025 or the equivalent end of the scored held-out future, from the source that states it |
| `audit.rows.authorized`, `audit.rows.scored`, `audit.rows.no_allocation` | count | |
| `handoff.q2.incumbent_headroom` | text | handoff §11 question 2, the sentence on incumbent headroom |
| `reviewed.layouts.count` | count | the layout count stated at reviewed plan line 60 (Q-009) |
| `comp.supp.sections` | text | JSON list of every section heading in `IJSSOL_CSLAP_v1_supplementary.tex`, in order, each as `"S<k> <title>"`; `line` is the first heading's line (U6) |
| `comp.supp.temporal.details` | text | what the supplement states about the unseen-week or temporal evaluation (extract, split rule, weeks), quoting the most specific line; `"UNAVAILABLE"` if the supplement is silent (U6, Q-002) |
| `comp.supp.workload.definition` | text | how the supplement defines or measures station workload or budgets, if it does (U6) |

**Search rule (U6).** Every `comp.*` value is searched in both `IJSSOL_CSLAP_v1.tex` and `IJSSOL_CSLAP_v1_supplementary.tex`. When a value appears in both files, cite the main-text line as `source` and give the supplement line in NOTES.

A derived value is not extracted. ORCH computes it from the merged entries and records the computation:
- `prov.tail_unused = prov.stream_end − prov.tail_start` when `prov.stream_end.semantics` is `length`;
- `prov.tail_unused = prov.stream_end + 1 − prov.tail_start` when it is `last_index`.

The two extractors must agree on `semantics`, and exactly one formula is valid (Q-013).
