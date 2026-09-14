## Answers

**1. What does line 250 apply to?**

Line 250 applies to decision panels (ADP), not to BCL critic sets:
- It sits under §4.4's "Panels" table (line 270: "**Panels** (defaults...)").
- §4.3 is titled "Class J: adversarial debate panel (ADP)", and line 182 ("A DR without a named panel is an ADP-3 decision") ties "panel" to Class J votes.
- Decisively, line 242 lists four distinct categories under the builder rule: "panel seats, BCL critics, independent confirmers and second chairs". The plan's own taxonomy therefore treats panels and BCL critics as separate things.

P1 step 8 is a BCL-2 loop (§4.5), not a named panel.

**2. Do the two critics have the same identity under line 56?**

No. Line 56 reads: "Identity = agent type plus model family, within a phase." `results-integrity-reviewer`/opus and `general-purpose`/opus share the family (opus) but differ in agent type, so they are different identities.

**3. Which families does the P1 step 8 critic set span after the reseats?**

Two: opus and sonnet.
- Plan lines 587-589 list the critics as `results-integrity-reviewer`/opus, `scientific-reviewer`/fable (red) and `general-purpose`/sonnet (blue).
- `reseat_log.md` reseats only the second: "scientific-reviewer/fable, red-team critic of the register | scientific-reviewer/sonnet | fable unavailable...". The other two seats are not listed there, so they are unchanged.
- The set is therefore opus (results-integrity-reviewer) plus sonnet (scientific-reviewer and general-purpose).

**4. Does the plan forbid a critic from sharing only a family with the builder?**

No such provision appears in the sections I read. Line 241 says: "A builder never votes on, reviews, or confirms a fix to its own artifact." That prohibits the builder itself (the same identity) from reviewing; it does not prohibit a shared family. Since identity is agent type plus family (line 56), `results-integrity-reviewer` sharing "opus" with the builder `general-purpose`/opus is not the builder reviewing its own artifact.

**5. Verdict: FALSE.**

The premise mistakes line 250's panel-level family-mix rule, which governs ADP panels and not BCL critics (per line 242's taxonomy), for a family-match test between builder and critic that the plan never states. Even under that reading, the step 8 critic set already spans two families (opus, sonnet) after the logged reseat. And the plan does make the results-integrity-reviewer/opus seat valid: identity is agent type plus family (line 56), and the builder conflict covers only the same identity (lines 241-245), which that critic does not share with the builder `general-purpose`/opus.
