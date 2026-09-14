# Literature review: storage assignment and workload balance under uncertain and changing demand

Prepared 2026-09-14 for the lead writer of the extension article on storage location assignment in automated pick-and-pass warehouses. This file supports the writing; it is not manuscript text.

Evidence tags used throughout:

- **[Article]**: reported by the cited article and checked against its full text or abstract. Section 2 gives the access level for each article.
- **[NotebookLM]**: synthesis produced by NotebookLM. It is reported only where it was checked, and the check result is stated.
- **[Interpretation]**: my own reading across articles. It is not a finding of any single article.

---

## 1. Search and selection

### 1.1 Scope

The review covers four strands:

- **(a)** Workload or workload-balance constraints in storage and station assignment, in pick-and-pass, zone and robotic picking.
- **(b)** Robust, scenario-based, stochastic and data-driven storage assignment, and re-slotting under changing demand.
- **(c)** Robust optimisation foundations: constraint tightening and budgeted robustness, data-driven uncertainty sets, and scenario or sampled constraints.
- **(d)** Out-of-sample and rolling-origin evaluation of decisions made on historical data.

### 1.2 Eligibility (applied as stated by the user)

- **Admitted:** peer-reviewed research or review articles published in scientific journals.
- **Excluded:** preprints without a journal version, conference papers, theses, books and book chapters, blogs, and web profiles.
- **Verification before eligibility:**
  - Every article was checked on the Crossref REST API: type `journal-article`, title, authors, container title, year, volume, issue and pages, plus `update-to`, `updated-by` and `relation` fields for retractions or corrections.
  - Every article was also checked on OpenAlex (`is_retracted`).
  - All 31 included articles are Crossref `journal-article` records, have `is_retracted = false`, and carry no correction or retraction relation.
- **Journal peer review for the less familiar venue:** the Alphanumeric Journal policy page on DergiPark (checked 2026-09-14) states double-blind review with at least two referee approvals.

### 1.3 Selection

I selected articles for direct relevance to (a) to (d), transparent methods and substantive findings. Seminal and recent work are both represented. Citation counts and recency were not used as quality criteria.

An article was admitted to the evidence table only if I could read its abstract or full text. Six otherwise promising, eligible articles were set aside because neither was reachable from this host (section 4.1). One seed paper, Tashman (2000), passed bibliographic eligibility but could not be read. It is kept as a bibliographic-only entry, and its content is not attributed (see the note under the table).

### 1.4 NotebookLM evidence base

- **Dedicated notebook:** "Lit review (journal articles only): robust storage assignment, workload balance, out-of-sample evaluation".
- **Notebook id:** `49cac84f-28b0-4175-b602-6cc535d580b5`.
- **Isolation:** created for this review. No other notebook in the account was used or modified.
- **Contents:** 21 sources, all eligible journal articles, covering 20 of the 31 included articles. Bertsimas and Sim (2004) appears twice, as a publisher page and as an author PDF.
  - 11 PDFs:
    - Version of record: Winkelmann et al. 2025, Dündar 2025, Tarczyński 2023, Cerqueira et al. 2020.
    - Author or working-paper versions of the published articles: Bertsimas-Gupta-Kallus 2018 (arXiv), Van Parys et al. 2021 (arXiv), Bertsimas-Sim 2003 and 2004 (MIT), Bergmeir et al. 2018 (Monash working paper), Ben-Tal-Nemirovski 1999 (author site), Yu-de Koster 2008 (ERIM working paper).
  - 10 publisher landing pages: Jane-Laih 2005, Ang et al. 2012, Christofides-Colloff 1973, Pazour-Carlo 2015, Mirzaei et al. 2021, Bertsimas-Sim 2004, Soyster 1973, Campi-Garatti 2008, Luedtke-Ahmed 2008, Smith-Winkler 2006.
- **Import failures:** 33 URL imports were attempted for paywalled articles: 23 DOI links, then 10 ScienceDirect PII links as a retry. Ten DOI links were indexed as publisher pages; the other 23 attempts failed (Elsevier, Emerald and Taylor & Francis blocked access; Springer returned HTTP 406). NotebookLM still registered all 23 failures in the notebook, as error-status entries or error pages ("Just a moment...", "Error", "Internal Server Error", "406 Not Acceptable"). I deleted those 23 so the notebook holds only articles; they were my own additions from this task.
- **Deep-research results:** none were bulk-imported. Every result was inspected by hand.

### 1.5 Queries and runs

| Step | Tool | Query or action | Output |
|---|---|---|---|
| Deep research run 1 (task `31fbc938-5566-4a0a-8671-2c7a0969c520`) | NotebookLM `source add-research --mode deep`, no import | "Find peer-reviewed journal articles (no preprints, conference papers or theses) on storage location assignment with workload balancing constraints in pick-and-pass, zone picking and robotic picking warehouses, and on robust, stochastic, scenario-based, data-driven or dynamic storage assignment and re-slotting under uncertain or changing demand. Give journal, year, authors and DOI for each." | 78 web results and a 41.7k-character report |
| Deep research run 2 (task `c9824c7b-cea3-4e67-bc61-b4a4efc3c470`) | same | "...on: (1) robust optimization with budgeted uncertainty or constraint tightening and safety margins for integer and assignment problems; (2) data-driven construction of uncertainty sets from historical samples; (3) the scenario approach and sampled or chance constraints with feasibility guarantees; (4) out-of-sample, hold-out and rolling-origin evaluation of decisions or forecasts built from historical data, including in-sample optimism of optimized decisions; and (5) applications of these methods to warehouse storage, slotting or workload planning..." | 76 web results and a 42.7k-character report (mostly off-topic or non-journal) |
| Title and topic searches | Crossref `query.bibliographic`, top 3 hits | About 95 queries: author-and-title strings for known and deep-research leads, plus topical strings (e.g. "pick-and-pass storage assignment workload balancing zones", "storage reassignment robotic mobile fulfillment order fluctuation", "robust storage location assignment demand uncertainty warehouse") | Candidate DOIs |
| Verification | Crossref + OpenAlex (DOI only, no personal data) | 92 distinct DOIs | 91 journal articles; 1 DOI not in Crossref (404) |
| Abstract retrieval where Crossref had none | Semantic Scholar Graph API (DOI only), IDEAS/RePEc pages, OpenAIRE, EconBiz, scholar.archive.org | 35 DOIs | Abstracts found for several; none for the six articles in section 4.1 or for Tashman (2000) |
| Cited questions (NotebookLM `ask`) | Dedicated notebook | a1 workload-balance modelling; a2 designs that evaluate on data other than the optimisation data; a3 conservatism and guarantees (failed twice: response over 50 MB); a3b same question restricted to the 8 robust-optimisation sources; a4 in-sample optimism and evaluation protocols; a5 re-slotting versus protection, restricted to 7 storage sources | Answers with source references; checked against the texts (section 3.4) |

### 1.6 Screening counts

| Stage | Count |
|---|---|
| Deep-research web results screened at title, venue and URL level | 154 (78 + 76) |
| Distinct DOIs verified bibliographically (Crossref + OpenAlex) | 92 |
| Included: content verified | 30 |
| Included: bibliographic record only (seed paper) | 1 (Tashman 2000) |
| Promising candidates listed as excluded in section 4 | 53 eligible journal articles, plus ineligible item types |

Most of the 154 web results were not journal articles (ResearchGate, Google Scholar and DBLP profiles, Sci-Hub mirrors, arXiv, SSRN, theses, conference papers), or were off topic.

---

## 2. Included articles

**Access codes:**

- **FT-VoR:** full text, version of record.
- **FT-AV:** full text, author or working-paper version of the published article.
- **FT-PP:** full text as indexed from the publisher page in NotebookLM.
- **ABS:** abstract only.
- **BIB:** bibliographic record only.

Keys refer to `verified_references.bib`.

### 2.1 (a) Workload balance in storage and station assignment

| Citation (key) | DOI | Research question | Method | Principal findings | Limitations | Why it matters | Access |
|---|---|---|---|---|---|---|---|
| Jane, C.-C. (2000). Storage location assignment in a distribution center. *Int. J. Physical Distribution & Logistics Management* 30(1), 55-71. (`jane2000storage`) | 10.1108/09600030010307984 | How to assign products to zones of a relay (pick-and-pass) pick line so pickers carry nearly equal loads, and how to adjust when order volume fluctuates. | Heuristics based on historical orders; a continuity index; simulation. | Balancing heuristic and two adjustment heuristics for order-volume fluctuation, verified on empirical data and by simulation. [Article] | Heuristic; single case; the abstract gives no quantitative gains. | Earliest identified work that makes workload balance across pick-and-pass pickers the storage objective and treats volume fluctuation. | ABS |
| Jane, C.-C., Laih, Y.-W. (2005). A clustering algorithm for item assignment in a synchronized zone order picking system. *EJOR* 166(2), 489-496. (`jane2005clustering`) | 10.1016/j.ejor.2004.01.042 | How to assign items to zones in synchronized zone picking to balance picker workload and cut idle time. | Co-appearance similarity from orders; natural-cluster model (relaxation of the NP-hard homogeneous cluster model); heuristic; simulation. | Balances workload among pickers and reduces order completion time on company data. [Article] | Synchronized (not sequential) zones; deterministic order data; abstract-level evidence. | Shows the co-appearance versus balance trade-off in zone assignment. | ABS (publisher page) |
| Yu, M., De Koster, R. (2008). Performance approximation and design of pick-and-pass order picking systems. *IIE Transactions* 40(11), 1054-1069. (`yu2008pickandpass`) | 10.1080/07408170802167613 | How to estimate lead time and utilisation of pick-and-pass systems quickly, including the effect of station storage policy. | G/G/m queueing network (Whitt's QNA); simulation validation. | The approximation is accurate enough for design use [Article]. In the working-paper example, a uniform storage policy gives shorter mean order throughput times than a non-uniform one, with the gap widest at the heaviest load (20.31%, Table 6) [Article, working-paper version]. | Steady-state analytical model; storage policy compared rather than optimised; the number comes from the working-paper version. | Performance basis for why balanced station loads matter in pick-and-pass lines. | ABS + FT-AV |
| Tarczyński, G. (2023). Linear programming models for optimal workload and batching in pick-and-pass warehousing systems. *Operations Research and Decisions* 33(3). (`tarczynski2023`) | 10.37190/ord230309 | Joint zone assignment with workload balance, plus batching and sequencing, for pick-and-pass systems. | MILPs: zone assignment minimising the maximum expected zone workload; batching and sequencing models; generated instances (80-20 demand curve). | Storage plus batching optimisation reduces total picking time by about 35-45% versus random policies; balancing expected zone workload alone with random batching gives 10-20% [Article]. The author notes that storage decisions based on historical data carry uncertainty, since even perfectly balanced zones can see unequal workloads for a particular order set [Article]. | Expected-demand model; orders drawn from the same distribution used for the assignment (no hold-out); exemplary instances. | Closest formulation to a workload-share model for pick-and-pass zones; already cited by the companion paper. | FT-VoR |
| Fedtke, S., Boysen, N., Schumacher, P. (2023). In-line kitting for part feeding of assembly lines: workload balancing and storage assignment to reduce the workers' walking effort. *OR Spectrum* 45(3), 717-758. (`fedtke2023inline`) | 10.1007/s00291-023-00723-1 | How to reduce picker walking in in-line kitting stations, where kits pass stations along a conveyor. | Optimisation model combining station workload balancing with container storage assignment; solution procedures; computational study. | Walking effort can be reduced significantly by balancing workload among stations and optimising storage within stations, without additional cost. [Article] | Assembly-line kitting rather than a warehouse; deterministic. | Structural analogue of pick-and-pass: serial stations, a passing flow, and balance plus storage decided jointly. | ABS |
| Kim, J., Hong, S. (2022). A dynamic storage location assignment model for a progressive bypass zone picking system with an S/R crane. *JORS* 73(5), 1155-1166. (`kim2022dynamic`) | 10.1080/01605682.2021.1892462 | Storage assignment that balances zone workload and reduces recirculation, and reassignment under limited relocation capacity. | Storage location assignment (SLA) model balancing a weighted sum of picks and visits across zones; storage location reassignment (SLR) model moving prioritised product pairs; simulation on industry orders. | Completion time reduced by 9.2-13.6% (SLA) and 5.9-8.9% (SLR); SLR preferable when only minimal changes are allowed. [Article] | Deterministic demand inputs; single system type; abstract-level evidence. | Links a workload-balance assignment directly to capacity-limited re-slotting. | ABS |
| Yuan, R., Cezik, T., Graves, S.C. (2018). Stowage decisions in multi-zone storage systems. *IJPR* 56(1-2), 333-343. (`yuan2018stowage`) | 10.1080/00207543.2017.1398428 | How to spread inventory across zones with limited picking capacity to meet uncertain demand. | Simulation study of zone-stowage policies. | Two policies balance picking workload across zones: a chaining-inspired split across two zones, and stowing to the zone with the smallest expected workload. [Article] | Policy comparison, not optimisation; simulation-based. | Balance under uncertain demand, obtained by hedging allocations across zones. | ABS |
| Zhang, J., Tian, L., Zhou, Z. (2024). Joint optimization of item and pod storage assignment problems with picking aisles' workload balance in robotic mobile fulfillment systems. *Complexity* 2024, 1-15. (`zhang2024joint`) | 10.1155/2024/9260431 | Joint item-to-pod and pod-to-location assignment in RMFS with a picking-aisle workload balance constraint. | MIP; improved genetic algorithm; comparison with Gurobi and two-stage heuristics. | Robot movement distance increases with more stringent workload balance constraints; distance is smallest when the storage area's width-to-length ratio is close to 1. [Article] | Abstract-only access (the open PDF could not be fetched from this host); experimental design not checked. | Explicit workload-balance constraint in storage assignment with a reported price of tightening it. | ABS |
| Winkelmann, D., Tolkmitt, F., Ulrich, M., Römer, M. (2025). Integrated storage assignment for an e-grocery fulfilment centre: accounting for day-of-week demand patterns. *FSMJ* 37(2), 558-598. (`winkelmann2025integrated`) | 10.1007/s10696-024-09549-7 | Integrated selection, station and shelf assignment for an 8-station pick-and-pass loop with balanced station workloads and day-of-week demand. | MILP with constraints bounding each station's relative deviation from the average daily picks (threshold δ); fix-and-optimise heuristic; variation-aware extension with day-of-week constraints; simulation over 52 weeks × 6 days, 100 runs, coefficient of variation (CV) 0.05-0.3. | Average-demand assignment exceeds 3% day-of-week deviation. Day-of-week constraints bring it below 1%, with the objective deviation up by 0.11 percentage points. In simulated week-to-week variation at CV 0.05, maximum deviation exceeds 4% (basic) versus 2.46% (variation-aware), and mean deviation falls from 1.01% to 0.57%. At CV 0.3 the benefit shrinks to 7.48% (mean) and 6.75% (maximum). [Article] | Single retailer; simulated rather than observed later weeks; the balance target is still exceeded out of sample. The authors name robust or stochastic optimisation as future work. | Closest setting overall: workload-share constraints in pick-and-pass storage, with explicit evidence that constraints set on averages are violated under realised variation. | FT-VoR |
| Debold, S. (2025). A storage assignment approach considering SKU repetitions in sequential zone picking. *C&IE* 210, 111482. (`debold2025skurepetitions`) | 10.1016/j.cie.2025.111482 | Whether storing the same SKU in several zones mitigates zone imbalance under high demand variability. | Binary program; three-stage heuristic with variable neighbourhood search (VNS); simulation calibrated on real e-grocery data; real-world test. | Heuristic beats benchmarks on average by up to 19.5%; a few repetitions improve performance; real-world test shows up to 40% gains in zone workload balancing. [Article] | Abstract-level evidence; the repetition decision depends on SKU count and space. | Recent sequential-zone evidence that balance is threatened by demand variability. | ABS |

### 2.2 (b) Stochastic, robust, data-driven and dynamic storage assignment

| Citation (key) | DOI | Research question | Method | Principal findings | Limitations | Why it matters | Access |
|---|---|---|---|---|---|---|---|
| Christofides, N., Colloff, I. (1973). The rearrangement of items in a warehouse. *Operations Research* 21(2), 577-589. (`christofides1973rearrangement`) | 10.1287/opre.21.2.577 | Least-cost sequence of moves to rearrange items after relative demand changes. | Two-stage algorithm. | Optimal in the restricted case of short rearrangement cycles, with the warehouse kept operating. [Article] | Target layout taken as given; old model. | Seminal statement that demand change creates a costly rearrangement problem. | ABS |
| Thonemann, U.W., Brandeau, M.L. (1998). Optimal storage assignment policies for AS/RS with stochastic demands. *Management Science* 44(1), 142-148. (`thonemann1998stochastic`) | 10.1287/mnsc.44.1.142 | Do turnover- and class-based policies remain good under stochastic demand? | Analytical; discrete and continuous racks; k-th pallet formulation. | Turnover-based policy is optimal (minimises one-way travel time) under stochastic demand; both turnover- and class-based policies beat random storage. [Article] | Unit-load AS/RS; no workload constraints. | Early stochastic-demand result for storage policies. | ABS |
| Ang, M., Lim, Y.F., Sim, M. (2012). Robust storage assignment in unit-load warehouses. *Management Science* 58(11), 2114-2130. (`ang2012robust`) | 10.1287/mnsc.1120.1543 | Multiperiod storage and retrieval under variable supply and uncertain demand with partially known distributions. | Factor-based demand; robust model minimising worst-case expected travel; linear decision rule reduced to a moderate-size LP. | The robust linear policy comes close to the expected value with perfect information and significantly outperforms existing heuristics. [Article] | Unit-load setting; travel objective; no workload-balance constraints. | Reference application of robust optimisation to storage assignment. | ABS (publisher page) |
| Pazour, J.A., Carlo, H.J. (2015). Warehouse reshuffling: insights and optimization. *TR-E* 73, 207-226. (`pazour2015reshuffling`) | 10.1016/j.tre.2014.11.002 | How to optimise sequential repositioning of items, and what common assumptions cost. | Mathematical programme; complexity; heuristics; proof on when double-handling helps. | Proposed heuristics improve on a benchmark by relaxing cycle handling and allowing double-handling. [Article] | Given target layout; unit-load focus. | Quantifies the cost side of re-slotting. | ABS (RePEc + publisher page) |
| Kübler, P., Glock, C.H., Bauernhansl, T. (2020). A new iterative method for solving the joint dynamic storage location assignment, order batching and picker routing problem in manual picker-to-parts warehouses. *C&IE* 147, 106645. (`kubler2020iterative`) | 10.1016/j.cie.2020.106645 | Jointly solving dynamic storage assignment, batching and routing while accounting for future demand dynamics. | Iterative heuristic; numerical experiments. | May yield significant savings in travel distance. [Article] | Abstract-level; manual picker-to-parts setting; gains not quantified in the abstract. | Dynamic, demand-aware re-slotting integrated with operations. | ABS |
| Mirzaei, M., Zaerpour, N., de Koster, R. (2021). The impact of integrated cluster-based storage allocation on parts-to-picker warehouse performance. *TR-E* 146, 102207. (`mirzaei2021ica`) | 10.1016/j.tre.2020.102207 | Does integrating turnover and affinity from historical orders improve storage allocation in automated storage and retrieval (AS/R) and robotic mobile fulfilment (RMF) systems? | Integrated cluster allocation (ICA) model and heuristic; Monte Carlo demand-change test; real dataset with train/validation split. | Up to 40% retrieval-time reduction versus turnover- and class-based policies. When 10-100% of orders are replaced by random new orders (100 sets per level), ICA stays beneficial up to 60% change (AS/R) and 70% (RMF). On a real dataset (28,000 orders), 70% of orders were randomly selected for training and the rest used for validation. [Article] | The validation split is random, not temporal; one-way travel model in the main analysis. | Rare explicit test of a storage allocation on orders not used to build it, and of robustness to demand change. | FT-PP |
| Waubert de Puiseau, C. et al. (2022). Dynamic storage location assignment in warehouses using deep reinforcement learning. *Technologies* 10(6), 129. (`waubertdepuiseau2022dslap`) | 10.3390/technologies10060129 | Can deep reinforcement learning (DRL) learn a storage policy for the dynamic storage location assignment problem (DSLAP) from historical storage and retrieval data? | DRL agent trained on one year of operations; evaluated on the following two months. | 6.3% lower cost than the incumbent ABC-based strategy on the new data. [Article] | Single case; one temporal split; abstract-level evidence. | Only included study with a temporal (train-then-later-period) evaluation of a storage policy on real data. | ABS |
| Dündar, B. (2025). A robust optimization approach to address correlation uncertainty in stock keeping unit assignment in warehouses. *Alphanumeric Journal* 13(1), 1-12. (`dundar2025robust`) | 10.17093/alphanumeric.1670030 | SKU-to-location assignment with uncertain pairwise correlations. | Quadratic assignment problem (QAP) linearised; robust counterpart with Bertsimas-Sim budget Γ0 on how many correlation coefficients deviate within an interval; Gurobi; 5, 10 and 12 SKUs with generated correlations. | Objective rises with Γ0 and deviation size (e.g. 10 SKUs, 10% deviation: 293.7 at Γ0 = 0, 307.1 at Γ0 = 10). CPU time 1,372 s at 12 SKUs and 5,062 s at 13 SKUs; the author judges larger instances intractable. [Article] | Toy scale; synthetic correlations; robustness only in the objective (no uncertain constraints); no out-of-sample test. | Only included storage paper that applies budgeted robustness directly. | FT-VoR |
| Wu, X. (2026). Item storage reassignment problem in robotic mobile fulfillment systems under customer order characteristic fluctuations. *JORS*, advance online, 1-14. (`wu2026reassignment`) | 10.1080/01605682.2026.2616411 | How to reassign items to pods as the demand pattern evolves. | Interchange-guided sequencing algorithm (IGSA); computational experiments. | Demonstrates IGSA's effectiveness and analyses when reassignment should be performed under different item varieties and warehouse capacities. [Article] | Advance online (no volume yet); abstract-level evidence. | Most recent work on when to re-slot under demand change. | ABS |

### 2.3 (c) Robust optimisation foundations

| Citation (key) | DOI | Research question | Method | Principal findings | Limitations | Why it matters | Access |
|---|---|---|---|---|---|---|---|
| Soyster, A.L. (1973). Convex programming with set-inclusive constraints and applications to inexact linear programming. *Operations Research* 21(5), 1154-1157. (`soyster1973convex`) | 10.1287/opre.21.5.1154 | Optimisation when feasibility is defined by set containment. | Convex programming; auxiliary LP. | Under a special resource-set form the problem reduces to an LP, applicable to inexact LP. [Article] | Protection against all set members; very conservative [Interpretation]. | Origin of worst-case (set-inclusive) robust LP. | ABS |
| Ben-Tal, A., Nemirovski, A. (1999). Robust solutions of uncertain linear programs. *Operations Research Letters* 25(1), 1-13. (`bental1999robust`) | 10.1016/S0167-6377(99)00016-4 | Tractable robust counterparts of uncertain LPs. | Robust counterpart theory; ellipsoidal uncertainty; portfolio example. | The robust counterpart with ellipsoidal uncertainty is a conic quadratic programme solvable in polynomial time [Article]. In the example, the robust policy never produced a loss in 3,600 simulations and its yield was about 15 times more stable than the nominal policy, which lost 9% with probability 0.5 [Article, author version]. | Ellipsoidal sets give nonlinear counterparts; the example is illustrative. | Tractability basis for margin-type robust constraints. | FT-AV |
| Bertsimas, D., Sim, M. (2003). Robust discrete optimization and network flows. *Math. Programming* 98, 49-71. (`bertsimas2003robust`) | 10.1007/s10107-003-0396-4 | Budgeted robustness for integer and 0-1 problems. | Robust integer programme of moderately larger size; probabilistic bounds. | Conservatism is controlled through probabilistic bounds on constraint violation. With cost-only uncertainty in 0-1 problems, the robust counterpart needs at most n+1 nominal solves, so polynomially solvable problems stay polynomial. [Article] | Bounds assume independent, bounded, symmetric coefficient deviations [Article, full text]. | Budget-of-uncertainty tool for integer assignment models. | FT-AV |
| Bertsimas, D., Sim, M. (2004). The price of robustness. *Operations Research* 52(1), 35-53. (`bertsimas2004price`) | 10.1287/opre.1030.0065 | How to reduce the conservatism of robust LP. | Protection level Γ per constraint limiting how many coefficients deviate; linear robust counterpart; probability bounds. | Conservatism adjusted via probabilistic bounds on constraint violation; the robust formulation stays linear and extends to discrete problems. [Article] | Independence and symmetry assumptions; the bounds are a priori, not data-calibrated [Interpretation]. | Standard reference for constraint tightening with a tunable budget. | FT-AV + ABS |
| Campi, M.C., Garatti, S. (2008). The exact feasibility of randomized solutions of uncertain convex programs. *SIAM J. Optimization* 19(3), 1211-1230. (`campi2008exact`) | 10.1137/07069821X | Feasibility of solutions obtained from sampled constraints. | Theory for the scenario (constraint randomisation) approach. | Exact feasibility result for fully-supported problems; a bound for all other convex programs that cannot be improved. [Article] | Convex programmes only; i.i.d. sampling is the usual setting [Interpretation, not verified in text]. | Guarantee basis for sampled-constraint (scenario) margins. | ABS (publisher page) |
| Luedtke, J., Ahmed, S. (2008). A sample approximation approach for optimization with probabilistic constraints. *SIAM J. Optimization* 19(2), 674-699. (`luedtke2008sample`) | 10.1137/070702928 | Replacing a chance constraint's distribution by a sample. | Sample approximation theory; numerical illustration. | A higher-risk sample problem gives a lower bound with probability approaching one exponentially fast; a lower-risk sample problem gives feasible solutions with high probability; a priori sample sizes for both. [Article] | Assumes random samples from the true distribution [Article]. | Links sample size and risk level to feasibility, relevant to empirical percentile margins. | ABS (publisher page) |
| Bertsimas, D., Gupta, V., Kallus, N. (2018). Data-driven robust optimization. *Math. Programming* 167(2), 235-292. (`bertsimas2018datadriven`) | 10.1007/s10107-017-1125-8 | How to build uncertainty sets from data. | Uncertainty sets from statistical hypothesis tests; experiments in portfolio management and queueing. | Tractable sets whose robust solutions carry a finite-sample probabilistic guarantee; the data-driven sets significantly outperform traditional robust sets when data are available. [Article] | Guarantee relies on sampling assumptions (see a3b check in section 3.4). | Principled route from historical data to uncertainty sets and margins. | FT-AV (abstract-level use) |

### 2.4 (d) Out-of-sample and rolling-origin evaluation

| Citation (key) | DOI | Research question | Method | Principal findings | Limitations | Why it matters | Access |
|---|---|---|---|---|---|---|---|
| Tashman, L.J. (2000). Out-of-sample tests of forecasting accuracy: an analysis and review. *International Journal of Forecasting* 16(4), 437-450. (`tashman2000outofsample`) | 10.1016/S0169-2070(00)00065-0 | Not verified (no abstract or text accessible). Title-level scope: analysis and review of out-of-sample tests of forecasting accuracy. | Not verified. | Not verified. Secondary only: Cerqueira et al. (2020, full text) state that Tashman (2000) recommends applying out-of-sample evaluation over multiple test periods, and that their own results agree. [Article: Cerqueira et al.] | Bibliographic record only. | Seed and standard citation for multiple-origin evaluation; read the article before attributing content. | BIB |
| Smith, J.E., Winkler, R.L. (2006). The optimizer's curse: skepticism and postdecision surprise in decision analysis. *Management Science* 52(3), 311-322. (`smith2006optimizer`) | 10.1287/mnsc.1050.0451 | Why chosen alternatives disappoint relative to their estimates. | Analytical; Bayesian adjustment. | Selecting on estimated values makes the chosen alternative's value lower than its estimate on average, even with unbiased estimates; the disappointment can be substantial; Bayesian shrinkage is proposed. [Article] | Decision-analysis framing. | Justifies not scoring an optimised storage plan on its own training data. | ABS (publisher page) |
| Bergmeir, C., Hyndman, R.J., Koo, B. (2018). A note on the validity of cross-validation for evaluating autoregressive time series prediction. *CSDA* 120, 70-83. (`bergmeir2018note`) | 10.1016/j.csda.2017.11.003 | When is standard K-fold cross-validation (CV) valid for time series? | Theory; simulation; real example. | For purely autoregressive models with uncorrelated errors, standard K-fold CV is valid and performs favourably against out-of-sample and non-dependent CV. [Article] | Applies to autoregressive models with uncorrelated errors; breaks under heavy misspecification [Article]. | Counterpoint showing that protocol choice depends on the model and the data. | FT-AV |
| Cerqueira, V., Torgo, L., Mozetič, I. (2020). Evaluating time series forecasting models: an empirical study on performance estimation methods. *Machine Learning* 109(11), 1997-2028. (`cerqueira2020evaluating`) | 10.1007/s10994-020-05910-7 | Which performance-estimation method best predicts true out-of-sample loss? | 11 methods (CV variants, holdout, repeated holdout, prequential); 174 real series (97 stationary, 77 non-stationary) plus synthetic. | Blocked CV suits stationary series; for non-stationary series, repeated holdout over multiple test periods gives the most accurate estimates; a single holdout is relatively poor. [Article] | Univariate forecasting, not optimisation decisions. | Strongest verified evidence for multiple-origin temporal hold-out on drifting data. | FT-VoR |
| Van Parys, B.P.G., Mohajerin Esfahani, P., Kuhn, D. (2021). From data to decisions: distributionally robust optimization is optimal. *Management Science* 67(6), 3387-3402. (`vanparys2021data`) | 10.1287/mnsc.2020.3678 | Least conservative data-driven decisions with controlled out-of-sample disappointment. | Meta-optimisation; large deviations theory. | The optimal predictor-prescriptor pair solves a distributionally robust problem over a relative-entropy ball around the empirical distribution; out-of-sample disappointment is the probability that actual expected cost exceeds predicted cost. [Article] | Independent samples from the data-generating distribution [Article]. | Formalises in-sample optimism and its control. | ABS + FT-AV |

---

## 3. Synthesis

### 3.1 Agreements

1. **Workload balance is usually a hard deviation bound or a min-max objective, set on average or expected demand.**
   - [Article] Winkelmann et al. (2025) bound each station's relative deviation from the average daily picks by a threshold δ.
   - [Article] Tarczyński (2023) minimises the maximum expected zone workload.
   - [Article] Kim and Hong (2022) balance a weighted sum of picks and visits across zones.
   - [Article] Zhang et al. (2024) impose an aisle workload-balance constraint.
   - [Article] Jane (2000) and Jane and Laih (2005) make balance the aim of their heuristics.
   - [Article] Winkelmann et al. note that workload balancing appears in the objective or the constraint set of most zone-assignment studies they review.
2. **Balance set on averages does not hold for realised demand.**
   - [Article] In Winkelmann et al., the average-based assignment shows more than 3% day-of-week deviation against a 1% target. Under simulated week-to-week variation, even the day-of-week-aware model reaches 2.46% at CV 0.05.
   - [Article] Tarczyński (2023) states that zones balanced on expected demand can still receive unequal workloads for a particular order set.
   - [Article] Jane (2000) adds adjustment heuristics for order-volume fluctuation.
   - [Article] Debold (2025) motivates SKU repetition by imbalance under high demand variability.
3. **The reported efficiency cost of balance is small but not zero.**
   - [Article] Winkelmann et al.: objective deviation up by 0.11 percentage points for day-of-week balance.
   - [Article] Zhang et al.: robot distance increases as balance constraints tighten.
   - [Article] Fedtke et al.: walking reduced without additional cost.
   - [Interpretation] The price of balance depends on the setting, and none of these studies measures it out of sample.
4. **Re-slotting is costly and handled as its own decision.**
   - [Article] Christofides and Colloff (1973) and Pazour and Carlo (2015) optimise the move sequence.
   - [Article] Kim and Hong (2022) restrict reassignment to limited relocation capacity. Their SLR model gains 5.9-8.9% against 9.2-13.6% for full reassignment.
   - [Article] Wu (2026) analyses when reassignment should be performed.
   - [Article] Winkelmann et al. state that rearranging SKUs for short-term (day-of-week) variation is often not possible or practical, whereas seasonal or long-term change can justify rearrangement.
5. **Robust optimisation offers a graded menu of conservatism.**
   - [Article] Set containment (Soyster 1973).
   - [Article] Tractable ellipsoidal counterparts (Ben-Tal and Nemirovski 1999).
   - [Article] A budget on the number of deviating coefficients, with probabilistic violation bounds, that keeps LP and IP structure (Bertsimas and Sim 2003, 2004).
   - [Article] Uncertainty sets built from data through hypothesis tests, with finite-sample guarantees (Bertsimas et al. 2018).
   - [Article] Sampled-constraint guarantees (Campi and Garatti 2008; Luedtke and Ahmed 2008).
6. **Scoring an optimised decision on the data used to build it is optimistic, and temporal multi-origin testing is preferable on non-stationary data.**
   - [Article] Smith and Winkler (2006): the optimizer's curse.
   - [Article] Van Parys et al. (2021): out-of-sample disappointment.
   - [Article] Cerqueira et al. (2020): repeated holdout is best for non-stationary series. They attribute the multiple-test-period recommendation to Tashman (2000).

### 3.2 Disagreements and tensions

1. **Cross-validation versus temporal hold-out.**
   - [Article] Bergmeir et al. (2018) show that standard K-fold CV is valid, and favourable, for purely autoregressive models with uncorrelated errors.
   - [Article] Cerqueira et al. (2020) agree for stationary series (their synthetic scenario corroborates Bergmeir et al.) but find repeated holdout better for non-stationary real series.
   - [Interpretation] Warehouse order data show day-of-week and seasonal structure (Winkelmann et al.; Tarczyński). A random split such as Mirzaei et al.'s 70/30 order sample does not test drift. Rolling-origin evaluation is therefore the more defensible protocol for storage decisions.
2. **Protect against variation or rearrange.**
   - [Article] Ang et al. (2012) and Winkelmann et al. (2025) build static plans that absorb variation.
   - [Article] Mirzaei et al. (2021) report that ICA stays beneficial up to 60-70% random order change.
   - [Article] Christofides and Colloff, Pazour and Carlo, Kim and Hong, Kübler et al. and Wu instead adapt the assignment.
   - [Interpretation] These are complements at different time scales, which Winkelmann et al. make explicit. No included study chooses jointly between a protection margin and a re-slotting frequency.
3. **Guarantee assumptions versus warehouse data.**
   - [Article] Bertsimas and Sim assume independent, bounded, symmetric coefficient deviations.
   - [Article] Van Parys et al. assume independent samples.
   - [Article] Luedtke and Ahmed assume random samples from the true distribution.
   - [Interpretation] Daily or weekly demand in the included storage studies is autocorrelated and seasonal, so these guarantees do not transfer directly and must be checked empirically out of sample.
4. **Deterministic balance constraints versus realised balance.**
   - [Article] Winkelmann et al. show that constraints satisfied on annual day-of-week averages are exceeded in simulated weeks: 2.46% against a 1% target at CV 0.05, and more than 10% at CV 0.3.
   - [Interpretation] This is direct motivation for tightening workload-share constraints with a margin or a data-driven set. That step is not taken in the included storage literature.

### 3.3 Research gaps (all [Interpretation], each grounded in the cited articles)

1. **No robust workload-share model for pick-and-pass storage was found.** No included article combines workload-share constraints in pick-and-pass or zone storage assignment with constraint tightening (budgeted, data-driven or sampled) calibrated on historical orders. The closest pieces are:
   - Winkelmann et al.: deterministic day-of-week constraints, evaluated by simulation.
   - Dündar: budgeted robustness in the objective only, at most 13 SKUs.
   - Ang et al.: robust, but unit-load with a travel objective.
   - Zhang et al.; Kim and Hong: deterministic balance constraints.
2. **Out-of-sample evaluation of storage decisions is rare and never rolling-origin.** The designs found are:
   - Waubert de Puiseau et al.: one temporal split.
   - Mirzaei et al.: random order split plus a synthetic demand-change test.
   - Winkelmann et al.: simulated weeks drawn from fitted distributions.
   - Tarczyński: orders generated from the same distribution.
   - No included storage study evaluates across several successive origins, which Cerqueira et al. find most accurate for non-stationary data.
3. **The margin versus re-slotting trade-off is unquantified.** Kim and Hong and Wu address when and how much to re-slot. Winkelmann et al. propose robust or stochastic methods for random variation and multi-year data for structural change as future work. None measures how a protection margin changes the needed re-slotting frequency.
4. **Scale remains a barrier.** Dündar's robust QAP becomes intractable above about 13 SKUs. Ang et al. obtain tractability through linear decision rules in a unit-load setting. Winkelmann et al. needed a heuristic for their integrated MILP.
5. **Guarantees are not tested under temporal dependence.** The robust and sampled guarantees in (c) rest on independence or random-sampling assumptions. No included storage study tests whether nominal violation levels hold on later, dependent data.

### 3.4 NotebookLM outputs: what was checked and what failed

**Run 1 report (deep research).**
- Bibliographic errors found:
  - DOI of Pan and Wu (2009) given as 10.1016/j.cie.2009.01.002; Crossref: 10.1016/j.cie.2008.11.026.
  - DOI of Mirzaei et al. (TR-E) given as 10.1016/j.tre.2021.102207; Crossref: 10.1016/j.tre.2020.102207.
  - DOI of Li, Deng and Ma (IEEE Access 2024) given as 10.1109/ACCESS.2024.3352801; Crossref: 10.1109/access.2024.3385791.
  - Authors of Leon et al. (2023, *Mathematics*) given as "Manuel Chica, Angel A. Juan"; Crossref: Leon, Li, Peyman, Calvet, Juan.
  - The second author of Zhang et al. (2024) given as "Li Tian"; Crossref: Lingkun Tian.
- Unverified claim: it attributes a longitudinal "continuous daily healing" evaluation to Çobanoğlu et al. (2021). The abstract does not mention one.
- Consequence: no bibliographic fact was taken from the report.

**Answer a1 (workload-balance modelling).**
- Verified in the full texts: Winkelmann's deviation-bound constraints, the >3% versus <1% result, and the δ ≤ 1% recommendation; Tarczyński's min-max objective, 35-45% and 10-20%; the 20.31% value in Yu and de Koster's Table 6 (working-paper version).
- [NotebookLM], interpretive: calling the uniform storage policy one that "balances station workload" is NotebookLM's reading. The text defines it as equal storage space per product class across stations.

**Answer a2 (evaluation on other data).**
- Error: Mirzaei et al. attributed to "van den Berg et al.".
- Error: the 50,000-order benchmark dataset conflated with the 28,000-order validation dataset.
- Overstatement: it says ICA keeps "substantial savings even when 100% of orders are replaced". The article says ICA remains beneficial up to 60% (AS/R) and 70% (RMF) change.
- Verified: Winkelmann's 52 × 6-day, 100-run simulation and its numbers; Ben-Tal and Nemirovski's 400-simulation portfolio test.
- Not verified, not used: the claim that Bertsimas et al. (2018) select sets by 5-fold cross-validation.

**Answer a3b (conservatism and guarantees).**
- Consistent with the abstracts and full texts for the mechanism of each method.
- Not verified, not used: the specific bound expressions and assumption lists it gives (e.g. an exponential bound formula for Bertsimas-Sim, i.i.d. sampling for Bertsimas et al. and Campi-Garatti).

**Answer a4 (in-sample optimism, protocols).**
- Agrees with the verified abstracts of Smith and Winkler, Van Parys et al., Bergmeir et al. and Cerqueira et al.
- Not verified, not used: its framing of a "disagreement" between Bergmeir et al. and Cerqueira et al. goes beyond what Cerqueira et al. state; they say their first experiment corroborates Bergmeir et al.

**Answer a5 (re-slotting versus protection).**
- Verified: Winkelmann's statement that rearranging for short-term variation is often not practical; Tarczyński's remark on unequal zone workloads for particular order sets.
- Not verified, not used: its characterisation of Pazour and Carlo's loaded and unloaded travel components beyond the abstract.

---

## 4. Promising candidates excluded

### 4.1 Eligible journal articles, excluded because content could not be verified

For each of these, no abstract or full text was reachable. The DOI imports into NotebookLM failed; Crossref, OpenAlex, Semantic Scholar and OpenAIRE hold no abstract; and the publisher page blocked access. Bibliographic eligibility was confirmed. Read the full text before citing.

- Pan, J.C.-H., Wu, M.-H. (2009). *C&IE* 57(1), 261-268. 10.1016/j.cie.2008.11.026. Storage assignment for a pick-and-pass order picking line.
- Pan, J.C.-H., Shih, P.-H., Wu, M.-H., Lin, J.-H. (2015). *C&IE* 81, 1-13. 10.1016/j.cie.2014.12.010. GA storage assignment for pick-and-pass. Cited by Winkelmann et al. as showing, via simulation and queueing approximations, that workload balancing improves pick-and-pass performance (secondary).
- Park, J., Hong, S. (2025). *C&OR* 180, 107060. 10.1016/j.cor.2025.107060. Time-decomposed workload balancing in sequential zone picking.
- Park, J., Park, C., Hong, S. (2023). *C&IE* 185, 109700. 10.1016/j.cie.2023.109700. Gaussian-process storage assignment with risk assessment for progressive zone picking. Only the SSRN preprint abstract is available, and it is not used.
- Manzini, R., Accorsi, R., Gamberi, M., Penazzi, S. (2015). *IJPE* 170, 790-800. 10.1016/j.ijpe.2015.06.026. Class-based storage over life-cycle picking patterns.
- Carlo, H.J., Giraldo, G.E. (2012). *C&IE* 63(4), 1003-1012. 10.1016/j.cie.2012.06.012. Perpetually organised unit-load warehouses.

The following also had no accessible abstract and were lower priority:

- Kuo et al. (2016) *ASOC* 46, 143-150 (10.1016/j.asoc.2016.03.012).
- Melacini et al. (2011) *IJAMT* 53, 841-854 (10.1007/s00170-010-2881-2).
- Jewkes et al. (2004) *C&OR* 31(4), 623-636 (10.1016/s0305-0548(03)00035-2).
- Roy et al. (2019) *TR-E* 122, 119-142 (10.1016/j.tre.2018.11.005).
- Zhuang et al. (2024) *EJOR* 316(2), 718-732 (10.1016/j.ejor.2024.02.025).
- Li, Moghaddam, Nof (2016) *IJAMT* 84, 2179-2194 (10.1007/s00170-015-7806-7).
- Guo et al. (2021) *TR-E* 151, 102359 (10.1016/j.tre.2021.102359).
- Xu, Ren (2022) *C&IE* 172, 108618 (10.1016/j.cie.2022.108618).
- Keung, Lee, Ji (2021) *AEI* 50, 101369 (10.1016/j.aei.2021.101369).
- Ang, Lim (2019) *EJOR* 278(1), 186-201 (10.1016/j.ejor.2019.03.046).
- Baron et al. (2019) *EJOR* 276(2), 451-465 (10.1016/j.ejor.2019.01.043).
- Fildes (1992) *IJF* 8(1), 81-98 (10.1016/0169-2070(92)90009-x).
- Bergmeir, Benítez (2012) *Inf. Sci.* 191, 192-213 (10.1016/j.ins.2011.12.028).
- Calafiore, Campi (2005) *Math. Prog.* 102(1), 25-46 (10.1007/s10107-003-0499-y).

### 4.2 Eligible and verified, but excluded for scope, overlap or priority

**(a) Workload balance adjacent**
- Vanheusden et al. (2022) *IJPR* 60(7), 2126-2150 (10.1080/00207543.2021.1884307). Balance measures over time in order-picking planning, not storage. Already in the companion bibliography as `vanheusden2022workload`.
- Vanheusden et al. (2020) *C&IE* 141, 106269 (10.1016/j.cie.2020.106269). Operational daily workload balancing, not storage.
- Saylam, Çelik, Süral (2023) *IJPR* 61(7), 2086-2104 (10.1080/00207543.2022.2058433). Min-max routing in dynamic zones, not storage. In the companion bibliography.
- Parikh, Meller (2008) *TR-E* 44(5), 696-719 (10.1016/j.tre.2007.03.002). Workload imbalance as a cost in choosing batch versus zone picking; strategic.
- van Gils et al. (2017) *IJPR* 55(21), 6380-6393 (10.1080/00207543.2016.1216659). Workload forecasting for staffing in zone picking; not storage.
- Tu et al. (2021) *Enterprise Information Systems* 15(9), 1238-1259 (10.1080/17517575.2020.1811388). Cyber-physical-system pick-and-pass storage GA with balance and emergency replenishment; overlaps the Pan et al. line; simulation only.
- Zou et al. (2017) *IJPR* 55(20), 6175-6192 (10.1080/00207543.2017.1331050). Workstation assignment rules in RMFS; queueing, not storage.

**(b) Dynamic, robust or data-driven storage adjacent**
- Kim, Pais, Shen (2020) *IEEE T-ASE* 17(4), 1854-1867 (10.1109/tase.2020.2979897). Reoptimisation of item-to-pod assignment when similarity values change; relevant but pod-similarity rather than workload; cut to keep the set focused.
- Chou, Yu, Wu (2023) *IJSSOL* 10(1), 2228447 (10.1080/23302674.2023.2228447). Correlated storage assignment updated each replenishment cycle; no uncertainty or workload model.
- Xu, Ren (2020) *Complexity* 2020, 1621828 (10.1155/2020/1621828). Multistage dynamic storage assignment; overlaps Kübler et al.; simulation only.
- Çobanoğlu, Güre, Bayram (2021) *Pamukkale Univ. J. Eng. Sci.* 27(4), 520-531 (10.5505/pajes.2021.34979). Data-driven storage assignment case study; NotebookLM's claims about it could not be verified.
- Leon et al. (2023) *Mathematics* 11(7), 1577 (10.3390/math11071577). Simheuristic with operational stochasticity rather than demand change.
- Zarinchang et al. (2024) *J. Industrial and Production Engineering* 41(1), 40-59 (10.1080/21681015.2023.2263009). Multi-objective storage metaheuristic including worker safety; not uncertainty.
- Pang, Chan (2017) *IJPR* 55(14), 4035-4052 (10.1080/00207543.2016.1244615). Association-rule storage assignment on synthetic data.
- Venkitasubramony, Adil (2019) *IJPR* 57(5), 1345-1365 (10.1080/00207543.2018.1472402). Scenario-based robust warehouse design (size, lane depth), not assignment.
- Mirzaei et al. (2022) *IJPR* 60(2), 549-568 (10.1080/00207543.2021.1971787). Companion key `mirzaei2021`. The TR-E paper was preferred for its verified validation design.
- Yuan, Graves, Cezik (2019) *POMS* 28(2), 354-373 (10.1111/poms.12925). Velocity-based pod storage; fluid model without demand uncertainty.
- Cezik, Graves, Liu (2025) *POMS* 34(11), 3400-3415 (10.1111/poms.13745). Stowage policy.
- Weidinger, Boysen, Briskorn (2018) *Transportation Science* 52(6), 1479-1495 (10.1287/trsc.2018.0826). Rack parking decisions.
- Lamballais Tessensohn et al. (2020) *IISE Trans.* 52(1), 1-17 (10.1080/24725854.2018.1560517). Inventory allocation.
- Li, Deng, Ma (2024) *IEEE Access* 12, 51463-51484 (10.1109/access.2024.3385791). Item storage with non-empty pods.
- Hausman, Schwarz, Graves (1976) *Management Science* 22(6) (10.1287/mnsc.22.6.629) is seminal class-based storage but outside the uncertainty and workload scope.

**Reviews** (not needed for the claims above; content not checked beyond abstracts)
- Boysen, de Koster, Weidinger (2019) *EJOR* 277(2), 396-411 (10.1016/j.ejor.2018.08.023).
- Boysen, de Koster (2025) *EJOR* 320(3), 449-464 (10.1016/j.ejor.2024.03.026).
- Reyes et al. (2019) *IJIEC* 199-224 (10.5267/j.ijiec.2018.8.001).
- Gu et al. (2007) *EJOR* 177(1) (10.1016/j.ejor.2006.02.025).
- de Koster et al. (2007) *EJOR* 182(2) (10.1016/j.ejor.2006.07.009).
- Bertsimas, Brown, Caramanis (2011) *SIAM Review* 53(3) (10.1137/080734510).
- Gorissen et al. (2015) *Omega* 53 (10.1016/j.omega.2014.12.006).
- Gabrel et al. (2014) *EJOR* 235(3) (10.1016/j.ejor.2013.09.036).

**(c) and (d) adjacent**
- Calafiore, Campi (2006) *IEEE TAC* 51(5), 742-753 (10.1109/tac.2006.875041). Scenario approach in control design; Campi and Garatti (2008) retained as the sharper convex-programme result.
- Nemirovski, Shapiro (2006) *SIAM J. Optim.* 17(4) (10.1137/050622328). Convex approximations of chance constraints; not sampled.
- Mohajerin Esfahani, Kuhn (2018) *Math. Prog.* 171 (10.1007/s10107-017-1172-1). Wasserstein DRO; overlaps Van Parys et al.
- Bertsimas, Brown (2009) *OR* 57(6) (10.1287/opre.1080.0646). Uncertainty sets from risk measures; overlaps Bertsimas et al. (2018).
- Feizollahi, Feyzollahi (2015) *Operations Research Perspectives* 2, 114-123 (10.1016/j.orp.2015.06.001). Robust QAP with budgeted flows; not storage-specific.
- Dehghani Filabadi, Mahmoudzadeh (2022) *INFORMS J. Optimization* 4(3), 249-277 (10.1287/ijoo.2021.0069). Effective budget refinement.
- Kleywegt, Shapiro, Homem-de-Mello (2002) *SIAM J. Optim.* 12(2) (10.1137/s1052623499363220); Mak, Morton, Wood (1999) *ORL* 24 (10.1016/s0167-6377(98)00054-6). SAA and solution-quality bounds; outside the scope chosen.
- Ban, Rudin (2019) *OR* 67(1) (10.1287/opre.2018.1757); Bertsimas, Kallus (2020) *MS* 66(3) (10.1287/mnsc.2018.3253); Gupta, Rusmevichientong (2021) *MS* 67(1) (10.1287/mnsc.2019.3554); Elmachtoub, Grigas (2022) *MS* 68(1) (10.1287/mnsc.2020.3922). Data-driven decision-making; the in-sample optimism argument is covered by Smith and Winkler and Van Parys et al.
- Hyndman, Koehler (2006) *IJF* 22(4) (10.1016/j.ijforecast.2006.03.001). Accuracy measures, not protocols.

### 4.3 Ineligible item types seen in screening

- **Preprints and posted content:**
  - arXiv 2209.03998, the preprint of Winkelmann et al.; the journal version is used.
  - Several SSRN posted-content records (2016-2026), including preprint versions of Park-Park-Hong, Hong-Park and Debold, and of Debold-Gönsch-Dochow, whose journal version (*OR Spectrum* 2025) is out of scope.
- **Conference papers:**
  - Kofler et al. (2011, LINDI).
  - Cai et al. (2016, LISS), "storage frequency and workload balance".
  - Hvolby et al. (2026, ICINT).
  - A CEUR-WS workshop paper and a SPIE proceedings paper (2025).
  - Thi et al. (2020, GTSD).
- **Book chapters:** Kofler et al. (2014); Chabot et al. (2024, in the companion bibliography); a Bertsimas-Thiele tutorial.
- **Theses:** TDX, ThinkIR, and a TU/e master thesis.
- **Profiles and aggregators:** ResearchGate, Google Scholar, DBLP, Connected Papers, SciSpace, Sci-Hub mirrors.
- **Unverifiable:** a Chinese-language *Chinese Journal of Management Science* (2026) article on RMFS replenishment with aisle workload balance. Its DOI 10.16381/j.cnki.issn1003-207x.2024.0687 returns 404 at Crossref, and the text was not accessible.

---

## 5. Access limitations and caveats

- **Abstract-only evidence:** 13 included articles are supported at abstract level only (ABS in section 2). Statements about them should stay at the level of what the abstract says.
- **Author and working-paper versions:** these were used for Ben-Tal and Nemirovski (1999), Bertsimas and Sim (2003, 2004), Bertsimas et al. (2018), Van Parys et al. (2021), Bergmeir et al. (2018) and Yu and de Koster (2008). Page-specific numbers taken from them should be checked against the version of record before quoting. Yu and de Koster's 20.31% is one such number.
- **Tashman (2000):** bibliographic verification only. The recommendation to evaluate over multiple test periods is attributed to Tashman here only through Cerqueira et al. (2020).
- **Search coverage:** limited to NotebookLM deep research (Google web index) and Crossref title and topic searches. Scopus and Web of Science were not available. Recent articles, non-English journals and very new online-first items may be missing.
- **Blocked retrieval:** Elsevier, Emerald and Taylor & Francis pages blocked automated retrieval from this host. This, not a quality judgement, is why several relevant Elsevier articles (section 4.1) are absent from the evidence table.
