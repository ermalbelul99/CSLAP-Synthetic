#!/usr/bin/env python3
# P1 anchors, builder A (blind double reproduction). Read-only: reads only ANCHOR_SPEC allowed inputs,
# writes nothing, imports no repository module. stdout: one JSON object {key: entry}.
# stderr: section E displayed-precision cross-check and verification warnings.
import hashlib
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP, localcontext
from fractions import Fraction as F

import pandas as pd

REPO = r"C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic"
R = "reports/horizon_robustness_results"
HO = "ho3_20260913"
SEEDS = (11, 22, 33)
HO_ARMS = (("NOM", "NOM"), ("TIGHT", "TIGHT"), ("HIST_ACT", "HIST+ACT"), ("HIST_ACT_T", "HIST+ACT-T"))
TS_ARMS = (("NOM", "NOM"), ("TIGHT", "TIGHT"), ("HIST", "HIST"), ("HIST_ACT", "HIST+ACT"))
HORIZONS = (10937, 21874, 43748)
BIG = {"assignment", "product_ids", "product_line_counts", "slot_assignment", "audit"}
CF_REL = f"{R}/tables/case_frame.csv"


def ap(rel):
    return os.path.join(REPO, *rel.split("/"))


_SHA = {}


def sha(rel):
    if rel not in _SHA:
        h = hashlib.sha256()
        with open(ap(rel), "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        _SHA[rel] = h.hexdigest()
    return _SHA[rel]


def src(rel, selector):
    return {"path": rel, "sha256": sha(rel), "selector": selector}


OUT, WARN = {}, []


def put(key, value_exact, value_float, unit, rounding, sources, computation):
    assert key not in OUT, key
    OUT[key] = {"value_exact": value_exact, "value_float": value_float, "unit": unit,
                "display_rounding": rounding, "sources": sources, "computation": computation}


def putq(key, q, unit, rounding, sources, computation):
    q = F(q)
    put(key, str(q), float(q), unit, rounding, sources, computation)


def check(cond, msg):
    if not cond:
        WARN.append(msg)
    return bool(cond)


def strip(o):
    if isinstance(o, dict):
        return {k: strip(v) for k, v in o.items() if k not in BIG}
    if isinstance(o, list):
        return [strip(v) for v in o]
    return o


def load_json(rel):
    with open(ap(rel), encoding="utf-8") as fh:
        return strip(json.load(fh, parse_float=str))  # stored decimal text kept verbatim


def read_csv(rel):
    return pd.read_csv(ap(rel), dtype=str, keep_default_na=False)


def fclose(a, b, tol=F(1, 10 ** 12)):
    return abs(F(a) - F(b)) <= tol


def station_stats(ev, where):
    st = ev["stations"]
    check(len(st) == 24 and [s["station_index"] for s in st] == list(range(24)), f"{where}: station order")
    sh = [F(s["share_exact"]) for s in st]
    tg = [F(s["target_exact"]) for s in st]
    cp = [F(s["cap_exact"]) for s in st]
    fl = [F(s["floor_exact"]) for s in st]
    hi = [F(s["worst_share_exact"]) for s in st]
    has_lo = all("lowest_share_exact" in s for s in st)  # absent in older (5e1ee22f) records
    lo = [F(s["lowest_share_exact"]) for s in st] if has_lo else None
    for i in range(len(st)):
        check(F(ev["station_shares_exact"][i]) == sh[i] and F(ev["targets_exact"][i]) == tg[i]
              and F(ev["caps_exact"][i]) == cp[i] and F(ev["floors_exact"][i]) == fl[i]
              and F(ev["worst_scenario_envelope_exact"][i]) == hi[i]
              and (not has_lo or F(ev["lowest_scenario_envelope_exact"][i]) == lo[i]), f"{where}: vector mismatch {i}")
        check(F(st[i]["line_count"], ev["total_lines"]) == sh[i], f"{where}: share != line_count/total_lines {i}")
    return {
        "maxdev_pp": max(abs(a - b) for a, b in zip(sh, tg)) * 100,
        "cap_n": sum(a > c for a, c in zip(sh, cp)),
        "floor_n": sum(a < f for a, f in zip(sh, fl)),
        "worst_pp": max([F(0)] + [a - c for a, c in zip(sh, cp)] + [f - a for a, f in zip(sh, fl)]) * 100,
        "above_n": sum(a > h for a, h in zip(sh, hi)),
        "below_n": sum(a < l for a, l in zip(sh, lo)) if has_lo else None,
        "above_flag": sum(bool(s["beyond_worst_scenario"]) for s in st),
        "below_flag": sum(bool(s["below_lowest_scenario"]) for s in st) if has_lo else None,
        "ids": [(s["station_index"], s["station_id"]) for s in st],
        "target": {s["station_index"]: s["target"] for s in st},
        "share": {s["station_index"]: s["share"] for s in st},
    }


cf = read_csv(CF_REL)


def cf_row(case_id):
    sub = cf[cf.case_id == case_id]
    assert len(sub) == 1, case_id
    return sub.iloc[0]


# ------------------------------------------------------------------ A. held-out factorial
man = load_json(f"{R}/campaigns/{HO}/manifest.json")
cfg = man["config"]
assert cfg["stage"] == "holdout" and cfg["datasets"] == ["BERNER"] and cfg["rule"] == "two_sided"
assert (cfg["delta"], cfg["nu"], cfg["tightening"], cfg["horizons"]) == ("0.02", "0.01", "0.5", [21874])
assert len(man["rows"]) == 12
HOREC = {}
for row in man["rows"]:
    rel = f"{R}/campaigns/{HO}/{row['expected_result']}"
    d = load_json(rel)
    c = d["case"]
    assert (c["case_id"], c["arm"], c["seed"], c["dataset_id"], c["origin"], c["n"], c["rule"], c["delta"],
            c["nu"], c["tightening"], c["stage"]) == (row["case_id"], row["arm"], row["seed"], "BERNER", 243151,
                                                     21874, "two_sided", "0.02", "0.01", "0.5", "holdout")
    assert d["status"] == "COMPLETE"
    k = (row["arm"], row["seed"])
    assert k not in HOREC
    HOREC[k] = {"rel": rel, "d": d, "es": station_stats(d["evaluation"], f"{rel}:evaluation"),
                "rs": station_stats(d["reference_evaluation"], f"{rel}:reference_evaluation")}
assert set(HOREC) == {(a, s) for _, a in HO_ARMS for s in SEEDS}


def msel(arm, s, field):
    return f"case.arm={arm},case.seed={s}: {field}"


def ho_srcs(arms, field):
    return [src(HOREC[(a, s)]["rel"], msel(a, s, field)) for a in arms for s in SEEDS]


visits, maxdev = {}, {}
for tok, arm in HO_ARMS:
    passes = 0
    for s in SEEDS:
        rec = HOREC[(arm, s)]
        rel, d, es = rec["rel"], rec["d"], rec["es"]
        ev = d["evaluation"]
        cfr = cf_row(d["case"]["case_id"])
        sk = f"s{s}"
        one = lambda field: [src(rel, msel(arm, s, field))]
        v = F(ev["mean_visits_exact"])
        check(v == F(ev["visit_count"], ev["order_count"]) and ev["order_count"] == 21874, f"{rel}: mean visits")
        check(cfr.mean_visits_exact == ev["mean_visits_exact"], f"{rel}: case_frame mean_visits_exact")
        visits[(tok, s)] = v
        putq(f"ho.visits.{tok}.{sk}", v, "visits_per_order", 6, one("evaluation.mean_visits_exact"),
             f"stored exact = visit_count/order_count = {ev['visit_count']}/{ev['order_count']}; = case_frame mean_visits_exact")
        maxdev[(tok, s)] = es["maxdev_pp"]
        putq(f"ho.maxdev.{tok}.{sk}", es["maxdev_pp"], "pp", 6, one("evaluation.stations[0..23].share_exact,target_exact"),
             "max_i |share_exact - target_exact| * 100, exact")
        we = F(ev["worst_excess_percentage_points_exact"])
        check(we == es["worst_pp"], f"{rel}: worst excess recount")
        check((ev["joint_pass"] is True) == (we == 0), f"{rel}: pass vs worst")
        putq(f"ho.breach.{tok}.{sk}.worst", we, "pp", 6, one("evaluation.worst_excess_percentage_points_exact"),
             "stored exact; = max(0, max_i(share-cap), max_i(floor-share)) * 100 recomputed from stations")
        capn, floorn = ev["cap_violation_count"], ev["floor_violation_count"]
        check(capn == es["cap_n"] and floorn == es["floor_n"], f"{rel}: cap/floor recount")
        check(str(capn) == cfr.cap_violation_count and str(floorn) == cfr.floor_violation_count, f"{rel}: case_frame counts")
        check(ev["violation_count"] == capn + floorn, f"{rel}: violation_count")
        putq(f"ho.breach.{tok}.{sk}.cap_count", capn, "count", None, one("evaluation.cap_violation_count"),
             "stored; = exact recount share_exact > cap_exact; = case_frame")
        putq(f"ho.breach.{tok}.{sk}.floor_count", floorn, "count", None, one("evaluation.floor_violation_count"),
             "stored; = exact recount share_exact < floor_exact; = case_frame")
        ms = F(d["validation"]["minimum_required_slack_exact"])
        check(ms == F(d["policy_validation"]["minimum_required_slack_exact"]), f"{rel}: slack validation vs policy")
        check(fclose(ms, cfr.minimum_required_slack), f"{rel}: case_frame slack")
        putq(f"ho.min_slack.{tok}.{sk}", ms, "share", 6, one("validation.minimum_required_slack_exact"),
             "stored exact; = policy_validation field; = case_frame float")
        g, b = d["solve_result"]["gap"], d["solve_result"]["bound"]
        check(g == d["native_attempt"]["solve_result"]["gap"] and b == d["native_attempt"]["solve_result"]["bound"], f"{rel}: native gap/bound")
        check(float(g) == float(cfr.gap) and F(b) == F(cfr.bound), f"{rel}: case_frame gap/bound")
        put(f"ho.gap.{tok}.{sk}", str(g), float(g), "fraction", 6, one("solve_result.gap"),
            "as stored; = native_attempt.solve_result.gap; = case_frame")
        put(f"ho.bound.{tok}.{sk}", str(b), float(F(b)), "visits", None, one("solve_result.bound"),
            "as stored; = native_attempt.solve_result.bound; = case_frame")
        check(es["above_flag"] == es["above_n"] and es["below_flag"] == es["below_n"], f"{rel}: departure flags")
        check(ev["station_novelty_count"] == es["above_flag"] and ev["station_novelty_count_lower"] == es["below_flag"], f"{rel}: novelty counts")
        putq(f"ho.departures.{tok}.{sk}.above", es["above_flag"], "count", None, one("count(evaluation.stations[*].beyond_worst_scenario)"),
             "flag count; = exact recount share_exact > worst_share_exact; = station_novelty_count")
        putq(f"ho.departures.{tok}.{sk}.below", es["below_flag"], "count", None, one("count(evaluation.stations[*].below_lowest_scenario)"),
             "flag count; = exact recount share_exact < lowest_share_exact; = station_novelty_count_lower")
        passes += ev["joint_pass"] is True
        check((ev["joint_pass"] is True) == (cfr.joint_pass == "True"), f"{rel}: case_frame joint_pass")
    putq(f"ho.pass.{tok}.count", passes, "count", None, ho_srcs([arm], "evaluation.joint_pass"),
         "seeds (of 3) with joint_pass true; each = (cap+floor violations == 0) and = case_frame")
    putq(f"ho.visits.{tok}.mean", sum(visits[(tok, s)] for s in SEEDS) / 3, "visits_per_order", 6,
         ho_srcs([arm], "evaluation.mean_visits_exact"), "(s11 + s22 + s33) / 3, exact")
    ms_ = ho_srcs([arm], "evaluation.stations[0..23].share_exact,target_exact")
    putq(f"ho.maxdev.{tok}.max", max(maxdev[(tok, s)] for s in SEEDS), "pp", 6, ms_, "max over seeds, exact")
    putq(f"ho.maxdev.{tok}.min", min(maxdev[(tok, s)] for s in SEEDS), "pp", 6, ms_, "min over seeds, exact")

ALL_ARMS = [a for _, a in HO_ARMS]
ref_means = {F(HOREC[k]["d"]["reference_evaluation"]["mean_visits_exact"]) for k in HOREC}
ref_layouts = {HOREC[k]["d"]["reference_evaluation"]["layout_hash"] for k in HOREC}
futures = {HOREC[k]["d"][e]["future_hash"] for k in HOREC for e in ("evaluation", "reference_evaluation")}
assert len(ref_means) == 1 and len(ref_layouts) == 1 and len(futures) == 1
inc = next(iter(ref_means))
for k in HOREC:
    check(float(inc) == float(cf_row(HOREC[k]["d"]["case"]["case_id"]).reference_mean_visits), f"{k}: case_frame reference_mean_visits")
putq("ho.visits.incumbent", inc, "visits_per_order", 6, ho_srcs(ALL_ARMS, "reference_evaluation.mean_visits_exact"),
     "stored exact; identical in all 12 rows, one reference layout_hash, one future_hash")
for tok, arm in HO_ARMS:
    mean = F(OUT[f"ho.visits.{tok}.mean"]["value_exact"])
    putq(f"ho.saving.{tok}.pct", (inc - mean) / inc * 100, "pct", 6,
         ho_srcs([arm], "evaluation.mean_visits_exact; reference_evaluation.mean_visits_exact"),
         "(incumbent - arm mean) / incumbent * 100, exact")
tm, hm = F(OUT["ho.visits.TIGHT.mean"]["value_exact"]), F(OUT["ho.visits.HIST_ACT_T.mean"]["value_exact"])
putq("ho.visits.HIST_ACT_T_over_TIGHT.pct", (hm / tm - 1) * 100, "pct", 6,
     ho_srcs(["TIGHT", "HIST+ACT-T"], "evaluation.mean_visits_exact"), f"({hm} / {tm} - 1) * 100, exact")
single = [(inc - visits[(tok, s)]) / inc * 100 for tok, _ in HO_ARMS for s in SEEDS]
sr = ho_srcs(ALL_ARMS, "evaluation.mean_visits_exact; reference_evaluation.mean_visits_exact")
putq("ho.saving.single_run.min.pct", min(single), "pct", 6, sr, "min over 12 rows of (incumbent - seed visits) / incumbent * 100")
putq("ho.saving.single_run.max.pct", max(single), "pct", 6, sr, "max over 12 rows of (incumbent - seed visits) / incumbent * 100")
inc_md = {HOREC[k]["rs"]["maxdev_pp"] for k in HOREC}
assert len(inc_md) == 1
putq("ho.maxdev.incumbent", next(iter(inc_md)), "pp", 6, ho_srcs(ALL_ARMS, "reference_evaluation.stations[0..23].share_exact,target_exact"),
     "max_i |share_exact - target_exact| * 100, exact; identical in all 12 rows")
inc_jp = {HOREC[k]["d"]["reference_evaluation"]["joint_pass"] for k in HOREC}
assert len(inc_jp) == 1
jp = next(iter(inc_jp)) is True
put("ho.incumbent.joint_pass", "1" if jp else "0", 1.0 if jp else 0.0, "bool", None,
    ho_srcs(ALL_ARMS, "reference_evaluation.joint_pass"), "stored; identical in all 12 rows")
inc_we = {F(HOREC[k]["d"]["reference_evaluation"]["worst_excess_percentage_points_exact"]) for k in HOREC}
assert len(inc_we) == 1
wev = next(iter(inc_we))
check(all(HOREC[k]["rs"]["worst_pp"] == wev for k in HOREC), "incumbent worst excess recount")
putq("ho.incumbent.worst_excess", wev, "pp", 6, ho_srcs(ALL_ARMS, "reference_evaluation.worst_excess_percentage_points_exact"),
     "stored exact; identical in all 12 rows; = station recount")

# ------------------------------------------------------------------ B. drift and dispersion
DRIFT = f"{R}/tables/drift_survey.csv"
dr = read_csv(DRIFT)
row = dr[dr.dataset_id == "BERNER@holdout"]
assert len(row) == 1
row = row.iloc[0]
assert row.origin == "243151" and row.n == "21874"
dsrc = lambda cols: [src(DRIFT, f"dataset_id=BERNER@holdout: {cols}")]
for key, col, unit, rnd in (("hist_tv_max", "historical_tv_max", "tv", 6), ("hist_tv_mean", "historical_tv_mean", "tv", 6),
                            ("hist_tv_p90", "historical_tv_p90", "tv", 6), ("hist_tv_last", "historical_tv_last", "tv", 6),
                            ("future_tv", "future_tv_ex_post", "tv", 6), ("blocks", "historical_blocks", "count", None),
                            ("n", "n", "count", None), ("origin", "origin", "count", None)):
    put(f"drift.holdout.{key}", row[col], float(F(row[col])), unit, rnd, dsrc(col), "stored decimal string")
tvmax, ftv = F(row.historical_tv_max), F(row.future_tv_ex_post)
w = F(int(row.n), int(row.origin))
putq("drift.holdout.w_star", 1 - tvmax / ftv, "fraction", 6, dsrc("historical_tv_max,future_tv_ex_post"),
     "1 - historical_tv_max / future_tv_ex_post, exact from stored decimals")
putq("drift.holdout.w_order_count", w, "fraction", 6, dsrc("n,origin"), "n / origin, exact")
putq("drift.holdout.hist_tv_max.like_for_like", tvmax / (1 - w), "tv", 6, dsrc("historical_tv_max,n,origin"),
     "historical_tv_max / (1 - n/origin), exact")
for suf, wv in (("w_0_05", F(1, 20)), ("w_0_10", F(1, 10)), ("w_one_eleventh", F(1, 11))):
    putq(f"drift.holdout.hist_tv_max.like_for_like.{suf}", tvmax / (1 - wv), "tv", 6, dsrc("historical_tv_max"),
         f"historical_tv_max / (1 - {wv}), exact")
DISP = f"{R}/tables/dispersion_survey.csv"
dp = read_csv(DISP)
for tok, nval, mult in (("n_half", 10937, "1/2"), ("n_P", 21874, "1"), ("n_2P", 43748, "2")):
    sub = dp[(dp.dataset_id == "BERNER") & (dp.origin == "199403") & (dp.n == str(nval))]
    assert len(sub) == 1 and sub.iloc[0].horizon_multiple == mult
    val = sub.iloc[0].max_abs_pp
    s_ = [src(DISP, f"dataset_id=BERNER,origin=199403,n={nval} (horizon_multiple {mult}): max_abs_pp")]
    put(f"disp.explor.{tok}.max_abs", val, float(F(val)), "pp", 4, s_, "stored decimal string")
    putq(f"disp.explor.{tok}.max_abs.like_for_like", F(val) / (1 - F(nval, 199403)), "pp", 6, s_,
         f"max_abs_pp / (1 - {nval}/199403), exact")


# ------------------------------------------------------------------ C. upper-only versus two-sided
def berner_block(camp, rule, delta):
    m = load_json(f"{R}/campaigns/{camp}/manifest.json")
    sub = cf[(cf.campaign == camp) & (cf.dataset_id == "BERNER")]
    assert set(sub.rule) == {rule} and set(sub.delta) == {delta}, camp
    out = {}
    for tok, arm in TS_ARMS:
        a = sub[sub.arm == arm]
        assert sorted(int(x) for x in a.n) == list(HORIZONS) and set(a.seed) == {"11"} and set(a.scored) == {"True"}, (camp, arm)
        per_n = {}
        for n in HORIZONS:
            r = a[a.n == str(n)].iloc[0]
            mr = [x for x in m["rows"] if x["case_id"] == r.case_id]
            assert len(mr) == 1 and mr[0]["arm"] == arm and mr[0]["n"] == n and mr[0]["dataset_id"] == "BERNER"
            crel = f"{R}/campaigns/{camp}/{mr[0]['expected_result']}"
            d = load_json(crel)
            assert d["case"]["case_id"] == r.case_id and d["status"] == "COMPLETE"
            check((d["evaluation"]["joint_pass"] is True) == (r.joint_pass == "True"), f"{crel}: joint_pass vs case_frame")
            check(fclose(d["validation"]["minimum_required_slack_exact"], r.minimum_required_slack), f"{crel}: slack vs case_frame")
            per_n[n] = {"cfr": r, "rel": crel, "d": d}
        out[tok] = per_n
    return out


def cfsel(camp, rule, delta, arm, col):
    return f"campaign={camp},dataset_id=BERNER,rule={rule},delta={delta},arm={arm},seed=11,n in 10937|21874|43748: {col}"


def pass_keys(pattern, camp, rule, delta, blk):
    for tok, arm in TS_ARMS:
        per = blk[tok]
        cnt = sum(per[n]["cfr"].joint_pass == "True" for n in HORIZONS)
        srcs = [src(CF_REL, cfsel(camp, rule, delta, arm, "joint_pass"))] + \
               [src(per[n]["rel"], f"case.arm={arm},case.n={n}: evaluation.joint_pass") for n in HORIZONS]
        putq(pattern.format(tok=tok), cnt, "count", None, srcs, "horizons (of 3) with joint_pass True; = case evaluation.joint_pass")


def slack_keys(prefix, camp, blk):
    for n in HORIZONS:
        e = blk["TIGHT"][n]
        putq(f"{prefix}.{n}", F(e["d"]["validation"]["minimum_required_slack_exact"]), "share", 6,
             [src(e["rel"], f"case.arm=TIGHT,case.n={n}: validation.minimum_required_slack_exact")],
             f"stored exact; = case_frame minimum_required_slack float ({camp})")


uo = berner_block("screen_20260910", "upper_only", "0.01")
pass_keys("uo.berner.pass.{tok}.count", "screen_20260910", "upper_only", "0.01", uo)
slack_keys("uo.berner.min_slack.TIGHT", "screen_20260910", uo)
for tag, camp, delta in (("d01", "ts_b01_20260912", "0.01"), ("d02", "ts_d02_20260912", "0.02"), ("d03", "ts_b03_20260912", "0.03")):
    blk = berner_block(camp, "two_sided", delta)
    pass_keys(f"ts.berner.{tag}.pass.{{tok}}.count", camp, "two_sided", delta, blk)
    if tag != "d02":
        continue
    slack_keys("ts.berner.d02.min_slack.TIGHT", camp, blk)
    for tok, arm in (("HIST_ACT", "HIST+ACT"), ("HIST", "HIST")):
        tot = {"cap": 0, "floor": 0}
        for n in HORIZONS:
            e = blk[tok][n]
            ev = e["d"]["evaluation"]
            st = station_stats(ev, e["rel"])
            check(ev["cap_violation_count"] == st["cap_n"] and ev["floor_violation_count"] == st["floor_n"], f"{e['rel']}: recount")
            check(str(ev["cap_violation_count"]) == e["cfr"].cap_violation_count
                  and str(ev["floor_violation_count"]) == e["cfr"].floor_violation_count, f"{e['rel']}: case_frame counts")
            tot["cap"] += ev["cap_violation_count"]
            tot["floor"] += ev["floor_violation_count"]
        for kind in ("cap", "floor"):
            fld = f"{kind}_violation_count"
            srcs = [src(CF_REL, cfsel(camp, "two_sided", delta, arm, fld))] + \
                   [src(blk[tok][n]["rel"], f"case.arm={arm},case.n={n}: evaluation.{fld}") for n in HORIZONS]
            putq(f"ts.berner.d02.{tok}.{kind}_breaches_total", tot[kind], "count", None, srcs,
                 f"sum over 3 horizons of evaluation.{fld}; each = exact station recount = case_frame")

syn = cf[(cf.rule == "two_sided") & (cf.dataset_id != "BERNER")]
assert all(x.startswith("syn_") for x in syn.dataset_id)
syn_ds = sorted(set(syn.dataset_id))
putq("ts.synthetic_instances.count", len(syn_ds), "count", None,
     [src(CF_REL, "rule=two_sided,dataset_id!=BERNER: nunique(dataset_id)")],
     f"distinct synthetic datasets run two-sided: {syn_ds}; campaigns {sorted(set(syn.campaign))}")
n_inst = len(set(zip(syn.dataset_id, syn.origin, syn.n)))
putq("extra.ts.synthetic_instances.instances", n_inst, "count", None,
     [src(CF_REL, "rule=two_sided,dataset_id!=BERNER: nunique((dataset_id,origin,n))")], "distinct (dataset, origin, n) instances")

# ------------------------------------------------------------------ D. accounting and context
AUDIT, AIDX = f"{R}/analysis_audit.md", f"{R}/artifact_index.json"
with open(ap(AUDIT), encoding="utf-8") as fh:
    lines = fh.read().splitlines()
ci = next(i for i, l in enumerate(lines) if l.strip() == "## Campaigns included")
analysed, an_lines = [], []
for i in range(ci + 1, len(lines)):
    if lines[i].startswith("## "):
        break
    mm = re.match(r"^\| `([^`]+)` \|", lines[i])
    if mm:
        analysed.append(mm.group(1))
        an_lines.append(i + 1)
sup_i = next(i for i, l in enumerate(lines) if l.startswith("Excluded as superseded"))
superseded = re.findall(r"`([^`]+)`", lines[sup_i])
aidx = load_json(AIDX)
check(set(analysed) == set(cf.campaign), "analysed vs case_frame")
check(analysed == [c_["name"] for c_ in aidx["campaigns"]], "analysed vs artifact_index")
check(superseded == aidx["excluded_superseded_campaigns"], "superseded vs artifact_index")
check(not (set(superseded) & set(cf.campaign)), "superseded present in case_frame")
put("acct.campaigns.analysed", json.dumps(analysed), None, "list", None,
    [src(AUDIT, f"'Campaigns included' table, Campaign column, lines {an_lines[0]}-{an_lines[-1]}"),
     src(CF_REL, "unique(campaign)"), src(AIDX, "campaigns[].name")],
    f"{len(analysed)} names; set = case_frame campaigns; list = artifact_index campaigns[].name")
put("acct.campaigns.superseded", json.dumps(superseded), None, "list", None,
    [src(AUDIT, f"line {sup_i + 1} 'Excluded as superseded': backticked names"), src(AIDX, "excluded_superseded_campaigns")],
    f"{len(superseded)} names; = artifact_index; none in case_frame")
den_i = next(i for i, l in enumerate(lines) if l.strip() == "## Denominator audit")
bins = {}
for i in range(den_i + 1, len(lines)):
    if lines[i].startswith("#"):
        break
    mm = re.match(r"^\| \**([^|*]+?)\**\s*\| \**(\d+)\**\s*\|", lines[i])
    if mm:
        bins[mm.group(1).strip()] = (int(mm.group(2)), i + 1)
n_auth, n_scored = len(cf), int((cf.scored == "True").sum())
n_noalloc = int((cf.allocation_returned == "False").sum())
check(n_auth == bins["Authorized rows"][0], "authorized vs audit")
check(n_scored == bins["Scored on its future horizon"][0], "scored vs audit")
check(n_noalloc == bins["Returned no allocation"][0], "no allocation vs audit")
check(n_noalloc == int((cf.status != "COMPLETE").sum()), "no allocation vs status")
for key, val, sel, lab in (("acct.rows.authorized", n_auth, "row count", "Authorized rows"),
                           ("acct.rows.scored", n_scored, "count(scored=True)", "Scored on its future horizon"),
                           ("acct.rows.no_allocation", n_noalloc, "count(allocation_returned=False)", "Returned no allocation")):
    putq(key, val, "count", None, [src(CF_REL, sel), src(AUDIT, f"line {bins[lab][1]} '{lab}'")],
         "recomputed from case_frame over the analysed campaigns; = audit value")
sc = cf[cf.scored == "True"]
assert (sc.layout_hash != "").all()
putq("acct.layouts.scored", sc.layout_hash.nunique(), "count", None, [src(CF_REL, "scored=True: nunique(layout_hash)")],
     "distinct layout_hash among scored rows, analysed campaigns (definition assumed; see Q-card)")
putq("extra.acct.layouts.scored.distinct_solve_key", sc.solve_key.nunique(), "count", None,
     [src(CF_REL, "scored=True: nunique(solve_key)")], "alternative reading: distinct solves among scored rows")
putq("extra.acct.layouts.scored.per_campaign_sum", int(sc.groupby("campaign").layout_hash.nunique().sum()), "count", None,
     [src(CF_REL, "scored=True: sum over campaign of nunique(layout_hash)")], "alternative reading: layouts counted within campaign")

PROF = f"{R}/tables/station_profile_industrial.csv"
sp = read_csv(PROF)
idx2lab, lab2idx = {}, {}
for i_, lab in set(zip(sp.station_index.astype(int), sp.station)):
    idx2lab.setdefault(i_, set()).add(lab)
    lab2idx.setdefault(lab, set()).add(i_)
bij = all(len(v) == 1 for v in idx2lab.values()) and all(len(v) == 1 for v in lab2idx.values())
ref_ids = {tuple(HOREC[k][e]["ids"]) for k in HOREC for e in ("rs", "es")}
same_ids = len(ref_ids) == 1
ref_idx = {i_ for i_, _ in next(iter(ref_ids))}
sp_ho = sp[sp.campaign == HO]
idx_match = set(sp_ho.station_index.astype(int)) == ref_idx == set(idx2lab)
rows_ok = len(sp_ho) == 288 and len(set(zip(sp_ho.arm, sp_ho.seed, sp_ho.station_index))) == 288
val_ok = True
for r_ in sp_ho.itertuples(index=False):
    rec = HOREC[(r_.arm, int(r_.seed))]
    i_ = int(r_.station_index)
    val_ok &= float(r_.target) == float(rec["rs"]["target"][i_]) and float(r_.future_share) == float(rec["es"]["share"][i_])
join = bij and same_ids and idx_match and rows_ok and val_ok
put("alias.join_exact", "1" if join else "0", 1.0 if join else 0.0, "bool", None,
    [src(PROF, "station_index,station (all rows); campaign=ho3_20260913 rows: arm,seed,target,future_share")] +
    ho_srcs(ALL_ARMS, "reference_evaluation.stations[*].station_index,station_id,target; evaluation.stations[*].share"),
    f"index<->label bijective over {len(sp)} rows: {bij}; profile index set = reference station_index set 0..23: {idx_match}; "
    f"same index/station_id order in all 12 records: {same_ids}; 288 unique ho3 rows: {rows_ok}; "
    f"profile target = reference target and future_share = evaluation share at joined index, all 288 rows: {val_ok}")
put("alias.map", json.dumps({str(i_): next(iter(idx2lab[i_])) for i_ in sorted(idx2lab)}), None, "map", None,
    [src(PROF, "distinct (station_index, station)")], "one S_k per station_index, index order")
sid = dict(next(iter(ref_ids)))
put("extra.alias.station_id_by_index", json.dumps({str(i_): sid[i_] for i_ in sorted(sid)}), None, "map", None,
    ho_srcs(["NOM"], "reference_evaluation.stations[*].station_index,station_id"), "identical in all 12 records")

slk = {}
for (arm, s), rec in HOREC.items():
    v_ = rec["d"]["reference_evaluation"]["validation"]
    slk.setdefault(arm, set()).add((v_["minimum_required_slack_exact"], tuple(x["label"] for x in v_["scenario_shares"]), v_["model_feasible_exact"]))
assert all(len(v) == 1 for v in slk.values())
slk = {a: next(iter(v)) for a, v in slk.items()}
assert slk["NOM"][:2] == slk["TIGHT"][:2] and slk["NOM"][1] == ("history",)
assert slk["HIST+ACT"][:2] == slk["HIST+ACT-T"][:2]
putq("ho.incumbent.training_slack", F(slk["NOM"][0]), "share", 6,
     ho_srcs(["NOM", "TIGHT"], "reference_evaluation.validation.minimum_required_slack_exact"),
     "incumbent validated on the single 'history' scenario [0,243151) that NOM/TIGHT train on; identical in those 6 rows (scenario set assumed; see Q-card)")
putq("extra.ho.incumbent.training_slack.hist_act_scenarios", F(slk["HIST+ACT"][0]), "share", 6,
     ho_srcs(["HIST+ACT", "HIST+ACT-T"], "reference_evaluation.validation.minimum_required_slack_exact"),
     f"same field on the {len(slk['HIST+ACT'][1])}-scenario HIST+ACT set; identical in those 6 rows; model_feasible_exact "
     f"{slk['HIST+ACT'][2]} (HIST+ACT), {slk['HIST+ACT-T'][2]} (HIST+ACT-T)")

# ------------------------------------------------------------------ E. displayed-precision cross-check (stderr)
E = [("ho.pass.NOM.count", "0"), ("ho.pass.TIGHT.count", "3"), ("ho.pass.HIST_ACT.count", "0"), ("ho.pass.HIST_ACT_T.count", "3"),
     ("ho.visits.NOM.mean", "3.231630"), ("ho.visits.TIGHT.mean", "3.269742"), ("ho.visits.HIST_ACT.mean", "3.263692"),
     ("ho.visits.HIST_ACT_T.mean", "3.346774"), ("ho.visits.incumbent", "3.847124"), ("ho.maxdev.NOM.max", "3.143883"),
     ("ho.maxdev.TIGHT.max", "1.756255"), ("ho.maxdev.HIST_ACT.max", "2.178584"), ("ho.maxdev.HIST_ACT_T.max", "1.159749"),
     ("ho.maxdev.incumbent", "1.156787"), ("ho.visits.HIST_ACT_T_over_TIGHT.pct", "2.355907"),
     ("drift.holdout.future_tv", "0.194956"), ("drift.holdout.hist_tv_max", "0.194411"), ("drift.holdout.hist_tv_mean", "0.171100")]


def rstr(q, nd):
    q = F(q)
    with localcontext() as ctx:
        ctx.prec = 80
        return str((Decimal(q.numerator) / Decimal(q.denominator)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))


mism = 0
for key, shown in E:
    got = rstr(OUT[key]["value_exact"], len(shown.split(".")[1]) if "." in shown else 0)
    mism += got != shown
    print(f"E {'MATCH' if got == shown else 'MISMATCH'} {key} computed={got} displayed={shown}", file=sys.stderr)
print(f"E mismatches: {mism}; verification warnings: {len(WARN)}", file=sys.stderr)
for w_ in WARN:
    print("WARN " + w_, file=sys.stderr)

sys.stdout.write("{\n" + ",\n".join(json.dumps(k) + ":" + json.dumps(v, separators=(",", ":")) for k, v in OUT.items()) + "\n}\n")
