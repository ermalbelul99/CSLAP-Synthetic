"""ORCH utility: append dispatch events to the governance dispatch log (INV-10; addendum A-001 item 10).

Usage:
  log_dispatch.py dispatched --phase P0 --wave P0-W1 --task T --agent-type A --family F --role R
      --prompt-file PATH [--inputs PATH ...] [--built PATH ...] [--review PATH ...] [--allowed PATH ...]
      [--retry-of SEQ] [--backfilled] [--reply-only]
  log_dispatch.py completed --seq N --result-file PATH [--self-reported-model TEXT] [--backfilled]
  log_dispatch.py failed --seq N --reason TEXT [--result-file PATH] [--backfilled]
  log_dispatch.py correct --seq N --event dispatched|completed|failed --reason TEXT
      [--set-allowed PATH ...] [--set-inputs PATH ...] [--set-self-reported-model TEXT] [--backfilled]

Rules (A-001 item 10):
  * builder and check_author roles require --allowed, unless --reply-only marks a dispatch that
    returns everything in its reply and writes nothing (formats section 1 example: allowed_outputs []);
  * every role except probe requires --inputs or --review;
  * completed events always carry self_reported_model as a string ("not reported" by default);
  * a correction supersedes the latest event with the same (seq, event), copies it, overrides the
    named fields, and records the reason in a "correction" field.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
W = ROOT / "reports" / "horizon_robustness_results" / "writing"
LOG = W / "governance" / "dispatch_log.jsonl"
STATE = W / "governance" / "state.json"
NEEDS_ALLOWED = {"builder", "check_author"}


def rel(path: str) -> str:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    return p.resolve().relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_events() -> list[dict]:
    if not LOG.exists():
        return []
    return [json.loads(line) for line in LOG.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event", choices=["dispatched", "completed", "failed", "correct"])
    parser.add_argument("--phase")
    parser.add_argument("--wave")
    parser.add_argument("--task")
    parser.add_argument("--agent-type")
    parser.add_argument("--family")
    parser.add_argument("--role")
    parser.add_argument("--prompt-file")
    parser.add_argument("--inputs", nargs="*", default=[])
    parser.add_argument("--built", nargs="*", default=[])
    parser.add_argument("--review", nargs="*", default=[])
    parser.add_argument("--allowed", nargs="*", default=[])
    parser.add_argument("--retry-of", type=int)
    parser.add_argument("--seq", type=int)
    parser.add_argument("--result-file")
    parser.add_argument("--self-reported-model")
    parser.add_argument("--reason")
    parser.add_argument("--backfilled", action="store_true")
    parser.add_argument("--reply-only", action="store_true")
    parser.add_argument("--event", dest="target_event", choices=["dispatched", "completed", "failed"])
    parser.add_argument("--set-allowed", nargs="*")
    parser.add_argument("--set-inputs", nargs="*")
    parser.add_argument("--set-self-reported-model")
    args = parser.parse_args(argv)

    state = json.loads(STATE.read_text(encoding="utf-8"))
    events = load_events()

    if args.event == "dispatched":
        missing = [k for k in ("phase", "wave", "task", "agent_type", "family", "role", "prompt_file") if getattr(args, k) is None]
        if missing:
            print(f"missing arguments: {missing}", file=sys.stderr)
            return 2
        if args.role in NEEDS_ALLOWED and not args.allowed and not args.reply_only:
            print(f"role {args.role} requires --allowed (or --reply-only for a dispatch that writes nothing)", file=sys.stderr)
            return 2
        if args.reply_only and args.allowed:
            print("--reply-only cannot be combined with --allowed", file=sys.stderr)
            return 2
        if args.role != "probe" and not (args.inputs or args.review):
            print(f"role {args.role} requires --inputs or --review", file=sys.stderr)
            return 2
        seq = int(state.get("next_seq", 1))
        prompt = rel(args.prompt_file)
        if not (ROOT / prompt).is_file():
            print(f"prompt file does not exist: {prompt}", file=sys.stderr)
            return 2
        inputs = [rel(p) for p in args.inputs] + [rel(p) for p in args.review if (ROOT / rel(p)).is_file()]
        record = {
            "seq": seq, "event": "dispatched", "ts": now(), "phase": args.phase, "wave": args.wave,
            "task": args.task, "identity": {"agent_type": args.agent_type, "family": args.family},
            "role": args.role, "artifacts_built": [rel(p) for p in args.built],
            "artifacts_under_review": [rel(p) for p in args.review], "self_reported_model": None,
            "prompt_file": prompt,
            "input_hashes": {p: sha256(ROOT / p) for p in dict.fromkeys(inputs) if (ROOT / p).is_file()},
            "allowed_outputs": [rel(p) for p in args.allowed], "result_file": None,
            "retry_of": args.retry_of, "failure_reason": None,
        }
        if args.backfilled:
            record["backfilled"] = True
        if args.reply_only:
            record["reply_only"] = True
        state["next_seq"] = seq + 1
        state.setdefault("in_flight", []).append(seq)
    elif args.event == "correct":
        if args.seq is None or args.target_event is None or not args.reason:
            print("correct requires --seq, --event and --reason", file=sys.stderr)
            return 2
        prior = [e for e in events if e["seq"] == args.seq and e["event"] == args.target_event]
        if not prior:
            print(f"no {args.target_event} event for seq {args.seq}", file=sys.stderr)
            return 2
        record = dict(prior[-1])
        record["ts_correction"] = now()
        if args.set_allowed is not None:
            record["allowed_outputs"] = [rel(p) for p in args.set_allowed]
        if args.set_inputs is not None:
            record["input_hashes"] = {rel(p): sha256(ROOT / rel(p)) for p in args.set_inputs if (ROOT / rel(p)).is_file()}
        if args.set_self_reported_model is not None:
            record["self_reported_model"] = args.set_self_reported_model
        if args.backfilled:
            record["backfilled"] = True
        record["correction"] = args.reason
    else:
        if args.seq is None:
            print("--seq is required", file=sys.stderr)
            return 2
        prior = [e for e in events if e["seq"] == args.seq]
        if not prior:
            print(f"unknown seq {args.seq}", file=sys.stderr)
            return 2
        record = dict(prior[-1])
        record.pop("correction", None)
        record.pop("ts_correction", None)
        record["event"] = args.event
        record["ts"] = now()
        if args.result_file:
            result = rel(args.result_file)
            if not (ROOT / result).is_file():
                print(f"result file does not exist: {result}", file=sys.stderr)
                return 2
            record["result_file"] = result
        if args.event == "completed":
            if not record.get("result_file"):
                print("a completed event needs --result-file", file=sys.stderr)
                return 2
            record["self_reported_model"] = args.self_reported_model or record.get("self_reported_model") or "not reported"
        if args.event == "failed":
            record["failure_reason"] = args.reason or "unspecified"
        if args.backfilled:
            record["backfilled"] = True
        state["in_flight"] = [s for s in state.get("in_flight", []) if s != args.seq]

    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(f"{args.event} seq={record['seq']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
