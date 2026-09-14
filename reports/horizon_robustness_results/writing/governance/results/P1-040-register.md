I built the register with 31 claims. I also wrote `claims.md`, generated from it, and `interpretation_errata.md` with 30 entries. All three are in `reports/horizon_robustness_results/writing/evidence/`.

**Checks.** The frozen checker passes on the final file ("CLAIMS TRACE PASSED (31 claims, 169 tokens)"). I also ran a separate script that applies the addendum's stricter §2 rules, and it passes too. `--schema` fails only because `requirements_map.json` does not exist yet. I ran no git command.

**Counts by type:** observation 9; scope 3; definition 3; premise 3; context 2; limitation 2; assumption 2; interpretation 2; disclosure 2; derivation 2; recommendation 1.

**Endpoint status:** predeclared primary 1; predeclared secondary 3; additional descriptive 4; exploratory 5; not applicable 18.

**Ids for the P1 step 5 rows:**

| Row | Claim |
|---|---|
| Scenario trade-off | C-01 |
| Margin reading | C-02 (primary), C-03 (secondary) |
| Mechanism | C-04 |
| Solver returns | C-05 |
| Drift | C-06 (Q-008 conditional wordings) |
| Protocol | C-07 |
| Margin rule | C-08 |
| Target and headroom | C-09 |
| Upper-only versus two-sided | C-10 |
| Model relation | C-11 |
| Band shape | C-12 |
| Savings in context | C-13 |
| Synthetic evidence role | C-14 |
| Unused tail | C-15 |
| Trapped activation | C-16 |
| Negative results | C-17 |

Claims C1–C8 of the first plan and the reviewed plan's §2 corrections are merged into the register. The remaining additions are C-18 to C-23 and C-25 to C-31, plus C-24, the scope-once paragraph.

**Values with no anchor or document value** (none is `UNAVAILABLE` in the two files; these are simply missing). Each is written in words or left out:
- the exploratory origin index;
- the upper-only tolerance, the δ of 0.01 and 0.03 in the two-sided sensitivity campaigns, and the reserved margin λδ;
- the incumbent's two-sided pass count at the exploratory origin;
- the upper-only synthetic instance count, which also stays forbidden as "29 instances";
- the exploratory-origin total-variation distances;
- breach magnitude by direction (only the worst breach and counts by direction are anchored);
- test-suite counts;
- `comp.supp.temporal.details` is `UNAVAILABLE`, and no claim uses it.

**Q-cards**
- **Q-A (E): test count.** The first plan and reviewed plan say 260 tests; handoff line 58 says 241. Decisive test: read the 13 Sep review `GATES.md` G2. Default: state no count (errata E-29).
- **Q-B (E): missing document values.** Add document values for δ 0.01 and 0.03 (`CAMPAIGN_PREDECLARATION.md:363-366`), the upper-only δ (line 62) and the exploratory origin (line 430). Default: words.
- **Q-C (J): negative-result classes.** C-17 classifies no result as a "genuine failure", which is open to challenge. Options: (a) as written; (b) classify the no-margin HIST+ACT misses as a genuine failure. Default: (a), with the BCL critics deciding.
- **Q-004 is still open.** No claim states a motivation for share targets.
