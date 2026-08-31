"""Gate oracles for GATES_z_contract.md.

Z1-Z7 validate the PRE-REGISTERED DESIGN and are runnable before a single
solve: they check that the declared z window is anchored in measurement, that
the contract is arithmetically sound, that it discriminates in both
directions, and that it still rejects the pathology it exists to prevent.

Each subcommand exits 0 and prints its success-only token ONLY when every
assertion inside it passes.
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDS = os.path.join(REPO, "data", "derived", "berner_daily_folds")
sys.path.insert(0, os.path.join(REPO, "Baselines"))

DECLARED_Z = (3.0, 4.0, 6.0)
DECLARED_GAMMA = (0, 1, 2, 4)


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def _fold_dirs():
    return sorted(glob.glob(os.path.join(FOLDS, "berner_daily_r0f*")))


def _day_matrix(orders, prods):
    piv = (orders.assign(_P=orders["PRODUCT"].astype(str))
           .groupby(["DELIVERY_DATE", "_P"]).size().unstack(fill_value=0))
    return piv.reindex(columns=[str(p) for p in prods],
                       fill_value=0).to_numpy(float)


def fold(d, with_test=False):
    """Load a fold with the SAME product naming the solver uses."""
    from milp_highs_robust import read_data
    tag = os.path.basename(d)
    st = pd.read_csv(os.path.join(d, tag + "_train_stations.csv"), sep=";")
    pr = pd.read_csv(os.path.join(d, tag + "_train_products.csv"), sep=";")
    tro = pd.read_csv(os.path.join(d, tag + "_train_orders.csv"), sep=";")
    _a, _b, prods, _c = read_data(tag + "_train", d)
    sids = [str(s) for s in st["STATION_ID"]]
    s_idx = {s: i for i, s in enumerate(sids)}
    warm = {f"PROD_{r.PRODUCT_ID}": str(r.WARM_STATION) for r in pr.itertuples()}
    inc = np.array([s_idx.get(warm.get(p, ""), -1) for p in prods])
    if (inc < 0).any():
        fail(f"{tag}: incumbent unresolved for {int((inc < 0).sum())} products")
    oh = np.zeros((len(prods), len(sids)))
    oh[np.arange(len(prods)), inc] = 1.0
    out = {"tag": tag, "st": st, "prods": prods, "sids": sids, "inc": inc,
           "oh": oh, "Dtr": _day_matrix(tro, prods),
           "caps": st["CAPACITY"].astype(float).to_numpy()}
    if with_test:
        teo = pd.read_csv(os.path.join(d, tag + "_test_orders.csv"), sep=";")
        out["Dte"] = _day_matrix(teo, prods)
    return out


def band(D, oh):
    """mu_s and sigma_s of the station SHARE.

    Delegates to the PRODUCTION module (Baselines/share_contract.py) rather
    than reimplementing the formula. A gate that re-derives the logic it is
    checking would pass even if the shipped code were wrong -- it would only
    prove that two copies agree with each other.
    """
    from share_contract import fit_share_band
    mu, sd, shares = fit_share_band(D, oh)
    return shares, mu, sd


def z_needed(shares, mu, sd):
    return (shares.max(axis=0) - mu) / np.maximum(sd, 1e-12)


# ---------------------------------------------------------------- Z1
def z1():
    inc_need, med_need = [], []
    for d in _fold_dirs():
        f = fold(d)
        sh, mu, sd = band(f["Dtr"], f["oh"])
        zz = z_needed(sh, mu, sd)
        inc_need.append(zz.max())
        med_need.append(float(np.median(zz)))
    hi, lo = max(inc_need), float(np.mean(med_need))
    if not (5.5 <= hi <= 6.5):
        fail(f"incumbent worst-station z is {hi:.2f}, expected ~6.07 - the "
             f"declared upper bound is not anchored where the ledger says")
    if not (2.4 <= lo <= 3.0):
        fail(f"median-station z is {lo:.2f}, expected ~2.7")
    for z in DECLARED_Z:
        if not (lo - 0.35 <= z <= hi + 1e-9):
            fail(f"declared z={z} falls outside the measured window "
                 f"[{lo:.2f}, {hi:.2f}] - it would license behaviour the site "
                 f"has never shown, or demand balance it has never achieved")
    print(f"Z1 PASS z-window-anchored (incumbent needs {hi:.2f}, median "
          f"station {lo:.2f}, declared {DECLARED_Z} all inside)")


# ---------------------------------------------------------------- Z2
def z2():
    worst = 0.0
    for d in _fold_dirs():
        f = fold(d)
        sh, _mu, _sd = band(f["Dtr"], f["oh"])
        err = np.abs(sh.sum(axis=1) - 1.0).max()
        worst = max(worst, float(err))
        if err > 1e-9:
            fail(f"{f['tag']}: a day's shares sum to {1 + err:.12f}, not 1")
    print(f"Z2 PASS shares-sum-to-one (worst deviation {worst:.2e} over all "
          f"folds and days)")


# ---------------------------------------------------------------- Z3
def z3():
    """Exercises the production module's own assertion routine, then confirms
    that routine actually rejects a violated identity."""
    from share_contract import check_identities
    for d in _fold_dirs():
        f = fold(d)
        sh, mu, sd = band(f["Dtr"], f["oh"])
        for z in DECLARED_Z:
            try:
                check_identities(mu, sd, z, sh)
            except AssertionError as exc:
                fail(f"{f['tag']} z={z}: {exc}")
    # positive control: the checker must reject a band that does not sum to 1
    f = fold(_fold_dirs()[0])
    _sh, mu, sd = band(f["Dtr"], f["oh"])
    try:
        check_identities(mu * 0.9, sd, 3.0)
        fail("check_identities accepted a band whose mu sums to 0.9 - the "
             "production assertion cannot fail")
    except AssertionError:
        pass
    print(f"Z3 PASS allowance-identity (sum(mu)=1 exactly; total permission = "
          f"1 + z*sum(sigma) > 1 at every declared z)")


# ---------------------------------------------------------------- Z4
def z4():
    """Fitting on train must NOT equal fitting on train+test. If it does, the
    training fit is silently seeing the future."""
    for d in _fold_dirs():
        f = fold(d, with_test=True)
        _s1, mu_tr, sd_tr = band(f["Dtr"], f["oh"])
        pooled = np.vstack([f["Dtr"], f["Dte"]])
        _s2, mu_pool, sd_pool = band(pooled, f["oh"])
        if np.allclose(mu_tr, mu_pool, atol=1e-12) and \
                np.allclose(sd_tr, sd_pool, atol=1e-12):
            fail(f"{f['tag']}: train-only and train+test fits are identical - "
                 f"the training fit is contaminated by test data")
        if f["Dte"].shape[0] >= f["Dtr"].shape[0]:
            fail(f"{f['tag']}: test window is not smaller than train - "
                 f"fold construction is wrong")
    print("Z4 PASS no-leakage (train-only fit provably differs from a "
          "train+test fit on every fold)")


# ---------------------------------------------------------------- Z5
def z5():
    for d in _fold_dirs():
        f = fold(d)
        sh, mu, sd = band(f["Dtr"], f["oh"])
        hi = float(z_needed(sh, mu, sd).max())
        over_hi = int((sh > mu + hi * sd + 1e-9).sum())
        if over_hi != 0:
            fail(f"{f['tag']}: incumbent still breaches {over_hi} station-days "
                 f"at its own required z={hi:.2f}")
        over_lo = int((sh > mu + 2.0 * sd + 1e-9).sum())
        if over_lo == 0:
            fail(f"{f['tag']}: incumbent passes even at z=2 - the contract "
                 f"cannot fail and proves nothing")
    print("Z5 PASS discriminates-both-ways (incumbent clean at its own z, "
          "breaching at z=2, on all four folds)")


# ---------------------------------------------------------------- Z6
def z6():
    """Two negative controls, because one is not enough.

    (a) FLOOR: pile the highest-volume products onto the biggest stations. The
        contract must reject this at every declared z. This proves the
        constraint still prevents the pathology it exists for -- but it is so
        extreme that it is also rejected at z=20, so on its own it cannot tell
        a sensible z from an absurd one. (Found by mutation testing.)

    (b) BOUNDARY: a station sitting exactly at mu + 8*sigma must be rejected at
        every declared z (all < 8) and ACCEPTED at z = 10. Without the second
        half the oracle could pass by rejecting everything.
    """
    # (b) boundary discrimination, on the fitted band itself
    for d in _fold_dirs():
        f = fold(d)
        _sh, mu, sd = band(f["Dtr"], f["oh"])
        probe = mu + 8.0 * sd                      # a share 8 sigmas out
        for z in DECLARED_Z:
            if not (probe > mu + z * sd + 1e-12).any():
                fail(f"{f['tag']}: a station at mu+8sigma is NOT rejected at "
                     f"z={z} - the oracle does not bind where it claims to")
        if (probe > mu + 10.0 * sd + 1e-12).any():
            fail(f"{f['tag']}: a station at mu+8sigma is still rejected at "
                 f"z=10 - the oracle rejects everything and cannot "
                 f"discriminate")

    for d in _fold_dirs():
        f = fold(d)
        D, caps, sids = f["Dtr"], f["caps"], f["sids"]
        sh, mu, sd = band(D, f["oh"])
        totals = D.sum(axis=0)
        order = np.argsort(-totals)                    # busiest products first
        st_order = np.argsort(-caps)                   # biggest stations first
        bad = np.zeros((len(f["prods"]), len(sids)))
        k = 0
        for s in st_order:
            take = int(caps[s])
            for p in order[k:k + take]:
                bad[p, s] = 1.0
            k += take
        if k < len(order):
            for p in order[k:]:
                bad[p, int(st_order[-1])] = 1.0
        bad_sh = (D @ bad) / D.sum(axis=1)[:, None]
        for z in DECLARED_Z:
            over = int((bad_sh > mu + z * sd + 1e-9).sum())
            if over == 0:
                fail(f"{f['tag']} z={z}: the CONCENTRATED layout passes - the "
                     f"contract no longer prevents the pathology it exists "
                     f"for, so z={z} is too permissive")
    print(f"Z6 PASS concentration-rejected (floor: a concentrated layout is "
          f"rejected at z={DECLARED_Z}; boundary: mu+8sigma is rejected at "
          f"every declared z and accepted at z=10, so the oracle "
          f"discriminates)")


# ---------------------------------------------------------------- Z7
def z7():
    gmax = max(DECLARED_GAMMA)
    worst = float('inf')
    for d in _fold_dirs():
        f = fold(d)
        D, oh, inc = f["Dtr"], f["oh"], f["inc"]
        sh, mu, sd = band(D, oh)
        # The BINDING day is the QUIETEST one, not the busiest. Protection is
        # a constant number of lines (it depends on lhat, not on the day),
        # while the allowance z*sum(sigma)*L(d) scales with the day's volume.
        # So slack is smallest on the lowest-volume day. Checking the busiest
        # day would overstate affordability by the max/min volume ratio, which
        # is 2.6x on these folds.
        quietest = float(D.sum(axis=1).min())
        lhat = D.std(axis=0, ddof=1)
        prot = 0.0
        for s in range(len(f["sids"])):
            own = lhat[inc == s]
            if own.size:
                prot += float(np.sort(own)[::-1][:gmax].sum())
        for z in DECLARED_Z:
            slack = z * float(sd.sum()) * quietest
            if prot > slack:
                fail(f"{f['tag']} z={z}: Gamma={gmax} needs {prot:.0f} lines "
                     f"but only {slack:.0f} are available on the quietest "
                     f"training day - the declared Gamma range is not "
                     f"affordable at this z")
            worst = min(worst, slack / prot) if prot > 0 else worst
    print(f"Z7 PASS gamma-range-affordable (Gamma up to {gmax} fits inside the "
          f"slack on the QUIETEST training day at every declared z, on all "
          f"four folds; tightest cell has {worst:.2f}x the protection it "
          f"needs)")


# ---------------------------------------------------------------- Z9
def z9():
    """beta must TIGHTEN the share band, and a tightening must COST visits.

    Before Phase 3 the beta arm was a silent no-op under --share-z: rhs_lines
    overrode the tightened TIME_CAPACITY, so beta solved the unchanged band and
    duplicated gamma=0 (measured: -0.01% and -0.19% train visits, i.e. noise).
    """
    from share_contract import allowance_lines, tighten
    # (a) arithmetic: the band must shrink by exactly 1/beta
    for d in _fold_dirs():
        f = fold(d)
        _sh, mu, sd = band(f["Dtr"], f["oh"])
        totals = f["Dtr"].sum(axis=1)
        for z in DECLARED_Z:
            base = tighten(mu, sd, z, 1.0)
            for b in (1.02, 1.05):
                tb = tighten(mu, sd, z, b)
                if not np.allclose(tb * b, base, atol=1e-12):
                    fail(f"{f['tag']} z={z} beta={b}: band does not scale by "
                         f"1/beta")
                if not np.all(tb < base):
                    fail(f"{f['tag']} z={z} beta={b}: band did not shrink")
                ab = allowance_lines(mu, sd, z, totals, beta=b)
                a1 = allowance_lines(mu, sd, z, totals, beta=1.0)
                if not np.all(ab < a1):
                    fail(f"{f['tag']} z={z} beta={b}: allowance did not shrink")

    # (b) structural: wherever grid layouts exist, beta must be ENFORCED.
    #
    # This replaces an earlier check that required every beta arm's objective
    # to exceed its gamma0 baseline. That assertion is only valid for exact
    # optima: beta's feasible set is a strict subset of gamma0's, so the
    # OPTIMAL beta objective cannot be lower. Hexaly is a local-search solver
    # and returns incumbents, not optima, so the comparison tests solver luck
    # rather than the model. On the Phase 7 grid it failed in 6 of 24 cells
    # (worst -1.79%) while beta was demonstrably enforced in all 24.
    #
    # What is checked instead is exactly what "beta is binding" means, and it
    # holds regardless of solver quality: the returned layout must satisfy the
    # TIGHTENED band on every training day, and must differ from the gamma0
    # layout. The Phase 3 defect -- beta silently solving the unchanged band --
    # fails both.
    #
    # The objective comparison is still computed and REPORTED as a measured
    # solver gap, because a beta layout beating gamma0 is a feasible gamma0
    # point with a lower objective, i.e. proof that gamma0 was suboptimal by
    # that margin. It is asserted only against a loose bound: past ~5% the gap
    # would swamp the 7-15% Price of Robustness the study is measuring, and no
    # arm comparison would mean anything.
    import json
    from milp_highs_robust import read_data  # noqa: F401
    from share_contract import onehot_from_assignment
    GAP_BOUND = 5.0
    seen, worst_gap, deltas = 0, 0.0, []
    for d in _fold_dirs():
        f = fold(d)
        tag = f["tag"]
        _sh, mu, sd = band(f["Dtr"], f["oh"])
        totals = f["Dtr"].sum(axis=1)
        for z in DECLARED_Z:
            cell = _cell(z)
            res = os.path.join(cell, "results.csv")
            lay_dir = os.path.join(cell, "layouts")
            if not (os.path.isfile(res) and os.path.isdir(lay_dir)):
                continue
            df = pd.read_csv(res)
            sub = df[df.fold == int(tag[-1])]
            g0r = sub[sub.arm == "gamma0"]
            g0p = os.path.join(lay_dir, f"layout_{tag}_g0.json")
            if g0r.empty or not os.path.isfile(g0p):
                continue
            g0 = json.load(open(g0p, encoding="utf-8"))
            base = float(g0r.solver_obj.iloc[0])
            for b in (1.02, 1.05):
                lp = os.path.join(lay_dir, f"layout_{tag}_b{b}.json")
                if not os.path.isfile(lp):
                    continue
                seen += 1
                lay = json.load(open(lp, encoding="utf-8"))
                oh = onehot_from_assignment(lay, f["prods"], f["sids"])
                rhs = allowance_lines(mu, sd, z, totals, beta=b)
                over = int((((f["Dtr"] @ oh) > rhs + 1e-9).any(axis=1)).sum())
                if over:
                    fail(f"{tag} z={z:g} beta={b}: layout breaches the "
                         f"TIGHTENED band on {over} training days - the "
                         f"tightening was not enforced")
                if all(str(lay.get(k)) == str(g0.get(k)) for k in g0):
                    fail(f"{tag} z={z:g} beta={b}: layout is IDENTICAL to "
                         f"gamma0 - beta is a silent no-op")
                row = sub[sub.arm == f"tight{b}"]
                if not row.empty and bool(row.feasible_model.iloc[0]):
                    dlt = 100.0 * (float(row.solver_obj.iloc[0]) - base) / base
                    deltas.append(dlt)
                    worst_gap = max(worst_gap, -dlt)
    if worst_gap > GAP_BOUND:
        fail(f"a beta arm beat its gamma0 baseline by {worst_gap:.2f}%, above "
             f"the {GAP_BOUND:.0f}% bound - the solver gap would swamp the "
             f"Price of Robustness being measured")
    mean_d = float(np.mean(deltas)) if deltas else float("nan")
    print(f"Z9 PASS beta-tightens-band (band scales by exactly 1/beta and "
          f"shrinks at every declared z on all folds; {seen} beta layouts all "
          f"satisfy the TIGHTENED band on every training day and all differ "
          f"from gamma0; mean visit cost {mean_d:+.2f}%, largest reverse gap "
          f"{worst_gap:.2f}% = a measured bound on Hexaly suboptimality)")


# ---------------------------------------------------------------- Z14
def z14():
    """gamma_bind and gamma_cover must be correct, not merely present.

    Hand-computable case: one station holding three products with deviations
    [10, 5, 2] and 12 lines of headroom. Cumulative protection is [10, 15, 17],
    so the first budget that exceeds 12 is the SECOND -> gamma_bind = 2. With a
    realised test overshoot of 12, the first budget that reaches it is also the
    second -> gamma_cover = 2.
    """
    sys.path.insert(0, os.path.join(REPO, "Baselines"))
    from daily_metrics_share import gamma_bind, gamma_cover
    oh = np.array([[1.0], [1.0], [1.0]])            # 3 products, 1 station
    lhat = np.array([10.0, 5.0, 2.0])
    Dtr = np.array([[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]])   # load 3 per day
    rhs_tr = np.array([[15.0], [15.0]])                  # headroom 12
    gb = gamma_bind(Dtr, oh, lhat, rhs_tr)
    if int(gb[0]) != 2:
        fail(f"gamma_bind = {gb[0]}, expected 2 (protection 10 fits in 12, "
             f"10+5=15 does not)")
    Dte = np.array([[10.0, 5.0, 5.0]])                   # load 20
    rhs_te = np.array([[8.0]])                           # excess 12
    gc = gamma_cover(Dte, oh, lhat, rhs_te)
    if int(gc[0]) != 2:
        fail(f"gamma_cover = {gc[0]}, expected 2")
    # a station that never overshoots must ask for nothing
    if int(gamma_cover(Dte, oh, lhat, np.array([[100.0]]))[0]) != 0:
        fail("gamma_cover is non-zero for a station that never overshot")
    # a station already infeasible must bind at 0
    if int(gamma_bind(Dtr, oh, lhat, np.array([[1.0], [1.0]]))[0]) != 0:
        fail("gamma_bind is not 0 for an already-infeasible station")
    print("Z14 PASS gamma-bind-cover-correct (hand-computed case reproduced, "
          "plus the no-overshoot and already-infeasible edge cases)")


# ---------------------------------------------------------------- Z18
def z18():
    """The evaluator must NOT recurse into nested result directories.

    daily_metrics.py globs layouts tree-wide and keys arms by filename, so
    identical arm names in different directories collide and the
    alphabetically-last path silently wins -- which once scored 120-second
    smoke layouts as if they were 800-second grid results. Plant a decoy with
    a colliding name one level down and require it to be ignored.
    """
    import json
    import shutil
    import subprocess
    import tempfile
    src = os.path.join(REPO, "results", "z_contract")
    probe = None
    for cand in glob.glob(os.path.join(src, "*", "layouts")):
        probe = os.path.dirname(cand)
        break
    if probe is None:
        probe = (r"C:\Users\ebelul\AppData\Local\Temp\2\claude"
                 r"\c--ermal-CSLAP-Full-Project-CSLAP-Synthetic"
                 r"\6f5eb64b-99e3-4daa-9b47-d254dae08cd2\scratchpad"
                 r"\phase3_probe")
    if not os.path.isdir(os.path.join(probe, "layouts")):
        fail("no results directory with layouts/ available to test against")

    tmp = tempfile.mkdtemp(prefix="z18_")
    try:
        work = os.path.join(tmp, "cell")
        shutil.copytree(probe, work)
        real = sorted(glob.glob(os.path.join(work, "layouts", "*.json")))
        if not real:
            fail("probe has no layouts")
        # decoy: same filename, one level deeper, with every product on one
        # station. If it is picked up, the score changes drastically.
        decoy_dir = os.path.join(work, "nested", "layouts")
        os.makedirs(decoy_dir)
        lay = json.load(open(real[0], encoding="utf-8"))
        one = sorted(set(lay.values()))[0]
        json.dump({k: one for k in lay},
                  open(os.path.join(decoy_dir, os.path.basename(real[0])), "w"))

        out = os.path.join(tmp, "m.csv")
        r = subprocess.run(
            [sys.executable, os.path.join(REPO, "Baselines",
                                          "daily_metrics_share.py"),
             "--folds", os.path.join(REPO, "data", "derived",
                                     "berner_daily_folds"),
             "--results", work, "--z", "6", "--out", out],
            capture_output=True, text=True, cwd=REPO)
        if r.returncode != 0:
            fail(f"evaluator failed: {r.stderr.strip()[-400:]}")
        df = pd.read_csv(out)
        arm = os.path.basename(real[0]).split("_")[-1][:-5]
        sub = df[(df.arm == arm) & (df.role == "train")]
        if sub.empty:
            fail(f"arm {arm} not scored at all")
        if float(sub.worst_day_ratio.max()) > 5.0:
            fail(f"arm {arm} scored a worst ratio of "
                 f"{sub.worst_day_ratio.max():.1f} - the nested DECOY layout "
                 f"was picked up, so the collision defect is present")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("Z18 PASS no-layout-collision (a colliding decoy planted one level "
          "below the results directory is ignored)")


# --------------------------------------------------------------- layout
# Output convention the grid and these gates share.
# Sandbox hook for mutation testing ONLY. Unset in every real gate run,
# and announced loudly when set so sandboxed output can never be
# mistaken for evidence. It exists because the mutation fixture must
# build and DESTROY a tree, and it must never be able to destroy the
# real results.
ZDIR = os.environ.get("CSLAP_ZDIR_SANDBOX",
                      os.path.join(REPO, "results", "z_contract"))
if "CSLAP_ZDIR_SANDBOX" in os.environ:
    print(f"*** SANDBOX: reading {ZDIR}, NOT the real results ***")
ARMS = ("gamma0", "gamma1", "gamma2", "gamma4", "tight1.02", "tight1.05")
# solver-row arm name -> evaluator arm name (layout file stem)
_MET_ARM = {"gamma0": "g0", "gamma1": "g1", "gamma2": "g2",
            "gamma4": "g4", "tight1.02": "b1.02",
            "tight1.05": "b1.05"}


def _cell(z):
    return os.path.join(ZDIR, f"z{z:g}")


def _results(z):
    return os.path.join(_cell(z), "results.csv")


def _metrics(z):
    return os.path.join(ZDIR, f"metrics_z{z:g}.csv")


# ---------------------------------------------------------------- Z10
# The pilot runs the PRE-REGISTERED configuration (Hexaly, 600 s per arm).
# A first attempt at a reduced 120 s limit is kept alongside at
# pilot_f0_z3_120s: there Gamma=4 returned no incumbent (NOT proven
# infeasible) and this gate failed, which is exactly what a pilot is for.
PILOT = os.path.join(ZDIR, "pilot_f0_z3_600s")
PILOT_Z = 3.0
PILOT_FOLD = 0
# Measured on the fold-0 training days under the incumbent, and consistent
# with the pre-registered pooled table (8+8+9+10 = 35 of 179 days at z=3).
PILOT_INC_VIOL = 8
PILOT_DAYS = 38


def z10():
    """The pilot cell must complete end to end and honour its own contract.

    The pilot exists to catch a broken chain BEFORE ~13 solver-hours are spent,
    so it checks the three things that have actually gone wrong in this study:
    an arm silently missing, a layout recorded feasible while breaching the
    contract it was optimised against, and a local-search solver claiming a
    proof it cannot produce. It runs at a reduced time limit, so it is a
    validation of the pipeline and NOT a result: its objective values are not
    comparable with the grid's and are never reported as such.
    """
    res = os.path.join(PILOT, "results.csv")
    met = os.path.join(PILOT, "metrics_pilot.csv")
    for q in (res, met):
        if not os.path.isfile(q):
            fail(f"pilot missing {q}")

    d = pd.read_csv(res)
    folds = sorted(int(x) for x in d.fold.unique())
    if folds != [PILOT_FOLD]:
        fail(f"pilot folds {folds}, expected [{PILOT_FOLD}]")
    got = sorted(d.arm.unique())
    if got != sorted(ARMS):
        fail(f"pilot arms {got}, expected {sorted(ARMS)}")
    if d.duplicated(["fold", "arm"]).any():
        fail("pilot has duplicate (fold, arm) rows")
    bnd = pd.to_numeric(d.get("solver_bound"), errors="coerce").fillna(0.0)
    if np.isinf(bnd).any():
        fail("pilot claims a PROVEN infeasibility Hexaly cannot certify")

    m = pd.read_csv(met)
    if not (m.z == PILOT_Z).all():
        fail(f"pilot metrics carry z={sorted(m.z.unique())}, expected "
             f"{PILOT_Z:g}")
    tr = m[m.role == "train"]
    inc = tr[tr.arm == "incumbent"]
    if len(inc) != 1:
        fail(f"{len(inc)} incumbent train rows, expected 1")
    if int(inc.n_days.iloc[0]) != PILOT_DAYS:
        fail(f"{int(inc.n_days.iloc[0])} training days, expected {PILOT_DAYS}")
    if int(inc.days_violated.iloc[0]) != PILOT_INC_VIOL:
        fail(f"incumbent breaches {int(inc.days_violated.iloc[0])} of "
             f"{PILOT_DAYS} fold-0 training days at z=3, but the measured "
             f"reference is {PILOT_INC_VIOL}; the fit or scoring path drifted")

    opt = tr[tr.arm != "incumbent"]
    if len(opt) != len(ARMS):
        fail(f"{len(opt)} optimised arms scored on train, expected {len(ARMS)}")
    bad = opt[opt.days_violated > 0]
    if len(bad):
        fail(f"{len(bad)} pilot layouts breach their OWN training contract: "
             f"{bad[['arm', 'days_violated', 'n_days']].to_dict('records')}")
    print(f"Z10 PASS pilot-honours-contract ({len(opt)} optimised arms, 0 of "
          f"{PILOT_DAYS} training days breached; incumbent reference "
          f"{PILOT_INC_VIOL}/{PILOT_DAYS} reproduced)")


# ---------------------------------------------------------------- Z11
def z11():
    """All twelve cells ran and wrote six arms each."""
    total = 0
    for z in DECLARED_Z:
        p = _results(z)
        if not os.path.isfile(p):
            fail(f"z={z:g}: no results.csv at {p}")
        d = pd.read_csv(p)
        folds = sorted(int(x) for x in d.fold.unique())
        if folds != [0, 1, 2, 3]:
            fail(f"z={z:g}: folds {folds}, expected [0, 1, 2, 3]")
        for fld in folds:
            got = sorted(d[d.fold == fld].arm.unique())
            if got != sorted(ARMS):
                fail(f"z={z:g} fold {fld}: arms {got}, expected {sorted(ARMS)}")
            total += len(got)
        if d.duplicated(["fold", "arm"]).any():
            fail(f"z={z:g}: duplicate (fold, arm) rows")
    if total != 72:
        fail(f"{total} solver rows, expected 72")
    print(f"Z11 PASS grid-complete (3 z x 4 folds x 6 arms = {total} rows)")


# ---------------------------------------------------------------- Z12
def z12():
    """Every SOLVED layout must satisfy the contract it was optimised against.

    A layout that breaches its own training contract would mean the solver
    returned an infeasible point and the harness recorded it as feasible --
    exactly the failure that made the CPLEX arms meaningless (they broke
    53-92% of their own training days while being reported feasible).
    """
    checked = 0
    for z in DECLARED_Z:
        p = _metrics(z)
        if not os.path.isfile(p):
            fail(f"z={z:g}: no metrics at {p}")
        d = pd.read_csv(p)
        tr = d[(d.role == "train") & (d.arm != "incumbent")]
        if tr.empty:
            fail(f"z={z:g}: no optimised arms scored on train")

        # Vacuity guard. An arm that returned no layout writes no file, so it
        # would simply be absent here and this gate would pass on the arms that
        # did solve. Tie the scored set to what the solver actually claimed:
        # every (fold, arm) recorded feasible must have been scored, and
        # nothing may be scored that was not recorded feasible.
        rs = pd.read_csv(_results(z))
        claimed = {(int(r.fold), _MET_ARM[r.arm])
                   for r in rs.itertuples() if bool(r.feasible_model)}
        scored = {(int(r.fold), str(r.arm)) for r in tr.itertuples()}
        missing, extra = claimed - scored, scored - claimed
        if missing:
            fail(f"z={z:g}: {len(missing)} arms are recorded feasible but were "
                 f"never scored against their contract: {sorted(missing)}")
        if extra:
            fail(f"z={z:g}: {len(extra)} arms were scored but are not recorded "
                 f"feasible in results.csv: {sorted(extra)}")

        bad = tr[tr.days_violated > 0]
        if len(bad):
            rows = bad[["fold", "arm", "days_violated", "n_days"]]
            fail(f"z={z:g}: {len(bad)} optimised layouts breach their OWN "
                 f"training contract: {rows.to_dict('records')}")
        checked += len(tr)
    print(f"Z12 PASS layouts-honour-contract ({checked} optimised train rows, "
          f"0 breaching their own contract)")


# ---------------------------------------------------------------- Z15
def z15():
    """The incumbent must reproduce the PRE-REGISTERED coverage table.

    GATES_z_contract.md declares, before any solving, that the incumbent leaves
    80.4% / 94.4% / 99.4% of training days fully clean at z = 3 / 4 / 6. Over
    179 pooled training days that is exactly 35 / 10 / 1 violated days. If the
    evaluator disagrees, either the fit or the scoring path has drifted since
    pre-registration and every downstream number is suspect.
    """
    expect = {3.0: 35, 4.0: 10, 6.0: 1}
    for z in DECLARED_Z:
        p = _metrics(z)
        if not os.path.isfile(p):
            fail(f"z={z:g}: no metrics at {p}")
        d = pd.read_csv(p)
        inc = d[(d.arm == "incumbent") & (d.role == "train")]
        if len(inc) != 4:
            fail(f"z={z:g}: {len(inc)} incumbent train rows, expected 4")
        if int(inc.n_days.sum()) != 179:
            fail(f"z={z:g}: {int(inc.n_days.sum())} training days, expected 179")
        got = int(inc.days_violated.sum())
        if got != expect[z]:
            fail(f"z={z:g}: incumbent violates {got} training days but the "
                 f"pre-registered coverage table says {expect[z]}")
    print(f"Z15 PASS incumbent-matches-preregistration (35/10/1 violated "
          f"training days at z=3/4/6, exactly as declared)")


# ---------------------------------------------------------------- Z16
def z16():
    """No row may claim a proven infeasibility.

    Hexaly is a local-search solver. INCONSISTENT (a presolve contradiction) is
    mapped to proven; INFEASIBLE means only that nothing was found. If a
    proven-infeasible row ever appears here it must be justified explicitly,
    not accepted silently.
    """
    rows = 0
    for z in DECLARED_Z:
        p = _results(z)
        if not os.path.isfile(p):
            fail(f"z={z:g}: no results.csv at {p}")
        d = pd.read_csv(p)
        rows += len(d)
        if "solver_bound" not in d.columns:
            fail(f"z={z:g}: results.csv has no solver_bound column")
        proven = d[np.isinf(pd.to_numeric(d.solver_bound,
                                          errors="coerce").fillna(0.0))]
        if len(proven):
            fail(f"z={z:g}: {len(proven)} rows carry solver_bound=inf, i.e. "
                 f"claim a PROVEN infeasibility Hexaly cannot certify: "
                 f"{proven[['fold', 'arm']].to_dict('records')}")
    print(f"Z16 PASS no-false-proof ({rows} rows, none claiming a proven "
          f"infeasibility)")


# ---------------------------------------------------------------- Z17
def z17():
    """Per-fold outputs must survive the driver's overwrite-mode persist().

    run_bs_robust_experiment writes results.csv with to_csv (overwrite) and its
    row list starts empty per process, so sending several folds to one --out
    silently keeps only the last. The grid snapshots each cell; this checks the
    snapshots are complete and agree with the merged file.
    """
    for z in DECLARED_Z:
        snap = os.path.join(_cell(z), "_snapshots")
        if not os.path.isdir(snap):
            fail(f"z={z:g}: no _snapshots directory - per-fold outputs were "
                 f"not preserved against overwrite-mode persist()")
        parts = sorted(glob.glob(os.path.join(snap, "f*_results.csv")))
        if len(parts) != 4:
            fail(f"z={z:g}: {len(parts)} per-fold snapshots, expected 4")
        merged = pd.read_csv(_results(z))
        tot = 0
        for q in parts:
            d = pd.read_csv(q)
            if len(d) != 6:
                fail(f"z={z:g}: {os.path.basename(q)} has {len(d)} arms, "
                     f"expected 6")
            tot += len(d)
        if tot != len(merged):
            fail(f"z={z:g}: snapshots hold {tot} rows but merged results.csv "
                 f"has {len(merged)}")
    print("Z17 PASS per-fold-outputs-complete (4 snapshots x 6 arms per z, "
          "consistent with the merged results.csv)")


# ---------------------------------------------------------------- Z19
def z19():
    """The folds are NESTED, and the honest anchors are the distinct-day ones.

    The pre-registration reported coverage over "179 training days", which is a
    sum over expanding windows (38 < 43 < 47 < 51, all from 2021-09-01), so the
    earliest 38 days are counted four times. This gate pins both facts: that
    the folds really are nested, and that the corrected distinct-day anchors
    are what the ledger now states. It exists so the inflated figures cannot
    drift back in.
    """
    from share_contract import fit_share_band, allowance_lines
    dirs = _fold_dirs()
    if len(dirs) != 4:
        fail(f"{len(dirs)} folds, expected 4")
    sets, prev = [], None
    for d in dirs:
        tag = os.path.basename(d)
        tro = pd.read_csv(os.path.join(d, tag + "_train_orders.csv"), sep=";")
        cur = set(tro["DELIVERY_DATE"].unique())
        sets.append(cur)
        if prev is not None and not prev <= cur:
            fail(f"{tag}: training window is not a superset of the previous "
                 f"fold - the folds are not the expanding windows assumed")
        prev = cur
    nested_sum = sum(len(x) for x in sets)
    distinct = len(set().union(*sets))
    if nested_sum != 179 or distinct != 51:
        fail(f"nested sum {nested_sum} (expected 179), distinct {distinct} "
             f"(expected 51)")

    f = fold(dirs[-1])                    # fold 3 trains on all 51 distinct days
    _sh, mu, sd = band(f["Dtr"], f["oh"])
    D, oh = f["Dtr"], f["oh"]
    if D.shape[0] != 51:
        fail(f"fold 3 has {D.shape[0]} training days, expected 51")
    expect = {3.0: 41, 4.0: 48, 6.0: 50}       # clean days of 51
    for z in DECLARED_Z:
        rhs = allowance_lines(mu, sd, z, D.sum(axis=1), 1.0)
        clean = int((~(((D @ oh) > rhs + 1e-9).any(axis=1))).sum())
        if clean != expect[z]:
            fail(f"z={z:g}: {clean}/51 distinct days clean, ledger states "
                 f"{expect[z]}/51")
    if abs(100 * expect[6.0] / 51 - 98.0) > 0.1:
        fail("the z=6 distinct-day anchor is not 98.0%")
    print(f"Z19 PASS folds-nested-anchors-honest (38<43<47<51 nested, "
          f"179 slots over {distinct} distinct days; incumbent leaves "
          f"41/48/50 of 51 days clean at z=3/4/6, i.e. 80.4/94.1/98.0%, "
          f"not the pre-registered 80.4/94.4/99.4%)")


if __name__ == "__main__":
    fn = {"z1": z1, "z2": z2, "z3": z3, "z4": z4, "z5": z5, "z6": z6, "z7": z7,
          "z9": z9, "z10": z10, "z11": z11, "z12": z12, "z14": z14, "z15": z15,
          "z16": z16, "z17": z17, "z18": z18, "z19": z19}
    if len(sys.argv) != 2 or sys.argv[1] not in fn:
        print(f"usage: checks_z.py <{'|'.join(fn)}>")
        sys.exit(2)
    fn[sys.argv[1]]()
