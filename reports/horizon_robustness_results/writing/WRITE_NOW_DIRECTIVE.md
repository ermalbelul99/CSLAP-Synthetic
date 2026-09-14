# Write-now directive: reuse the accepted study, stop rebuilding its validation

Authority: the user's latest instruction to replace the long preparation workflow
with writing and focused writing reviews. This directive supersedes conflicting
P0-P9 preparation, tooling, panel and gate requirements in
`../WRITING_ORCHESTRATION_PLAN_20260914.md`, its addenda and the earlier reviewed
plan. It preserves the scientific scope, confidentiality and source protection.
It is a delegation instruction, not a manuscript or an execution log.

## Immediate action

Do not resume the old seq-71 claim-register/checker workflow. Record one short
scope-change note, preserve existing work, and proceed to manuscript production.
Mark abandoned preparation tasks **superseded by user instruction**, not passed,
completed or scientifically invalid. No new governance checker or panel is needed
to record this user decision. The old checker framework is no longer a gate.

The recorded state is P1-W9, no work in flight, next seq 71. Inspect whether any
partial manuscript now exists before writing; reuse it if so. At the time this
directive was prepared, the manuscript, drafts and architecture folders had no
files. Do not delete or rebuild the existing evidence package.

## Treat the experimental evidence as fixed inputs

The study's accepted results and established qualifications are the factual basis
of the article. Do not independently establish their validity again.

Reuse these existing inputs (paths relative to this writing directory unless
prefixed otherwise):

* `evidence/anchors.json` and `evidence/document_values.json`: existing numerical
  inputs; no new extraction or independent recomputation.
* `evidence/claims.md`, `evidence/claims.json`,
  `evidence/interpretation_errata.md`: working claim and qualification references,
  not a new gate that must be perfected before drafting.
* `governance/prompts/P1-register-rev1.md` and already resolved question/decision
  notes: carry forward settled corrections directly into the relevant prose.
  Do not execute that brief's old dispatch/checking instructions. Optional
  register housekeeping can follow the manuscript; it cannot delay it.
* `../EXPERIMENT_REVIEW_HANDOFF.md`, `../CAMPAIGN_PREDECLARATION.md`,
  `../WRITING_EXECUTION_PLAN_REVIEWED_20260914.md`: accepted study context and
  scientific boundaries, read with the already documented corrections.
* Existing publication tables and figures under `../tables/` and `../figures/`.
  Campaign directories are retained evidence, not a work queue.
* Repository-root `IJSSOL_CSLAP_v1.tex`, `IJSSOL_CSLAP_v1_supplementary.tex`,
  and `manuscript_checks/baseline/IJSSOL_CSLAP_v1.bib`: the submitted companion,
  notation/style reference and bibliography. Do not use older IJPR drafts.

Preserve unfavorable as well as favorable findings, all scope limitations, the
fixed-product/excluded-station treatment, the closed catalogue and the
snapshot-conditioned information boundary. The accepted framing is a bounded
comparative study with a positive margin result and an observed scenario/fidelity
trade-off, not a universal future guarantee or a calibrated automatic margin rule.

Distinguish accepted measurements from interpretations. A previous panel's vote
is not empirical evidence. Use established corrections; do not silently invent
new interpretations or replace conflicting numbers. If a concrete contradiction
is encountered during writing, identify the two existing sources and flag that
specific claim for the user. Continue unaffected sections. This exception is not
permission to search for new discrepancies or restart a study-wide audit.

## Stop these activities

* No solver calls, tests, stored-layout revalidation, rescoring, raw-order reads,
  campaign regeneration, new surveys or use of the remaining future tail.
* No blind numerical builders, anchor recomputation, document-value re-extraction,
  repeated accounting checks, new experimental analyses or significance tests.
* No brute-force mathematical checker, edge-case test harness, independent
  derivation campaign, code review of solver internals or new checker fixtures.
* No replacement governance framework, requirements-map completion programme,
  checker repair rounds, model probes, style-voting panels or competing blueprint
  competitions before prose. Deferred checker defects stay deferred.
* No compulsory numerical-macro infrastructure. Reuse existing anchors directly;
  simple formatting/export of accepted values into LaTeX tables or macros is
  allowed if useful, but must not become a prerequisite for drafting.

## Keep these writing-quality activities

Check that the manuscript faithfully states the accepted results, uses the right
units and denominators, distinguishes exploratory from held-out evidence, and
does not overclaim. This is editorial fidelity, not experimental revalidation.
Read accepted formulations to explain them correctly; correct notation and
exposition in the new paper without reopening the implemented model.

Keep focused comparison with the closest published work and with the submitted
companion. Verify any new literature citation against the source it attributes;
do not invent references. One research pass and one targeted follow-up for a
specific missing citation are enough for the initial draft. An unresolved
citation gets a visible author-review marker in the draft, never a fabricated
entry. Do not present an unfinished reference as verified in the final package.

The current governing decisions U1-U3 specify a **venue-neutral, AI-written
article**, companion alignment, and compilation by the user on Overleaf. Do not
reinstate the earlier Taylor & Francis first-draft gate at this stage or infer
that a future venue has approved the workflow. Keep truthful AI disclosure and
defer venue-specific submission requirements until a venue is chosen.

## Short execution workflow

### 1. Produce manuscript text now; run supporting work in parallel

Use one concise outline, prepared by the lead writer as part of drafting. No
separate style canon, paragraph-by-paragraph blueprint or outline vote.
Default structure: introduction and companion connection; related work;
information contract and formulation; methods and protocol; results; discussion
and limitations; conclusions. Adjust this structure editorially as needed.

The first production pass must deliver substantive LaTeX sections, not just a
skeleton or another plan. Start with problem/context, model/protocol and the
accepted results. Complete the introduction, discussion and abstract as the
argument becomes coherent. Literature work must not block sections whose sources
and content are already available.

| Assignment | Agent and skills | Scope |
|---|---|---|
| Lead writer/integrator | `academic-writer`; `academic-paper`, `reviewer_first_skill`, `operations-research-scientific-writing` | Owns the manuscript; writes clear, connected prose and a self-contained companion bridge |
| Literature support, parallel | `academic-researcher`; `literature-review-citation`, `citation-verification` | Focused closest-work comparison and verified citation notes; no new empirical baselines |
| Mathematical exposition review, once sections exist | `formulation-reviewer`; `mathematical-formulation`, `robust-modeling` | Checks the written equations, definitions and inherited/changed constraints against accepted notes; no new computations |
| Results presentation, when needed | Lead writer using `experimental-results-presentation` | Formats existing tables/figures and interprets accepted findings; no re-analysis |

Use the actual `.claude/agents/` and `.claude/skills/` files, read before applying
them. This directive overrides inherited thesis/journal defaults, demands for
new testing, automatic escalation into research, and elaborate process gates.
Read only the references relevant to the current section.

Keep at most three active sub-agent assignments with disjoint write ownership.
One integrator owns final manuscript files; reviewers return comments, not
competing rewrites. Background work means useful parallel tasks, not every
specialist running continuously.

Retain the user's current permitted model pool and exclusions: no Haiku; do not
wait for unavailable Fable credits. Use available authorized models without new
probes or identity-diversity gates. Routine editorial disagreements are resolved
by the integrator with a short reason. If a genuinely consequential judgment
needs a vote, retain the user's weighting rule, limit it to one round, and return
an unresolved substantive question to the user. Never vote on numerical truth.

### 2. Review the actual manuscript, with bounded revision loops

For the first complete draft, run these two reviews in parallel:

* `scientific-reviewer`, explicitly in **manuscript-only mode**: does the text
  accurately express the accepted findings, explain the methods, acknowledge
  limits, and distinguish the extension from the companion? No results audit.
* `narrative-reviewer`: argument, section order, transitions, clarity, proportion
  of detail, accessible explanations and absence of repetitive table recitation.

The lead writer makes one consolidated revision. Reviewers then check only the
changed passages and unresolved findings, not the entire preparation record.
Allow at most **two review/revision rounds for the complete manuscript**. After
that, return any material disagreement in the handoff rather than opening a new
panel or testing programme. Optional section reviews during drafting must be
targeted and must not create their own nested consensus loops.

Use `clean-scientific-writer` for one final language pass if needed, followed by
`academic-prose-auditor` only for remaining sentence-level issues. The existing
`no-ai-slop/ACADEMIC_ADAPTER.md` is Detect-only. Preserve scientific qualifications,
citations and technical terms. Do not invoke every overlapping prose skill on
every section, and do not claim that a style check detects whether AI wrote text.

### 3. Deliver an Overleaf-ready writing package

Produce the new manuscript, supplement, bibliography, referenced figures/tables
and a brief handoff under this writing directory. Reuse existing assets. Any
necessary figure reformatting must preserve accepted data and stay presentation-
only; no new analytical display that requires recomputing the study.

Perform lightweight document checks: referenced files exist; labels and citations
resolve; inserted values/units match the accepted source; no private site codes
appear in new text or figures; the file package has no missing dependencies.
Use available existing checks where they directly help, or inspect manually.
Do not develop a new static checker, exporter or validation framework. Do not
claim a successful PDF compilation; the user compiles on Overleaf.

Keep the companion, evidence inputs, solver code and campaign artifacts unchanged.
No git writes, installations, external uploads or journal contact. Keep only a
short progress log, unresolved author questions and a truthful AI-use record.

The final handoff must say what was written, what specialist reviews changed,
what remains for author confirmation, and that the results were **reused, not
revalidated during writing**. The user and original assistant will examine the
finished article together before the final scientific/submission decision.

**Next response from the writing agent:** acknowledge the scope change, name the
first substantive sections being produced, and start those sections. Do not
return another multi-day preparation plan or a fresh dispatch-budget exercise.
