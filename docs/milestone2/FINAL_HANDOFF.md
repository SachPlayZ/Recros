# Recros presentation handoff

Ready October 14, 2026. Presentation: October 15. Use the existing Mac and Command
Code subscription. The demo works from cached source evidence; its optional tiny
model runs locally.

## Open these first

- [New eight-slide research result](deliverables/Recros_hierarchy_result.pptx): proof, structural experiment and fault-bound demonstration.
- [Live hierarchy study](http://127.0.0.1:8008/hierarchy), [measured result](hierarchy/RESULT.md) and [derivation](hierarchy/DERIVATION.md).

- [Updated editable fourteen-slide deck](deliverables/Recros_milestone2_updated.pptx), with speaker notes and citations.
- [Slide script and viva preparation](PRESENTATION.md).
- [Public discovery demo](http://127.0.0.1:8008/explore).
- [One-person reading result](transfer/HUMAN_READING_PILOT.md).
- [Verification record](VERIFICATION.md).

The private familiar-work page links to discovery using your ten known anchors.
Its token is in `apps/api/data/personal-case/access-token.txt`; keep that URL out of
public slides. Project Hail Mary refers to the confirmed film; Percy Jackson
remains a series. The unknown musical reason stays unknown.

## Automatic product demonstration

1. Open `/explore`: Project Hail Mary starts with 5 movies, 5 books and 5 songs.
2. Show the source-domain movie list, the recent-release slot and the less-popular slot.
3. Search another title in the 222,915-work catalogue; familiar anchors are optional.
4. Scroll below the automatic lists to refine with text or sourced label filters.
   A movie-only filter keeps books and songs available. The original picks stay above.
5. Open the label-coverage disclosure. Book/song language and song genres are missing;
   the app does not invent them. Impressions are not user satisfaction.

See [product details](PRODUCT_DISCOVERY.md) and [hierarchical-facet prior art](HIERARCHICAL_FACETS_RESEARCH.md).

## Three-minute evidence demonstration

1. Open `/evidence`. Use the public starting film **2001: A Space Odyssey**, target
   **Books**, cached **DeepSeek**. Choose **Inquiry** and **Unease** and find candidates.
2. The current scaled bank selects **Vanishing Acts**. Read its two short supporting
   excerpts. This is a conditional suggestion for these declared criteria.
3. Remove its unease claim. The fixed shortlist stays the same and the selected
   work changes to **Annihilation**. Restore the claim to restore the original state.
4. Use the credits-only evidence control. The system abstains because credits do
   not support the requested source features. Restore full evidence afterward.
5. Show the text-only comparison and the decision trace. Optionally switch to the
   tiny model to show saved weights actually running on CPU. Its evidence gate
   depends on teacher passages, and its independent human reading outcome was weak.

Do not rate these recommendations during the demonstration or call this personal
satisfaction. Explicit user-selected criteria are a proposed operationalization,
not a guarantee of fear, engagement or relatability.

## Concrete progress

| Artifact | Verified scope |
|---|---|
| Automatic product catalogue | 222,915 works, including 19 sourced additions; 20,000,263 movie ratings |
| Automatic ranking | 5 picks in each domain; all seven report weights with availability handling |
| Narrative index | 50,066 movie/book summaries |
| Evidence bank | 210 works: 102 films, 102 books, six sourced tracks |
| Scaled extraction | Eight actual DeepSeek calls; 174 accepted claims; one failed 24-record batch |
| Tiny language model | 562,464 parameters, trained from random weights; saved local checkpoint |
| Reading pilot | One person, five judged paragraphs and one unsure; teacher TP 6, student TP 0 |
| Planning suite | 24 scripted tasks; exact planner, information gain and DeepSeek tie |
| Movie pilot | 93 eligible test users; greater tail share with lower relevance |
| Software checks | 105 tests pass; actual local inference and evidence controls verified |

The 170,653 source song records have acoustic metadata, not narrative summaries.
The narrative bank contains six specially sourced tracks; it does not semantically
annotate the entire song catalogue. There are no real shared-user preferences
across the three recovered datasets. Never join their unrelated user IDs.

The strongest contribution to explain is the implemented diagnosis and handling of
missing information, with transparent experiments on source interpretation,
language-model capacity and decision planning. The new hierarchy study has a project-derived tractability proposition and a
conservative structural-fault bound. Worldwide originality, general SLM capability
and independently measured recommendation gains remain unestablished.
Closest prior work is attributed in the deck and [literature review](LITERATURE_REVIEW.md).

## Running and preserving it

```bash
cd /Users/mansitibrewal/chronicles/Recros
bash scripts/run_milestone2.sh
```

The server is already running on port 8008. Leave it running for rehearsal. If
port 8008 is occupied, check the existing server before launching another. Normal
discovery makes no hosted calls. Impressions are recorded locally; ratings are
written only when a person presses feedback controls. Preview mode writes neither. Do not regenerate
annotations or retrain during the presentation.

Git branch `sprint` now includes upstream `00a02c4`. The teammate pushed retrieval
scripts and documentation, rather than tracked CSV files. Existing local work was
preserved, with recovery copies in `apps/api/data/git-sync/20261014T074723Z` and
94 non-overlapping files hash-checked. No remote push was performed. Raw datasets,
checkpoints, credentials and personal records remain ignored; do not publish them.

The earlier May scores used a different evaluation with leakage and weak-label
limitations. Do not compare them numerically to the new chronological movie pilot.
For a defensible next milestone, gather independent target usefulness judgments,
hold candidates and question budgets fixed, and evaluate better source extraction
before attempting to claim compact-model substitution.
