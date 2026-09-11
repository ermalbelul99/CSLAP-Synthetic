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
| `ck.py` | The checks, T0–T13. `python ck.py all`, or a subset: `python ck.py t2 t13` |
| `claims.tsv` | The claims ledger: one row per load-bearing claim, with its epistemic tier, the qualifier it must carry, and the phrases it may not. Anchored on **verbatim text, not line numbers**, so it survives edits that move lines |
| `baseline/` | Byte copies of the `.tex` and `.bib` taken before the revision series. T4 and T13 compare against these. **Do not refresh them** — they are the reference that makes numeric drift detectable |
| `out/` | Generated reports. Gitignored |

## The two rules worth knowing before editing the manuscript

**Never introduce a blank line inside a paragraph block you are editing.** `paragraphs()` splits on
blank lines, so a stray one can separate a ledger claim's trigger from its required qualifier. The
text still compiles and looks identical, but the invariant silently stops being enforced while T2
continues to pass.

**Do not refresh `baseline/`.** If a value legitimately changes, record why; do not re-snapshot to
make the check go quiet.

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
