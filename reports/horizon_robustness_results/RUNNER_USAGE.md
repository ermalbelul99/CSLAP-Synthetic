# Runner handoff (implementation only)

No empirical campaign is authorized or started by this document. The user's latest instruction is to finish the current implementation leftovers and report, then stop before further study execution.

## Interfaces

Use the existing CPLEX Python environment for orchestration. It launches the selected backend through that backend's own licensed interpreter. No Node installation, environment activation, package installation or secret copying is required.

Read-only command:

```powershell
& 'C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe' -m Baselines.horizon_robustness.runner quote --stage pilot
```

The default pilot selects seed1001 from the 50-, 500- and 2000-product families and BERNER; first origin, n=P, seed11, NOM/HIST+ACT, Hexaly, one thread. The selector `BERNER` explicitly maps to the article adapter's internal catalogue ID `berner`. Larger stages are explicit: `screen`, `core`, or a named one-axis `sensitivity`. `--datasets` chooses an explicit subset of the approved 29 instances plus BERNER. A sensitivity invocation specifies one parameter value and one named axis; it never constructs an implicit Cartesian grid.

`--rule two_sided` (added 12 September 2026 for exploratory revision 2) quotes the two-sided rule with floors `max(0, b_s - delta)` beside the ceilings; the primary two-sided delta is `0.02` (`Protocol.two_sided_delta`). The default `upper_only` produces manifests byte-identical to those quoted before the option existed, because the rule is serialised and hashed only when two-sided.

`--stage holdout` (added 13 September 2026 for exploratory revision 3) quotes one explicit deployment origin per dataset: the end of the furthest future the first origin can score (first origin + 2P), which no solve, survey or re-scoring of the study has read. It accepts any subset of the approved seeds and, with `--horizons`, a subset of the protocol horizon grid; primary parameters are required as for a screen. The `horizons` key appears in a manifest's config only for this stage, so every earlier manifest still rebuilds byte-identically. The arm `HIST+ACT-T` (same revision) is HIST+ACT's uncertainty set optimised inside the tightened band delta*(1-lambda) on both sides, exactly as TIGHT tightens the nominal model; its scoring band is the declared one. The four upper-only arms' input and model hashes are unchanged.

Quote generation reads complete approved sources for catalogue/snapshot reconstruction but never optimizes. The quote pins source, catalogue, history, training, mathematical-model, runtime/package, implementation, warm-start, seed and resource identities. Do not reuse a quote after editing implementation or data. Regenerate it before approving a campaign. The original planning documents remain preserved; INDUSTRIAL_AMENDMENT_20260909.md controls industrial policy.

The `run` CLI requires the saved JSON manifest, `--approved-manifest-hash`, `--solver-budget-seconds`, and `--wall-cutoff-seconds`; an explicit `--output` must remain under `reports/horizon_robustness_results/campaigns`. No execution command is prescribed here because the pilot ceiling still needs confirmation. UTF-8 manifests with a PowerShell BOM are accepted. Existing complete artifacts are never replaced.

The CLI's `run` uses `supervised_run`: a watchdog encloses data loading, model preparation, native solves, validation and scoring. It enforces the overall wall cutoff and aggregate process-tree RSS ceiling, with a short bounded process-cleanup interval afterward. Each native attempt separately has a time allowance of native solver cap plus the quoted build allowance, truncated to the remaining campaign time. Defaults are 600 seconds additional per-attempt building allowance and 32 GiB aggregate RSS, explicitly visible in the quote. These defaults are engineering limits, not scientific parameters or approved campaign budgets.

The lower-level Python `run(...)` is used inside that supervisor and by fixtures. On its own, it checks the overall deadline between preparation/scoring phases; it is not a hard wall-clock supervisor. Use the CLI or `supervised_run(...)` for campaigns.

## Artifact layout

```text
campaign/
  manifest.json
  invocations/<id>.started.json, <id>.finished.json
  solves/<solve-key>/attempts/<primary-or-retry-id>/
    request.json       # frozen TrainingProblem/options; no future orders
    child.json         # PID + process creation time
    stdout.txt, stderr.txt
    native.json        # solver result + request/runtime attestation
    terminal.json     # native outcome, including failures
  cases/<case-id>.frozen.json
  cases/<case-id>.json
  cases/<case-id>/retries/<retry-id>.json
  supervision/<id>/request.json, child.json, result.json, terminal.json
```

The native solve key may be shared by several case IDs, but every case retains its own next-n-order evaluation and its original historical reference target. The complete layout certificate is durably published before selecting that future segment. Native input hashes are retained even when another case reuses the mathematically identical model. Diagnostic minimum-slack objectives do not replace the declared future ceilings.

Ordinary resume reuses complete successes AND failures. An interrupted scoring phase can finish from its saved allocation without a new solve. A deliberate retry requires both a distinct `--retry-id` and `--retry-reason`; old artifacts remain intact. Successful native results are reused for score-only retries. Parent kernel locks and PID/creation-time checks prevent duplicate live work. An interrupted launch with no reliable child identity fails closed and requires a manual process audit; a retry reason alone does not establish that an unknown old process has stopped. Corrupt final artifacts are not silently trusted or overwritten.

If the outer supervisor stops the campaign before some per-case records exist, its terminal record explicitly lists every quoted case with the saved outcome or a resource/error status. Those missing outcomes are not zero-performance observations. An interrupted supervisor/parent may leave a started record and partial files; these remain visible for audited recovery. Do not delete a campaign directory to conceal an unsuccessful attempt.

## Verification scope

Fixture checks cover policy/manifest tampering, file IPC, exact cache identities, per-horizon scoring, allocation-before-future order, independent rejection of invalid candidates, immutable resumption, deliberate retries, native errors, missing identities, process cleanup and memory/time limits. Four-product real CPLEX and Hexaly children verify the process boundary. A separate short-lived synthetic process-tree fixture checks actual Windows timeout cleanup. None is an industrial/benchmark robustness-performance experiment.
