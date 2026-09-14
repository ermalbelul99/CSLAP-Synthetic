# User decisions after the go

User decisions take precedence over every other governing document (plan §0, item 1). Every dispatch brief refers
to this file. A user decision is not a plan addendum and needs no decision record.

## U5 (14 Sep 2026): IJSSOL v1 is the only baseline; IJPR versions are not

**Question asked.** P0:G2 failed because the prior study's protected-source ledger (8 Sep) predates the user's commit
`16b6003`. That commit (13 Sep 23:37, "docs(ijpr): author's v4 manuscript revisions and cover letter") changed
`IJPR_CSLAP_v4.tex` and `IJPR_CSLAP_v4_supplementary.tex`.

**User answer, verbatim:** "The final clean article we submitted is not IJPR but IJSSOL v1 so do not take IJPR versions
as baseline to make the extension"

**Consequences for the run:**

1. **Companion baseline.** The only companion baseline for content, notation, style, numbers and citations is
   `IJSSOL_CSLAP_v1.tex`, with `IJSSOL_CSLAP_v1_supplementary.tex` and `IJSSOL_CSLAP_v1.bib` (D2).
2. **IJPR files are excluded.** `IJPR_CSLAP_v2.tex`, `IJPR_CSLAP_v3*.tex`, `IJPR_CSLAP_v4*.tex`, `IJPR_CSLAP*.bib` and
   `C&OR_CSLAP.tex` are earlier or other drafts. No agent may use them as a baseline, source of wording, style
   reference, number source or citation source.
3. **IJPR files stay protected.** They remain read-only (H2) and pinned in the source manifest, but nothing reads
   them for writing purposes.
4. **P0:G2 is waived by user decision.** The gate reports only the two IJPR files as modified, and the user states that
   IJPR versions are not the baseline. The record keeps status UNMET with a waiver that references U5. The prior
   study's ledger (`.unlazy/horizon-cslap/preserved_sources.json`) is not refreshed or edited. From P0 on, protection
   of every pinned file, IJPR files included, rests on `W/tools/check_inputs.py`.

## U6 (14 Sep 2026): the IJSSOL v1 supplement is part of the companion baseline

**User message, verbatim:** "IJSSOL v1 has also a supplementary file you should consider as well"

**Consequences for the run.** `IJSSOL_CSLAP_v1_supplementary.tex` belongs to the companion baseline on equal
footing with `IJSSOL_CSLAP_v1.tex`. Every step that consults the companion consults both files:

1. P1 document values: companion values are searched in both files.
2. P3 notation bridge: symbols defined in the supplement are included.
3. P4 companion overlap: supplementary content counts as inherited material.
4. P5a style measurement: the supplement's conventions are measured, and supplement-specific conventions are
   recorded separately.
5. P6/P7 supplement drafting: the extension's supplement follows the companion supplement's conventions.
6. P7/P8 overlap scan: the draft is compared against both files.
7. Citations: the manuscript may point to the companion supplement's sections, following the companion's
   own citation style.

## U7 (14 Sep 2026): votes weighted by model; Haiku excluded; Fable retried after a 12-hour window

**User message, verbatim (transcribed from speech):** "the majority vote should not be ... considered the same for each model. So Fable and Opus has the highest coefficient in the vote because those are the smartest models. Fable might be a model that might be down most of the time due to usage credits, but you still should keep trying, uh, but with a time window, let's say, uh, the agent that uses Fable fails, you should not retry with him until the next twelve hours, for example, because the usage credit is ... weekly basis and not ... hour basis. And next, uh, you should make sure that, uh, we don't use a high IQ as an model because it's not good at all. And as I said, the majority voting should not be, uh, weightless. It should have weights where Opus and Fayble have the highest weight. Sonnet has the low weight. and Haiku should not be at all present."

**Interpretation.** "High IQ" is read as "Haiku", a speech-transcription error. This agrees with the same message's "Haiku should not be at all present".

**Consequences for the run (these override plan §3 H9, §4.3, §4.4 and every seat assignment):**

1. **Haiku is excluded.** No dispatch uses the `haiku` family in any role: builder, extractor, researcher, critic, voter, confirmer, second chair, reader, referee, check author, code reviewer or probe. Earlier Haiku dispatches (seq 4, 8, 10, 14) stay in the record as history.
2. **Votes are weighted.** Each ballot carries the weight of its family: opus 2, fable 2, sonnet 1. These numbers are ORCH's implementation of "highest" and "low"; the user may change them.
   - An option wins with a strict majority of the total weight of valid ballots, meaning more than half of that total.
   - Runoffs, conservative defaults and fallbacks in §4.3 use weighted counts.
   - Ties in weight follow the existing tie-break order.
   - Every DR records the weights and the weighted tally.
3. **Fable retry window.** When a fable dispatch fails with a usage-limit or unavailable-model error, fable is marked unavailable with `retry_after` = failure time + 12 hours.
   - No fable dispatch is made before `retry_after`.
   - Once `retry_after` has passed, the next seat planned for fable is dispatched to fable again. That real dispatch serves as the probe.
   - A new failure resets the window.
   - `state.json` records the window.
4. **Minimum families.** This replaces H9's "fewer than three families". The run requires opus and sonnet, and H9 applies only if either of them is unavailable.
   - Panels still mix at least two families, and seats are drawn only from opus, fable (when available) and sonnet.
   - Every identity-diversity rule operates on these families.
5. **Seat preference (ORCH implementation).**
   - Consequential builders, critics and voters use opus, or fable when available.
   - Sonnet fills lighter roles, and roles that require a family other than opus. An example is the independent confirmer of artifacts ORCH built (DR-001 A-003).
   - Where an identity rule would have used haiku, the seat goes to another agent type from sonnet or opus under the §4.4 reseat rule.
6. **DR-001 re-tallied under U7.** Without the haiku ballots and with these weights, the outcomes are unchanged:
   - A-001 b3: sonnet 1 + opus 2.
   - A-002 b2: opus 2 against sonnet 1 for b3.
   - A-003 b: sonnet 1 + opus 2.
   - A-004 a: sonnet 1 + opus 2.

## U8 (14 Sep 2026): answer to hard stop H8-P0-001; checker fix round 3; tooling fix-round budget; no git writes

**Question asked.** Hard stop H8-P0-001 (`governance/hard_stops/H8-P0-001.md`) was raised because P0:G4 could not pass after BCL rounds seq 5/6 and seq 16/17 and targeted fix round seq 19/20. Two MAJOR findings were open, F-036 and F-038. The options offered were:
1. one more narrow fix round;
2. the same fix round, plus a fix-round budget for tooling gates;
3. accepting the checkers with disclosure.

**User answer, verbatim:** "I agree with you recommended path but to specify one thing is that you should not mess with git for now. Let's make sure we work well here and do not worry to push things in Git for now. Just do not break what was already in place here"

**Decision.**
1. **Checker fix round 3.** Fix round 3 covers F-036 and F-038, plus the MINOR findings F-037, F-039, F-040 and F-041. The check author is general-purpose/sonnet. A narrow code-reviewer/opus re-review follows.
2. **Tooling fix-round budget.**
   - Scope: a required gate that fails only because of open findings against check scripts or their fixtures, under `W/tools/`, `W/math/tools/`, `W/checks/` or `L/fixtures/`.
   - Budget: up to 2 further targeted fix rounds beyond the one H8 allows, before H8 applies, counted per phase.
   - In P0, fix round 3 is the first of these two.
   - H8 is unchanged for every evidence, claim, number, literature, mathematics and manuscript gate.
3. **No git writes of any kind until the user says otherwise.**
   - No commits: the D1 commits at the ends of P4, P7 and P9 are suspended.
   - No push.
   - No `init`, `add`, `commit`, `stash`, `checkout`, `reset` or `config`, in the project repository or in any temporary repository.
   - Agents run no git command.
   - Fixtures and tools stub git instead of running it.
   - Read-only inspection by ORCH stays allowed (`git --no-optional-locks status`, `log`, `diff`). So does the existing read-only status call inside `check_governance.py`.
4. **Nothing in place is broken.** Protected sources and the current repository state stay untouched. After every tooling round, ORCH checks HEAD, the staged index and the fixture tree for git repositories, read-only.

**Consequences for the run.**
- **Hard stop.** H8-P0-001 is resolved.
- **Addenda.** A-005 (tooling fix-round budget) and A-006 (no git writes; D1 suspended) cite `U: U8`.
- **Check at the time of the answer.** HEAD is `7b4d0a8`, there are 0 staged files, no `.git` directory exists under `.unlazy/horizon-writing/`, and there are 0 commits by the fixture identity.
