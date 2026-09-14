"""Blind double-reproduction, builder B (targeted revision 2, dispatch seq 57,
findings F-078, F-079, F-080; revision of dispatch seq 38, card Q-005).

Reads only the allowed inputs listed in ANCHOR_SPEC.md sections A-D and prints
one JSON object {key: entry} to stdout. Standard library, pandas and numpy
only. Uses fractions.Fraction wherever the input is an exact field or a
count. Never imports or runs a repository module; never reads raw order
data.

Revision from seq 36: ANCHOR_SPEC section D no longer has the single key
`ho.incumbent.training_slack` (previously emitted as UNAVAILABLE because
scenario_shares[0] disagreed with a naive index-0 read across rows). It is
replaced by two explicit keys, `ho.incumbent.training_slack.history` and
`ho.incumbent.training_slack.hist_act`, selected by case arm rather than by
inspecting scenario_shares[0]. See the bottom of Section D.

Revision from seq 38 (this file): ANCHOR_SPEC gained 44 new required keys for
three BCL round-2 findings. Every other key below is untouched from the seq
38 file, in both code and value.
- F-078 (Section A): `ho.breach.<ARM>.<SEED>.cap_worst` and `.floor_worst`
  for NOM, TIGHT, HIST_ACT, HIST_ACT_T. Computed from the case records'
  per-station `share_exact` (future share), `cap_exact` and `floor_exact`
  (band limits): cap_worst = max_i max(0, share_exact_i - cap_exact_i) * 100,
  floor_worst = max_i max(0, floor_exact_i - share_exact_i) * 100, over the
  24 evaluated stations. Checked against the existing `.worst` and the
  existing `.cap_count` / `.floor_count` at the point of computation.
- F-079 (Section A): `ho.saving.single_run.margin.min.pct` /
  `.max.pct` (TIGHT and HIST_ACT_T, 6 rows) and
  `ho.saving.single_run.no_margin.min.pct` / `.max.pct` (NOM and HIST_ACT,
  6 rows), same formula as `ho.saving.single_run.min.pct` / `.max.pct`.
  Checked against the existing overall min/max at the point of computation.
- F-080 (Section C): `uo.berner.layouts.<ARM>.count` and
  `ts.berner.d01|d02|d03.layouts.<ARM>.count` for NOM, TIGHT, HIST,
  HIST_ACT: count of distinct `layout_hash` values over the BERNER rows of
  each campaign and arm, read from `R/tables/case_frame.csv` (per the seq 57
  task instructions, not from the per-case JSON records), with the covered
  horizons reported in `computation`.
"""
import hashlib
import json
import pathlib
from fractions import Fraction as F

import pandas as pd

REPO = pathlib.Path("C:/ermal/CSLAP_Full_Project/CSLAP-Synthetic")
R = REPO / "reports/horizon_robustness_results"

RESULT: dict = {}
_SHA_CACHE: dict = {}


def sha256_file(path: pathlib.Path) -> str:
    key = str(path)
    if key not in _SHA_CACHE:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        _SHA_CACHE[key] = h.hexdigest()
    return _SHA_CACHE[key]


def relpath(path: pathlib.Path) -> str:
    return path.relative_to(REPO).as_posix()


def src(path: pathlib.Path, selector: str) -> dict:
    return {"path": relpath(path), "sha256": sha256_file(path), "selector": selector}


def load_json(path: pathlib.Path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def entry(value_exact, value_float, unit, sources, computation, display_rounding=None):
    return {
        "value_exact": str(value_exact),
        "value_float": value_float,
        "unit": unit,
        "display_rounding": display_rounding,
        "sources": sources,
        "computation": computation,
    }


def unavailable(reason: str) -> str:
    return f"UNAVAILABLE: {reason}"


def set_key(key, val):
    if key in RESULT:
        raise KeyError(f"duplicate key {key}")
    RESULT[key] = val


# --------------------------------------------------------------------------
# Arm token <-> stored arm-name mapping (ANCHOR_SPEC conventions).
# --------------------------------------------------------------------------
TOKEN_TO_STORED = {
    "NOM": "NOM",
    "TIGHT": "TIGHT",
    "HIST": "HIST",
    "HIST_ACT": "HIST+ACT",
    "HIST_ACT_T": "HIST+ACT-T",
}
STORED_TO_TOKEN = {v: k for k, v in TOKEN_TO_STORED.items()}
SEED_TOKEN = {11: "s11", 22: "s22", 33: "s33"}


def load_campaign_cases(campaign: str, dataset_filter: str = None):
    """Load every non-frozen cases/*.json in a campaign, keyed by case_id.

    Returns dict case_id -> (data, path). Only reads *.json files that are
    not *.frozen.json (the frozen half of each pair is never opened).
    """
    cases_dir = R / "campaigns" / campaign / "cases"
    out = {}
    for p in sorted(cases_dir.glob("*.json")):
        if p.name.endswith(".frozen.json"):
            continue
        data = load_json(p)
        if dataset_filter is not None:
            if data.get("case", {}).get("dataset_id") != dataset_filter:
                continue
        out[data["case"]["case_id"]] = (data, p)
    return out


# ============================================================================
# Section A: held-out factorial (campaign ho3_20260913)
# ============================================================================
HO_CAMPAIGN = "ho3_20260913"
ho_cases_by_id = load_campaign_cases(HO_CAMPAIGN)

# Index by (arm_token, seed)
ho_index = {}
for cid, (data, path) in ho_cases_by_id.items():
    arm_stored = data["case"]["arm"]
    arm_token = STORED_TO_TOKEN[arm_stored]
    seed = data["case"]["seed"]
    ho_index[(arm_token, seed)] = (data, path)

ARMS_A = ["NOM", "TIGHT", "HIST_ACT", "HIST_ACT_T"]
SEEDS = [11, 22, 33]

# --- ho.pass.<ARM>.count ---
for arm in ARMS_A:
    sources = []
    passed = 0
    for seed in SEEDS:
        data, path = ho_index[(arm, seed)]
        ev = data["evaluation"]
        sources.append(src(path, f"evaluation.joint_pass (seed {seed})"))
        if ev["joint_pass"]:
            passed += 1
    set_key(
        f"ho.pass.{arm}.count",
        entry(passed, float(passed), "count", sources,
              "count of seeds (of 3) where evaluation.joint_pass is true"),
    )

# --- ho.visits.<ARM>.<SEED> and ho.visits.<ARM>.mean ---
arm_seed_visits = {}
for arm in ARMS_A:
    seed_fracs = []
    for seed in SEEDS:
        data, path = ho_index[(arm, seed)]
        ev = data["evaluation"]
        vex = ev["mean_visits_exact"]
        frac = F(vex)
        seed_fracs.append(frac)
        arm_seed_visits[(arm, seed)] = frac
        set_key(
            f"ho.visits.{arm}.{SEED_TOKEN[seed]}",
            entry(vex, float(frac), "visits_per_order",
                  [src(path, "evaluation.mean_visits_exact")],
                  "artifact exact field evaluation.mean_visits_exact"),
        )
    mean_frac = sum(seed_fracs, F(0)) / 3
    sources = [src(ho_index[(arm, s)][1], "evaluation.mean_visits_exact") for s in SEEDS]
    set_key(
        f"ho.visits.{arm}.mean",
        entry(mean_frac, float(mean_frac), "visits_per_order", sources,
              "mean of evaluation.mean_visits_exact over the 3 seeds", display_rounding=6),
    )

# --- ho.visits.incumbent (confirm identical across the 12 rows) ---
incumbent_visit_vals = set()
incumbent_sources = []
for (arm, seed), (data, path) in ho_index.items():
    re_ = data["reference_evaluation"]
    incumbent_visit_vals.add(re_["mean_visits_exact"])
    incumbent_sources.append(src(path, "reference_evaluation.mean_visits_exact"))
incumbent_identical = len(incumbent_visit_vals) == 1
incumbent_visits_exact = next(iter(incumbent_visit_vals))
set_key(
    "ho.visits.incumbent",
    entry(incumbent_visits_exact, float(F(incumbent_visits_exact)), "visits_per_order",
          incumbent_sources,
          "reference_evaluation.mean_visits_exact, confirmed identical=%s across all 12 rows"
          % incumbent_identical, display_rounding=6),
)

# --- ho.visits.HIST_ACT_T_over_TIGHT.pct ---
mean_hat = F(str(RESULT["ho.visits.HIST_ACT_T.mean"]["value_exact"]))
mean_tight = F(str(RESULT["ho.visits.TIGHT.mean"]["value_exact"]))
ratio_pct = (mean_hat / mean_tight - 1) * 100
sources = [src(ho_index[("HIST_ACT_T", s)][1], "evaluation.mean_visits_exact") for s in SEEDS] + \
          [src(ho_index[("TIGHT", s)][1], "evaluation.mean_visits_exact") for s in SEEDS]
set_key(
    "ho.visits.HIST_ACT_T_over_TIGHT.pct",
    entry(ratio_pct, float(ratio_pct), "pct", sources,
          "(mean HIST_ACT_T / mean TIGHT - 1) * 100, from exact seed means", display_rounding=6),
)

# --- ho.saving.<ARM>.pct and single_run min/max ---
incumbent_frac = F(incumbent_visits_exact)
for arm in ARMS_A:
    arm_mean_frac = F(str(RESULT[f"ho.visits.{arm}.mean"]["value_exact"]))
    saving_pct = (incumbent_frac - arm_mean_frac) / incumbent_frac * 100
    sources = [src(ho_index[(arm, s)][1], "evaluation.mean_visits_exact") for s in SEEDS] + \
              [src(ho_index[(arm, SEEDS[0])][1], "reference_evaluation.mean_visits_exact")]
    set_key(
        f"ho.saving.{arm}.pct",
        entry(saving_pct, float(saving_pct), "pct", sources,
              "(incumbent - arm mean) / incumbent * 100", display_rounding=6),
    )

single_run_pcts = []
single_run_sources = []
for arm in ARMS_A:
    for seed in SEEDS:
        seed_frac = arm_seed_visits[(arm, seed)]
        pct = (incumbent_frac - seed_frac) / incumbent_frac * 100
        single_run_pcts.append((pct, arm, seed))
        single_run_sources.append(src(ho_index[(arm, seed)][1], "evaluation.mean_visits_exact"))
single_run_pcts.sort(key=lambda t: t[0])
min_pct = single_run_pcts[0][0]
max_pct = single_run_pcts[-1][0]
set_key(
    "ho.saving.single_run.min.pct",
    entry(min_pct, float(min_pct), "pct", single_run_sources,
          "min over the 12 rows of (incumbent - seed visits) / incumbent * 100 "
          f"(achieved by {single_run_pcts[0][1]}.{SEED_TOKEN[single_run_pcts[0][2]]})",
          display_rounding=6),
)
set_key(
    "ho.saving.single_run.max.pct",
    entry(max_pct, float(max_pct), "pct", single_run_sources,
          "max over the 12 rows of (incumbent - seed visits) / incumbent * 100 "
          f"(achieved by {single_run_pcts[-1][1]}.{SEED_TOKEN[single_run_pcts[-1][2]]})",
          display_rounding=6),
)

# --- ho.saving.single_run.margin.{min,max}.pct, .no_margin.{min,max}.pct (F-079) ---
# margin arms: TIGHT, HIST_ACT_T (the "-T" / tightened arms carry an explicit margin).
# no_margin arms: NOM, HIST_ACT.
MARGIN_ARMS = {"TIGHT", "HIST_ACT_T"}
NO_MARGIN_ARMS = {"NOM", "HIST_ACT"}


def _subset_extreme(arms_set):
    subset_sorted = sorted((t for t in single_run_pcts if t[1] in arms_set), key=lambda t: t[0])
    return subset_sorted[0], subset_sorted[-1], subset_sorted


margin_min_t, margin_max_t, margin_sorted = _subset_extreme(MARGIN_ARMS)
no_margin_min_t, no_margin_max_t, no_margin_sorted = _subset_extreme(NO_MARGIN_ARMS)

if min(margin_min_t[0], no_margin_min_t[0]) != min_pct:
    raise ValueError(
        "ho.saving.single_run margin/no_margin split: min(margin_min, no_margin_min) "
        f"= {min(margin_min_t[0], no_margin_min_t[0])} != overall min_pct = {min_pct}"
    )
if max(margin_max_t[0], no_margin_max_t[0]) != max_pct:
    raise ValueError(
        "ho.saving.single_run margin/no_margin split: max(margin_max, no_margin_max) "
        f"= {max(margin_max_t[0], no_margin_max_t[0])} != overall max_pct = {max_pct}"
    )

margin_sources = [src(ho_index[(arm, seed)][1], "evaluation.mean_visits_exact")
                   for (_, arm, seed) in margin_sorted] + \
                  [src(ho_index[(margin_sorted[0][1], SEEDS[0])][1], "reference_evaluation.mean_visits_exact")]
no_margin_sources = [src(ho_index[(arm, seed)][1], "evaluation.mean_visits_exact")
                      for (_, arm, seed) in no_margin_sorted] + \
                     [src(ho_index[(no_margin_sorted[0][1], SEEDS[0])][1], "reference_evaluation.mean_visits_exact")]

set_key(
    "ho.saving.single_run.margin.min.pct",
    entry(margin_min_t[0], float(margin_min_t[0]), "pct", margin_sources,
          "min over the 6 TIGHT and HIST_ACT_T rows of (incumbent - seed visits) / incumbent * 100 "
          f"(achieved by {margin_min_t[1]}.{SEED_TOKEN[margin_min_t[2]]})", display_rounding=6),
)
set_key(
    "ho.saving.single_run.margin.max.pct",
    entry(margin_max_t[0], float(margin_max_t[0]), "pct", margin_sources,
          "max over the 6 TIGHT and HIST_ACT_T rows of (incumbent - seed visits) / incumbent * 100 "
          f"(achieved by {margin_max_t[1]}.{SEED_TOKEN[margin_max_t[2]]})", display_rounding=6),
)
set_key(
    "ho.saving.single_run.no_margin.min.pct",
    entry(no_margin_min_t[0], float(no_margin_min_t[0]), "pct", no_margin_sources,
          "min over the 6 NOM and HIST_ACT rows of (incumbent - seed visits) / incumbent * 100 "
          f"(achieved by {no_margin_min_t[1]}.{SEED_TOKEN[no_margin_min_t[2]]})", display_rounding=6),
)
set_key(
    "ho.saving.single_run.no_margin.max.pct",
    entry(no_margin_max_t[0], float(no_margin_max_t[0]), "pct", no_margin_sources,
          "max over the 6 NOM and HIST_ACT rows of (incumbent - seed visits) / incumbent * 100 "
          f"(achieved by {no_margin_max_t[1]}.{SEED_TOKEN[no_margin_max_t[2]]})", display_rounding=6),
)

# --- ho.maxdev.<ARM>.<SEED>, .max, .min ---
def station_maxdev(stations):
    """max_i |share_exact - target_exact| * 100 over the station list."""
    devs = [abs(F(s["share_exact"]) - F(s["target_exact"])) * 100 for s in stations]
    return max(devs)


arm_seed_maxdev = {}
for arm in ARMS_A:
    seed_devs = []
    for seed in SEEDS:
        data, path = ho_index[(arm, seed)]
        ev = data["evaluation"]
        dev = station_maxdev(ev["stations"])
        arm_seed_maxdev[(arm, seed)] = dev
        seed_devs.append(dev)
        set_key(
            f"ho.maxdev.{arm}.{SEED_TOKEN[seed]}",
            entry(dev, float(dev), "pp", [src(path, "evaluation.stations[*].share_exact,target_exact")],
                  "max over the 24 stations of |share_exact - target_exact| * 100",
                  display_rounding=6),
        )
    dev_max = max(seed_devs)
    dev_min = min(seed_devs)
    sources = [src(ho_index[(arm, s)][1], "evaluation.stations[*].share_exact,target_exact") for s in SEEDS]
    set_key(f"ho.maxdev.{arm}.max", entry(dev_max, float(dev_max), "pp", sources,
                                           "max over the 3 seeds of ho.maxdev.<ARM>.<SEED>", display_rounding=6))
    set_key(f"ho.maxdev.{arm}.min", entry(dev_min, float(dev_min), "pp", sources,
                                           "min over the 3 seeds of ho.maxdev.<ARM>.<SEED>", display_rounding=6))

# --- ho.maxdev.incumbent (same quantity from reference_evaluation, confirm identical) ---
incumbent_maxdev_vals = set()
incumbent_maxdev_sources = []
for (arm, seed), (data, path) in ho_index.items():
    re_ = data["reference_evaluation"]
    dev = station_maxdev(re_["stations"])
    incumbent_maxdev_vals.add(dev)
    incumbent_maxdev_sources.append(src(path, "reference_evaluation.stations[*].share_exact,target_exact"))
incumbent_maxdev_identical = len(incumbent_maxdev_vals) == 1
incumbent_maxdev = next(iter(incumbent_maxdev_vals))
set_key(
    "ho.maxdev.incumbent",
    entry(incumbent_maxdev, float(incumbent_maxdev), "pp", incumbent_maxdev_sources,
          "max over the 24 stations of |share_exact - target_exact| * 100, from reference_evaluation, "
          "confirmed identical=%s across all 12 rows" % incumbent_maxdev_identical, display_rounding=6),
)

# --- ho.breach.<ARM>.<SEED>.worst / .cap_count / .floor_count / .cap_worst / .floor_worst ---
for arm in ARMS_A:
    for seed in SEEDS:
        data, path = ho_index[(arm, seed)]
        ev = data["evaluation"]
        worst = F(ev["worst_excess_percentage_points_exact"])
        set_key(
            f"ho.breach.{arm}.{SEED_TOKEN[seed]}.worst",
            entry(worst, float(worst), "pp", [src(path, "evaluation.worst_excess_percentage_points_exact")],
                  "artifact exact field evaluation.worst_excess_percentage_points_exact "
                  "(worst cap/floor exceedance in pp, 0 if pass)", display_rounding=6),
        )
        cap_count = ev["cap_violation_count"]
        floor_count = ev["floor_violation_count"]
        set_key(
            f"ho.breach.{arm}.{SEED_TOKEN[seed]}.cap_count",
            entry(cap_count, float(cap_count), "count",
                  [src(path, "evaluation.cap_violation_count")],
                  "artifact field evaluation.cap_violation_count"),
        )
        set_key(
            f"ho.breach.{arm}.{SEED_TOKEN[seed]}.floor_count",
            entry(floor_count, float(floor_count), "count",
                  [src(path, "evaluation.floor_violation_count")],
                  "artifact field evaluation.floor_violation_count"),
        )

        # F-078: directional breach magnitudes from the stored per-station future
        # shares (share_exact) and band limits (cap_exact, floor_exact).
        stations = ev["stations"]
        cap_excess_list = [max(F(0), F(s["share_exact"]) - F(s["cap_exact"])) for s in stations]
        floor_excess_list = [max(F(0), F(s["floor_exact"]) - F(s["share_exact"])) for s in stations]
        cap_worst_frac = max(cap_excess_list) * 100
        floor_worst_frac = max(floor_excess_list) * 100

        larger = max(cap_worst_frac, floor_worst_frac)
        if larger != worst:
            raise ValueError(
                f"ho.breach.{arm}.{SEED_TOKEN[seed]}: max(cap_worst={cap_worst_frac}, "
                f"floor_worst={floor_worst_frac}) = {larger} != .worst = {worst}"
            )
        if (cap_worst_frac > 0) != (cap_count > 0):
            raise ValueError(
                f"ho.breach.{arm}.{SEED_TOKEN[seed]}.cap_worst positivity ({cap_worst_frac} > 0) "
                f"disagrees with cap_violation_count = {cap_count}"
            )
        if (floor_worst_frac > 0) != (floor_count > 0):
            raise ValueError(
                f"ho.breach.{arm}.{SEED_TOKEN[seed]}.floor_worst positivity ({floor_worst_frac} > 0) "
                f"disagrees with floor_violation_count = {floor_count}"
            )

        stations_src = src(path, "evaluation.stations[*].share_exact,cap_exact,floor_exact")
        set_key(
            f"ho.breach.{arm}.{SEED_TOKEN[seed]}.cap_worst",
            entry(cap_worst_frac, float(cap_worst_frac), "pp", [stations_src],
                  "max over the 24 stations of max(0, share_exact - cap_exact) * 100 "
                  "(largest excess above the cap); 0 if no station exceeds its cap; checked equal "
                  "to .worst when it is the larger of the two sides, and checked positive iff "
                  ".cap_count is positive", display_rounding=6),
        )
        set_key(
            f"ho.breach.{arm}.{SEED_TOKEN[seed]}.floor_worst",
            entry(floor_worst_frac, float(floor_worst_frac), "pp", [stations_src],
                  "max over the 24 stations of max(0, floor_exact - share_exact) * 100 "
                  "(largest shortfall below the floor); 0 if no station is below its floor; checked "
                  "equal to .worst when it is the larger of the two sides, and checked positive iff "
                  ".floor_count is positive", display_rounding=6),
        )

# --- ho.min_slack.<ARM>.<SEED> ---
for arm in ARMS_A:
    for seed in SEEDS:
        data, path = ho_index[(arm, seed)]
        slack = F(data["validation"]["minimum_required_slack_exact"])
        set_key(
            f"ho.min_slack.{arm}.{SEED_TOKEN[seed]}",
            entry(slack, float(slack), "share", [src(path, "validation.minimum_required_slack_exact")],
                  "artifact exact field validation.minimum_required_slack_exact"),
        )

# --- ho.gap.<ARM>.<SEED>, ho.bound.<ARM>.<SEED> ---
for arm in ARMS_A:
    for seed in SEEDS:
        data, path = ho_index[(arm, seed)]
        sr = data["solve_result"]
        gap = sr["gap"]
        bound = sr["bound"]
        set_key(
            f"ho.gap.{arm}.{SEED_TOKEN[seed]}",
            entry(str(gap), float(gap), "fraction", [src(path, "solve_result.gap")],
                  "artifact field solve_result.gap, no exact variant stored"),
        )
        set_key(
            f"ho.bound.{arm}.{SEED_TOKEN[seed]}",
            entry(int(bound), float(bound), "visits", [src(path, "solve_result.bound")],
                  "artifact field solve_result.bound (integer visits count)"),
        )

# --- ho.incumbent.joint_pass, ho.incumbent.worst_excess ---
incumbent_jp_vals = set()
incumbent_we_vals = set()
for (arm, seed), (data, path) in ho_index.items():
    re_ = data["reference_evaluation"]
    incumbent_jp_vals.add(re_["joint_pass"])
    incumbent_we_vals.add(re_["worst_excess_percentage_points_exact"])
jp_identical = len(incumbent_jp_vals) == 1
we_identical = len(incumbent_we_vals) == 1
jp_val = next(iter(incumbent_jp_vals))
we_val_exact = next(iter(incumbent_we_vals))
set_key(
    "ho.incumbent.joint_pass",
    entry("1" if jp_val else "0", 1.0 if jp_val else 0.0, "bool", incumbent_maxdev_sources[:1],
          "reference_evaluation.joint_pass, confirmed identical=%s across all 12 rows" % jp_identical),
)
set_key(
    "ho.incumbent.worst_excess",
    entry(F(we_val_exact), float(F(we_val_exact)), "pp", incumbent_maxdev_sources[:1],
          "reference_evaluation.worst_excess_percentage_points_exact, confirmed identical=%s across all 12 rows"
          % we_identical, display_rounding=6),
)

# --- ho.departures.<ARM>.<SEED>.above / .below ---
for arm in ARMS_A:
    for seed in SEEDS:
        data, path = ho_index[(arm, seed)]
        ev = data["evaluation"]
        above = sum(1 for s in ev["stations"] if s["beyond_worst_scenario"])
        below = sum(1 for s in ev["stations"] if s["below_lowest_scenario"])
        set_key(
            f"ho.departures.{arm}.{SEED_TOKEN[seed]}.above",
            entry(above, float(above), "count", [src(path, "evaluation.stations[*].beyond_worst_scenario")],
                  "count of stations with evaluation.stations[i].beyond_worst_scenario true"),
        )
        set_key(
            f"ho.departures.{arm}.{SEED_TOKEN[seed]}.below",
            entry(below, float(below), "count", [src(path, "evaluation.stations[*].below_lowest_scenario")],
                  "count of stations with evaluation.stations[i].below_lowest_scenario true"),
        )

# ============================================================================
# Section B: drift and dispersion (F16, F17)
# ============================================================================
drift_path = R / "tables" / "drift_survey.csv"
drift_df = pd.read_csv(drift_path, dtype=str)
drift_row = drift_df[drift_df["dataset_id"] == "BERNER@holdout"].iloc[0]

DRIFT_COLS = {
    "hist_tv_max": "historical_tv_max",
    "hist_tv_mean": "historical_tv_mean",
    "hist_tv_p90": "historical_tv_p90",
    "hist_tv_last": "historical_tv_last",
    "future_tv": "future_tv_ex_post",
    "blocks": "historical_blocks",
    "n": "n",
    "origin": "origin",
}
drift_unit = {
    "hist_tv_max": "tv", "hist_tv_mean": "tv", "hist_tv_p90": "tv", "hist_tv_last": "tv",
    "future_tv": "tv", "blocks": "count", "n": "count", "origin": "count",
}
for key, col in DRIFT_COLS.items():
    raw = drift_row[col]
    if key in ("blocks", "n", "origin"):
        set_key(f"drift.holdout.{key}", entry(int(raw), float(raw), drift_unit[key],
                                               [src(drift_path, f"row BERNER@holdout, column {col}")],
                                               f"row BERNER@holdout, column {col} (integer count)"))
    else:
        set_key(f"drift.holdout.{key}", entry(raw, float(raw), drift_unit[key],
                                               [src(drift_path, f"row BERNER@holdout, column {col}")],
                                               f"row BERNER@holdout, column {col}, decimal string as stored",
                                               display_rounding=6))

hist_tv_max_f = F(drift_row["historical_tv_max"])
future_tv_f = F(drift_row["future_tv_ex_post"])
n_f = F(int(drift_row["n"]))
origin_f = F(int(drift_row["origin"]))
w_star = 1 - hist_tv_max_f / future_tv_f
w_order_count = n_f / origin_f
drift_src = [src(drift_path, "row BERNER@holdout")]
set_key("drift.holdout.w_star", entry(w_star, float(w_star), "fraction", drift_src,
                                       "1 - historical_tv_max / future_tv_ex_post", display_rounding=6))
set_key("drift.holdout.w_order_count", entry(w_order_count, float(w_order_count), "fraction", drift_src,
                                              "n / origin", display_rounding=6))

ll_base = hist_tv_max_f / (1 - w_order_count)
set_key("drift.holdout.hist_tv_max.like_for_like",
        entry(ll_base, float(ll_base), "tv", drift_src,
              "historical_tv_max / (1 - w_order_count)", display_rounding=6))

for wname, wval in (("w_0_05", F(5, 100)), ("w_0_10", F(10, 100)), ("w_one_eleventh", F(1, 11))):
    v = hist_tv_max_f / (1 - wval)
    set_key(f"drift.holdout.hist_tv_max.like_for_like.{wname}",
            entry(v, float(v), "tv", drift_src,
                  f"historical_tv_max / (1 - {wname.replace('w_', '').replace('_', '.')})",
                  display_rounding=6))

disp_path = R / "tables" / "dispersion_survey.csv"
disp_df = pd.read_csv(disp_path, dtype=str)
disp_df["n_int"] = disp_df["n"].astype(int)
disp_df["origin_int"] = disp_df["origin"].astype(int)
disp_berner = disp_df[(disp_df["dataset_id"] == "BERNER") & (disp_df["origin_int"] == 199403)]
H_MAP = {"n_half": 10937, "n_P": 21874, "n_2P": 43748}
for hname, hval in H_MAP.items():
    row = disp_berner[disp_berner["n_int"] == hval].iloc[0]
    max_abs = row["max_abs_pp"]
    max_abs_f = F(max_abs)
    set_key(f"disp.explor.{hname}.max_abs",
            entry(max_abs, float(max_abs), "pp", [src(disp_path, f"BERNER industrial row n={hval}, origin=199403, column max_abs_pp")],
                  f"row dataset_id=BERNER, origin=199403, n={hval}, column max_abs_pp, decimal string as stored",
                  display_rounding=6))
    ratio = F(hval, 199403)
    ll = max_abs_f / (1 - ratio)
    set_key(f"disp.explor.{hname}.max_abs.like_for_like",
            entry(ll, float(ll), "pp", [src(disp_path, f"BERNER industrial row n={hval}, origin=199403, column max_abs_pp")],
                  f"max_abs_pp / (1 - {hval}/199403)", display_rounding=6))

# ============================================================================
# Section C: upper-only versus two-sided reconciliation (F12)
# ============================================================================
def load_manifest(campaign):
    p = R / "campaigns" / campaign / "manifest.json"
    return load_json(p), p


ARMS_C = ["NOM", "TIGHT", "HIST", "HIST_ACT"]


def berner_case_index(campaign, manifest_rows, manifest_path):
    """arm_token, n -> (data, case_path) for BERNER rows in a campaign."""
    idx = {}
    berner_rows = [r for r in manifest_rows if r.get("dataset_id") == "BERNER"]
    for r in berner_rows:
        arm_token = STORED_TO_TOKEN[r["arm"]]
        n = r["n"]
        case_path = R / "campaigns" / campaign / "cases" / f"{r['case_id']}.json"
        idx[(arm_token, n)] = load_json(case_path), case_path
    return idx


# --- uo.berner (screen_20260910, delta 0.01, upper-only) ---
screen_manifest, screen_manifest_path = load_manifest("screen_20260910")
screen_idx = berner_case_index("screen_20260910", screen_manifest["rows"], screen_manifest_path)
screen_horizons = sorted({n for (_, n) in screen_idx})
assert screen_horizons == [10937, 21874, 43748]

for arm in ARMS_C:
    passed = 0
    sources = []
    for n in screen_horizons:
        data, path = screen_idx[(arm, n)]
        ev = data["evaluation"]
        sources.append(src(path, f"evaluation.joint_pass (n={n})"))
        if ev["joint_pass"]:
            passed += 1
    set_key(f"uo.berner.pass.{arm}.count",
            entry(passed, float(passed), "count", sources,
                  "count of horizons (of 3) where evaluation.joint_pass is true, "
                  "campaign screen_20260910, delta=0.01, BERNER"))

for n in screen_horizons:
    data, path = screen_idx[("TIGHT", n)]
    slack = F(data["validation"]["minimum_required_slack_exact"])
    set_key(f"uo.berner.min_slack.TIGHT.{n}",
            entry(slack, float(slack), "share", [src(path, "validation.minimum_required_slack_exact")],
                  f"TIGHT arm, n={n}, campaign screen_20260910, validation.minimum_required_slack_exact"))

# --- ts.berner.d0X.pass (Q-012) ---
TS_CAMPAIGNS = {"d01": "ts_b01_20260912", "d02": "ts_d02_20260912", "d03": "ts_b03_20260912"}
ts_idx = {}
ts_manifest_rows = {}
for dtag, campaign in TS_CAMPAIGNS.items():
    manifest, manifest_path = load_manifest(campaign)
    ts_manifest_rows[dtag] = (manifest["rows"], manifest_path)
    idx = berner_case_index(campaign, manifest["rows"], manifest_path)
    ts_idx[dtag] = idx
    horizons = sorted({n for (_, n) in idx})
    assert horizons == [10937, 21874, 43748], (dtag, horizons)

    for arm in ARMS_C:
        passed = 0
        sources = []
        for n in horizons:
            data, path = idx[(arm, n)]
            ev = data["evaluation"]
            sources.append(src(path, f"evaluation.joint_pass (n={n})"))
            if ev["joint_pass"]:
                passed += 1
        set_key(f"ts.berner.{dtag}.pass.{arm}.count",
                entry(passed, float(passed), "count", sources,
                      f"count of horizons (of 3) where evaluation.joint_pass is true, "
                      f"campaign {campaign}, BERNER two-sided"))

# --- ts.berner.d02.min_slack.TIGHT.<n> ---
d02_idx = ts_idx["d02"]
d02_horizons = sorted({n for (_, n) in d02_idx})
for n in d02_horizons:
    data, path = d02_idx[("TIGHT", n)]
    slack = F(data["validation"]["minimum_required_slack_exact"])
    set_key(f"ts.berner.d02.min_slack.TIGHT.{n}",
            entry(slack, float(slack), "share", [src(path, "validation.minimum_required_slack_exact")],
                  f"TIGHT arm, n={n}, campaign ts_d02_20260912, validation.minimum_required_slack_exact"))

# --- ts.berner.d02.HIST_ACT / HIST cap_breaches_total / floor_breaches_total ---
for arm in ("HIST_ACT", "HIST"):
    cap_total = 0
    floor_total = 0
    sources = []
    for n in d02_horizons:
        data, path = d02_idx[(arm, n)]
        ev = data["evaluation"]
        cap_total += ev["cap_violation_count"]
        floor_total += ev["floor_violation_count"]
        sources.append(src(path, "evaluation.cap_violation_count, evaluation.floor_violation_count"))
    set_key(f"ts.berner.d02.{arm}.cap_breaches_total",
            entry(cap_total, float(cap_total), "count", sources,
                  "sum of evaluation.cap_violation_count over the 3 horizons, campaign ts_d02_20260912"))
    set_key(f"ts.berner.d02.{arm}.floor_breaches_total",
            entry(floor_total, float(floor_total), "count", sources,
                  "sum of evaluation.floor_violation_count over the 3 horizons, campaign ts_d02_20260912"))

# --- uo.berner.layouts.<ARM>.count, ts.berner.d0X.layouts.<ARM>.count (F-080) ---
# Per the seq 57 task instructions: distinct layout_hash values over the BERNER rows of
# each campaign and arm in R/tables/case_frame.csv (not the per-case JSON records).
case_frame_path_c = R / "tables" / "case_frame.csv"
case_frame_df_c = pd.read_csv(case_frame_path_c, dtype=str)
case_frame_df_c["n_int"] = case_frame_df_c["n"].astype(int)

LAYOUT_CAMPAIGNS = {
    "uo.berner": "screen_20260910",
    "ts.berner.d01": "ts_b01_20260912",
    "ts.berner.d02": "ts_d02_20260912",
    "ts.berner.d03": "ts_b03_20260912",
}
ARMS_LAYOUT = ["NOM", "TIGHT", "HIST", "HIST_ACT"]

for key_prefix, campaign in LAYOUT_CAMPAIGNS.items():
    camp_berner = case_frame_df_c[
        (case_frame_df_c["campaign"] == campaign) & (case_frame_df_c["dataset_id"] == "BERNER")
    ]
    for arm in ARMS_LAYOUT:
        arm_stored = TOKEN_TO_STORED[arm]
        sub = camp_berner[camp_berner["arm"] == arm_stored]
        horizons = sorted(sub["n_int"].unique().tolist())
        n_layouts = int(sub["layout_hash"].nunique())
        set_key(
            f"{key_prefix}.layouts.{arm}.count",
            entry(
                n_layouts, float(n_layouts), "count",
                [src(case_frame_path_c,
                     f"campaign={campaign}, dataset_id=BERNER, arm={arm_stored}, column layout_hash")],
                f"distinct layout_hash values over case_frame.csv rows with campaign={campaign}, "
                f"dataset_id=BERNER, arm={arm_stored}; those rows cover horizons n={horizons}",
            ),
        )

# --- ts.synthetic_instances.count ---
synthetic_ids = set()
synth_sources = []
for dtag, (rows, mpath) in ts_manifest_rows.items():
    ds_here = {r["dataset_id"] for r in rows if r.get("dataset_id") != "BERNER"}
    if ds_here:
        synth_sources.append(src(mpath, "rows[*].dataset_id (non-BERNER)"))
    synthetic_ids |= ds_here
set_key("ts.synthetic_instances.count",
        entry(len(synthetic_ids), float(len(synthetic_ids)), "count", synth_sources,
              "distinct non-BERNER dataset_id values across manifest rows of ts_b01_20260912, "
              "ts_d02_20260912, ts_b03_20260912 (rule=two_sided); found: "
              + ", ".join(sorted(synthetic_ids))))

# ============================================================================
# Section D: accounting and context
# ============================================================================
audit_path = R / "analysis_audit.md"
audit_text = audit_path.read_text(encoding="utf-8")

import re

analysed = re.findall(r"^\|\s*`([a-zA-Z0-9_]+)`\s*\|", audit_text, flags=re.MULTILINE)
# keep only rows from the "Campaigns included" table (first table with backtick-quoted names)
included_section = audit_text.split("## Campaigns included")[1].split("## Denominator audit")[0]
analysed = re.findall(r"^\|\s*`([a-zA-Z0-9_]+)`\s*\|", included_section, flags=re.MULTILINE)

superseded_line = [ln for ln in audit_text.splitlines() if ln.startswith("Excluded as superseded")][0]
superseded = re.findall(r"`([a-zA-Z0-9_]+)`", superseded_line)

audit_src = [src(audit_path, "section 'Campaigns included' and 'Excluded as superseded' line")]
set_key("acct.campaigns.analysed",
        entry(json.dumps(analysed), None, "list", audit_src,
              "campaign names in backticks, section 'Campaigns included' rows"))
set_key("acct.campaigns.superseded",
        entry(json.dumps(superseded), None, "list", audit_src,
              "campaign names in backticks, 'Excluded as superseded' line"))

case_frame_path = R / "tables" / "case_frame.csv"
cf = pd.read_csv(case_frame_path)
cf_src = [src(case_frame_path, "columns campaign, scored, allocation_returned")]

campaigns_present = sorted(cf["campaign"].unique())
assert sorted(analysed) == campaigns_present, (sorted(analysed), campaigns_present)

authorized = len(cf)
scored = int((cf["scored"] == True).sum())  # noqa: E712
no_allocation = int((cf["scored"] == False).sum())  # noqa: E712
set_key("acct.rows.authorized", entry(authorized, float(authorized), "count", cf_src,
                                       "len(case_frame.csv), restricted to the analysed campaigns "
                                       "(all rows in the table already are)"))
set_key("acct.rows.scored", entry(scored, float(scored), "count", cf_src,
                                   "count of case_frame.csv rows with scored == True"))
set_key("acct.rows.no_allocation", entry(no_allocation, float(no_allocation), "count", cf_src,
                                          "count of case_frame.csv rows with scored == False "
                                          "(equivalently allocation_returned == False)"))

layouts_scored = int(cf.loc[cf["scored"] == True, "layout_hash"].nunique())  # noqa: E712
set_key("acct.layouts.scored",
        entry(layouts_scored, float(layouts_scored), "count",
              [src(case_frame_path, "column layout_hash, rows with scored == True")],
              "distinct layout_hash values among case_frame.csv rows with scored == True"))

# --- alias.join_exact, alias.map ---
station_path = R / "tables" / "station_profile_industrial.csv"
sp = pd.read_csv(station_path)
sp_ho3 = sp[sp["campaign"] == "ho3_20260913"]
map_check = sp_ho3.groupby("station_index")["station"].nunique()
one_to_one_in_table = bool((map_check == 1).all())
alias_dict = sp_ho3.drop_duplicates("station_index").set_index("station_index")["station"].to_dict()
alias_dict = {int(k): v for k, v in alias_dict.items()}

# station_index set used in the held-out case records' reference evaluation
ref_case, ref_path = next(iter(ho_index.values()))
ref_station_indices = sorted(s["station_index"] for s in ref_case["reference_evaluation"]["stations"])
table_station_indices = sorted(alias_dict.keys())
join_exact = one_to_one_in_table and (ref_station_indices == table_station_indices) and \
    (len(set(ref_station_indices)) == len(ref_station_indices))

set_key("alias.join_exact",
        entry("1" if join_exact else "0", 1.0 if join_exact else 0.0, "bool",
              [src(station_path, "campaign=ho3_20260913, column station_index"),
               src(ref_path, "reference_evaluation.stations[*].station_index")],
              "station_index in station_profile_industrial.csv (campaign ho3_20260913) joins one-to-one "
              "onto the station_index set used in the held-out case records' reference evaluation"))
set_key("alias.map",
        entry(json.dumps({str(k): v for k, v in sorted(alias_dict.items())}), None, "map",
              [src(station_path, "campaign=ho3_20260913, columns station_index, station")],
              "{station_index: station} from station_profile_industrial.csv, campaign ho3_20260913, "
              "one row per station_index"))

# --- ho.incumbent.training_slack.history, ho.incumbent.training_slack.hist_act (Q-005 revision) ---
# ANCHOR_SPEC section D replaces the ambiguous single key with two, selected by case arm (not by
# inspecting scenario_shares[0]): the NOM/TIGHT rows train on the single history scenario, the
# HIST_ACT/HIST_ACT_T rows train on the historical block scenario set.
TRAINING_SLACK_GROUPS = {
    "history": ["NOM", "TIGHT"],
    "hist_act": ["HIST_ACT", "HIST_ACT_T"],
}

for group_name, arms in TRAINING_SLACK_GROUPS.items():
    slack_vals = set()
    label_sets = set()
    sources = []
    for arm in arms:
        for seed in SEEDS:
            data, path = ho_index[(arm, seed)]
            v = data["reference_evaluation"]["validation"]
            slack_vals.add(v["minimum_required_slack_exact"])
            label_sets.add(tuple((s["label"], s["start"], s["stop"]) for s in v["scenario_shares"]))
            sources.append(
                src(path, f"reference_evaluation.validation.minimum_required_slack_exact "
                          f"(arm={arm}, seed={seed})")
            )
    if len(slack_vals) != 1:
        raise ValueError(
            f"ho.incumbent.training_slack.{group_name}: minimum_required_slack_exact is not "
            f"identical across the 6 rows of arms {arms}: {sorted(slack_vals)}"
        )
    if len(label_sets) != 1:
        raise ValueError(
            f"ho.incumbent.training_slack.{group_name}: reference_evaluation.validation."
            f"scenario_shares label/start/stop is not identical across the 6 rows of arms "
            f"{arms}: {label_sets}"
        )
    slack_exact = next(iter(slack_vals))
    slack_frac = F(slack_exact)
    labels = next(iter(label_sets))
    label_desc = ", ".join(f"(label={lab}, start={st}, stop={sp_})" for (lab, st, sp_) in labels)
    set_key(
        f"ho.incumbent.training_slack.{group_name}",
        entry(
            slack_exact, float(slack_frac), "share", sources,
            "reference_evaluation.validation.minimum_required_slack_exact, taken from the "
            f"{' and '.join(arms)} rows (case.arm tokens {arms}) of campaign {HO_CAMPAIGN}, all "
            "3 seeds each (6 rows); rows selected by case.arm, not by scenario_shares[0]; "
            "confirmed identical across all 6 rows; those rows' "
            "reference_evaluation.validation.scenario_shares entries are: " + label_desc,
            display_rounding=6,
        ),
    )

# ============================================================================
# Emit
# ============================================================================
print(json.dumps(RESULT, indent=None, sort_keys=True))
