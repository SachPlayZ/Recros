# October 15 presentation script and viva

Use [the twelve-slide deck](deliverables/Recros_milestone2_final.pptx). This script matches
its order. Aim for seven to nine minutes plus a three-minute demonstration.
Detailed citations and limitations are also in the speaker notes.

## 1. Recros

“Our project studies recommendations across movies, books and individual songs.
A common theme does not always explain why someone liked a work. We now separate
what the user wants from what the candidate's source material supports, and let
the system ask, inspect, recommend or abstain.”

## 2. Data recovery and scale

“We recovered and verified the source datasets. There are 222,896 normalized
works and over twenty million movie ratings. A text index covers 50,066 movie/book
summaries; fixed queries select an evidence bank of 210 works. The song source has
acoustic metadata rather than narrative summaries, so six separately sourced
tracks support this demo.”

Only movies provide real user interactions. A large catalogue is not a new
cross-domain preference test, and not every indexed work has been annotated.

## 3. Representation diagnosis

“One participant liked and disliked films that our concept representation mapped
to the same feature. A deterministic classifier using that identical vector cannot
reproduce both labels. This exposed information loss before planning. Genre
metadata separated this observed pair; fitting these ten examples would not
establish generalization.”

This is a counting identity. It does not apply to models receiving richer text,
titles, item IDs or other distinguishing inputs.

## 4. Interpretation and decisions

“DeepSeek interprets public summaries offline. The runtime checks exact excerpts
and source versions while treating missing features as unknown. The user selects
the current criteria. A small exact checker makes a conditional choice or
abstains. We also trained a tiny causal language model and can run its saved
weights locally.”

The criteria are inquiry, unease, interiority and connection: source-feature
proxies, not guarantees of engagement, scariness or relatability. The student
pipeline's evidence gate depends on teacher passages.

## 5. Evidence-removal demonstration

“For inquiry and an unsettling atmosphere in a book, the bank selects Vanishing
Acts and shows two supporting phrases. Removing its atmosphere claim changes the
choice to Annihilation, with the same shortlist. With only credits, it abstains.”

Run [the live sequence](FINAL_HANDOFF.md). The starting title provides context;
explicitly selected criteria determine the request. The system does not infer an
unspoken reason from the title.

## 6. Development source-reading comparison

“On eighteen supplied passages, DeepSeek features give mean NDCG at three of
0.979 compared with 0.902 for fixed BM25 queries, across eleven request types with
positive reference labels. The Codex assistant authored those labels before
extraction. This is agreement with a development reference, not independent
human recommendation accuracy.”

Four teacher labels were missed. Exact quoting does not establish correct
interpretation. See [label provenance](transfer/LABEL_PROVENANCE.md).

## 7. Tiny language model

“We trained 562,464 parameters from random initialization on local summaries and
teacher-labelled feature examples. The v2 run took about 115 seconds on CPU. Its
development F1 was 0.167, versus 0.148 for a TF-IDF student and 0.913 for the
teacher. We saved both checkpoints and report the weak result.”

There are 135 training records, 33 validation records and 4,000 pretraining
summaries. Music is absent from training. Evaluation titles were excluded from
training, but the passages had already been examined in development; v1 influenced
v2. We did not match teacher pretraining resources or establish general SLM capability.

## 8. Human reading pilot

“We then froze predictions and asked one participant to judge six paragraphs
with model answers hidden. Five were judged and one was unsure. DeepSeek matched
six of seven positive labels. The student matched none and added two labels.
Filtering removed those two labels but retained no positives. That is not success.”

These are new human judgments on development paragraphs. They measure supplied
text interpretation, not satisfaction after consuming works. N is one participant,
regardless of paragraph or binary-decision count. No training used these judgments.

## 9. Planning comparison

“Our twenty-four scripted tasks vary known versus unknown preferences and item
evidence across six domain directions. Exact planning, information gain and
DeepSeek tie at 24 scripted matches. A one-step decision-value policy abstains on
six complementary-information cases. This demonstrates the mechanism, without
showing superiority over the strong baselines.”

Preferences and action costs are hypothetical. The same twelve works recur;
there are no twenty-four human participants.

## 10. Separate movie-ranking pilot

“On a chronological movie-rating evaluation with 93 eligible users, discovery
increased long-tail share from 0.22% to 7.85%, while NDCG fell from 0.1547 to
0.1498 and recall fell too. Coverage did not improve. This is an exposure and
relevance tradeoff, not a Pareto improvement.”

Popularity NDCG was 0.1556. The paired NDCG interval includes zero. The May report
used a different task with leakage and weak-label limitations; its numbers are
not comparable to this temporal evaluation.

## 11. Contribution and next test

“We deliver a working discovery loop, a larger local data pipeline, an actual
tiny-model experiment, reproducible comparisons and visible failure analysis.
The next question is whether better representations and information acquisition
improve independently judged cross-domain usefulness.”

The next experiment needs real target judgments, matched candidates and question
budgets, stronger extraction training, and quality-versus-coverage measurement.

## 12. Attribution

“Evidence-based transfer has close prior art in EviSnap. Preference elicitation
and minimax regret are established methods. We attribute those ideas and present
our integration and bounded experiments as the contribution. Algorithmic novelty
and independent preference improvement remain open.”

## Likely viva questions

**What changed since milestone one?**
The original pipeline used nineteen features and LightGBM with template
explanations. We added actual hosted interpretation, source/version checks,
information-action planning, a causal language student, larger text retrieval,
evidence-removal controls and explicit evaluation.

**Why is the student weak despite the large datasets?**
Unlabelled summaries, acoustic metadata and movie ratings are different resources.
The compact model saw a small teacher-labelled set. Next-token training on a few
thousand summaries does not provide the hosted teacher's semantic knowledge.
Music is a distribution shift. Strong training fit with weak validation suggests
inadequate supervision; we have not isolated one causal explanation.

**Does the regret certificate guarantee a good recommendation?**
It certifies a calculation inside the declared feature/utility model and candidate
set, conditional on appropriate interpretation and intervals. It does not bound
true enjoyment or NDCG. A separate minimum-support rule prevents a lone weak
candidate from winning simply because it has no competitor.

**Is exact quoting a hallucination detector?**
It rejects fabricated excerpts and changed sources. A real excerpt can still be
interpreted wrongly. Semantic review is separate; our human pilot checks that
interpretation on a small supplied-text sample.

**Are shared users linking the three datasets?**
There are no verified shared-user histories across these sources. This prototype
transfers explicit criteria through text. Real preference-transfer evaluation
requires shared users or independently collected judgments.

**Why not train on twenty million ratings now?**
They support movie collaborative ranking but do not label the four source-reading
criteria or cross-domain tastes. The separate 93-user pilot used MovieLens 100K.
The 20M ratings were recovered and audited, not used in new neural ranking training.

**Is this novel, or plagiarism?**
We cite related methods and sources, identify our local implementation and avoid
invention claims for established theory. A novel algorithm or independent
usefulness gain has not been demonstrated. The present contribution is the
integrated system and transparent experiments.

**Why use DeepSeek by default in an LLM/SLM project?**
The student failed to match teacher extraction. We compare both and expose local
inference, while using the better observed interpreter for the demo. An unfavorable
small-model result is still an experiment; substituting it silently would weaken
the system and misrepresent the evidence.

## Updated deck and automatic product

Use `deliverables/Recros_milestone2_updated.pptx` (14 editable slides).
The automatic product is `/explore`: a source work produces five movies, five
books and five songs before refinement. Its 222,915-work catalogue and actual
metadata coverage are documented separately from the evidence-bank experiments.
The last additions cover LTO film/novel annotation, CATN's learned aspects and a
proposed comparison of flat tags, hierarchy and conditioned independent facets.
Do not claim that the hierarchy experiment has already been run or that every
catalogue item has Novel Updates tags.

## Focused research-result presentation

Use `deliverables/Recros_hierarchy_result.pptx` to present the new result in eight
slides: impossible flat-label world, exact shared-weight graph reduction,
276-state structural result, 2,048-facet oracle/runtime check, and the failure
and conservative repair when a hierarchy relation is wrong. Speaker notes state
the full assumptions, data provenance and established component precedents.

The live page is `/hierarchy`. Toggle the toy structural-fault allowance from 0
to 1, then inspect a post hoc film/book case and its flat-model witness. This
is a controlled model demonstration. Avoid describing 21.7% tighter bounds as
an accuracy gain or a zero model gap as certified enjoyment.
