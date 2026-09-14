# AI-use record

This is a truthful record from which the manuscript's AI declaration is written (plan §3). Update it at the end
of every phase.

## Tools

| Tool | Version / identifier | Role |
|---|---|---|
| Claude Code (VS Code extension, Claude Agent SDK) | session of 14 Sep 2026 | Orchestrator (ORCH): dispatches, chairs panels, verifies claims, runs checks |
| Claude Opus 5 | `claude-opus-5` | ORCH model; sub-agent family `opus` |
| Claude Fable 5.1 | `claude-fable-5-1` | Sub-agent family `fable`, subject to available credits |
| Claude Sonnet 5 | `claude-sonnet-5` | Sub-agent family `sonnet` |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | Sub-agent family `haiku` |
| Apify web-fetch (MCP) | as available | Retrieval of public pages blocked for plain fetch (D3) |

The P0 model probe records self-reported model identities in `environment.md`.

## Uses by phase

| Phase | Use | Human checks pending |
|---|---|---|
| Planning (14 Sep) | AI wrote and reviewed the orchestration plan (7 review reports; `PLAN_REVIEW_LEDGER_20260914.md`) | User approved the plan and gave the go |
| P0 (14 Sep, after U7) | User decision U7: votes weighted by model (opus 2, fable 2, sonnet 1); haiku removed from all roles; fable retried after 12 h windows | Weights are an ORCH implementation of the user instruction; the user may change the numbers |
