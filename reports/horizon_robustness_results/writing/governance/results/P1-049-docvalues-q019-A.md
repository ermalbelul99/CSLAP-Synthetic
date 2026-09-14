All confirmed exact. Now producing the final answer.

```json
{
  "pred.upperonly.delta": {
    "value_exact": "0.01",
    "unit": "share",
    "source": {
      "path": "reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md",
      "line": 62,
      "sha256": "9e122abb0eb27623e3ac4248e06bf9cde28cdc3b9987217f527603ce78824d71",
      "quoted_text": "δ = 0.01 and ν = 0.01 remain the primary settings for every"
    }
  },
  "pred.twosided.delta_aspiration": {
    "value_exact": "0.01",
    "unit": "share",
    "source": {
      "path": "reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md",
      "line": 364,
      "sha256": "9e122abb0eb27623e3ac4248e06bf9cde28cdc3b9987217f527603ce78824d71",
      "quoted_text": "δ = 0.01** — the user's preferred rule, run as the *aspiration*"
    }
  },
  "pred.twosided.delta_fallback": {
    "value_exact": "0.03",
    "unit": "share",
    "source": {
      "path": "reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md",
      "line": 366,
      "sha256": "9e122abb0eb27623e3ac4248e06bf9cde28cdc3b9987217f527603ce78824d71",
      "quoted_text": "δ = 0.03** — the user's stated fallback."
    }
  },
  "pred.exploratory.origin": {
    "value_exact": "199403",
    "unit": "count",
    "source": {
      "path": "reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md",
      "line": 430,
      "sha256": "9e122abb0eb27623e3ac4248e06bf9cde28cdc3b9987217f527603ce78824d71",
      "quoted_text": "ever scored in this study (first origin 199,403 plus 2P)."
    }
  }
}
```

NOTES (word count kept under budget):

`pred.upperonly.delta`: §2 line 62 "δ = 0.01 and ν = 0.01 remain the primary settings for every headline table" — chosen, it is §2's explicit primary-setting statement, before §8's two-sided amendment. Also stated incidentally at line 279 (min-slack straddle test) and confirmed externally at `EXPERIMENT_REVIEW_HANDOFF.md:91`; line 62 is the defining declaration.

`pred.twosided.delta_aspiration`/`delta_fallback`: §8.2 lines 363-366 list all three δ values with roles; lines 364 and 366 name aspiration and fallback directly. `EXPERIMENT_REVIEW_HANDOFF.md:126` restates both ("0.01 kept as the aspiration; 0.03 as the fallback") but §8.2 is the predeclaration itself, so cited.

`pred.exploratory.origin`: §9.2 line 429 gives the revision-3 holdout origin (243,151); line 430's parenthetical "(first origin 199,403 plus 2P)" is the only stated value for the earlier, first-eligible deployment origin used by the exploratory campaigns (stages B-F, revision 2), so cited over 429/448 (which give 243,151, a different origin).

Files read: `reports/horizon_robustness_results/writing/evidence/DOCUMENT_VALUES_SPEC.md`, `reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md` (sha256 above), plus grep-only checks (no content read) of `EXPERIMENT_REVIEW_HANDOFF.md`, `WRITING_EXECUTION_PLAN_REVIEWED_20260914.md`, `DATA_PROVENANCE.md`, `analysis_audit.md` for corroborating/competing mentions. Nothing written; no git command run.
