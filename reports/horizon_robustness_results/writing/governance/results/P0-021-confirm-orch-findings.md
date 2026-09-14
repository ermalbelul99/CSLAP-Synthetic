# Confirmer decisions: F-031 to F-034

```
F-031: CONFIRMED
evidence: required_gates.json P0:G4 entry now (fixed) carries required_evidence naming a code-reviewer VERDICT and a note "F-031" — confirming the finding's own description of the pre-fix entry (gate/type/check/expect/self only). GOVERNANCE_FORMATS.md §19: "P0:G4 cannot be recorded MET" before a code-reviewer VERDICT: PASS. DR-001.md outcome table, A-001="b3", adopted text includes amendment R verbatim. grep of check_governance.py shows no hardcoded P0:G4/"amendment R" logic outside the docstring mention (line 1) — enforcement runs entirely through required_gates.json's required_evidence (GOVERNANCE_FORMATS.md §10/§13). Without it, nothing operationalized R. P0-017-code-rereview-checks.md: "Amendment R: not enforced... required_gates.json:44-52."
note: The registry, not the docstring, is what check_phase_completeness actually consults; an unwritten required_evidence item is a real enforcement gap, not cosmetic.

F-032: CONFIRMED
evidence: current gates/P0-G5.json "rerecorded" field: prior record used fixture probe_two_families (output P0-G5.r1.txt, sha256 2930435a...), stated "removed in seq 16 (finding F-032)". P0-016-fix-round-check-author.md fixture-list diff: "removed: `probe_two_families`". Current directory listing of .unlazy/horizon-writing/fixtures/check_governance/ has no probe_two_families entry; probe_sonnet_missing exists and is what the fixed record now cites. P0-G5.r1.txt content ("MODEL FAMILIES AVAILABLE (3: haiku, opus, sonnet)") matches the stale pre-fix, pre-U7 run.
note: Pre-fix record pointed its negative control at a fixture the same fix round had already deleted.

F-033: CONFIRMED
evidence: plan line 262 requires only that --snapshot "hash W/ and L/ and record git status --porcelain" — it does not require catching gitignored+untracked files outside W/L, so the checker still satisfies line 262 as written; no addendum was owed. check_governance.py:17-30 docstring documents the gap, but PLAN_ADDENDA.md (read in full) has no F-003 entry, and a code docstring is not a governance-reviewed artifact. The eventual fix lives in environment.md's new "Known limitation of the change detector (F-003, F-033, F-035)" section — a disclosure, not a PLAN_ADDENDA entry — confirming disclosure alone was the correct remedy.
note: Pre-fix, no governance-visible document surfaced the gap; that absence was a real, minor transparency lapse even though no rule change was required.

F-034: CONFIRMED
evidence: environment.md:1 now reads "plan P0 step 3" (fixed). P0-018-conformance-recheck.md: "environment.md:1 headers itself 'plan P0 steps 3 and 5,' but P0 step 5 is the check-author wave... which environment.md does not document — A-004 (PLAN_ADDENDA.md:69) requires these two files to cover steps 3 and 6, not 3 and 5." Plan lines 449-451 (step 3, model probe) match environment.md's content; lines 460-463 (step 5, check-author wave) are absent from it. PLAN_ADDENDA.md:69 (A-004 item 1) names steps "3 and 6," not "3 and 5."
note: Self-citation error confirmed against both the plan text and A-004's actual wording.
```

No Q-card — evidence for all four was conclusive and consistent across the artifact, its fix record, and the governing documents.
