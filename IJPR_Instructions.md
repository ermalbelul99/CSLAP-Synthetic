# IJPR Submission & Writing Specifications

## 1. General & Technical Standards
- **Journal:** International Journal of Production Research (IJPR)
- **Language:** English (US or UK spelling, strictly consistent throughout).
- **Units:** SI units only (non-italicized).
- **LaTeX Requirements:** Must use Taylor & Francis `Interact` layout (APA reference style). 
  - Required package in preamble: `\usepackage{float}`.
  - A separate `.bib` file is mandatory. All references in `.bib` must have matching in-text citations.
- **Equations:** Must be fully editable LaTeX math environments.

## 2. Formatting & Hard Positioning (Figures & Tables)
- **Positioning Rule:** Figures and tables MUST NOT be allowed to float freely across pages.
- **Implementation:** Always use the hard positioning specifier `[H]` for all figure and table environments (e.g., `\begin{figure}[H]` and `\begin{table}[H]`).
- **Placement:** Embed each float directly inside the main text body at the exact location where it is referenced to preserve strict logical and narrative flow.
- **Display Items Limit:** Maximum **15 combined** figures and tables (e.g., 10 tables + 5 figures, or 12 figures + 3 tables). Exceeding 15 total display items triggers immediate unsubmission.

## 3. Structural & Word Limits (Research Articles)
- **Total Word Count:** ≤ 12,000 words. 
  - *Note: This limit is inclusive of Abstract, Main Text, Tables, References, and Figure/Table Captions.*
- **Abstract:** Unstructured paragraph, strictly ≤ 200 words.
- **Keywords:** 5 to 6 keywords.

## 4. Mandatory Content Elements (IJPR Specific Criteria)
The paper **must** explicitly contain the following six sections/themes:
1. **Literature Context:** Exhaustive analysis of prior publications specifically from *Production Research* and related domain journals.
2. **Methodological Novelty:** A novel decision aid model for the design or management of production systems and logistics, explained clearly for a general production research readership.
3. **Benchmarking:** Rigorous comparison with state-of-the-art approaches.
4. **Practical Application:** Detailed discussion on real-life applications of the proposed method in production systems/logistics.
5. **Managerial Insights:** Explicit, actionable insights tailored for industrial decision-makers.
6. **Research Perspectives:** Clear directions for future research.

## 5. Required Structural Sequence
1. **Title Page:** Title, Author names, Affiliations, ORCIDs, Corresponding Author email.
2. **Abstract & Keywords**
3. **Main Text:** Introduction, Materials & Methods, Results, Discussion (with embedded `[H]` floats).
4. **Managerial Insights & Research Perspectives**
5. **Author Contributions Statement**
6. **Acknowledgments**
7. **Funding Details**
8. **Disclosure Statement** (Conflicts of interest)
9. **Declaration of Generative AI Use**
10. **Data Availability Statement (DAS)**
11. **References**
12. **Appendices** (if applicable)
13. **Tables & Figures:** Inline with text via `[H]`.

## 6. Required Standard Boilerplate Statements

### Author Contributions Statement
> *Example:* "Author A and Author B were involved in the conception and design of the study. Author A performed the data analysis and algorithmic implementation. Author A and Author B drafted and critically revised the manuscript for intellectual content. All authors approved the final version and agree to be accountable for all aspects of the work."

### Disclosure Statement
> *Example:* "The authors report there are no competing interests to declare."

### Funding Details
> *Example:* "This work was supported by [Funding Agency] under Grant [number XXXX]." *(If none: "No financial support was received for this research.")*

### Generative AI Use
> *Example (if unused):* "The authors report generative AI was not used in their research or preparation of this manuscript."

### Data Availability Statement (DAS)
> *Example:* "The data supporting the findings of this study are available upon reasonable request from the corresponding author."