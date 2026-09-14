"""Governance-record consistency checker (plan INV-10, INV-11; P0:G4, P0:G5; A-001; U7).

Parses every record under ``W/governance/`` using the formats fixed by
``W/governance/GOVERNANCE_FORMATS.md`` and applies rules (a)-(i), dispatch-log integrity, the
required-gate registry (``--phase``), waivers, verdicts, red-team pre-mortems and the U7 (14 Sep
2026, ``user_decisions.md``) haiku-exclusion and weighted-vote rules.

Modes
-----
``check_governance.py [--root DIR] [--allow-pending] [--phase P#]``   Audit mode.
``check_governance.py --snapshot ID [--root DIR]``                     Write a snapshot of W/ and L/.
``check_governance.py --compare ID [--root DIR]``                      Compare the tree against a snapshot.
``check_governance.py --probe [--root DIR]``                           Check model-family availability.

``--root`` defaults to the repository root, derived from this script's own location.

F-029 (D8a): ``--snapshot`` prints two digests. ``SNAPSHOT CONTENT SHA256`` is the digest stored in
the written file's own ``snapshot_sha256`` field, computed over the snapshot payload (``files``,
``git_status``, ``porcelain_hashes`` and, when present, ``git_note``) before that field is added.
``SNAPSHOT FILE SHA256`` is the SHA-256 of the file as written to disk, which does include
``snapshot_sha256`` and therefore differs from the content digest. ``--compare`` recomputes the
stored snapshot's content digest from the file on disk and reports ``SNAPSHOT CHANGED`` with the
diff line ``snapshot file tampered`` if it no longer matches the stored ``snapshot_sha256``.

F-022 (D1): ``--compare`` validates the snapshot ID against ``ID_RE`` and requires the governance
directory to exist before it reads the snapshot or writes a compare receipt. A failure on either
check prints ``COMPARE FAILED: <reason>``, exits 1 and writes nothing.

Known gap (F-003, corrected per F-035): a snapshot hashes every file under W and L directly, and
hashes the content of every path git's porcelain status reports outside W and L. A file outside W
and L that is both gitignored (so it never appears in porcelain output) and untracked is invisible
to ``--snapshot``/``--compare``. ``.unlazy/horizon-writing/`` (L) is itself gitignored as a whole,
through ``.unlazy/.gitignore``, and so is ``W/tools/__pycache__/``; detection is unaffected by
either fact, because W and L are hashed directly rather than discovered through git status. The
residual gap is therefore limited to gitignored, untracked files outside W and L; ORCH tracks that
residual risk manually.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

W_REL = "reports/horizon_robustness_results/writing"
L_REL = ".unlazy/horizon-writing"

PHASE_ORDER = [f"P{i}" for i in range(10)]
ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")
DR_REF_RE = re.compile(r"^DR-\d+$")
CONFIRMABLE_WAIVER_DECISION_RE_TMPL = r"^##\s*{decision}\b.*\("


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def now_ts() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm_path(p: str) -> str:
    return str(p).replace("\\", "/").strip()


def load_jsonl(path: Path, violations: list[str] | None = None, label: str | None = None) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as exc:
            if violations is not None:
                violations.append(f"VIOLATION (log): {label or path.name} line {i} is not parsable JSON ({exc})")
    return out


def latest_by_id(records: list[dict], key: str) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    for r in records:
        rid = r.get(key)
        if rid is not None:
            latest[rid] = r
    return latest


def identity_key(ident) -> tuple:
    if ident == "ORCH":
        return ("ORCH", None)
    if isinstance(ident, dict):
        return (ident.get("agent_type"), ident.get("family"))
    return (None, None)


def identity_eq(a, b) -> bool:
    return identity_key(a) == identity_key(b)


def is_dr_ref(v) -> bool:
    return isinstance(v, str) and bool(DR_REF_RE.match(v))


def build_seat_index(seats: list[dict]) -> dict[int, dict]:
    """Map every seq that names a seat -- its own seq or any round_seqs value -- to that seat
    (GOVERNANCE_FORMATS.md #19: a ballot's identity is the seat whose seq, or one of whose
    round_seqs values, equals the ballot's seq)."""
    index: dict[int, dict] = {}
    for s in seats:
        if s.get("seq") is not None:
            index[s["seq"]] = s
        for rs in (s.get("round_seqs") or {}).values():
            index[rs] = s
    return index


# ---------------------------------------------------------------------------
# Loading governance records
# ---------------------------------------------------------------------------

def load_drs(decisions_dir: Path) -> list[dict]:
    drs = []
    if not decisions_dir.is_dir():
        return drs
    for f in sorted(decisions_dir.glob("DR-*.md")):
        text = f.read_text(encoding="utf-8")
        # F-010/F-006: the fenced json block must be the first thing in the file (anchored match,
        # not a search anywhere in the file).
        m = re.match(r"\s*```json\s*\n(.*?)\n```", text, re.DOTALL)
        data = None
        if m:
            try:
                data = json.loads(m.group(1))
            except json.JSONDecodeError:
                data = None
        drs.append({"_file": f.name, "_path": f, "_data": data, "_stem": f.stem})
    return drs


def load_gates(gates_dir: Path, violations: list[str]) -> dict[str, tuple[Path, dict]]:
    # F-006: keyed by file name, not by the record's own "gate" field, so a second file cannot
    # silently overwrite a failing record's slot.
    records: dict[str, tuple[Path, dict]] = {}
    if not gates_dir.is_dir():
        return records
    for gf in sorted(gates_dir.glob("*.json")):
        try:
            data = json.loads(gf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            violations.append(f"VIOLATION (e): {gf.name} is not parsable JSON")
            continue
        records[gf.stem] = (gf, data)
    return records


def load_registry(root: Path, violations: list[str]) -> dict:
    path = root / W_REL / "governance" / "required_gates.json"
    if not path.is_file():
        return {"phases": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        violations.append("VIOLATION (phase): required_gates.json is not parsable JSON")
        return {"phases": {}}


def load_gate_output_text(root: Path, gate_stem: str, output_file: str | None = None) -> tuple[str | None, str | None]:
    # F-028 (D7, formats #20): read the stored output from the record's own output_file when
    # present, else fall back to the stem-based path under L/gate_outputs/.
    if output_file:
        path = root / output_file
    else:
        path = root / L_REL / "gate_outputs" / f"{gate_stem}.txt"
    if not path.is_file():
        return None, None
    data = path.read_bytes()
    return data.decode("utf-8", errors="replace"), sha256_bytes(data)


def gate_output_file_ok(output_file: str) -> bool:
    # F-040 (N5, formats #20, U8 fix round 3): when present, output_file must normalize to a path
    # under L_REL/gate_outputs/, with no ".." segment anywhere in it. The stem-based fallback
    # (output_file absent) is unaffected and is not checked here.
    norm = norm_path(output_file)
    if norm.startswith("/") or (len(norm) > 1 and norm[1] == ":"):
        return False
    if ".." in norm.split("/"):
        return False
    prefix = f"{L_REL}/gate_outputs/"
    return norm.startswith(prefix) and norm != prefix


def load_verdicts(root: Path, by_seq: dict[int, dict], u7_from_seq, violations: list[str]) -> dict[str, dict]:
    path = root / W_REL / "governance" / "verdicts.jsonl"
    records = load_jsonl(path, violations, "verdicts.jsonl")
    out: dict[str, dict] = {}
    for v in records:
        vid = v.get("id")
        valid = True
        seq = v.get("seq")
        ident = v.get("identity")
        token = v.get("token")
        result_file = v.get("result_file")
        e = by_seq.get(seq)
        if e is None or e.get("event") != "completed":
            violations.append(f"VIOLATION (v): {vid} seq={seq} has no completed dispatch")
            valid = False
            e = None
        elif not identity_eq(ident, e.get("identity")):
            violations.append(f"VIOLATION (v): {vid} identity does not match dispatch-log seq={seq}")
            valid = False

        # F-025 (D4): a verdict is valid only if token is a non-empty string, result_file equals
        # the result_file of the completed dispatch-log event for that seq, and that file contains
        # token verbatim. A malformed verdict is a violation and never a crash.
        if not isinstance(token, str) or not token:
            violations.append(f"VIOLATION (v): {vid} token is not a non-empty string ({token!r})")
            valid = False
        expected_result_file = e.get("result_file") if e is not None else None
        if not result_file or result_file != expected_result_file:
            violations.append(
                f"VIOLATION (v): {vid} result_file {result_file!r} does not match the dispatch-log "
                f"result_file for seq={seq} ({expected_result_file!r})"
            )
            valid = False
        elif not (root / result_file).is_file():
            violations.append(f"VIOLATION (v): {vid} result_file missing ({result_file})")
            valid = False
        elif isinstance(token, str) and token and token not in (root / result_file).read_text(encoding="utf-8", errors="replace"):
            violations.append(f"VIOLATION (v): {vid} token {token!r} not found verbatim in result_file")
            valid = False
        check_haiku_post_u7(ident, seq, u7_from_seq, f"verdict {vid}", violations)
        out[vid] = {"_data": v, "_valid": valid}
    return out


def load_rtp(root: Path, by_seq: dict[int, dict], violations: list[str]) -> dict[str, dict]:
    rtp_dir = root / W_REL / "governance" / "rtp"
    out: dict[str, dict] = {}
    if not rtp_dir.is_dir():
        return out
    for f in sorted(rtp_dir.glob("RTP-*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            violations.append(f"VIOLATION (rtp): {f.name} is not parsable JSON")
            continue
        rid = data.get("id", f.stem)
        valid = True
        points = data.get("points") or []
        if not points:
            violations.append(f"VIOLATION (rtp): {f.name} has no points")
            valid = False
        for pt in points:
            if not pt.get("disposition") or not pt.get("evidence"):
                violations.append(f"VIOLATION (rtp): {f.name} has a point with no disposition or no evidence")
                valid = False
        seq = data.get("seq")
        e = by_seq.get(seq)
        if e is None or e.get("event") != "completed":
            violations.append(f"VIOLATION (rtp): {f.name} seq={seq} has no completed dispatch")
            valid = False
        out[rid] = {"_data": data, "_valid": valid}
    return out


# ---------------------------------------------------------------------------
# Log integrity
# ---------------------------------------------------------------------------

def check_log_integrity(root: Path, events: list[dict], allow_pending: bool, violations: list[str], info: list[str]) -> dict[int, dict]:
    if not events:
        violations.append("VIOLATION (log): dispatch log missing or empty (zero-items rule)")
        return {}

    known_events = {"dispatched", "completed", "failed"}
    seen_seqs: list[int] = []
    first_event_of_seq: dict[int, str] = {}
    # A-001 item 10 (amendment S3): a correction is matched on (seq, event), so a correction to
    # the "dispatched" event must not hide a later "completed" event for the same seq.
    latest_by_key: dict[tuple[int, str], dict] = {}
    for e in events:
        seq = e.get("seq")
        ev = e.get("event")
        if ev not in known_events:
            violations.append(f"VIOLATION (log): seq {seq} has an unknown event value {ev!r}")
            continue
        if seq not in first_event_of_seq:
            first_event_of_seq[seq] = ev
            seen_seqs.append(seq)
        latest_by_key[(seq, ev)] = e

    for seq, ev in first_event_of_seq.items():
        if ev != "dispatched":
            violations.append(f"VIOLATION (log): seq {seq} does not start with a dispatched event")

    by_seq: dict[int, dict] = {}
    for seq in seen_seqs:
        terminal_event = None
        if (seq, "completed") in latest_by_key:
            terminal_event = "completed"
        elif (seq, "failed") in latest_by_key:
            terminal_event = "failed"
        if terminal_event is not None:
            rec = latest_by_key[(seq, terminal_event)]
            by_seq[seq] = rec
            if terminal_event == "completed":
                result_file = rec.get("result_file")
                if not result_file or not (root / result_file).is_file():
                    violations.append(f"VIOLATION (log): seq {seq} completed event names a missing result_file ({result_file})")
                sr_model = rec.get("self_reported_model")
                if not isinstance(sr_model, str):
                    violations.append(f"VIOLATION (log): seq {seq} completed event self_reported_model is not a string ({sr_model!r})")
            else:
                if not rec.get("failure_reason"):
                    violations.append(f"VIOLATION (log): seq {seq} failed event has no failure_reason")
        else:
            rec = latest_by_key[(seq, "dispatched")]
            by_seq[seq] = rec
            if allow_pending:
                info.append(f"IN FLIGHT {seq}")
            else:
                violations.append(f"VIOLATION (log): IN FLIGHT {seq}")

    return by_seq


def check_haiku_dispatches(events: list[dict], u7_from_seq, violations: list[str]) -> None:
    if not u7_from_seq:
        return
    for e in events:
        if e.get("event") != "dispatched":
            continue
        ident = e.get("identity") or {}
        seq = e.get("seq")
        if ident.get("family") == "haiku" and seq is not None and seq >= u7_from_seq:
            violations.append(f"VIOLATION (d): haiku dispatched seq {seq} after U7")


def check_haiku_post_u7(ident, seq_hint, u7_from_seq, context: str, violations: list[str]) -> None:
    """U7 (14 Sep 2026): no dispatch may use the haiku family from seq u7_from_seq on. Applied
    wherever an identity with a seq appears in a governance record."""
    if not u7_from_seq or not isinstance(ident, dict):
        return
    fam = ident.get("family")
    seq = seq_hint if seq_hint is not None else ident.get("seq")
    if fam == "haiku" and seq is not None and seq >= u7_from_seq:
        violations.append(f"VIOLATION (d): haiku {context} seq {seq} after U7")


def check_participant(ident, by_seq: dict[int, dict], context: str, violations: list[str], expected_roles: set[str] | None = None) -> None:
    if ident is None:
        return
    if ident == "ORCH":
        return
    if is_dr_ref(ident):
        return
    if not isinstance(ident, dict):
        violations.append(f"VIOLATION (c): {context} has a malformed identity ({ident!r})")
        return
    seq = ident.get("seq")
    if seq is None:
        violations.append(f"VIOLATION (c): {context} carries no seq")
        return
    e = by_seq.get(seq)
    if e is None or e.get("event") != "completed":
        violations.append(f"VIOLATION (c): {context} seq={seq} has no dispatch-log entry whose latest event is completed")
        return
    logged = e.get("identity") or {}
    claimed = (ident.get("agent_type"), ident.get("family"))
    seen = (logged.get("agent_type"), logged.get("family"))
    if claimed != seen:
        violations.append(
            f"VIOLATION (c): {context} seq={seq} identity mismatch (claimed {claimed}, dispatch log {seen})"
        )
        return
    # F-009/F-023 (D2, Q-011 a): the verifier's confirmer role and the fix-confirmer's role were
    # never checked against the log. check_participant() takes a set of allowed roles so a
    # fix_confirmed_by identity can be valid with dispatch-log role critic or code_review.
    if expected_roles is not None and e.get("role") not in expected_roles:
        violations.append(
            f"VIOLATION (c): {context} seq={seq} has dispatch-log role {e.get('role')!r}, "
            f"expected one of {sorted(expected_roles)}"
        )


# ---------------------------------------------------------------------------
# Evidence resolution (A-001 item 5, item 6; GOVERNANCE_FORMATS #13)
# ---------------------------------------------------------------------------

def check_dr_ref(ref: str, dr_ids: set[str], dr_pass: dict[str, bool], dr_by_id: dict[str, dict],
                  artifact, require_artifact: bool, context: str, tag: str, violations: list[str]) -> None:
    if ref not in dr_ids:
        violations.append(f"VIOLATION ({tag}): {context} references {ref}, which does not exist")
        return
    if not dr_pass.get(ref, False):
        violations.append(f"VIOLATION ({tag}): {context} references {ref}, which fails rule (d)")
        return
    dr = dr_by_id[ref]
    panel = (dr["_data"] or {}).get("panel") or "ADP-3"
    if panel != "ADP-3":
        violations.append(f"VIOLATION ({tag}): {context} references {ref}, whose panel is {panel!r}, not ADP-3")
    if require_artifact and artifact not in ((dr["_data"] or {}).get("artifacts_under_decision") or []):
        violations.append(f"VIOLATION ({tag}): {context} references {ref}, whose artifacts_under_decision does not include {artifact!r}")


def ref_exists(ref: str, dr_ids: set[str], finding_ids: set[str], verdict_ids: set[str], rtp_ids: set[str], root: Path) -> bool:
    if ref.startswith("DR-"):
        return ref in dr_ids
    if ref.startswith("F-"):
        return ref in finding_ids
    if ref.startswith("V-"):
        return ref in verdict_ids
    if ref.startswith("RTP-"):
        return ref in rtp_ids
    if ref.startswith("FILE:"):
        return (root / ref[len("FILE:"):]).is_file()
    return False


def resolve_evidence_item(item: dict, root: Path, dr_pass: dict[str, bool], dr_by_id: dict[str, dict],
                           verdict_records: dict[str, dict], rtp_records: dict[str, dict],
                           gate_phase: str | None = None) -> bool:
    kind = item.get("kind")
    if kind == "FILE":
        return (root / item["path"]).is_file()
    if kind == "DR":
        qcard = item.get("q_card")
        for dr_id, dr in dr_by_id.items():
            data = dr["_data"] or {}
            if data.get("q_card") == qcard and dr_pass.get(dr_id, False):
                return True
        return False
    if kind == "VERDICT":
        agent_type = item.get("agent_type")
        token_any = item.get("token_any") or []
        min_count = item.get("min_count", 1)
        # F-026 (D5): a verdict counts only if its phase equals the phase of the gate being
        # checked, unless the evidence item names an explicit phase.
        required_phase = item.get("phase", gate_phase)
        count = 0
        for v in verdict_records.values():
            if not v.get("_valid"):
                continue
            data = v["_data"]
            ident = data.get("identity") or {}
            if ident.get("agent_type") != agent_type:
                continue
            if required_phase is not None and data.get("phase") != required_phase:
                continue
            if data.get("token") in token_any:
                count += 1
        return count >= min_count
    if kind == "RTP":
        phase = item.get("phase")
        for r in rtp_records.values():
            if r.get("_valid") and r["_data"].get("phase") == phase:
                return True
        return False
    if kind == "any_of":
        for alt in item.get("alternatives", []) or []:
            if all(resolve_evidence_item(sub, root, dr_pass, dr_by_id, verdict_records, rtp_records, gate_phase) for sub in alt):
                return True
        return False
    return False


# ---------------------------------------------------------------------------
# Rules (a)-(i)
# ---------------------------------------------------------------------------

def rule_a(findings_latest: dict[str, dict], dr_ids: set[str], dr_pass: dict[str, bool], dr_by_id: dict[str, dict],
           allow_pending: bool, violations: list[str]) -> None:
    for fid, f in findings_latest.items():
        if f.get("severity") not in ("BLOCKING", "MAJOR"):
            continue
        verification = f.get("verification") or {}
        status = verification.get("status")
        built_by = f.get("built_by")
        artifact = f.get("artifact")
        verifier = verification.get("by")

        if status == "PENDING":
            if not allow_pending:
                violations.append(f"VIOLATION (a): finding {fid} is PENDING without --allow-pending")
            continue
        if status not in ("CONFIRMED", "REJECTED"):
            violations.append(f"VIOLATION (a): finding {fid} has invalid verification.status ({status!r})")
            continue

        if is_dr_ref(verifier):
            check_dr_ref(verifier, dr_ids, dr_pass, dr_by_id, artifact, True, f"finding {fid} verification.by", "a", violations)
        elif identity_eq(verifier, built_by):
            violations.append(f"VIOLATION (a): finding {fid} verifier equals built_by identity")

        if status == "CONFIRMED":
            fcb = f.get("fix_confirmed_by")
            if not fcb:
                # Q-card (P0-006): --allow-pending also tolerates a CONFIRMED finding whose fix is
                # not yet confirmed. Without the flag it stays a violation.
                if not allow_pending:
                    violations.append(f"VIOLATION (a): finding {fid} is CONFIRMED with a null fix_confirmed_by")
            elif is_dr_ref(fcb):
                check_dr_ref(fcb, dr_ids, dr_pass, dr_by_id, artifact, False, f"finding {fid} fix_confirmed_by", "a", violations)
            elif identity_eq(fcb, built_by):
                violations.append(f"VIOLATION (a): finding {fid} fix_confirmed_by equals built_by identity")


def check_orch_confirmer(value, field: str, artifact, dr_ids: set[str], dr_pass: dict[str, bool],
                          dr_by_id: dict[str, dict], require_artifact: bool, fid: str, violations: list[str]) -> None:
    # A-003 (DR-001 amendment b): for artifacts ORCH built, verification.by and fix_confirmed_by
    # must be a non-opus identity or an ADP-3 DR; never "ORCH" and never an opus identity.
    if value == "ORCH":
        violations.append(f"VIOLATION (b): finding {fid} {field} is ORCH for an ORCH-built artifact")
        return
    if is_dr_ref(value):
        check_dr_ref(value, dr_ids, dr_pass, dr_by_id, artifact, require_artifact, f"finding {fid} {field}", "b", violations)
        return
    if isinstance(value, dict):
        if value.get("family") == "opus":
            violations.append(f"VIOLATION (b): finding {fid} {field} is an opus identity for an ORCH-built artifact")
        return
    violations.append(f"VIOLATION (b): finding {fid} {field} is malformed ({value!r})")


def rule_b(findings_latest: dict[str, dict], dr_ids: set[str], dr_pass: dict[str, bool], dr_by_id: dict[str, dict],
           u7_from_seq, violations: list[str]) -> None:
    # F-009: this clarification has no severity limit, unlike rule (a); it is checked for every
    # ORCH-built finding regardless of severity.
    for fid, f in findings_latest.items():
        if f.get("built_by") != "ORCH":
            continue
        verification = f.get("verification") or {}
        status = verification.get("status")
        if status not in ("CONFIRMED", "REJECTED"):
            continue
        artifact = f.get("artifact")
        verifier = verification.get("by")
        check_orch_confirmer(verifier, "verification.by", artifact, dr_ids, dr_pass, dr_by_id, True, fid, violations)
        check_haiku_post_u7(verifier, None, u7_from_seq, f"finding {fid} verification.by", violations)

        fcb = f.get("fix_confirmed_by")
        if fcb is not None:
            check_orch_confirmer(fcb, "fix_confirmed_by", artifact, dr_ids, dr_pass, dr_by_id, False, fid, violations)
            check_haiku_post_u7(fcb, None, u7_from_seq, f"finding {fid} fix_confirmed_by", violations)


def rule_c(findings_latest: dict[str, dict], drs: list[dict], by_seq: dict[int, dict], violations: list[str]) -> None:
    for fid, f in findings_latest.items():
        check_participant(f.get("raised_by"), by_seq, f"finding {fid} raised_by", violations)
        verification = f.get("verification") or {}
        check_participant(verification.get("by"), by_seq, f"finding {fid} verification.by", violations, expected_roles={"confirmer"})
        check_participant(f.get("fix_confirmed_by"), by_seq, f"finding {fid} fix_confirmed_by", violations, expected_roles={"critic", "code_review"})

    for dr in drs:
        data = dr["_data"]
        if not isinstance(data, dict):
            continue
        seats = data.get("seats", []) or []
        for seat in seats:
            check_participant(seat, by_seq, f"{dr['_file']} seat seq={seat.get('seq')}", violations)
        seat_index = build_seat_index(seats)
        for ballot in data.get("ballots", []) or []:
            seq = ballot.get("seq")
            if seq not in seat_index:
                violations.append(f"VIOLATION (c): {dr['_file']} ballot seq={seq} has no matching seat")


def check_weighted_votes(fname: str, data: dict, seat_index: dict[int, dict], seats: list[dict],
                          state: dict, u7_from_seq, violations: list[str]) -> bool:
    # U7 items 2/3 (F-027, D6): weighted majority voting.
    ok = True
    state_weights = (state or {}).get("vote_weights", {}) or {}

    # F-058 (F-044 remainder): the non-integer-round check now runs first, over every ballot in the
    # DR -- valid or invalid -- before either early return below. Previously it ran only over
    # valid_ballots, and only after both early-return points (weighted rule not applying; weighted
    # rule applying with no weights), so a DR the weighted rule does not apply to, and an invalid
    # ballot in any DR, never produced this violation at all.
    ballots = data.get("ballots") or []
    bad_round_seqs: set = set()
    for b in ballots:
        if not isinstance(b, dict):
            continue
        if "round" in b:
            r = b.get("round")
            if not isinstance(r, int) or isinstance(r, bool):
                seq = b.get("seq")
                if seq not in bad_round_seqs:
                    violations.append(f"VIOLATION (d): {fname} ballot seq={seq} has a non-integer round")
                    ok = False
                bad_round_seqs.add(seq)

    # F-027: the rule applies -- weights and weighted_tally become mandatory -- once any seat's
    # seq or round_seqs value is at or above state.json's u7_from_seq. There is no default of 1
    # for a seated family with no state weight.
    seat_seqs: list[int] = []
    for s in seats:
        if s.get("seq") is not None:
            seat_seqs.append(s["seq"])
        seat_seqs += list((s.get("round_seqs") or {}).values())
    applies = bool(u7_from_seq) and any(sv is not None and sv >= u7_from_seq for sv in seat_seqs)

    weights = data.get("weights")
    has_weights = isinstance(weights, dict)
    if not applies and not has_weights:
        return ok

    if not has_weights:
        violations.append(f"VIOLATION (d): {fname} has a seat at or after u7_from_seq but no weights")
        return False

    seated_families = {s.get("family") for s in seats if s.get("family")}
    for fam in sorted(seated_families):
        if fam not in state_weights:
            violations.append(f"VIOLATION (d): {fname} seated family {fam!r} has no weight in state.json vote_weights")
            ok = False
        elif fam not in weights:
            violations.append(f"VIOLATION (d): {fname} seated family {fam!r} is missing from weights")
            ok = False
        elif weights[fam] != state_weights[fam]:
            violations.append(f"VIOLATION (d): {fname} weight for {fam} ({weights[fam]}) does not match state.json vote_weights ({state_weights[fam]})")
            ok = False

    tally = data.get("weighted_tally")
    if applies and not isinstance(tally, dict):
        violations.append(f"VIOLATION (d): {fname} has a seat at or after u7_from_seq but no weighted_tally")
        return False
    tally = tally or {}

    outcome = data.get("outcome")
    rule_field = data.get("rule")
    # F-058 (F-044 remainder): valid_ballots/usable_ballots reuse bad_round_seqs computed above over
    # every ballot, so an invalid ballot's bad round is still recorded even though the ballot itself
    # is excluded from valid_ballots (and therefore usable_ballots) exactly as before.
    valid_ballots = [b for b in ballots if b.get("valid")]
    usable_ballots = [b for b in valid_ballots if b.get("seq") not in bad_round_seqs]

    # Batched (outcome is an object keyed by sub-question) vs. single-question DRs: in the
    # single-question case weighted_tally is the flat {option: weight} dict itself, not
    # weighted_tally.get(<sub-question>) -- there is no sub-question key to look up.
    batched = isinstance(outcome, dict)
    sub_qs = list(outcome.keys()) if batched else [None]

    def rule_of(q):
        return (rule_field.get(q) if isinstance(rule_field, dict) else rule_field) or ""

    def exempt(q_rule) -> bool:
        return any(str(q_rule).startswith(p) for p in ("runoff", "conservative_default", "fallback", "orch_pick"))

    # F-038 (N3, U8 fix round 3): a DR the weighted rule applies to (a seat at or above
    # u7_from_seq) must not pass with nothing checked just because every ballot is invalid. Flag
    # each non-exempt sub-question (or the single question) instead of returning ok unconditionally.
    if not valid_ballots:
        if applies:
            for q in sub_qs:
                if exempt(rule_of(q)):
                    continue
                label = q or "outcome"
                violations.append(f"VIOLATION (d): {fname} weighted rule applies to {label} but no ballot is valid")
                ok = False
        return ok

    for q in sub_qs:
        q_outcome = outcome[q] if batched else outcome
        q_rule = rule_of(q)
        q_tally = ((tally.get(q) or {}) if batched else tally) or {}
        label = q or "outcome"

        # F-027: the final round is computed per sub-question, over the ballots that carry a
        # position for that sub-question -- not once for the whole DR. F-044 (N10): ballots with a
        # non-integer round are excluded here (usable_ballots), already flagged above.
        relevant: list[tuple[dict, object]] = []
        for b in usable_ballots:
            pos = b.get("position")
            opt = pos.get(q) if isinstance(pos, dict) else pos
            if opt is not None:
                relevant.append((b, opt))
        if not relevant:
            # F-038 (N3): an outcome sub-question with no ballot carrying a position for it (for
            # example a mistyped key) must not pass with no tally check.
            if not exempt(q_rule):
                violations.append(f"VIOLATION (d): {fname} outcome sub-question {label} has no valid ballot carrying a position for it")
                ok = False
            continue
        # F-039 (N4): a ballot with no round field defaults to round 1 both here (choosing the
        # final round) and below (deciding which ballots belong to it), so it is never silently
        # dropped from the tally just for omitting the field.
        final_round = max(b.get("round", 1) for b, _ in relevant)
        computed: dict[str, int] = {}
        for b, opt in relevant:
            if b.get("round", 1) != final_round:
                continue
            seat = seat_index.get(b.get("seq"))
            fam = seat.get("family") if seat else None
            if fam not in weights:
                continue  # already flagged above as an unweighted seated family
            computed[opt] = computed.get(opt, 0) + weights[fam]

        if computed != q_tally:
            violations.append(f"VIOLATION (d): {fname} weighted_tally for {label} ({q_tally}) does not match the weight of the valid final-round ballots ({computed})")
            ok = False
            continue

        if exempt(q_rule):
            continue
        total = sum(computed.values())
        winners = [opt for opt, w in computed.items() if total > 0 and w > total / 2]
        if q_outcome not in winners:
            violations.append(f"VIOLATION (d): {fname} outcome {q_outcome!r} for {label} is not the strict weighted majority of {computed}")
            ok = False
    return ok


def rule_d(drs: list[dict], by_seq: dict[int, dict], u7_from_seq, state: dict, violations: list[str]) -> dict[str, bool]:
    passed: dict[str, bool] = {}
    for dr in drs:
        fname = dr["_file"]
        stem = dr["_stem"]
        data = dr["_data"]
        ok = True
        if not isinstance(data, dict):
            violations.append(f"VIOLATION (d): {fname} has no parsable leading json block")
            passed[stem] = False
            continue

        declared_id = data.get("id")
        if declared_id != stem:
            violations.append(f"VIOLATION (d): {fname} json id {declared_id!r} does not match file name {stem!r}")
            ok = False

        ballots = data.get("ballots")
        if not ballots:
            violations.append(f"VIOLATION (d): {fname} has empty ballots")
            ok = False
        chair_checks = data.get("chair_checks")
        if not chair_checks:
            violations.append(f"VIOLATION (d): {fname} has empty chair_checks")
            ok = False

        seats = data.get("seats", []) or []
        # F-002: exclude replaced (and second_chair) seats from the panel-size count and from the
        # family-diversity set.
        counted = [s for s in seats if s.get("role") not in ("second_chair", "replaced")]
        families = {s.get("family") for s in counted if s.get("family")}  # F-010: None is not a family
        if len(families) < 2:
            violations.append(f"VIOLATION (d): {fname} seat families have fewer than 2 distinct values")
            ok = False

        artifacts_under_decision = set(data.get("artifacts_under_decision", []) or [])
        seat_index = build_seat_index(seats)
        for s in seats:
            built = set(s.get("built", []) or [])
            if built & artifacts_under_decision:
                violations.append(f"VIOLATION (d): {fname} seat seq={s.get('seq')} built list intersects artifacts_under_decision")
                ok = False
            if s.get("role") == "replaced":
                rbs = s.get("replaced_by_seq")
                if rbs is None:
                    violations.append(f"VIOLATION (d): {fname} replaced seat seq={s.get('seq')} has no replaced_by_seq")
                    ok = False
                else:
                    e = by_seq.get(rbs)
                    if e is None or e.get("event") != "completed":
                        violations.append(f"VIOLATION (d): {fname} replaced_by_seq={rbs} has no completed dispatch")
                        ok = False
            seq_vals = [s["seq"]] if s.get("seq") is not None else []
            seq_vals += list((s.get("round_seqs") or {}).values())
            for sv in seq_vals:
                check_haiku_post_u7(s, sv, u7_from_seq, f"{fname} seat", violations)

        panel = data.get("panel") or "ADP-3"
        expected = {"ADP-3": 3, "ADP-5": 5}.get(panel)
        if expected is None:
            violations.append(f"VIOLATION (d): {fname} has an unknown panel size {panel!r}")
            ok = False
        elif len(counted) != expected:
            violations.append(
                f"VIOLATION (d): {fname} seat count {len(counted)} (excluding second_chair and replaced) "
                f"!= {expected} for panel {panel}"
            )
            ok = False

        for b in ballots or []:
            seat = seat_index.get(b.get("seq"))
            if seat is not None:
                check_haiku_post_u7(seat, b.get("seq"), u7_from_seq, f"{fname} ballot", violations)

        # F-027 (D6): the DR-001 name exemption is removed. check_weighted_votes itself decides
        # whether the rule applies (any seat seq or round_seqs value at or after u7_from_seq); a DR
        # whose seats all predate u7_from_seq, DR-001 on the real root included, is unaffected.
        if not check_weighted_votes(fname, data, seat_index, seats, state, u7_from_seq, violations):
            ok = False

        passed[stem] = ok
    return passed


def rule_e(gate_records: dict[str, tuple[Path, dict]], dr_ids: set[str], finding_ids: set[str],
           verdict_ids: set[str], rtp_ids: set[str], root: Path, violations: list[str]) -> None:
    seen_gate_ids: dict[str, str] = {}
    for stem, (gf, data) in gate_records.items():
        gate_id = data.get("gate")
        expected_stem = (gate_id or "").replace(":", "-")
        if expected_stem != stem:
            violations.append(f"VIOLATION (e): {gf.name} gate field {gate_id!r} does not match file name {stem!r}")
        if gate_id in seen_gate_ids:
            violations.append(f"VIOLATION (e): duplicate gate id {gate_id!r} in {gf.name} and {seen_gate_ids[gate_id]}")
        else:
            seen_gate_ids[gate_id] = gf.name

        check = data.get("check")
        is_manual = check == "MANUAL"
        refs = data.get("evidence_refs") or []
        status = data.get("status")

        if is_manual:
            if data.get("exit_code") is not None:
                violations.append(f"VIOLATION (e): {gf.name} is MANUAL but has a non-null exit_code")
            if not refs:
                violations.append(f"VIOLATION (e): {gf.name} is MANUAL with empty evidence_refs")
        else:
            exit_code = data.get("exit_code")
            token_found = data.get("token_found")
            if not isinstance(exit_code, int) or isinstance(exit_code, bool):
                violations.append(f"VIOLATION (e): {gf.name} is missing an integer exit_code")
            if not isinstance(token_found, bool):
                violations.append(f"VIOLATION (e): {gf.name} is missing a boolean token_found")
            sha = data.get("output_sha256")
            if not (isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha)):
                violations.append(f"VIOLATION (e): {gf.name} is missing a valid 64-hex output_sha256")
            nc = data.get("negative_control")
            nc_ok = (isinstance(nc, dict) and isinstance(nc.get("exit_code"), int) and nc.get("exit_code") != 0) or (
                isinstance(nc, str) and nc.startswith("EXEMPT:")
            )
            if not nc_ok:
                violations.append(f"VIOLATION (e): {gf.name} has an invalid negative_control")
            # F-001: a non-MANUAL gate is MET only with exit_code 0 and token_found true.
            if status == "MET" and (exit_code != 0 or token_found is not True):
                violations.append(
                    f"VIOLATION (e): {gf.name} has status MET but exit_code={exit_code!r} token_found={token_found!r}"
                )

        for r in refs:
            if not ref_exists(r, dr_ids, finding_ids, verdict_ids, rtp_ids, root):
                violations.append(f"VIOLATION (e): {gf.name} evidence_ref {r} does not exist")

        if status not in ("MET", "UNMET"):
            violations.append(f"VIOLATION (e): {gf.name} status must be MET or UNMET (got {status!r})")


def rule_f(root: Path, dr_ids: set[str], dr_pass: dict[str, bool], violations: list[str]) -> None:
    path = root / W_REL / "governance" / "PLAN_ADDENDA.md"
    if not path.is_file():
        # F-010: a missing PLAN_ADDENDA.md used to pass silently.
        violations.append("VIOLATION (f): PLAN_ADDENDA.md not found")
        return
    text = path.read_text(encoding="utf-8")
    ud_path = root / W_REL / "governance" / "user_decisions.md"
    ud_text = ud_path.read_text(encoding="utf-8") if ud_path.is_file() else ""
    headings = list(re.finditer(r"^## (A-\d+)\b.*$", text, re.MULTILINE))
    for i, m in enumerate(headings):
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[start:end]
        aid = m.group(1)
        dr_match = re.search(r"^DR:\s*(DR-\d+)\s*$", body, re.MULTILINE)
        u_match = re.search(r"^U:\s*(U\d+)\s*$", body, re.MULTILINE)
        if dr_match:
            ref = dr_match.group(1)
            if ref not in dr_ids:
                violations.append(f"VIOLATION (f): {aid} references missing {ref}")
            elif not dr_pass.get(ref, False):
                violations.append(f"VIOLATION (f): {aid} references {ref}, which fails rule (d)")
        elif u_match:
            uref = u_match.group(1)
            if not re.search(rf"^##\s*{re.escape(uref)}\b", ud_text, re.MULTILINE):
                violations.append(f"VIOLATION (f): {aid} references {uref}, which has no heading in user_decisions.md")
        else:
            violations.append(f"VIOLATION (f): {aid} has no 'DR: DR-###' or 'U: U#' line")


def rule_g(registry: dict, gate_records: dict[str, tuple[Path, dict]], root: Path, dr_pass: dict[str, bool],
           dr_by_id: dict[str, dict], verdict_records: dict[str, dict], rtp_records: dict[str, dict],
           violations: list[str]) -> None:
    for phase, gates in (registry.get("phases") or {}).items():
        for g in gates:
            gate_id = g.get("gate")
            req = g.get("required_evidence")
            if not req:
                continue
            entry = gate_records.get((gate_id or "").replace(":", "-"))
            if entry is None:
                continue  # absence is reported by phase completeness, not here
            _, data = entry
            if data.get("status") != "MET":
                continue
            for item in req:
                if not resolve_evidence_item(item, root, dr_pass, dr_by_id, verdict_records, rtp_records, phase):
                    violations.append(f"VIOLATION (g): {gate_id} is MET but required evidence {item} does not resolve")


def rule_h(root: Path, by_seq: dict[int, dict], all_events: list[dict], u7_from_seq, violations: list[str]) -> None:
    path = root / W_REL / "governance" / "check_scripts.json"
    registry: list[dict] = []
    if path.is_file():
        try:
            registry = json.loads(path.read_text(encoding="utf-8")) or []
        except (json.JSONDecodeError, OSError):
            violations.append("VIOLATION (h): check_scripts.json is not parsable JSON")
            registry = []

    # A-001 item 7: the registry is mandatory once any check-script file exists under W/tools,
    # W/math/tools or W/checks. W/governance/tools/*.py are ORCH utilities and are exempt.
    disk_scripts: set[str] = set()
    for sub in ("tools", "math/tools", "checks"):
        base = root / W_REL / sub
        if base.is_dir():
            for p in base.rglob("*.py"):
                disk_scripts.add(norm_path(p.relative_to(root).as_posix()))
    exempt_prefix = norm_path(W_REL) + "/governance/tools/"
    disk_scripts = {s for s in disk_scripts if not s.startswith(exempt_prefix)}

    if disk_scripts and not path.is_file():
        violations.append(
            "VIOLATION (h): check_scripts.json is missing although check-script files exist under "
            "W/tools, W/math/tools or W/checks"
        )

    registry_by_script: dict[str, dict] = {}
    for entry in registry:
        script = norm_path(entry.get("script", ""))
        if script in registry_by_script:
            violations.append(f"VIOLATION (h): {script} is registered more than once")
        registry_by_script[script] = entry

    for script in sorted(disk_scripts):
        if script not in registry_by_script:
            violations.append(f"VIOLATION (h): {script} exists on disk but is not registered in check_scripts.json")

    for entry in registry:
        script = norm_path(entry.get("script", "<unknown>"))
        kind = entry.get("kind")
        author = entry.get("author") or {}
        if kind not in ("check", "generator"):
            violations.append(f"VIOLATION (h): {script} has an invalid kind {kind!r} (expected check or generator)")
        check_participant(author, by_seq, f"{script} author", violations)
        check_haiku_post_u7(author, author.get("seq"), u7_from_seq, f"check-script {script} author", violations)

        if kind == "check":
            reviewer = entry.get("reviewer") or {}
            if reviewer.get("agent_type") != "code-reviewer":
                violations.append(f"VIOLATION (h): {script} reviewer agent_type is not code-reviewer")
            if reviewer.get("family") == author.get("family"):
                violations.append(f"VIOLATION (h): {script} reviewer family equals author family")
            check_participant(reviewer, by_seq, f"{script} reviewer", violations)
            check_haiku_post_u7(reviewer, reviewer.get("seq"), u7_from_seq, f"check-script {script} reviewer", violations)

            checks_artifacts = {norm_path(p) for p in entry.get("checks_artifacts", []) or []}
            author_key = (author.get("agent_type"), author.get("family"))
            # F-005: scan every event, not just the latest per seq (a collision recorded only at
            # dispatch time, not repeated in the completed event, must still be caught). Report at
            # most once per seq even though dispatched and completed both carry the same
            # artifacts_built, so the message is not duplicated for an ordinary seq.
            flagged_seqs: set = set()
            for e in all_events:
                ident = e.get("identity") or {}
                seq = e.get("seq")
                if (ident.get("agent_type"), ident.get("family")) != author_key or seq in flagged_seqs:
                    continue
                built = {norm_path(p) for p in e.get("artifacts_built", []) or []}
                if checks_artifacts & built:
                    flagged_seqs.add(seq)
                    violations.append(
                        f"VIOLATION (h): {script} author also appears as a builder of a checked artifact (seq {seq})"
                    )


def rule_i(root: Path, violations: list[str]) -> None:
    for base_rel in (W_REL, L_REL):
        base = root / base_rel
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            length = len(str(p.resolve()))
            if length > 240:
                violations.append(f"VIOLATION (i): path is {length} characters (limit 240): {p}")


# ---------------------------------------------------------------------------
# Required-gate registry completeness (A-001 item 1) and waivers (item 2)
# ---------------------------------------------------------------------------

def phases_up_to(p: str) -> list[str]:
    idx = PHASE_ORDER.index(p)
    return PHASE_ORDER[: idx + 1]


def waiver_valid(root: Path, g: dict, data: dict, stem: str, gate_records: dict[str, tuple[Path, dict]],
                  violations: list[str]) -> bool:
    gate_id = g.get("gate")
    waiver = data.get("waiver")
    if not isinstance(waiver, dict):
        violations.append(f"VIOLATION (waiver): {gate_id} is UNMET with no waiver object")
        return False
    ok = True
    decision = waiver.get("decision")
    condition = waiver.get("condition")

    ud_path = root / W_REL / "governance" / "user_decisions.md"
    ud_text = ud_path.read_text(encoding="utf-8") if ud_path.is_file() else ""
    if not decision or not re.search(CONFIRMABLE_WAIVER_DECISION_RE_TMPL.format(decision=re.escape(str(decision))), ud_text, re.MULTILINE):
        violations.append(f"VIOLATION (waiver): {gate_id} waiver names a decision heading that does not exist in user_decisions.md")
        ok = False

    waivable = g.get("waivable_by") or []
    entry = next((w for w in waivable if w.get("decision") == decision), None)
    if entry is None:
        violations.append(f"VIOLATION (waiver): {gate_id} decision {decision!r} is not listed under waivable_by for this gate")
        return False

    if not condition:
        violations.append(f"VIOLATION (waiver): {gate_id} waiver has an empty condition")
        ok = False
    if data.get("exit_code") != entry.get("exit_code"):
        violations.append(f"VIOLATION (waiver): {gate_id} waiver exit_code {data.get('exit_code')!r} != registry exit_code {entry.get('exit_code')!r}")
        ok = False

    # F-040 (N7, U8 tooling round): apply the same gate_output_file_ok location check to the
    # record's output_file here that the MET path applies (check_phase_completeness), before ever
    # reading it -- a waiver record must not be able to point output_file outside
    # L_REL/gate_outputs/ (for example back at governance/results/) and have it silently read.
    output_file = data.get("output_file")
    if output_file is not None and not gate_output_file_ok(output_file):
        violations.append(
            f"VIOLATION (waiver): {gate_id} output_file does not resolve under {L_REL}/gate_outputs/ with no '..' segment: {output_file!r}"
        )
        ok = False
    else:
        text, sha = load_gate_output_text(root, stem, output_file)
        lines = [ln for ln in (text or "").splitlines() if ln.strip()]
        exact_lines = entry.get("exact_lines") or []
        if sorted(lines) != sorted(exact_lines):
            violations.append(f"VIOLATION (waiver): {gate_id} stored output does not equal the registry's exact_lines")
            ok = False
        # F-028 (D7, formats #20): the waiver path never compared output_sha256, so edited output
        # text still passed. It must match on the waiver path exactly as it does on the MET path.
        if text is None or sha != data.get("output_sha256"):
            violations.append(f"VIOLATION (waiver): {gate_id} output_sha256 does not match the stored gate output")
            ok = False

    for req_gate in entry.get("requires_gates_met", []) or []:
        req_entry = gate_records.get(req_gate.replace(":", "-"))
        if not req_entry or req_entry[1].get("status") != "MET":
            violations.append(f"VIOLATION (waiver): {gate_id} waiver requires {req_gate} MET in the same run")
            ok = False
    return ok


def check_phase_completeness(root: Path, registry: dict, gate_records: dict[str, tuple[Path, dict]],
                              target_phases: list[str], target_phase_self_exempt: str | None,
                              dr_pass: dict[str, bool], dr_by_id: dict[str, dict],
                              verdict_records: dict[str, dict], rtp_records: dict[str, dict],
                              violations: list[str]) -> None:
    # F-024 (D3): only the self gate of the target phase (the phase named by --phase) is exempt
    # from needing a record; self gates of earlier phases need one like any other gate. Without
    # --phase (closed_phases), target_phase_self_exempt is None and no self gate is exempt.
    phases = registry.get("phases") or {}
    for phase in target_phases:
        for g in phases.get(phase, []) or []:
            gate_id = g.get("gate")
            stem = (gate_id or "").replace(":", "-")

            if g.get("self") and phase == target_phase_self_exempt:
                for item in g.get("required_evidence") or []:
                    if not resolve_evidence_item(item, root, dr_pass, dr_by_id, verdict_records, rtp_records, phase):
                        violations.append(f"VIOLATION (phase): {gate_id} is the target self gate but required evidence {item} does not resolve")
                continue

            entry = gate_records.get(stem)
            if entry is None:
                violations.append(f"VIOLATION (phase): {gate_id} has no gate record ({phase})")
                continue
            _, data = entry
            gtype = g.get("type")
            status = data.get("status")

            if gtype == "manual":
                # F-024 (D3): a manual gate passes only if its record has status MET and every
                # required_evidence item resolves.
                if status != "MET":
                    violations.append(f"VIOLATION (phase): {gate_id} manual gate status is {status!r}, expected MET")
                for item in g.get("required_evidence") or []:
                    if not resolve_evidence_item(item, root, dr_pass, dr_by_id, verdict_records, rtp_records, phase):
                        violations.append(f"VIOLATION (phase): {gate_id} manual required evidence {item} does not resolve")
                continue

            if status == "MET":
                if data.get("exit_code") != 0:
                    violations.append(f"VIOLATION (phase): {gate_id} is MET but exit_code != 0")
                output_file = data.get("output_file")
                # F-040 (N5): output_file, when present, must resolve under L_REL/gate_outputs/
                # with no ".." segment; the stem-based fallback is unchanged.
                if output_file is not None and not gate_output_file_ok(output_file):
                    violations.append(f"VIOLATION (phase): {gate_id} output_file does not resolve under {L_REL}/gate_outputs/ with no '..' segment: {output_file!r}")
                else:
                    text, sha = load_gate_output_text(root, stem, output_file)
                    if text is None or sha != data.get("output_sha256"):
                        violations.append(f"VIOLATION (phase): {gate_id} output_sha256 does not match the stored gate output ({output_file or f'{L_REL}/gate_outputs/{stem}.txt'})")
                    else:
                        for tok in g.get("expect", []) or []:
                            if tok not in text:
                                violations.append(f"VIOLATION (phase): {gate_id} expected token {tok!r} not found in the stored gate output")
                nc = data.get("negative_control")
                if g.get("negative_control") == "exempt":
                    if not (isinstance(nc, str) and nc.startswith("EXEMPT:")):
                        violations.append(f"VIOLATION (phase): {gate_id} is registered exempt from a negative control but its record lacks an EXEMPT note")
                else:
                    if not (isinstance(nc, dict) and isinstance(nc.get("exit_code"), int) and nc.get("exit_code") != 0):
                        violations.append(f"VIOLATION (phase): {gate_id} is missing a real negative control")
                for item in g.get("required_evidence") or []:
                    if not resolve_evidence_item(item, root, dr_pass, dr_by_id, verdict_records, rtp_records, phase):
                        violations.append(f"VIOLATION (phase): {gate_id} is MET but required evidence {item} does not resolve")
            elif status == "UNMET":
                if not waiver_valid(root, g, data, stem, gate_records, violations):
                    violations.append(f"VIOLATION (phase): {gate_id} is UNMET with no valid waiver")
            else:
                violations.append(f"VIOLATION (phase): {gate_id} has status {status!r}, expected MET or UNMET")


# ---------------------------------------------------------------------------
# Audit mode
# ---------------------------------------------------------------------------

def audit(root: Path, allow_pending: bool, phase_arg: str | None) -> tuple[list[str], list[str]]:
    violations: list[str] = []
    info: list[str] = []
    gov = root / W_REL / "governance"

    events = load_jsonl(gov / "dispatch_log.jsonl", violations, "dispatch_log.jsonl")
    by_seq = check_log_integrity(root, events, allow_pending, violations, info)

    state: dict = {}
    state_path = gov / "state.json"
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            violations.append("VIOLATION (log): state.json is not parsable JSON")
    u7_from_seq = state.get("u7_from_seq")
    check_haiku_dispatches(events, u7_from_seq, violations)

    findings = load_jsonl(gov / "findings.jsonl", violations, "findings.jsonl")
    findings_latest = latest_by_id(findings, "id")

    drs = load_drs(gov / "decisions")
    dr_pass = rule_d(drs, by_seq, u7_from_seq, state, violations)
    dr_ids = {dr["_stem"] for dr in drs}
    dr_by_id = {dr["_stem"]: dr for dr in drs}
    finding_ids = set(findings_latest)

    rule_a(findings_latest, dr_ids, dr_pass, dr_by_id, allow_pending, violations)
    rule_b(findings_latest, dr_ids, dr_pass, dr_by_id, u7_from_seq, violations)
    rule_c(findings_latest, drs, by_seq, violations)

    verdict_records = load_verdicts(root, by_seq, u7_from_seq, violations)
    rtp_records = load_rtp(root, by_seq, violations)
    verdict_ids = set(verdict_records)
    rtp_ids = set(rtp_records)

    gate_records = load_gates(gov / "gates", violations)
    rule_e(gate_records, dr_ids, finding_ids, verdict_ids, rtp_ids, root, violations)
    rule_f(root, dr_ids, dr_pass, violations)

    registry = load_registry(root, violations)
    rule_g(registry, gate_records, root, dr_pass, dr_by_id, verdict_records, rtp_records, violations)
    rule_h(root, by_seq, events, u7_from_seq, violations)
    rule_i(root, violations)

    target_phases = phases_up_to(phase_arg) if phase_arg else list(state.get("closed_phases") or [])
    check_phase_completeness(root, registry, gate_records, target_phases, phase_arg, dr_pass, dr_by_id, verdict_records, rtp_records, violations)

    return violations, info


def cmd_audit(root: Path, allow_pending: bool, phase_arg: str | None) -> int:
    violations, info = audit(root, allow_pending, phase_arg)
    for line in info:
        print(line)
    for v in violations:
        print(v)
    if violations:
        print(f"GOVERNANCE VIOLATIONS ({len(violations)})")
        return 1
    print("GOVERNANCE CONSISTENT")
    return 0


# ---------------------------------------------------------------------------
# Snapshot / compare
# ---------------------------------------------------------------------------

def line_path(line: str) -> str:
    part = line[3:] if len(line) > 3 else line
    if " -> " in part:
        part = part.split(" -> ")[-1]
    return part.strip().strip('"')


def under_w_or_l(path_part: str) -> bool:
    return (
        path_part == W_REL
        or path_part.startswith(W_REL + "/")
        or path_part == L_REL
        or path_part.startswith(L_REL + "/")
    )


def run_git_status(root: Path) -> tuple[list[str] | None, bool, str | None]:
    if not (root / ".git").exists():
        return None, True, "not a git repository"
    try:
        # F-003/F-011: --no-optional-locks avoids touching .git/index; a non-zero exit must fail
        # the snapshot instead of silently comparing [] to [].
        result = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
            capture_output=True, text=True,
        )
    except OSError as exc:
        return None, False, f"git invocation failed: {exc}"
    if result.returncode != 0:
        return None, False, f"git exited {result.returncode}: {result.stderr.strip()}"
    lines = [ln for ln in result.stdout.splitlines() if not under_w_or_l(line_path(ln))]
    return lines, True, None


def compute_snapshot(root: Path) -> tuple[dict, bool]:
    files: dict[str, str] = {}
    snapshots_dir = (root / L_REL / "snapshots").resolve()
    hashed_any = False
    for base_rel in (W_REL, L_REL):
        base = root / base_rel
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file():
                continue
            rp = p.resolve()
            if rp == snapshots_dir or snapshots_dir in rp.parents:
                continue
            files[p.relative_to(root).as_posix()] = sha256_file(p)
            hashed_any = True

    lines, ok, err = run_git_status(root)
    if not ok:
        raise RuntimeError(f"git status failed: {err}")

    # F-003: hash the content of every porcelain-listed path outside W and L, not merely record
    # the status line, so a second edit to an already-modified/untracked file is detected.
    porcelain_hashes: dict[str, str | None] = {}
    if lines is not None:
        for ln in lines:
            part = line_path(ln)
            fp = root / part
            porcelain_hashes[part] = sha256_file(fp) if fp.is_file() else None

    data: dict = {"files": files, "git_status": lines, "porcelain_hashes": porcelain_hashes}
    if lines is None:
        data["git_note"] = err or "not a git repository"
    return data, hashed_any


def write_receipt(path: Path, snap_id: str, result: str, diffs: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"id": snap_id, "result": result, "ts": now_ts(), "diffs": diffs}
    path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def cmd_snapshot(root: Path, snap_id: str) -> int:
    if not ID_RE.fullmatch(snap_id):
        print(f"invalid snapshot id (must match [A-Za-z0-9._-]+): {snap_id}")
        return 1
    gov = root / W_REL / "governance"
    if not gov.is_dir():
        # F-004: a wrong --root must not silently write an empty, vacuously-matching snapshot.
        print(f"SNAPSHOT FAILED: {gov} does not exist (wrong --root?)")
        return 1
    snap_dir = root / L_REL / "snapshots"
    snap_path = snap_dir / f"{snap_id}.json"
    if snap_path.is_file():
        print(f"SNAPSHOT FAILED: id already exists, refusing to overwrite: {snap_id}")
        return 1
    try:
        data, hashed_any = compute_snapshot(root)
    except RuntimeError as exc:
        print(f"SNAPSHOT FAILED: {exc}")
        return 1
    if not hashed_any:
        print("SNAPSHOT FAILED: no files were hashed under W or L (wrong --root?)")
        return 1
    # F-029 (D8a): the content digest is computed over the snapshot payload (files, git_status,
    # porcelain_hashes and, when present, git_note) before snapshot_sha256 is added, and it is the
    # value stored in that field. The file digest is the SHA-256 of the file as actually written,
    # which does include snapshot_sha256 and therefore differs from the content digest.
    content_payload = json.dumps(data, indent=1, sort_keys=True) + "\n"
    content_digest = sha256_bytes(content_payload.encode("utf-8"))
    data["snapshot_sha256"] = content_digest
    snap_dir.mkdir(parents=True, exist_ok=True)
    file_bytes = (json.dumps(data, indent=1, sort_keys=True) + "\n").encode("utf-8")
    snap_path.write_bytes(file_bytes)
    file_digest = sha256_bytes(file_bytes)
    print(f"SNAPSHOT WRITTEN {snap_id}")
    print(f"SNAPSHOT CONTENT SHA256 {content_digest}")
    print(f"SNAPSHOT FILE SHA256 {file_digest}")
    return 0


def cmd_compare(root: Path, snap_id: str) -> int:
    # F-022 (D1): the snapshot ID and the governance root are validated before any read of the
    # snapshot or any write of a compare receipt. A failure here prints COMPARE FAILED: <reason>,
    # exits 1 and writes nothing.
    if not ID_RE.fullmatch(snap_id):
        print(f"COMPARE FAILED: invalid snapshot id (must match [A-Za-z0-9._-]+): {snap_id}")
        return 1
    gov = root / W_REL / "governance"
    if not gov.is_dir():
        print(f"COMPARE FAILED: {gov} does not exist (wrong --root?)")
        return 1

    snap_path = root / L_REL / "snapshots" / f"{snap_id}.json"
    receipt_path = root / L_REL / "snapshots" / f"{snap_id}.compare.json"
    if not snap_path.is_file():
        print(f"no such snapshot: {snap_id}")
        print(f"SNAPSHOT CHANGED {snap_id}")
        write_receipt(receipt_path, snap_id, "CHANGED", ["no such snapshot"])
        return 1
    try:
        old = json.loads(snap_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"could not parse snapshot {snap_id}: {exc}")
        print(f"SNAPSHOT CHANGED {snap_id}")
        write_receipt(receipt_path, snap_id, "CHANGED", [f"unparsable snapshot: {exc}"])
        return 1

    try:
        new, _hashed_any = compute_snapshot(root)
    except RuntimeError as exc:
        print(f"SNAPSHOT CHANGED {snap_id}: {exc}")
        write_receipt(receipt_path, snap_id, "CHANGED", [str(exc)])
        return 1

    diffs: list[str] = []

    # F-029 (D8a): recompute the stored snapshot's own content digest and compare it to the
    # snapshot_sha256 it carries. A mismatch means the snapshot file itself was edited after it was
    # written, which --compare must report like any other change.
    stored_digest = old.get("snapshot_sha256")
    old_for_digest = {k: v for k, v in old.items() if k != "snapshot_sha256"}
    recomputed_digest = sha256_bytes((json.dumps(old_for_digest, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    if stored_digest != recomputed_digest:
        diffs.append("snapshot file tampered")

    old_files = old.get("files", {})
    new_files = new.get("files", {})
    for p in sorted(set(old_files) | set(new_files)):
        if p not in old_files:
            diffs.append(f"ADDED {p}")
        elif p not in new_files:
            diffs.append(f"REMOVED {p}")
        elif old_files[p] != new_files[p]:
            diffs.append(f"CHANGED {p}")

    old_porc = old.get("porcelain_hashes", {}) or {}
    new_porc = new.get("porcelain_hashes", {}) or {}
    for p in sorted(set(old_porc) | set(new_porc)):
        if old_porc.get(p) != new_porc.get(p):
            diffs.append(f"CHANGED {p}")

    old_lines = set(old.get("git_status") or [])
    new_lines = set(new.get("git_status") or [])
    git_diff_lines = [f"GIT STATUS ADDED: {ln}" for ln in sorted(new_lines - old_lines)]
    git_diff_lines += [f"GIT STATUS REMOVED: {ln}" for ln in sorted(old_lines - new_lines)]

    for d in diffs:
        print(d)
    for d in git_diff_lines:
        print(d)

    changed = bool(diffs or git_diff_lines)
    result = "CHANGED" if changed else "MATCH"
    write_receipt(receipt_path, snap_id, result, diffs + git_diff_lines)
    if changed:
        print(f"SNAPSHOT CHANGED {snap_id}")
        return 1
    print(f"SNAPSHOT MATCH {snap_id}")
    return 0


# ---------------------------------------------------------------------------
# Probe mode (U7 item 1)
# ---------------------------------------------------------------------------

def parse_ts(ts: str) -> dt.datetime | None:
    try:
        return dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except (ValueError, TypeError):
        return None


def family_effective_status(info) -> str:
    if not isinstance(info, dict):
        return "unavailable"
    status = info.get("status")
    if status == "excluded":
        return "excluded"
    if status == "available":
        return "available"
    retry_after = parse_ts(info.get("retry_after"))
    if retry_after is not None:
        now = dt.datetime.now(dt.timezone.utc)
        if now >= retry_after:
            return "available"
        return f"retry after {info.get('retry_after')}"
    return "unavailable"


def cmd_probe(root: Path) -> int:
    state_path = root / W_REL / "governance" / "state.json"
    if not state_path.is_file():
        print("MODEL FAMILIES INSUFFICIENT (state.json missing)")
        return 1
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        print("MODEL FAMILIES INSUFFICIENT (state.json unparsable)")
        return 1

    families = state.get("families", {}) or {}
    # U7 item 4: minimum families is now opus and sonnet by default, not "3 of 4".
    required = state.get("required_families") or ["opus", "sonnet"]

    available = []
    for name in sorted(families):
        eff = family_effective_status(families[name])
        print(f"family {name}: {eff}")
        if eff == "available":
            available.append(name)

    missing_required = [f for f in required if f not in available]
    if not missing_required:
        print(f"MODEL FAMILIES AVAILABLE ({len(available)}: {', '.join(available)})")
        return 0
    print(f"MODEL FAMILIES INSUFFICIENT ({', '.join(missing_required)})")
    return 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None)
    parser.add_argument("--allow-pending", action="store_true")
    parser.add_argument("--phase", default=None, metavar="P#")
    parser.add_argument("--snapshot", default=None, metavar="ID")
    parser.add_argument("--compare", default=None, metavar="ID")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args(argv)

    script_path = Path(__file__).resolve()
    # This script lives at <root>/reports/horizon_robustness_results/writing/tools/check_governance.py,
    # four directories below the repository root.
    root = Path(args.root).resolve() if args.root else script_path.parents[4]

    modes = [bool(args.snapshot), bool(args.compare), args.probe]
    if sum(modes) > 1:
        print("only one of --snapshot, --compare, --probe may be given", file=sys.stderr)
        return 2

    if args.phase is not None and any(modes):
        print("--phase applies only to audit mode", file=sys.stderr)
        return 2
    if args.phase is not None and args.phase not in PHASE_ORDER:
        print(f"--phase must be one of {PHASE_ORDER}", file=sys.stderr)
        return 2

    if args.snapshot:
        return cmd_snapshot(root, args.snapshot)
    if args.compare:
        return cmd_compare(root, args.compare)
    if args.probe:
        return cmd_probe(root)
    return cmd_audit(root, args.allow_pending, args.phase)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
