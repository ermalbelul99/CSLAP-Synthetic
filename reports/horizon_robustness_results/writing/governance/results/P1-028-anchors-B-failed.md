# Dispatch seq 28: anchors builder B (optimization-coder/sonnet), FAILED

**Recorded by:** ORCH, 2026-09-14T12:16Z, after SNAPSHOT MATCH P1-W2.

## Failure

Task notification, status `failed`, verbatim:

> Agent "P1 anchors builder B (sonnet)" failed: Agent terminated early due to an API error: You've hit your session limit · resets 2:10pm (Europe/Paris) (error type rate_limit, HTTP 429, request id req_011Cf3GwJ2ZvXneeeFpgFzDt, model sent to the API: claude-sonnet-5)

The agent's reply stopped part-way through an OUTPUT JSON block, inside the key `ts.berner.d03.pass.TIGHT…`. The reply is incomplete, so it is not used, and it is not reproduced here. The session limit that stopped the agent also paused ORCH; the limit had reset when work resumed.

## Files the agent left

During the dispatch the agent wrote files outside the repository, into the ORCH session scratchpad. The snapshot compare confirmed that nothing inside the repository changed.

These files are kept for the record in `P1-W2-agent-scratch/`, and none of them is used as evidence:
- `p1_anchors_B_script.py`
- `out.json`
- `out_perkey.json`
- `err.txt`
- `chunk_00` to `chunk_07`

The agent never returned these files and never stated their hashes. Their manifest, with sizes, modification times and SHA-256 values, is `P1-W2-agent-scratch/MANIFEST.json`.

## Process gap (finding F-059)

Both DBR anchor builders were allowed to run their scripts from a temporary directory outside the repository. Both used the same ORCH session scratchpad for this, and neither brief forbade reading it.

The modification times show:
- builder A's `out_A_v1.json` at 13:29 local time;
- builder B's `out.json` at 13:30;
- builder A's final `anchors_A.py` and `out_A.json` at 13:32.

Blindness between A and B therefore cannot be proven for this wave.

## Consequence

Anchors B is dispatched again as a retry of seq 28, with:
- a private working directory;
- an explicit ban on reading the ORCH session scratchpad and any other agent's files.

ORCH also re-runs both anchor scripts from the source data. Agreement between A's script, which ORCH re-runs, and an isolated B is the evidence that P1:G1 will rest on.
