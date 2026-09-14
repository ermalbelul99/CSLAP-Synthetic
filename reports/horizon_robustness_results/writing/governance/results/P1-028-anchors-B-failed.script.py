"""
P1 anchors, builder B (double-blind reproduction).
Reads only the allowed inputs listed in ANCHOR_SPEC.md and prints one JSON
object {key: entry} to stdout. Standard library + pandas (for csv/json path
walking convenience only; all numeric work is exact via fractions.Fraction).
Writes nothing. Imports no repository module.
"""
import csv
import hashlib
import json
import re
import sys
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path

REPO_ROOT = Path(r"C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic")
R = REPO_ROOT / "reports" / "horizon_robustness_results"

_SHA_CACHE: dict = {}


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/")


def sha256_of(path: Path) -> str:
    key = str(path)
    if key not in _SHA_CACHE:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        _SHA_CACHE[key] = h.hexdigest()
    return _SHA_CACHE[key]


def src(path: Path, selector: str) -> list:
    return [{"path": rel(path), "sha256": sha256_of(path), "selector": selector}]


def entry(value_exact, value_float, unit, display_rounding, sources, computation):
    return {
        "value_exact": value_exact,
        "value_float": value_float,
        "unit": unit,
        "display_rounding": display_rounding,
        "sources": sources,
        "computation": computation,
    }


def exact_entry(fr: F, unit: str, dr, sources, computation) -> dict:
    return entry(str(fr), float(fr), unit, dr, sources, computation)


def count_entry(n: int, sources, computation) -> dict:
    return entry(str(int(n)), float(n), "count", None, sources, computation)


def bool_entry(b: bool, sources, computation) -> dict:
    return entry("1" if b else "0", float(1 if b else 0), "bool", None, sources, computation)


def dec_frac(s: str) -> F:
    """Exact rational from a decimal string exactly as stored in a file."""
    return F(Decimal(s))


def load_json_literal(path: Path) -> dict:
    """Parse JSON keeping every number as the literal string written in the
    file (no float round-trip), so non-exact decimal fields (gap, etc.) can
    be reproduced verbatim."""
    text = path.read_text(encoding="utf-8")
    return json.loads(text, parse_float=str, parse_int=str)


def read_csv_rows(path: Path) -> list:
    """Read a CSV preserving every field as the literal string stored in the
    file (no pandas float64 round-trip)."""
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


OUT: dict = {}

# --------------------------------------------------------------------------
# Shared loads
# --------------------------------------------------------------------------
CASE_FRAME_PATH = R / "tables" / "case_frame.csv"
case_frame_rows = read_csv_rows(CASE_FRAME_PATH)


def cf_find(**kwargs) -> list:
    out = []
    for row in case_frame_rows:
        if all(row.get(k) == str(v) for k, v in kwargs.items()):
            out.append(row)
    return out


def cf_find_one(**kwargs) -> dict:
    rows = cf_find(**kwargs)
    assert len(rows) == 1, f"expected 1 row for {kwargs}, got {len(rows)}"
    return rows[0]


# ==========================================================================
# Section A: held-out factorial (campaign ho3_20260913)
# ==========================================================================
HO_CAMPAIGN = "ho3_20260913"
HO_CASES_DIR = R / "campaigns" / HO_CAMPAIGN / "cases"
HO_ARMS = {"NOM": "NOM", "TIGHT": "TIGHT", "HIST_ACT": "HIST+ACT", "HIST_ACT_T": "HIST+ACT-T"}
SEEDS = [11, 22, 33]

ho_case_json = {}  # (arm_token, seed) -> parsed json dict
ho_case_path = {}  # (arm_token, seed) -> Path

for arm_token, stored_arm in HO_ARMS.items():
    for seed in SEEDS:
        row = cf_find_one(campaign=HO_CAMPAIGN, arm=stored_arm, seed=seed)
        case_id = row["case_id"]
        p = HO_CASES_DIR / f"{case_id}.json"
        ho_case_json[(arm_token, seed)] = load_json_literal(p)
        ho_case_path[(arm_token, seed)] = p

# Per-(arm, seed) computed quantities
ho_mean_visits = {}       # (arm, seed) -> Fraction
ho_maxdev = {}             # (arm, seed) -> Fraction (share of 1, not yet *100)
ho_breach_worst = {}       # (arm, seed) -> Fraction (share, not yet *100)
ho_cap_count = {}
ho_floor_count = {}
ho_min_slack = {}          # (arm, seed) -> Fraction
ho_gap_str = {}
ho_bound_str = {}
ho_joint_pass = {}
ho_departures_above = {}
ho_departures_below = {}

incumbent_visits_set = set()
incumbent_maxdev_set = set()
incumbent_joint_pass_set = set()
incumbent_worst_excess_set = set()

for (arm_token, seed), data in ho_case_json.items():
    ev = data["evaluation"]
    stations = ev["stations"]
    mean_visits = F(ev["mean_visits_exact"])
    ho_mean_visits[(arm_token, seed)] = mean_visits

    maxdev = max(abs(F(s["share_exact"]) - F(s["target_exact"])) for s in stations)
    ho_maxdev[(arm_token, seed)] = maxdev

    cap_excess = []
    floor_excess = []
    cap_count = 0
    floor_count = 0
    dep_above = 0
    dep_below = 0
    for s in stations:
        share = F(s["share_exact"])
        cap = F(s["cap_exact"])
        floor = F(s["floor_exact"])
        if share > cap:
            cap_count += 1
            cap_excess.append(share - cap)
        else:
            cap_excess.append(F(0))
        if share < floor:
            floor_count += 1
            floor_excess.append(floor - share)
        else:
            floor_excess.append(F(0))
        if s.get("beyond_worst_scenario") is True:
            dep_above += 1
        if s.get("below_lowest_scenario") is True:
            dep_below += 1
    ho_cap_count[(arm_token, seed)] = cap_count
    ho_floor_count[(arm_token, seed)] = floor_count
    ho_breach_worst[(arm_token, seed)] = max(max(cap_excess), max(floor_excess))
    ho_departures_above[(arm_token, seed)] = dep_above
    ho_departures_below[(arm_token, seed)] = dep_below

    ho_min_slack[(arm_token, seed)] = F(ev["validation"]["minimum_required_slack_exact"])
    ho_gap_str[(arm_token, seed)] = data["solve_result"]["gap"]
    ho_bound_str[(arm_token, seed)] = data["solve_result"]["bound"]
    ho_joint_pass[(arm_token, seed)] = bool(ev["joint_pass"])

    ref = data["reference_evaluation"]
    incumbent_visits_set.add(F(ref["mean_visits_exact"]))
    ref_maxdev = max(abs(F(s["share_exact"]) - F(s["target_exact"])) for s in ref["stations"])
    incumbent_maxdev_set.add(ref_maxdev)
    incumbent_joint_pass_set.add(bool(ref["joint_pass"]))
    incumbent_worst_excess_set.add(F(ref["worst_excess_percentage_points_exact"]))

# ho.pass.<ARM>.count
for arm_token in HO_ARMS:
    n_pass = sum(1 for seed in SEEDS if ho_joint_pass[(arm_token, seed)])
    OUT[f"ho.pass.{arm_token}.count"] = count_entry(
        n_pass,
        [src(ho_case_path[(arm_token, s)], "evaluation.joint_pass") for s in SEEDS],
        "count of seeds (of 3) with evaluation.joint_pass == true",
    )

# ho.visits.<ARM>.<SEED> and .mean
for arm_token in HO_ARMS:
    exact_sum = F(0)
    for seed in SEEDS:
        mv = ho_mean_visits[(arm_token, seed)]
        exact_sum += mv
        OUT[f"ho.visits.{arm_token}.s{seed}"] = exact_entry(
            mv, "visits_per_order", 6,
            src(ho_case_path[(arm_token, seed)], "evaluation.mean_visits_exact"),
            "evaluation.mean_visits_exact, verbatim",
        )
    mean_fr = exact_sum / 3
    OUT[f"ho.visits.{arm_token}.mean"] = exact_entry(
        mean_fr, "visits_per_order", 6,
        [src(ho_case_path[(arm_token, s)], "evaluation.mean_visits_exact") for s in SEEDS],
        "mean of evaluation.mean_visits_exact over seeds 11/22/33",
    )

# ho.visits.incumbent
assert len(incumbent_visits_set) == 1, f"incumbent visits not identical: {incumbent_visits_set}"
incumbent_visits = next(iter(incumbent_visits_set))
OUT["ho.visits.incumbent"] = exact_entry(
    incumbent_visits, "visits_per_order", 6,
    [src(p, "reference_evaluation.mean_visits_exact") for p in ho_case_path.values()],
    "reference_evaluation.mean_visits_exact, identical across all 12 rows",
)

# ho.visits.HIST_ACT_T_over_TIGHT.pct
hist_act_t_mean = sum((ho_mean_visits[("HIST_ACT_T", s)] for s in SEEDS), F(0)) / 3
tight_mean = sum((ho_mean_visits[("TIGHT", s)] for s in SEEDS), F(0)) / 3
ratio_pct = (hist_act_t_mean / tight_mean - 1) * 100
OUT["ho.visits.HIST_ACT_T_over_TIGHT.pct"] = exact_entry(
    ratio_pct, "pct", 6,
    [src(ho_case_path[("HIST_ACT_T", s)], "evaluation.mean_visits_exact") for s in SEEDS]
    + [src(ho_case_path[("TIGHT", s)], "evaluation.mean_visits_exact") for s in SEEDS],
    "(mean HIST_ACT_T visits / mean TIGHT visits - 1) * 100, exact means",
)

# ho.saving.<ARM>.pct  and single-run min/max
all_single_savings = []  # (fraction_pct, arm, seed)
for arm_token in HO_ARMS:
    arm_mean = sum((ho_mean_visits[(arm_token, s)] for s in SEEDS), F(0)) / 3
    saving_pct = (incumbent_visits - arm_mean) / incumbent_visits * 100
    OUT[f"ho.saving.{arm_token}.pct"] = exact_entry(
        saving_pct, "pct", 6,
        [src(ho_case_path[(arm_token, s)], "evaluation.mean_visits_exact") for s in SEEDS]
        + [src(ho_case_path[(arm_token, SEEDS[0])], "reference_evaluation.mean_visits_exact")],
        "(incumbent mean visits - arm mean visits) / incumbent mean visits * 100",
    )
    for seed in SEEDS:
        single = (incumbent_visits - ho_mean_visits[(arm_token, seed)]) / incumbent_visits * 100
        all_single_savings.append((single, arm_token, seed))

min_single = min(all_single_savings, key=lambda t: t[0])
max_single = max(all_single_savings, key=lambda t: t[0])
OUT["ho.saving.single_run.min.pct"] = exact_entry(
    min_single[0], "pct", 6,
    [src(ho_case_path[(min_single[1], min_single[2])], "evaluation.mean_visits_exact & reference_evaluation.mean_visits_exact")],
    f"min over 12 rows of (incumbent - seed visits)/incumbent*100; row {min_single[1]}/s{min_single[2]}",
)
OUT["ho.saving.single_run.max.pct"] = exact_entry(
    max_single[0], "pct", 6,
    [src(ho_case_path[(max_single[1], max_single[2])], "evaluation.mean_visits_exact & reference_evaluation.mean_visits_exact")],
    f"max over 12 rows of (incumbent - seed visits)/incumbent*100; row {max_single[1]}/s{max_single[2]}",
)

# ho.maxdev.<ARM>.<SEED> and .max/.min
for arm_token in HO_ARMS:
    vals = []
    for seed in SEEDS:
        md = ho_maxdev[(arm_token, seed)] * 100
        vals.append(md)
        OUT[f"ho.maxdev.{arm_token}.s{seed}"] = exact_entry(
            md, "pp", 6,
            src(ho_case_path[(arm_token, seed)], "evaluation.stations[*].share_exact, target_exact"),
            "100 * max over 24 stations of |share_exact - target_exact|",
        )
    OUT[f"ho.maxdev.{arm_token}.max"] = exact_entry(
        max(vals), "pp", 6,
        [src(ho_case_path[(arm_token, s)], "evaluation.stations[*].share_exact, target_exact") for s in SEEDS],
        "max over the 3 seeds of ho.maxdev.<ARM>.<SEED>",
    )
    OUT[f"ho.maxdev.{arm_token}.min"] = exact_entry(
        min(vals), "pp", 6,
        [src(ho_case_path[(arm_token, s)], "evaluation.stations[*].share_exact, target_exact") for s in SEEDS],
        "min over the 3 seeds of ho.maxdev.<ARM>.<SEED>",
    )

# ho.maxdev.incumbent
assert len(incumbent_maxdev_set) == 1, f"incumbent maxdev not identical: {incumbent_maxdev_set}"
incumbent_maxdev = next(iter(incumbent_maxdev_set)) * 100
OUT["ho.maxdev.incumbent"] = exact_entry(
    incumbent_maxdev, "pp", 6,
    [src(p, "reference_evaluation.stations[*].share_exact, target_exact") for p in ho_case_path.values()],
    "100 * max over 24 stations of |share_exact - target_exact|, reference_evaluation, identical across all 12 rows",
)

# ho.breach.<ARM>.<SEED>.worst / .cap_count / .floor_count
for arm_token in HO_ARMS:
    for seed in SEEDS:
        worst_pp = ho_breach_worst[(arm_token, seed)] * 100
        OUT[f"ho.breach.{arm_token}.s{seed}.worst"] = exact_entry(
            worst_pp, "pp", 6,
            src(ho_case_path[(arm_token, seed)], "evaluation.stations[*].share_exact, cap_exact, floor_exact"),
            "100 * max(max(share-cap,0), max(floor-share,0)) over 24 stations; 0 if no station breaches",
        )
        OUT[f"ho.breach.{arm_token}.s{seed}.cap_count"] = count_entry(
            ho_cap_count[(arm_token, seed)],
            src(ho_case_path[(arm_token, seed)], "evaluation.stations[*].share_exact > cap_exact"),
            "count of stations with share_exact > cap_exact",
        )
        OUT[f"ho.breach.{arm_token}.s{seed}.floor_count"] = count_entry(
            ho_floor_count[(arm_token, seed)],
            src(ho_case_path[(arm_token, seed)], "evaluation.stations[*].share_exact < floor_exact"),
            "count of stations with share_exact < floor_exact",
        )

# ho.min_slack.<ARM>.<SEED>
for arm_token in HO_ARMS:
    for seed in SEEDS:
        OUT[f"ho.min_slack.{arm_token}.s{seed}"] = exact_entry(
            ho_min_slack[(arm_token, seed)], "share", 6,
            src(ho_case_path[(arm_token, seed)], "evaluation.validation.minimum_required_slack_exact"),
            "evaluation.validation.minimum_required_slack_exact, verbatim",
        )

# ho.gap.<ARM>.<SEED> / ho.bound.<ARM>.<SEED>  (as stored, no exact field)
for arm_token in HO_ARMS:
    for seed in SEEDS:
        gap_s = ho_gap_str[(arm_token, seed)]
        OUT[f"ho.gap.{arm_token}.s{seed}"] = entry(
            gap_s, float(gap_s), "fraction", 6,
            src(ho_case_path[(arm_token, seed)], "solve_result.gap"),
            "solve_result.gap, decimal string exactly as stored",
        )
        bound_s = ho_bound_str[(arm_token, seed)]
        OUT[f"ho.bound.{arm_token}.s{seed}"] = entry(
            bound_s, float(bound_s), "visits", None,
            src(ho_case_path[(arm_token, seed)], "solve_result.bound"),
            "solve_result.bound, exactly as stored",
        )

# ho.incumbent.joint_pass / ho.incumbent.worst_excess
assert len(incumbent_joint_pass_set) == 1
OUT["ho.incumbent.joint_pass"] = bool_entry(
    next(iter(incumbent_joint_pass_set)),
    [src(p, "reference_evaluation.joint_pass") for p in ho_case_path.values()],
    "reference_evaluation.joint_pass, identical across all 12 rows",
)
assert len(incumbent_worst_excess_set) == 1
incumbent_worst_excess_pp = next(iter(incumbent_worst_excess_set)) * 100
OUT["ho.incumbent.worst_excess"] = exact_entry(
    incumbent_worst_excess_pp, "pp", 6,
    [src(p, "reference_evaluation.worst_excess_percentage_points_exact") for p in ho_case_path.values()],
    "100 * reference_evaluation.worst_excess_percentage_points_exact, identical across all 12 rows",
)

# ho.departures.<ARM>.<SEED>.above / .below
for arm_token in HO_ARMS:
    for seed in SEEDS:
        OUT[f"ho.departures.{arm_token}.s{seed}.above"] = count_entry(
            ho_departures_above[(arm_token, seed)],
            src(ho_case_path[(arm_token, seed)], "evaluation.stations[*].beyond_worst_scenario"),
            "count of stations with beyond_worst_scenario == true",
        )
        OUT[f"ho.departures.{arm_token}.s{seed}.below"] = count_entry(
            ho_departures_below[(arm_token, seed)],
            src(ho_case_path[(arm_token, seed)], "evaluation.stations[*].below_lowest_scenario"),
            "count of stations with below_lowest_scenario == true",
        )

# ==========================================================================
# Section B: drift and dispersion
# ==========================================================================
DRIFT_PATH = R / "tables" / "drift_survey.csv"
drift_rows = read_csv_rows(DRIFT_PATH)
drift_row = next(r for r in drift_rows if r["dataset_id"] == "BERNER@holdout")

drift_field_map = {
    "hist_tv_max": "historical_tv_max",
    "hist_tv_mean": "historical_tv_mean",
    "hist_tv_p90": "historical_tv_p90",
    "hist_tv_last": "historical_tv_last",
    "future_tv": "future_tv_ex_post",
}
for out_key, col in drift_field_map.items():
    val = drift_row[col]
    OUT[f"drift.holdout.{out_key}"] = entry(
        val, float(val), "tv", 6,
        src(DRIFT_PATH, f"row dataset_id=='BERNER@holdout', column {col}"),
        f"{col}, decimal string exactly as stored",
    )
for out_key, col in [("blocks", "historical_blocks"), ("n", "n"), ("origin", "origin")]:
    val = drift_row[col]
    OUT[f"drift.holdout.{out_key}"] = count_entry(
        int(val),
        src(DRIFT_PATH, f"row dataset_id=='BERNER@holdout', column {col}"),
        f"{col}, integer as stored",
    )

hist_tv_max_fr = dec_frac(drift_row["historical_tv_max"])
hist_tv_mean_fr = dec_frac(drift_row["historical_tv_mean"])
future_tv_fr = dec_frac(drift_row["future_tv_ex_post"])
n_fr = F(int(drift_row["n"]))
origin_fr = F(int(drift_row["origin"]))

w_star = 1 - hist_tv_max_fr / future_tv_fr
OUT["drift.holdout.w_star"] = exact_entry(
    w_star, "fraction", 6,
    src(DRIFT_PATH, "row BERNER@holdout, historical_tv_max & future_tv_ex_post"),
    "1 - historical_tv_max/future_tv_ex_post, exact rationals from stored decimals",
)

w_order_count = n_fr / origin_fr
OUT["drift.holdout.w_order_count"] = exact_entry(
    w_order_count, "fraction", 6,
    src(DRIFT_PATH, "row BERNER@holdout, n & origin"),
    "n/origin, exact",
)

hist_tv_max_lfl = hist_tv_max_fr / (1 - w_order_count)
OUT["drift.holdout.hist_tv_max.like_for_like"] = exact_entry(
    hist_tv_max_lfl, "tv", 6,
    src(DRIFT_PATH, "row BERNER@holdout, historical_tv_max, n, origin"),
    "historical_tv_max / (1 - n/origin), exact",
)

for suffix, w in [("w_0_05", dec_frac("0.05")), ("w_0_10", dec_frac("0.10")), ("w_one_eleventh", F(1, 11))]:
    val = hist_tv_max_fr / (1 - w)
    OUT[f"drift.holdout.hist_tv_max.like_for_like.{suffix}"] = exact_entry(
        val, "tv", 6,
        src(DRIFT_PATH, "row BERNER@holdout, historical_tv_max"),
        f"historical_tv_max / (1 - {suffix.replace('w_', '').replace('_', '.')}), exact",
    )

DISPERSION_PATH = R / "tables" / "dispersion_survey.csv"
disp_rows = read_csv_rows(DISPERSION_PATH)
disp_berner = [r for r in disp_rows if r["dataset_id"] == "BERNER" and r["origin"] == "199403"]
disp_by_n = {int(r["n"]): r for r in disp_berner}
assert set(disp_by_n) == {10937, 21874, 43748}, disp_by_n.keys()
disp_h_map = {"n_half": 10937, "n_P": 21874, "n_2P": 43748}

for h_label, n_val in disp_h_map.items():
    row = disp_by_n[n_val]
    val = row["max_abs_pp"]
    OUT[f"disp.explor.{h_label}.max_abs"] = entry(
        val, float(val), "pp", None,
        src(DISPERSION_PATH, f"row dataset_id==BERNER, origin==199403, n=={n_val}, column max_abs_pp"),
        "max_abs_pp, decimal string exactly as stored",
    )
    max_abs_fr = dec_frac(val)
    w = F(n_val, 199403)
    lfl = max_abs_fr / (1 - w)
    OUT[f"disp.explor.{h_label}.max_abs.like_for_like"] = exact_entry(
        lfl, "pp", 6,
        src(DISPERSION_PATH, f"row dataset_id==BERNER, origin==199403, n=={n_val}, column max_abs_pp"),
        f"max_abs_pp / (1 - {n_val}/199403), exact",
    )

# ==========================================================================
# Section C: upper-only vs two-sided reconciliation
# ==========================================================================
C_ARMS = {"NOM": "NOM", "TIGHT": "TIGHT", "HIST": "HIST", "HIST_ACT": "HIST+ACT"}
N_HORIZONS = [10937, 21874, 43748]


def campaign_case_path(campaign: str, case_id: str) -> Path:
    return R / "campaigns" / campaign / "cases" / f"{case_id}.json"


def pass_counts_for(campaign: str) -> dict:
    out_local = {}
    for arm_token, stored_arm in C_ARMS.items():
        rows = cf_find(campaign=campaign, dataset_id="BERNER", arm=stored_arm)
        assert len(rows) == 3, f"{campaign}/{stored_arm}: expected 3 BERNER horizons, got {len(rows)}"
        n_pass = sum(1 for r in rows if r["joint_pass"] == "True")
        out_local[arm_token] = (n_pass, rows)
    return out_local


uo_pass = pass_counts_for("screen_20260910")
for arm_token, (n_pass, rows) in uo_pass.items():
    OUT[f"uo.berner.pass.{arm_token}.count"] = count_entry(
        n_pass,
        [src(CASE_FRAME_PATH, f"campaign=screen_20260910, dataset_id=BERNER, arm={C_ARMS[arm_token]}, column joint_pass")],
        "count of horizons (of 3) with joint_pass == True, screen_20260910 (upper_only, delta=0.01)",
    )

for n_val in N_HORIZONS:
    row = cf_find_one(campaign="screen_20260910", dataset_id="BERNER", arm="TIGHT", n=n_val)
    case_json = load_json_literal(campaign_case_path("screen_20260910", row["case_id"]))
    slack_fr = F(case_json["evaluation"]["validation"]["minimum_required_slack_exact"])
    OUT[f"uo.berner.min_slack.TIGHT.{n_val}"] = exact_entry(
        slack_fr, "share", 6,
        src(campaign_case_path("screen_20260910", row["case_id"]), "evaluation.validation.minimum_required_slack_exact"),
        f"TIGHT minimum_required_slack at BERNER n={n_val}, screen_20260910, upper_only, delta=0.01",
    )

ts_campaigns = {"d01": "ts_b01_20260912", "d02": "ts_d02_20260912", "d03": "ts_b03_20260912"}
for delta_tag, campaign in ts_campaigns.items():
    pc = pass_counts_for(campaign)
    for arm_token, (n_pass, rows) in pc.items():
        OUT[f"ts.berner.{delta_tag}.pass.{arm_token}.count"] = count_entry(
            n_pass,
            [src(CASE_FRAME_PATH, f"campaign={campaign}, dataset_id=BERNER, arm={C_ARMS[arm_token]}, column joint_pass")],
            f"count of horizons (of 3) with joint_pass == True, {campaign} (two_sided)",
        )

for n_val in N_HORIZONS:
    row = cf_find_one(campaign="ts_d02_20260912", dataset_id="BERNER", arm="TIGHT", n=n_val)
    case_json = load_json_literal(campaign_case_path("ts_d02_20260912", row["case_id"]))
    slack_fr = F(case_json["evaluation"]["validation"]["minimum_required_slack_exact"])
    OUT[f"ts.berner.d02.min_slack.TIGHT.{n_val}"] = exact_entry(
        slack_fr, "share", 6,
        src(campaign_case_path("ts_d02_20260912", row["case_id"]), "evaluation.validation.minimum_required_slack_exact"),
        f"TIGHT minimum_required_slack at BERNER n={n_val}, ts_d02_20260912, two_sided, delta=0.02",
    )

for arm_out, arm_stored in [("HIST_ACT", "HIST+ACT"), ("HIST", "HIST")]:
    cap_total = 0
    floor_total = 0
    for n_val in N_HORIZONS:
        row = cf_find_one(campaign="ts_d02_20260912", dataset_id="BERNER", arm=arm_stored, n=n_val)
        cap_total += int(float(row["cap_violation_count"]))
        floor_total += int(float(row["floor_violation_count"]))
    OUT[f"ts.berner.d02.{arm_out}.cap_breaches_total"] = count_entry(
        cap_total,
        [src(CASE_FRAME_PATH, f"campaign=ts_d02_20260912, dataset_id=BERNER, arm={arm_stored}, column cap_violation_count")],
        "sum of cap_violation_count over the 3 BERNER horizons, ts_d02_20260912",
    )
    OUT[f"ts.berner.d02.{arm_out}.floor_breaches_total"] = count_entry(
        floor_total,
        [src(CASE_FRAME_PATH, f"campaign=ts_d02_20260912, dataset_id=BERNER, arm={arm_stored}, column floor_violation_count")],
        "sum of floor_violation_count over the 3 BERNER horizons, ts_d02_20260912",
    )

synth_datasets = set()
for campaign in ts_campaigns.values():
    for row in case_frame_rows:
        if row["campaign"] == campaign and row["dataset_id"] != "BERNER":
            synth_datasets.add(row["dataset_id"])
OUT["ts.synthetic_instances.count"] = count_entry(
    len(synth_datasets),
    [src(CASE_FRAME_PATH, "campaign in {ts_b01_20260912,ts_d02_20260912,ts_b03_20260912}, distinct dataset_id != BERNER")],
    f"count of distinct synthetic dataset_id run two-sided: {sorted(synth_datasets)}",
)

# ==========================================================================
# Section D: accounting and context
# ==========================================================================
AUDIT_PATH = R / "analysis_audit.md"
audit_text = AUDIT_PATH.read_text(encoding="utf-8")

m = re.search(r"## Campaigns included\n(.*?)\n\n", audit_text, re.S)
included_block = m.group(1)
analysed = re.findall(r"^\|\s*`([^`]+)`", included_block, re.M)
assert len(analysed) == 6, analysed

m2 = re.search(r"Excluded as superseded[^:]*:\s*(.+)", audit_text)
superseded = re.findall(r"`([^`]+)`", m2.group(1))
assert len(superseded) == 4, superseded

cf_campaigns = sorted({r["campaign"] for r in case_frame_rows})
assert set(analysed) == set(cf_campaigns), (set(analysed), set(cf_campaigns))

OUT["acct.campaigns.analysed"] = entry(
    json.dumps(analysed), None, "list in value_exact as JSON string", None,
    src(AUDIT_PATH, '"## Campaigns included" table, backticked campaign column (lines 13-20)') +
    src(CASE_FRAME_PATH, "distinct campaign values (cross-check)"),
    "campaign names from the 6 data rows of the Campaigns included table, cross-checked against case_frame.csv campaign values",
)
OUT["acct.campaigns.superseded"] = entry(
    json.dumps(superseded), None, "list", None,
    src(AUDIT_PATH, '"Excluded as superseded" line (line 22), backticked names'),
    "the 4 backticked names on the Excluded as superseded line",
)

n_authorized = len(case_frame_rows)
n_scored = sum(1 for r in case_frame_rows if r["scored"] == "True")
n_no_allocation = sum(1 for r in case_frame_rows if r["scored"] == "False")
assert n_authorized == n_scored + n_no_allocation
OUT["acct.rows.authorized"] = count_entry(
    n_authorized, src(CASE_FRAME_PATH, "row count"), "len(case_frame.csv), the 6 analysed campaigns"
)
OUT["acct.rows.scored"] = count_entry(
    n_scored, src(CASE_FRAME_PATH, "column scored == True"), "count of case_frame.csv rows with scored == True"
)
OUT["acct.rows.no_allocation"] = count_entry(
    n_no_allocation, src(CASE_FRAME_PATH, "column scored == False"),
    "count of case_frame.csv rows with scored == False (status NO_INCUMBENT_LIMIT or NUMERICAL_ISSUE)",
)

scored_layout_hashes = {r["layout_hash"] for r in case_frame_rows if r["scored"] == "True" and r["layout_hash"]}
OUT["acct.layouts.scored"] = count_entry(
    len(scored_layout_hashes),
    src(CASE_FRAME_PATH, "column layout_hash, rows with scored == True"),
    "count of distinct layout_hash values among scored==True rows across the 6 analysed campaigns "
    "(definition inferred; ANCHOR_SPEC gives no field-level definition for Q-009, see NOTES)",
)

STATION_PROFILE_PATH = R / "tables" / "station_profile_industrial.csv"
station_rows = read_csv_rows(STATION_PROFILE_PATH)
ho_station_rows = [r for r in station_rows if r["campaign"] == HO_CAMPAIGN]
index_to_station = {}
join_exact = True
for r in ho_station_rows:
    idx = int(r["station_index"])
    name = r["station"]
    if idx in index_to_station and index_to_station[idx] != name:
        join_exact = False
    index_to_station[idx] = name
station_to_index = {}
for idx, name in index_to_station.items():
    if name in station_to_index and station_to_index[name] != idx:
        join_exact = False
    station_to_index[name] = idx

# cross-check against the station_index set used in the held-out case records'
# reference evaluation (should be exactly 0..23 for every one of the 12 rows)
ref_index_sets = set()
for data in ho_case_json.values():
    idxs = frozenset(int(s["station_index"]) for s in data["reference_evaluation"]["stations"])
    ref_index_sets.add(idxs)
if len(ref_index_sets) != 1 or set(index_to_station) != next(iter(ref_index_sets)):
    join_exact = False

OUT["alias.join_exact"] = bool_entry(
    join_exact,
    src(STATION_PROFILE_PATH, "campaign==ho3_20260913, columns station_index, station") +
    [src(p, "reference_evaluation.stations[*].station_index") for p in ho_case_path.values()],
    "station_index -> station is one-to-one in station_profile_industrial.csv (campaign ho3_20260913) "
    "and its key set matches the station_index set used in every reference_evaluation of the held-out cases",
)
OUT["alias.map"] = entry(
    json.dumps({str(k): v for k, v in sorted(index_to_station.items())}), None, "JSON string", None,
    src(STATION_PROFILE_PATH, "campaign==ho3_20260913, columns station_index, station"),
    "{station_index: station} built from station_profile_industrial.csv, campaign ho3_20260913",
)

# ho.incumbent.training_slack (Q-005): fields inspected, none give a training-scenario slack
inspected_fields = [
    "case", "evaluation (incl. validation)", "reference_evaluation (incl. validation)",
    "policy_validation", "solve_result", "native_attempt", "top-level validation",
]
OUT["ho.incumbent.training_slack"] = "UNAVAILABLE: no stored field gives the incumbent's " \
    "minimum_required_slack on its training scenarios. reference_evaluation.validation." \
    "minimum_required_slack_exact is computed against the held-out future horizon (ex post), " \
    "not the incumbent's training scenarios; the incumbent is a fixed baseline, never solved " \
    "in-campaign, so it carries no separate training-scenario evaluation block. Fields inspected " \
    "in cases/<case_id>.json: " + ", ".join(inspected_fields)

# ==========================================================================
print(json.dumps(OUT, indent=None, sort_keys=True))
