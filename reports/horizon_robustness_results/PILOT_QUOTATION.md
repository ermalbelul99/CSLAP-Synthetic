# Engineering pilot quotation — not yet authorized to run

The direct read-only inventory check confirms all four proposed pilot datasets are eligible. No solver was imported or called by that check. The implemented runner's independent dry quote subsequently reproduced all rows and the 6,840-second total; source loading and quote preparation took 166.203 seconds in that diagnostic invocation. No empirical solver was called. Regenerate a frozen manifest from the final implementation before approving execution; the diagnostic quote is not campaign authorization.

| Dataset | Full products | Complete orders | Historical origin (count) | Future n | Solves | Per-solve limit |
|---|---:|---:|---:|---:|---:|---:|
| syn_50sku_seed1001 | 50 | 2,482 | 1,737 | 50 | 2 | 120 s |
| syn_500sku_seed1001 | 500 | 24,044 | 16,830 | 500 | 2 | 300 s |
| syn_2000sku_seed1001 | 2,000 | 67,637 | 47,345 | 2,000 | 2 | 1,200 s |
| BERNER, complete retained system | 21,874 | 284,862 | 199,403 | 21,874 | 2 | 1,800 s |

Methods: NOM and HIST+ACT. Seed: 11. One thread. Primary backend: Hexaly. delta=0.01, nu=0.01; these are separate absolute share and activation-mass parameters. No parameter is selected from future outcomes. The pilot's purpose is model construction, process/evaluator integration, memory and runtime assessment, not a final empirical verdict.

Maximum configured native solver time: 6,840 seconds = 1.9 hours over eight solves. Building, validation, data preparation and reporting add wall time. The pending user question proposes a three-hour overall campaign cutoff, including building. Hitting that cutoff must leave explicit uncompleted/resource-limited records, not dropped cases or silently longer execution. The runner must quote its precise watchdog and memory configuration as well.

Authorization remains pending. The user's latest instruction is to finish current implementation leftovers, report completed work and remaining tasks, and stop before subsequent execution. No benchmark or industrial optimization has started. Only source audits and tiny software/solver correctness fixtures have run. Current runner defaults quote a 600-second additional per-attempt build allowance and a 32-GiB process-tree memory ceiling; the CLI supervisor enforces the overall wall cutoff across preparation, native solves and scoring, followed by a short bounded cleanup interval. These limits must accompany the eventual campaign authorization.
