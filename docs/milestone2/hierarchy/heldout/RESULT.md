# Real-rating validation: hierarchy saves annotation effort, without an established ranking gain

October 14, 2026. This is a new held-out experiment. The earlier structural results and protocols remain unchanged.

## Finding

Across **320 held-out historical profiles**, the coherent certificate used **6.42** missing-label lookups on average versus **6.86** for the flat certificate with the same sound unary propagation. This is **6.5% fewer lookups** in the primary 50% masking condition.

The paired mean saving is **0.444 lookups**, with a 95% user-bootstrap interval **[0.197, 0.750]**. Both policies keep exactly the same five recommendations. This is an annotation-effort result, not evidence that the hierarchy improves human enjoyment.

**The nonzero-weight hierarchy reranker did not establish higher NDCG than the flat reranker. Validation selected zero theme weight, and the 75% masking stress test found lower NDCG than the historical baseline.** The defensible deployment interpretation is to retain the validated historical ranking and use the hierarchy as a conditional confidence checker when metadata is costly to acquire.

## Data and prospective local protocol

- Local source: **20,000,263 MovieLens ratings**. Conservative title/year + IMDb matching yielded **1,242 LTO-labelled films** and **3,841,046 matched ratings**. Ambiguous identities were excluded and logged.
- Chronological global cutoffs within matched ratings: train through February 19, 2006; validation through October 2, 2009; later ratings form test outcomes.
- Split sizes: 2,304,628 train, 768,209 validation and 768,209 test ratings.
- 128 validation profiles and 320 distinct test profiles, sampled in disjoint user-ID partitions. Future activity counts establish evaluability; future rating values do not choose profiles or parameters.
- Profiles use only the last 20 prior ratings. Evaluation users are excluded from the background similarity/popularity fit. All previously seen items are excluded from candidates. This simulates limited history, rather than proving zero-history cold start.
- Test background: 3,024,833 prior ratings from other users, 789 available films; 254–769 unseen candidates per profile.
- Retrieve the same 16 candidates for every decision method without inserting future positives. Rank five. Future rating >=4 is relevant, with unobserved candidates treated as nonrelevant for this offline evaluation. All 320 profiles enter primary means; 314 have an eligible positive target.
- User theme coefficients come from regularized regression on prior ratings, not scripted likes. Each request uses the 16 largest absolute coefficients and their ancestors (22–44 active facets). Independent intervals of ±25% are fixed sensitivity assumptions, not calibrated confidence intervals.
- Target metadata is artificially masked at 50% and 75%. Listed LTO themes and ancestors are 1; unlisted themes are 0 only within this controlled closed-world reference. Unlisted does not establish that a theme is absent in reality.
- Parameters are selected on validation only. The nonzero gamma=.5 comparison was frozen separately from the validation-selected deployment weight to prevent a zero-weight comparison from masquerading as a hierarchy test.
- Parent protocol SHA-256: `274be049eaca299152d310e9c418bdf4dffa6306162b05b0286f0a19e9b11fa0`. This was a local prospective freeze, not an external preregistration. EASE was added in a separately frozen extension before validation scoring; a full-catalog audit was declared during the test run before reading its results.

## Real held-out ranking: same 16 candidates, 50% missing labels

NDCG discounts relevant recommendations lower in the list. Recall measures how many eligible held-out positives the five recommendations recover. These outcomes are independent historical ratings, not generated matching utilities.

| Method | NDCG@5 | 95% user-bootstrap CI | Recall@5 |
|---|---:|---:|---:|
| Popularity | 0.2327 | [0.2026, 0.2642] | 0.1160 |
| Genre content | 0.1847 | [0.1579, 0.2115] | 0.0898 |
| ItemKNN | 0.2369 | [0.2067, 0.2684] | 0.1217 |
| Validated historical baseline | 0.2385 | [0.2084, 0.2696] | 0.1224 |
| EASE | 0.2320 | [0.2032, 0.2612] | 0.1292 |
| Flat regret + propagation | 0.2311 | [0.2015, 0.2616] | 0.1179 |
| Coherent hierarchy regret | 0.2322 | [0.2029, 0.2625] | 0.1185 |
| History-only marginal imputation | 0.2400 | [0.2104, 0.2706] | 0.1250 |
| Complete-annotation diagnostic | 0.2359 | [0.2065, 0.2673] | 0.1203 |

Primary paired NDCG difference (hierarchy minus flat): **+0.0010**, 95% CI **[-0.0005, +0.0029]**. The interval includes zero. This does not establish improvement or noninferiority.

The historical baseline is a validation-selected genre/ItemKNN mixture with popularity fallback for an empty positive profile. Validation selects content weight 0. EASE regularization selects 10,000. All nonzero theme comparisons use the same gamma=.5; neither method receives extra labels.

The complete-annotation row is a diagnostic using unmasked reference metadata, not a deployable missing-label baseline. Same-pool metrics must not be presented as a full-catalog contest.

### Full-catalog baseline audit

| Baseline | NDCG@5 | Recall@5 |
|---|---:|---:|
| Popularity | 0.2136 | 0.0995 |
| Genre content | 0.0261 | 0.0112 |
| ItemKNN | 0.2320 | 0.1189 |
| Validated historical baseline | 0.2385 | 0.1224 |
| EASE | 0.2247 | 0.1237 |

This audit lets baselines rank the entire available unseen matched-film catalog. We did not run a full-catalog pairwise hierarchy solver, so no global superiority claim follows.

## Metadata acquisition: same recommendations, different stopping rules

The first item of the fixed historical ranking is checked against its 15 challengers. Both methods see the same adaptive lookup sequence, use sound propagation and stop when normalized worst-case matching regret is <=0.20. Each lookup reveals one bit of the LTO reference. The budget is 24. The five-item recommendation list remains identical throughout; the certificate concerns its first item.

| Masked labels | Flat mean lookups | Hierarchy mean lookups | Mean saving, 95% CI | Relative reduction | Flat / hierarchy certified |
|---|---:|---:|---:|---:|---:|
| 50% | 6.862 | 6.419 | 0.444 [0.197, 0.750] | 6.5% | 250 / 255 of 320 |
| 75% | 17.600 | 16.928 | 0.672 [0.359, 1.034] | 3.8% | 119 / 129 of 320 |

- Costs include all sampled profiles and cap unsuccessful runs at their actual expenditure. They are not mean costs only among successful certificates.
- At 50% masking, 19/320 profiles save lookups. Among these benefiting profiles the descriptive mean saving is 7.47; it is not a population-wide claim. There are 65 profiles that neither model certifies within the budget.
- At 75% masking, 26/320 profiles save lookups. Only 129/320 receive a coherent certificate, versus 119/320 flat. The high failure rate matters.
- The coherent model can never stop later than the flat model along this shared sequence because its bound is tighter. That ordering is mathematical. The empirical result measures the frequency and magnitude with rating-derived preferences.
- These are simulated metadata annotation lookups. We did not measure human preference questions, actual tagging labor, API annotation cost or source-extraction accuracy.

## Stress-test failure and the validation guard

At 75% missing labels and gamma=.5, hierarchy NDCG is **0.2242**, versus **0.2385** for the historical baseline. The paired difference is **-0.0143**, 95% CI **[-0.0254, -0.0034]**. This interval is negative in this stress condition.

Validation selected gamma=0 before test scoring. Consequently, the selected deployment policy reproduces the historical baseline list exactly and has NDCG@5=0.2385. This is an intentional fallback supported by validation, not a hierarchy accuracy improvement. A nonsignificant difference at 50% masking must not hide the 75% failure.

## Computational tradeoff

The 16-item pairwise matrix has median **67.3 ms**, p95 **74.4 ms** on this Mac, excluding fitting, retrieval and source I/O.

A separate post-result replay of the primary certification prefixes measures **1.95 ms** flat and **29.88 ms** coherent computation on average. The added **27.93 ms** divided by **0.444** saved lookups gives an exploratory mean break-even annotation latency of **62.9 ms per lookup**.

That calculation assumes one uniform per-lookup latency. We did not measure annotation latency. Existing cheap labels may make exact certification unnecessary. This single replay times flat first and excludes fitting/retrieval/I/O, so it is not a production latency guarantee.

## Contribution boundary

This strengthens the earlier result with independent held-out relevance outcomes, stronger baselines, a quantified acquisition tradeoff and a falsifying stress condition. The candidate contribution remains the specialized exact uncertainty formulation and structural-fault extension, rather than invention of hierarchy tagging, minimax regret, graph cuts, or acquisition-cost analysis.

One temporal split and one catalog intersection do not establish generalization. LTO annotations are retrospective and incomplete. Ratings reflect selective historical exposure. There is no new book/song user validation, human trial or SLM accuracy improvement. The original PDF’s seven-signal product ranking formula is not reproduced by this isolated decision-layer experiment.

## Reproduction and verification

Completed protocols and results are protected against overwrite. A replication uses the same frozen inputs in a separate output directory, rather than creating a new split:

```bash
mkdir -p docs/milestone2/hierarchy/heldout-reproduction
cp docs/milestone2/hierarchy/heldout/{protocol,corpus,baseline-extension-protocol,full-catalog-audit-protocol}.json docs/milestone2/hierarchy/heldout-reproduction/
PYTHONPATH=apps/api:ml/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-research/bin/python -m recros_ml.research.hierarchy_holdout validate --out docs/milestone2/hierarchy/heldout-reproduction
PYTHONPATH=apps/api:ml/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-research/bin/python -m recros_ml.research.hierarchy_holdout test --out docs/milestone2/hierarchy/heldout-reproduction
```

The local parquet cache is reconstructed by the `freeze` command only in a clean separate experiment; its hash must match the preserved protocol before scoring. The cache comes from the locally downloaded original data. Source hashes, identity exclusions, validation trials, per-user predictions, lookup sequences, full-catalog scores and timing replay are preserved.

Verification: 112 API/ML tests pass, including conservative identity matching, temporal isolation, exclusion of evaluation users from background fitting, future-rating-independent sampling, constrained-ridge EASE equations, complete-information utility ranking and lookup stopping invariants.

## Primary sources

- [MovieLens 20M, GroupLens](https://grouplens.org/datasets/movielens/20m/)
- [LTO v2026.04, author release](https://zenodo.org/records/19367236)
- [EASE, Steck 2019](https://arxiv.org/abs/1905.03375)
- [Metric definitions, RecBole](https://recbole.io/docs/recbole/recbole.evaluator.metrics.html)
- [Derivation and attribution](../DERIVATION.md)

