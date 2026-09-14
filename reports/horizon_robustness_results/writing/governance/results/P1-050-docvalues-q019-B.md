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
      "quoted_text": "**δ = 0.01** — the user's preferred rule, run as the *aspiration*"
    }
  },
  "pred.twosided.delta_fallback": {
    "value_exact": "0.03",
    "unit": "share",
    "source": {
      "path": "reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md",
      "line": 366,
      "sha256": "9e122abb0eb27623e3ac4248e06bf9cde28cdc3b9987217f527603ce78824d71",
      "quoted_text": "**δ = 0.03** — the user's stated fallback."
    }
  },
  "pred.exploratory.origin": {
    "value_exact": "199403",
    "unit": "count",
    "source": {
      "path": "reports/horizon_robustness_results/CAMPAIGN_PREDECLARATION.md",
      "line": 430,
      "sha256": "9e122abb0eb27623e3ac4248e06bf9cde28cdc3b9987217f527603ce78824d71",
      "quoted_text": "first origin 199,403 plus 2P"
    }
  }
}
```

NOTES
- `pred.upperonly.delta`: line 62 (§2 Parameters) is where the primary δ is defined. Line 159 restates it for stage B. Lines 198, 279, 299 and 303 only use it. Handoff line 91 also restates it.
- `pred.twosided.delta_aspiration`: line 364 labels it. Line 375 is its table row. Line 383 says "±1 aspiration" without the decimal. Handoff lines 126 and 1084 repeat it.
- `pred.twosided.delta_fallback`: line 366 labels it. Line 376 is its table row. Handoff lines 126 and 1084 repeat it.
- `pred.exploratory.origin`: line 430 is the only line in any allowed source that gives the number. Line 50 gives only the rule floor(0.70·M). Handoff line 551 gives "first origin + 2P" without a number. Neither IJSSOL file, DATA_PROVENANCE, analysis_audit nor the reviewed plan contains 199,403. Check: 199,403 + 2 × 21,874 = 243,151, which matches lines 429 and 436.
- The sha256 covers the raw bytes; the file has LF line endings. A Python check confirmed every quote is verbatim. No ambiguity, so no Q-card.
