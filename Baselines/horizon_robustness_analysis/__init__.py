"""Analysis-layer package, deliberately OUTSIDE the solve-path package.

`Baselines.horizon_robustness.runner.runtime_metadata` derives the campaign
implementation identity from every `*.py` in the solver package directory, and
a worker fails closed when that identity changes. Analysis code changes often
during reporting and can never affect a native solve, so it lives here: editing
a table or figure must not invalidate a frozen campaign manifest or block an
ordinary resume. See EXPERIMENT_REVIEW_HANDOFF.md, "Code changes".
"""

# Recorded in artifact_index.json and analysis_audit.md so derived material can
# be told apart by the analysis code that produced it. Bump on any change that
# alters a table or figure.
ANALYSIS_VERSION = "2026-09-13-r3"

__all__ = ["analysis", "rescoring", "ANALYSIS_VERSION"]
