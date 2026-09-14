# Execution environment (plan P0 step 3)

Recorded on 14 Sep 2026 by ORCH.

## Host and toolchain

| Item | Value | How recorded |
|---|---|---|
| OS | Windows Server 2019 Standard 10.0.17763 (`Windows-10-10.0.17763-SP0`) | `platform.platform()` |
| Shells | PowerShell 5.1 (primary); Git Bash | session environment |
| Python (all gate checks) | `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe`, Python 3.10.11 | `sys.version` |
| Python packages | numpy 2.2.1; pandas 2.2.3; matplotlib 3.10.6; jsonschema 4.23.0 | `importlib.metadata` |
| PDF libraries | none (pypdf, fitz and pdfplumber absent) | `importlib.util.find_spec` |
| git | 2.53.0.windows.2 | `git --version` |
| Node.js | absent (the unlazy gate-check scripts cannot run; gates use Python checks, following the "Node waived" precedent) | `command -v node` |
| LaTeX (pdflatex, latexmk, tectonic, MiKTeX, TeX Live) | absent; the user compiles on Overleaf (U3) | `command -v`, path probes |
| Other interpreters seen | `venv\Scripts\python.exe` (Python 3.10.11); `C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe` (Hexaly environment; not used, since H1 forbids tests and solvers) | earlier session probes |

## Model families (P0 model probe, dispatch seq 1–4)

| Family | Status | Self-reported model | Result file |
|---|---|---|---|
| opus | available | Opus 5 (claude-opus-5) | `W/governance/results/P0-001-probe-opus.md` |
| fable | **unavailable**: HTTP 429, out of usage credits (claude-fable-5-1) | none | `W/governance/results/P0-002-probe-fable.md` |
| sonnet | available | Claude Sonnet 5 (claude-sonnet-5) | `W/governance/results/P0-003-probe-sonnet.md` |
| haiku | available | claude-haiku-4-5-20251001 | `W/governance/results/P0-004-probe-haiku.md` |

Three families are available, which meets the plan's minimum (H9). Fable is re-probed at each phase start. Reseats are listed in `W/governance/reseat_log.md`.

## Plan decisions and external access

| Decision | Setting |
|---|---|
| D1 | Local commits. Baseline commit `7b4d0a8`; later commits at the ends of P4, P7 and P9; no push. |
| D2 | Companion = root `IJSSOL_CSLAP_v1.tex`, `IJSSOL_CSLAP_v1_supplementary.tex` and `IJSSOL_CSLAP_v1.bib` at HEAD (U5, U6). |
| D3 | Apify web-fetch may retrieve public URLs that return 403 to a plain fetch. Only ORCH has that tool; retrieved pages are saved under `W/literature/fetched/`. |
| D4 | The run goes end to end and pauses only at hard stops. |
| D5 | Revision 4 is accepted without a fourth gate round. |

## Path-length constraint

The host enforces the classic 259-character MAX_PATH limit. The repository root is 43 characters; the session scratchpad prefix is 135. Campaign trees are never copied under the scratchpad. INV-11 rule (i) caps paths created by the run at 240 characters.

## Update: user decision U7 (14 Sep 2026)

- haiku: **excluded** from every role from dispatch seq 17 on. Its earlier probe (seq 4) and votes (seq 10, 14) remain as history.
- fable: unavailable, retried only after a 12 h window following each usage-limit failure. Current retry_after: 2026-09-14T19:27:48Z (state.json).
- Required families (revised H9): opus and sonnet.
- Vote weights: opus 2, fable 2, sonnet 1. Rosters: governance/u7_rosters.md.

## Known limitation of the change detector (findings F-003, F-033, F-035)

- **What the plan requires.** Read-only wave step 2 (`WRITING_ORCHESTRATION_PLAN_20260914.md:262`) requires `--snapshot` to hash `W/` and `L/` and to record `git status --porcelain`. `check_governance.py` does both. It also hashes the content of every path that the porcelain status reports outside W and L.
- **Residual gap.** A file outside W and L that is both gitignored and untracked never appears in porcelain output. Writing or editing such a file during a read-only wave therefore goes undetected. On 14 Sep 2026 the read-only listing `git --no-optional-locks status --porcelain=v1 --ignored=matching -uall` showed 67 ignored entries outside the governed trees or around them, including:
  - `venv/`, `data/derived`, `20260908/` and `capsweep_instances/`;
  - several `__pycache__/` directories;
  - 48 entries under `reports/horizon_robustness_results/`, which are campaign runner byproducts.
- **W and L themselves.** `.unlazy/horizon-writing/` (L) is gitignored as a whole through `.unlazy/.gitignore`, and so is `W/tools/__pycache__/`. Detection inside W and L is unaffected, because both trees are hashed file by file. For D1 this means the ledger L stays local and never enters a commit.
- **ORCH mitigation.** For every read-only wave, ORCH saves the ignored-entry listing before the wave and compares it with a fresh listing after `--compare`. This catches new ignored entries. It does not catch edits to files inside an ignored directory that already existed. Read-only agents are instructed to write nothing (preamble item 1).
