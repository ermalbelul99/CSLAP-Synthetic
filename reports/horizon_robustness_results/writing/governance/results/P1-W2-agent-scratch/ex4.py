import json, os
from fractions import Fraction as F
import pandas as pd
R = r"C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results"
cf = pd.read_csv(R+r"\tables\case_frame.csv", dtype=str, keep_default_na=False)
print(cf.record_source.value_counts().to_dict(), cf.frozen_layout.value_counts().to_dict())
for camp in ["screen_20260910","ts_b01_20260912","ts_d02_20260912","ts_b03_20260912"]:
    man = json.load(open(os.path.join(R,"campaigns",camp,"manifest.json"),encoding="utf-8"))
    print("==", camp, {k:v for k,v in man["config"].items() if k!="datasets"}, len(man["rows"]), "rowkeys", sorted(man["rows"][0].keys()))
    for row in man["rows"]:
        if row["dataset_id"] != "BERNER": continue
        p = os.path.join(R,"campaigns",camp,row["expected_result"])
        ex = os.path.exists(p)
        d = json.load(open(p,encoding="utf-8"), parse_float=str) if ex else None
        ev = d["evaluation"] if d else {}
        print(row["arm"], row["n"], row["seed"], row["delta"], row.get("rule"), row["case_id"][:10], ex, d and d["status"], ev.get("joint_pass"), ev.get("cap_violation_count"), ev.get("floor_violation_count"),
              d and d["validation"].get("minimum_required_slack_exact"), d and d["validation"].get("minimum_required_slack"), ev.get("training_horizon"), ev.get("horizon"), ev.get("rule"))
# ho recompute checks
man = json.load(open(os.path.join(R,"campaigns","ho3_20260913","manifest.json"),encoding="utf-8"))
for row in man["rows"]:
    d = json.load(open(os.path.join(R,"campaigns","ho3_20260913",row["expected_result"]),encoding="utf-8"), parse_float=str)
    for tag in ["evaluation","reference_evaluation"]:
        ev = d[tag]
        st = ev["stations"]
        md = max(abs(F(s["share_exact"])-F(s["target_exact"])) for s in st)*100
        cap = sum(F(s["share_exact"])>F(s["cap_exact"]) for s in st)
        flo = sum(F(s["share_exact"])<F(s["floor_exact"]) for s in st)
        we = max([F(0)]+[F(s["share_exact"])-F(s["cap_exact"]) for s in st]+[F(s["floor_exact"])-F(s["share_exact"]) for s in st])*100
        ab = sum(F(s["share_exact"])>F(s["worst_share_exact"]) for s in st)
        be = sum(F(s["share_exact"])<F(s["lowest_share_exact"]) for s in st)
        fab = sum(bool(s["beyond_worst_scenario"]) for s in st); fbe = sum(bool(s["below_lowest_scenario"]) for s in st)
        # vector vs stations consistency
        vec_ok = all(F(ev["station_shares_exact"][i])==F(st[i]["share_exact"]) and F(ev["targets_exact"][i])==F(st[i]["target_exact"]) and F(ev["worst_scenario_envelope_exact"][i])==F(st[i]["worst_share_exact"]) for i in range(24))
        print(row["arm"], row["seed"], tag[:3], float(md), cap, ev["cap_violation_count"], flo, ev["floor_violation_count"], we==F(ev["worst_excess_percentage_points_exact"]), ab, fab, be, fbe, vec_ok, ev["joint_pass"], ev["mean_visits_exact"]==str(F(ev["visit_count"], ev["order_count"])) )
