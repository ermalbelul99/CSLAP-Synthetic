# Writing package for final examination (draft; completed at handoff)

This is the handoff for the extension article, prepared under `WRITE_NOW_DIRECTIVE.md`. It lists what was written, how it was reviewed, the literature review deliverables, and what the authors still need to decide.

**Results were reused, not revalidated during writing.** Every number in the manuscript comes from the accepted evidence inputs (`evidence/anchors.json`, `evidence/document_values.json`, the claim register and the submitted companion). No solver was called, no test was run, no stored layout was revalidated or rescored, no raw order was read and the reserved tail of orders was not used. **No PDF was compiled**; the authors compile on Overleaf.

## 1. What to open

| File | Content |
|---|---|
| `manuscript/main.tex` | Title, abstract, keywords, section inputs, declaration placeholders |
| `manuscript/sections/01_introduction.tex` ... `07_conclusion.tex` | The seven sections |
| `manuscript/supplement.tex` | Standalone supplementary material, sections S1 to S6 |
| `manuscript/figures/` | Two figures (PDF for LaTeX, PNG for viewing) |
| `manuscript/references.bib` | Companion bibliography plus verified entries from the literature review |
| `manuscript/AUTHOR_QUESTIONS.md` | Questions raised during writing |
| `literature/LITERATURE_REVIEW.md` | Literature review deliverables (1) to (4) |
| `literature/citation_notes_for_writer.md`, `literature/verified_references.bib` | Attributable statements per article; verified BibTeX |
| `AI_USE_RECORD.md` | Truthful record of AI use |
| `WRITING_PROGRESS.md` | Short progress log |

Overleaf: upload `main.tex`, `sections/`, `figures/` and `references.bib` as one project (apacite with BibTeX); compile `supplement.tex` as a second document with the same bibliography.

## 2. Manuscript status

**State:** complete first draft after two bounded review rounds and a final fix pass; ready for the authors' examination, not for submission.

**Approximate length** (words, including table and caption text; the abstract is prose only):

| Part | Words |
|---|---|
| Abstract | 242 |
| 1 Introduction | 1,120 |
| 2 Related work (with comparison table) | 1,620 |
| 3 Information contract and share-policy formulation | 2,280 |
| 4 Data, protocol and staged design | 1,710 |
| 5 Results (seven tables and two figures in the article overall) | 3,190 |
| 6 Discussion | 2,520 |
| 7 Conclusions | 350 |
| Sections total | about 12,800 |
| Supplement (S1 to S6) | about 2,800 |

**Lightweight document checks (write-now directive):** every `\input` and figure file exists; every `\ref`/`\eqref` label is defined; all 26 cited keys resolve in `references.bib` (61 entries, no duplicate keys, no companion entry removed); no internal dataset name, station code or order identifier in the manuscript, figures, supplement, handoff files or literature files; no em dashes in prose; no significance-test wording; the predeclared label "Replication endpoint" is quoted once with its qualifier. Every number in the text and tables was traced by the orchestrator to `evidence/anchors.json` or `evidence/document_values.json` at each pass, and the scientific reviewer rechecked the held-out numbers in both rounds.

**Visible `\authorreview` markers (16), all needing the authors:**

- `main.tex` (6): author block; data availability; funding; competing interests; author contributions; AI-use statement wording.
- `sections/03_model.tex` (2): definition of a complete order; criteria of the order-retention rule.
- `sections/04_protocol.tex` (1): solver, model representation and time limits of the exploratory campaigns, and the representation of the held-out solves.
- `supplement.tex` (7): author block; held-out solver timings, objectives, version and hardware; definition of a large order; upper-only synthetic outcomes by stratum; two-sided synthetic outcomes by cell; per-horizon Company A breaches and visits; exploratory-origin drift distances.

**Not done, by design:** no PDF compilation; no final language pass by `clean-scientific-writer` or `academic-prose-auditor` (the directive makes it optional, and two narrative review rounds already covered templated and promotional patterns; it can be run on request).

**Internal files are not for circulation.** `evidence/`, `governance/` and the scratch material behind this package use the internal dataset name and station codes. Share only `manuscript/`, `literature/` and the top-level handoff files.

## 3. How the text was produced and reviewed

One lead writer (`academic-writer`, Opus) wrote and integrated every manuscript file; reviewers only commented; the orchestrating assistant decided which comments to accept, checked each pass against the evidence and did not edit manuscript prose.

| Step | Who | What it produced or changed |
|---|---|---|
| Figures | Orchestrator | Two presentation-only re-plots of stored held-out rows; highlighted out-of-band markers match the anchored breach counts for all 12 solves |
| Pass 1 | Lead writer | `main.tex`, Introduction, Model, Protocol, Results; every table and prose number traced to the anchors by the orchestrator |
| Formulation review | `formulation-reviewer` | 9 comments (4 must-fix): zero-workload products wrongly described as fixed in place; activation set undefined for an empty inactive set; nonlinear station indicators without their linear rows; a single-point range compared with the wrong share. All accepted (one suggested sentence replaced by claim-register wording) |
| Pass 1b | Lead writer | Model and Protocol corrected; notation P^0 and K_t |
| Pass 2a | Lead writer | Discussion, Conclusions, supplement S1 to S6, provisional abstract, declaration placeholders |
| Literature | `notebooklm-researcher` | `literature/` package (section 4 below); all 31 DOIs re-resolved on Crossref by the orchestrator |
| Pass 2b-i | Lead writer | Related Work with a comparison table; 23 verified references merged |
| Review round 1 | `narrative-reviewer`, `scientific-reviewer` | Narrative: contribution order, Discussion repeating Results, table recital in Results, repeated qualifiers, templated sentences. Scientific: every held-out number rechecked (all match); an unpredeclared comparison used as a headline without its qualifiers; one unsupported site check; abstract fidelity; gap unit; undefined terms |
| Revision | Lead writer | Consolidated changes from both reviews, literature markers resolved, Related Work fixes |
| Review round 2 (final) | same reviewers | Scientific: round 1 findings resolved; no revised number conflicts with the anchors; new: minimum slack described backwards, Winkelmann et al. contrasted on features their model shares (two-sided bounds, day-of-week protection), held-out wording wider than the accepted claim, literature statements broader than the reviewed set. Narrative: argument sound; remaining repetition across Introduction, Related Work and Discussion, question-style openers, abstract over length. All accepted |
| Final fixes | Lead writer | All accepted round 2 findings and four orchestrator findings applied (minimum slack wording, Winkelmann et al. contrast, held-out wording, repetition, openers, abstract to 242 words); one further wording fix in Discussion 6.2. Final diff read by the orchestrator: no number changed; document checks clean |

**Integrator decisions the authors may reverse**

- The limitation on the held-out misses of HIST+ACT sits in Discussion 6.5, with a pointer from Results; the scope paragraph stays at the end of Section 4.
- Working title: "Station workload shares after re-slotting a pick-and-pass warehouse: a held-out comparison of reserved margins and historical scenarios" (a neutral title chosen over "Keeping" and "Preserving", which imply success).
- The comparison of the reserve with the incumbent's historical station-level variation keeps the settled wording "did not predict compliance here" with its qualifiers, and is not in the abstract because it was not a predeclared endpoint. A reviewer's proposal to write "neither set nor validated" was declined because the settled register correction replaced that wording (the half-width was chosen with that statistic).
- The Discussion's site practices are presented as suggestions not tested as operating procedures; the minimum-slack practice is described as information that does not indicate compliance.

## 4. Literature review deliverables

Topic as interpreted (the instruction's "[TOPIC]" placeholder was not filled): storage location assignment and workload balance in pick-and-pass and zone picking under uncertain or changing demand, with the robust-optimisation and out-of-sample-evaluation ideas that the extension uses. See section 5, question L1.

- **(1) Search and selection account:** `literature/LITERATURE_REVIEW.md` §1.
- **(2) Table of the most valuable eligible articles:** §2 (31 journal articles in four strands, each with citation, DOI, research question, method, principal findings, limitations, relevance and access level).
- **(3) Cited synthesis of agreements, disagreements and gaps:** §3, with every statement tagged as the article's finding, NotebookLM synthesis (checked) or the reviewer's interpretation; §3.4 records NotebookLM errors found and not used.
- **(4) Promising candidates excluded, with reasons:** §4.
- Access limits and search coverage: §5.

## 5. Questions for the authors

Manuscript-level questions, with locations and sources, are in `manuscript/AUTHOR_QUESTIONS.md`. The questions below need the authors' decision before submission.

**Literature**

- **L1. Topic.** The literature instruction left "[TOPIC]" unfilled. The review covers storage assignment and workload balance in pick-and-pass and zone picking under uncertain or changing demand, robust-optimisation foundations (tightening, budgeted and data-driven sets, sampled constraints) and out-of-sample evaluation. Is that the intended topic?
- **L2. Articles not read.** Pan and Wu (2009) and Pan et al. (2015), the pick-and-pass storage classics, were eligible but unreachable and are not cited; Tashman (2000) is cited at title level only; 13 included articles were read at abstract level. Should someone with library access read these before submission?
- **L3. Coverage.** No Scopus or Web of Science search was run. Is a database search wanted?
- **L4. Notebook.** The dedicated NotebookLM notebook ("Lit review (journal articles only): robust storage assignment, workload balance, out-of-sample evaluation", id `49cac84f-28b0-4175-b602-6cc535d580b5`) stays in the account. Keep or delete it? The agent removed 23 failed-import error entries it had itself added; no other notebook was touched.

**Content and evidence**

- **E1. Values that no accepted source records** are marked in red rather than filled: the definitions of "complete order" and of the order-retention rule; the solver, model representation and time limits of the exploratory campaigns; the definition of a large order in the freeze rule; returned training objectives, timings, solver version and hardware; synthetic and per-horizon exploratory outcomes in the supplement. Report them (after extraction by the evidence process) or delete the sentences?
- **E2. Site policy.** Does Company A state its workload policy as station shares (card Q-004 remains unresolved)? Do order dates exist operationally at the site?
- **E3. Deferred preparation work.** The earlier preparation workflow (next step seq 71, register revision brief and findings F-071, F-074 to F-077) was superseded, not completed. Should any of it be resumed as a check before submission?

**Authorship and submission**

- **S1.** Author list, affiliations, author contributions, funding, competing interests and data availability are placeholders.
- **S2.** The AI-use statement says that the text was drafted with generative AI assistance under the authors' direction; the tools and the authors' review of the text must be named in the wording the chosen venue requires (`AI_USE_RECORD.md` has the details).
- **S3.** Target venue, and whether the manuscript should be converted to that venue's class and reference style.

## 6. Preparation work superseded by the write-now directive

Recorded in `governance/SCOPE_CHANGE_WRITE_NOW.md`: those tasks were superseded by user instruction, not passed, completed or found invalid. The evidence they produced was reused as fixed input.
