# IJSS:O&L — Submission Specification and Rewrite Plan

**Target journal:** *International Journal of Systems Science: Operations & Logistics* (Taylor & Francis)
**Source manuscript:** `IJPR_CSLAP_v4.tex` + `IJPR_CSLAP_v4_supplementary.tex` + `IJPR_CSLAP_v4.bib` (ground truth for all results)
**Guideline version transcribed:** updated 22 June 2026
**This file created:** 2026-09-09
**Status:** Part A–F are the journal's rules. Part G–K are our decisions and plan.

> **Draft in progress (2026-09-09).** `IJSSOL_CSLAP_v1.tex`, `IJSSOL_CSLAP_v1_supplementary.tex`,
> `IJSSOL_CSLAP_v1.bib` and `IJSSOL_Cover_Letter.md` now exist, branched from the v4 files (which are
> untouched and remain ground truth). The rewrite is applied: contribution reframed, ~900 words cut,
> compliance edits in. Estimated ≈11,845 words including full biographies — **the Overleaf
> `pdftotext | wc -w` count governs.** Open items are listed in Part K and marked `[[ ]]` / `ACTION:`
> in the files themselves.

> Previous route: rejected at *International Journal of Production Research*; transfer advised within the
> same category. Longer earlier drafts (`IJPR_CSLAP_v2.tex`, `v3.tex`, `v3_supplementary.tex`) may be mined
> for restored text, **but where any number, claim or wording conflicts, v4 wins.**

---

## PART A — Hard gates (a failure here means the paper is returned without review)

### A1. Cover letter — three mandatory elements
> "Manuscripts without cover letters containing each of the three elements below will be unsubmitted."

1. **Institutional email address AND a link to an institutional profile page for each author.**
2. **An explanation of how the manuscript submission relates to the aims and scope of the journal.**
3. **A statement of contribution — a summary of no more than 100 words.**

This is stricter than IJPR. Our existing `IJPR_Cover_Letter.md` / `.docx` does **not** satisfy it and must be
rewritten, not adapted. See §J4 for the drafting brief.

### A2. Institutional email addresses for all authors
- Required **both in the manuscript and in the ScholarOne system profile**.
- Personal domains (gmail, hotmail, …) are permitted **only as secondary contacts**, and must be linked to the
  researcher's institutional profile.
- "Correspondence from generic or unverified email accounts will not receive a response and will be removed."

**Action items for our author list (open, must be resolved before submission):**

| Author | Affiliation | Institutional email | Institutional profile link |
|---|---|---|---|
| Ermal Belul | UTC / Heudiasyc + Savoye | `ermal.belul@hds.utc.fr` ✔ (already in v4) | needed (Heudiasyc staff page) |
| Marwane Bouznif | Savoye | needed — corporate `@savoye.com` | needed — corporate/company profile page |
| Dritan Nace | UTC / Heudiasyc | needed | needed |
| Antoine Jouglet | UTC / Heudiasyc | needed | needed |

*Note:* the guideline assumes academic affiliations. For the industrial co-author, supply the corporate address
plus the closest thing to an institutional profile page (company staff/R&D page, or an ORCID record).
Do **not** submit with `ermalbeluli10@gmail.com` as a primary contact anywhere.

### A3. Word limit
> "For initial submissions, the main text of a typical paper for this journal should not exceed **12,000 words**
> (18,000 words for a review), **including all manuscript elements**. The editors may return or desk-reject
> papers deemed excessively long."

**This is the same ceiling as IJPR — there is no extra room.** Read "including all manuscript elements"
conservatively, i.e. the same inclusive count we used for IJPR: abstract + main text + tables + captions +
references. The explicit desk-reject-for-length warning is *new* relative to the IJPR guideline and should be
treated as a signal, not boilerplate. See Part I.

### A4. Authorship is frozen at submission
> "This journal does not accept changes to the authorship list post-submission."

Confirm the four-author list and the CRediT split **before** uploading.

### A5. Everything must be in English
US or UK spelling, consistent throughout. v4 is UK English (`minimise`, `optimise`, `behaviour`) — keep it and
do not let restored v2/v3 text reintroduce US spellings.

---

## PART B — Article types, and which one we submit

The journal accepts: **Original Articles**, **Data Notes**, **Method**, **Review Article**.

**We submit as an Original Article.** Requirements:
- Elements in this order: title page; abstract; keywords; main text (introduction, materials and methods,
  results, discussion); acknowledgments; declaration of interest statement; references; appendices (as
  appropriate); table(s) with caption(s) (on individual pages); figures; figure captions (as a list).
- **Unstructured abstract of 200 words.**
- **No more than 6 keywords.**

Types we are *not* using, recorded so the option is closed:
- **Method** — 2,500–4,000 words, structured abstract (Introduction/Methods/Results/Discussion), 3–6 keywords,
  mandatory author-contributions statement. Far too short for this study; rejecting this option is not a
  close call.
- **Data Note** — describes a deposited dataset only, no interpretation or conclusions. Not applicable; our
  industrial data is confidential.
- **Review Article** — requires a **pre-approved proposal to the Editor-in-Chief**; unsolicited reviews are
  returned without review. Not applicable.

> **Transcription note.** The guideline page as supplied contains two unlabelled blocks between the article-type
> entries (one specifying 2,500–4,000 words / 3–6 keywords, one specifying an unstructured 200-word abstract).
> These read as rendering artefacts of the journal's article-type accordion. They do **not** override the
> Original Article specification above. If in doubt at submission time, re-check the live page.

---

## PART C — Manuscript elements and required statements

### C1. Order of elements (Original Article)
```
Title page  →  Abstract  →  Keywords  →  Main text (intro, materials & methods, results, discussion)
→  Acknowledgments  →  Declaration of interest  →  References  →  Appendices
→  Tables (with captions, on individual pages)  →  Figures  →  Figure captions (as a list)
```
Two observations:
- The prescribed main-text sequence is **IMRaD**. Our v4 sequence (Introduction / Related production research /
  Problem definition / Solution methods / Computational experiments / Industrial application / Managerial
  insights / Conclusions) is a standard OR-paper mapping onto IMRaD and is acceptable under format-free
  submission (Part D). Do not force literal IMRaD headings.
- The element order puts tables and figures **at the end**. Format-free submission (Part D) explicitly permits
  them inline, so `[H]` placement is retained for the initial submission. Editable versions are required at
  revision stage.

### C2. Statements required at the end, before the references

| Statement | Required? | Status in v4 | Action |
|---|---|---|---|
| **Author Contributions Statement** | Yes | present | keep; align wording with CRediT roles |
| **CRediT roles** | Supported, entered at submission | not in file | assign the four authors' roles in ScholarOne |
| **Acknowledgements** | as appropriate | present | keep |
| **Funding details** | Yes — declare all, or declare none | present (ANRT / CIFRE with Savoye) | add the grant number if one exists |
| **Disclosure statement** | Yes — **use the subheading "Disclosure of interest"** | present, headed "Disclosure statement" | **rename the heading** |
| **Declaration of generative AI use** | Yes | present | keep; verify it still describes actual use |
| **Data availability statement** | Yes, with hyperlink/DOI/persistent identifier | present | see §C4 |
| **Biographical note, ≤200 words per author** | Yes | **absent** | **write four bios** — new requirement, not in the IJPR spec |

Suggested wording where the journal gives it:
- Disclosure: *"The authors report there are no competing interests to declare."*
- Funding, if none: declare that explicitly. (Not our case — we have ANRT/CIFRE support.)
- Generative AI, if unused: *"The authors report generative AI was not used in their research or preparation of
  this manuscript."* (Not our case — v4 already declares assisted language refinement. Keep that declaration.)

### C3. Ethics statement for a non-public dataset — **easy to miss, applies to us**
> "All original research papers involving humans, animals, plants, biological material, **protected or non-public
> datasets**, collections or sites, must include a written statement in the Methods section, confirming ethical
> approval has been obtained … In settings where ethics approval for non-interventional studies is not required,
> authors must include a statement to explain this."

The Company A order data is a non-public dataset. **Add one or two sentences to the industrial-application
section** stating that the records are anonymised commercial operational data (order lines and station
assignments), contain no personal data, were used with the partner company's permission, and that no ethics
approval was required because the study involves no human or animal subjects. Have the Savoye/Company A contact
confirm the wording before submission.

Clinical trials registry, informed consent, and health & safety sections of the guideline do not apply.

### C4. Data availability statement
Journal policy is **"share upon reasonable request"**. The DAS must detail where the data is and how to access
it, and give a hyperlink, DOI or other persistent identifier where data is open. At submission you will be asked
whether a dataset is associated with the paper; if yes, a DOI or reviewer URL may be requested.

v4's DAS is already close to compliant. Required edits:
- The synthetic instance archive currently points at an **anonymous** `anonymous.4open.science` link. This
  journal uses **single-anonymous** review (authors are not anonymous to reviewers), so the anonymised link is
  no longer needed for blinding — but it is still a working URL. Preferably deposit the two instance families in
  a **persistent repository (Zenodo / Figshare) and cite a DOI**, which is what the guideline actually asks for.
- Keep the confidentiality clause for the Company A dataset.
- Keep the note that Hexaly and CPLEX licences cannot be redistributed.
- Update the cross-references to the supplementary section numbers after the rewrite.

### C5. Optional extras worth considering
- **Image descriptions (alt text)** — T&F generates them with AI; authors may supply their own. Worth supplying
  for the four figures, since AI-generated alt text on a station-workload bar chart will be poor.
- **Supplemental online material** — published via Figshare. This is where `IJPR_CSLAP_v4_supplementary.tex`
  goes, renamed and renumbered.
- **Article extenders** — graphical abstract, video abstract, infographic. Optional, paid service available.
  Not planned.

---

## PART D — Format-free submission (a genuine relaxation vs IJPR)

> "Authors may submit their paper in any scholarly format or layout … There are no strict formatting
> requirements, but all manuscripts must contain the essential elements needed to evaluate a manuscript:
> abstract, author affiliation, figures, tables, funder information, and references."

Consequences for us:

| Item | IJPR rule we were under | IJSS:O&L rule | Decision |
|---|---|---|---|
| Document class | T&F `interact.cls`, APA style, mandatory | any scholarly format | **Keep `interact.cls`** — it is a T&F journal, the file already compiles on Overleaf, and switching classes buys nothing |
| Reference style | APA via `apacite`, mandatory | any consistent scholarly style; **`.bib` file mandatory** for LaTeX; journal style applied post-acceptance | **Keep apacite/APA.** Keep `IJPR_CSLAP_v4.bib` (rename to match the new file) |
| Reference completeness | — | author(s), journal/book title, article/chapter title, year, volume/issue, pages **essential**; DOIs recommended | audit the 41 cited entries for missing volume/issue/pages (`zhen2025` is "advance online publication"; `kim2020` has no pages; `tarczynski2023` carries a DOI in a `note` field — move it to a `doi` field) |
| In-text citation coverage | — | "All bibliographic entries must contain a corresponding in-text citation" | v4 already cites 41 of the 41 entries used; re-verify after cuts, and delete any entry whose citation is removed |
| **Display-item cap** | **max 15 figures + tables combined** | **no cap stated** | constraint lifted, but see Part I — fewer floats is still the right move |
| Float placement | `[H]`, inline, mandatory | inline or separate | keep `[H]` inline |
| Spelling | consistent | US or UK, consistent | keep UK |

**At the revision stage an editable version of the article must be supplied regardless of the initial format.**
The LaTeX source satisfies this.

### D1. ScholarOne upload mechanics for a LaTeX submission
- Convert to **PDF first**. Upload the PDF as the **"Manuscript - with author details" / "Manuscript - anonymous"** file.
- Upload the **LaTeX source as a single ZIP**, marked **"LaTeX Source Files"**.
- Peer review is **single anonymous** (reviewers anonymous, authors named) by **two independent reviewers**.
  An anonymised manuscript is therefore not strictly required, but prepare one if ScholarOne demands the slot.
- Submissions are screened by **Crossref Similarity Check**. Our text overlaps heavily with the earlier IJPR and
  C&OR submissions — both unpublished and rejected, so this is not misconduct — but if any version was posted
  publicly (HAL, arXiv, institutional repository, ResearchGate), **declare it in the cover letter**, because the
  preprint policy also warns that anonymity cannot be guaranteed for shared preprints.

---

## PART E — Figures, tables, equations, units

- **Figures:** 1200 dpi line art, 600 dpi greyscale, 300 dpi colour, at final size. Preferred formats PS, JPEG,
  TIFF, or Word (DOC/DOCX) for Word-drawn figures.
  → **Measured 2026-09-09.** What matters is pixels ÷ printed inches, not the PNG's `pHYs` metadata. At the
  placement widths used in the manuscript, six of the seven images clear 300 dpi comfortably (345–724 dpi,
  because they sit at `0.46\linewidth`). **Only `gap_vs_size_crossover.png` falls short, at 265 dpi**
  (1,440 px across `0.86\linewidth` ≈ 5.4 in) — regenerate that one at `dpi=300` or wider.
  → Their embedded metadata reads 100–200 dpi, which some production pipelines check even when the pixels
  suffice, so re-saving all seven with `savefig(..., dpi=300)` is the safer, cheap option.
- **Colour:** free online. **In print: £300 per figure for figures 1–4, then £50 per figure from figure 5.**
  With four colour figures the print charge would be £1,200. → **Decline print colour** and make sure every
  figure is legible in greyscale (the station-workload bar charts and the crossover plot must not rely on hue
  alone; use markers/hatching/line style).
- **Tables:** must present new information rather than duplicating the text; readable without the text; editable
  files. Our `booktabs` tables qualify. The coloured row shading in `tab:reliability` and `tab:industrial`
  encodes meaning by colour alone — **add a redundant non-colour cue** (bold, a symbol, or a "Best" column) so
  the tables survive greyscale printing.
- **Equations:** must be editable — LaTeX math environments satisfy this.
- **Units:** SI, non-italicised.
- **Third-party material:** obtain written permission for anything under someone else's copyright. Our figures
  are all our own; confirm the Company A data plots carry no company branding or identifying layout detail.

Assets currently referenced by v4, all present on disk:
```
Images_CSLAP/gap_vs_size_crossover.png
Images_CSLAP/r4_number_of_lines_per_station.png
Images_CSLAP/r5_pct_change_lines_per_station.png
Images_CSLAP/Hexaly_number_of_lines_per_station.png
Images_CSLAP/Hexaly_pt_relative_change_number_of_lines_per_station_new.png
Images_CSLAP/CG_SetPart_number_of_lines_per_station.png
Images_CSLAP/CG_SetPart_pt_relative_change_number_of_lines_per_station_new.png
```
(The two `*_new.png` files are untracked in git — commit them before building the submission bundle.)

---

## PART F — Costs, licensing, post-submission

- **No submission fee, no publication fee, no page charges.** Only the print-colour charge in Part E.
- **Open Access is optional** via T&F Open Select; APC applies, only the corresponding author can request
  institutional funding, and the corresponding author cannot be changed later to gain eligibility. Decide before
  submission whether UTC or ANRT requires OA.
- **Open Research Project:** the journal is running an editorial-policy study; we may receive an extra email
  about open research practices during evaluation. Opting out (`datasharing@tandf.co.uk`, quoting the Manuscript
  ID) has no effect on the editorial decision.
- Keep a copy of the Accepted Manuscript on acceptance.

---

## PART G — What changes relative to the IJPR version

Carry over unchanged (both journals require it):
abstract ≤200 words unstructured · English only · SI units · `.bib` mandatory · author contributions statement ·
funding details · disclosure · generative-AI declaration · data availability statement · 12,000-word ceiling.

Changes to make:

| # | Change | Type |
|---|---|---|
| 1 | Rewrite the cover letter around the three mandatory elements (§A1) | **blocking** |
| 2 | Collect institutional emails + institutional profile links for all four authors (§A2) | **blocking** |
| 3 | Retitle "Disclosure statement" → **"Disclosure of interest"** | trivial |
| 4 | Write four biographical notes, ≤200 words each | new |
| 5 | Add the non-public-dataset ethics statement to the methods/industrial section (§C3) | new, easy to miss |
| 6 | Assign CRediT roles for all four authors at submission | new |
| 7 | Replace journal name in all file headers, comments and the supplementary title | cosmetic but do it |
| 8 | Reposition the framing for a *systems science / operations & logistics* readership, not a *production research* one (§J1) | substantive |
| 9 | Deposit the synthetic instances under a persistent DOI and update the DAS (§C4) | recommended |
| 10 | 15-float cap no longer applies; greyscale-safe figures and tables now matter more (Part E) | net relaxation + new constraint |
| 11 | Re-audit `.bib` entries for volume/issue/pages completeness (Part D) | housekeeping |
| 12 | Rename files: `IJSSOL_CSLAP_v1.tex`, `IJSSOL_CSLAP_v1_supplementary.tex`, `IJSSOL_CSLAP_v1.bib` | housekeeping |

---

## PART H — Measured state of `IJPR_CSLAP_v4.tex`

All figures below were measured from the source on 2026-09-09 with the calibrated word ruler
(see the `ijpr-wordcount-estimation` note: strip comments and tikz, `\ref`→1 token, `\cite`→3 tokens/key,
then add ≈1,078 words of bibliography for 41 apacite entries and ≈69 words of tikz node text).

| Quantity | Value | Limit | Verdict |
|---|---|---|---|
| Estimated total | **≈ 12,000 words** (at the cap; v4's own header states it was cut to fit 12,000) | 12,000 | **no headroom** |
| Abstract | **199 words** | 200 | at the cap |
| Keywords | 6 | ≤6 | at the cap |
| Tables | 6 | — | fine |
| Figures | 4 | — | fine |
| Algorithms | 1 (in main text) | — | movable |
| Unique cited references | 41 | — | ≈1,078 words of the budget |

**Where the words actually go** (ruler units; the body totals 11,517 in these units — use the *shares*, not the
absolute numbers, since the ruler runs ~7% high against a compiled count):

| Section | Ruler words | Share of body |
|---|---|---|
| Introduction | 444 | 4% |
| Related production research | 1,000 | 9% |
| Problem definition + MILP + set-variable reformulation | 980 | 9% |
| **Clustering heuristic** | **1,055** | **9%** |
| **Column generation** (master, pricing, drive, bound) | **2,090** | **18%** |
| Initialisation + baselines | 393 | 3% |
| Instance generation + protocol | 557 | 5% |
| Synthetic results | 1,426 | 12% |
| Industrial application | 1,487 | 13% |
| Out-of-sample weeks | 409 | 4% |
| Bounded reassignment | 407 | 4% |
| Managerial insights | 383 | 3% |
| Conclusions | 481 | 4% |
| Front + back matter | 587 | 5% |

**The single most useful number here: the two secondary methods consume 3,145 ruler-words — 27% of the body —
against 980 for the model itself and 2,303 for the entire industrial validation.** More than a quarter of the
paper is spent on two methods that are neither the headline result nor the method we deploy. That is the
mechanical explanation for "a reviewer who has to follow all of it may lose the central value."

Comparison with the longer drafts (same ruler, so directly comparable): `v3` ≈ 15,200 real words,
`v2` ≈ 16,300 real words — roughly **3,200 and 4,300 words above the new journal's ceiling**.

---

## PART I — The form question, settled

**Question posed:** keep the article essentially as it is and adapt it to the new journal's requirements, or
deliberately shorten it — making the set-variable MILP the core contribution and reducing the column generation
and the greedy heuristic to a compact comparison section?

### I1. The facts that decide it

1. **There is no extra room.** IJSS:O&L's ceiling is 12,000 words — identical to IJPR's — and it adds an
   explicit warning that over-long papers may be returned or desk-rejected. v4 is already at the ceiling.
   The option "restore material from v2/v3" is closed on arithmetic alone: v3 is ~3,200 words over, v2 ~4,300.
2. **The density is measurable, not a feeling.** 27% of the body is spent on the two methods that lose on the
   industrial instance (Part H).
3. **Adding material in response to each rejection has already happened three times.** v2 → v3 → v4 records a
   study that grew under review and then had to be cut back to fit, with the cuts falling on the supplement
   rather than on the argument. Repeating that pattern makes the same problem worse.

So: **shorten deliberately.** Adapting v4 as-is would resubmit a paper already diagnosed as too dense into a
journal with the same limit and a stated impatience for length.

### I2. But do not make the set-variable MILP the *sole* core — this is the part to get right

The obvious version of the shortening plan has a real weakness, and it should be named before we commit to it.

If the set-variable MILP becomes *the contribution*, then the paper's novelty reduces to **"choose the right
decision encoding for your commercial solver."** A skeptical referee will make three moves against that:

- The set-variable formulation is a **Hexaly-specific feature**, not a new model. Equations (10)–(13) of v4 are
  an equivalent restatement of (1)–(6); v4 says so itself ("Only the representation changes").
- The 7.8% advantage over the binary form rests on **one instance, one engine, one budget**. On the 29 synthetic
  instances the two forms land within 0.6% of each other at every size — the paper reports this honestly, which
  is a strength of the writing but leaves the headline resting on a single data point.
- A vendor-tied result is uncomfortable in a systems/OR journal. v4 already concedes that what is missing is
  "the cost to a practitioner without a commercial licence."

Making that the centre of the paper puts the weakest-supported claim in the most exposed position.

### I3. The recommendation

**Shorten as proposed, but relocate the centre of gravity to the model plus the industrial validation, with the
set-variable MILP as the method that delivers them.** Concretely, the paper claims three things, in this order:

1. **A problem reformulation.** CSLAP for automated pick-and-pass systems with **station visits** as the
   objective under **hard per-station capacity and workload budgets** — replacing the travel-distance objective
   that the CSLAP literature inherits from manual warehouses. This is a modelling contribution, it is
   solver-independent, and it is exactly what a systems/logistics journal rewards.
2. **A deployable solution at real industrial scale.** 21,874 SKUs, 26 stations, 13.7% of station visits removed
   in sample, **6.6–7.4% on weeks the layout was not fitted to**, every station inside its own workload budget,
   and a **bounded-reassignment path** (relocation cap `k`) so the gain can be taken gradually on a live site.
   This is the part no competing study has, and it is the part an O&L readership will judge the paper on.
3. **A comparison establishing that the chosen method is the right one.** Three solution approaches plus two
   literature metaheuristics, one protocol, one set of budgets, 29 instances, paired tests. Here the
   set-variable-vs-binary result lives — as **evidence supporting the choice**, where a single strong data point
   is perfectly adequate, rather than as the headline, where it is not.

This framing keeps everything true, demotes the column generation and the heuristic without discarding them, and
removes the vendor-encoding attack surface by refusing to stand the paper on it.

### I4. What we knowingly give up

State these to ourselves now so they are not discovered mid-review:

- **The lower bound leaves the main text.** The Farley-type bound is the only formal guarantee anywhere in the
  paper. It is already reported as vacuous above 50 SKUs, so the loss is presentational rather than substantive
  — but a referee who wants a bound will now find it only in the supplement. Keep one sentence in the main text
  saying the method carries a valid bound, that it is informative only at 50 SKUs, and where the derivation is.
- **The best workload-dispersion result belongs to the column generation** (utilisation SD 2.41% against the
  set-variable MILP's 4.48%). Do not lose this in the compression — it is the argument for CG in the managerial
  section, and it is the reason CG stays in the paper at all.
- **The 2,000-SKU crossover belongs to the heuristic and the CG** (−1.3% and −1.6% against the reference, in two
  minutes against twenty for the heuristic). It rests on three instances and v4 already reports it as observed
  rather than general. Compressing it is fine; deleting it would remove the only place the deployed method is
  beaten, and a comparison that never loses reads as advocacy.
- **Methodological novelty for an OR referee.** The price-and-complete drive and the aggregated master are the
  most technically original things in the paper. Moving their machinery to the supplement is right for the word
  budget, but the main text must still state *what is new about them in two sentences*, or an OR referee will
  score the paper as an application study.

### I5. Rejected alternatives

- **Keep v4 essentially as is, adapt the front matter.** Cheapest, but re-runs the failure mode into a journal
  with the same ceiling and a desk-reject warning. Rejected.
- **Split into two papers** (methods paper + industrial application paper). Tempting, but the industrial result
  is what makes the methods interesting and the methods are what make the industrial result credible; split, both
  halves get weaker, and the second submission carries a self-overlap problem through Crossref. Rejected.
- **Submit as a Method article** (2,500–4,000 words). The word range cannot hold a 21,874-SKU industrial
  validation. Rejected.

---

## PART J — Rewrite plan

### J1. Repositioning for the new readership
IJPR wanted "Related **production** research" and mandated managerial insights. IJSS:O&L is a **systems science /
operations & logistics** journal. Changes:

- Retitle §2 from "Related production research" to something neutral ("Related work" / "Literature and
  positioning"). The section's IJPR-heavy citation set (`saylam2023minmax`, `jaghbeer2020automated`,
  `pang2017datamining`, `larco2017discomfort`, `vanheusden2022workload`, `vanheusden2023practical`,
  `dekoster2012zones`, `mirzaei2021`) was assembled to demonstrate IJPR fit. Keep the ones that carry an
  argument; the ones that exist only to show journal fit can go — each removed citation also removes ~26 words
  of bibliography.
- The **systems** framing is available and underused: a pick-and-pass warehouse *is* a constrained
  material-handling system where the storage decision, the station buffers and the workload budgets interact.
  Say so once, in the introduction, in the journal's own vocabulary.
- **Keep the managerial insights section** even though this journal does not mandate it — it is the right
  section for an O&L audience and it is already short (383 words).
- The cover letter's aims-and-scope paragraph (§A1.2) should make the same argument in three sentences.

### J2. Word budget for the rewrite

Target: **≈10,200–10,600 real words**, i.e. deliberately ~1,400–1,800 under the ceiling rather than at it.
Landing under the limit is itself part of the answer to the density problem.

| Section | Now (ruler) | Target (ruler) | Δ | How |
|---|---|---|---|---|
| Introduction | 444 | 500 | +56 | sharpen the three-contribution paragraph around the §I3 ordering |
| Related work | 1,000 | 800 | −200 | drop journal-fit-only citations; merge the two decomposition paragraphs |
| Problem definition + both formulations | 980 | 980 | 0 | **untouched — this is now the core** |
| **Clustering heuristic** | **1,055** | **450** | **−605** | keep the five stages as one compact paragraph + the β-on-ζ rule in one sentence; move the four-threshold list, the calibration argument and `tab:capsweep` to the supplement (S1 already carries the full sweep) |
| **Column generation** | **2,090** | **650** | **−1,440** | keep: why a bundle-sized unit of change suits a piecewise-constant objective; the aggregated master in 2–3 sentences; one sentence that it carries a valid bound. Move the pricing subproblem, Algorithm 1, the four operators and the bound discussion to the supplement |
| Initialisation + baselines | 393 | 350 | −43 | trim |
| Instance generation + protocol | 557 | 557 | 0 | keep — this is the credibility of the comparison |
| Synthetic results | 1,426 | 1,250 | −176 | keep the table and all five findings; compress the prose around them |
| Industrial application | 1,487 | 1,600 | +113 | **expand slightly** — add the ethics statement (§C3) and let the deployment argument breathe |
| Out-of-sample weeks | 409 | 409 | 0 | untouched — this is the second-strongest result in the paper |
| Bounded reassignment | 407 | 407 | 0 | untouched |
| Managerial insights | 383 | 400 | +17 | keep four insights; make the CG-for-balance point explicit (§I4) |
| Conclusions | 481 | 450 | −31 | trim the future-work list |
| Front + back matter | 587 | 640 | +53 | ethics statement, renamed disclosure heading |
| **Body total** | **11,517** | **9,443** | **−2,074** | |
| + bibliography (fewer citations) | 1,078 | ~950 | −128 | |
| + tikz node text | 69 | 69 | 0 | |
| **Estimated total** | **≈12,000** | **≈10,300** | **−1,700** | |

### J3. Display items after the rewrite
Main text drops from 11 items to **8**: 5 tables (positioning, synthetic benchmark, industrial, out-of-sample,
bounded reassignment) + 3 figures (schematic, crossover, station workload). Moved to the supplement:
`tab:capsweep`, `alg:cgdrive`, `fig:heuristic_flow`. No cap applies, but 8 well-chosen floats read as a
controlled paper and 11 read as a dense one.

### J4. Supplementary material after the rewrite
Current `IJPR_CSLAP_v4_supplementary.tex` has S1–S10. Absorb the demoted material and renumber:
- **New S-sections:** heuristic thresholds and calibration argument; the community-bound table; the heuristic
  flow figure; the pricing subproblem; the price-and-complete algorithm and its four operators; the bound
  discussion and why it is loose.
- **Existing S1–S10** keep their content; renumber and re-point every "Supplementary Section~SX" cross-reference
  in the main text. The supplement compiles standalone as an `article` class and needs only the `.bib` beside it.
- Update the supplement's title block (it currently names IJPR).
- The supplement is **not** counted against the 12,000 words, but it is peer-reviewed material — it must stay
  readable on its own, and it must not become the place where load-bearing claims hide.

### J5. Cover letter drafting brief (three elements, in order)
1. **Author identification block** — four rows: name, institutional email, institutional profile URL.
2. **Aims-and-scope paragraph** — three sentences: (a) the paper studies a constrained material-handling system
   in which storage assignment, station buffers and workload budgets interact; (b) it delivers a decision model
   and a validated solution on an operating facility of 21,874 SKUs; (c) it belongs to the journal's operations
   and logistics remit as a systems-level slotting decision with a deployment path.
3. **Statement of contribution, ≤100 words** — draft to fit exactly the three claims of §I3, in that order.
   Count the words; the limit is explicit.

Also state in the cover letter, briefly: that the manuscript was previously submitted elsewhere and is not under
consideration anywhere else, and whether any version is publicly posted (Part D1).

---

## PART K — Pre-submission checklist

**Blocking**
- [ ] Cover letter with all three mandatory elements (§A1)
- [ ] Institutional email + institutional profile link for all four authors, in the manuscript and in ScholarOne (§A2)
- [ ] Author list and CRediT roles frozen and agreed (§A4, §C2)
- [ ] Estimated total word count ≤ 12,000, ideally ≈10,300 (§J2) — governing number is `pdftotext … | wc -w` on the Overleaf build

**Manuscript content**
- [ ] Disclosure heading renamed to **"Disclosure of interest"**
- [ ] Ethics statement for the non-public Company A dataset added to the methods/industrial section (§C3)
- [ ] Four biographical notes, ≤200 words each
- [ ] Abstract ≤200 words, unstructured, single paragraph
- [ ] ≤6 keywords
- [ ] DAS updated; synthetic instances deposited under a persistent DOI if feasible
- [ ] Journal name replaced everywhere (main file, supplement, headers, comments)
- [ ] All "Supplementary Section~SX" cross-references re-pointed after renumbering
- [ ] Every `.bib` entry cited in text; every entry has author/title/journal/year/volume/pages

**Figures and tables**
- [ ] All figures regenerated at ≥300 dpi at final print size
- [ ] Every figure legible in greyscale (no hue-only encoding)
- [ ] Colour-shaded table rows carry a redundant non-colour cue
- [ ] Print colour declined (£300/figure) unless someone is paying
- [ ] `Images_CSLAP/*_new.png` committed to git
- [ ] Alt text drafted for the four figures (optional but recommended)

**Build and upload**
- [ ] Compile on Overleaf from the T&F Interact template — **never locally** (no `interact.cls` on this machine)
- [ ] PDF uploaded as "Manuscript - with author details"
- [ ] LaTeX source uploaded as a **single ZIP** marked "LaTeX Source Files" (tex + supplement + bib + `Images_CSLAP/`)
- [ ] Supplementary PDF uploaded as supplemental material
- [ ] Decided: Open Select yes/no, and who funds the APC if yes
- [ ] Decided: opt out of the Open Research Project, or not

---

## Ground-truth reminder

`IJPR_CSLAP_v4.tex` / `_supplementary.tex` / `.bib` are authoritative for **every number, table and claim**.
`v2` and `v3` are longer and may be quarried for restored prose, structure or explanation, but where any value
or claim differs, **v4 wins without discussion**. Time budgets in `tab:reliability` (120 / 300 / 600 / 1,200 s)
remain the protocol of record for any new run.
