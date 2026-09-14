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

User decisions made after the go are recorded in `reports/horizon_robustness_results/writing/governance/user_decisions.md`: U5, U6, U7 and U8. U8 means no git commands of any kind.

# Brief: P1 code review of the evidence checkers and the carry-over checker fixes (INV-13)

**Identity:** `code-reviewer`/opus, role `code_review`. You are read-only and static: return everything in your reply. The author was `general-purpose`/sonnet (the P1 check-author dispatch).

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. `W` = `reports/horizon_robustness_results/writing`; `L` = `.unlazy/horizon-writing`.

## Specification

- `W/governance/prompts/P1-check-author.md` (Parts A and B)
- `W/evidence/ANCHOR_SPEC.md` and `W/evidence/DOCUMENT_VALUES_SPEC.md`
- Plan: P1, INV-3, INV-5, INV-11, INV-13, Appendix D
- For Part B:
  - `W/governance/results/P0-024-code-rereview3-narrow.md` (N7 to N10);
  - `W/governance/findings.jsonl` (F-040, F-042, F-043, F-044);
  - `W/governance/user_decisions.md` U8;
  - `W/governance/GOVERNANCE_FORMATS.md` §20.

## Under review

- `W/tools/compare_anchors.py`
- `W/tools/check_claims.py`
- `L/fixtures/compare_anchors/**`
- `L/fixtures/check_claims/**`
- Part B changes in `W/tools/check_governance.py`, `L/fixtures/check_governance/run_all.py` and the new `check_governance` fixtures
- The check-author report `W/governance/results/P1-*-check-author.md`, and ORCH's recorded runs `L/gate_outputs/p1checks_*.txt`

## Questions

1. **Spec conformance.** Does each mode implement the specification exactly? The modes are default, `--documents`, `--schema`, `--coverage` and `--argument`.
2. **Vacuous passes.** Which checks can pass without checking anything? Look at zero keys, zero claims, empty lists, and patterns that expand to nothing.
3. **Numeric tokens in `check_claims`.**
   - Do the exemptions hide real numbers?
   - Can a wrong number pass through rounding tolerance or through unit confusion (pct versus pp versus share)?
4. **Section E cross-check in `compare_anchors`.** Can a mismatch pass without a closed Q-card and an errata entry?
5. **Fixtures.** Does each fixture fail, or pass, for its stated reason? Does `run_all.py` cover every Part A and Part B fixture?
6. **Safety.** Confirm that `compare_anchors.py` and `check_claims.py` write nothing and start no subprocess.
7. **Part B.** Answer FIXED or NOT FIXED, with `file:line`, for each finding:
   - F-040: the waiver path location check;
   - F-042: no bytecode written under W, and the suite's own check for it is not vacuous;
   - F-043: the scanner no longer exempts itself, catches command-string git calls, and the proof fires on them;
   - F-044: a non-integer round gives a violation and no crash.
8. **U8.** Confirm that no file under `L/fixtures/` and no tool under `W/tools/` can execute git, other than the existing read-only status call in `check_governance.py`.
9. **Regressions.** Did anything regress in `check_governance.py` rules confirmed in seq 20 and seq 24?

## ORCH findings and cards to address

ORCH verified the following against the code before this review. For each one, confirm it, extend it or reject it, with evidence.

**Findings** (`W/governance/findings.jsonl`):
- **F-045 (MAJOR).** `local_restriction` removes backtick fragments before it matches the `for` clause, so backticked restriction values vanish. `extract_key_patterns` then treats those same values as independent keys. On the unedited spec, section B demanded the bogus keys `n_half`, `n_P` and `n_2P` and no `disp.explor.*` key. Section C demanded `d01`, `d02` and `d03` and no two-sided pass-count key.
- **F-046 (MAJOR).** A placeholder with an empty domain expands to zero keys, and no problem is reported (`compare_anchors.py:180-183`).
- **F-047 (MAJOR).** `check_tail_unused` accepts both tail formulas. Under Q-013, it must accept only the formula that matches the merged `prov.stream_end` `semantics`.

**Cards:**
- **Q-012 (resolved).** Arm scope. ORCH edited `ANCHOR_SPEC.md` so that every `<ARM>` row carries a plain per-row arm list, and split the two-sided pass-count row by δ. Check that the parser expands the edited spec to the intended keys: section A 147, section B 20, section C 27, section D 9.
- **Q-013 (resolved).** The tail-semantics field in `DOCUMENT_VALUES_SPEC.md`.
- **Q-014 (open, Class J).** Root-marker scope. As the non-ORCH confirmer that plan §4.2 requires, confirm or reorder the option ordering from most to least conservative, and state your choice.

A `VERDICT: PASS` from you is required before ORCH registers the two new scripts in `check_scripts.json` and records P1:G1 to P1:G5.

## Return in reply (at most 800 words)

```
VERDICT: PASS | REVISE
## Part A findings  (severity; file:line; claim; evidence; fix)
## Part B fix confirmation (F-040, F-042, F-043, F-044)
## U8 git ban
## Required changes for the author fix round
```
