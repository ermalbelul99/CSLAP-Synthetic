15 August 2026

To the Editor-in-Chief and Editorial Board
*International Journal of Production Research*
Taylor & Francis Group

RE: Submission of "Efficient and practical solutions for the correlated storage location assignment problem in automated pick-and-pass warehouses" as a Research Article

Dear Editor-in-Chief and Editorial Team,

Please find enclosed our manuscript for consideration as a Research Article.

The decision we address belongs to the slotting planner of an automated pick-and-pass distribution centre: which of tens of thousands of SKUs to hold at each picking station, under a fixed slot count and an engineered daily workload budget. No picker walks in these systems. Travel distance, the objective that dominates the correlated storage location assignment literature, measures nothing the facility pays for. What it pays for is how often a tote leaves the main line and merges back, so we pose the problem around station visits under hard capacity and workload caps.

That objective is piecewise constant. Relocating one product usually changes nothing, and the linear relaxation says no more than that every order visits some station, so branch-and-bound and single-swap metaheuristics stall. All three of our methods move whole product groups: a set-variable reformulation of the mixed-integer programme, a set-partitioning column generation driven as a price-and-complete matheuristic, and a clustering heuristic whose community bound is indexed on station slot capacity rather than catalogue size.

We validate on 29 benchmark instances of 50 to 2,000 products with paired statistical testing, and on an operating warehouse of 21,874 products and 26 stations, where the set-variable MILP removes 13.7% of station visits inside every workload limit. A layout is fitted once and then operated as demand moves, so we also evaluate on unseen weeks. There the reduction is 6.6 to 7.4%. That figure, not the in-sample one, is what a site should plan against: some 5,400 to 6,050 fewer stops per week.

Which method to deploy depends on whether a site's stations are interchangeable, and we report where each wins. A bounded-reassignment model caps how many SKUs may move in a cycle, so a manager can set the relocation budget against labour and know the marginal return. That return is sub-proportional, and we say why. Re-optimising on a rolling window of eight to ten weeks holds most of the gain.

We chose IJPR because the contribution is a decision aid for a production system that already exists, and because it rests on this journal's own corpus: nine of our references are IJPR articles. It sets no shop-floor control rule, which would belong in *Production Planning & Control*, and no integration architecture, which would suit *IJCIM*. It settles the placement daily operations inherit, tested against a real facility.

The required declarations follow. The manuscript is original, unpublished, not under consideration elsewhere, and has no preprint or earlier conference version. It involves no human or animal subjects, so ethics approval does not apply. Funding came from the Association Nationale de la Recherche et de la Technologie under a CIFRE grant with Savoye, and the authors have no competing interests. Both synthetic instance families and the per-instance convergence records are openly available through an anonymised link in the Data Availability Statement, de-anonymised on acceptance. The industrial dataset is confidential and available on request.

Thank you for considering our manuscript.

Sincerely,

Ermal Belul
Doctoral researcher (CIFRE)
Université de technologie de Compiègne, CNRS, Heudiasyc UMR 7253, Compiègne, France, and Savoye, France
ermal.belul@hds.utc.fr | +33 7 51 59 39 10
ORCID: 0009-0006-3589-6267

On behalf of the co-authors:
Marwane Bouznif, Savoye, France (ORCID 0000-0002-5138-1582)
Dritan Nace, Université de technologie de Compiègne, CNRS, Heudiasyc UMR 7253, France (ORCID 0000-0003-3914-2463)
Antoine Jouglet, Université de technologie de Compiègne, CNRS, Heudiasyc UMR 7253, France (ORCID 0000-0001-9251-249X)
