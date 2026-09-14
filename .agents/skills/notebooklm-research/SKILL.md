---
name: notebooklm-research
description: Use Google NotebookLM to create source-based notebooks, ingest scientific papers, run deep research, and answer literature questions with traceable source citations. Use for NotebookLM or scientific-article research in this project; do not use for ordinary Jupyter .ipynb creation.
---

# NotebookLM research for CSLAP

Use the project launcher from the repository root in PowerShell:

```powershell
& .\tools\notebooklm.ps1 --help
```

It runs the user's `uvx --python 3.12 --from notebooklm-skill --with rookiepy notebooklm` command. If `uvx` is missing, install `uv` and Python 3.12; see the install commands in `tools/notebooklm.ps1`. The CLI is supplied by `notebooklm-py`, a dependency of `notebooklm-skill`. Check `--help` when using additional operations because the older instructions in `.claude/notebooklm-research/README.md` and `references/` describe notebooklm-py 0.3.x and have obsolete command shapes. This project setup was checked with CLI 0.7.3.

## Authentication

Check the session first:

```powershell
& .\tools\notebooklm.ps1 auth check --test
```

This machine was authenticated with Firefox: sign in to Google/NotebookLM in Firefox, then run `& .\tools\notebooklm.ps1 login --browser-cookies firefox`. This imports the active browser's Google cookies through `rookiepy` into NotebookLM's local profile. The ordinary `login` command can open Chrome or Playwright Chromium, but bundled Chromium is missing here and the Chrome attempt did not save a session. Recheck auth afterward. The 0.7.x default session path is under `~/.notebooklm/profiles/default/`; do not print, copy, or commit cookie files. Login is account-specific and cannot be completed by project setup alone.

## Scientific literature workflow

1. Define a focused question and search terms, including CSLAP terminology, adjacent storage-location assignment terms, method names, and date bounds where relevant. Inspect existing notebooks with `list --json` before creating a duplicate. This account already has notebooks titled `CSLAP Problem`, `IJPR Articles on CSLAP`, and `SLAP Problem`; check their sources when relevant. Name new notebooks for a topic or review question.
2. Prefer primary scientific sources: publisher landing pages, DOI links, arXiv papers, or the article PDFs the user provides. Check title, authors, year, venue, DOI, and whether a source is a preprint or peer-reviewed version. Add the full paper PDF when a landing page cannot be indexed. Keep a record of source URLs/DOIs and inclusion reasons in the research output.
3. Add sources, wait for indexing, and inspect the source list. Use NotebookLM deep research to discover further material when the question needs it, then assess the discovered items before importing them. Deep research is a discovery/synthesis feature, not independent verification of bibliographic facts.
4. Ask focused questions with `ask --json` and preserve its source IDs/references. Distinguish what individual papers report from NotebookLM's synthesis and from your own inference. Verify important numbers, methods, conclusions, and bibliographic details against the source PDF/full text. Do not fabricate citations or cite a NotebookLM answer as a paper.
5. Deliver a concise research brief with question/scope, search and selection notes, findings tied to article title/DOI/URL, disagreements or limitations, and open questions. If evidence is missing or access is limited, say so. NotebookLM searches the web inside its own research feature; source grounding improves traceability but does not guarantee correctness.

## Current CLI examples

```powershell
& .\tools\notebooklm.ps1 list --json
& .\tools\notebooklm.ps1 create "CSLAP literature: correlated storage" --json
& .\tools\notebooklm.ps1 source add "https://doi.org/..." --notebook NOTEBOOK_ID --json
& .\tools\notebooklm.ps1 source add "C:\path\to\paper.pdf" --notebook NOTEBOOK_ID --type file --json
& .\tools\notebooklm.ps1 source list --notebook NOTEBOOK_ID --json
& .\tools\notebooklm.ps1 source add-research "correlated storage location assignment peer reviewed papers" --notebook NOTEBOOK_ID --from web --mode deep --no-wait --json
& .\tools\notebooklm.ps1 research wait --notebook NOTEBOOK_ID --timeout 1800 --json
& .\tools\notebooklm.ps1 ask "Compare the objective functions and solution methods in these sources, with citations." --notebook NOTEBOOK_ID --json
```

`source add-research` does not import every discovered source by default. Review the results first; use `research wait --import-all --cited-only` only when that selection is appropriate. For more commands, use `& .\tools\notebooklm.ps1 <command> --help` rather than guessing from old docs. Notebook creation, source import, and research within the user's NotebookLM account are part of an explicitly requested NotebookLM research task. Sharing, publication, and deletion require their own explicit request.
