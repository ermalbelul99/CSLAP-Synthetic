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

User decisions made after the go are recorded in `reports/horizon_robustness_results/writing/governance/user_decisions.md`:
- U5: IJSSOL v1 is the only baseline.
- U6: its supplement is part of that baseline.
- U7: votes are weighted (opus 2, fable 2, sonnet 1), haiku is excluded from every role, and fable is retried no sooner than 12 h after a failure.

# Brief: P0 targeted fix round 2 on the governance checkers

**Identity:** `general-purpose`/sonnet, role `check_author`. You wrote these scripts in seq 5 and revised them in seq 16. `code-reviewer`/opus reviewed them in seq 6 and seq 17 and will re-review this round.

**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. `W` = `reports/horizon_robustness_results/writing`; `L` = `.unlazy/horizon-writing`.

**Allowed outputs.** Write nothing else. Bash is allowed, but only for the runs listed under "Runs".
- `W/tools/check_governance.py`
- `W/tools/check_inputs.py`
- `L/fixtures/check_governance/**`
- `L/fixtures/check_inputs/**`

## Read

1. **The review.** `W/governance/results/P0-017-code-rereview-checks.md` (seq 17, VERDICT: REVISE). Its line references are to the seq 16 version of the code, which is the current file.
2. **The findings.** `W/governance/findings.jsonl`: the latest line for each of F-022 to F-030 and F-035. All are CONFIRMED by ORCH.
3. **The formats.** `W/governance/GOVERNANCE_FORMATS.md`, in particular:
   - §2, including the new "Fix confirmer role" paragraph;
   - §4, §9–§11, §13, §19, §20.
4. **The resolved Q-card.** `W/governance/questions/Q-011.md`, resolution (a).
5. **Registry and decisions.** `W/governance/required_gates.json` (P0:G4 now carries `required_evidence`); `W/governance/PLAN_ADDENDA.md` A-001; `W/governance/user_decisions.md` U7.
6. **Current code and fixtures.** `W/tools/check_governance.py`, `W/tools/check_inputs.py`, `L/fixtures/**`, `L/fixtures/check_governance/run_all.py`.

## Required changes

For each change, keep the existing violation-message style and add a short comment naming the finding.

1. **F-022 (D1).** `--compare` validates the ID with `ID_RE` and requires `<root>/W/governance` to exist before any read of the snapshot or any write. A failure prints `COMPARE FAILED: <reason>`, exits 1 and writes nothing.
2. **F-023 (D2, Q-011 a).** A `fix_confirmed_by` identity is valid when its dispatch-log role is `critic` or `code_review`.
   - The role check for `verification.by` (`confirmer`) is unchanged.
   - The A-003 family rules are unchanged.
   - `check_participant()` takes a set of allowed roles.
3. **F-024 (D3).** In `--phase P#`:
   - Only the self gate of the target phase P# is exempt from needing a record. Self gates of earlier phases need records like any other gate.
   - The target phase's self gate must still resolve its `required_evidence`.
   - A manual gate passes only if its record has `status` MET and every `required_evidence` item resolves.
   - In the audit without `--phase` (closed phases), no self gate is exempt.
4. **F-025 (D4).** A verdict is valid only if all of the following hold:
   - `token` is a non-empty string;
   - `result_file` equals the `result_file` of the completed dispatch-log event for that `seq`;
   - that file contains `token` verbatim.

   A malformed verdict is a violation and never a crash.
5. **F-026 (D5).** VERDICT evidence counts only verdicts whose `phase` equals the phase of the gate being checked, unless the evidence item names an explicit `phase`.
6. **F-027 (D6).** Weighted votes:
   - **Where weights come from.** Take weights from `state.json` `vote_weights`. If a DR carries `weights`, each entry must equal the state value. A seated family with no state weight is a violation, and there is no default of 1.
   - **Final round.** For each sub-question, the final round is the highest round among valid ballots that carry a position for that sub-question.
   - **When the rule applies.** A DR must carry `weights` and `weighted_tally` when any seat `seq` or `round_seqs` value is at or above `state.json` `u7_from_seq`. The strict-majority check then runs, except where that sub-question's `rule` starts with runoff, conservative_default, fallback or orch_pick.
   - **DR-001.** Remove the DR-001 name exemption. DR-001 must still pass on the real root, because its seats all predate `u7_from_seq`.
7. **F-028 (D7, formats §20).**
   - A gate's output text is read from the record's `output_file` when present, else from `L/gate_outputs/<stem>.txt`.
   - `output_sha256` must equal the SHA-256 of that file, on the MET path and on the waiver path.
   - A mismatch is a violation on both paths.
8. **F-029 (D8a).** `--snapshot` prints two lines:
   - `SNAPSHOT CONTENT SHA256 <digest>`, the digest stored in the file's `snapshot_sha256`, computed over the snapshot without that field;
   - `SNAPSHOT FILE SHA256 <digest>`, the SHA-256 of the written file.

   Document both in the docstring. `--compare` also recomputes the stored content digest, and reports `SNAPSHOT CHANGED` with the diff `snapshot file tampered` if the digest does not match.
9. **F-030 (D8c), `check_inputs.py`.** If the manifest has no `counts` object, or lacks a count for any group in `GROUP_NAMES`:
   - print `MANIFEST COUNTS MISSING <group or all>`;
   - exit 1.

   Run the real root once. If the real manifest lacks counts, do not weaken the rule; return a Q-card instead.
10. **F-035.** Correct the module docstring:
    - `.unlazy/horizon-writing/` is gitignored as a whole, through `.unlazy/.gitignore`, and so is `W/tools/__pycache__/`;
    - detection is unaffected, because W and L are hashed directly;
    - the residual gap is limited to gitignored, untracked files outside W and L.

## Fixtures

Each fixture gets `meta.json` and a byte-exact `expected.txt`. `run_all.py` must cover all of them and report the new count.

**Add:**
1. `compare_bad_id`: `--compare ../x` fails and writes nothing. The runner checks that no file was created.
2. `compare_match`: a snapshot, then a compare with no change, gives `SNAPSHOT MATCH`.
3. `compare_tracked_outside_edited_twice`: a procedural runner that builds a temporary git repository.
   - Location: under `L/fixtures/check_governance/_work/` only. It deletes that repository at the end.
   - Git runs only inside that temporary repository, with `-c user.name=fixture -c user.email=fixture@invalid`. Never run git against the project repository except read-only `status`.
   - Sequence: take a snapshot, edit an already-modified tracked file outside W and L a second time, then compare. The expected result is `SNAPSHOT CHANGED`.
4. `snapshot_file_tampered`: a stored snapshot whose content no longer matches `snapshot_sha256` gives `SNAPSHOT CHANGED`.
5. `weight_mismatch`: a DR `weights` entry differs from `vote_weights`.
6. `weights_missing_post_u7`: a DR with a seat at or above `u7_from_seq` and no `weights`.
7. `batched_early_settled_pass`: a batched DR with a sub-question settled only in round 1 and weights present. It must pass.
8. `probe_fable_retry_past`: fable `retry_after` is in the past, so fable counts as available.
9. `manual_gate_unmet`: a manual gate recorded UNMET whose evidence resolves. It must fail.
10. `self_gate_earlier_phase_missing`: `--phase P1` with no P0 self-gate record. It must fail.
11. `self_gate_evidence_unresolved`: `--phase P0` where the P0 self gate's `required_evidence` does not resolve. It must fail.
12. `verdict_unrelated_file`: a verdict whose `result_file` exists and contains the token but differs from the dispatch log's `result_file`.
13. `verdict_null_token`: fails with a violation and no traceback.
14. `verdict_wrong_phase`: VERDICT evidence satisfied only by a verdict from another phase. It must fail.
15. `output_file_differs_from_stem_pass`, and `output_file_hash_mismatch` (the latter must fail).
16. `waiver_hash_mismatch`: a waiver whose stored output lines are right but whose `output_sha256` does not match. It must fail.
17. `fix_confirmer_code_review_pass`, and `fix_confirmer_wrong_role`, where the confirmer's dispatch role is `builder` (must fail).
18. In `L/fixtures/check_inputs/`: `counts_missing`.

**Extend `pass`** so that it exercises all of the following:
- `round_seqs` and batched positions;
- weights;
- an `output_file` that differs from the stem;
- `FILE:` and `V-` references;
- `closed_phases`;
- a finding fix-confirmed by a `code_review` dispatch.

## Runs

These are the only runs allowed:
- `L/fixtures/check_governance/run_all.py`, and any check_inputs fixture runner it calls.
- On the real root, read-only modes only:
  - `check_inputs.py`;
  - `check_governance.py --allow-pending`;
  - `check_governance.py --phase P0`;
  - `check_governance.py --probe`.

Never use `--snapshot` or `--compare` on the real root. Run no repository tests, solvers, survey scripts or data loaders.

**Expected on the real root.** `--phase P0` should still show violations that are ORCH's open work, not checker defects. Report them verbatim, and flag any you think is a checker defect. The expected ones are:
- the missing `P0:G6` record;
- the P0:G4 code-reviewer VERDICT evidence, unresolved until the next re-review;
- the pending findings F-022 to F-035.

## Return in reply (at most 700 words)

- **Files changed.**
- **Where each change landed.** For each of changes 1 to 10: `file:line`.
- **Fixtures.** The list of added fixtures, and the `run_all.py` result line (for example `FIXTURES OK (N)`).
- **Real-root output, verbatim:**
  - `check_inputs.py`: the last two lines;
  - `--allow-pending`: the output;
  - `--phase P0`: the full violation list;
  - `--probe`: the output.
- **Q-cards,** if any.
