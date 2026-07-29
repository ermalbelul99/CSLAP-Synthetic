r"""Instrumented profiler for cg_setpart_cplex: per-component wall time + per-iteration
master-LP growth + final ILP status. Monkey-patches the module functions with timers;
does NOT modify the solver. Writes JSON to profile_out/."""
from __future__ import annotations
import json, os, sys, time, argparse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "Baselines"))
import cg_setpart_cplex as CG

acc = {"lp": 0.0, "ip": 0.0, "price": 0.0, "complete": 0.0, "swap": 0.0, "heur": 0.0}
lp_trace = []   # (iter, n_cols_before, lp_seconds)
price_trace = []  # (iter, price_seconds, n_cols_returned, optimal)
ip_info = {}
_it = {"n": 0}

def wrap(obj, name, key, is_method, on_call=None):
    orig = getattr(obj, name)
    def inner(*a, **k):
        t = time.time(); r = orig(*a, **k); dt = time.time() - t
        acc[key] += dt
        if on_call: on_call(dt, a, k, r)
        return r
    setattr(obj, name, inner)

def lp_cb(dt, a, k, r):
    _it["n"] += 1
    self = a[0]
    lp_trace.append((_it["n"], len(self.patterns), round(dt, 4)))
def price_cb(dt, a, k, r):
    cols, rc_lb, opt = r
    price_trace.append((_it["n"], round(dt, 3), len(cols), bool(opt)))
def ip_cb(dt, a, k, r):
    chosen, bnd = r
    ip_info.update(seconds=round(dt, 2), n_chosen=len(chosen))

wrap(CG.Master, "solve_lp", "lp", True, lp_cb)
wrap(CG.Master, "solve_ip", "ip", True, ip_cb)
wrap(CG.ExactPricer, "price", "price", True, price_cb)
# module-level functions
for fn, key in (("complete_partition", "complete"), ("swap_descent", "swap"),
                ("heuristic_pricing", "heur")):
    orig = getattr(CG, fn)
    def mk(orig, key):
        def inner(*a, **k):
            t = time.time(); r = orig(*a, **k); acc[key] += time.time() - t; return r
        return inner
    setattr(CG, fn, mk(orig, key))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--time", type=int, required=True)
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()
    op, st, pr, pl = CG.read_data(args.prefix, args.dir)
    t0 = time.time()
    res = CG.run_cg_setpart(op, st, pr, pl, time_limit=args.time, seed=42, verbose=False)
    total = time.time() - t0
    out = {
        "tag": args.tag, "n_skus": len(pr), "n_orders": len(op),
        "n_stations": len(st), "budget_s": args.time, "total_s": round(total, 1),
        "visits": res[1], "best_bound": res[7], "cap_broken": res[5], "wl_broken": res[6],
        "n_iterations": _it["n"], "components_s": {k: round(v, 1) for k, v in acc.items()},
        "ip_info": ip_info,
        "lp_trace": lp_trace, "price_trace": price_trace,
    }
    os.makedirs("profile_out", exist_ok=True)
    with open(f"profile_out/profile_{args.tag}.json", "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: out[k] for k in
          ("tag","n_skus","n_iterations","total_s","visits","best_bound","components_s","ip_info")}, indent=2))

if __name__ == "__main__":
    main()
