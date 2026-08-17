# Action plan: reconciling `IJPR_CSLAP_v2.tex` to the author's ground truth

Supersedes the earlier comparison report. Decisions below are the author's, taken
2026-08-11. Nothing in this plan has been applied to the article yet.

**Authoritative initialisation (author-supplied; the runs that produced the published
numbers are no longer in the repository, so the code is *not* the reference here).**

| Method | Synthetic benchmark | Industrial (Company A) |
|---|---|---|
| SA-C | own COI initialisation | original layout |
| GA | random feasible population | original layout |
| Set-partitioning CG | **LPT** | original layout |
| Binary MILP | **LPT** | original layout |
| Set-variable MILP | **LPT** | original layout |
| Clustering heuristic | **LPT** | original layout |
(intent was always a coherent feasible starting referent layout (which we call legacy and that is accurate for the industrial which refers to the original placement from company A while for the synthetic should be the LPT on our methods))

Other decisions: keep the v2 community-bound rule and add C&OR's mega-cluster rationale as
its motivation; drop the Gurobi/engine variants entirely with no acknowledgement (verified:
the tex contains **zero** Gurobi mentions, so no edit is needed); keep the set-variable MILP
as the comparison reference.

---

## Part A — Article edits, in execution order

### A1. Create a dedicated initialisation subsection, and define LPT in it

**Why first:** LPT is currently used four times before it is defined — introduction
(l. 96), §4.1 (l. 309), Algorithm 1 (l. 414) — and defined only at §4.4 (l. 481). Every
later edit depends on there being one authoritative place that says what LPT is and who
gets it.

**Action.** New subsection at the end of §4, before §4.4's baseline material, titled
*Initialisation and warm start*. It must contain, in this order:

1. **The LPT construction, in full.** Products sorted by descending order-line frequency,
   each assigned greedily to the station with the lowest accumulated workload; the sweep
   respects both $\zeta_s$ and $T_s$, so the result is feasible by construction and can be
   supplied to a solver as a valid incumbent. Note that it ignores correlation entirely,
   which is what makes it usable both as a warm start and as the correlation-blind anchor
   reported in Table 4.
2. **The per-method table above**, stated as a table or a tight list.
3. **One sentence on why the industrial case differs**: every method starts from the layout
   the site operates, so a reported reduction is measured against the configuration in use.

**Cross-references to repair once this exists:** l. 96 (introduction), l. 309 (§4.1
incumbent sentence — see A2), l. 414 (Algorithm 1's "LPT partition of $P$ over $S$
(Section~\ref{sec:baselines})" pointer), l. 481 (delete the now-duplicated definition).

### A2. Clearance of MILPs
We express the 2 MILP approaches currently in our draft article "IJPR_CSLAP_v2.tex" as 2 different methods where in fact they should foll under 1 category which is mathematicl model formulated as a mixed integer linear programming model and solved through commercial solvers like Hexaly in our case. The only thing that changes is 2 variants of presenting the MILP model to the soler which is through binary/contious decision variables and set decision variables (which is just a specific feature of the Hexlay solver) and it is not that we have constructed 2 different models, but the reframing we mention to set decision variables is just a feature of this specific solver (which also should be refered through ciying the specific source that explains this feature on the solver), and this formulation makes use of new math abstractions that the solver has to make it easier to construct based on the set decsion variables. The respective reference of this feature to use if it is not already part on our IJPR_CSLAP.bib is:
```
\bibitem[(Blaise, Hexaly)]{blaisemodeling}
Blaise, L., n.d. Modeling scheduling problems with Hexaly. Hexaly, 251 Boulevard Pereire, 75017 Paris, France.
```

### A3. Replace the current §4.4 initialisation paragraph

The paragraph beginning *"On the synthetic benchmark each method starts from its own
prescribed initialisation…"* asserts the opposite of the ground truth for three methods. It
must be replaced, not patched: under the ground truth the MILPs (this MILPs are one method but put into the solver into 2 different variants), Heuristic and the CG **do** receive a
common LPT start, so the sentence *"Forcing a common start would depart from Kim & Smith and
Zhang et al. rather than reproduce them"* is also wrong and must go.

Replacement logic: the three optimising methods share the LPT start so that any quality
difference isolates the search rather than the initialisation; the two literature baselines
keep the initialisation their own sources prescribe, because reproducing them faithfully is
the point of including them.

### A4. Explain COI and the GA's random population

Both are named but never explained. Add to the nAppendix D and refer it there:

- **COI (cube-per-order index):** products ranked by demand volume per unit of storage
  occupied, then filled into stations in that order — the classical storage rule that
  \citet{kim2012} start from. It is correlation-blind in the same way LPT is, but ranks on
  a different quantity (volume per slot rather than line frequency).
- **GA random feasible population:** each of the 50 initial members is drawn by assigning
  products to stations uniformly at random subject to the slot capacity, so the population
  spans the feasible region rather than a neighbourhood of one layout, as \citet{pan2015}
  prescribe.



### A5. Restore the mega-cluster rationale as the community bound's motivation

**In §4.1**, attach a reason to $\beta$ rather than presenting it as a bare formula: a
community is placed as a block, so the bound exists to keep blocks within the physical
geometry of a picking zone and to prevent operationally infeasible over-large clusters.
This is C&OR's (C&OR_CSLAP.tex) justification and it remains correct.

**In §6**, connect it to the measurement explicitly. Suggested substance: the rule sets
$\beta$ from a single capacity, which presumes interchangeable stations; on a site whose
stations hold between 8 and 2,575 products it yields $\beta = 266$, a block no small station
can accept — the failure mode the original bound's clamp was designed to prevent, here
reached empirically. Then the measured evidence: feasibility is not an interval across the
nineteen values tried, and only one of seven grid points is feasible.

This is the single highest-value narrative addition in the plan: it converts the industrial
limitation from an admission into an explained result.

### A6. Restore named roles on the three method subsections

Retitle §4.1–§4.3 on the C&OR pattern, but with roles that are true of the current methods
(the old "operational agility" rested on a soft workload cap that no longer exists):

- Set-variable reformulation → *strategic optimization*
- Greedy clustering heuristic → *fast feasible layouts*
- Set-partitioning column generation → *decomposition with a valid bound*

Keep the §4 opener as it now stands (same problem, differing in what each gives up); it is
consistent with these labels.

### A7. Attach a rationale to each threshold in §4.1

Each of $\phi$, $\gamma$, $r$ currently appears as a formula with a one-line gloss. C&OR
gave each a purpose (noise floor at 1% of catalogue volume; significance floor at 2%;
confidence filter against ubiquitous endpoints). Restore that, briefly.

### A8. Critical Assessment of the Current Appendix Architecture

Proposed Restructuring OptionsOption 1: The Three-Domain Macro-Appendix Strategy (Recommended)Regroup the six sections into three cohesive, domain-specific appendices:Appendix A: Algorithmic Specifications and Implementation DetailsA.1 Pseudocode for Greedy Product Clustering (former App A)A.2 Incremental Evaluation of Swap Local Search (former App B)A.3 Baseline Metaheuristic Parameterization (former App E, excluding hardware/seeds)Appendix B: Calibration and sensitivity of the heuristic's thresholdsB.1 Community Bound Calibration ($\beta$-sweep) (former App C)B.2 Threshold Sensitivity of the Clustering Heuristic (former App D). Here some edits are needed and we should not get directly as they were the App C and App D
This is the main goal of this appendix whhich will have two parts: first the calibration (why β = 0.4ζ, on the geometry family), then the sensitivity (are all four robust at those settings, on the benchmark family), and a single sentence up front explaining why two families are needed. That removes the reader's confusion, which is the real problem you spotted, without discarding either piece of evidence.
Appendix C: Mathematical Proofs of Lower BoundsC.1 Linear Relaxation Floor of the Binary MILP (former App F)C.2 Farley-Type Dual Bound for Column Generation (former App F)Rationale: This maintains a strict logical separation between Algorithms, Empirical Tuning, and Mathematical Proofs, reducing section count by 50% without losing a single equation or table.
```
\appendix
\section{Algorithmic Specifications and Local Search Details}\label{app:algo_details}

\subsection{Greedy Product Clustering Pseudocode}\label{app:heuristic}
% Consolidated Algorithm 1 block...

\subsection{Calibration and sensitivity of the heuristic's thresholds}\label{app:swapeval}
% Formerly Appendix B paragraph...

\subsection{Metaheuristic Baseline Parameters}\label{app:baselines}
% GA and SA-C parameter details (hardware details moved to Sec 5.2)...

\section{Empirical Parameter Calibration and Sensitivity Analysis}\label{app:calibration}

\subsection{Community Bound Scaling ($\beta$-sweep)}\label{app:capsweep}
% Table C.1 (former Table 5) and scaling narrative...

\subsection{Threshold Sensitivity Analysis}\label{app:sensitivity}
% Table C.2 (former Table 6) and threshold sensitivity text...

\section{Mathematical Proofs of Bounding Claims}\label{app:bounds}

\subsection{Binary MILP Linear Relaxation Floor}
% Proof text for LP relaxation...

\subsection{Column Generation Farley-Type Dual Bound}
% Proof text for CG bound...
```

### A9. Sweep for consequential knock-on claims

After A1–A8, re-check every sentence that depends on initialisation:

- l. 96 introduction — "improve substantially on the correlation-blind LPT anchor" now needs
  to be consistent with LPT *also* being their warm start (a method that starts from LPT
  improving on LPT is a different statement from one that beats it from scratch).
- §5.3 "Both literature baselines trail" — the attribution to the objective rather than to
  tuning must survive the fact that the baselines now start from a *different* place than
  the three optimising methods. This is a real confound and should be named as one.
- Appendix D's GA and SA-C paragraphs — already corrected to random/COI; verify they match
  the new subsection word for word.

### A10. Simplify the column-generation narrative — style only, method unchanged

**Hard constraint on this item.** The method stays exactly as it is. The aggregated master,
the single persistent pricing model, the price-and-complete drive and the Farley bound are
the current work and produced the current results. Nothing from C&OR's CG section is to be
imported as content. What is borrowed is only how that content was *sequenced and paced*.

**Diagnosis — why §4.3 is hard to follow.** The subsection is not too technical; it is
told three times. §4.3.4 currently narrates the same four stages in three different
structures, one after another:

1. a `description` block defining four operators (\textsc{GreedyPrice}, \textsc{ExactPrice},
   \textsc{Complete}, \textsc{Descend}),
2. two algorithm floats carrying the pseudocode, and
3. an `itemize` explaining what each of the four stages does,

and then two further list structures for the feasibility mechanism. Five list environments
in one subsection, with the operators introduced far from the stage that uses them, is what
makes the reader lose the thread — not the mathematics.

**What C&OR did better, and is worth copying.**

- *Name the obstacle, then the fix, in that order.* C&OR opens the matheuristic subsection
  with "A cardinality-tight partition master does not advance on isolated columns", explains
  why in two sentences, and only then introduces the coordination mechanism. v2 has the same
  material but interleaves it with the operator definitions.
- *End each subsection by saying what it buys.* C&OR closes the station-indexed master with
  "This station-indexed master is exactly the formulation we run on the heterogeneous
  industrial instance." Every subsection tells the reader where that piece is used. v2 does
  this in some subsections and not others.
- *Keep the reassurance numbers inline.* C&OR states the support count, the one-off model
  build cost and the first solve time at the point where the reader would otherwise wonder
  whether exact pricing is affordable. v2 carries most of these but places them late.
- *One idea per paragraph, no nested lists.* C&OR's subsections are prose with at most one
  list; v2's drive subsection is mostly lists.

**Actions.**

1. **Fold the four operators into the stage that uses them.** Delete the standalone
   `description` block and introduce each operator once, inside the stage description where
   it acts. \textsc{Descend} is used by Stages 1, 2 and 4, so define it first and refer back.
2. **Merge the two algorithm floats into one**, or apply the `\addtocounter{algorithm}{-1}`
   + "(continued)" pattern that Algorithm 3/4 already uses correctly. As it stands the two
   floats share a caption, only the second is labelled, and §4.3.4's cross-reference points
   at a float containing only Stages 2–4.
3. **Absorb the feasibility discussion into Stage 2.** The penalty rate $\rho$ and the
   explicit gate are properties of how the loop admits a completion; stating them where the
   loop is described removes a whole list and a backward reference.
4. **Split §4.3.5 into two paragraphs with distinct jobs**: what the bound *is* (construction
   plus formula), and what it does *not* certify (the returned layout). These are currently
   interleaved, which is why the scope caveat reads as a retraction rather than a
   clarification.
5. **Add a closing sentence to each of §4.3.1–§4.3.3** naming where that piece is used —
   station-indexed on the industrial site, aggregated on the synthetic family, one pricing
   model for both.
6. **Target: no subsection with more than one list environment.**

**Verification for this item.** Word count must not rise (the aim is fewer words, not more);
no equation, symbol, algorithm line or number may change; and §4.3 must still state the four
stages, the two masters, the single pricing model and the bound. A reader should be able to
answer "what does each stage do, and why is there a stall to fix?" after one pass.

### A11. Notation-consistency audit across body and appendices

Two things to check, one already clean.

**Already verified clean — record and move on.** The pattern-selection dual and the pattern
index were migrated correctly: `\mu_s` appears 5 times and `\pi_s` never; `y_{sq}` 5 times
and `y_{sk}` never; `q \in K_s` 4 times and `k \in K_s` never. The convexity rows
\eqref{eq:convgen} and their dual $\mu_s \le 0$ are consistent between the master, the
pricing reduced cost and Appendix F's bound derivation. No action needed.

**Genuine collision to fix — $\zeta$ carries two meanings.** The notation table defines
$\zeta_s$ as the number of storage locations at station $s$. The community-bound rule
introduced in §4.1 uses a bare $\zeta = |P|/|S|$ as a single scalar. A reader meeting
$\zeta$ in the $\beta$ formula has to infer that it is the common value of $\zeta_s$ under
interchangeable stations. Fix by either adding $\zeta$ to the notation table with that
definition, or writing the rule as $\beta = \max(5, \lfloor 0.4\,\bar{\zeta}+\tfrac12\rfloor)$
with $\bar{\zeta}$ defined once as the common slot capacity. This matters because $\beta$ is
now a load-bearing methodological claim and a referee will read the formula closely.

**Sweep to run once the edits are done.** For every symbol introduced in the notation table,
confirm it is used with one meaning throughout body, algorithms and appendices; and for
every symbol used in an appendix, confirm it appears in the notation table or is defined at
its first appendix use. $\Pi$/$\Pi^{\ast}$, $\rho$, $c_q$, $\sigma_p$, $w_u$ and $U$ are the
ones most likely to have drifted, since they span §4.3, Algorithm 1 and Appendix F.

---


## Part B — Remote actions on the anonymised data repository

The repository currently holds **only the 29 benchmark instances**. The article as it now
stands promises more than that.

| # | Action | Why it is needed |
|---|---|---|
| **R1** | Upload the **80 calibration instances** (EXP-02c), or the generator plus the station counts and seeds 2001–2010 that regenerate them exactly | The Data Availability Statement now names them, and they carry the sole justification for $\beta = 0.4\zeta$. Without them the coefficient is an assertion |
| **R2** | Upload `synthetic_data_zhang.py` with the exact settings for **both** families — correlation 0.7, order size $U[5,15]$, subset fraction $U[0.1,0.5]$, and the station-count rule used per family | Both families are said to be reconstructible "exactly"; that requires the generator, not just seeds |
| **R3** | Upload the **sensitivity-sweep configuration** behind Appendix C — the 19 configurations, the multiplier convention (applied post-clamp), and the per-size caps | Appendix C reports a 667-evaluation study whose design is currently described only in prose |
| **R4** | Add a repository README mapping each article table and figure to the artifact that produces it | Closes the last gap between "the data is available" and "the reader can find what backs a given claim" |
| **R5** | Verify the 29 instances in the repository still match the pinned hashes in `hash_manifest_v3.txt` | The article's reproducibility rests on those instances being byte-identical to the ones benchmarked |

The industrial dataset stays out, as now — commercially confidential, available on
reasonable request, as does the dated extract behind the temporal hold-out.

---

## Part D — Verification after the edits

1. **LPT defined before first use.** No occurrence of "LPT" before the new subsection except
   in the introduction, and that one pointing forward.
2. **One initialisation statement.** The per-method assignment appears exactly once; §4.1,
   §4.4, Appendix D and Algorithm 1 all defer to it rather than restating it.
3. **No surviving contradiction.** Grep the four locations listed in A8 and confirm each
   agrees with the new subsection.
4. **Numbers untouched.** None of A1–A8 changes a result. If D1-b is chosen, the heuristic
   rows change and Gate 1 (numerical integrity) must be re-run in full.
5. **Word budget.** A1, A3, A5 and A7 all add text. Measure the main-text count on Overleaf
   before and after; the abstract is currently 196 of 200 and the main text is the tighter
   constraint.
6. **Display items.** Unchanged at 14 of 15 unless the per-method initialisation is set as a
   table, which would take it to 15 of 15 — a list is the safer form.
