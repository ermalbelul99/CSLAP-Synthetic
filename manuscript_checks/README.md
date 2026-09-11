# Manuscript checks

Static checks for `IJSSOL_CSLAP_v1.tex` and its supplement. Run from anywhere:

```bash
python manuscript_checks/ck.py all
```

Paths are derived from the script's own location, so the suite can be moved as a unit.

## Why this exists outside `.claude/`

`.claude/` is gitignored in this repository. This suite carries the numeric baseline that proves a
prose revision changed no experimental value, so it has to be tracked. It previously lived in
`C:\tmp` and would not have survived a temp wipe.

## Contents

| Path | Role |
|---|---|
| `ck.py` | The checks, T0–T14. `python ck.py all`, or a subset: `python ck.py t2 t13` |
| `claims.tsv` | The claims ledger: one row per load-bearing claim, with its epistemic tier, the qualifier it must carry, and the phrases it may not. Anchored on **verbatim text, not line numbers**, so it survives edits that move lines |
| `allowed_value_changes.tsv` | Numeric changes a recorded re-run legitimately produced, one row per value with its reason. T4 reports a context as a note when every value that moved in it is declared here, and still fails otherwise |
| `baseline/` | Byte copies of the `.tex` and `.bib` taken before the revision series. T4 and T13 compare against these. **Do not refresh them** — they are the reference that makes numeric drift detectable |
| `out/` | Generated reports. Gitignored |

## What T5 actually counts

IJSSOL allows 12,000 words **including all manuscript elements** and desk-rejects for length, so
the count has to match that definition. texcount's "words in text" does not: it omits every
`tabular` body, and it cannot see `\tbl{}` or `\tabnote{}` because those are `interact.cls` macros
rather than `\caption{}`. On this manuscript the difference is about 1,400 words — enough for the
naive count to report comfortable headroom while the manuscript is over the ceiling. T5 therefore
sums text, headers, captions, table bodies, references and tikz, and prints the decomposition.

The bibliography term is an estimate (26 words per entry). Treat the total as a guide and confirm
against the compiled PDF before submitting.

## The three rules worth knowing before editing the manuscript

**Never introduce a blank line inside a paragraph block you are editing.** `paragraphs()` splits on
blank lines, so a stray one can separate a ledger claim's trigger from its required qualifier. The
text still compiles and looks identical, but the invariant silently stops being enforced while T2
continues to pass.

**Do not refresh `baseline/`.** If a value legitimately changes, declare it in
`allowed_value_changes.tsv` with its reason; do not re-snapshot to make the check go quiet.

**Declare a value only if it really moved.** T4's context key is the 40 characters either side with
digits stripped, so editing one table row can merge two rows onto a single key and make an
untouched value look as though it changed. T4 compares each value's total count in the file before
declaring it moved, but if a figure it flags turns out to be byte-identical to the baseline, the
fix is to leave it alone, not to add it to the ledger.

## What is not checked here

No check invokes `pdflatex` or `biber` — no LaTeX engine exists on this machine, and the manuscript
compiles on Overleaf only. Spacing, page breaks, widow/orphan behaviour and float displacement are
therefore invisible to this suite and must be read off the compiled PDF.

Judgement is also out of scope: whether a list improves a passage, whether items are genuinely
parallel, and whether a repaired paragraph still argues its point all need a human.

## Governing rules

The list and run-in checks (T11–T12) implement `reviewer_first_skill` §XIX-A, which is the sole
authority on structural lists in this project and is deliberately **bidirectional**: both a bulleted
Results section and a manuscript with zero lists and unresolved announced counts are findings.
