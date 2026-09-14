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

# Brief: P0 check-author wave (plan P0 step 5; INV-2, INV-10, INV-11, INV-13)

**Identity:** `general-purpose`/sonnet, role `check_author`.
**Repository root:** `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`. Below, `W` = `reports/horizon_robustness_results/writing` and `L` = `.unlazy/horizon-writing`.
**Python:** `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe` (standard library plus jsonschema, numpy and pandas).

## Read first

1. `reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md`: §4.3, §4.4, §5 (INV-2, INV-10, INV-11, INV-13) and P0.
2. `W/governance/GOVERNANCE_FORMATS.md`: the record formats your checker parses. It is authoritative.
3. `W/governance/tools/make_manifest.py` (how the manifest was built) and `W/governance/source_manifest.json`. The manifest is large; inspect it with a short Python snippet, do not read it whole.
4. `W/governance/tools/log_dispatch.py` (how dispatch events are written) and `W/governance/state.json`.

## Allowed outputs (write nothing else)

- `W/tools/check_inputs.py`
- `W/tools/check_governance.py`
- `L/fixtures/check_inputs/**`
- `L/fixtures/check_governance/**`

## Script 1: `W/tools/check_inputs.py`

**Purpose.** Prove that every file pinned in `W/governance/source_manifest.json` is unchanged, and that no file has been added to a pinned group.

**CLI.** `check_inputs.py [--root DIR]`. The root defaults to the repository root, found from the script's location (`parents[3]`). The manifest is read from `<root>/reports/horizon_robustness_results/writing/governance/source_manifest.json`.

**Behaviour.**

1. Recompute SHA-256 for every manifest entry, in 1 MiB chunks. The pinned inputs total about 1.7 GB, so the check must finish in about a minute or less.
2. Re-enumerate every pinned group with exactly the rules of `make_manifest.py`, and report any file present on disk but absent from the manifest as `ADDED`:
   - `reports/horizon_robustness_results/**`, excluding `writing/`
   - root-level `*.tex` and `*.bib`
   - `manuscript_checks/**`, excluding `out/`
   - `tools/horizon_robustness/**`
   - `Baselines/horizon_robustness/**`
   - `Baselines/horizon_robustness_analysis/**`
   - `tests/horizon_robustness/**`
   - `.claude/agents/**`, `.claude/commands/**`, `.claude/skills/**`
   - `.unlazy/horizon-cslap/preserved_sources.json`
   - `__pycache__` and `*.pyc` are excluded everywhere.

   Re-implement these rules; do not import `make_manifest.py`. The check must stay independent of the tool it checks.
3. Print one line per problem: `MODIFIED <path>`, `MISSING <path>` or `ADDED <path>`.
4. Exit codes and final lines:
   - Success prints `INPUTS UNCHANGED (<n> files)` and exits 0.
   - Any problem prints `INPUTS CHANGED (<k> problems)` and exits 1.
   - A manifest with zero entries prints `INPUTS CHECK FAILED: empty manifest` and exits 1.
   - A missing or unparsable manifest exits 1 with a clear message.

## Script 2: `W/tools/check_governance.py`

**CLI.**

| Invocation | Purpose |
|---|---|
| `check_governance.py [--root DIR] [--allow-pending]` | Audit mode: rules (a)–(i) plus log integrity |
| `check_governance.py --snapshot ID [--root DIR]` | Write a snapshot |
| `check_governance.py --compare ID [--root DIR]` | Compare against a snapshot |
| `check_governance.py --probe [--root DIR]` | Check model-family availability |

`--root` defaults to the repository root (`parents[3]` of the script).

### Audit mode

Parse every record under `<root>/W/governance/` using `GOVERNANCE_FORMATS.md`. Apply the rules below. Print each violation as `VIOLATION (<rule>): <detail>`. Print `GOVERNANCE CONSISTENT` and exit 0 only when there are no violations; otherwise print `GOVERNANCE VIOLATIONS (<k>)` and exit 1.

- **Log integrity.**
  - The dispatch log must exist and contain at least one event; otherwise fail (zero-items rule).
  - Each `seq` must start with a `dispatched` event.
  - A `completed` event must name an existing `result_file`.
  - A `failed` event must carry a `failure_reason`.
  - Seqs dispatched with no terminal event are reported as `IN FLIGHT <seq>`. That is a violation unless `--allow-pending` is given.
- **(a) Findings** (`findings.jsonl`, latest line per id).
  - Every BLOCKING or MAJOR finding needs `verification.status` CONFIRMED or REJECTED. PENDING is allowed only with `--allow-pending`.
  - CONFIRMED needs a non-null `fix_confirmed_by`.
  - The verifier and the fix confirmer must not equal the `built_by` identity (same agent_type and family).
- **(b) ORCH self-rejection.** A finding with `built_by == "ORCH"`, `verification.status == "REJECTED"` and `verification.by == "ORCH"` is a violation.
- **(c) Unlogged participants.** Every identity object carrying a `seq` must match a dispatch-log seq whose latest event is `completed`, with the same agent_type and family. This covers findings (`raised_by`, `verification.by`, `fix_confirmed_by`), DR seats and DR ballots. `"ORCH"` is exempt.
- **(d) Decision records** (`decisions/DR-*.md`, leading fenced json block). Violations:
  - unparsable json;
  - empty `ballots` or `chair_checks`;
  - seat families (excluding `second_chair`) with fewer than 2 distinct values;
  - a seat whose `built` list intersects `artifacts_under_decision`;
  - a seat count, excluding `second_chair` and replaced voters, other than 3 for `ADP-3` or 5 for `ADP-5`. A missing panel means ADP-3.
- **(e) Gate records** (`gates/*.json`).
  - Non-MANUAL gates need an integer `exit_code`, a boolean `token_found`, a 64-hex `output_sha256`, and a `negative_control` that is either an object with a non-zero `exit_code` or a string starting with `EXEMPT:`.
  - MANUAL gates need a non-empty `evidence_refs`. Every ref must exist as a DR file (`DR-###`) or a finding id (`F-###`).
  - `status` must be MET or UNMET.
- **(f) Addenda.** Every `## A-###` heading in `PLAN_ADDENDA.md` needs a `DR: DR-###` line naming an existing DR file.
- **(g) Phase rules.** Every gate record for P3:G2, P5:G1, P5:G3, P8:G1 or P9:G2 with status MET must have a non-empty `evidence_refs`, and every referenced DR must itself pass rule (d).
- **(h) Check-script registry** (`check_scripts.json`; a missing file is allowed while empty). For each entry:
  - the reviewer's agent_type is `code-reviewer`;
  - the reviewer's family differs from the author's;
  - the author identity does not appear as a builder (`artifacts_built`) of any path in `checks_artifacts`, in any dispatch-log event.
- **(i) Path length.** Every file under `<root>/W` and `<root>/L` has an absolute path of at most 240 characters.

### Snapshot mode

`--snapshot ID` writes `<root>/L/snapshots/<ID>.json` containing:
- the SHA-256 of every file under `<root>/W` and `<root>/L`, excluding `<root>/L/snapshots/`;
- the output of `git -C <root> status --porcelain --untracked-files=all`, with lines for paths under W or L removed. If `<root>` is not a git repository, store `null` and a note.

It then prints `SNAPSHOT WRITTEN <ID>`. Note that `.unlazy/` is gitignored, so git status never shows it; W and L are already hashed directly.

`--compare ID` recomputes the same data. On a match it prints `SNAPSHOT MATCH <ID>` and exits 0. Otherwise it prints each `CHANGED|ADDED|REMOVED <path>`, a git-status difference if any, then `SNAPSHOT CHANGED <ID>`, and exits 1.

### Probe mode

`--probe` reads `state.json` `families`. If three or more have `status: available`, it prints `MODEL FAMILIES AVAILABLE (<n>: <names>)` and exits 0. Otherwise it prints `MODEL FAMILIES INSUFFICIENT (<n>)` and exits 1.

### Fixtures (negative controls, INV-11)

Build miniature repository trees under `L/fixtures/` that mirror the real relative layout (`reports/horizon_robustness_results/writing/governance/...`, `.unlazy/horizon-writing/...`).

**For `check_inputs`:**
- `pass/`: a tiny tree plus a manifest that matches it. Must exit 0.
- `modified/`: one byte changed. Must exit 1.
- `added/`: an extra file in a pinned group. Must exit 1.
- `empty/`: a manifest with zero entries. Must exit 1.

**For `check_governance`:**
- `pass/`: a minimal consistent governance tree. It contains one dispatched and completed probe, one confirmed finding with an independent verifier and a fix confirmer, one valid ADP-3 DR, one runnable gate record, and one MANUAL gate that references the DR. Must exit 0.
- `orch_self_rejection/`: rule (b). Must exit 1.
- `author_collision/`: rule (h). The script author is also the builder of a checked artifact. Must exit 1.
- `empty_log/`: zero-items rule. Must exit 1.
- `probe_two_families/`: `--probe` must exit 1.
- `snapshot_change/`: a documented two-step procedure. Run `--snapshot` on a copy, change one file, then `--compare`, which must exit 1. Provide `run_snapshot_fixture.py`, which does this inside a temporary copy under `L/fixtures/check_governance/_work/` and deletes it afterwards.

You may run your two scripts on your own fixtures, and `check_inputs.py` once on the real root (read-only), to confirm they behave as specified. Run nothing else.

## Return in reply (plain text, at most 600 words)

1. The files written.
2. The exact CLI and success tokens.
3. The fixture list with the exit code you observed for each.
4. The runtime of `check_inputs.py` on the real root, with its result line.
5. Any ambiguity in `GOVERNANCE_FORMATS.md`, as Q-cards.
