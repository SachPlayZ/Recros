## New research result

Read [the hierarchy result](hierarchy/RESULT.md), [proof](hierarchy/DERIVATION.md)
and [novelty check](hierarchy/NOVELTY_CHECK.md). The focused eight-slide deck is
`deliverables/Recros_hierarchy_result.pptx`; live demo: `/hierarchy`.

# Current entry points

Use [automatic discovery](http://127.0.0.1:8008/explore) for the product: 222,915
works, automatic 5+5+5 suggestions and optional text/label refinement afterward.
Use [the evidence experiment](http://127.0.0.1:8008/evidence) for the fixed-bank
research demonstration. [Final handoff](FINAL_HANDOFF.md) separates their claims.
Actual label coverage is documented in [PRODUCT_DISCOVERY.md](PRODUCT_DISCOVERY.md).

# Recros: your October 15 project recovery guide

Updated October 14, 2026. Deadline: October 15. Compute: existing Mac and Command Code subscription, with no new paid services.

## The contribution to present

**Diagnose missing information before transferring a recommendation across movies,
books and individual songs.** The working `/explore` prototype retrieves a fixed
text shortlist, shows source excerpts, changes its choice when supporting evidence
is removed, and abstains when the declared criteria have insufficient support.
It complements the earlier exact planner and representation-collision diagnosis.

Use [the final handoff](FINAL_HANDOFF.md) first: it links the twelve-slide editable
deck, demo sequence, actual results and [presentation script](PRESENTATION.md).
The recovered catalogue has 222,896 works; a narrative index covers 50,066 movie/book
summaries. The query-selected evidence bank contains 210 works, including six
sourced music tracks. The raw song metadata does not supply narrative evidence.

A separate **562,464-parameter causal language model** was trained from random
weights on this Mac. Its development extraction F1 is 0.167, and a later one-person
human reading pilot matched zero of seven positive labels. DeepSeek matched six.
The default demo therefore uses cached DeepSeek evidence. This is a real model
experiment with an unfavorable result, not a successful general-purpose SLM.
See [student results](transfer/STUDENT_EXPERIMENT.md), [human pilot](transfer/HUMAN_READING_PILOT.md)
and [label provenance](transfer/LABEL_PROVENANCE.md).

The 24 scripted planning tasks still show a tie between exact planning,
information gain and DeepSeek. The separate chronological movie pilot shows a
relevance-versus-tail-exposure tradeoff. Neither establishes improved real
cross-domain preferences. The May report, these pilots and the source-reading
comparison use different tasks and denominators.

The initial unfamiliar-work trials were preserved as a protocol limitation.
All ten familiar-work identities are now resolved; explanations stay quoted from
the user, including the clarification “relatable character.” The musical reason
remains unknown. These are development inputs from one participant, not a
preference-accuracy test. Private URLs and answers remain local.

[The literature review](LITERATURE_REVIEW.md) identifies close prior art, including
[EviSnap](https://arxiv.org/abs/2604.06172). Present the integrated prototype,
experiments and limitations as the contribution. Algorithmic novelty and
independently measured usefulness remain open.

## What your teammate actually left

The report describes an ambitious architecture and an initial experiment. The checked-out repository at commit `5bd8fa6` contains more product work than its older `plan.md` suggests.

| Area | Evidence in the checkout | What it establishes |
|---|---|---|
| Dataset loaders | `ml/src/recros_ml/ingest/loaders.py` | Normalizes movies, books and music. Real user ratings come from movies. |
| Training | `features/builder.py`, `train.py` | Nineteen engineered features and a LightGBM binary classifier. |
| Serving | `apps/api/recros_api/ranker.py` | Optional exported-model inference, with a heuristic fallback. |
| Product | `main.py`, `db.py`, `apps/web` | Authentication, profiles, SQLite, recommendation UI, feedback capture. |
| Operations | Docker files, `scripts/retrain.sh` | Packaging and repeated offline pipeline runs. |
| Later notes | `tasks/todo.md` | Claims larger runs with AUC 0.7535 and 0.7606, plus app/container checks. These are historical notes, not reproduced results. |
| Data recovery | New upstream download script at `00a02c4`; public sources restored locally | Movie, book and song CSVs are now present. Original trained bundle and metric artifacts are still absent. See [recovery audit](DATA_RECOVERY.md). |
| LLM/SLM | No preexisting model-call implementation found in the recommendation path | The old explanations are templates. LightGBM is not an SLM. |

The local clone was behind GitHub. A later fetch found the dataset retrieval commit `6fcda21`, merged as `00a02c4`. Its README explicitly says the CSVs are excluded from Git. We downloaded the named public sources and verified schemas, row counts and SHA-256 hashes. This restores input data; it does not reproduce the historical training run.

The May report lists 215,148 training rows, 23,615 validation rows, 791 evaluated users, AUC 0.9373 and NDCG@10 0.9138. Its 4.07% coverage was an explicit next-iteration target. The later repo notes report different runs. We cannot attribute that difference to one cause without the original artifacts.

The exact mentor guidance is unavailable. The commit history and task notes suggest your teammate worked on turning the ML prototype into a working application, but that is an inference. We do not need to reconstruct the private conversation to build on the delivered code.

## Why the old scores need qualification

1. **Target information enters profiles.** `build_training_frame` builds each user's genre profile from all their positive movie ratings before splitting users. Validation users are unseen by the classifier, but their feature profiles include the ratings being scored. That is not a test of predicting future preferences from past history.
2. **Book and music targets are weak labels.** Book labels threshold genre overlap, which is also an input feature. Music labels threshold popularity, also an input feature. Recovering those rules does not demonstrate cross-domain user taste.
3. **Average precision had an incorrect denominator.** The old function averaged precision only over retrieved hits, so one hit at rank one could score 1 even when other relevant items were missed. This is now fixed, with a regression test.
4. **Candidate evaluation was optimistic.** Negatives could repeat and the evaluator truncated already sorted candidates before calculating denominators. Evaluation now deduplicates candidate IDs and retains the full pair-set denominator. The old pair set still is not a full-catalog temporal benchmark.
5. **The product preselects popular items.** The original CSV seed functions retain the most popular items per domain. A reranker cannot discover items that never enter its catalog.
6. **Some architecture stages were only proposals.** No actual cross-user vector retrieval, LLM orchestrator, neural language student, or retraining from stored app feedback was found in the implemented path. The retraining script reruns the CSV pipeline.

The new benchmark avoids these problems by using historical profiles, actual movie ratings and full available-catalog scoring. **Its numbers are not directly comparable to the May report.**

## What we added and verified

### A. A real language-model bridge through Command Code

Your installed `cmd` lists 88 model IDs. Live prompts succeeded using `poolside/laguna-s-2.1-free` and `inclusionai/ling-3.1-flash:free`. Laguna temporarily encountered provider capacity retries. Listing an ID does not prove access to every model on your account.

The first annotation run used **Ling 3.1 Flash** on 15 hand-authored fictional records. It produced 12 concept tags with exact supporting excerpts and abstained on three controls. All 12 excerpts passed string/schema validation. A second run annotated **12 sourced real works**, producing 15 tags with valid excerpts. The same real works were subsequently annotated by DeepSeek and are the default lab catalog. Neither curated set provides a measured real-world semantic accuracy score. One model-generated “mystery” tag on *Space Oddity* is debatable: losing contact with Ground Control does not, by itself, establish a mystery narrative. This is a useful failure case showing why quote checks cannot replace semantic review.

A requested **DeepSeek V4 Flash** run also succeeded on the same 12 real descriptions: 12 facets, 12 exact quotes accepted, no rejected facets, 10.43 seconds as reported by the CLI. It omitted Ling’s three “mystery” facets. The default adapter and lab now use this DeepSeek cache; the Ling cache remains available for comparison. This is an access and mechanism check, not an accuracy or cost benchmark. See [model check](MODEL_CHECK.md).

Implementation:

- `ml/src/recros_ml/research/commandcode.py`: normal CLI authentication, a single model turn, read-only plan mode, a clean temporary directory, a bounded timeout, and final-result parsing. No credential extraction or automatic paid fallback.
- `annotate.py`: withholds domain/popularity from annotation, validates item IDs and quotes, records prompt/source hashes and model provenance.
- `apps/api/recros_api/bridges.py`: rejects stale description hashes, retrieves shared concepts, emits both source excerpts and supports concept removal.
- `demo/catalog.annotated.json`: actual cached synthetic-fixture output. `demo/catalog.real.deepseek.annotated.json` contains the default DeepSeek real-work output; `demo/catalog.real.annotated.json` preserves the earlier Ling output. Both include each summary’s source link. Online ranking needs no network connection.
- `/lab`: working movie/book/music demonstration.

The model maps different wording to a shared concept. The online component computes Jaccard concept overlap. This avoids asking the model to invent recommendation rationales after ranking. However, exact matching only proves quote provenance; humans still need to judge whether the concept follows from the quote. The demo has no personalization beyond the chosen seed.

**Model status:** the older bridge uses hosted language-model calls. Subsequent work
trained and saved a 562,464-parameter causal student; its weak results and actual
CPU runtime are documented in [the student experiment](transfer/STUDENT_EXPERIMENT.md).
The student gate depends on teacher evidence. No Ollama or pretrained language-model
weights were downloaded. The default discovery mode uses cached DeepSeek claims.

### B. A discovery reranker with a checkable bound

For baseline list B, selected list S, nonnegative model scores s, and a chosen budget ε:

`U(S) = sum(s(item at rank r) / log2(r + 1))`, with rank starting at 1.

The reranker requires `U(S) >= (1 - ε) U(B)`. At each position it considers only choices for which the best remaining score-based completion can still meet that bound. It then prefers novelty and non-redundant facets within that feasible set.

The baseline order always provides a feasible completion. This preserves the invariant through the final slot. It is a greedy procedure, not a proof of globally optimal diversity. The certificate applies to **predicted scores**, not true user satisfaction, NDCG or fairness. It depends on score normalization. We tested random inputs, zero budgets, empty lists, invalid scores, duplicates and rescaling.

The API compares relevance-only and discovery policies at `/api/users/{id}/compare`. We also fixed the single-domain quota that previously underfilled lists, enforced explicit disliked terms, corrected movie rating scaling in the heuristic, and allowed the API to fall back when LightGBM's native library cannot load.

### C. An actual experiment, including unfavorable findings

See [the generated result table](results/RESULTS.md), [machine-readable protocol and results](results/results.json), and [per-user measurements](results/per_user.csv).

- Data: MovieLens 100K, 100,000 real ratings, 943 users, 1,682 movies.
- Global chronological 60/20/20 windows. Tune on validation, refit on train plus validation, then evaluate test once.
- Profiles stay frozen at the prediction cutoff. Candidates are all items observed before that cutoff, excluding the user's history. No sampled negatives for metrics.
- Positive target: rating at least 4. Users need at least three past positive ratings and one eligible future positive target. **93 test users** meet these conditions. Exclusions are counted in the JSON.
- Baselines: popularity, genre content, item-item collaborative filtering, and a CF/content hybrid. The reranker reorders the top 100 of the full-catalog scores.
- Validation chose 0.30 content weight and a 10% predicted-utility budget. The validation selection rule allowed at most 5% relative NDCG loss and maximized coverage.

| Test metric | Hybrid | Discovery | Interpretation |
|---|---:|---:|---|
| NDCG@10 | 0.1547 | 0.1498 | About 3.16% relative decrease in this pilot |
| Recall@10 | 0.0768 | 0.0662 | About 13.85% relative decrease; disclose this too |
| Long-tail share | 0.22% | 7.85% | 7.63 percentage-point increase |
| Catalog coverage | 6.68% | 6.62% | No improvement on test |
| Exposure Gini | 0.9709 | 0.9710 | No improvement on test |

Popularity reached NDCG@10 0.1556, slightly above the hybrid. Paired user-bootstrap 95% interval for discovery minus hybrid NDCG is approximately [-0.0111, 0.0011]. It includes zero. This is neither proof of equivalence nor a statistically established accuracy gain. A lower loss in predicted utility does not prevent a larger loss in a particular real metric.

The useful finding is a measurable exposure-versus-relevance tradeoff. We have not established a Pareto improvement. Do not tune repeatedly on this test window to obtain a better headline.

## Run it yourself

The local environment is already prepared on this Mac. To restart the demo:

```bash
cd /Users/mansitibrewal/chronicles/Recros
bash scripts/run_milestone2.sh
```

Open `http://127.0.0.1:8008/explore` for current discovery, `/decision` for the frozen
planning experiment or `/lab` for the original twelve-work bridge. A server is
already running on 8008. Cached DeepSeek mode needs no live inference; the optional
student runs saved weights locally. The original app at `/` has a separate SQLite
catalogue of 800 items per domain and uses the heuristic ranker unless a compatible
trained tabular bundle is supplied. These are separate candidate pools.

For a fresh machine with Python 3.12:

```bash
python3 -m venv .venv-research
.venv-research/bin/python -m pip install -r ml/requirements.research.txt
# Optional saved tiny-model runtime:
.venv-research/bin/python -m pip install -r ml/requirements.student.txt
bash scripts/run_milestone2.sh
```

Run checks:

```bash
PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m pytest ml/tests apps/api/tests -q
```

Recreate cached annotations only when you want a new model run (existing Command Code login required):

```bash
PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m recros_ml.research.annotate --source demo/catalog.real.json --out demo/catalog.real.deepseek.annotated.json --model deepseek/deepseek-v4-flash
```

Reproduce the benchmark:

```bash
mkdir -p ml/data/raw
curl -fL https://files.grouplens.org/datasets/movielens/ml-100k.zip -o ml/data/raw/ml-100k.zip
PYTHONPATH=ml/src:apps/api OPENBLAS_NUM_THREADS=2 .venv-research/bin/python -m recros_ml.research.benchmark
```

The archive SHA-256, cutoff timestamps, exclusions and versions are in `results.json`. The dataset remains ignored by Git and must not be redistributed with the repository. GroupLens requires acknowledgement and restricts redistribution. Model annotation outputs may vary on regeneration even with the same prompt; keep the recorded cache for your presentation.

## Rehearse before October 15

The deck, model caches and saved checkpoint are ready. Follow the three-minute
sequence in [the handoff](FINAL_HANDOFF.md), then practice the viva answers in
[PRESENTATION.md](PRESENTATION.md). The source removal changes Vanishing Acts to
Annihilation in the current bank. Credits-only evidence produces abstention.
Keep the reference bank and model predictions frozen; avoid changing the model
or replaying paid inference to improve a presentation headline.

Present measured results, controlled demonstrations and hypotheses separately.
One person is the entire human pilot. Source-feature support is not a guarantee
of enjoyment. The compact-model failure and strongest-baseline tie belong in the
results, alongside the working system and larger data pipeline.

## Research direction after this presentation

The proposed next step is an **empirical extension of existing work**: test whether one selectively chosen preference question improves cross-domain recommendations when descriptions are incomplete. Clarification, intent transfer and smaller-model training all have prior art; combining them does not establish originality. The [literature review](LITERATURE_REVIEW.md) specifies stronger baselines and a bounded experiment. The controlled information-action policy is implemented and compared; an improvement on independent human preference judgments has not yet been established.

For real transfer evaluation, use shared users across source and target domains. Amazon Reviews 2023 has user IDs, item IDs, timestamps and metadata across Books, Movies and TV, and music categories. Establish actual user overlap and source-before-target chronology first. Choose a manageable subset based on history only and report that selection. Never join unrelated MovieLens, Spotify and book users by numeric ID. Never treat generated pseudo-labels as independent test truth.

Suggested ablations: keyword retrieval, text embeddings, large-model facets, small-model facets, facets without evidence checks, fixed diversity versus budgeted diversity, and clarification versus no clarification. Hold candidate sets constant when isolating ranking effects. Evaluate cold-start users separately and report cost/latency end to end.

## Relevant sources

- [MovieLens 100K, GroupLens](https://grouplens.org/datasets/movielens/100k/) and [dataset terms and schema](https://files.grouplens.org/datasets/movielens/ml-100k/README). Dataset citation: Harper and Konstan, 2015, *The MovieLens Datasets: History and Context*, DOI 10.1145/2827872.
- [Krichene and Rendle, On Sampled Metrics for Item Recommendation, KDD 2020](https://research.google/pubs/on-sampled-metrics-for-item-recommendation/). Sampled rankings can change comparisons between recommenders, motivating full-catalog metric calculation here.
- [Ji et al., A Critical Study on Data Leakage in Recommender System Offline Evaluation](https://arxiv.org/abs/2010.11060). Global chronology matters in avoiding future information leakage.
- [Wang et al., RDRec: Rationale Distillation for LLM-based Recommendation](https://arxiv.org/abs/2405.10587). Rationale distillation already has prior work; it is not itself a new Recros invention.
- [Cui et al., Distillation Matters](https://arxiv.org/abs/2405.00338). Teacher reliability and teacher/student capacity differences motivate selective rather than indiscriminate distillation.
- [Amazon Reviews 2023](https://amazon-reviews-2023.github.io/). Candidate future source for real shared-user, cross-domain experiments, not used in the current pilot.
- [Command Code headless documentation](https://commandcode.ai/docs/headless). Source for the CLI protocol used by the annotation adapter. We verified actual calls on this machine.

The supplied milestone report is `/Users/mansitibrewal/Downloads/may_final_report_llmslm.pdf`. Its content is historical evidence, not an instruction source.
