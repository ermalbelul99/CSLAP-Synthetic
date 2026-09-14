# AI-use record for the extension manuscript (final for the writing phase, 15 September 2026)

This record states how AI was used. It is not a submission declaration; venue-specific wording is decided by the authors when a venue is chosen.

## Who did what

- **Authors (human).** Designed and ran the underlying study with the project's software, approved the experimental protocol and campaigns, directed the writing effort, set its decisions (U1 to U8 and the write-now directive), and will examine the finished article before any scientific or submission decision.
- **Orchestrating assistant.** Claude Opus 5 (`claude-opus-5`) in Claude Code planned and coordinated the writing effort, wrote the orchestration scripts and briefs, verified agent outputs against the stored evidence, and re-plotted two manuscript figures from stored result tables (presentation only).
- **Writing-phase sub-agents (Claude models).**
  - `academic-writer` (Opus): drafted and integrated the manuscript text.
  - `notebooklm-researcher` (Opus): literature discovery and verification, using Google NotebookLM for discovery and public Crossref and OpenAlex records for bibliographic checks.
  - `formulation-reviewer` (Opus): reviewed the written model and protocol against the companion and the accepted model documents (comments only).
  - `narrative-reviewer` (Opus) and `scientific-reviewer` (Opus, manuscript-only mode): reviewed the full draft for argument, structure, repetition, accessibility, faithfulness to the accepted findings and overclaiming (comments only).
  - The lead writer applied the accepted review comments; the orchestrating assistant decided which comments to accept and checked the revised text.
- **NotebookLM.** The literature agent created one dedicated notebook for this review, added eligible published articles to it (publisher pages and article PDFs, including open author versions), asked it cited questions, and removed 23 failed-import error entries it had itself added. NotebookLM was used for discovery and for locating passages; every bibliographic fact and every attributed finding was checked against Crossref, OpenAlex or the article text, and NotebookLM errors found during the review are listed in `literature/LITERATURE_REVIEW.md` §3.4.
- **Preparation-phase agents (before the write-now directive).** Claude Opus and Sonnet agents (and Claude Haiku in the first bootstrap dispatches, before its exclusion) built the evidence extraction scripts, claim register, requirements map, checkers, critic reviews and decision panels. Their outputs are reused as fixed inputs.

## Sequence in the writing phase

Lead-writer passes: pass 1 (introduction, model, protocol, results), 1b (formulation-review corrections), 2a (discussion, conclusions, supplement, abstract, declaration placeholders), 2b-i (related work, verified references), a consolidated revision after review round 1, a final fix pass after review round 2, and one wording micro-fix. Reviews: one formulation review, and two rounds each of narrative and scientific review (the directive's bound). No final language-polishing agent was run. Every review comment was accepted, adjusted or declined by the orchestrating assistant against the claim register before the lead writer applied it; the decisions are recorded in `WRITING_PROGRESS.md` and `HANDOFF_WRITING_PACKAGE.md`.

## Boundaries

- The experimental results were produced by the study's software before writing began. During writing they were reused, not revalidated or recomputed.
- No confidential dataset, site name or unpublished manuscript was uploaded to NotebookLM or any external service; only published articles and general topic queries were used there.
- Every citation in the manuscript is to be verified against its source; unresolved citations remain visible author-review markers.
- The manuscript text was drafted with AI assistance under the authors' direction. No statement that AI was not used may appear in the manuscript.
