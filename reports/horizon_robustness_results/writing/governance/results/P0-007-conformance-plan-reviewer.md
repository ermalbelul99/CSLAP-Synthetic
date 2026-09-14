VERDICT: PLAN_NEEDS_REVISION

Short forms: plan = `R/WRITING_ORCHESTRATION_PLAN_20260914.md`; formats = `W/governance/GOVERNANCE_FORMATS.md`; cg = `W/tools/check_governance.py`.

## What already conforms

- **Q1.** Every CHECK/EXPECT in `L/gates/leaf-P0..P7.md` matches plan §6. Gaps 1 and 3 cover P8 and P9.
- **Q3.** The recorded families are enough to avoid H9 (state.json:15-35; P0-G5.json MET). P0:G2 was handled as a hard stop: the user was asked and nothing was voted on (status.log:7-8). Resting protection on `check_inputs.py` matches INV-2 and F4 (plan:67, 342).
- **U6.** It reaches P1 (DOCUMENT_VALUES_SPEC.md:14,48), and the supplement is pinned (source_manifest.json:22677).
- **Records.** The D1 commit exists (.git/logs/HEAD:43). Snapshot P0-W3 exists. `state.json` in_flight [6,7,8] matches the dispatch log.

## GAPS (blocking)

1. **P8:G1 and P9:G1 do not run the automated suite.** Evidence: plan:1001-1002, 1020, 1024-1025, 1044; leaf-P8.md:6 and leaf-P9.md:6 each run a single script. Fix: add one CHECK/EXPECT for each suite script and each P9 step 1 re-run.

2. **The U5 waiver does not carry to P9.**
   - Evidence: P9 re-runs `check_protected_sources.py` (plan:1025), which fails again on the same IJPR files (P0-G2.txt:1-2) and triggers H8 (plan:137).
   - The plan requires a DR for every post-go addendum (plan:28). The formats cannot record a user decision there (formats:94-95), and user_decisions.md:4 says U5 needs no DR.
   - Fix: allow addenda and gate waivers to cite `U: U5`, and carry the waiver into P9 with an addendum.

3. **Rule (e) and GATES.md G1 pass when gates are missing or unmet.**
   - Evidence: cg:322-323 accepts UNMET; cg:346-349 skip absent records; no required-gate list exists (only cg:28). The formats have no `waiver` field (formats:73-81), yet P0-G2.json:14-20 uses one. This conflicts with INV-11 (plan:403).
   - Fix: add a required-gate registry. Fail when a record is absent, when MET lacks exit 0 and the token, and when UNMET lacks a valid waiver.

4. **Rule (g) and the manual gates cannot be checked from the formats.**
   - Evidence: the plan requires formulation PASS and code PASS (plan:692-693), the canon DRs and PRES-3 sign-off (829-830), PLAN_SOLID (839), the convergence verdicts (1004-1012, 1020) and RTP dispositions (1045-1046). But `evidence_refs` accepts only DR and F ids (formats:81; cg:284-289), and rule (g) only checks that refs are non-empty (cg:351-359).
   - Fix: add a verdict record (seq, identity, token, artifact), an RTP record, and a per-gate table of required evidence.

5. **Rule (b) blocks the ADP-3 route.** Evidence: the plan lets an ADP-3 reject a finding against an ORCH-built artifact (plan:247-248), but the clarification allows only an identity (formats:69). Fix: allow `verification.by: "DR-###"` when that DR is an ADP-3.

6. **Rule (h) passes vacuously.** Evidence: `check_scripts.json` is absent although two check scripts exist, and cg returns silently (cg:364-365). This breaks "no empty passes" (plan:408). Fix: register seq 5 (author) and seq 6 (reviewer) before P0:G4, and fail on any unregistered W/tools script.

7. **INV-10 dispatch fields are incomplete.**
   - Evidence:
     - seq 5 has empty `allowed_outputs` although its brief allowed four paths (dispatch_log.jsonl:10; P0-005 brief:65-70), and its `self_reported_model` is null;
     - seq 6-8 have empty `input_hashes` (lines 11-13);
     - seq 1-4 were marked completed in the same second they were dispatched;
     - seq 5 was dispatched at 07:27:49, before the families were recorded at 07:29:26 (state.json:17), so the ledger's "probe before check-author" row (ledger:159) cannot be verified.
   - Fix: append corrective events, flag back-filled timestamps, and make `log_dispatch.py` require these fields.

8. **Two P0 deliverables are missing and no gate checks them.** Evidence: `environment.md` (plan:449-450, cited at ai_use_record.md:17) and `verification_inventory.md` (plan:466-467) do not exist. Fix: write both, and add a manual P0 gate.

9. **A fable reseat creates a model-family collision in P1.**
   - Evidence: reseat_log.md:13 gives extraction B to opus, and opus also builds the register (P1-register.md:56). The critic `results-integrity-reviewer`/opus was not reseated (plan:587), so it now reviews opus-built artifacts.
   - The plan wants confirmers from a different family (plan:288), and its reseat test is family-level (plan:243). Only sonnet built none of the three artifacts.
   - Fix: reseat that critic to sonnet, or record the identity-level reading in a DR.

## NICE-TO-HAVE

- P0:G3 prints two tokens (P0-G3.txt:11,22), but leaf-P0.md:17 expects one. The plan says "tokens" (plan:477).
- The OWNS lines in leaf-P6.md:3 and leaf-P7.md:3 omit the fixture directories INV-11 requires (plan:404).
- `EDIT INVARIANTS PASSED` (plan:997) has no gate record.
- P0-code-review-checks.md and P0-dryrun-P1-briefs.md lack the user_decisions pointer that user_decisions.md:4 requires.
- ORCH is Opus 5 (ai_use_record.md:11). While fable is out, prefer non-opus confirmers for ORCH-built artifacts.
- After the reseat, the P1 red and blue seats are both sonnet (reseat_log.md:15; plan:587-588). Log a diversity note.

## Consensus note

Escalated to ORCH, not the user. Close gaps 1-9 before P0:G4 closes. Gaps 3-6 change the INV-11 rule table, so they need a DR and a new code-reviewer review (plan:421). Record gaps 2 and 9 as PLAN_ADDENDA entries.
