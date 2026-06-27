# EXP-02a — CSLAP Multi-Instance Confidence Intervals (run-experiment plan)
# Status: COMPLETE / ACCEPTED (2026-06-24). scientific-reviewer STATUS: ACCEPTED (all 5 checks PASS;
#   binding condition = feasibility caveat in §3.12, applied). RESULT: N=50 methods tied (Heur~SA~GA;
#   Heur-SA p=0.38, Heur-GA p=0.85 ns; SA-GA p=4.9e-4); N=500 separated, all pairs sig (Wilcoxon
#   p=1.95e-3): Heur 78655 < GA 84417 < SA-C 88372; N=1000/2000 same order, descriptive only (K=4/3).
#   Heuristic best on visits BUT violates workload in 80-100% of instances (workload-relaxed) -> among
#   feasible methods GA>SA-C by ~5% at N>=500. GA seed axis near-inert (std~79~1%). Total 5.7h.
#   Integrated into Ch.3 §3.12 (sec:cslap-robustness, Table tab:exp02a) + App. B (app:exp02a, Tables
#   tab:exp02a-full + tab:exp02a-pairwise). Artifacts: CSLAP-Synthetic/exp02a_results/*.csv + hash_manifest.txt.
# Status (was): REV 2 (plan-gate round-1 fixes applied 2026-06-22). License-free; NO Hexaly/Gurobi/CPLEX.
# Feeds: Chapter 3 §3.12 (removes "single run / CIs pending" caveat) + Appendix B. Parent: draft-chapter-ch3.md.
# REV-2 changes vs REV1 (closing plan-reviewer GAPs):
#   G1 primary stat = absolute mean-visits ± CI + paired differences; best-found rel-gap demoted to a
#      labeled RELATIVE-RANKING secondary (NOT optimality). Frozen-Hexaly optimality gap NOT used:
#      EXP-02a instances differ (new seeds) from the one curated instance Hexaly solved, so no
#      per-instance optimum exists license-free -> report absolute visits, not gap-to-optimum.
#   G2 significance = PAIRED test (Wilcoxon signed-rank primary at small K; paired-t secondary) on
#      per-instance differences; CI-overlap demoted to descriptive diagnostic.
#   G3 R_GA=1 default (GA solver axis is near-inert: repair-shuffle only fires on capacity overflow,
#      often a no-op); freed budget reallocated to MORE instances at cheap sizes. Tiny R_GA=3 side-probe
#      at N=50 (3 instances) to DOCUMENT the near-inert axis.
#   G4 determinism success-criterion split (Heur exact = true overwrite guard; SA/GA "modulo wall-clock
#      stop") + per-seed CSV-distinctness hash assertion (catches seed-not-applied/overwrite).
#   G5 fixed-budget vs run-to-completion elevated to a STATED METHOD LIMITATION + success criterion;
#      time_s reported in every row; iso-time column optional.

## 1. Objective
Replace single-run synthetic numbers in Ch.3 §3.12 with mean ± 95% CI across multiple independently
generated random CSLAP instances per size, for the 3 license-free methods (GA, SA-C, Heuristic).
Answer "n=1?": quantify each method's reliability across the generator's instance distribution and
test whether inter-method differences are real (paired test) or within noise. Out of scope: exact/
commercial solvers; modifying the 3 baselines or the generator.

## 2. Environment (verified)
- Interpreter C:\Users\ebelul\Anaconda3\envs\savoye2023\python.exe (3.10). numpy, pandas, scipy 1.10.0 present.
- New runner must NOT import run_benchmarks.py (pulls dotenv + Gurobi/Hexaly). Import generator + 3 baselines directly.
- Exec dir: CSLAP_Problem\Different_Solution_Approaches\Full_Package_Code_With_All_Approaches\CSLAP-Synthetic\

## 3. Instance generation (VERIFIED — seedable generator; no blocker)
Entry: Data_Generators/synthetic_data_zhang.py -> generate_synthetic_data_zhang(num_skus, theta=0.7,
seed=42, output_dir). Zhang Common-Itemset, theta=0.7; fully seedable (rng=np.random.RandomState(seed),
all draws via rng -> distinct seed = independent instance). DERIVED params: num_itemsets=int(N*U[0.1,0.5]);
num_orders=int(N*U[30,50]); num_stations=max(5,N//100); CAPACITY=N//num_stations; SPEED=1;
TIME_CAPACITY=ceil((total_freq/num_stations)*1.10). Writes {prefix}_{orders,stations,products}.csv (sep=";"),
prefix=syn_{N}sku, returns 3 DataFrames.
COLLISION (handled): prefix has NO seed -> per (size,seed) write to OWN dir exp02a_instances/syn_{N}sku_seed{s}/
and read_data(f"syn_{N}sku", that_dir). Zero baseline edits. curated synthetic_datasets/ untouched.

## 4. Methods + call signatures (VERIFIED — reuse, do NOT modify)
read_data(prefix,data_dir): ga/sa -> (order_prods,stations,products,prod_lines); heuristic -> (...,orders_df) 5-tuple.
- GA: genetic_algorithm(order_prods,stations,products,prod_lines, pop_size=50,generations=200,cx_rate=0.8,
  mut_rate=0.1, time_limit, quick=False, warm_start_assignment=None) -> (state,best_visits,elapsed,
  max_workload,workload_std_dev,cap_broken,wl_broken). Internal RandomState(42) FIXED + global np.random.shuffle
  in repair_capacity (fires ONLY on capacity overflow, often no-op). set np.random.seed(g) before call =>
  controls only the repair shuffle (partial, often inert). No warm start.
- SA-C: simulated_annealing_correlated(...,T0=800,T_min=1,cooling_rate=0.95,sa_iter_factor=2,K_groups=10,
  time_limit, quick=False, warm_start_assignment=None) -> (best_state,best_visits,elapsed,max_workload,
  workload_std_dev,cap_broken,wl_broken). ALL randomness via internal RandomState(42) -> DETERMINISTIC per
  instance; R_SA=1. No warm start.
- Heuristic: heuristic_cslap(order_prods,stations,products,prod_lines,orders_df) -> (assignment,total_visits,
  elapsed,max_workload,workload_std_dev,cap_broken,wl_broken). NO RNG, runs to COMPLETION (no time limit);
  R_Heur=1.
Metric map: best_visits/total_visits->visits; elapsed->time_s; wl_broken->wl_broken; cap_broken sanity.

## 5. Metric semantics (VERIFIED)
visits = total order-station visits (CSLAP objective; identical in all 3; matches results_syn_*.csv).
wl_broken = #stations exceeding TIME_CAPACITY (soft, penalty 1000; methods can violate). cap_broken ~0.

## 6. Seed scheme + concrete K (REV 2)
Axis (a) instance-gen seed (PRIMARY = the data randomness): per N, K instances, seeds {1001..1000+K}.
Axis (b) solver seed: GA only, near-inert. DEFAULT R_GA=1 (one np.random.seed=20240612 before each GA call).
  SA-C R_SA=1, Heur R_Heur=1 (deterministic). Side-probe: at N=50, for the first 3 instances, also run GA
  with 2 extra seeds {20240613,20240614} -> report GA within-instance seed-std (expected ~0, documents the
  partial/inert axis). Side-probe rows tagged solver_probe=True, EXCLUDED from the main CI aggregation.
Concrete K (rigor concentrated at cheap sizes per GAP-3):
| N | K | R_GA(main) | note |
| 50 | 12 | 1 | + 3-instance R_GA=3 side-probe |
| 500 | 10 | 1 | |
| 1000 | 4 | 1 | |
| 2000 | 3 | 1 | CI uninformative (df=2) -> report point + range, NOT a CI claim (see §8) |
Fixed wall-clock budgets (GA/SA time-limited): 50->120s, 500->300s, 1000->600s, 2000->900s. Heuristic to completion.

## 7. Reported quantities (REV 2 — primary vs secondary)
PRIMARY (per method × size): absolute mean visits ± 95% CI across the K instances; AND pairwise paired
differences (see §8). These need no optimum and are non-circular.
SECONDARY (clearly labeled): best_found(i)=min over {GA(i),SA(i),Heur(i)} of visits; rel_rank(method,i)=
(visits-best_found)/best_found (percent). LABEL it "relative ranking among the 3 license-free methods
(min-of-3 => the per-instance winner is 0 by construction; this is NOT a gap to the true optimum)."
NOTE: no per-instance exact optimum is available license-free (the frozen Hexaly synthetic values apply
only to the ONE curated instance, not to these new-seed instances), so EXP-02a does NOT claim optimality
gaps; it reports absolute performance + relative ranking + reliability.

## 8. Statistics (REV 2)
Replication unit = instance. Per (method×size): mean_visits, std, n=K, 95% t-interval
mean ± t_{.975,K-1}*std/sqrt(K) (scipy.stats.t.ppf; report t-mult+df). min/max. For N=2000 (K=3,df=2)
report mean + [min,max] and mark CI "uninformative (n=3)" — do NOT lean on its CI.
SIGNIFICANCE (PRIMARY, paired — instances shared across methods): for each method pair (Heur-SA, Heur-GA,
SA-GA) compute per-instance visit differences and run Wilcoxon signed-rank (primary; robust at K=3..12)
AND paired-t (secondary); report the per-instance mean paired difference ± 95% CI and the p-value.
Conclusion per size: pair difference significant (CI excludes 0 / p<0.05) => ranking robust; else not
distinguishable at this K (honest non-result). CI-OVERLAP of the independent means = descriptive
diagnostic ONLY (anti-conservative; do not use as the significance verdict).
N=2000 (n=3): Wilcoxon cannot reach p<0.05 (min two-sided p ~ 0.25), so pairwise significance at
N=2000 is reported DESCRIPTIVELY only (the significance deliverable is scoped to N=50,500; success #3).
wl: frac_instances_wl_broken (#{wl_broken>0}/K) + mean_wl_broken per (method×size). GA seed-std from §6 side-probe.

## 9. New runner (NO baseline edits)
New: Baselines/run_exp02a_multiseed.py. sys.path.insert Data_Generators/ + Baselines/; import ONLY
generate_synthetic_data_zhang + the 3 baselines. For each N, each seed s: generate into per-seed dir,
read_data per baseline, run Heur(1x)+SA(1x)+GA(R_GA x), capture 7-tuples, write per-instance rows AS THEY
COMPLETE (restartable). At start, WRITE a hash manifest (sha256) of ga_baseline.py, sa_correlated.py,
heuristic_synthetic.py, synthetic_data_zhang.py into the out dir (auto-evidence of "unmodified", success #4).
Do NOT modify the 3 baselines or the generator.

## 10. Time budget (REV 2 default ~5-6 h; toggles offered)
With R_GA=1, K=12/10/4/3, budgets 120/300/600/900:
GA: 12*120+10*300+4*600+3*900 = 1440+3000+2400+2700 = 9540 s
SA: same = 9540 s ; Heur ~600 s ; side-probe (3 inst @50, +2 GA seeds) 6*120=720 s
Total ~20,400 s ~ 5.7 h single-thread (GA+SA dominate via time_limit).
TOGGLES (present to user at approval): FAST ~3 h = drop N=2000 + budgets 90/180/360 => GA/SA ~6,000 s each;
FULL ~5.7 h = above. Heur+SA cheap; budget is GA/SA time_limit-bound. Run serially in background.

## 11. Output (under exp02a_results/)
(a) exp02a_per_instance.csv: size_n, instance_seed, method, solver_seed, solver_probe, visits, time_s,
best_found_visits, rel_rank_pct, max_workload, workload_std_dev, cap_broken, wl_broken, num_orders,
num_itemsets, num_skus, num_stations.
(b) exp02a_aggregated.csv: size_n, method, n_instances, mean_visits, std_visits, ci95_lo, ci95_hi, t_mult,
df, min_visits, max_visits, ci_informative(bool), mean_rel_rank_pct, rel_rank_ci95_lo, rel_rank_ci95_hi,
frac_instances_wl_broken, mean_wl_broken, ga_seed_std_n50.
(c) exp02a_pairwise.csv: size_n, pair, mean_diff_visits, diff_ci95_lo, diff_ci95_hi, wilcoxon_p,
paired_t_p, significant(bool), ci_overlap_diagnostic(bool).
(d) exp02a_instances/syn_{N}sku_seed{s}/ retained for reproducibility (deletable); hash_manifest.txt.

## 12. Reproduce command
cd CSLAP-Synthetic; & savoye2023\python.exe Baselines\run_exp02a_multiseed.py --sizes 50 500 1000 2000
--k-per-size 12 10 4 3 --ga-seeds 20240612 --ga-sideprobe-seeds 20240613 20240614 --sideprobe-size 50
--sideprobe-k 3 --instance-seed-start 1001 --time-limits 120 300 600 900 --theta 0.7
--out-dir exp02a_results --instance-dir exp02a_instances
SMOKE first: --sizes 50 --k-per-size 2 --ga-seeds 20240612 --time-limits 30 (validate end-to-end).

## 13. Success criterion (verifiable, REV 2)
1. exp02a_per_instance.csv exists; no NaN in visits for completed rows.
2. exp02a_aggregated.csv has 12 rows (3 methods x 4 sizes); finite mean_visits; ci95_lo<ci95_hi where
   ci_informative=True; N=2000 rows ci_informative=False.
3. exp02a_pairwise.csv present with Wilcoxon + paired-t p-values and per-pair significance for N=50,500
   (enables the §3.12 "is the ranking real?" statement). [PAIRED test is the deliverable, not optional.]
4. Baseline files unchanged — verified by the auto-written sha256 manifest matching the repo files.
5a. (true overwrite/seed guard) Heuristic re-run on (N=50,seed=1001) reproduces identical visits
    (deterministic, no time limit); AND the 3 generated CSVs for seed{s} are hash-DISTINCT from seed{s+1}
    (proves the generation seed was actually applied -> no silent overwrite).
5b. SA-C/GA reproduce identical visits ONLY modulo the wall-clock stopping point (state this; their
    trajectory is deterministic but the stop iteration is load-dependent) — NOT a hard pass/fail.

## 14. Stated method limitation + open items
- FIXED-BUDGET FAIRNESS (limitation, must appear in §3.12 + App. B): GA and SA-C are evaluated at a fixed
  wall-clock budget; the heuristic terminates earlier at completion. Rankings are budget-conditional, not
  asymptotic, and hardware-dependent. Required write-up sentence: "GA and SA-C are run to a fixed wall-clock
  budget (state seconds per size); the heuristic runs to completion. Reported rankings are therefore
  conditional on that budget and on the machine, not asymptotic." Report time_s in every row; pin CPU/machine
  + single-thread in App. B. Optional nice-to-have: an iso-time column (GA/SA visits at the heuristic's wall-clock).
- best_found uses GA-main (R_GA=1) result; trivially reversible since GA has one main run.
- SA-C & Heur CIs are pure data-axis (deterministic per instance) — the cleanest; GA's extra seed axis is
  documented as near-inert via the N=50 side-probe.
- Generator num_orders/num_stations/num_itemsets are DERIVED from num_skus+seed; report realized values per instance.
- N=2000 K=3: report point + range, no CI claim. If tighter conclusions wanted later, add instances (linear cost).
