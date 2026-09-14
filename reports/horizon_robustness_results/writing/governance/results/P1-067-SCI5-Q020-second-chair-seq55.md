```
PREMISE: FALSE
```

The cited numbers are quoted correctly, but they show up just as much in arms that passed. Values from `W/evidence/anchors.json`:

| Arm | `ho.pass.*.count` | `ho.min_slack.*` s11/s22/s33 | `ho.departures.*.below` s11/s22/s33 |
|---|---|---|---|
| NOM | 0 (l.38) | 0.019998, 0.019999, 0.019999 (l.9, 21, 33) | 13, 13, 13 (l.13, 25, 37) |
| TIGHT | 3 (l.78) | 0.009992, 0.009996, 0.009999 (l.49, 61, 73) | 12, 13, 13 (l.53, 65, 77) |
| HIST_ACT | 0 (l.118) | 0.019997, 0.019997, 0.019999 (l.89, 101, 113) | 3, 4, 4 (l.93, 105, 117) |
| HIST_ACT_T | 3 (l.158) | 0.009993, 0.009998, 0.009998 (l.129, 141, 153) | 2, 4, 4 (l.133, 145, 157) |

"below" counts stations where the realised share fell below the lowest training scenario (l.133 selector). δ = 0.02 and λ = 0.5 come from `document_values.json:393`, so the tightened allowance is 0.02 × 0.5 = 0.01.

Reason: Every arm used its whole allowance, and HIST_ACT_T passed on all three seeds while falling below the modelled set at 2, 4 and 4 stations, the same count as HIST_ACT on s22 and s33. So the two facts do not separate passes from misses; the only difference left is the allowance size, which C-03's first qualifier says "does not isolate the margin from solver and layout effects" (`claims.json:101`), and C-04 is only an additional descriptive observation (`claims.json:133`). That leaves the mechanism uncertain, so the "empirical limitation" category (reviewer-first line 574) is still open.
