import json, sys
def tree(o, path="", depth=0, maxdepth=8, out=None):
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}.{k}" if path else k
            if isinstance(v, (dict, list)):
                n = len(v)
                print("  "*depth + f"{k}: {type(v).__name__}[{n}]")
                if depth < maxdepth:
                    if isinstance(v, list):
                        if n and isinstance(v[0], (dict, list)):
                            tree(v[0], p+"[0]", depth+1, maxdepth)
                        elif n:
                            print("  "*(depth+1) + f"[0]= {repr(v[0])[:120]}")
                    else:
                        if n > 60 and all(not isinstance(x,(dict,list)) for x in list(v.values())[:5]):
                            ks=list(v.items())[:4]
                            print("  "*(depth+1) + f"(scalar dict) sample {ks}")
                        else:
                            tree(v, p, depth+1, maxdepth)
            else:
                print("  "*depth + f"{k} = {repr(v)[:150]}")
    elif isinstance(o, list):
        if o: tree(o[0], path+"[0]", depth, maxdepth)
d = json.load(open(sys.argv[1], encoding="utf-8"))
tree(d)
