# Governance record formats

These formats implement Appendices B, C and E and invariants INV-10 and INV-11 of
`WRITING_ORCHESTRATION_PLAN_20260914.md`. `W/tools/check_governance.py` parses them.

All paths are repository-relative and use forward slashes.

An **identity** is an object `{"agent_type": str, "family": "opus"|"fable"|"sonnet"|"haiku"}`. The
orchestrator is written as the string `"ORCH"`.

## 1. Dispatch log: `W/governance/dispatch_log.jsonl`

The log is append-only and holds one JSON object per line. Each dispatch writes a `dispatched` event
and later a terminal event (`completed` or `failed`) with the same `seq`. A checker takes the latest
event for each `seq`.

```json
{"seq": 12, "event": "dispatched|completed|failed", "ts": "2026-09-14T10:00:00Z",
 "phase": "P1", "wave": "P1-W2", "task": "anchors-A",
 "identity": {"agent_type": "general-purpose", "family": "opus"},
 "role": "builder|critic|voter|confirmer|second_chair|reader|referee|probe|check_author|code_review|extractor|researcher",
 "artifacts_built": ["reports/.../anchors.json"],
 "artifacts_under_review": [],
 "self_reported_model": null,
 "prompt_file": "reports/horizon_robustness_results/writing/governance/prompts/P1-012-anchors-A.md",
 "input_hashes": {"reports/.../case_frame.csv": "<sha256>"},
 "allowed_outputs": [],
 "result_file": "reports/horizon_robustness_results/writing/governance/results/P1-012-anchors-A.md",
 "retry_of": null, "failure_reason": null}
```

On a `completed` event, `result_file` must name an existing file.

## 2. Findings: `W/governance/findings.jsonl`

Also append-only. The latest line for each `id` wins.

```json
{"id": "F-001", "phase": "P1", "raised_by": {"agent_type": "...", "family": "...", "seq": 14},
 "artifact": "path", "built_by": {"agent_type": "...", "family": "..."} ,
 "severity": "BLOCKING|MAJOR|MINOR", "claim": "...", "evidence": "...",
 "verification": {"status": "PENDING|CONFIRMED|REJECTED", "by": "ORCH" | {"agent_type": "...", "family": "...", "seq": 15}, "evidence": "..."},
 "fix_confirmed_by": null | {"agent_type": "...", "family": "...", "seq": 16}}
```

`built_by` is `"ORCH"` when the orchestrator built the artifact.

**Fix confirmer role (Q-011, Class E).** The dispatch named by `fix_confirmed_by` has role `critic` or `code_review`: the critic that raised the finding, or another critic (plan §4.5 BCL step 5). For findings against ORCH-built artifacts, the §3 clarification and A-003 still apply.

## 3. Decision records: `W/governance/decisions/DR-###.md`

Each file starts with one fenced `json` block, followed by the human-readable record from Appendix B.

```json
{"id": "DR-001", "q_card": "Q-008", "panel": "ADP-3|ADP-5",
 "artifacts_under_decision": ["path"],
 "seats": [{"agent_type": "...", "family": "...", "seq": 20, "role": "plain|red|blue|second_chair", "built": ["path"]}],
 "rounds": 2, "runoff": false,
 "ballots": [{"seq": 20, "round": 1, "valid": true, "position": "a"}],
 "chair_checks": ["opened locator X: confirmed"],
 "outcome": "a", "rule": "strict_majority|runoff|conservative_default|fallback|orch_pick",
 "dissent": "...", "reversible": true, "listed_in_handoff": false}
```

A DR with no named panel counts as ADP-3.

**Clarifications (14 Sep 2026, from the P0 check author's Q-cards):**

- **Seat roles.** A seat's `role` may also be `replaced`. That marks a voter replaced under §4.3 chair verification item 4. Rule (d) excludes `replaced` and `second_chair` seats from the panel-size count. A `replaced` seat must name `replaced_by_seq`.
- **Ballot identity.** A ballot's identity is the seat with the same `seq` in the same DR. A ballot whose `seq` matches no seat is a violation.
- **Findings against ORCH-built artifacts.** When `built_by` is `"ORCH"`, `verification.by` must be an independent confirmer identity, never `"ORCH"`, whether the finding is CONFIRMED or REJECTED (plan §4.5 BCL step 3). `fix_confirmed_by` must be a critic identity and is never `"ORCH"` (plan §4.5 BCL step 5).

## 4. Gate records: `W/governance/gates/<P#>-<G#>.json`

```json
{"gate": "P0:G1", "check": "PY reports/.../check_inputs.py" | "MANUAL",
 "expect": "INPUTS UNCHANGED", "exit_code": 0, "token_found": true,
 "output_sha256": "<sha256 of combined stdout+stderr>", "ts": "...",
 "negative_control": {"fixture": ".unlazy/horizon-writing/fixtures/check_inputs/", "exit_code": 1, "token_found": false} | "EXEMPT: <reason>",
 "evidence_refs": ["DR-001", "F-003"], "status": "MET|UNMET"}
```

A `MANUAL` gate has `exit_code` null. It must list `evidence_refs` that exist as DR files or finding ids.

## 5. Check-script registry: `W/governance/check_scripts.json`

```json
[{"script": "reports/.../tools/check_inputs.py",
  "author": {"agent_type": "general-purpose", "family": "sonnet", "seq": 5},
  "reviewer": {"agent_type": "code-reviewer", "family": "fable", "seq": 6},
  "checks_artifacts": ["reports/.../governance/source_manifest.json"]}]
```

## 6. Plan addenda: `W/governance/PLAN_ADDENDA.md`

Each entry is a level-2 heading `## A-### <title>` and must contain a line `DR: DR-###` that names
an existing DR file.

## 7. State: `W/governance/state.json`

Defined in Appendix D of the plan. `families` maps each family to
`{"status": "available|unavailable", "ts": "...", "self_reported_model": "..."}`.

## 8. Snapshots: `.unlazy/horizon-writing/snapshots/<id>.json`

A snapshot holds the SHA-256 of every file under `W/` and `L/` (the snapshot directory itself is
excluded), plus the output of `git status --porcelain --untracked-files=all`. The `W/` and `L/` paths
are excluded from the porcelain part because their files are already hashed.

# Version 2 additions (DR-001, 14 Sep 2026)

## 9. Waivers in gate records (A-001 item 2, A-002)

A gate record may carry a waiver:

```json
"waiver": {"by": "USER", "decision": "U5",
           "file": "reports/horizon_robustness_results/writing/governance/user_decisions.md",
           "condition": "output names no MODIFIED or MISSING file other than the allowed paths"}
```

A waiver is valid only if all of these hold (A-001 amendment S3, A-002):
1. `user_decisions.md` contains a heading `## <decision> (`.
2. `required_gates.json` lists that decision under the gate's `waivable_by`.
3. The `condition` field is present and non-empty.
4. The record's `exit_code` equals the registry entry's `exit_code`.
5. The stored `output_file`, ignoring empty lines, consists of exactly the registry entry's `exact_lines`, in any order, and nothing else.
6. Every gate named in the entry's `requires_gates_met` has a `MET` record from the same run.

A gate with status `UNMET` and a valid waiver counts as satisfied for completeness. It is never reported as `MET`.

## 10. Required-gate registry and `--phase` (A-001 item 1, A-004)

`W/governance/required_gates.json` lists every gate of plan §6 by phase. For each gate it records:
- `type` (runnable or manual);
- `check` and `expect` tokens;
- `negative_control` exemption;
- `waivable_by`;
- `required_evidence`;
- `self: true` for the governance gate that evaluates the phase.

`check_governance.py --phase P#` enforces completeness for every phase up to and including P#. Without `--phase`, the audit enforces completeness only for phases listed in `state.json` `closed_phases`.

**Completeness rules:**

| Gate | Condition to satisfy |
|---|---|
| Any gate | A record `gates/<P#>-<G...>.json` exists (colon replaced by hyphen), or the gate is `self` |
| Runnable, `MET` | `exit_code == 0`, every `expect` token found in `output_file`, and a negative-control object with non-zero exit (or an exemption the registry permits) |
| Runnable, `UNMET` | Has a valid waiver |
| Manual | Every `required_evidence` item resolves |

Runnable gates with `required_evidence` must also resolve it.

## 11. Verdict records: `W/governance/verdicts.jsonl` (A-001 item 3)

The file is append-only, one JSON object per line:

```json
{"id": "V-001", "phase": "P0", "seq": 23, "identity": {"agent_type": "plan-reviewer", "family": "opus"},
 "role": "critic", "artifacts": ["path"], "token": "PLAN_SOLID",
 "result_file": "reports/horizon_robustness_results/writing/governance/results/P0-023-....md", "ts": "..."}
```

A verdict is valid only if `seq` is a completed dispatch with the same identity and `result_file` contains `token` verbatim.

## 12. Red-team pre-mortem records: `W/governance/rtp/RTP-###.json` (A-001 item 4)

```json
{"id": "RTP-001", "phase": "P4", "seq": 80, "identity": {"agent_type": "scientific-reviewer", "family": "sonnet"},
 "package": "reports/horizon_robustness_results/writing/CHECKPOINT_A.md",
 "points": [{"text": "...", "locator": "...", "disposition": "FIXED|REJECTED|DISCLOSED", "evidence": "..."}]}
```

An RTP record is valid only if it has at least one point, every point has a disposition and non-empty evidence, and `seq` is a completed dispatch.

## 13. Evidence references (A-001 item 5)

`evidence_refs` entries take these forms: `DR-###`, `F-###`, `V-###`, `RTP-###`, `FILE:<repository path>`. Each one must resolve.

**`required_evidence` kinds:**
- `FILE {path}`
- `DR {q_card}`: the DR must pass rule (d)
- `VERDICT {agent_type, token_any, min_count?}`
- `RTP {phase}`
- `any_of {alternatives: [[...], ...]}`: at least one alternative must be fully present

## 14. Decision records as verifiers (A-001 item 6)

In a finding, `verification.by` may be `"DR-###"`. That DR's panel must be ADP-3 (A-001 amendment S1), and its `artifacts_under_decision` must include the finding's `artifact`.

## 15. Check-script registry v2 (A-001 item 7)

Every `.py` file under `W/tools/`, `W/math/tools/` and `W/checks/` must appear in `check_scripts.json`:

```json
{"script": "...", "kind": "check|generator", "author": {"agent_type", "family", "seq"},
 "reviewer": {"agent_type": "code-reviewer", "family", "seq"} | null, "checks_artifacts": [...]}
```

For `kind: check`:
- the reviewer's `agent_type` is `code-reviewer`;
- the reviewer's family differs from the author's;
- both seqs are completed dispatches with matching identities;
- the author identity built none of `checks_artifacts` in any dispatch-log event.

ORCH utilities under `W/governance/tools/` are exempt.

## 16. Addenda (A-001 item 8)

Every `## A-###` entry contains `DR: DR-###`, naming an existing DR file that passes rule (d), or `U: U#`, naming a heading in `user_decisions.md`.

## 17. Dispatch-log corrections (A-001 item 10)

A correction is a superseding event with the same `seq`. It copies the prior terminal event, overrides the corrected fields, and adds `"correction": "<what changed and why>"`. Events recorded after the fact carry `"backfilled": true`.

A correction event is matched on (`seq`, `event`) (A-001 amendment S3). Every `completed` event carries `self_reported_model` as a string, or the literal `"not reported"`.

`log_dispatch.py` enforces two requirements:
- `--allowed` for the `builder` and `check_author` roles;
- `--inputs` or `--review` for every role except `probe`.

## 18. Snapshot receipts

- `--compare ID` writes `L/snapshots/<ID>.compare.json` with a timestamp, the result and the listed differences.
- ORCH captures compare output outside W and L, then copies it into `L/gate_outputs/` only after the compare has finished.
- Snapshot IDs match `[A-Za-z0-9._-]+`. Existing IDs are never overwritten.

## 19. Batched cards, multi-round seats, effective date

- **Batched cards.** On a card with sub-questions, `position` (ballots), `outcome` and `rule` (DR) may each be an object keyed by sub-question, for example `{"A-001": "b3"}`.
- **Seats across rounds.** A seat may carry `round_seqs` (for example `{"2": 13}`), giving the dispatch seq of each later round. A ballot's identity is the seat whose `seq`, or one of whose `round_seqs` values, equals the ballot's `seq`. A ballot that matches no seat is a violation.
- **Effective date (A-001 amendment R).** Sections 9 to 19 take effect for `check_governance.py` once the code-reviewer re-review of the P0 fix round returns `VERDICT: PASS`, recorded as a verdict record. Until then P0:G4 cannot be recorded MET.

## 20. Gate output text (Q-card from the P0 fix round, resolved by ORCH as Class E)

Every runnable gate record carries an output_file field that names the stored combined stdout+stderr of the check, under .unlazy/horizon-writing/gate_outputs/. The P0 records P0-G1, P0-G2, P0-G3 and P0-G5 already do. check_governance.py reads the text from output_file when that field is present, and falls back to .unlazy/horizon-writing/gate_outputs/<gate-stem>.txt otherwise. output_sha256 must equal the SHA-256 of that file.

## 21. Reply-only dispatches (ORCH utility change, 14 Sep 2026)

A builder dispatch that returns everything in its reply and writes nothing has an empty `allowed_outputs`, as the §1 example shows for P1 anchors A. Examples are DBR anchor builders and derivation builders.

- **Logging.** `log_dispatch.py dispatched --role builder --reply-only` records such a dispatch. It sets `"reply_only": true`, and `--allowed` is refused alongside it.
- **Built artifacts.** `artifacts_built` still names the repository paths where ORCH will save the returned script and output, so builder exclusion and INV-13 apply to that identity.
- **Governance checks.** `check_governance.py` places no requirement on `allowed_outputs`.
