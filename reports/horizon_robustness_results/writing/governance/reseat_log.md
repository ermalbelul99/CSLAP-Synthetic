# Reseat log

This log records seats reassigned under the reseat rule of plan §4.4. Each dispatch-log entry also records the
identity that was actually used.

The P0 probe of 14 Sep 2026 found `fable` unavailable (HTTP 429, out of usage credits) and `opus`, `sonnet` and
`haiku` available. Fable is re-probed at each phase start.

| Phase | Planned seat | Reseated to | Reason |
|---|---|---|---|
| P0 | code-reviewer/fable (reviews `check_inputs.py`, `check_governance.py`) | code-reviewer/opus | fable unavailable; reviewer family must differ from the author (sonnet) |
| P1 | general-purpose/fable, anchors B (DBR) | general-purpose/haiku | fable unavailable; `compare_anchors.py` author (sonnet) may not build what it checks; A is opus |
| P1 | general-purpose/fable, document-value extraction (DBR, with haiku) | general-purpose/opus | fable unavailable; the extraction pair needs two families, and sonnet authors the comparison check |
| P1 | code-reviewer/fable (reviews P1 check scripts) | code-reviewer/opus | fable unavailable; family must differ from the author (sonnet) |
| P1 | scientific-reviewer/fable, red-team critic of the register | scientific-reviewer/sonnet | fable unavailable; sonnet built none of the artifacts under review (register, map, document values) |

## Rules adopted by DR-001 (A-003)

- P1 critic seats are read at identity level. `results-integrity-reviewer`/opus remains a valid critic of general-purpose/opus-built artifacts.
- ORCH runs on Opus 5 and counts as family opus. Independent confirmers and fix confirmers of ORCH-built artifacts come from an available non-opus family; if none is available, the finding goes to ADP-3.
- Diversity note: after the reseats, the P1 red-team and blue-team seats are both sonnet.

## Reassignments under user decision U7 (Haiku excluded; weights opus 2, fable 2, sonnet 1; fable retried after 12 h)

| Phase | Planned seat | Reassigned to | Reason |
|---|---|---|---|
| P1 | general-purpose/haiku, anchors B (DBR) | optimization-coder/sonnet, or general-purpose/fable when past retry_after | U7 excludes haiku; the family must differ from anchors A (opus); the identity must differ from the check author general-purpose/sonnet (INV-13) |
| P1 | general-purpose/haiku, document-value extraction A | optimization-coder/sonnet, or general-purpose/fable when past retry_after | U7; the pair needs two families (partner general-purpose/opus); the identity differs from the check author |
| P1 | general-purpose/haiku, requirements map | general-purpose/opus | U7; the coverage check author is general-purpose/sonnet, so the builder must be another identity |
| P2 | general-purpose/haiku, check_sources.py author | general-purpose/sonnet; its code-reviewer must then be opus | U7 |
| P2 | academic-researcher/haiku, extra search round | academic-researcher/sonnet, or fable when past retry_after | U7 |
| P3 | general-purpose/haiku, edge-case enumerator author | general-purpose/sonnet; its code-reviewer must then be opus | U7 |
| P3+ | CRT reader 1 general-purpose/haiku | general-purpose/sonnet, fresh | U7 |
| all | any other haiku seat | the same agent type from opus, fable (past retry_after) or sonnet, under the §4.4 reseat rule | U7 |

Weighted votes (U7): every DR records the family weights and the weighted tally. Panels mix at least two of opus, fable and sonnet.
