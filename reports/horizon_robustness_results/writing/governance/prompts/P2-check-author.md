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

# Brief: P2 check-author, `check_sources.py` (INV-11, INV-13)

**Identity:** `general-purpose`/sonnet, role `check_author` (U7 excludes haiku). Your code reviewer will be `code-reviewer`/opus.

**Paths.**
- Root: `C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic`.
- `W` = `reports/horizon_robustness_results/writing`.
- `L` = `.unlazy/horizon-writing`.
- Python: `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe`.

**Allowed outputs.** `W/tools/check_sources.py` and `L/fixtures/check_sources/**`.

**Spec.** Plan P2 and Appendix D (`source_register.json` entry). The default root is `Path(__file__).resolve().parents[4]`; verify it with `git rev-parse --show-toplevel`. `--root DIR` overrides it.

## Default mode

Validate `W/literature/source_register.json` (a list, or `{"sources": [...]}`) with jsonschema against Appendix D:
- `class` is one of literature, own_submitted, software;
- `access` is one of FULL_TEXT, ABSTRACT_ONLY, UNRESOLVED, LOCAL;
- `citation_level` is one of full, existence, none;
- `found_by` is one of A, B, both, ORCH;
- `dimensions` carries all seven keys.

Then enforce the consistency rules:

| Entry type | Required |
|---|---|
| `access: FULL_TEXT` | `citation_level: full` |
| `access: ABSTRACT_ONLY` | `citation_level: existence` |
| `access: UNRESOLVED` | `citation_level: none` |
| `class: literature` | `doi` or `verification_url`, plus `metadata_verified: true` unless `access` is UNRESOLVED |
| `class: own_submitted` | `local_sha256` matching the current bytes of the named local file, and `access: LOCAL` |
| `class: software` | `verification_url` |

Also:
- `W/literature/comparison_matrix.md` must exist.
- Every register `id` cited in that matrix must exist with `access` other than UNRESOLVED.
- Every matrix row must carry at least one locator, i.e. text in square brackets or a `§`/`eq.`/`p.` token.
- There must be at least 8 matrix rows.
- There must be at least one register entry.

Output: `SOURCE REGISTER VALID (<n> sources, <m> matrix rows)` and exit 0, or the problems and exit 1.

## `--anchors` mode

Three anchors must be present, matched by DOI, case-insensitive:
- `10.1007/s10696-024-09549-7`
- `10.17093/alphanumeric.1670030`
- `10.1016/S0169-2070(00)00065-0`

Each must satisfy one of:
- `access: FULL_TEXT`, with locators that cover the required sections. For Winkelmann these are tokens `5.2` and `5.4`.
- A named open item in `W/literature/retrieval_requests.md` that mentions the DOI.

Output: `ANCHORS ACCOUNTED (3)` and exit 0; otherwise exit 1.

## Fixtures

Create:
- `pass/`
- `bad_citation_level/`
- `unresolved_in_matrix/`
- `own_submitted_hash_mismatch/`
- `anchor_missing/`, which must fail under `--anchors`

Run your script on your own fixtures only.

**Return in reply** (at most 400 words): the files written, the CLI and tokens, the fixture exit codes you observed, and any Q-cards.
