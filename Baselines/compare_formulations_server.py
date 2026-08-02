import os
import pandas as pd
from scipy import stats
R="exp02a_results"
b=pd.read_csv(f"{R}/exp02a_binary_hexaly_server16core.csv")
b=b[b.status=="OK"][["size_n","instance_seed","visits","time_s","wl_broken","products_moved"]]
b=b.rename(columns={"visits":"binary","time_s":"b_time","wl_broken":"b_wl"})
r=pd.read_csv("exp02a_results_rerun/exp02a_per_instance.csv")
r=r[(r.status=="OK")&(r.method=="Hexaly")][["size_n","instance_seed","visits","time_s"]]
r=r.rename(columns={"visits":"setvar","time_s":"s_time"})
m=b.merge(r,on=["size_n","instance_seed"])
m["gap"]=100.0*(m.binary-m.setvar)/m.setvar
rows=[]
for n,g in m.groupby("size_n"):
    d=g.binary.values-g.setvar.values
    try: p=stats.wilcoxon(g.binary,g.setvar,mode="exact").pvalue
    except ValueError: p=float("nan")
    rows.append({"N":n,"n":len(g),"binary":round(g.binary.mean(),1),
                 "setvar":round(g.setvar.mean(),1),"gap_%":round(g.gap.mean(),2),
                 "bin_wins":int((d<0).sum()),"ties":int((d==0).sum()),
                 "wilcoxon_p":(round(float(p),4) if p==p else ""),
                 "bin_time":round(g.b_time.mean()),"set_time":round(g.s_time.mean())})
out=pd.DataFrame(rows)
pd.set_option("display.width",220)
print("=== SERVER (article's machine): binary vs set-variable ===")
print(out.to_string(index=False))
d=m.binary.values-m.setvar.values
print(f"\npooled n={len(m)}  binary wins {int((d<0).sum())}  mean gap {m.gap.mean():+.2f}%  "
      f"wilcoxon p={stats.wilcoxon(m.binary,m.setvar,mode='exact').pvalue:.4f}")
out.to_csv(f"{R}/exp02a_binary_vs_setvar_server16core.csv",index=False)
m.to_csv(f"{R}/exp02a_binary_vs_setvar_server16core_perinstance.csv",index=False)
print(f"\nwrote {R}/exp02a_binary_vs_setvar_server16core.csv")
