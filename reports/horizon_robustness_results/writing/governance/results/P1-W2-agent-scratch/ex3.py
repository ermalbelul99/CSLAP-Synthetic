import pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
R = r"C:\ermal\CSLAP_Full_Project\CSLAP-Synthetic\reports\horizon_robustness_results\tables"
cf = pd.read_csv(R+r"\case_frame.csv", dtype=str, keep_default_na=False)
print(cf.shape)
print(cf.groupby(["campaign","rule","delta","stage"]).size())
print("scored", cf.scored.value_counts().to_dict(), "alloc", cf.allocation_returned.value_counts().to_dict(), "status", cf.status.value_counts().to_dict())
b = cf[cf.dataset_id.str.upper().str.startswith("BERNER")]
print(b.dataset_id.unique())
cols = ["campaign","dataset_id","origin","n","arm","delta","seed","rule","status","scored","joint_pass","cap_violation_count","floor_violation_count","minimum_required_slack","worst_excess_pp","mean_visits_exact","reference_mean_visits"]
print(b[b.campaign.isin(["screen_20260910","ts_b01_20260912","ts_d02_20260912","ts_b03_20260912"])][cols].sort_values(["campaign","arm","n"]).to_string())
print(cf.dataset_id.unique())
tw = cf[cf.rule=="two_sided"]
print(tw.groupby(["campaign","dataset_id"]).size())
print("layout_hash scored distinct", cf[cf.scored=="True"].layout_hash.nunique(), "solve_key distinct scored", cf[cf.scored=="True"].solve_key.nunique(), "solve_key all", cf.solve_key.nunique())
print(cf.groupby("campaign").agg(rows=("case_id","size"), sk=("solve_key","nunique"), lh=("layout_hash", lambda s: s[s!=""].nunique())))
print(cf.reused_solve.value_counts())
