"""Prove the grid gates can BOTH pass and fail, before the grid runs.

Builds a synthetic fixture under results/z_contract that satisfies Z11, Z12,
Z15, Z16 and Z17, confirms they pass, then mutates the fixture once per gate
with the specific defect that gate exists to catch and requires it to fail.
Removes the fixture afterwards, so no synthetic data can be mistaken for a
real result.
"""
import os
import shutil
import subprocess
import sys

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "_gate_fixture")
os.environ["CSLAP_ZDIR_SANDBOX"] = ZDIR
assert "CSLAP_Full_Project" not in ZDIR or "_gate_fixture" in ZDIR
CHECKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checks_z.py")
PY = sys.executable
ZS = (3.0, 4.0, 6.0)
ARMS = ("gamma0", "gamma1", "gamma2", "gamma4", "tight1.02", "tight1.05")
NDAYS = {0: 38, 1: 43, 2: 47, 3: 51}          # sums to 179
INC_VIOL = {3.0: [8, 8, 9, 10], 4.0: [2, 2, 3, 3], 6.0: [0, 0, 0, 1]}


def build():
    shutil.rmtree(ZDIR, ignore_errors=True)
    for z in ZS:
        cell = os.path.join(ZDIR, f"z{z:g}")
        snap = os.path.join(cell, "_snapshots")
        os.makedirs(snap)
        rows = []
        for fld in range(4):
            per = [{"fold": fld, "arm": a, "solver_obj": 17000.0 + 100 * i,
                    "solver_bound": 1500.0, "feasible_model": True}
                   for i, a in enumerate(ARMS)]
            pd.DataFrame(per).to_csv(
                os.path.join(snap, f"f{fld}_results.csv"), index=False)
            rows += per
        pd.DataFrame(rows).to_csv(os.path.join(cell, "results.csv"),
                                  index=False)
        mrows = []
        for fld in range(4):
            mrows.append({"fold": fld, "z": z, "arm": "incumbent",
                          "role": "train", "n_days": NDAYS[fld],
                          "days_violated": INC_VIOL[z][fld],
                          "worst_day_ratio": 1.0})
            mrows.append({"fold": fld, "z": z, "arm": "incumbent",
                          "role": "test", "n_days": 5, "days_violated": 0,
                          "worst_day_ratio": 0.9})
            for a in ("g0", "g1", "g2", "g4", "b1.02", "b1.05"):
                mrows.append({"fold": fld, "z": z, "arm": a, "role": "train",
                              "n_days": NDAYS[fld], "days_violated": 0,
                              "worst_day_ratio": 0.99})
                mrows.append({"fold": fld, "z": z, "arm": a, "role": "test",
                              "n_days": 5, "days_violated": 0,
                              "worst_day_ratio": 0.95})
        pd.DataFrame(mrows).to_csv(
            os.path.join(ZDIR, f"metrics_z{z:g}.csv"), index=False)


def run(gate):
    env = dict(os.environ, CSLAP_ZDIR_SANDBOX=ZDIR)
    r = subprocess.run([PY, CHECKS, gate], capture_output=True,
                       text=True, cwd=REPO, env=env)
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1][:150]


def expect(gate, want_pass, label):
    code, msg = run(gate)
    ok = (code == 0) if want_pass else (code != 0)
    print(f"  {'PASS' if ok else 'BROKEN'}  {gate} {label}")
    if not ok:
        print(f"         -> {msg}")
    return ok


ok = True
print("Building synthetic fixture that SHOULD satisfy the grid gates...")
build()
for g in ("z11", "z12", "z15", "z16", "z17"):
    ok &= expect(g, True, "accepts a well-formed grid")

print("\nMutating the fixture with the defect each gate exists to catch...")

build()
p = os.path.join(ZDIR, "z3", "results.csv")
d = pd.read_csv(p)
d[d.arm != "gamma4"].to_csv(p, index=False)          # drop an arm
ok &= expect("z11", False, "rejects a cell missing an arm")

build()
p = os.path.join(ZDIR, "z4", "metrics_z4.csv")
p = os.path.join(ZDIR, "metrics_z4.csv")
d = pd.read_csv(p)
i = d[(d.arm == "g2") & (d.role == "train")].index[0]
d.loc[i, "days_violated"] = 3                        # breaches own contract
d.to_csv(p, index=False)
ok &= expect("z12", False, "rejects a layout breaching its own contract")

build()
p = os.path.join(ZDIR, "metrics_z6.csv")
d = pd.read_csv(p)
i = d[(d.arm == "incumbent") & (d.role == "train")].index[0]
d.loc[i, "days_violated"] = 7                        # drifts from pre-reg
d.to_csv(p, index=False)
ok &= expect("z15", False, "rejects incumbent drift from the pre-registration")

build()
p = os.path.join(ZDIR, "z3", "results.csv")
d = pd.read_csv(p)
d.loc[0, "solver_bound"] = float("inf")              # false proof
d.to_csv(p, index=False)
ok &= expect("z16", False, "rejects a false proven-infeasibility claim")

build()
p = os.path.join(ZDIR, "metrics_z3.csv")
d = pd.read_csv(p)
d[~((d.arm == "g4") & (d.fold == 1))].to_csv(p, index=False)  # solved, unscored
ok &= expect("z12", False, "rejects a feasible arm that was never scored")

build()
p = os.path.join(ZDIR, "z3", "results.csv")
d = pd.read_csv(p)
d.loc[d.arm == "gamma4", "feasible_model"] = False   # scored but not feasible
d.to_csv(p, index=False)
ok &= expect("z12", False, "rejects an arm scored without a feasible record")

build()
os.remove(os.path.join(ZDIR, "z6", "_snapshots", "f2_results.csv"))
ok &= expect("z17", False, "rejects a lost per-fold snapshot")

shutil.rmtree(ZDIR, ignore_errors=True)
print(f"\nfixture removed; ZDIR exists = {os.path.isdir(ZDIR)}")
print("ALL GATE MUTATIONS BEHAVED" if ok else "SOME GATES DID NOT DISCRIMINATE")
sys.exit(0 if ok else 1)
