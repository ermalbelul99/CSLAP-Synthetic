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

User decisions made after the go are recorded in `reports/horizon_robustness_results/writing/governance/user_decisions.md`: U5, U6, U7 and **U8**. U8 bans git writes of every kind.

# Brief: P0 targeted fix round 3 on the governance checkers (user decision U8)

**Identity:** `general-purpose`/sonnet, role `check_author`. You wrote these scripts in seq 5, 16 and 19. `code-reviewer`/opus reviewed them in seq 6, 17 and 20, and will narrowly re-review this round.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. `W` = `reports/horizon_robustness_results/writing`; `L` = `.unlazy/horizon-writing`.

**Allowed outputs.** Write nothing else.
- `W/tools/check_governance.py`
- `W/tools/check_inputs.py`
- `L/fixtures/check_governance/**`
- `L/fixtures/check_inputs/**`

## Git ban (user decision U8, absolute)

- **You run no git command of any kind**: not `status`, `log`, `init`, `add`, `commit` or `config`, and not with `-C`.
- **No fixture, runner or helper you write may execute git.**
- **The one git call allowed** is the existing read-only call inside `check_governance.py` (`git --no-optional-locks status`, used by `--snapshot`/`--compare`). It stays as it is, and fixtures reach it only through the normal CLI.
- **If a step would need git, stop** and return a Q-card instead.

## Read

1. `W/governance/results/P0-020-code-rereview2-checks.md`, the seq 20 review (VERDICT: REVISE), with defects N1 to N6.
2. `W/governance/findings.jsonl`: the latest line for each of F-036 to F-041 (F-036 = N1, F-037 = N2, F-038 = N3, F-039 = N4, F-040 = N5, F-041 = N6).
3. `W/governance/user_decisions.md`, section U8.
4. `W/governance/GOVERNANCE_FORMATS.md` §3, §19 and §20.
5. The current `W/tools/check_governance.py`, `W/tools/check_inputs.py`, `L/fixtures/check_governance/run_all.py`, `L/fixtures/check_governance/compare_tracked_outside_edited_twice/run_fixture.py` and `L/fixtures/check_governance/snapshot_change/run_snapshot_fixture.py`.

## Required changes

Add a short comment naming the finding at each change.

1. **F-036 (N1) under U8: make the second-edit fixture git-free.** Rewrite `compare_tracked_outside_edited_twice/run_fixture.py` so that it runs no git at all.
   - Load `check_governance.py` as a module with `importlib.util.spec_from_file_location`.
   - Replace its git-status function (the one `compute_snapshot` uses) with a stub. The stub returns a successful porcelain listing that contains ` M outside.txt`.
   - Build the tree under `L/fixtures/check_governance/_work/run-<id>/`. Edit `outside.txt` once, call the module's snapshot entry point, edit it a second time, then call the compare entry point.
   - Assert `SNAPSHOT CHANGED` with a `CHANGED outside.txt` diff. Delete the work directory in `finally`.
   - Exit non-zero at the first failed step.
   - Then make `run_all.py` fail, with a clear line, if any `.py` file under `L/fixtures/` contains a subprocess argument list that invokes git. Match `["git"`, `'git',` and `"git",` in argument lists, and state the heuristic in a comment.
2. **F-038 (N3).** In `check_weighted_votes()`, add two violations:
   - an outcome sub-question with no valid ballot carrying a position for it;
   - a DR to which the weighted rule applies (a seat at or above `u7_from_seq`) whose ballots include no valid one.

   The exemption stays: skip the check when that sub-question's `rule` (or the DR's `rule`, for a single question) starts with runoff, conservative_default, fallback or orch_pick. DR-001 on the real root must still pass.
3. **F-037 (N2).** The `compare_match` and `snapshot_file_tampered` fixtures must not leave receipts in their fixture trees.
   - Run their snapshot/compare on a copy under `_work/`, deleted afterwards, through a small runner if needed.
   - Remove any `*.compare.json` receipt already left inside those two fixture trees.
4. **F-039 (N4).** A ballot with no `round` field uses the same default (1) when the final round is chosen and when the tally is computed.
5. **F-040 (N5).** A gate record's `output_file` must normalize to a path under `.unlazy/horizon-writing/gate_outputs/`, with no `..` segment. Otherwise report a `VIOLATION (phase)` naming the gate. The stem fallback is unchanged.
6. **F-041 (N6).** In `check_inputs.py`, any count that is not an integer prints `MANIFEST COUNTS MISSING <group>` and fails the run. This covers null, strings and booleans.

## Fixtures

Each fixture gets `meta.json` and a byte-exact `expected.txt`, or a runner with explicit assertions. `run_all.py` covers all of them and reports the new count.

- `batched_outcome_key_without_ballots`: an outcome key with no matching ballot position. Must fail.
- `weighted_no_valid_ballots_post_u7`: must fail.
- `ballot_missing_round`: a single-question DR subject to U7 whose final-round ballots omit `round`. The tally must count them, and the fixture must pass.
- `output_file_outside_gate_outputs`: must fail.
- `check_inputs/counts_null`: must fail.
- The rewritten git-free `compare_tracked_outside_edited_twice`: must still detect the second edit.
- The `run_all.py` no-git scan, together with a proof that the scan fires. Build a throwaway `.py` under `_work/` that contains a git argument list, show that the scan flags it, then delete it. The throwaway file is never executed.

## Runs (only these)

- `L/fixtures/check_governance/run_all.py`.
- On the real root, read-only modes:
  - `check_inputs.py`;
  - `check_governance.py --allow-pending`;
  - `check_governance.py --phase P0`;
  - `check_governance.py --probe`.
- Never use `--snapshot` or `--compare` on the real root.
- Run no git command, repository test, solver, survey script or data loader.

**Expected `--phase P0` violations on the real root**, all of them ORCH's open work: F-036 and F-038 fix confirmations, the P0:G4 code-reviewer PASS evidence, and the P0:G6 record.

## Return in reply (at most 600 words)

- **Files changed**, including removed receipts.
- **Changes 1-6:** `file:line` for each.
- **Fixtures:** the added fixtures and the `run_all.py` result line.
- **Git ban:** a statement that no git command was run and that the no-git scan reports clean, with its output line.
- **Real-root outputs**, verbatim: the last two lines of `check_inputs.py`, `--allow-pending`, the full `--phase P0` violation list, and `--probe`.
- **Q-cards**, if any.
