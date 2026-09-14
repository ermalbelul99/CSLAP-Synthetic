import json, glob, os
from fractions import Fraction as F
R = r"C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results"
man = json.load(open(os.path.join(R,"campaigns","ho3_20260913","manifest.json"),encoding="utf-8"))
print("manifest keys", list(man.keys()), "rows", len(man["rows"]))
first = True
for row in man["rows"]:
    d = json.load(open(os.path.join(R,"campaigns","ho3_20260913",row["expected_result"]),encoding="utf-8"))
    ev, ref = d["evaluation"], d["reference_evaluation"]
    if first:
        print("stations[0] ev:", json.dumps(ev["stations"][0], indent=0))
        print("stations[0] ref:", json.dumps(ref["stations"][0], indent=0))
        print("future_boundaries", ev["future_boundaries"])
        print("ref.validation keys", list(ref["validation"].keys()))
        print("ev.validation keys", list(ev["validation"].keys()))
        print("ref.validation scen labels", [ (s["label"], s["start"], s["stop"]) for s in ref["validation"]["scenario_shares"]])
        print("ref station_ids", ref["station_ids"])
        print("ev station idx", [s.get("station_index") for s in ev["stations"]])
        print("ref station idx", [(s.get("station_index"), s.get("station_id")) for s in ref["stations"]])
        first = False
    print(row["arm"], row["seed"], d["status"], "ev.mean", ev["mean_visits_exact"], "ref.mean", ref["mean_visits_exact"], "jp", ev["joint_pass"], "refjp", ref["joint_pass"],
          "we", ev["worst_excess_percentage_points_exact"], "cap", ev["cap_violation_count"], "floor", ev["floor_violation_count"],
          "slack", d["validation"]["minimum_required_slack_exact"], d["policy_validation"]["minimum_required_slack_exact"],
          "refval.slack", ref["validation"].get("minimum_required_slack_exact"), "refval.feas", ref["validation"].get("model_feasible_exact"),
          "ev.val.slack", ev["validation"].get("minimum_required_slack_exact"),
          "gap", d["solve_result"]["gap"], "bound", d["solve_result"]["bound"], "nscen", len(d["validation"]["scenario_shares"]), len(ref["validation"]["scenario_shares"]),
          "refhash", ref["layout_hash"], "fh", ev["future_hash"][:8], ref["future_hash"][:8],
          "bws", sum(s["beyond_worst_scenario"] for s in ev["stations"]), "bls", sum(s["below_lowest_scenario"] for s in ev["stations"]))
