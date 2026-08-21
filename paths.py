"""Canonical filesystem roots for the Bertsimas-Sim workload-feasibility code.

Ported from the ``bs-robustness-clean`` branch of ``belulerm/CSLAP_Problem`` and
remapped onto this repository's layout. The upstream study kept every input and
output under a purpose-built ``data/`` tree; here the two datasets that already
exist locally are pointed at where they actually live, and only the artefacts
this repository does not yet hold get new locations.

Scripts in ``Baselines/`` reach this module with the pattern already used by
``Baselines/report_industrial_deviation.py``::

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from paths import DERIVED, RESULTS

Mapping to upstream
-------------------
``EXP02A_INSTANCES`` and ``BERNER_CSV`` resolve to the copies already tracked in
this repository, so the ported adapters run against local data unchanged.
``ISCF_INSTANCES``, ``DERIVED`` and ``RESULTS`` name directories that do not
exist here yet -- the ISCF instance families, the fold/cover/layout artefacts and
the study's own outputs were not ported. They are CLI defaults only; nothing
imports them eagerly, so their absence is harmless until an ISCF run is set up.
"""

from __future__ import annotations

import os

ROOT: str = os.path.dirname(os.path.abspath(__file__))

BASELINES: str = os.path.join(ROOT, "Baselines")
PAPER: str = os.path.join(ROOT, "paper")

DATA: str = os.path.join(ROOT, "data")

# --- raw, as delivered -----------------------------------------------------
RAW: str = os.path.join(DATA, "raw")
ISCF_RAW: str = os.path.join(RAW, "ISCF_Data")            # not present locally

# The industrial order lines already live in this repository.
BERNER_RAW: str = os.path.join(ROOT, "Heuristic_Connex_Set_Project", "data")
BERNER_CSV: str = os.path.join(BERNER_RAW, "BERNER_ORDER_LINES_09-12.csv")

# --- CSLAP instances -------------------------------------------------------
INSTANCES: str = os.path.join(DATA, "instances")
ISCF_INSTANCES: str = os.path.join(INSTANCES, "iscf")     # not present locally

# The article benchmark instances already live at the repository root.
EXP02A_INSTANCES: str = os.path.join(ROOT, "exp02a_instances")

# --- derived artefacts and study outputs -----------------------------------
DERIVED: str = os.path.join(DATA, "derived")
COVER_LOGS: str = os.path.join(DERIVED, "logs")
RESULTS: str = os.path.join(ROOT, "results")

__all__ = [
    "ROOT", "BASELINES", "PAPER",
    "DATA", "RAW", "ISCF_RAW", "BERNER_RAW", "BERNER_CSV",
    "INSTANCES", "ISCF_INSTANCES", "EXP02A_INSTANCES",
    "DERIVED", "COVER_LOGS", "RESULTS",
]
