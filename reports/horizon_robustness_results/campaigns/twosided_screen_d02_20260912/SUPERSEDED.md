# SUPERSEDED — twosided_screen_d02_20260912 (launch attempt 1)

Status: **INVALIDATED FOR SCIENTIFIC USE. Preserved as an immutable failure record.**
Superseded by: `../ts_d02_20260912/` — the identical manifest and implementation
hash, rerun under a shorter directory name.

## What happened

The campaign was launched on 12 September 2026 (01:33 local) under approved
manifest hash `4d0b6fbe8eaca292a46c675c86468dd8d37d3faabdcf78f9ce2f3a1e7752617b`
(implementation hash `5e1ee22fe31372d86e4c549f747604b9d3b46524182a516efb7f247833b261f8`).
The supervised child rebuilt and verified the quote, acquired the campaign lock,
wrote `manifest.json` and the invocation record, then crashed while publishing
the very first solve request:

    FileNotFoundError: [Errno 2] No such file or directory:
    '...\campaigns\twosided_screen_d02_20260912\solves\<64-hex>\attempts\primary\request.json.partial-<32-hex>'

That path is exactly 260 characters long. This host (Windows Server 2019 with
`LongPathsEnabled` not set) enforces the classic `MAX_PATH` limit of 259 usable
characters, and reports the overflow as "not found". The completed upper-only
campaigns used 15-character directory names (`screen_20260910`), which put the
same temporary file at 247 characters; this directory's 28-character name pushed
it past the limit. The threshold was reproduced outside the campaign tree on the
same day: a 259-character file path opens, a 260-character one fails.

Outcome: **0 native solves launched, 0 solver seconds charged** (no worker
process was ever spawned), 609 s elapsed, `PROCESS_ERROR`, and all 60 quoted
cases recorded as `CAMPAIGN_ERROR` in `supervision/<id>/terminal.json`.

## Assessment

An operator error in choosing the output directory name, not a defect in the
two-sided model, the manifest or the runner's provenance logic; the failure
occurred before any model reached a solver. Nothing about the science, the
manifest or the implementation changed. The two queued sensitivity campaigns
were launched in the same chain with equally long names and failed identically;
each carries its own `SUPERSEDED.md`.

## Correction

Rerun into a 15-character directory name, the same length as the completed
campaigns, with the same manifest and the same approval. The solver package is
deliberately **not** edited (no long-path prefix), so the implementation hash and
every approved manifest remain valid. Retry identifiers, should any ever be
needed, must stay short for the same reason.

This directory and all of its artifacts are retained unchanged.
