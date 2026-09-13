# SUPERSEDED — twosided_berner_d01_20260912 (launch attempt 1)

Status: **INVALIDATED FOR SCIENTIFIC USE. Preserved as an immutable failure record.**
Superseded by: `../ts_b01_20260912/` — the identical manifest and implementation
hash, rerun under a shorter directory name.

## What happened

Second run of the sequential chain launched on 12 September 2026, under approved
manifest hash `13e5bf8bc5d31a714c5e6ae8ef904b1e8f07724c3b24c55358c3da39aee0694a`
(implementation hash `5e1ee22fe31372d86e4c549f747604b9d3b46524182a516efb7f247833b261f8`;
BERNER, two-sided rule, δ = 0.01, 12 rows, 8 unique solves). The supervised child
rebuilt and verified the quote, took the campaign lock, wrote `manifest.json` and
the invocation record, created the first attempt directory, and crashed publishing
the first solve request:

    FileNotFoundError: [Errno 2] No such file or directory:
    '...\campaigns\twosided_berner_d01_20260912\solves\<64-hex>\attempts\primary\request.json.partial-<32-hex>'

The same 260-character path overflow as `../twosided_screen_d02_20260912/`: this
host enforces the classic `MAX_PATH` limit (259 usable characters; long paths not
enabled) and the 28-character directory name overflows it by one. See that
directory's `SUPERSEDED.md` for the reproduction.

Outcome: **0 native solves launched, 0 solver seconds charged**, 444 s elapsed,
`PROCESS_ERROR`, all 12 quoted cases recorded as `CAMPAIGN_ERROR` in
`supervision/<id>/terminal.json`, no case file written.

## Assessment and correction

Operator error in the output directory name; the two-sided model, the manifest
and the runner's provenance logic are untouched and the failure happened before
any model reached a solver. Rerun into a 15-character directory with the same
manifest and approval; the solver package is deliberately not edited.

This directory and all of its artifacts are retained unchanged.
