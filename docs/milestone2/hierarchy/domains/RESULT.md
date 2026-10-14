# Books and songs: held-out extension and three-domain comparison

October 14, 2026. All measurements below come from preserved first runs. The movie experiment was not retuned or overwritten.

## Finding

We now test the same uncertainty mechanism against real movie ratings, book ratings and recording-level song listening events. Metadata masking and label completion remain controlled simulations. These are independent datasets with independent users, not evidence of shared-user cross-domain preference transfer.

**No domain establishes a hierarchy ranking gain over propagated flat labels. All three validation runs select zero theme-reranking weight. Small mean annotation-bit savings appear in all three domains, with positive supplemental adjusted intervals, but benefit only a small minority of evaluated profiles.**

The acquisition ordering follows from the tighter conditional bound; the experiment measures its size and frequency. A hierarchy can rule out impossible annotation worlds while a learned matching utility still predicts enjoyment poorly.

## Primary acquisition comparison

50% missing metadata, fixed hybrid reference ranking, normalized first-pick regret threshold 0.20 and maximum 24 source-reference bit lookups. Both stopping rules see the same query sequence and sound propagation. The five recommendations remain exactly identical. Means include unsuccessful budget-limited runs.

| Domain | Test profiles | Flat mean lookups | Hierarchy mean lookups | Reduction | Saving, nominal 95% CI | Profiles benefiting | Certificates flat / hierarchy |
|---|---:|---:|---:|---:|---:|---:|---:|
| Movies | 320 | 6.862 | 6.419 | 6.5% | 0.444 [0.197, 0.750] | 19 | 250 / 255 |
| Books | 320 | 15.316 | 14.953 | 2.4% | 0.362 [0.150, 0.619] | 13 | 168 / 174 |
| Songs | 181 | 12.249 | 12.094 | 1.3% | 0.155 [0.033, 0.309] | 5 | 129 / 129 |

These are annotation-bit lookups, not measured LLM calls, human preference questions, tagging labor or API charges. Actual services may return several labels in one response. The certificate concerns the first pick among 16 retrieved candidates and assumes the declared preference intervals and ontology are adequate; it does not certify human enjoyment or the entire catalog.

The lookup benchmark deliberately uses the nonzero gamma=.5 sensitivity model. When the selected ranking utility uses gamma=0, missing genre bits cannot affect that utility and no genre acquisition is needed for its ranking. The lookup saving therefore does not itself justify deploying the rejected nonzero model.

## Real held-out relevance

Same 16-item candidate pools, NDCG@5 at gamma=.5 and 50% missing labels. EASE is an established additional comparator. Reference hybrid parameters and EASE regularization are selected on validation only. Scores from different datasets/splits are not directly comparable as measures of which entertainment domain is easier.

| Domain | Hybrid reference | EASE | Flat regret | Hierarchy regret | Hierarchy minus flat, nominal 95% CI |
|---|---:|---:|---:|---:|---:|
| Movies | 0.2385 | 0.2320 | 0.2311 | 0.2322 | +0.0010 [-0.0005, +0.0029] |
| Books | 0.6190 | 0.6368 | 0.5999 | 0.5994 | -0.0005 [-0.0037, +0.0026] |
| Songs | 0.1649 | 0.1813 | 0.1586 | 0.1589 | +0.0003 [-0.0037, +0.0042] |

The historical movie and book validation studies selected zero theme weight. The song validation result is recorded independently below. Zero weight means that the paired deployment-policy family retains the reference list, rather than establishing a hierarchy accuracy gain. EASE is a separate comparator and is not automatically the reference retriever.

### Supplemental intervals across three domains

The original nominal intervals remain unchanged. The following supplemental bootstrap uses 20,000 profile resamples and Bonferroni-adjusted 98.33% intervals within each three-domain endpoint family. It is a descriptive correction, not a new parameter-selection procedure.

| Domain | Paired NDCG hierarchy minus flat | Adjusted interval | Mean saved lookups | Adjusted interval |
|---|---:|---:|---:|---:|
| Movies | +0.0010 | [-0.0009, +0.0033] | 0.444 | [0.150, 0.841] |
| Books | -0.0005 | [-0.0042, +0.0033] | 0.362 | [0.119, 0.681] |
| Songs | +0.0003 | [-0.0047, +0.0051] | 0.155 | [0.006, 0.370] |

### 75% missing-label stress condition

| Domain | Flat / hierarchy mean lookups | Flat / hierarchy certified | Hierarchy minus hybrid NDCG, nominal 95% CI |
|---|---:|---:|---:|
| Movies | 17.600 / 16.928 | 119 / 129 of 320 | -0.0143 [-0.0254, -0.0034] |
| Books | 22.484 / 22.369 | 39 / 42 of 320 | -0.0234 [-0.0391, -0.0072] |
| Songs | 19.558 / 19.298 | 59 / 60 of 181 | -0.0112 [-0.0247, +0.0025] |

High certification failure and negative relevance differences remain part of the result. Absence of a significant difference does not establish equivalence or noninferiority.

## Book dataset and split

- Source: Goodbooks-10k, **5,976,479 real ratings and 10,000 books**. All six downloaded source files match their pinned GitHub commit blob hashes. Duplicate user/book pairs: 0.
- CPU-bounded catalog: **3,000 books**, chosen by positive counts from disjoint background users, yielding **1,814,381 background ratings**. This is not a reproduction of a full 10k benchmark score.
- **128 validation and 320 test profiles**. Background users have ID modulo5 in {3,4}, validation modulo5=0, test modulo5 in {1,2}. Numeric IDs are never joined to other domains.
- Within each evaluated profile, 20 random ratings are supplied; remaining ratings are held out. No explicit timestamps exist, so this is a cross-sectional random split with no forward-prediction claim. Eligibility uses counts and known-history positivity, not future rating values.
- **69 facets and 38 implications**. Genre/subgenre mappings are project-declared and frozen before scoring. Source shelf assignments require at least five votes. Themes/tone, edition language and publication period are separate facets. Source data are not exhaustive semantic ground truth.
- The content baseline uses author identifiers, not hidden genre labels. Aggregate average ratings and catalog-wide ratings counts never score popularity; only the disjoint background interaction matrix does.
- Publication period is not story-setting era. Catalog edition language is not necessarily original language. Geographic setting is not inferred from author identity.
- Validation selects author/ItemKNN mixture alpha=0.5 and theme gamma=0. EASE can outperform this mixture and is reported separately.
- Frozen protocol: `78175dfd9cf8e70659b9d148bf2904eaa017b11632c19705cc64e3a2afc0e1a5`.

## Song dataset and split

- Source log: **19,150,868 actual song-play events** from Last.fm 1K. The decompressed original MD5 matches its published checksum. The AcousticBrainz genre archive also matches its published MD5.
- Genre source: **566,710 recordings**, with source-provided genre/subgenre paths. Joining **exact recording MusicBrainz IDs** yields **6,574,469 plays of 176,909 recordings across 991 matched listeners**. No fuzzy title joins or artist-only proxy evaluation.
- CPU-bounded catalog: **2,000 recordings**, selected by distinct background training listeners before validation/test. **1,353,724 play events** belong to this selected catalog. This popular, annotated subset limits long-tail generalization.
- **95 validation and 181 test listeners** with disjoint background partitions. Global matched-event cutoffs: 2008-02-19T11:27:49+00:00 train and 2008-10-14T19:40:32+00:00 validation. Test events occur later.
- Repeat plays are aggregated only within each historical window. Profiles use the 20 most recent distinct previously played recordings. Signed genre coefficients learn centered log(1+past play count), not declared dislikes or invented enjoyment ratings.
- A relevant test target is played after the cutoff and absent from the pre-cut logs. Previously played recordings are excluded. Unobserved recordings are treated as nonrelevant offline, not actual dislikes.
- Internal adapter field `rating=4+log(1+plays)` lets existing binary-positive routines consume play events. It is not a star rating; centering removes the added constant for preference fitting.
- **327 genre facets and 297 source-provided implications**. Lastfm genres were inferred by the AcousticBrainz authors from collaborative recording tags. Retrospective annotations and missing subgenre negatives remain limitations.
- The content baseline uses artist identifiers, not hidden genre labels. A song is identified and recommended by recording MBID, with title and artist retained as display metadata.
- Validation selects artist/ItemKNN mixture alpha=0.5 and theme gamma=0.
- Frozen protocol: `6b696ed560412343c323dac92b753560cdf226820fc30e0f25d983c7c2461982`.

## Full-catalog baseline audit

Each baseline can rank every unseen item in its available catalog. Hierarchy is still tested as a 16-candidate decision layer. Consequently, the same-pool table cannot establish global superiority over these full-catalog baselines.

| Domain | Popularity | Metadata content | ItemKNN | Hybrid reference | EASE |
|---|---:|---:|---:|---:|---:|
| Movies | 0.2136 | 0.0261 | 0.2320 | 0.2385 | 0.2247 |
| Books | 0.2888 | 0.4688 | 0.5748 | 0.6190 | 0.6455 |
| Songs | 0.0637 | 0.1524 | 0.1221 | 0.1649 | 0.1832 |

## Implementation, integrity and claim boundary

- `domain_holdout.py` prepares independent datasets, freezes corpus/windows/cohorts, selects parameters on validation, and refuses to overwrite completed scoring runs. The original movie protocols and predictions remain unchanged.
- Genre tags and preference intervals are sensitivity-model inputs, not calibrated probabilities. Masking reveals both positive and unlisted-negative reference bits; actual annotation correctness and noisy extraction remain unmeasured.
- Same-item gaps, shared preference cancellation, implication propagation, temporal isolation, source identity, future-count exclusion and constrained-ridge EASE equations have meaningful unit tests. The full API/ML suite has 116 passing tests.
- Effective seeds: new-domain partition/profile sampling 271828; shared missing-label masks 314159 plus profile/condition offsets; original nominal bootstrap 42. Supplemental corrected intervals use 20261014. Only separate mask means are reported.
- There is no linked-user evidence for movie-to-book, book-to-song or song-to-movie transfer. The three domains validate applicability of the decision mechanism independently.
- The fixed five-item list stays unchanged in the acquisition experiment. Its conditional certificate concerns the first item; ranking by individual minimax-regret scores does not solve optimal five-item set recommendation.
- Worldwide originality remains unverified. Hierarchical multi-label music genres are explicitly prior art in the AcousticBrainz source, not our invention. The candidate contribution is the specialized uncertainty formulation and structural-fault bound described in the existing derivation.
- The label-proxy, limited-profile and popular-item subsets do not establish semantic intent understanding, causal satisfaction, universal cold-start performance, fairness, long-tail exposure or an SLM improvement.

## Run commands

```bash
# First download the public sources in a clean local environment.
.venv-research/bin/python scripts/fetch_domain_holdout.py
PYTHONPATH=apps/api:ml/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-research/bin/python -m recros_ml.research.domain_holdout prepare book
PYTHONPATH=apps/api:ml/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-research/bin/python -m recros_ml.research.domain_holdout validate book
PYTHONPATH=apps/api:ml/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-research/bin/python -m recros_ml.research.domain_holdout test book
# Repeat prepare/validate/test with music. Completed runs refuse overwrite.
.venv-research/bin/python scripts/report_three_domains.py
```

Replication requires a clean separate checkout or saved output copy; preserve the existing frozen protocols and source windows. The source hashes, per-profile predictions, validation grid, query traces, full-catalog predictions and comparison report are saved. Runtime figures exclude fitting, source I/O and any real annotation service.

## Primary sources and attribution

- [Goodbooks-10k, Zygmunt Zając](https://github.com/zygmuntz/goodbooks-10k)
- [Last.fm 1K original README and permitted academic mirror](https://github.com/eifuentes/lastfm-dataset-1K)
- [AcousticBrainz genre dataset, Bogdanov et al.](https://mtg.github.io/acousticbrainz-genre-dataset/data/)
- [AcousticBrainz public label release](https://zenodo.org/records/2553414)
- [EASE, Harald Steck](https://arxiv.org/abs/1905.03375)
- [Original movie held-out result](../heldout/RESULT.md)
- [Derivation and attribution](../DERIVATION.md)

