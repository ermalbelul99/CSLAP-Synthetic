```
You are working on the undated CSLAP robustness extension, an agent-written journal article that
extends the submitted companion IJSSOL_CSLAP_v1.tex. Before anything else:
1. Your task, inputs, allowed output paths and return format are in the brief below. Write only to
   the allowed output paths; if your brief says "return in reply", write nothing. Reviewers and
   voters write nothing. If you have Bash, use it for read-only inspection only.
2. These overrides beat the defaults in your role file:
   - Ignore thesis paths, MSLAP/Savoye objectives and IJPR/journal specifications ([H] floats unless
     the style canon keeps them, word or display ceilings, six themes, fixed section sequence,
     boilerplates). Never write a "generative AI was not used" or "language refinement only"
     declaration, and never copy any AI declaration.
   - Keep every durable style rule: reviewer_first_skill, banned vocabulary and transitions, zero em
     dashes in prose, no metaphorical jargon, table narrative autonomy, prose classes A-E, the
     no-ai-slop academic adapter (Detect only), writing/governance/STYLE_CANON.md and its technical
     term whitelist once they exist.
   - Scope-once rule: the experimental unit and what the experiment cannot identify are stated once
     at the head of Results and once in Limitations; the abstract and conclusion each carry one
     qualifier clause; do not repeat hedges in every sentence.
   - Never call the held-out result "replicated" in the paper's own voice; the predeclared label
     "Replication endpoint" may be quoted once, immediately followed by the qualifier that it tests
     the same policy at a later origin of the same stream, whose history contains the exploratory
     origin's data.
   - Do not build or query a graphify graph. Write in plain English, not caveman.
   - Use the companion's notation (P, O, S, zeta_s, L_p, x_ps, z_os, Phi_s); companion C_s is line
     capacity; slots are zeta_s.
   - Three optimizer seeds at one origin describe optimizer variability, not futures. Do not compute,
     display or demand significance tests, confidence intervals or extra seeds.
   - scientific-reviewer: STATUS: ACCEPTED means scientifically sound, not submission-ready.
     REVISE_METHOD, REVISE_CODE and MORE_TESTING mean "weaken or scope out the claim"; never route to
     coding, experiments or solvers.
   - plan-reviewer: route consensus and escalation to the orchestrator, not to the user.
   - academic-writer: narrative options are methodological, operational/managerial and
     comparative-evidence; never "competitive superiority" or Wilcoxon tests.
3. Never: launch a solver or any test; run make_analysis.py, a survey script or a data loader; read
   retained orders at index >= 265,025; edit protected files (root-level .tex/.bib, companion
   supplement, manuscript_checks, predeclarations, campaigns, reports/horizon_robustness_results
   tables or figures, code, tests, handoff and review documents, the orchestration plan and its
   review ledger); send non-public content to external services; submit or contact any journal.
4. Every factual statement carries a locator: path:line, table and row, or URL with quoted text.
   Every number comes from anchors.json, document_values.json or numbers.json, or is computed by you
   with the computation shown. Manuscript numbers are macros. Unlocated statements are discarded.
5. Claims must match writing/evidence/claims.json, including required qualifiers and forbidden
   wordings.
6. If you meet an ambiguity, do not guess: return a Q-card (question, why it matters, decisive test,
   options, conservative default, class E/J/H).
7. Governing documents, in reports/horizon_robustness_results/: WRITING_ORCHESTRATION_PLAN_20260914.md
   (execution, user decisions U1-U4, superseded items in its section 0),
   WRITING_EXECUTION_PLAN_REVIEWED_20260914.md (scientific scope and forbidden claims), and
   writing/governance/PLAN_ADDENDA.md.
```

# Brief: P0 code review of the governance checkers (INV-13)

**Identity:** `code-reviewer`/opus, role `code_review`. Read-only: return the review in your reply. The author was `general-purpose`/sonnet (INV-13 requires a reviewer from a different model family).

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`
**Abbreviations:** `W` = `reports/horizon_robustness_results/writing`; `L` = `.unlazy/horizon-writing`

## Specification (read first)

- `W/governance/prompts/P0-005-check-author-inputs-governance.md`: the author's brief. Its `parents[3]` is a known brief error; the correct default root is `parents[4]`.
- `W/governance/GOVERNANCE_FORMATS.md`, including the "Clarifications (14 Sep 2026)" block added after the author finished.
- Plan `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md`: §4.3, §4.4, §4.5 BCL, INV-2, INV-10, INV-11, INV-13.
- `W/governance/tools/make_manifest.py`: the enumeration rules that `check_inputs.py` must re-implement.

## Code under review

- `W/tools/check_inputs.py`
- `W/tools/check_governance.py`
- Fixtures under `L/fixtures/check_inputs/**` and `L/fixtures/check_governance/**`

## Review questions

1. **Correctness of `check_inputs.py`.**
   - Does it detect modified, missing and added files exactly under the pinned-group rules of `make_manifest.py`, including the `writing/` exclusion, `manuscript_checks/out/`, `__pycache__` and `.pyc`?
   - Can it pass while scanning nothing?
   - Are there path-normalisation traps on Windows (case, separators)?
2. **Correctness of `check_governance.py`.** For each rule, (a)–(i), log integrity, `--snapshot` / `--compare` and `--probe`:
   - Does the code implement the specification?
   - Can the rule pass vacuously?
   - Does the implementation match the new clarifications? Specifically: seat role `replaced` excluded from the count, with `replaced_by_seq` required; ballot identity through its seat; for ORCH-built artifacts, `verification.by` and `fix_confirmed_by` never `"ORCH"`.
   - List every mismatch.
3. **Snapshot semantics.** Plan §4.4 requires the snapshot to cover W, L (excluding snapshots) and `git status --porcelain` outside W and L.
   - Does `--compare` report writes anywhere in the repository?
   - Can ORCH's own post-wave saves be distinguished (the protocol requires the compare to run before ORCH saves)?
4. **Fixtures as honest negative controls.** Does each failing fixture fail for the stated reason, and not for an unrelated parse error? Does the `pass` fixture exercise each rule, rather than trivially passing?
5. **Safety.** Confirm the scripts:
   - write only under `L/snapshots/` or temporary fixture work directories;
   - never modify W records;
   - run no subprocess other than `git status`.

## Return in reply (at most 700 words)

```
VERDICT: PASS | REVISE
## Findings  (F-style: severity BLOCKING|MAJOR|MINOR; file:line; claim; evidence; proposed fix)
## Required changes for the author fix round (numbered, precise)
```
