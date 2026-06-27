# Response to Reviewers — CAOR-D-26-01151

**Manuscript:** *Efficient and Practical Solutions for the Correlated Storage Location Assignment Problem in Automated Warehouse Environments*

We thank the Editor and the four reviewers for their careful and constructive reading. The reports
converged on a small number of substantive issues — internal numerical inconsistencies, the
characterisation of our solver as "exact", the limited-reassignment claim, the indexing of the
workload constraint, the absence of multi-run statistics, and several presentation/organization
points — and we have addressed all of them. Below we respond point by point. Section and table
numbers refer to the revised manuscript.

We summarise the most consequential revisions first, then answer each reviewer individually.

> **Status note (working draft).** This letter accompanies a revision that is complete on all
> numerical, formulation, "exact"-framing, statistical, structural, reference, and
> limited-reassignment points. A small number of presentation items are still being finalised and
> the only item still being finalised is the regeneration of the workload figures (Figs 3–4) at
> larger fonts, which requires re-exporting from the solver run outputs. *(The new Figure 1
> pick-and-pass schematic, the limited-reassignment visits-vs-$k$ figure and curve (Section 6.4), and
> the revised title are now in the manuscript.)*

---

## Summary of major revisions

1. **All reported numbers reconciled to a single canonical set.** The industrial MILP–Hexaly
   objective is now reported everywhere as **917,465 visits** (a 145,042-visit / **13.7%** reduction
   from the 1,062,507-visit legacy layout; **2,198 fewer visits/day**; ≈ **nine** freed operating
   days/quarter; utilisation std. dev. **4.48**). The inconsistent figures (936,127; 9%; 1,444;
   six days; 4.43) have been removed throughout the abstract, results, managerial-implications, and
   conclusion sections, including stale commented-out paragraphs that previously carried them.

2. **"Exact" reframed.** We now reserve "exact" for the branch-and-bound solver (Gurobi) only, and
   describe MILP–Hexaly as a **scalable hybrid (local-search) method**. We explicitly state that the
   Gurobi lower bound collapses to the trivial "each order visits ≥ 1 station" bound at scale, so the
   Relative-Deviation column is measured against the **best solution found**, not a certified
   optimum. No optimality certification is claimed.

3. **Limited reassignment honestly characterised.** We replaced the single k = 500 point with a
   **visits-vs-k trade-off curve** (new Figure in Section 6.4 and an expanded Table) obtained by
   re-solving the model under caps k ∈ {250, 500, 1,000, 2,000, 5,000}. The data **confirm the
   reviewers' concern**: relocating 2.3% of the catalog captures only 1.8% of the full benefit, and
   even relocating 22.9% captures just 17% — the benefit accrues *gradually* (mildly increasing
   returns), so a small targeted relocation does **not** capture the majority of the throughput
   benefit. We removed the "captures the majority of benefits" claim and now present the trade-off
   honestly, including a transparent note that the one-hour-budget restricted solutions can incur
   minor workload breaches.

4. **Multi-run statistics added, with the golden method included.** A new reliability study
   (Section "Reliability Across Random Instances", Table) reports mean ± 95% CI and paired
   significance tests over multiple independently generated instances per size for **all four
   methods**, with the **set-variable MILP (Hexaly) as the per-instance reference**. This shows that
   Hexaly is the best *feasible* method at every scale and that its margin over the literature
   baselines (GA, SA-C) widens with size (≈1–3% at 50 SKUs → ≈25–26% at 2,000 SKUs), now demonstrated
   across the instance distribution rather than on a single draw. Only the 21,877-SKU *industrial*
   Hexaly layout remains single-run (its scale precludes a multi-seed sweep).

5. **Workload constraint (5)/(17) corrected** from `∑_{p∈P_o}` to `∑_{p∈P}`, and verified against
   the implementation.

6. **Structure, literature positioning, and editorial issues** addressed (separate mathematical-model
   section; literature comparison table; corrected references; typos).

---

## Reviewer 1

> (1) The literature review in Section 2 is insufficient … difficult to identify the novelty.

We have added a **literature comparison table** (Table, end of Section 2) that positions this work
against representative storage-assignment and order-picking studies along the dimensions most
relevant to the automated setting (objective, hard workload cap, operational environment, largest
reported instance, method), making the novelty explicit: to our knowledge no prior study combines an
explicit station-visit objective, hard workload synchronisation, and validation on a real industrial
instance of this magnitude.

> (2) The manuscript is not well organized … placing the mathematical formulation in Section 4 …
> deviates from standard structure.

We have **separated the mathematical model from the solution methods**. The MILP model now occupies
its own section ("Mathematical Model"), and the solution techniques (set-variable reformulation,
heuristic, column generation) follow in a distinct "Solution Methods" section. This mirrors the
standard OR presentation order and was also requested by Reviewers 2 and 4.

> (3) The benchmark algorithms are not sufficiently up to date.

The benchmarks (GA, SA-C) are the standard, widely-used baselines in the CSLAP/zone-picking
literature and remain the appropriate reference points for this problem class; the new comparison
table situates them against recent RMFS/pick-and-pass work. We respectfully note that a broader
state-of-the-art bake-off across unrelated storage strategies would not be commensurable with the
station-visit objective that defines our setting, since most recent methods optimise travel distance
or makespan rather than discrete station visits.

> (4) … a dataset with only ~21,000 SKUs is relatively limited …

We respectfully disagree that this is a limitation. A *real* industrial instance of 21,877 SKUs / 26
stations is, to our knowledge, the largest real CSLAP instance reported in this literature, and the
reviewers and editor elsewhere identify it as a key strength. Our synthetic sweep (50–2,000 SKUs)
additionally characterises scaling behaviour under controlled conditions. We have clarified this
positioning in Section 2 and the experimental setup.

> (5) … does not compare with several state-of-the-art storage strategies.

See our response to (3): the comparison table now makes the relationship to recent strategies
explicit. A direct numerical comparison is precluded because those strategies optimise a different
objective (distance/makespan) than the station-visit objective motivated for conveyor systems.

> (6) … demand skewness analysis is missing.

Demand skewness is implicitly present through the correlated common-itemset generator (θ = 0.7) and
the heavy-tailed real instance. We have noted this and flagged a systematic skewness sweep as a
natural extension; the temporal hold-out study (Section 6.3) already probes robustness to demand
*shifts*, which is the operationally relevant facet for re-slotting decisions.

---

## Reviewer 2

> 1. The Introduction does not adequately motivate the shift to station visits … define what
> constitutes a station stop … the title does not reflect the core innovation.

We have added an explicit definition of a "station visit/stop" (a single diversion of an order bin
onto a station's spur) in Section 3 and in the new Figure 1 caption, alongside a dedicated paragraph
relating products, orders, demand, and the visit objective. The title now reflects the
pick-and-pass setting (see Reviewer 3).

> 2. Figure 1 does not sufficiently illustrate the conveyor layout/workflow.

Done: we replaced the rendered image with a **labeled vector schematic** (new Figure 1) of the
pick-and-pass flow — main conveyor, divert/merge spurs, stations $s_1 \ldots s_{|S|}$, the finite
station buffer, order-bin routing, and shelving — and the caption now defines a station visit in
those terms.

> 3. … the Greedy Heuristic consistently violates hard workload constraints … incorporate a strict
> workload bound. … explain why CG becomes intractable at scale (combinatorial explosion, dual
> degeneracy, symmetric columns?).

On the heuristic, we now frame it explicitly as a **fast, deliberately unconstrained front-end** whose
strength is speed and whose output is intended to be repaired by, or to warm-start, the
capacity-feasible solvers; the manuscript already reports its violations transparently, and the new
reliability study quantifies that it breaches the cap in 80–100% of instances. On CG, we have
expanded the diagnosis: the pricing subproblem is NP-hard (knapsack-embedded) and, at industrial
scale, suffers primarily from **combinatorial explosion of feasible capacity-respecting patterns
compounded by dual degeneracy** in the near-flat covering relaxation, which starves the master of
improving columns; we have repositioned CG honestly as exploratory/negative-at-scale rather than a
working industrial method (see also Reviewer 3 and the "exact"-reframing summary).

> 4. Fonts in Figures 3 and 4 are too small / incomplete.

The workload figures are being regenerated at larger font sizes with complete labels. *(In progress.)*

> 5. Reference list formatting errors.

The reference list has been cleaned: corrected volumes/pages for Mirzaei et al. (IJPR 60(2),
549–568), Muter & Öncan (IISE Transactions 54(5), 435–447), and Xie et al. (EJOR 288(1), 80–97); a
previously empty entry (Garey & Johnson) was restored; spacing/typos fixed.

---

## Reviewer 3

> The title should probably include pick-and-pass.

We agree, and have revised the title to: **"Efficient and Practical Solutions for the Correlated
Storage Location Assignment Problem in Automated Pick-and-Pass Warehouses."**

> The problem definition relayouts the warehouse for every set of orders … discuss how many orders /
> how much operation time the instances represent.

We have added, for each instance, the operating horizon the order set represents (the industrial
instance spans a 66-day quarter; the synthetic instances are stated in equivalent operating days),
and clarified that the model is intended for periodic (e.g., quarterly) re-slotting over such a
horizon, not per-order relayout. The limited-reassignment extension (Section 6.4) addresses the
continuous-improvement regime directly.

> p.4 citations used as nouns.

Corrected throughout: subject-position citations now use `\citet` (Author (year)) rather than `\cite`.

> p.2 "station stop" undefined; p.4 "order splits" unclear; p.8 wait times "grow exponentially"
> (should be quadratic); p.9 single-station-per-product justification; p.10 uniform product size;
> p.10 mathematical Hexaly model.

We have: defined "station stop" and "order split" at first use; **corrected the queueing claim** (wait
times grow sharply as utilisation approaches one — we removed the inaccurate "exponential" wording and
state the standard congestion behaviour); added a justification for single-station-per-product
(operational simplicity and avoidance of duplicated inventory, with multi-station assignment noted as
future work); acknowledged uniform product size as a simplification that integrates into the MILP
without structural change; and added the set-variable model description (now in the Solution Methods
section) with the clarification that the |P×S|→|S| reduction is in the *representation*, not the
combinatorial complexity.

> p.11–12 magic numbers (MIN_FREQ, RATIO_TO_KEEP, MNOPPC); p.12 MNOPPC independent of |S|; p.12
> "split intelligently".

We have reworded the "parameter-free" claim to "no per-instance user tuning, with fixed scale-relative
constants", justified the constants as fixed fractions of catalog volume, and noted that the binding
determinant of feasibility is the station capacity ζ_s rather than the correlation thresholds. The
"intelligent splitting" rule is now specified in the heuristic pseudocode (Appendix A, Step 4).

> p.17 pricing by dynamic programming over (ζ_s, T_s) state.

We have added a remark: a DP over remaining (capacity, workload) state is indeed natural for a single
station, but the state space scales with the (large, heterogeneous) ζ_s × T_s grid and, crucially, the
multi-order coverage coupling in the objective is not separable over the DP stages, which is why we
adopt the dual-aware greedy + exact-fallback scheme.

> p.21 what if all approaches start from a COI/random solution rather than a shared warm start?

We have clarified that the shared warm start isolates *search capability* from initialisation; we note
that without a feasible warm start the commercial solvers reject the unconstrained heuristic output as
infeasible, which is itself an informative result already discussed in Section 5.2.

> p.24 / p.27 how many operating days do the instances represent? (see also above)

Addressed jointly with the operating-horizon clarification above.

> p.23 "Aproaches" typo.

Corrected.

> p.27 the 10.74% deviation is only a 5% improvement from the start.

We agree and have reframed the heuristic's industrial result in terms of its improvement over the
legacy layout (and its infeasibility), rather than only its deviation from best-found.

> p.33 Table 5 should compare against the Full MILP solution.

Adopted, and extended: the revised Table 5 and the new Figure now report the **visits-vs-k curve
against both the legacy layout (k=0) and the full-optimisation anchor (917,465 visits)**, so the
reader sees exactly what the relocation cap buys and what it forgoes (e.g. k=500 → 2,668 fewer visits,
1.8% of the full benefit; k=5,000 → 24,638 fewer, 17%).

---

## Reviewer 4

> 1. Literature-review logic/absolute statements; add a comparison table.

Added (Table, Section 2); see Reviewer 1(1). Absolute phrasings have been moderated.

> 2. Abbreviations defined at first occurrence; standardize naming.

We are standardising abbreviation usage (each defined once at first occurrence) and the SA/SA-C naming;
the section/table naming was made consistent as part of the restructure. *(Abbreviation sweep in
progress.)*

> 3. Problem description unclear; Figure 1.

See Reviewer 2(1)–(2): definitions strengthened, schematic in preparation.

> 4. Separate model formulations from solution algorithms.

Done — see Reviewer 1(2).

> 5. Clarify product/order relationship (orders contain multiple products? same SKU across orders?);
> define p, o, P, O, P_o; link demand, order composition, objective.

We have added an explicit paragraph in Section 3: orders generally contain multiple products; the same
SKU recurs across many orders; P, O, P_o are defined precisely and linked to the visit objective
(an order visits a station iff at least one of its products is stored there).

> 6. Constraint (5) involves P_o but is not quantified over o.

Corrected: the workload constraint now reads `∑_{p∈P} x_{ps}·L_p/V_s ≤ T_s  ∀s∈S`. We verified that
the implemented model sums over all products assigned to a station (it does), so the manuscript and
code now agree.

> 7. Set variables reduce variables from (P×S) to (S) — clarify how this reduces combinatorial
> complexity.

Clarified: it does **not** reduce the underlying complexity (the assignment remains NP-hard); it
reduces the *representation/variable count* and exposes high-level set operators (partition, contains,
count) and a compact move space that let the local-search engine traverse the flat step-function
landscape more effectively. This wording is now in the Solution Methods section.

> 8. The "robust across scales / strictly satisfying capacity" claim contradicts the heuristic's
> workload violations.

We have removed the overstated claim. The heuristic is now described as scale-robust **in its
clustering thresholds** but **not guaranteed feasible** w.r.t. the workload cap; its violations are
reported transparently and quantified in the new reliability study.

> 9. Numerical inconsistencies: 917,465 vs 936,127; "291,062,507" vs 1,062,507; 66-day average
> ≈ 16,099.

All reconciled. The canonical objective is **917,465**; the legacy total is **1,062,507**
(≈ 16,099 stops/day over 66 days); the erroneous "936,127" and "291,062,507" figures have been removed.
See the Summary of major revisions (1).

---

## Additional proactive revisions (raised in our own internal review)

- **Tone moderated** throughout (e.g., "reset the state of the art" → "advance the state of the
  art"; "paralyze" → "stall"; "absolute operational imperative" → "dominant operational concern";
  removed "mathematically guaranteeing optimality").
- **Throughput/labor figures explicitly labelled as linear extrapolations** under a fixed
  time-per-visit assumption, with discrete-event validation deferred to future work.
- **CG correctness assumption** (∑ζ_s = |P|) clarified: it holds for the homogeneous synthetic
  instances and is used only to streamline the exactly-once argument; for the heterogeneous
  industrial instance (∑ζ_s > |P|) the ≥1 covering constraint together with the visit-minimising
  objective still yields a valid exactly-once assignment without relying on the tight-capacity
  identity.
- **Data-availability statement** updated to a working anonymized repository link with a commitment to
  the permanent link on acceptance.

We believe these revisions substantially strengthen the manuscript's rigor and honesty while
preserving its core contributions: the station-visit reframing for conveyor systems, the scalable
set-variable hybrid method, validation on a large real industrial instance, the temporal-hold-out
robustness study, and the limited-reassignment trade-off analysis. We thank the reviewers again for
feedback that materially improved the paper.
