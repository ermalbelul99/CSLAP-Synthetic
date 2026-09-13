# Mathematical scope of the order-horizon study

These are derivations from the declared model, not empirical findings. The industrial amendment of 9 September 2026 controls the retained system and assumed pre-known snapshot. No statement below establishes a probability of future feasibility.

## 1. Complete catalogue, fixed assignments, changing work

Let P contain every included warehouse product and S every included station. The two excluded industrial stations and their products are outside this system. All other frozen products remain inside P. Product and slot counts are equal. Each product occupies exactly one slot, whether or not its historical count is zero. No unknown new SKU is allowed in a future window.

For a future block W of n complete orders, let L_p(W) be its product workload count and T(W)=sum_p L_p(W)>0. Define q_p=L_p(W)/T(W), so q lies on the product simplex. Industrial workload counts distinct product-order pairs; synthetic workload retains original line multiplicity. Quantity is not this workload measure.

Write F_s for the products frozen at station s and M for movable products. The complete station share is

    r_s(x,q) = sum_{p in F_s} q_p + sum_{p in M} x_ps q_p.

The movable slot constraint is sum_{p in M} x_ps=C_s-|F_s|. Returning every fixed product restores the full C_s occupied slots. Fixed terms in the workload expression vary with q; freezing assignment does not freeze workload or workload share. A station whose products are all fixed still has a share constraint unless the station itself was explicitly excluded.

For order-station visits, a station touched by any fixed product already contributes one visit. Movable products can add a visit only if it was not already touched. Fixed-only orders and small orders remain in both objective and evaluation. Weighted identical supports are an exact compression only if every original order contributes its weight.

## 2. Scale invariance does not require dates

The reference target b_s is computed once at an origin from the complete historical workload under the declared incumbent. The ceiling is u_s=min(1,b_s+delta), with delta measured as an absolute share allowance. For any positive common multiplier c,

    c L_s / (c T) = L_s / T.

Consequently the same layout and demand proportions have the same feasibility at any positive total workload. This is exactly the user's abstract scalability assumption; physical throughput and station service limits are outside the claim. Changing only part of the workload changes its proportions and is not protected by scale invariance.

Dates are unnecessary to define the next n complete orders in a reliable sequence. They would be necessary to identify calendar-day/hour horizons, arrival rates or date-specific behavior. The choice of n remains part of the claim. The planned catalogue-relative grid n in {ceil(|P|/2), |P|, 2|P|} is a declared sensitivity design, not a discovered universal physical planning interval. Historical scenario blocks and primary future blocks use the SAME n. A longer training prefix supplies several matched historical blocks; it is not itself being treated as a single variance observation at a different horizon.

## 3. What upper-only protection means

Since sum_s r_s=1, the upper ceilings imply

    r_s >= max(0, 1 - sum_{j != s} u_j).

Without clipping and with common delta, this is max(0,b_s-(|S|-1)delta). In a two-station system, upper-only protection therefore also limits a station's decrease to delta. In a 24-station system, one station could in principle decrease by up to 23 percentage points when delta is one percentage point, provided the extra work is distributed across the others within their ceilings. Storage and demand restrictions may rule out that extreme for a particular instance.

Thus upper-only feasibility protects each station against excess share; it is not a symmetric promise to keep every station within plus/minus delta of its target. The implied lower bounds are necessary consequences, not an interchangeable lower-only formulation for arbitrary station counts. The study should report decreases as diagnostics and must not describe upper-only protection as two-sided balance preservation.

## 4. Exact finite robust counterpart

Let q^k be the historical n-block share vectors, including the pooled historical vector as an additional vertex. Let Z contain every catalogue product with zero historical workload. The declared activation uncertainty set, for nonempty Z, is

    U = {(1-a) z + a v : z in conv{q^k}, v in simplex(Z), 0 <= a <= nu}.

With Z empty, use the historical hull alone. For a fixed layout, write A_sk=r_s(x,q^k) and h_s=1 if any product in Z is assigned to s, zero otherwise. Then

    max_{q in U} r_s(x,q) = max_k max{A_sk, (1-nu) A_sk + nu h_s}.

Proof: a linear station sum attains its maximum over each simplex/hull at a vertex. For fixed vertices it is affine in a, so an endpoint a=0 or a=nu suffices. The fixed-product contribution is already part of A and h. Different stations can attain their worst values at different q; their separate maxima need not sum to one.

An independent alternative parameterization is q=sum_k lambda_k q^k + sum_{p in Z} mu_p e_p, with nonnegative weights, sum(lambda)+sum(mu)=1 and sum(mu)<=nu. This is a linear program and gives the same set. The software correctness suite checks the closed form against this separately constructed LP, rather than taking the formula as its own numerical oracle.

The guarantee is: if all finite rows are satisfied and the realized future q belongs to U, then every station respects u. It is simultaneous over stations for each q in U. It is NOT a guarantee that an unseen future lies in U, a 95% coverage statement, or protection for every possible future/order horizon. Floating-point solver certificates additionally require the documented numerical qualification and independent recomputation.

## 5. Activation protection and its limitations

nu is a workload-mass stress budget, not a probability and not an independent budget per inactive product. Every known inactive product remains allocated. If one such product is fixed at s, h_s=1 regardless of the movable layout. For nu<1 the activation row then becomes

    A_sk <= min{u_s, (u_s-nu)/(1-nu)}.

In particular u_s>=nu is necessary at that station; with b_s=0, delta>=nu is necessary. Several inactive products at the same station do not multiply the budget. If all h values are predetermined, activation reduces to station-specific tightening of the historical scenario constraints. If Z is empty or nu=0, HIST+ACT reduces to HIST. These equivalences must remain visible in comparisons and solve reuse.

The amended article snapshot does NOT imply all historically inactive products are frozen. Its freeze mask comes from the complete export and is held fixed by assumption; an item absent in the prefix may still belong to its movable pool.

Activation on previously unseen products does not cover arbitrary drift among previously active products. On those active coordinates, the allowed vectors remain proportional to combinations of historical vertices. With few historical blocks and many products, that restriction can be severe: a hull of K vertices has affine dimension at most K-1. Hence the model can be feasible and yet fail on future demand outside its set. Checking station-direction envelopes can expose some such departures but does not certify full product-vector membership. It is appropriate for the final study to find limited practical protection or no advantage over the tightening control.

## 6. Limits on universal future guarantees

If every possible nonnegative product mixture were admitted, a future concentrating all work on a product assigned to station s would give r_s=1. This can occur at any finite n by repeating orders for that product. For every nonempty station, a universal guarantee would therefore require u_s=1. Small nontrivial ceilings cannot protect an arbitrary future through static allocation alone. Adding dates does not remove this impossibility; it changes the horizon and available evidence, not the need to restrict demand uncertainty.

The declared U may itself contain fractional mixtures that are not exactly attainable by n orders. This is a conservative relaxation, not an assertion that each vertex mixture is a realizable order stream. n conditions which historical evidence constructs the set and which future is scored.

## 7. Minimum slack and useful correctness invariants

For any structurally feasible layout, its least common nonnegative slack is

    eta(x) = max{0, max_s(max_{q in U} r_s(x,q) - b_s)}.

Minimizing eta over layouts gives the model's required allowance, not an operationally acceptable allowance selected by the user. A validated layout gives an upper bound; a valid solver lower bound gives a lower bound. If a trustworthy lower bound exceeds the declared delta, the requested uncertainty protection is infeasible in the submitted model. A timeout with no layout or no bound proves neither feasibility nor infeasibility. Do not replace evaluation caps by eta after observing the future.

Two invariants follow directly. First, NOM and the declared TIGHT control always admit the historical reference: its historical share is b_s, and their ceilings are at least b_s. Second, the minimum-slack model admits that same structurally feasible reference with eta=1, because every station share is at most one. A native infeasibility report in either situation is an engineering/numerical contradiction to investigate, not a finding that future robustness is impossible.

## 8. Conditional information boundary

For industrial data the full catalogue, incumbent, capacities, fixed mask and retention rule are reconstructed by the article loader from the whole export and assumed available beforehand. This includes future-dependent last-station reconciliation and frequency-based freezing, and can affect which historical lines survive. It is a retrospective snapshot-conditioned experiment, not evidence that this metadata was actually available at each historical origin. Conditional on that snapshot, training counts, targets and scenarios use only the prefix, and each layout is fixed before future scoring. Source hashes, the complete allocation and exact scoring boundaries must make those claims auditable.

The date-based path remains a deferred alternative. Adopting it, changing the uncertainty family or selecting a different tolerance from future performance requires an explicit new study decision. None is inferred from the correctness checks above.

## 9. A useful consequence of matched, nested horizons

At one fixed historical origin, suppose n_large is an integer multiple of n_small. Because both historical grids are aligned at the same right endpoint, each complete large block is a union of complete small blocks. Its product-share vector is the line-volume-weighted convex combination of those small-block vectors. Both hulls also contain the identical pooled historical vector. Consequently

    U_large is a subset of U_small,

both for the historical hull and for its activation extension when Z and nu are unchanged. All current approved catalogue sizes are even, so the planned n=P/2, P, 2P grids have this nesting at a common origin. Reference targets, fixed masks and historical visit objective are unchanged across these horizons.

Therefore any layout robust-feasible for the smaller historical blocks is also feasible for the larger blocks; the exact minimum historical visit objective cannot increase when moving to the larger horizon's uncertainty set. This is a model consequence that can be tested independently of future data. Time-limited heuristic incumbents need not display the optimum's monotonicity and should not be mistaken for counterexamples to the theorem.

This does NOT establish monotone future feasibility: the next n_large orders include additional unseen orders beyond the first n_small. Their realized mix can differ substantially. Nor does this result apply automatically to non-multiple horizons or different historical origins. It supports the interpretation of the declared horizon grid without claiming a universal optimal n.

## 10. Exact integer-count restatement of the fixed-cap rows

Added 10 September 2026. This is a derivation about representation, not a new
modelling assumption, and it does not move the feasible set.

Every historical line count L_p^k is a nonnegative integer, and each scenario has
a positive integer line total T_k. The share row

    sum_p x_ps q_p^k <= u_s,     q_p^k = L_p^k / T_k

therefore has an integer left side once multiplied by T_k. Writing the activation
budget as an exact rational nu = N/M and multiplying that endpoint by M as well:

    base        sum_p x_ps L_p^k                    <= u_s T_k
    activation  (M-N) sum_p x_ps L_p^k + N T_k h_s  <= M u_s T_k

Both left sides are integers. For an integer z and a real r, z <= r holds exactly
when z <= floor(r). Hence

    base        sum_p x_ps L_p^k                    <= floor( u_s T_k )
    activation  (M-N) sum_p x_ps L_p^k + N T_k h_s  <= floor( M u_s T_k )

defines the SAME set of layouts. The restatement is neither a relaxation nor a
tightening, so delta, the ceilings u_s = min(1, b_s + delta), the uncertainty set
and the independent exact validator are untouched.

Its purpose is numerical. A solver satisfies a constraint only to within its own
feasibility tolerance. With rational-share coefficients that tolerance, about
1e-6 for the installed Hexaly 13, can admit a layout whose exact share exceeds
u_s by roughly that amount, which the exact validator then rejects. With integer
coefficients and an integer threshold, any violation is either zero or at least
one, so a tolerance below 1.0 cannot admit an exactly infeasible layout. The
observed industrial case moved from an exact residual of +1.0555e-06 (outside the
ceiling, rejected) to -1.208e-06 (strictly inside, accepted) under the identical
model and time limit.

Two boundary cases are worth stating. When the ceiling clips at u_s = 1, the base
threshold becomes floor(T_k) = T_k and the row is vacuous, correctly, since a
station cannot receive more than every line. When nu = 1 the base multiplier
M - N is zero and the activation row reduces to T_k h_s <= floor(u_s T_k), so a
station holding any historically inactive product is admissible only where
u_s = 1. Both agree with the continuous statement in Section 5.

The minimum-slack diagnostic is deliberately NOT restated this way: its epigraph
variable eta is a rational quantity rather than an integer count, so it remains
defined on the original rational model, and its bounds are bounds for that model.

Integer-range safety is explicit. The largest attainable left side is M T_k, and
the implementation refuses to emit a row whose left side could exceed the 64-bit
range rather than allowing silent wraparound. On the industrial case the largest
value actually built was 1.068e08, four orders of magnitude inside that limit.
