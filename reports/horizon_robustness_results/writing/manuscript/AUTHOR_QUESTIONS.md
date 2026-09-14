# Author questions

Questions raised while drafting the manuscript, updated after review round 1. The files covered are
`main.tex`, `supplement.tex` and `sections/01_introduction.tex` to `sections/07_conclusion.tex`. The
results were reused, not revalidated, during writing. No new computation was made, and no evidence
file was edited.

**Contradictions between sources.** No concrete contradiction between two accepted sources was
found in passes 1 to 2b or in the round 1 revision. The items below are missing inputs, open cards
and editorial placements that need author confirmation.

## 1. Motivation for a share rule instead of workload budgets (card Q-004, unresolved)

- **Where:** introduction, paragraph 2, marked `% AUTHOR-CONFIRM`.
- **Sources:**
  - Q-004 has no resolution line.
  - Its conservative default (a) says to motivate only from documented sources and to mark
    site-specific claims.
  - Documented sources:
    - the companion's budget definition (`IJSSOL_CSLAP_v1.tex:584`, document value
      `comp.budget.definition`);
    - the user's statement of the business rule, "every station stays within ±δ of its
      historical share" (`EXPERIMENT_REVIEW_HANDOFF.md` §2, line 115).
- **What the draft does now:**
  - It motivates the rule from the companion's queueing argument and from the fact that shares need
    no absolute workload level.
  - It presents the rule as the rule studied.
  - It does not claim that Company A operates to it.
- **Question:** does Company A state its workload policy as a share band? If not, how should the
  article describe where the rule comes from?

## 2. Citation of the submitted companion

- **Where:** `references.bib`, entry `belul_companion` (`@unpublished`, note "Submitted
  manuscript").
- **Question:**
  - Confirm the author list and title, copied from `IJSSOL_CSLAP_v1.tex` lines 50-56.
  - Give the year to cite (left empty).
  - Say whether the venue and any related-manuscript disclosure should be named.
  - The draft never describes the companion as published.

## 3. Description of the freeze rule and the large-order filter

- **Where:** main text Section 4.1, paragraph 2; Supplementary Section S4.
- **Sources:**
  - Companion main text, line 576: products "appearing in at most five orders".
  - Companion supplement, lines 530-532: at most five orders *and* at one of the three
    static-shelving stations.
  - `DATA_PROVENANCE.md` line 27: a large-order entry-frequency rule with a one-product edge case.
- **What the draft does now:**
  - It cites the companion's rule and says the loader takes the frequency count over large orders.
  - It says the filter selects only the movable pool.
  - It describes the one-product edge case in S4 without counts.
  - Supplementary Section S4 carries the marker `\authorreview{value: definition of a large order ...}`.
- **Question:** is this description acceptable, and what is the definition of a large order?

## 4. Software, representation and time limits of the solves

- **Where:** Section 4.3; Supplementary Section S1.
- **What the draft does now:** it gives only the accepted values for the held-out solves: Hexaly, one
  thread, 1,800 s per solve, 12 solves, 21,600 s configured, and the gap and bound of each solve.
- **Markers:**
  - Section 4.3 (added in review round 1, items B6 and B7):
    `\authorreview{value: solver, model representation and per-solve time limits of the exploratory
    campaigns, and the model representation of the held-out solves ...}`.
  - S1: `\authorreview{value: returned training objective, measured solve and build times, solver
    version and hardware ...}`.
- **Question:** which of these should be reported? Each needs a document value first.

## 5. Supplement values without an accepted source

The main text points to supplement sections by name (S1 to S6), and no cross-document package is
used. The supplement leaves visible `\authorreview{value: ...}` markers where it would need values
that are not anchors or document values:

- S1: returned training objectives, timings, solver version and hardware (see item 4).
- S4: definition of a large order (see item 3).
- S5.1: upper-only synthetic outcomes by catalogue-size stratum, arm and horizon, with paired
  outcomes, scored and non-returned denominators, and the synthetic instance count.
- S5.2: per-cell outcomes of the two-sided screen on the four synthetic warehouses, including the
  cells with no returned layout.
- S5.3: per-horizon breach counts by direction, worst breaches and visits of the Company A
  two-sided campaigns at δ = 0.01, 0.02 and 0.03.
- S6: exploratory-origin total-variation distances of the historical blocks and of the scored
  futures.

**Question:** which of these should be reported? Each needs an anchor or document value first. If
none is wanted, the markers and the corresponding sentences can be removed.

## 6. Placement of the scope paragraph (decided by the integrator; reversible by the authors)

- The scope paragraph stays as the last subsection of Section 4 (`subsec:scope`), immediately before
  Results.
- The first paragraph of Results points to it.
- The second statement required by claim C-24 opens Section 6.5 (`subsec:limitations`).

## 7. Placement of the HIST+ACT limitation (decided by the integrator; reversible by the authors)

- The classified limitation (DR-002 option d) is under "Empirical limitations" in Section 6.5.
- It keeps all five reviewer-first answers and marks the explanation as hypothetical.
- Its values now point to Tables 3 and 5 instead of being repeated.
- Results §5.1 keeps the NOM control contrast, with a clause pointing to Section 6.5.

## 8. Order dates at the site (claim C-25)

- **Where:** Section 4.1, paragraph 1, marked `% AUTHOR-CONFIRM`.
- **Question:** do order dates exist operationally at Company A? The draft treats order-identifier
  chronology as an assumption, and the dated protocol as deferred, not disproved.

## 9. Title, authors, abstract and declarations

- **Title:** the working title in `main.tex` and `supplement.tex` is now "Station workload shares
  after re-slotting a pick-and-pass warehouse: a held-out comparison of reserved margins and
  historical scenarios" (review round 1, item B9).
- **Abstract:** revised against the finished argument. The historical-variation check was removed
  from it (item B1).
- **Author block:** remains an `\authorreview` marker.
- **Declarations** follow the conclusion as `\authorreview` placeholders with `% AUTHOR-CONFIRM`
  comments:
  - data availability;
  - funding;
  - competing interests;
  - author contributions.
- **Use of generative AI:** the statement says that the manuscript text was drafted with generative
  AI assistance under the authors' direction. A marker asks the authors to confirm the wording, name
  the tools and state their review and responsibility.
- **Question:** complete these once a venue is chosen.

## 10. Cross-references

All section labels now exist, including `sec:related`, so the introduction's roadmap resolves. The
introduction's literature markers were replaced by verified citations in review round 1.

## 11. Definitions of "complete order" and "order-retention rule" (new, review round 1 item B7)

- **Where:** Section 3.1, two `\authorreview{definition: ...}` markers.
- **Sources:** the accepted sources use both terms but define neither.
  - `DATA_PROVENANCE.md` line 14 lists "Complete retained orders".
  - `MATHEMATICAL_SCOPE.md` §8 says that the retention rule is reconstructed from the whole export and
    can affect which historical lines survive.
- **What the draft does now:** it describes the order-retention rule only as the loader's rule for
  which order lines, and hence orders, are kept, reconstructed from the whole export and possibly
  dependent on later orders.
- **Question:** give the loader's criterion for a complete order and the criteria of the
  order-retention rule, so that each can be defined in one sentence.
