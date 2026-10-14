# Result: exact joint uncertainty on hierarchical facets

October 14, 2026. Candidate research contribution derived and tested in this project.
The [derivation](DERIVATION.md) states the proof and assumptions; the live model is
[available locally](http://127.0.0.1:8008/hierarchy). This result concerns computational
matching uncertainty. It does not establish better human enjoyment or a stronger SLM.

## What we derived

1. Under implication-only binary facets and independent bounded signed preferences,
   an exact pairwise worst-case ranking gap reduces to one minimum cut with 3m+2
   nodes and O(m+e) arcs. The preference vector is shared between both candidates.
2. Flat uncertainty can invent impossible parent/subtype combinations. In a
   k-pair construction it reports regret k where coherent regret is zero; after
   L1 normalization the phantom gap is 0.5.
3. Enforcing an incorrect hierarchy can invalidate a guarantee. A penalty-based
   graph-cut upper bound tolerates a declared budget of structural faults. This
   extension is conservative, rather than generally exact for the fault budget.

## Frozen structural experiment

- Public LTO release: 2,990 themes and 3,335 parent
  relations; 1,765 film records and 23 novels with
  mapped theme sections. All parent references resolve; story-tag parsing issues
  remain recorded in the protocol.
- 46 distinct source works (23 novels and 23 seeded films),
  both film→book and book→film directions, eight fixed target candidates per state.
- 276 states: three missing-data fractions and two preference-width
  conditions per source. There are 195 distinct retrieved target works.
  Request-active hierarchy sizes range from 12 to 22
  facets; the separate scaling test reaches 2,048 facets.
- Scripted broad-theme preferences and subtype exclusions. Active unlisted tags
  are assigned zero only in this closed-world reference experiment. Labels are
  artificially masked; they are not new LLM labels or independent human judgments.
- Protocol and inputs were frozen locally before measurement. The 276 states
  reuse 46 sources and overlapping candidates; they are not 276 independent people.
  Illustrations were selected after measurement for large bound differences.

Protocol SHA-256: `075d8e513dc8733abf1407153a44e083099aba06332d5bd2dae547a5e0c4a090`.

## Measured findings

The exact solver made **15,456 pairwise cuts**. No bound-order or
reference-bound failure occurred. It tightened the flat bound in **100 / 276
states (36.2%)**, after the flat baseline had already propagated known ancestor
and descendant facts. All methods below bound the same selected candidate:

| Bound | Mean normalized value |
|---|---:|
| Exact hierarchy + shared preferences | 0.2491 |
| Flat labels + shared preferences + unary propagation | 0.3179 |
| Independent per-item utility intervals, ablation | 0.4010 |

The exact bound is 21.7% lower on average than the flat common-weight bound.
This is tighter conditional uncertainty, **not a 21.7% accuracy gain**. The bound
ordering follows from the relaxation; the experiment measures its magnitude,
frequency and implementation correctness on these constructed states.

At a pre-used normalized threshold of 0.20, the same recommendation is certified
in **101 states** by the coherent model and **91** by the flat common-weight
model. Ten additional states pass without new item facts. The term certified
means the declared matching-model bound meets that threshold; it does not mean
human satisfaction is certified. At threshold zero both models certify 23 states,
so the hierarchy did not increase zero-regret coverage in this corpus.

For their separately selected candidates, mean coherent-model worst-case regret
is 0.2491 for exact selection and
0.2557 for flat-bound selection. Exact
minimax selection's optimality is a mathematical property of its objective;
these values are not independent evidence of preference accuracy.

## Independent computation checks and runtime

- Exact values and attaining witnesses checked against complete enumeration on
  240 seeded problems with up to five facets, signed interval weights, partial
  labels and implication DAGs. The native and Python flow backends agree.
- Structural fault upper bounds checked against complete budget-feasible
  enumeration on 90 further seeded problems with up to four facets.
- All **12 / 12** separately frozen scaling cases agree with a general HiGHS MILP
  oracle using the complete binary conjunction formulation. No timeout occurred.
- API/unit tests cover self-comparison, cycles, inconsistent evidence, structural
  fault feasibility, duplicate edges, large-integer fallback and read-only routes.

| Facets | Native cut median, ms | MILP median, ms | Python cut median, ms | MILP/native |
|---:|---:|---:|---:|---:|
| 32 | 0.325 | 4.854 | 1.187 | 14.95× |
| 128 | 0.749 | 5.637 | 4.561 | 7.52× |
| 512 | 2.485 | 13.162 | 27.907 | 5.30× |
| 2,048 | 8.817 | 34.311 | 108.952 | 3.89× |

Each row uses three seeded trees on this Mac, one discarded warm-up per solver,
and includes model/graph construction. Runtime is exploratory; implementation
language, presolve and ordering can affect it. The original Python cut backend
was slower than MILP at large sizes. Native integer flow was then added, with
the same frozen inputs; both runs are preserved. There is no universal speedup
claim and no exponential-baseline speedup percentage.

## Failure and the bounded repair

The recorded counterexample has coherent-model regret zero, but actual regret
one in a completion that violates one parent/subtype relation. Allowing one
structural fault raises the conservative bound to one, preventing that false
zero guarantee. Fault tolerance does not protect against incorrect observed
facts that happen to obey the ontology, or a preference box that excludes the
person's actual preferences.

## What is established and what remains novel only as a candidate

Minimax regret and joint feature/preference elicitation predate this project;
so do maximum closure, graph representability and Lagrangian upper bounds.
Our result is a specific derivation, exact implementation and structural
experiment for incomplete hierarchical facets with shared uncertain signed
preferences, extended by a declared structural-fault budget. Targeted searches
have not established an identical formulation. Global originality is not proved.
The full source attribution and expressiveness limits are in DERIVATION.md.

The next empirical test is independently judged intent and usefulness with
correctly sourced partial labels, the same candidates and a fixed question
budget. This experiment isolates the decision layer: it does not retrain the
tiny LM or turn author annotations into new human preference ground truth.
The original frozen source-reading and decision-planning experiments remain
separate and unchanged.

Reproduce with the existing research environment:

```bash
PYTHONPATH=apps/api:ml/src .venv-research/bin/python -m pytest ml/tests/test_hierarchy_regret.py apps/api/tests/test_hierarchy_routes.py -q
PYTHONPATH=apps/api:ml/src .venv-research/bin/python -m recros_ml.research.hierarchy_experiment run --result-name reproduction
```

The runner refuses to overwrite completed runs. Do not re-freeze the existing
protocol. `results.json` preserves the first Python-backend run;
`results-native.json` records the later native implementation. `states.json`,
`scales.json` and their protocol digests preserve all inputs.

## Held-out follow-up

The separate [real-rating experiment](heldout/RESULT.md) now evaluates 320
historical test profiles on independently held-out MovieLens ratings, after
validation on 128 disjoint profiles. It reports 6.5% fewer mean annotation
lookups for the same recommendations in its primary 50% masking condition,
with positive paired bootstrap savings. No ranking gain is established. The
75% masking stress condition lowers ranking relevance, and validation selects
zero theme-reranking weight. Its separate frozen protocol, raw predictions,
full-catalog baseline audit and computation tradeoff preserve that negative
finding. It does not change the earlier structural experiment or establish
human preference-question savings, book/song validation or SLM improvement.

A subsequent [book/song extension and three-domain comparison](domains/RESULT.md)
now evaluates 320 book profiles and 181 recording-level song listeners in
separate datasets. It preserves this movie study and finds small annotation-bit
savings without an established hierarchy ranking gain in either new domain.
The extension is within each domain; unrelated user IDs are never joined.
