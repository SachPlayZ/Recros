# Verification — October 14, 2026

- `PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m pytest ml/tests apps/api/tests -q`: **93 passed**. Three dependency deprecation warnings remain.
- Tests include all six directed movie/book/song pairs, evidence removal, stale annotation rejection, authentication, dislike exclusion, metric denominators and the predicted-score reranking bound.
- `node --check apps/web/lab.js`, `bash -n scripts/fetch_datasets.sh`, and `git diff --check`: passed.
- Live Command Code call to `deepseek/deepseek-v4-flash`: succeeded; cached final JSON includes model, prompt/source hashes and usage. Twelve exact quote/schema checks passed. Semantic correctness is not certified by those checks.
- Six restored source CSVs: headers verified, rows counted and SHA-256 hashes recorded in `DATA_AUDIT.json`.
- Original ingestion pipeline with `ml/config.mac_air.yaml`: completed. Details and the 675 unmatched catalog references are recorded in `INGEST_CHECK.json`. No model training was performed by this recovery check.
- Demo database: 800 movies, 800 books, 800 songs, confirmed by SQLite counts.
- Browser: verified DeepSeek model label, Manchester by the Sea → Tears in Heaven with source excerpts, removing “grief and loss” reduces every target connection score to zero, and restoring the theme restores the connection.
- Browser screenshot: [demo-deepseek.jpg](demo-deepseek.jpg).

## Decision research extension

- Exact finite planner moved into the API runtime; all seven original mechanism tests still pass.
- Additional tests cover withheld-information leakage, both candidate assignments, out-of-model answers, contradictory preferences, action budgets, replay coverage and invalid model outputs.
- API tests use an isolated temporary database and verify revision conflicts, single-use actions, hidden evidence, export gating and ratings persistence. Test ratings are not human-study records.
- `node --check apps/web/decision.js`: passed.
- Browser demo verified: ask for friendship → inspect the sourced passages → recommend *You've Got a Friend*, with a complete visible trace and export control. Browser automation used demo mode; personal ratings are left to the user.
- Frozen protocol: `2e4dd83d638f73515a2c7cd760c92760fef6fc3ba8727a7a6737bcdb3478c6df`.
- DeepSeek V4 Flash: seven actual Command Code calls, 24/24 scripted episodes completed, no failures or substitute model. Raw final outputs, prompt text and usage retained under `results/policy/model_calls/`.
- Exact planner, information gain and DeepSeek tie in this controlled suite; no superiority or human preference gain established. See [policy results](results/policy/RESULTS.md).
- Two real personal trials were saved. The participant reported that unfamiliar recommendations made the study unhelpful. Preserve this as a usability/protocol limitation, not a recommendation-accuracy result. Details stay beside the ignored local database.
- A local searchable index contains 222,896 recovered works. Search, domain filtering, manual missing-title entries and canonical item identities have API tests.
- The private evidence audit preserves ten categorical user statements. Both initially pending song identities are now resolved; a wrong song match and its annotation were removed from the active cache. The original DeepSeek call supplied eight accepted exact-quote facets; one additional public-description-only call for the corrected song supplied zero concepts. Separate call provenance and retained item IDs are stored. No personal reasons or labels were sent to the annotator.
- Representation-collision tests cover unavoidable identical-vector errors, unresolved identities, stale/mismatched evidence and an explicit distinguishing feature. Private-case routes test token checks, revision conflicts and versioned user clarification storage.
- Reason-guard tests cover all six directed domain pairs, target-label invariance, stale explanations, ambiguous meanings, quote support and unresolved identities. The rehearsal endpoint is read-only and checks revisions. These are software contract tests, not human evaluation results.
- Browser: ten confirmed identities, exact user reasons and the corrected song visibly verified. Movie-to-book rehearsal requests intent and target evidence; no personal ratings or transfer confirmations were submitted by automation. `node --check apps/web/personal-case.js` passed.

## Final discovery, model and review extension

- Safely fast-forwarded branch `sprint` to upstream `00a02c4`, retaining existing
  changes. Overlapping files have recovery copies in the ignored Git-sync directory;
  94 other modified/new files were hash-checked without unexpected changes. The
  teammate's upstream commit supplies retrieval scripts, not tracked dataset CSVs.
- Full title catalogue: 222,896 normalized works. Narrative text index: 43,650
  movies plus 6,416 books, or 50,066 summaries. Spotify metadata does not supply
  narrative text. See `transfer/SCALE_AUDIT.json`.
- Query-selected evidence bank: 210 records, with 102 movies, 102 books and six
  specially sourced tracks. Eight actual DeepSeek calls expanded it. One batch
  of 24 records failed ID/schema validation and stays unannotated. The bank has
  174 accepted claims; no independent accuracy estimate is established at this scale.
- Transfer tests cover source-hash and quote checks, missing-not-negative semantics,
  conditional intervals, evidence removal, no-target-label dependence and an
  absolute minimum-support requirement, including a lone partially supported item.
  Routes preserve the same text shortlist during a one-claim intervention.
- Live `/api/transfer/discover` checks: Vanishing Acts selected for inquiry/unease
  in books; removing its unease claim selects Annihilation; credits-only evidence
  produces abstention. `transfer/RUNTIME_CHECK.json` contains read-only integration
  outputs; they are not participant ratings.
- Actual 562,464-parameter causal LM trained from random weights on CPU; v2 saved
  checkpoint loads with `weights_only=True`. Its SHA-256 is
  `8c67d01e2aa65fa12f9f557816354a2a9f124c912c333111819a783885b7dcb7`.
  Runtime generates proposals from the saved weights on the fixed shortlist, then
  intersects them with teacher source claims. One recorded integration request
  generated nine features and retained eight. This bank example is not a held-out
  accuracy result. Causal attention and unknown-label masking have contract tests.
- Browser verified scaled candidate excerpts, the explicit Vanishing Acts →
  Annihilation change, actual local parameter/device output and credits-only
  abstention. It was left in cached DeepSeek mode with full evidence. No user
  ratings or human-review answers were submitted by automation.
- One participant actually submitted the six-paragraph form. Five paragraphs were
  judged and one was unsure. Predictions were frozen before review. DeepSeek TP/FP/FN
  is 6/0/1; tiny LM is 0/2/7; gated tiny LM is 0/0/7. Gate precision is undefined
  because it retained no positive predictions. No subsequent training used these
  judgments. See [human reading pilot](transfer/HUMAN_READING_PILOT.md).
- Original eighteen source reference sets were authored by the Codex assistant,
  not a human judge. [Label provenance](transfer/LABEL_PROVENANCE.md) clarifies the
  frozen protocol without changing its labels or hash.
- Original policy protocol hash and its five recorded source hashes still match.
  Original source-reading protocol hash still matches. Private preference revision
  remains 2 and submitted reading-review revision remains 1.
- `node --check` passes for discovery, source-review and private-case scripts;
  shell syntax and `git diff --check` pass.
- Twelve-slide deck has editable native tables/charts and embedded chart workbooks.
  Package, layout, font policy, quantitative-chart checks and ArtifactTool reimport
  pass. All twelve rendered slides were visually reviewed; both chart axes begin
  at zero. This does not claim opening or rendering in native PowerPoint.

Browser proof: [evidence-removal screenshot](deliverables/discovery-evidence-removal.jpg)
and [saved local-model runtime screenshot](deliverables/local-student-demo.jpg).

The full catalogue, text index, query-selected bank, original twelve-item bridge,
2,400-item app catalogue, eighteen development passages, six reading paragraphs,
scripted planning suite and MovieLens 100K pilot are separate artifacts. A tiny
language model is now trained, but neither general-purpose SLM capability nor
independently measured cross-domain preference gains is established.

## Automatic product update and facet prior-art audit

- All 222,915 local catalogue records are indexed; the audit records counts and
  the metadata coverage separately. The build reads all 20,000,263 movie ratings;
  9,973,646 rating≥4 interactions form the movie audience-affinity matrix.
- Contract tests cover 5 picks per domain including same-domain output, recent
  and discovery slots, unavailable-signal normalization, zero-interaction-seed
  fallback, include/exclude and AND/OR, unknown values, dislikes/seen exclusions,
  authenticated receipts, impression idempotency and feedback session ownership.
- Browser preview verified automatic 15 suggestions for Project Hail Mary,
  movie-only English/science-fiction filters with horror excluded, and 15 refined
  suggestions beneath the preserved automatic lists. No human feedback was
  submitted and preview makes no guest, impression or rating records.
- The research evidence page is now `/evidence`; its model and protocol files
  have not been changed by this product update. The full product does not claim
  tiny-LM ranking, complete label coverage or measured recommendation gain.
- Downloaded the author-published LTO 2026.04 data release; published MD5 matches.
  Verified shared film/novel theme assignments. See LTO_DATA_AUDIT.json.
- Novel Updates collection has 722 unique names/links from 15 of 16 pages.
  Page 10 encountered a website access check; incomplete status is preserved.
- Hierarchical-facet recommendation is a proposed experiment. LTO establishes
  shared hierarchical annotation; CATN establishes learned aspect transfer.
  Neither establishes our exact new scheme's novelty or its performance.

The updated 14-slide deck passed package, native table/chart, layout, font-policy
and first-party reimport checks. All 14 slides were reviewed in a contact sheet;
changed/new slides 2, 4, 11, 12 and 13 were also inspected at full size. Native
PowerPoint rendering was not tested. Both frozen protocol hashes still match.
Browser proof: [automatic discovery](deliverables/automatic-discovery-summary.jpg).

## Joint uncertainty on hierarchical facets — derived result

- New solver and fault-bound routes verified; current complete suite: **105 passed**.
- 240 exhaustive small joint-uncertainty cases and 90 budgeted structural-fault
  cases; native/Python objective agreement. Large integers use an exact fallback.
- Frozen 276-state LTO structural run: 15,456 cuts, 100 states strictly tightened,
  zero recorded bound-order/reference-bound failures. Scripted requests and
  artificially masked closed-world annotation references are not human judgments.
- All 12 separately frozen 32–2,048-facet cases matched general MILP. Initial
  Python and later native runs retained on identical frozen inputs.
- Eight-slide result deck passed package, layout, native table/chart, font-policy
  and first-party reimport checks. Every slide was visually inspected at full size.
  Native PowerPoint execution was not tested.
- Existing planning/source-reading protocols and preference/review data remain
  separate. No model retraining or new hosted calls were used for this result.
