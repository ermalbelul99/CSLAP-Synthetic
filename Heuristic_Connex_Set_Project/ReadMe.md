# Industrial dataset — Company A (BERNER)

This folder holds the raw industrial order lines behind the industrial case study of
`IJPR_CSLAP_v2.tex` (Section 6, `tab:industrial`, `tab:reassign`, `fig:workload`,
`fig:ksweep`).

```
data/BERNER_ORDER_LINES_09-12.csv    77 MB, semicolon-delimited
```

Schema: `PRODUCT;ORDER;QTY;STATION;BOX_ID` — 1,669,346 order lines, 22,239 raw products,
293,794 raw orders, 29 raw station identifiers.

## How the paper's figures are derived from it

`../data_loader_industrial.py` is the single reader; every industrial runner goes through
it and it hard-codes this path as its default. Its cleaning steps reconcile the raw counts
with the numbers printed in the article:

| Step | Effect |
|---|---|
| Drop stations `01.Z8`, `01.15`, `01.GED` | 29 → **26 active stations** |
| Remap `01.GE4` onto `01.E4` | 26 → 25 distinct |
| Products surviving the station filter | **21,874 SKUs** |
| Drop orders of 5 or fewer distinct products | 284,862 orders, **24 stations carrying movable SKUs** |
| Frequency pruning for the solver instance | 15,975 SKUs / 83,183 orders |

Station speeds are assigned by class (static 37,700 / palette 57,200 / dynamic 83,200,
each divided by the station's location count), which is what makes the solver's workload
units differ from raw line counts — see changelog entry B4ter on the `pl_solver` vs
`pl_full` distinction.

## Note on the temporal hold-out

`tab:temporal` (out-of-sample weeks) is **not** reproducible from this file: it has no date
column. Those six numbers come from a dated extract
(`BERNER_ORDER_LINES_DATE_ASSIGNED_21.csv`, `DELIVERY_DATE` spanning 2021-09-01 →
2021-11-30) held outside this repository. See `../RERUN_IJPR_RESULTS.md` §4.

## Confidentiality

Commercially confidential; not redistributable. The article's Data Availability Statement
offers it on reasonable request only.

---

*This folder previously also carried the standalone "connexity set" preprocessing program
(`connexset.py`, `Data_to_Matrix_v5.py`, `setup.*`, `ConnexSetRun_0/`). That prototype was
superseded by `../Baselines/heuristic_synthetic.py` and removed when this branch was
trimmed to the IJPR article; it remains on `main`.*
