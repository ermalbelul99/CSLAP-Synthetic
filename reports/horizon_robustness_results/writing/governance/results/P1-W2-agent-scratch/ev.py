import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
for sect in ["evaluation","reference_evaluation"]:
    print("=====", sect)
    for k, v in d[sect].items():
        if isinstance(v, list):
            s = f"list[{len(v)}]"
            if v: s += " [0]=" + repr(v[0])[:300]
        elif isinstance(v, dict):
            s = f"dict[{len(v)}] keys=" + repr(list(v.keys())[:12])[:300]
        else:
            s = repr(v)[:200]
        print(f"{k}: {s}")
print("===== solve_result.audit[0..3]")
for a in d["solve_result"]["audit"][:31]:
    print(repr(a)[:200])
print("top keys", list(d.keys()))
