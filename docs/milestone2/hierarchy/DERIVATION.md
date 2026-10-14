# Joint uncertainty on a label hierarchy: a project-derived tractable formulation

Derived and implemented October 14, 2026. The direction is the earlier proposal
to transfer relevant facets while preserving missing information. The specific
result is a graph reduction for simultaneous uncertain labels and uncertain
signed preferences, followed by a bound that tolerates a declared number of
structural hierarchy faults. This is a candidate research contribution; the
underlying closure, graph-cut and Lagrangian techniques are established.

## Model and exact result

A request has m binary facets. Each candidate has some known labels and some
unknown labels. An implication c→p means that a child facet implies its parent:
`x[c] <= x[p]`. Let H contain e such implications. No parent label implies that
every child is present. Several labels can be present simultaneously.

For one fixed source→target domain direction, the preference vector lies in an
independent interval box `W = product_j [L_j,U_j]`. Endpoints can be negative,
allowing a request to prefer a broad theme and avoid a particular subtype. The
same vector w evaluates every candidate in this target list. Utility is
`u(i,w,x_i) = sum_j w_j*x_i[j]`. These are declared conditional matching
utilities, not enjoyment probabilities or the May report's seven ranking signals.

Assume each item's completion set is nonempty, observed labels are correct,
implications are valid, and completions of different items have no additional
cross-item constraints. For distinct chosen item i and challenger k, define

`P(i,k) = max_(w,x_i,x_k) sum_j w_j*(x_k[j]-x_i[j])`.

The exact worst-case regret is `R(i) = max(0, max_(k != i) P(i,k))`.
An item compared with itself always has gap zero: its unknown labels cannot
take two different values in the same world.

**Proposition 1.** Each pairwise gap is computable by a single s–t minimum cut
on a graph with `3m+2` nodes and `O(m+e)` arcs. A finite N-candidate deterministic
minimax-regret recommendation therefore needs at most `N(N-1)` such cuts. No
enumeration of the joint label and weight worlds is required. Rational inputs
can be scaled to integer capacities; this implementation accepts integer-scaled
endpoints and uses exact integer flow values.

### Derivation

Write a for the challenger's label and b for the chosen label at one facet.
For fixed binary a,b, the maximizing weight is U when a>b and L when a<b:

`max_(w in [L,U]) w*(a-b) = U*a*(1-b) - L*(1-a)*b`.

Complement the chosen label: `y = 1-b`. The expression becomes

`L*a + L*y + (U-L)*a*y - L`.

The pair interaction has nonnegative coefficient `U-L`. Introduce an auxiliary
binary node z with weight `U-L`, and implications z→a and z→y. Maximizing selects
z exactly when both a and y are one whenever the coefficient is positive; if it
is zero its value is immaterial. Give a and y weight L. Subtract the constant L.

Copy each ontology implication c→p for challenger nodes a. For complemented
chosen nodes reverse it: y[p]→y[c]. Add hard constraints for observed a and y.
The resulting objective is a maximum-weight closed set on a directed graph.
For each positive-weight node v, add source→v with its weight as capacity. For
each negative-weight node, add v→sink with the negated weight. Implication and
fixed-value arcs receive a capacity larger than all possible finite costs.

The cut value equals the sum of positive node weights minus the weight of the
selected closed set. Subtracting `sum_j L_j` recovers P(i,k). The source-side
nodes supply coherent labels; interval endpoints supply the shared maximizing
weight vector. Direct substitution checks that this witness attains the value.
This is a specialization of established closure/graph-cut machinery, not an
invention of maximum flow. See [Picard, 1976](https://doi.org/10.1287/mnsc.22.11.1268)
and [Kolmogorov and Zabih, 2004](https://www.cs.cornell.edu/~rdz/Papers/KZ-PAMI04.pdf).

## Why hierarchy changes a decision

**Proposition 2: phantom regret.** Take k independent parent/subtype pairs. A
request assigns +1 to each parent and −1 to its subtype. Candidate A has all
labels unknown. Candidate B has all labels zero. Each subtype implies its
parent. A's utility is the sum of `parent-subtype`, which is always nonnegative
in a coherent completion. A therefore has exact worst-case regret zero.

A flat independent-label relaxation admits parent=0, subtype=1 for every pair.
It assigns A utility −k and reports regret k against B. Unary propagation does
not remove this error because all A's labels are unknown. The phantom gap grows
linearly with k on the unnormalized scale. If divided by the L1 weight sum 2k,
the gap is 0.5; it is not an unbounded normalized effect. This is an analytical
construction, not a measured human benefit.

More generally, after sound propagation of known labels:

`exact joint gap <= flat common-weight gap <= independent-utility interval gap`.

The first relaxation drops unknown-label coupling. The second additionally
allows different preference weights for the two candidates. Identical complete
profiles have joint gap zero even when their individual utility intervals are
wide. Interval width alone does not establish ranking uncertainty.

## What happens when the ontology is wrong

Blind enforcement can produce false confidence. In the k=1 construction, a
true completion parent=0, subtype=1 violates one implication. It makes A's
utility −1 and actual regret 1, despite the hard-hierarchy certificate of zero.
Thus a guarantee conditional on a perfect ontology is insufficient if structural
errors are plausible.

Let v count implication violations across the two compared label vectors. Keep
observed facts fixed. Suppose at most K implications may fail in the true pair.
For any penalty lambda≥0, define

`P_lambda(i,k) = max_(w,labels matching observed facts) [u(k)-u(i)-lambda*v]`.

**Proposition 3.** The budgeted worst-case gap satisfies

`P_K(i,k) <= min_(lambda in Lambda) [lambda*K + P_lambda(i,k)]`

for any nonempty set Lambda of nonnegative penalties. Each penalized inner
maximum is again a minimum cut: give an ontology arc capacity lambda rather
than hard capacity. Cutting that arc pays exactly for its violation. Keep
observations and auxiliary-node implications hard. Do not propagate observations
through potentially faulty ontology arcs before solving this model.

Proof: in every budget-feasible world, v≤K, so its unpenalized gap is at most
its penalized gap plus lambda*K, which is at most P_lambda+lambda*K. Maximize
over feasible worlds and then minimize the upper bounds. A feasibility cut with
zero utility weights finds the minimum possible number of structural violations.

The implementation uses a finite integer penalty grid (zero, powers of two and
a terminal value). Its answer is a conservative upper bound, **not generally
the exact budgeted optimum or the optimal continuous dual**. Its penalized
witness may violate more than K edges and must not be advertised as a feasible
worst-case world. An `attained` flag is true only when the witness fits the
budget and attains the unpenalized upper bound. For K=0 the hard solver is exact.

In the counterexample, K=1 raises the bound from zero to one. This prevents a
zero-regret certificate for that structurally inconsistent world. It does not
protect against incorrect observed labels that happen to obey the hierarchy,
misspecified utility, unmodeled context, or an underestimated fault budget.

## Expressiveness boundary

Independent signed intervals and implication-only label constraints are
essential to the reduction. It does not solve arbitrary coupled preference
constraints, fixed-sum weight simplexes, nonlinear utility or arbitrary label
disjunctions with the same graph construction.

Allowing unrestricted pairwise mutual exclusions includes an NP-hard family:
take unknown challenger labels as vertices of an arbitrary graph, impose
`x[u]+x[v]<=1` on every edge, use fixed positive vertex weights, and compare
against a known all-zero item. The pairwise gap is then maximum-weight
independent set. General solvers or conservative relaxations are needed for
that expanded model. This boundary is derived from the classical independent-set
problem, not claimed as a new hardness theorem.

## Contribution and attribution boundary

Joint feature/preference uncertainty and minimax-regret witnesses already appear
in [Boutilier, Regan and Viappiani, ICML 2009](https://icml.cc/2009/papers/427.pdf)
and [Regan and Boutilier, RecSys 2009](https://www.kevinregan.com/files/recsys09.pdf).
Their general formulations use optimization machinery; we do not claim the
uncertainty distinction or regret criterion. LTO supplies the public theme
ontology and annotations; CATN supplies precedent for fine-grained cross-domain
aspect transfer. Graph representability and Lagrangian bounds are established.

The candidate contribution is this explicit tractable formulation for incomplete
hierarchical facets with shared uncertain signed preferences, its structural
fault-budget extension, and the reproducible analysis of phantom regret on real
film/novel annotations under controlled masking. Targeted primary-source searches
did not establish a matching formulation, but this is not a proof of global
originality. Treat it as a project-derived result and candidate research method
pending a broader literature review and external scrutiny.
