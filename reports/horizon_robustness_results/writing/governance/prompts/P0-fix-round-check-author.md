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

User decisions after the go are recorded in `reports/horizon_robustness_results/writing/governance/user_decisions.md` (U5, U6).

# Brief: P0 author fix round for the governance checkers (BCL round 2)

**Identity:** general-purpose/sonnet, role `check_author`. You are the original author of both scripts.
**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`
**Abbreviations:** `W` = `reports/horizon_robustness_results/writing`, `L` = `.unlazy/horizon-writing`
**Python:** `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe`

## Read first

1. **Code review:** `W/governance/results/P0-006-code-review-checks.md`. Its "Required changes" 1–9 and findings F1–F12 are confirmed by ORCH; see `W/governance/findings.jsonl`, ids F-001..F-012.
2. **Decision:** `W/governance/decisions/DR-001.md`, the ADP-3 outcome on addenda A-001..A-004. The adopted text is in `W/governance/PLAN_ADDENDA.md`. Implement A-001 **as adopted there**, including any amendments. Where DR-001 differs from the draft `W/governance/questions/Q-010-addenda-draft.md`, DR-001 wins.
3. **Formats:** `W/governance/GOVERNANCE_FORMATS.md`, updated to v2 by ORCH, and `W/governance/required_gates.json`, the required-gate registry.
4. Your earlier brief, `W/governance/prompts/P0-005-check-author-inputs-governance.md`.

## Allowed outputs

- `W/tools/check_inputs.py`
- `W/tools/check_governance.py`
- `L/fixtures/check_inputs/**`
- `L/fixtures/check_governance/**`

Do **not** edit anything under `W/governance/`. The formats, registry and log utilities belong to ORCH. If they need changing, return a Q-card instead.

## Implement

1. **All code-review required changes (1–9).** In particular:
   - MET requires exit 0 and the token.
   - Replaced seats: honour the `replaced` role and `replaced_by_seq`.
   - Snapshots:
     - run git with `--no-optional-locks` and fail on a non-zero git exit;
     - hash every porcelain-listed path outside W and L;
     - document the gap for ignored paths in the docstring;
     - validate snapshot IDs, refuse to overwrite one, and refuse an empty snapshot;
     - write a `<ID>.compare.json` receipt.
   - Rule (h):
     - scan every event;
     - make the registry mandatory once any script exists under W/tools, W/math/tools or W/checks, with every such script registered by `kind`;
     - validate author and reviewer through the log;
     - normalise paths.
   - Key DRs and gates by file name, and flag duplicates.
   - Make fixtures honest (see item 5 below), and add `expected.txt` files with a runner.
   - Complete F8–F12, including manifest group counts and the manifest SHA-256 in `check_inputs`.
2. **A-001 items 1–9, as adopted:**
   - `--phase P#` with required-gate completeness from `required_gates.json`, where `self` gates are exempt and `closed_phases` is read from `state.json`;
   - the `waiver` validation, including the `allowed_paths` condition against the gate's recorded output file;
   - the `verdicts.jsonl` rule (the token must appear verbatim in `result_file`);
   - RTP records;
   - `evidence_refs` kinds DR, F, V, RTP and `FILE:`;
   - registry-driven `required_evidence`, including `any_of` and `min_count`;
   - `verification.by: "DR-###"`;
   - the mandatory check-script registry with `kind`;
   - addenda citing `DR:` or `U:`.
3. **The `--allow-pending` Q-card from the code review:** adopt the conservative default. `--allow-pending` also tolerates a CONFIRMED finding whose fix is not yet confirmed; without the flag it stays a violation.
4. **Keep existing behaviour and tokens:**
   - `INPUTS UNCHANGED (<n> files)`
   - `GOVERNANCE CONSISTENT`
   - `SNAPSHOT WRITTEN/MATCH/CHANGED <ID>`
   - `MODEL FAMILIES AVAILABLE`

   The default root stays `parents[4]`.
5. **Fixtures.** Every failing fixture must fail for exactly its stated reason; its `expected.txt` lists the exact VIOLATION lines. Provide `L/fixtures/check_governance/run_all.py`, which runs every fixture and asserts exit codes and expected lines. It prints `FIXTURES OK (<n>)` and exits 0, or `FIXTURES BROKEN` and exits 1.

   The pass fixture must exercise every rule, (a)–(i) plus `--phase`, waivers, verdicts, RTP, `any_of`, `replaced` seats and `second_chair`.

   Add failing fixtures for:
   - MET with a non-zero exit;
   - a replaced seat miscounted;
   - a missing required gate under `--phase`;
   - an invalid waiver (an extra file beyond `allowed_paths`);
   - a verdict token absent from its result file;
   - an unregistered check script;
   - a duplicate DR id;
   - an addendum without a DR or U line;
   - snapshot steps: an L write, ADDED, REMOVED, a second edit to a modified file.

## Run

Run only your scripts, on your fixtures and on the real root (both are read-only apart from snapshot files under `L/snapshots/`). Do **not** run `--snapshot` on the real root.

## Return in reply (at most 700 words)

- files changed;
- a mapping from each required change and each A-001 item to where it is implemented (`file:function`);
- the `run_all.py` output;
- the real-root result of `check_inputs.py`, and of `check_governance.py --allow-pending`, `--phase P0` and `--probe`, with their exit codes. P0 is not expected to pass until ORCH writes the remaining P0 records, so list the violations that are reported;
- any Q-cards.


## Adopted outcome of DR-001 (implement exactly this)

- **A-001 = b3.** Implement draft items 1-10, plus the following amendments.
  - **S1:** a `verification.by: "DR-###"` must name an ADP-3 DR.
  - **S3:** a waiver is valid only if all of these hold: `condition` is non-empty; `exit_code` equals the registry entry's `exit_code`; the output lines, ignoring empty lines, equal `exact_lines` exactly; and every gate in `requires_gates_met` is MET in the same run. Corrections are matched on (seq, event). Completed events carry `self_reported_model` as a string.
  - **R:** these rules take effect only after the code re-review of your fix round passes. Implement them now. ORCH will not record P0:G4 MET before the re-review verdict.
- **A-002 = b2.** The P9 protected-source waiver carries `requires_gates_met: ["P9:G1-inputs"]` (see `required_gates.json`).
- **A-003 = b.** For artifacts built by ORCH, `verification.by` and `fix_confirmed_by` must be a non-opus identity or an ADP-3 DR. They must never be `"ORCH"` or an opus identity. Enforce this under rules (a) and (b).
- **A-004 = a.** The registry already lists P0:G6 (manual), the per-script P8/P9 gates and both P0:G3 tokens.
- **Formats section 19.** Support batched positions, outcomes and rules as objects, and the seat `round_seqs` field for ballot identity. DR-001 itself uses both, and it must pass rule (d) after your fix.
