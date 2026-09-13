"""Prove the replacement Z9 still catches both defects it exists for."""
import json, os, shutil, subprocess, sys
import pandas as pd

import os  # noqa: E402
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL = os.path.join(REPO, "results", "z_contract")
SB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_z9_fixture")
CHECKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checks_z.py")
PY_ = sys.executable
FOLDS = os.path.join(REPO, "data", "derived", "berner_daily_folds")


def build():
    shutil.rmtree(SB, ignore_errors=True)
    for z in (3, 4, 6):
        shutil.copytree(os.path.join(REAL, f"z{z}"), os.path.join(SB, f"z{z}"))


def run():
    env = dict(os.environ, CSLAP_ZDIR_SANDBOX=SB)
    r = subprocess.run([PY_, CHECKS, "z9"], capture_output=True, text=True,
                       cwd=REPO, env=env)
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1][:160]


def expect(want_pass, label):
    code, msg = run()
    ok = (code == 0) if want_pass else (code != 0)
    print(f"  {'PASS' if ok else 'BROKEN'}  z9 {label}")
    if not ok:
        print(f"         -> {msg}")
    return ok


ok = True
print("Copying the REAL grid into a sandbox; it should still pass...")
build(); ok &= expect(True, "accepts the real grid")

print("\nMutating with each defect Z9 exists to catch...")
build()
tag = "berner_daily_r0f1"
lay = os.path.join(SB, "z4", "layouts")
shutil.copy(os.path.join(lay, f"layout_{tag}_g0.json"),
            os.path.join(lay, f"layout_{tag}_b1.02.json"))   # the Phase 3 no-op
ok &= expect(False, "rejects a beta layout identical to gamma0")

build()
pr = pd.read_csv(os.path.join(FOLDS, tag, tag + "_train_products.csv"), sep=";")
inc = {f"PROD_{r.PRODUCT_ID}": str(r.WARM_STATION) for r in pr.itertuples()}
json.dump(inc, open(os.path.join(SB, "z4", "layouts",
                                 f"layout_{tag}_b1.05.json"), "w"))
ok &= expect(False, "rejects a beta layout that breaches the tightened band")

shutil.rmtree(SB, ignore_errors=True)
print(f"\nsandbox removed = {not os.path.isdir(SB)}; real grid intact = "
      f"{os.path.isdir(REAL)}")
print("Z9 DISCRIMINATES" if ok else "Z9 DOES NOT DISCRIMINATE")
sys.exit(0 if ok else 1)
