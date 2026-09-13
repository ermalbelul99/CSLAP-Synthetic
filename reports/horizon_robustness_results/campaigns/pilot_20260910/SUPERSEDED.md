# SUPERSEDED — pilot_20260910 (first attempt)

Status: **INVALIDATED FOR SCIENTIFIC USE. Preserved as an immutable failure record.**
Superseded by: `../pilot_20260910b/` (clean rerun of the same eight quoted solves).

## What happened

The campaign ran under approved manifest hash
`7878826ca850796a1a3e81f6606a22717726c7bf2c6bbe88744701a56f863b87`
(implementation hash `c17ef16e9900d5bbac77b57c85b094d0118b5ce9890e2e283e8b256c73072658`).

While it was executing, the driver created two new analysis-layer modules,
`analysis.py` and `rescoring.py`, **inside** `Baselines/horizon_robustness/`.
`runner.runtime_metadata()` derives the campaign implementation identity from a
SHA-256 over every `*.py` in that package directory. Adding those files changed
the identity, so from the next native launch onward each worker recomputed a
runtime that no longer matched its frozen request and refused to solve:

    ContractError: WORKER_INPUT_CHANGED: worker runtime/problem differs from quote

Outcome: 1 `COMPLETE`, 7 `PROCESS_ERROR`, 425.4 s elapsed, 6,840 native cap
seconds charged. The single completed case (`syn_50sku_seed1001`, arm NOM,
n=50) launched before the source change and is internally consistent, but it is
NOT used in any analysis table: the campaign as a whole is invalidated so that
no result is drawn from a run whose implementation identity was mutated
mid-flight.

## Assessment

This is an operator error, not a runner defect. The provenance guard behaved
exactly as specified: it failed closed instead of solving a model whose code
identity had drifted from the approved quote. Nothing was silently accepted.

## Corrections applied before the rerun

1. Analysis-layer code moved to `Baselines/horizon_robustness_analysis/`, which
   is outside the solve-path implementation hash. Editing a table or figure can
   no longer invalidate a frozen campaign manifest or block an ordinary resume.
2. `runner._diagnose()` now records a bounded stdout/stderr excerpt in an
   attempt's immutable `terminal.json` when no native result is returned. In
   this campaign the only trace of the cause was the raw `stderr.txt` file; a
   failure must be diagnosable from the JSON record alone. Covered by
   `tests/horizon_robustness/test_runner.py::RunnerTests::
   test_failed_child_keeps_a_bounded_log_excerpt_in_its_terminal_record`, with a
   negative control confirming the test fails when the fix is neutralised.

Because correction 2 edits `runner.py`, the implementation hash changed
deliberately and the manifest was regenerated for the rerun. This directory and
all of its artifacts are retained unchanged.
