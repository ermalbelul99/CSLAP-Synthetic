"""Prove Z10 can BOTH pass and fail, without touching real results.

SAFETY. Two earlier versions of the mutation suite built their fixture inside
results/z_contract and deleted it on cleanup, destroying committed evidence
(recovered from git both times). Every mutation script now builds under its own
sandbox directory, exported via CSLAP_ZDIR_SANDBOX, and asserts before doing
anything that the path it is about to destroy is NOT the real results tree.

The fixture name must track the gate: checks_z.PILOT is derived from ZDIR, so
reading it from the module is what keeps the two in step. Hardcoding the name
here is what silently broke this suite once already -- the gate was retargeted
from the 120 s pilot to the 600 s one and this script kept mutating the old
path, so every mutation "passed" while proving nothing.
"""
import importlib.util
import os
import shutil
import subprocess
import sys

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
SB = os.path.join(HERE, "_z10_fixture")
CHECKS = os.path.join(HERE, "checks_z.py")
REAL = os.path.join(REPO, "results", "z_contract")
os.environ["CSLAP_ZDIR_SANDBOX"] = SB

# Ask the gate module itself which directory it reads, so the fixture can never
# drift away from the gate again.
_spec = importlib.util.spec_from_file_location("_cz", CHECKS)
_cz = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cz)
PILOT = _cz.PILOT
assert os.path.abspath(PILOT).startswith(os.path.abspath(SB)), (
    f"refusing to run: gate reads {PILOT}, which is not inside the sandbox "
    f"{SB} - this script would destroy real results")
assert not os.path.abspath(PILOT).startswith(os.path.abspath(REAL))

ARMS = ("gamma0", "gamma1", "gamma2", "gamma4", "tight1.02", "tight1.05")
MET = ("g0", "g1", "g2", "g4", "b1.02", "b1.05")


def build():
    shutil.rmtree(SB, ignore_errors=True)
    os.makedirs(PILOT)
    pd.DataFrame([{"fold": 0, "arm": a, "solver_obj": 17000.0 + 100 * i,
                   "solver_bound": 1500.0, "feasible_model": True}
                  for i, a in enumerate(ARMS)]).to_csv(
        os.path.join(PILOT, "results.csv"), index=False)
    rows = [{"fold": 0, "z": 3.0, "arm": "incumbent", "role": "train",
             "n_days": 38, "days_violated": 8, "worst_day_ratio": 1.2},
            {"fold": 0, "z": 3.0, "arm": "incumbent", "role": "test",
             "n_days": 5, "days_violated": 0, "worst_day_ratio": 0.9}]
    for a in MET:
        rows += [{"fold": 0, "z": 3.0, "arm": a, "role": "train", "n_days": 38,
                  "days_violated": 0, "worst_day_ratio": 0.99},
                 {"fold": 0, "z": 3.0, "arm": a, "role": "test", "n_days": 5,
                  "days_violated": 0, "worst_day_ratio": 0.95}]
    pd.DataFrame(rows).to_csv(os.path.join(PILOT, "metrics_pilot.csv"),
                              index=False)


def expect(want_pass, label):
    env = dict(os.environ, CSLAP_ZDIR_SANDBOX=SB)
    r = subprocess.run([sys.executable, CHECKS, "z10"], capture_output=True,
                       text=True, cwd=REPO, env=env)
    ok = (r.returncode == 0) if want_pass else (r.returncode != 0)
    print(f"  {'PASS' if ok else 'BROKEN'}  z10 {label}")
    if not ok:
        print(f"         -> {((r.stdout + r.stderr).strip() or '(silent)')[-200:]}")
    return ok


ok = True
print(f"fixture: {PILOT}")
print("Building a synthetic pilot that SHOULD satisfy Z10...")
build(); ok &= expect(True, "accepts a well-formed pilot")

print("\nMutating with each defect Z10 exists to catch...")
build()
p = os.path.join(PILOT, "results.csv"); d = pd.read_csv(p)
d[d.arm != "gamma2"].to_csv(p, index=False)
ok &= expect(False, "rejects a pilot missing an arm")

build()
p = os.path.join(PILOT, "metrics_pilot.csv"); d = pd.read_csv(p)
d.loc[(d.arm == "g4") & (d.role == "train"), "days_violated"] = 6
d.to_csv(p, index=False)
ok &= expect(False, "rejects a layout breaching its own contract")

build()
p = os.path.join(PILOT, "metrics_pilot.csv"); d = pd.read_csv(p)
d.loc[(d.arm == "incumbent") & (d.role == "train"), "days_violated"] = 3
d.to_csv(p, index=False)
ok &= expect(False, "rejects incumbent drift from the measured reference")

build()
p = os.path.join(PILOT, "results.csv"); d = pd.read_csv(p)
d.loc[0, "solver_bound"] = float("inf"); d.to_csv(p, index=False)
ok &= expect(False, "rejects a false proven-infeasibility claim")

shutil.rmtree(SB, ignore_errors=True)
print(f"\nsandbox removed = {not os.path.isdir(SB)}; real results intact = "
      f"{os.path.isdir(REAL)}")
print("Z10 DISCRIMINATES" if ok else "Z10 DOES NOT DISCRIMINATE")
sys.exit(0 if ok else 1)
