# Closed-catalogue, order-horizon robust CSLAP: study plan

Revision: 1.0, 2026-09-08. Status: proposed protocol, ready for joint review.

This document specifies the proposed research and its implementation sequence. It does not report new experiments, establish that the proposed method works, or authorize an experiment campaign. Implementation, smoke solves, and empirical runs remain deferred until the user approves the relevant stage. The companion [AGENT_HANDOFF.md](AGENT_HANDOFF.md) is the execution contract; [GATES.md](GATES.md) measures completion of this planning task only.

## 1. Decision and intended contribution

Pursue the undated, chronologically ordered path first. At a deployment origin, observe the historical orders, allocate the entire known catalogue, and keep that allocation fixed while the next **n complete orders** arrive. Assess the aggregate station workload shares over those n orders. Study several declared values of n, rather than presenting one arbitrary block size as universally correct.

The proposed contribution is a horizon-indexed extension of CSLAP: the trade-off between station visits, an explicit workload-share ceiling, and protection against specified changes in demand composition. Dates are not required to define this decision problem. Reliable sequence is required. Calendar duration, daily throughput, staffing, queues, and peak-within-window protection are not inferred from an order-count horizon.

Use a deliberately small first model family: historical n-order demand scenarios, augmented by a separate allowance for demand activation among historically inactive but already-known products. Its robust counterpart is finite and exact. Whether this family protects future workload better than nominal optimization or ordinary tightening is a hypothesis, not a premise. Do not promise a new general-purpose robust-optimization theory or publishability before examining that hypothesis.

The dated path remains a documented fallback. It is not an automatic response to a negative result; Section 11 distinguishes reasons for failure.

## 2. Non-negotiable modelling assumptions

### 2.1 A closed catalogue known before any historical/future split

Let P be the complete, finite set of products in the modelled warehouse, S its stations, and zeta_s the number of storage slots at station s. All product identities, storage requirements, and the fixed warehouse geometry are exogenous information available before the demand history is examined. In this study each product occupies one slot and each slot holds one product:

\[
|P|=\sum_{s\in S}\zeta_s,\qquad
\sum_s x_{ps}=1\quad(p\in P),\qquad
\sum_p x_{ps}=\zeta_s\quad(s\in S),\qquad x_{ps}\in\{0,1\}.
\]

The station-level representation is sufficient when slots within a station are interchangeable for the objective and constraints. Export a deterministic one-to-one product-to-slot mapping as well, using the known slot list. If slots are not interchangeable, that is a changed problem, not permission to invent compatible locations.

For a historical prefix H, define the workload count of every product, including absent ones:

\[
L_p(H)=\sum_{o\in H}\ell_{op},\qquad
Z_H=\{p\in P:L_p(H)=0\}.
\]

For p in Z_H, the observed count is exactly zero. The product remains in P, the assignment constraints, the output layout, and the future evaluator. Do not remove it, give it a null station, or allocate it only after its first order. Its historical objective contribution may be zero; its storage obligation is not.

This is justified as **uncertainty about orders for an existing assortment**, not uncertainty about assortment expansion. An inventory catalogue and an order log are different information sources: knowing an item exists does not reveal when, how often, or with which other items it will be ordered. It is legitimate to know its identity while hiding all future demand observations. A historically inactive product becoming popular is within scope. A product outside P arriving is an assumption violation, reported as `OUT_OF_CATALOGUE`; it is never silently dropped or given a fictitious spare slot.

The equality between catalogue size and slots formalizes a completely occupied warehouse. There is no spare-location argument for ignoring inactive products. It also makes new-product insertion, multiple locations per SKU, catalogue growth, and dynamic recourse separate future research topics.

**Provenance limitation:** an order export cannot identify items never ordered anywhere in that export. The BERNER case may treat the complete exported SKU roster as an exogenously supplied catalogue under this hard assumption. That is not evidence that the export contains every physical SKU. Document this limitation explicitly. Do not use whole-export frequencies, last-observed stations, or future co-occurrences under the guise of knowing the catalogue.

### 2.2 Workload and proportional scale

Workload is the number of pick lines under the source-specific conventions in Section 3, not ordered quantity and not station visits. For a nonempty window W:

\[
D(W)=\sum_{p\in P} L_p(W)>0,\quad
q_p(W)=L_p(W)/D(W),\quad
r_s(x,W)=\sum_{p\in P}x_{ps}q_p(W).
\]

All included stations and all catalogue products, fixed or movable, enter this denominator. Consequently sum_p q_p = sum_s r_s = 1. An empty workload window is invalid, not a zero-share feasible window.

Multiplying every L_p by the same positive finite factor leaves r_s unchanged. Thus proportional scale increases have no effect on workload-share feasibility. Actual infinite demand is not a numerical input. Physical processing rates, elapsed-time capacity and absolute throughput ceilings are outside this study by assumption; hard storage-slot capacity remains inside it. Larger n changes composition sampling and potential drift exposure, so it is not merely proportional rescaling.

### 2.3 A historical reference that remains fixed during future assessment

Construct or obtain one feasible reference allocation x_ref before seeing the future at an origin. Define:

\[
b_s=\sum_p x^{ref}_{ps}L_p(H)/D(H).
\]

This is a pooled, line-weighted historical share, not the unweighted average of block shares. The same reference, b vector, station labels, and tolerances apply to every method and every n at that origin. The future reference/incumbent workload is not used to reset the target or judge feasibility. Do not include a future-incumbent comparator in the main evaluation; compare optimization methods with each other.

Each rolling origin is a separate hypothetical deployment with a fresh historical estimate, not a simulation of automatic relocation every block. No allocation changes within a deployment's assessed horizon. Fixed products keep their locations but their future workload is recomputed; freezing a location must never freeze its historical workload contribution.

### 2.4 Upper-only ceilings

Use the user's proposed upper-only policy:

\[
u_s=\min(1,b_s+\delta),\qquad r_s(x,W)\le u_s\quad\text{for every included station}.
\]

There is no additional lower-bound constraint. Conservation nevertheless implies

\[
r_s(x,W)\ge\max\{0,1-\sum_{j\ne s}u_j\}.
\]

Without clipping, this becomes max(0, b_s-(|S|-1)delta). For two stations, a common upper allowance also limits each station's decrease by that allowance. With many stations, the allowable decrease can be much greater: several other stations can absorb it. Report this implication and under-allocation descriptively; do not describe upper-only protection as symmetric preservation of the original shares.

### 2.5 Tolerance is a research policy, not a fitted confidence band

Proposed primary reference: **delta = 0.01, one percentage point per station**. At b_s = 0.20 the ceiling is 0.21, not 0.22. This is not the submitted article's relative 10% workload allowance. It is a transparent, identical absolute-share departure limit, chosen as a research convention rather than claimed to be operationally optimal.

Predeclare the sensitivity grid delta in {0.0025, 0.005, 0.01, 0.02, 0.05}; add delta = 0 as an exact-preservation diagnostic, not an expected deployable policy. Keep delta fixed across horizons, origins' methods, and uncertainty variants. The b vector may differ between origins because their histories differ.

No data-only rule can establish the customer's acceptable departure from a target. Historical variability quantifies uncertainty; it does not determine acceptable imbalance. Therefore do not choose delta from future success, expand it until a solver succeeds, or reinstate the old automatic historical-95%-band rule. The publication must show the tolerance/protection/visits frontier and the minimum-required-slack diagnostic, not only the most flattering point.

A common percentage-point limit permits a larger relative increase at a small station. Also report each ceiling relative to b_s where b_s > 0, the effective total excess allowance sum_s(u_s-b_s), and the implied lower bounds. At b_s = 0, report percentage-point excess rather than division by zero. The 5-point setting may be permissive at small stations and is an outer sensitivity case, not the recommended operating tolerance.

## 3. Data contract and extension of the submitted article

### 3.1 The only empirical sources

Allowlist:

- `exp02a_instances/`: exactly the existing 29-instance benchmark; original products, stations, and order-line files.
- `Heuristic_Connex_Set_Project/data/BERNER_ORDER_LINES_09-12.csv`: the specified industrial source.

The manuscript and supplementary file are methodological references, not permission to use all their auxiliary datasets. Exclude ISCF, `data/instances/iscf`, dated BERNER alternatives, calibration families outside the 29 instances, top-SKU replacement benchmarks, and other empirical data. Do not regenerate, reshuffle, append artificial future orders to, or give invented dates to the benchmark. Tiny hand-worked software fixtures are allowed only after test approval and are labelled unit tests, never empirical evidence.

Read-only source hashes and an allowlisted manifest establish which files a run used. Derived files go in a new namespace; preserve the raw sources, submitted TeX files, existing results, root gates, and unrelated user changes.

### 3.2 Chronology and complete orders

Treat the increasing numerical component of the order ID as the relevant processing sequence. `ORD_2` precedes `ORD_10`; preserve the original ID in the manifest. Validate uniqueness of the parsed order key and group complete orders before slicing. A product row must never be split from the rest of its order at a train/test boundary. No random splits and no lexicographic sorting of numeric IDs.

This is an assumed processing chronology. Sorting does not prove that creation, release, picking, and delivery sequences agree. State the assumption for BERNER; for synthetic data the generator's order index supplies an ordered sequence, not demonstrated seasonality or empirical temporal drift. Reliable sequence is sufficient to define this experiment, but sequence alone supplies no probabilistic guarantee about future demand.

### 3.3 Source-specific line conventions

For synthetic instances, preserve order-line multiplicities in workloads. The generator can repeat a product within an order through overlapping sampled itemsets. Collapse to distinct product supports only for station-visit counting, where repeated lines do not add another visit to the same station. Preserve weights when identical order supports are compressed; no top-support truncation.

For BERNER, use semicolon-delimited input; drop rows missing PRODUCT, ORDER or STATION; canonicalize station alias `01.GE4` to `01.E4`; exclude rows at `01.Z8`, `01.15`, and `01.GED`; and deduplicate retained (ORDER, PRODUCT) pairs for workload. Thus ell_op is one for a retained product-order pair, regardless of repeated station observations. Keep a separate raw-observation table for historical reference preferences. Emit counts at each step. Evaluate the complete retained order stream, including small orders; do not inherit the old solver's order-size filter as an evaluation filter.

A loader that changes a product's station to its last occurrence over the full export must not be called before splitting. Where repeated station observations need reconciliation, the reference assignment uses only historical observations plus independently known static metadata. Historical reconciliation determines a single allocation, not product-specific future labels. This leakage-safe ordering can differ from the article loader, which reconciles stations globally before filtering. Quantify that discrepancy, particularly for products crossing an excluded station boundary, before accepting the industrial data gate. Do not silently claim identical preprocessing or change the declared pipeline to reproduce a headline count. An acceptance-changing discrepancy requires joint review.

### 3.4 Reference allocation and fixed products

Synthetic `STATION` labels are drawn per order line by the generator; they are not a consistent pre-existing product-to-station layout. Construct x_ref with a deterministic, capacity-respecting historical LPT rule, including zero-demand products. Sort products by decreasing historical line count and stable product ID; place each at the eligible station with smallest current line workload, breaking ties by station ID. All catalogue products are assigned. Do not use full-export `POPULARITY` to rank them.

For BERNER, prefer a genuinely pre-known full inventory layout and slot geometry. If no independent layout exists, construct and clearly label a **historical reference layout**, rather than claiming to recover the client's true incumbent. Use each observed product's last historical station as its preferred station; complete the remaining slots using stable product/station order, subject to capacities and genuinely fixed assignments. If those preferred choices conflict with known capacities, use a deterministic minimum-reassignment reconciliation with a lexicographic tie-break. No future station observations may resolve the conflict.

The complete exported product roster and any whole-export geometry used as a surrogate must be explicitly tagged `assumed_exogenous`; they are a case-study assumption, not verified historical availability. This exception never covers demand values or last-observed reference locations. Without sufficient geometry or a valid location for a product required to be fixed, stop the industrial branch and report the missing input. Synthetic work can continue.

Carry over genuine exogenous fixed-location restrictions. For an explicit, training-only adaptation of the article's computational freezing rule, let H_large be historical orders containing more than five distinct retained products. Freeze at x_ref (a) products absent from H_large, including historically inactive products, and (b) products present in at most five H_large orders whose reference station is in the loader's static class {`01.E4`, `01.31`, `01.30`}. Union these with genuinely fixed products. A static-class label is not a declaration that every product at that station is fixed. These exclusions reduce relocation decisions only: the objective and workload scenarios still contain all historical orders and all products. Record both the full catalogue and movable subset. Never derive this mask from future frequencies or force the article's reported movable count to recur at each cut. Synthetic products are all movable unless the instance declares a genuine restriction.

The article reports 21,874 products, 5,899 fixed and 15,975 movable in its original industrial configuration. These are reconciliation references, not hardcoded expected split counts. This extension's primary normalized workload denominator includes all retained stations, including stations with no movable products; the article describes two fully static stations and its industrial comparison table evaluates 24 movable stations. The full retained subsystem, not excluded warehouse zones, is the study universe. Declare this change of evaluation scope, provide a reconciliation table, and do not present the new percentages as directly interchangeable with that table. A movable-station view, if reported, is supplementary only and must not certify full retained-system feasibility.

Repository pitfalls established by inspection: `Data_Generators/synthetic_data_zhang.py` assigns per-line station labels; `data_loader_industrial.py` has full-input station reconciliation and reduced decision-pool logic; existing robust solver wrappers use legacy uncertainty formulations and may truncate order supports. Reuse only audited components behind the new contracts, not legacy end-to-end pipelines.

## 4. Horizons and chronological protocol

### 4.1 A common initial horizon grid

Let P_count be the size of the full catalogue, not the historically observed or movable subset. Use n in {ceil(P_count/2), P_count, 2P_count}, removing duplicate values for tiny unit fixtures only.

| Catalogue size | Existing benchmark instances | Initial n values |
|---|---:|---|
| 50 | 12 | 25, 50, 100 |
| 500 | 10 | 250, 500, 1000 |
| 1000 | 4 | 500, 1000, 2000 |
| 2000 | 3 | 1000, 2000, 4000 |
| BERNER full retained catalogue | one industrial case | ceil(P_count/2), P_count, 2P_count |

If BERNER's reconciled P_count is 21,874, these become 10,937, 21,874, and 43,748 orders. Do not force that catalogue count if cleaning disagrees.

This is a compact, geometrically spaced exposure grid. With roughly ten synthetic lines per order, it corresponds to about 5, 10, and 20 lines per catalogue product on average, not a guarantee that every product is observed. P_count is known independently of future outcomes. The rule is a comparable benchmark scale, not a theorem that P_count orders are operationally optimal. Report actual orders, lines, active-SKU fraction and n/P_count for every horizon. For an eventual deployment, n is an input chosen in orders; it need not be tied to P_count.

### 4.2 Origins and historical blocks

After source cleaning, let M be the number of complete orders and t0 = floor(0.70 M). Let n_max = 2P_count and J = min(4, floor((M-t0)/n_max)). Candidate origins are t_j = t0 + j n_max for j = 0,...,J-1. The core proposed campaign uses the first min(2,J) origins; further origins are a declared replication stage, not a replacement for an inconvenient first result.

For an origin t and horizon n, H is the complete prefix 1,...,t and the scored future is t+1,...,t+n. Build historical scenarios from complete, right-aligned, nonoverlapping n-order blocks in H. Exclude a leftover partial block from the scenario list, but include it when computing the whole-history objective and b. Add the whole-history normalized demand vector to the scenario list explicitly.

Require at least three complete historical n-blocks and one complete future n-block. Mark a failed eligibility check `INSUFFICIENT_HISTORY` or `INSUFFICIENT_FUTURE`; do not shrink n without disclosure, pad windows, or turn partial windows into complete ones. Three blocks make the construction definable, not statistically well-powered; report the actual count and flag fewer than ten as sparse historical evidence. If J = 0, there is no common largest-horizon core deployment; report that limitation and request a revised protocol before substituting smaller-horizon origins.

History may be longer than n: a learning prefix and a prediction horizon serve different purposes. What must match is the size n of historical scenario windows and the future window being assessed. Nonoverlap does not prove independence. Different horizons at the same origin share data; their results are paired and correlated.

### 4.3 Leakage and sequential use

Freeze the protocol and configuration before executing the new campaign. Development decisions may use the first 70% prefix only. Earlier project investigations have already looked at these datasets; label the resulting study retrospective/exploratory, not a newly untouched confirmatory holdout.

At each later origin, previously unfolded orders may enter H as they would in a rolling deployment, but the algorithm, grids, and reporting rules remain frozen. No future b, SKU popularity, co-occurrence, station mapping, model choice, slack, or solver tuning may enter that origin's model. The static catalogue and explicitly declared geometry are the only full-roster metadata exceptions.

Cross-evaluate a layout trained for n on other available m horizons after the primary scoring. This shows transfer and failure; it does not certify those horizons or justify selecting a winning n after looking at its future. We do not promise every prefix, every rolling window, or an unlimited future. A larger window can average variability but also encounter more drift; reliability need not improve monotonically with n.

## 5. The first robust model to implement

### 5.1 Historical objective

Minimize total historical station visits, or its equivalent mean over H:

\[
\min_x \sum_{o\in H}\sum_s y_{os},\qquad
y_{os}\ge x_{ps}\quad(p\in P_o),\qquad 0\le y_{os}\le1.
\]

With integral x and a positive visit objective these linking rows give the correct visit count. Identical distinct-product supports may be aggregated with their exact order multiplicities. Include fixed products' station touches in each support; an order visiting a fixed and movable product at the same station incurs one visit, not two. No objective truncation, future-order oracle, robust objective claim, or relocation-budget extension in the core model.

### 5.2 Historical scenario set

Let q^1,...,q^K be the historical n-block vectors together with q^H, indexed over every product in P. Define A_sk(x) = sum_p x_ps q_p^k. Every q^k is nonnegative, sums to one, and is zero on Z_H.

The historical uncertainty set is conv{q^1,...,q^K}. For linear station workload, requiring A_sk <= u_s for all s,k protects its entire convex hull. Scenarios preserve historically observed joint product-share movements; they do not assume independent product shocks.

### 5.3 Activation of historically inactive known products

For Z_H nonempty, introduce a separately declared activation budget nu in [0,1]. It bounds the **total future workload share** that may move to the historically inactive catalogue products, not the number of new products and not per-product probability. Define

\[
\mathcal U_{t,n}(\nu)=
\{(1-a)z+a v:\ z\in\operatorname{conv}\{q^k\},\quad
v\ge0,\ \sum_pv_p=1,\ v_p=0\ (p\notin Z_H),\ 0\le a\le\nu\}.
\]

This set preserves total share. It includes the unperturbed historical hull and allows activation to concentrate on any single known inactive SKU. It does not create a product or a slot. If Z_H is empty, define U as the historical hull and effective nu as zero; report this rather than manufacturing inactive products.

Use nu = 0.01 as the primary **stress assumption** and nu in {0, 0.0025, 0.005, 0.01, 0.02, 0.05} as a sensitivity grid. The primary value asks whether up to one percent of the future pick-line workload can activate formerly inactive items. It is not a forecast, a confidence level, or a promise that future activation is that small. Delta and nu have separate meanings and independent grids despite the same primary numerical value.

Before optimization, diagnose this assumption within H: at each eligible earlier cut on the same chronological block grid, identify the then-inactive catalogue products and measure their workload share in the following n orders, with both portions inside H. Report the resulting activation masses against the declared nu grid. Do not automatically adjust delta to accommodate them, and do not claim empirical maxima bound unseen activation. Future activation mass is scored afterward, not used to select nu. If historical evidence already exceeds the primary nu, label that primary stress level inadequate rather than hiding the warning.

### 5.4 Exact finite counterpart

Let h_s indicate whether at least one product in Z_H is assigned to station s. Encode h_s as binary with x_ps <= h_s for p in Z_H and h_s <= sum_{p in Z_H} x_ps. For an empty Z_H set h_s = 0.

Then the robust workload constraints are exactly

\[
A_{sk}(x)\le u_s,\qquad
(1-\nu)A_{sk}(x)+\nu h_s\le u_s\qquad(s\in S,\ k=1,\ldots,K).
\]

Reason: for fixed z and x the worst inactive-product distribution puts its mass at a station containing an inactive product if one is present there. Maximizing over a in [0,nu] requires only the endpoints; maximizing the remaining linear function over z requires only the historical vertices. Therefore

\[
\max_{q\in\mathcal U_{t,n}(\nu)}\sum_p x_{ps}q_p
=\max_k\max\{A_{sk},(1-\nu)A_{sk}+\nu h_s\}.
\]

These rows are linear in the binary formulation; the Hexaly set representation can compute A_sk and h_s from each station's product set. This removes the need for an iterative adversarial solve in the core algorithm. An independent small LP over the same uncertainty set will verify the formula on approved unit cases.

All products participate in the assignment even if absent from every historical order support. Fixed inactive products also contribute to h_s. Their location can make a robust limit unattainable; that is a real constraint conflict, not a reason to omit their demand.

For the independent LP check, use nonnegative historical weights w_k and inactive masses m_p with sum_k w_k + sum_p m_p = 1 and sum_p m_p <= nu, setting q = sum_k w_k q^k + m. This is a linear description of the same mixture set and avoids accidentally writing a bilinear verification problem. For an empty Z_H, m is absent and the weights sum to one.

### 5.5 What is and is not guaranteed

An independently verified feasible allocation satisfies all upper ceilings **for every q in the declared U**, and this statement is invariant to proportional workload scaling. This is a deterministic, conditional robustness guarantee. The model does not itself guarantee that the next n orders lie in U, or that the joint future compliance probability is 95%.

In particular, even if future activation mass is <= nu, active-product relative shares might leave the historical hull. In a high-dimensional catalogue, a hull of relatively few historical blocks can have low dimension and should not be sold as a full-dimensional predictive region. Report future station-direction excursions beyond the modelled worst shares; distinguish a missed scenario from a violation of an implemented robust constraint.

A previously active product becoming an unprecedented bestseller is not fully covered merely because inactive-product activation is covered. This is the principal weakness to try to falsify. If it matters empirically, a structured, full-catalogue mass-transfer extension is the next model-design proposal, requiring another discussion; do not quietly replace the model mid-campaign.

There is another important equivalence. If inactive-product locations are fixed, h_s is known, and for nu < 1 activation protection is exactly HIST with station-specific scenario ceilings min(u_s, (u_s-nu*h_s)/(1-nu)). The proposed industrial freezing rule makes this case relevant. If every station contains an inactive product, h_s = 1 everywhere. Report this reduction and verify it algebraically; do not claim that activation protection introduces a fundamentally new optimization mechanism in those cases. When inactive products can move, h_s may depend on the allocation. The meaningful scientific question remains whether the declared protection improves unseen workload outcomes at an acceptable cost, beyond the appropriate tightening controls.

There is no nontrivial allocation guaranteed against every possible future mix: if all future workload can fall on a product at a station with u_s < 1, that station can receive share one. Knowing the catalogue removes uncertainty about which items require storage, not arbitrary uncertainty about their demand.

### 5.6 Two analytical diagnostics before any performance claim

First, derive the minimum common percentage-point allowance for the selected uncertainty set:

\[
\delta_{min}(t,n,\nu)=
\min_{x\text{ storage/fixed feasible}}\max_s
\left[\max_{q\in\mathcal U_{t,n}(\nu)}\sum_p x_{ps}q_p-b_s\right]_+.
\]

Use an epigraph variable and the same finite rows with b_s + eta instead of u_s. A certified lower bound above the declared delta proves that model/policy combination infeasible. A feasible solution supplies an upper bound. A time limit with a gap between those bounds is unresolved, not an infeasibility proof. Never redefine the main ceiling using this diagnostic after scoring the future. Delta_min is specific to the modelled uncertainty, not the minimum slack the actual unknown future will need.

Second, document why an unrestricted total-variation ball is not automatically a richer alternative. For a nonempty station with a nonempty complement, the worst share in {q >= 0, sum q = 1, ||q-q^H||_1 <= 2 rho} equals min(1, A_sH + rho). For u_s < 1, protection reduces to A_sH <= u_s-rho: ordinary nominal tightening. If all stations have such caps and none are empty, S_count*rho <= sum_s(u_s-b_s) is necessary for feasibility. A diffuse worst case can exhaust a small slack budget before meaningful allocation choices help. Include this derivation as a control, not an invented claim of novelty.

## 6. Comparisons and falsifiable hypotheses

All arms use the same historical objective, full catalogue, fixed-product rules, reference b, future scoring ceiling u, solver representation, seeds, resources, and origins:

| Arm | Optimization workload constraints | Purpose |
|---|---|---|
| NOM | A_sH <= u_s | Nominal CSLAP extension |
| TIGHT | A_sH <= min(1,b_s+delta/2) | Ordinary half-headroom tightening control |
| HIST | A_sk <= u_s for all historical scenarios | Effect of observed composition variability |
| HIST+ACT | Section 5.4 with declared nu | Additional inactive-product protection |

NOM and TIGHT do not depend on n under this protocol. Solve each once per origin/delta/seed and reuse its frozen layout across n; record shared run IDs rather than treating the reused layouts as different optimizations. At nu = 0, HIST+ACT must reduce to HIST. If Z_H is empty, the same equivalence must hold at every nu.

For the sensitivity stage, use TIGHT's historical cap b_s+(1-lambda)delta with lambda in {0,0.25,0.5,0.75,1}; score every point against the unchanged u. Lambda = 0 recovers NOM. Show the tightening frontier, including infeasible/unsolved cases, so a robust gain is not credited merely to stronger historical restriction or a much larger visit cost.

Hypotheses:

- H1: historical scenario protection reduces held-out joint station-cap violations relative to NOM at the same declared ceilings.
- H2: any useful gain is not fully explained by ordinary tightening at comparable visit cost and computational effort.
- H3: activation protection is useful when previously inactive catalogue products actually receive demand, and otherwise becomes an identifiable cost or identical-model case.
- H4: the achievable protection/visits/slack trade-off changes with n; larger n is not assumed to be uniformly better.

Failure to reject a difference is not equivalence; better-looking means do not prove all four hypotheses. Stationary synthetic instances can show little benefit from protection. They are a control on finite-sample effects and solver cost, not proof of robustness to severe real-world drift. BERNER supplies one case of actual sequence variation, not a representative sample of all warehouses.

## 7. Evaluation, diagnostics and interpretation

Save a complete station-level record for every deployment, horizon and method, including b_s, u_s, r_s, historical and robust worst shares, fixed-product contributions, and the allocation hash. Primary measures:

- Joint compliance: indicator that every included station satisfies its ceiling; also report violation count and worst excess in percentage points.
- Mean station visits per future order, alongside historical mean visits. Compare paired differences against NOM and TIGHT, not the future incumbent.
- Positive excess sum, station-level decreases, and implied lower-bound distances. These describe redistribution, not absolute throughput.
- Solver/model feasibility status, independent validation status, native objective bound/gap if available, build/solve/validation times, and memory where measurable.
- Inactive catalogue count, number of inactive SKUs per station, realized activation share, and station-direction novelty beyond the modelled worst shares.

Separate three quantities: no allocation returned; a returned allocation failing its own stated optimization constraints; and an optimization-feasible allocation that breaches the ceiling on unseen future orders. These are computational failure, implementation/model-verification failure, and out-of-sample failure respectively. Never score missing solutions as successful future compliance, and never pool them silently with observed violations. Report both allocation-return rate and conditional future compliance.

Historical constraints include q^H, so an independently valid nominal/reference assignment is a useful nominal-feasibility check. It is not necessarily robust-feasible. Robust-feasible sets shrink as nu increases at fixed H,n, but sets across different n need not be nested. True minimum visits cannot improve when identical constraints are tightened; time-limited solver incumbents can, so report bounds/status before claiming a paradox.

Aggregate synthetic results first within instance across origins and seeds, then show paired instance-level summaries and catalogue-size strata. Solver seeds measure algorithm variability, not additional independent future streams. Overlapping horizons, repeated origins and individual stations are not independent replicates. If interval estimation is approved, resample whole synthetic instances with all paired observations intact and state the required independent-instance interpretation; with only three 2000-product instances, emphasize raw paired results and uncertainty. Do not attach a binomial 95% reliability guarantee to correlated windows. BERNER remains descriptive if only a few disjoint evaluation blocks are available.

Core figures: joint violation versus n/P_count; future visit cost versus worst share excess; tolerance/activation feasibility frontier; station-level historical target and future share; return-status breakdown. Every figure must include denominators, unresolved cases and the parameter settings. Do not select only feasible instances to imply universal success.

## 8. Solver strategy and resource boundaries

Use explicit Python interpreters, without requiring interactive activation:

- CPLEX: `C:\ermal\Virtual_Environment_CPLEX_1\Scripts\python.exe`.
- Hexaly: `C:\ermal\Virtual_Environment_LocalSolver_3\Scripts\python.exe`.

Both executable paths were found during read-only planning inspection. Licenses are reported available by the user; package versions, imports, license checkout and solving have **not** been tested in this planning task. No global installs, environment upgrades, or license edits are part of the plan.

CPLEX is the binary reference implementation for small-instance correctness, independent uncertainty LP checks, and valid bounds/infeasibility certificates where obtained. Hexaly's set-variable representation is the proposed main performance backend, particularly for the full industrial catalogue, consistent with the submitted article's representation findings. Cross-check both on the same small contracts; do not compare a robust Hexaly result only against a nominal CPLEX result and attribute backend differences to robustness.

Each backend consumes the same immutable, solver-neutral input and produces the same structured result. Use a partition of the entire catalogue into station sets in Hexaly; use x variables for all catalogue products in CPLEX, with fixed assignments enforced. Use exact weighted supports and full line scenarios in both. Legacy wrappers are references, not drop-in implementations of this protocol.

Preserve native termination codes. Distinguish a feasible incumbent, proven optimum within stated solver tolerances, proven infeasibility, time limit with no incumbent, memory/resource limit, numerical issue, and API/license error. In particular, do not interpret Hexaly `INFEASIBLE` as a proof that no feasible allocation exists, or CPLEX's ambiguous infeasible-or-unbounded state as proven infeasibility. Verify the installed version's status semantics before mapping them. Independently recompute assignment completeness, fixed locations, occupancy, robust shares and visits; native status alone cannot certify our data interpretation. [Hexaly status documentation](https://www.hexaly.com/docs/last/pythonapi/optimizer/hxsolutionstatus.html), [IBM solution-status documentation](https://www.ibm.com/docs/en/icos/22.1.2?topic=information-accessing-solution-status).

Proposed per-solve ceilings for budget estimation: 120 seconds at 50 products, 300 at 500, 600 at 1000, 1200 at 2000, and 1800 for the industrial engineering campaign. These are new provisional resource choices, not claims to reproduce the article's longer industrial budget. Record solver threads, hardware, installed versions and random seeds; use the same backend limits across arms within an instance. Do not run competing solvers concurrently for measured timing. Include preprocessing/model-build costs separately and report total end-to-end effort.

Primary seeds are {11,22,33}. With three horizons, NOM/TIGHT reuse and two horizon-dependent robust arms, there are eight primary solves per instance/origin/seed. For 29 synthetic instances, two eligible origins and three seeds, that is 1392 primary solves, at most 139.2 solver-hours using the proposed caps. If BERNER supports two such origins, it adds 48 solves and up to 24 solver-hours. These are cap-based estimates, not measured runtimes; sensitivities, validation, repeats, infeasibility diagnostics, model building and reporting add work.

Therefore do not launch the full matrix automatically. First produce a pilot manifest and cost quotation. Start with a small approved implementation-validation stage, then an approved engineering pilot, then a first-origin/one-seed screening matrix, and only then the agreed replication/sensitivity campaign. The first screening matrix is eight solves per instance and up to 23.2 synthetic solver-hours, plus up to four industrial solver-hours. Report these costs before requesting campaign approval. Any reduced campaign must be declared before running it, with correspondingly narrower claims.

## 9. Implementation phases and acceptance boundaries

The detailed ownership tree, interfaces, and gate inventory are in [AGENT_HANDOFF.md](AGENT_HANDOFF.md). Execution order:

1. Approve this protocol and create the future execution ledger; no scientific results are assumed.
2. Implement and verify immutable catalogue/order contracts, leakage-safe reference construction, and chronological slicing. Industrial provenance problems are resolved or explicitly handed off before industrial optimization.
3. Implement historical scenarios, activation envelope, independent evaluator, and exact reference proofs/tests.
4. Implement CPLEX and Hexaly adapters against that frozen contract; validate on hand-checkable cases before comparative runs.
5. Produce an allowlisted campaign manifest, run-count/resource estimate, and explicit failure handling. Obtain approval for the pilot tests/runs and their limits.
6. Run the approved engineering pilot; resolve implementation defects without tuning to hidden future outcomes. Requote costs before the main experiment campaign.
7. Freeze protocol revision, run the approved screening/replication matrix, then the separately budgeted sensitivity and minimum-slack diagnostics. Changes after outcomes are seen become a separately labelled exploratory revision.
8. Independently regenerate metrics, inspect failures, and write a separate robustness manuscript/report with evidence-qualified conclusions. Do not edit the submitted CSLAP article as part of this implementation unless requested.

The agent must not silently simplify the full catalogue, turn hard constraints into an unreported penalty, cut order supports, drop fixed workload, omit failures, widen delta/nu, switch datasets, or use future orders to repair a layout. These are acceptance-changing modifications that require discussion.

## 10. Theory and methodological grounding

The finite counterpart, conservation bounds, scale invariance, and total-variation reduction above are elementary derivations of this proposed formulation; prove them explicitly in the new report and verify the implementation independently. They are not empirical conclusions from the earlier robustness attempts.

Robust optimization protects against a declared uncertainty set; translating that protection into a probability statement requires justified statistical assumptions and a suitable set construction. Bertsimas, Gupta and Kallus establish such connections for their constructions under specified assumptions, including i.i.d. sampling; that is not a license to assign their guarantees to our dependent order blocks or binary allocation model. [Data-driven robust optimization](https://web.mit.edu/dbertsim/www/papers/Robust%20Optimization/Data-driven%20robust%20optimization.pdf).

Rolling-origin evaluation separates information available at a decision point from later outcomes and can be matched to the requested forecast horizon. Here the horizon is measured in complete orders; we borrow the evaluation principle, not a calendar model or an independence claim. [Forecasting: Principles and Practice, time-series cross-validation](https://otexts.com/fpp3/tscv.html).

These sources justify the methodological distinctions, not novelty of the particular storage formulation. A focused literature-positioning review is a future writing deliverable before claiming novelty. It must use primary papers and explicitly distinguish robust constraints from distributionally robust or chance-constrained guarantees.

## 11. Decision after the evidence, including the calendar fallback

Classify the result rather than demanding a positive outcome:

- **Useful under stated conditions:** future violations improve at a documented visit cost, relative to both nominal and tightening controls, with sufficient independently validated solutions and honest uncertainty limitations.
- **No demonstrated added value:** the benchmark is stable, the nominal layout already complies, or tightening explains the gains. This is a valid result; do not create drift or widen scope to force a positive finding.
- **Protection model inadequate:** realized composition changes repeatedly exceed the history-plus-activation structure. Discuss a full-catalogue structured transfer model before implementing it. Dates alone do not repair this omission.
- **Policy/uncertainty incompatibility:** valid lower bounds on delta_min exceed the declared tolerance, possibly because of fixed products or concentrated demand. Report the incompatibility; do not describe it as a missing-date problem.
- **Computationally unresolved:** solvers cannot establish enough feasible layouts/certificates at approved resources. Revisit representation or budget, not statistical conclusions.
- **Sequence/data inadequate:** processing order is not credible, geometry/reference metadata are insufficient, or too few eligible windows exist. State which claim is unsupported and request the necessary input.

Revisit the dated path if the scientific question must become shift/day/week compliance, if chronology cannot be supported by IDs, or if the industrial decision needs calendar duration and arrivals. Dates make operational horizons meaningful but still require a choice of day/shift/week and do not eliminate demand nonstationarity or the need for calibration. The synthetic benchmark cannot validate a calendar claim without actual date information; do not manufacture that information.

This plan is complete when its assumptions, implementation contract and proposed validation are reviewable. The implementation is complete only when its acceptance checks have current evidence. The study is complete when the approved experiments and failure analyses support an honest conclusion, whether positive, negative, or mixed. None of those completion states implies unconditional future feasibility.
