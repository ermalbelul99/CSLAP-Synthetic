# Citation notes for the writer

These are statements the manuscript can attribute to each included article. Each was checked against the article text or abstract, at the access level shown. Keys refer to `verified_references.bib`; the evidence table and caveats are in `LITERATURE_REVIEW.md`.

**Access levels:**

- **Full text (VoR):** version of record.
- **Full text (author version):** accepted, arXiv or working-paper version of the published article. Check page-specific numbers against the version of record before quoting.
- **Full text (publisher page):** as indexed by NotebookLM.
- **Abstract only.**
- **Bibliographic only.**

**Closeness flags** (setting of the extension article):

- **[WS]**: workload-share or workload-budget constraints in storage or station assignment.
- **[RS]**: re-slotting or reassignment under demand change.
- **[CT]**: constraint tightening, margins or budgeted robustness.
- **[OOS]**: out-of-sample evaluation of storage decisions.

The phrasings below are suggestions. Keep each claim at the level stated, and do not add numbers that are not listed here.

---

## Closest to the article's setting (read these first)

| Key | Flags | Why closest |
|---|---|---|
| `winkelmann2025integrated` | [WS] [OOS] (simulated) [RS] (discussion) | Station workload-deviation constraints in a pick-and-pass loop, shown to be violated under realised demand variation |
| `tarczynski2023` | [WS] | Min-max expected zone-workload storage model for pick-and-pass; notes the uncertainty of history-based assignment |
| `kim2022dynamic` | [WS] [RS] | Zone workload balance plus capacity-limited reassignment |
| `zhang2024joint` | [WS] | Explicit workload-balance constraint in storage assignment; tightening it raises travel |
| `dundar2025robust` | [CT] | Budgeted (Bertsimas-Sim) robust counterpart in a storage assignment model |
| `ang2012robust` | [CT] (robust) | Robust optimisation for multiperiod storage assignment under ambiguous demand |
| `waubertdepuiseau2022dslap` | [OOS] | Storage policy trained on one year and evaluated on the following two months |
| `mirzaei2021ica` | [OOS] [RS] (sensitivity) | Train/validation split of real orders, and robustness of a storage allocation to demand change |
| `wu2026reassignment` | [RS] | When to reassign storage as the demand pattern evolves |
| `bertsimas2004price` | [CT] | Standard reference for a tunable protection budget in constraints |

---

## (a) Workload balance in storage and station assignment

### `jane2000storage`: Jane (2000), IJPDLM 30(1)
Access: abstract only. Flags: [WS] [RS] (volume fluctuation).
1. Jane (2000) proposed a heuristic, based on historical customer orders, for assigning products to storage zones of a relay order-picking system, with the objective of balancing workloads so that all pickers carry almost the same load.
2. The same study presented two further heuristics, also based on historical data, for adjusting storage locations when order volume fluctuates, while keeping picker workloads balanced. The methods were illustrated with actual data and verified by simulation.

### `jane2005clustering`: Jane and Laih (2005), EJOR 166(2)
Access: abstract only (publisher page). Flags: [WS].
1. For synchronized zone order picking, Jane and Laih (2005) developed a heuristic that assigns items to zones to balance workload among pickers, improving system utilisation and reducing the time to fulfil each order.
2. Their model clusters items using a co-appearance similarity measure computed from customer orders (a natural cluster model, a relaxation of the NP-hard homogeneous cluster model). It was evaluated with empirical data and simulation.

### `yu2008pickandpass`: Yu and De Koster (2008), IIE Transactions 40(11)
Access: abstract (VoR) and full text (ERIM working-paper version). Flags: [WS] (performance basis).
1. Yu and De Koster (2008) developed a G/G/m queueing-network approximation for pick-and-pass order picking systems, to estimate order lead time and station utilisation quickly and to evaluate storage methods at stations, number of pickers, station size, order arrivals, and batching and splitting. [abstract]
2. In their numerical example, a uniform storage policy (equal storage space per product class at every station) gave shorter mean order throughput times than a non-uniform policy, with the difference growing with system load. [working-paper version, Table 6; check against the VoR before quoting the 20.31% maximum]

### `tarczynski2023`: Tarczyński (2023), Operations Research and Decisions 33(3)
Access: full text (VoR). Flags: [WS]. Companion key reused.
1. Tarczyński (2023) formulated MILP models for pick-and-pass systems. The first uses expected item demand to assign items to zones and balance the workload across zones, by minimising the maximum expected zone workload. Further models optimise order batching and batch sequencing.
2. On exemplary instances, combining the storage and batching optimisation reduced total order-picking time by about 35-45% compared with random policies. Balancing expected zone workload alone, with random batching, gave a 10-20% improvement.
3. The paper notes that storage assignment based on historical data involves risk and uncertainty, because even perfectly balanced zones can receive different workloads for a particular set of customer orders.

### `fedtke2023inline`: Fedtke, Boysen and Schumacher (2023), OR Spectrum 45(3)
Access: abstract only. Flags: [WS] (analogous serial-station setting).
1. Fedtke et al. (2023) studied in-line kitting. The first stations of an assembly line are reserved for pickers who fill kits travelling with each workpiece from SKU containers placed along the line.
2. They showed that pickers' walking effort can be reduced significantly by jointly balancing workload among stations and optimising the storage assignment of SKU containers within each station, without additional costs in their computational study.

### `kim2022dynamic`: Kim and Hong (2022), JORS 73(5)
Access: abstract only. Flags: [WS] [RS].
1. Kim and Hong (2022) proposed a storage location assignment model for progressive bypass zone picking that balances a weighted sum of the number of picks and the number of visits across zones, to reduce recirculation under a storage space restriction.
2. They extended it to a reassignment model for limited relocation capacity, which moves prioritised pairs of products.
3. In simulations with industry orders, full assignment and capacity-limited reassignment reduced order-picking completion time by 9.2-13.6% and 5.9-8.9% respectively. The reassignment model is preferable when management wants minimal changes.

### `yuan2018stowage`: Yuan, Cezik and Graves (2018), IJPR 56(1-2)
Access: abstract only. Flags: [WS] (under uncertain demand).
1. Yuan et al. (2018) studied how to distribute arriving inventory across storage zones with limited picking capacity, so that uncertain demand can be met.
2. In a simulation study, two zone-stowage policies balanced picking workload across zones well: splitting each product's receipt across two zones (a chaining-inspired allocation), and stowing to the zone with the smallest expected workload.

### `zhang2024joint`: Zhang, Tian and Zhou (2024), Complexity 2024
Access: abstract only. Flags: [WS].
1. Zhang et al. (2024) formulated a mixed-integer model for jointly assigning items to pods and pods to storage locations in robotic mobile fulfilment systems. The model includes a workload-balance constraint on picking aisles to avoid robot congestion and minimises robot movement distance; it is solved with an improved genetic algorithm.
2. Their experiments report that robot movement distance increases as the workload-balance constraints become more stringent.

Caution: abstract-level only. Avoid quantitative claims.

### `winkelmann2025integrated`: Winkelmann, Tolkmitt, Ulrich and Römer (2025), FSMJ 37(2)
Access: full text (VoR, open access). Flags: [WS] [OOS] (simulated weeks) [RS] (discussion). Seed paper.
1. Winkelmann et al. (2025) solved an integrated storage assignment problem for the pick-and-pass picking loop of an e-grocery fulfilment centre with an MILP. The model selects SKUs for the loop and assigns them to stations and shelves, subject to constraints limiting each station's relative deviation in daily picks from the average over all stations.
2. An assignment based on average demand exceeded 3% station deviation on individual days of the week against a 1% threshold. Adding day-of-week-specific constraints reduced the deviation below 1%, with the objective's deviation increasing by 0.11 percentage points.
3. In a simulation of week-to-week variation (52 weeks × 6 days, 100 runs), with coefficient of variation 0.05:
   - the average-based assignment produced a maximum station deviation above 4%, four times the intended 1%;
   - the day-of-week-aware assignment still reached 2.46%, about 43% lower;
   - mean absolute deviation fell from 1.01% to 0.57%;
   - the benefit shrank as variation grew (coefficient of variation 0.3).

   The authors suggest robust or stochastic optimisation for random variation as future work.

Also usable, from the full text: rearranging SKUs is often not possible or practical for short-term (day-of-week) variation, whereas seasonal or long-term demand changes typically require rearranging storage locations.

### `debold2025skurepetitions`: Debold (2025), Computers & Industrial Engineering 210
Access: abstract only. Flags: [WS].
1. Debold (2025) studied storing the same SKU in several zones of a sequential zone picking system, to mitigate imbalances between zones when high demand variability meets a small set of SKUs. The problem is modelled as a binary program and solved with a three-stage heuristic that anticipates order routing.
2. In a simulation calibrated with real e-grocery data, the heuristic outperformed benchmark approaches on average by up to 19.5%. A real-world test showed up to 40% gains in zone workload balancing.

---

## (b) Stochastic, robust, data-driven and dynamic storage assignment

### `christofides1973rearrangement`: Christofides and Colloff (1973), Operations Research 21(2)
Access: abstract only. Flags: [RS].
1. Christofides and Colloff (1973) addressed rearranging items in a warehouse when changes in relative demand turn formerly fast-moving items into slow movers. They gave a two-stage algorithm for the sequence of moves that minimises rearrangement cost or time.
2. The algorithm is optimal in the restricted case where rearrangement is done in short cycles, so the warehouse can remain operative.

### `thonemann1998stochastic`: Thonemann and Brandeau (1998), Management Science 44(1)
Access: abstract only. Flags: none (background).
1. Thonemann and Brandeau (1998) applied turnover-based and class-based storage policies to automated storage and retrieval systems with stochastic demand. They showed that the turnover-based policy is optimal, minimising one-way travel time, and that both policies reduce expected storage and retrieval time compared with random storage.

### `ang2012robust`: Ang, Lim and Sim (2012), Management Science 58(11)
Access: abstract only (publisher page). Flags: [CT] (robust optimisation).
1. Ang et al. (2012) modelled multiperiod storage and retrieval in a unit-load warehouse facing variable supply and uncertain demand. Demand depends affinely on uncertain factors whose distributions are only partially characterised. Their robust optimisation model minimises the worst-case expected total travel.
2. Using a linear decision rule reduces the model to a moderate-size linear optimisation problem. In their computational studies, the resulting policy came close to the expected value given perfect information and significantly outperformed existing heuristics.

### `pazour2015reshuffling`: Pazour and Carlo (2015), TR-E 73
Access: abstract only (RePEc and publisher page). Flags: [RS].
1. Pazour and Carlo (2015) studied warehouse reshuffling, the repositioning of items by moving them sequentially. They gave a mathematical programming formulation, a complexity analysis, heuristics, and a proof delimiting when double-handling is a productive move.
2. Their heuristics improved on a benchmark heuristic by relaxing how cycles are handled and by allowing double-handling.

### `kubler2020iterative`: Kübler, Glock and Bauernhansl (2020), Computers & Industrial Engineering 147
Access: abstract only. Flags: [RS].
1. Kübler et al. (2020) proposed an iterative heuristic that jointly solves storage location assignment, order batching and picker routing in manual picker-to-parts warehouses, taking account of future dynamics in customer demand. Numerical experiments indicate significant savings in travel distance.

### `mirzaei2021ica`: Mirzaei, Zaerpour and de Koster (2021), TR-E 146
Access: full text (publisher page). Flags: [OOS] [RS] (sensitivity to demand change).
1. Mirzaei et al. (2021) proposed an integrated cluster allocation policy that uses product turnover and affinity from historical orders to assign correlated products to storage in parts-to-picker systems. It reduced total retrieval time by up to 40% compared with full turnover-based and class-based storage.
2. In a Monte Carlo test that replaced 10-100% of the orders in a base example with new random orders, the policy remained beneficial for random changes in the demand pattern of up to 60% (AS/R system) and 70% (RMF system).
3. On a real warehouse dataset, 70% of orders were randomly selected to build the allocation and the remainder was used for validation. The split is random, not temporal.

Do not use NotebookLM's attribution of this paper to "van den Berg et al." or its "100% change" claim; both are wrong.

### `waubertdepuiseau2022dslap`: Waubert de Puiseau et al. (2022), Technologies 10(6)
Access: abstract only. Flags: [OOS].
1. Waubert de Puiseau et al. (2022) trained a deep reinforcement learning agent for dynamic storage location assignment on one year of historical storage and retrieval data. On new data from the following two months it reduced costs by 6.3% relative to the warehouse's ABC-classification-based strategy.

### `dundar2025robust`: Dündar (2025), Alphanumeric Journal 13(1)
Access: full text (VoR). Flags: [CT]. Seed paper.
1. Dündar (2025) formulated correlated SKU-to-location assignment in a forward picking area as a quadratic assignment problem, linearised it, and derived a robust counterpart following Bertsimas and Sim. A budget Γ0 limits how many uncertain SKU correlation coefficients may deviate within their intervals.
2. In tests with 5, 10 and 12 SKUs and generated correlations, the worst-case objective increased with the budget Γ0 and with the deviation size. Solution time rose from 1,372 s at 12 SKUs to 5,062 s at 13 SKUs, and the author reports that larger instances become computationally intractable.

Scope note: robustness here is applied to the objective coefficients, not to constraints, and no workload balance is modelled.

### `wu2026reassignment`: Wu (2026), JORS (advance online)
Access: abstract only. Flags: [RS].
1. Wu (2026) studied the item storage reassignment problem in robotic mobile fulfilment systems, arguing that item storage assignments should be adapted as the demand pattern evolves. The paper proposes an interchange-guided sequencing algorithm and analyses when reassignment should be performed under different item varieties and warehouse capacities.

---

## (c) Robust optimisation foundations

### `soyster1973convex`: Soyster (1973), Operations Research 21(5)
Access: abstract only (publisher page). Flags: [CT] (origin).
1. Soyster (1973) formulated convex programming problems whose feasible region is defined by set containment (convex activity sets summed within a convex resource set) rather than by fixed inequalities. For a special form of the resource set, the problem is solved via an auxiliary linear programme, with application to inexact linear programming.

Suggested framing: "the set-inclusive (worst-case) approach of Soyster (1973)". Bertsimas and Sim (2004) describe robust LP as proposed in the early 1970s.

### `bental1999robust`: Ben-Tal and Nemirovski (1999), Operations Research Letters 25(1)
Access: full text (author version). Flags: [CT].
1. Ben-Tal and Nemirovski (1999) proposed replacing an uncertain linear programme by its robust counterpart, and showed that with ellipsoidal uncertainty sets the robust counterpart is a conic quadratic programme solvable in polynomial time.
2. In their portfolio illustration, the robust solution was far more stable than the nominal one. Across the simulations it never produced a loss, while the nominal policy lost money with probability 0.5. [author version; check figures against the VoR before quoting]

### `bertsimas2003robust`: Bertsimas and Sim (2003), Mathematical Programming 98
Access: full text (author version). Flags: [CT].
1. Bertsimas and Sim (2003) extended budgeted robustness to discrete optimisation. When cost coefficients and constraint data of an integer programme are uncertain, their robust integer programme is only moderately larger and controls conservatism through probabilistic bounds on constraint violation.
2. When only the cost coefficients of a 0-1 problem on n variables are uncertain, the robust counterpart can be solved by solving at most n+1 instances of the nominal problem, so polynomially solvable problems remain polynomially solvable.

### `bertsimas2004price`: Bertsimas and Sim (2004), Operations Research 52(1)
Access: full text (author version) and abstract (VoR). Flags: [CT].
1. Bertsimas and Sim (2004) proposed robust linear optimisation in which the level of conservatism is adjusted flexibly, in terms of probabilistic bounds on constraint violation, while the robust formulation remains a linear optimisation problem that extends tractably to discrete problems.
2. In their model, uncertain coefficients are symmetric, bounded random variables. A per-constraint protection level limits how many coefficients are assumed to deviate from their nominal values. [full text]

### `campi2008exact`: Campi and Garatti (2008), SIAM Journal on Optimization 19(3)
Access: abstract only (publisher page). Flags: [CT] (sampled constraints).
1. Campi and Garatti (2008) established the exact feasibility of solutions obtained by constraint randomisation (sampled constraints) for fully-supported uncertain convex programmes. They also bounded the feasibility of randomised solutions for all other convex programmes; the result cannot be improved because it is exact for fully-supported problems.

### `luedtke2008sample`: Luedtke and Ahmed (2008), SIAM Journal on Optimization 19(2)
Access: abstract only (publisher page). Flags: [CT] (sample-based margins).
1. Luedtke and Ahmed (2008) studied replacing the distribution in a chance-constrained problem with an empirical distribution from a random sample. Solving the sample problem at a higher risk level yields a lower bound on the true optimum with probability approaching one exponentially fast. Under stated conditions, solving it at a lower risk level yields feasible solutions with high probability.
2. They derived a priori estimates of the sample size needed for either guarantee.

### `bertsimas2018datadriven`: Bertsimas, Gupta and Kallus (2018), Mathematical Programming 167(2)
Access: full text (arXiv author version), used at abstract level. Flags: [CT] (data-driven sets).
1. Bertsimas et al. (2018) proposed designing uncertainty sets for robust optimisation from data using statistical hypothesis tests. The resulting robust problems are computationally tractable, and their optimal solutions enjoy a finite-sample probabilistic guarantee.
2. In portfolio management and queueing experiments, the data-driven sets significantly outperformed traditional robust optimisation techniques when data were available.

---

## (d) Out-of-sample and rolling-origin evaluation

### `tashman2000outofsample`: Tashman (2000), International Journal of Forecasting 16(4)
Access: bibliographic only (no abstract or text reachable). Flags: none (protocol background). Seed paper.
- Safe now (title level): "Tashman (2000) reviews out-of-sample tests of forecasting accuracy."
- Safe via a verified citing source: "Cerqueira et al. (2020) note, following Tashman (2000), that applying hold-out evaluation over multiple test periods gives more reliable estimates than a single partition, and their experiments support this."
- Do not attribute specific recommendations (rolling origin, updating, window schemes) to Tashman until the article has been read.

### `smith2006optimizer`: Smith and Winkler (2006), Management Science 52(3)
Access: abstract only (publisher page). Flags: [OOS] (rationale).
1. Smith and Winkler (2006) showed that when alternatives are ranked by estimated values and the best is selected, the chosen alternative's true value should be expected to fall below its estimate, even when the estimates are unbiased. They call this the optimizer's curse and show the expected disappointment can be substantial.
2. They propose Bayesian adjustment of value estimates to avoid this post-decision disappointment.

### `bergmeir2018note`: Bergmeir, Hyndman and Koo (2018), Computational Statistics & Data Analysis 120
Access: full text (Monash working-paper version), used at abstract level. Flags: none (protocol background).
1. Bergmeir et al. (2018) showed that for purely autoregressive models, standard K-fold cross-validation can be used for time series evaluation provided the models have uncorrelated errors. In their simulations and real-world example it performed favourably compared with out-of-sample evaluation and non-dependent cross-validation.

### `cerqueira2020evaluating`: Cerqueira, Torgo and Mozetič (2020), Machine Learning 109(11)
Access: full text (VoR, open access). Flags: [OOS] (protocol).
1. Cerqueira et al. (2020) compared 11 performance-estimation methods (cross-validation variants, hold-out, repeated hold-out and prequential schemes) on 174 real-world time series (97 stationary, 77 non-stationary) and on synthetic series.
2. Blocked cross-validation was suitable for stationary series. For non-stationary series, out-of-sample methods gave the most accurate estimates, in particular hold-out repeated over multiple testing periods.

### `vanparys2021data`: Van Parys, Mohajerin Esfahani and Kuhn (2021), Management Science 67(6)
Access: abstract (VoR) and full text (arXiv author version). Flags: [OOS] [CT] (rationale).
1. Van Parys et al. (2021) defined out-of-sample disappointment as the probability that the actual expected cost of a data-driven decision under the unknown true distribution exceeds its predicted cost. They sought the least conservative data-driven predictors and decisions whose disappointment is constrained.
2. They proved that the optimal choice solves a distributionally robust optimisation problem over all distributions within a given relative-entropy distance of the empirical distribution. Their setting assumes a finite set of independent samples.

---

## Usage cautions for the writer

1. **Out-of-sample claims about storage studies.**
   - Waubert de Puiseau et al.: a single temporal split.
   - Mirzaei et al.: a random split plus a synthetic demand-change test.
   - Winkelmann et al.: simulated weeks drawn from fitted distributions.

   Supported by the included set: "no included storage study evaluates across several successive origins". Do not claim that no such study exists anywhere; the search was not exhaustive (see `LITERATURE_REVIEW.md` section 5).
2. **Claims that no one has combined workload-share constraints with budgeted or data-driven tightening.** Phrase as "we found no study that ...". The closest works are Winkelmann et al., Dündar, Ang et al., Zhang et al., and Kim and Hong.
3. **Pick-and-pass classics not verified here.** Pan and Wu (2009) and Pan et al. (2015) are eligible but their content could not be accessed. Read them before citing. Winkelmann et al.'s description of Pan et al. (2015) is secondary.
4. **Guarantees from (c).** They rest on independence or random-sampling assumptions (stated in Bertsimas and Sim 2004, Luedtke and Ahmed 2008, and Van Parys et al. 2021). If the manuscript uses such margins on autocorrelated, seasonal demand, present them as calibrated heuristics evaluated out of sample, not as carrying the formal guarantee.
