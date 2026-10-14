# Recros four presenter rehearsal guide

Prepared for the graduation project presentation on 15 October 2026

The latest presentation contains eight slides. This guide assigns two slides to each of four presenters, gives a two minute first milestone recap, and provides scripts that keep every presenter's complete segment under five minutes. The scripts explain the measured result without claiming that recommendation accuracy improved. The technical handbook supplies the detailed explanations; the separate question bank prepares each presenter for follow-up questions.

## Presentation assignments and timing

| Presenter | Slides | Responsibility | Rehearsal target | Maximum |
| --- | --- | --- | --- | --- |
| Presenter 1 | 1 and 2 | Two minute first milestone recap, research question, datasets | 4 minutes 15 seconds | 4 minutes 50 seconds |
| Presenter 2 | 3 and 4 | Recommendation relevance and annotation effort | 4 minutes | 4 minutes 40 seconds |
| Presenter 3 | 5 and 6 | Who benefits and what fails under severe missingness | 3 minutes 45 seconds | 4 minutes 30 seconds |
| Presenter 4 | 7 and 8 | Validation decision, contribution and limitations | 4 minutes | 4 minutes 45 seconds |

The expected presentation lasts about sixteen minutes, plus questions. These are rehearsal targets, not measured recordings. Read at about 115 to 125 words per minute and allow pauses while pointing to tables. Presenter 1's recap occupies two minutes only. Their remaining time covers the current slides. Each individual slide speech is also shorter than five minutes.

## Difficulty ranking from hardest to easiest

These scores measure the difficulty of explaining and defending the actual content. They do not measure how difficult a slide looks.

| Rank | Slide | Difficulty | Why it is difficult | Preparation priority |
| --- | --- | --- | --- | --- |
| 1 | 7 Validation retains the reference ranking | 9 of 10 | Requires validation versus test, the zero theme weight, EASE and full catalog versus shortlist distinctions | Presenter 4 should master the zero weight caveat |
| 2 | 3 Ranking gains remain unestablished | 8 of 10 | Requires NDCG, paired confidence intervals and fair comparisons | Presenter 2 should practise interpreting one row aloud |
| 3 | 6 Severe missingness often prevents a certificate | 7 of 10 | Requires understanding what a conditional certificate does and does not guarantee | Presenter 3 should distinguish a failure to certify from an incorrect recommendation |
| 4 | 4 Small annotation savings in each domain | 7 of 10 | Requires regret, fixed recommendations and the difference between bits and actual calls | Presenter 2 should explain the experiment as a stopping rule |
| 5 | 8 What the three domain extension establishes | 6 of 10 | Likely to attract questions about novelty, cross domain evidence and the LLM or SLM | Presenter 4 should know the precise contribution and prior art |
| 6 | 2 Independent data and held out profiles | 5 of 10 | Requires data identity, split choices and historical profiles | Presenter 1 should know why books use a random split |
| 7 | 5 Only a minority of profiles save lookups | 3 of 10 | Primarily percentages, but the denominator differs from slide 4 | Presenter 3 should distinguish benefit frequency from mean saving |
| 8 | 1 Recros title slide | 2 of 10 | Introduces the question with little technical material | The spoken milestone recap raises Presenter 1's overall preparation load |

Presenter 4 has the hardest conceptual defence. Presenter 2 has the heaviest statistics. Presenter 1 has the broadest historical recap. Presenter 3 has the simplest chart but must explain failure honestly. Every presenter should read the shared foundations in the handbook before learning their own questions.

## Presenter 1 opening recap

Show slide 1 throughout this recap. Rehearse this block for two minutes. It covers all the first milestone's achievement categories, key measurements and unresolved evaluation targets. Detailed tables appear in the handbook so you do not have to read every decimal aloud.

### Two minute recap script

Our first milestone established a literature review, a hybrid architecture and a preliminary model for movies, books and songs. We identified eight challenges: cold start, sparsity, popularity bias, filter bubbles, feedback loops, explainability, domain isolation and unequal exposure.

We designed nine stages: onboarding, language interpretation, memory, retrieval, compact ranking, diversity and fairness adjustment, explanations and cross domain enhancement, output, and feedback. The proposed weights were thirty percent similarity, twenty similar users, fifteen genre, ten each novelty, diversity and fairness, and five recency.

The PDF reports a nineteen feature gradient boosted ranker, about 215 thousand training rows and 24 thousand validation rows. Its best iteration was 342 and AUC approximately 0.94. Across 791 users, NDCG exceeded 0.91, recall rose to approximately 0.96, and MAP ranged from 0.91 to 0.98.

It reported thirty five percent nonprimary recommendations, 2.40 domains on average, 4.07 percent coverage and novelty minus 2.98. Coverage and novelty were weaknesses. Strong baselines, provider fairness, explanation quality and online satisfaction remained open. Today's protocols differ, so the scores are not a direct before and after comparison.

### Slide 1 current research script

We then asked a narrower question: when item labels are missing, can genre and theme relationships prevent us from treating logically impossible combinations as real uncertainty?

For example, a space opera implies science fiction. A flat system may consider space opera present while science fiction is absent. Our method removes such impossible combinations when the hierarchy is correct. We derived an exact graph based calculation for the declared model, and tested recommendation relevance and annotation effort separately. I will now explain the datasets behind the latest results.

### Slide 2 script

The movie test combines MovieLens ratings with the Literary Theme Ontology. It uses 789 available films and 320 test profiles. The book test uses Goodbooks ratings, a three thousand book subset and 320 profiles. The song test uses Last.fm listening events joined to AcousticBrainz genre labels, with two thousand recordings and 181 listeners.

Movies and songs use earlier interactions as history and later interactions as outcomes. Books lack explicit timestamps, so the book experiment uses randomly separated ratings. Each profile supplies twenty known works. These are historical users in public datasets, rather than volunteers recruited by us.

Song joins use exact recording identifiers, because an artist name or similar title cannot reliably identify a recording. The users in the three datasets are unrelated. Testing a mechanism in three domains therefore does not establish preference transfer between those domains. Presenter 2 will explain the relevance and annotation results.

### Presenter 1 cue card

Eight problems; nine stages; seven weights; reported ranker and validation; coverage weakness; new uncertainty question; three independent datasets. Say “the PDF reports” when discussing the earlier results. Say “compact ranker” for the gradient boosted model, because a decision tree is not itself a language model.

## Presenter 2 scripts for slides 3 and 4

### Slide 3 script

This slide evaluates whether recommendations actually recover independently held out ratings or plays. We use NDCG at five, which rewards relevant items more when they appear near the top. A value of one means the ideal ordering under that evaluation's relevance labels. It is not a probability that the user will enjoy a recommendation.

Within each row, every method receives the same sixteen candidates. The reference is our validation selected historical recommender. EASE is an established collaborative baseline. Flat regret considers uncertain labels separately after propagating known facts. The hierarchy method also respects relationships among the still unknown labels.

For movies, hierarchy scores 0.2322 against 0.2311 for flat regret. Books score 0.5994 against 0.5999. Songs score 0.1589 against 0.1586. These differences are small. More importantly, every paired confidence interval includes zero. We cannot conclude that the hierarchy improves relevance, and this also does not prove the methods are equivalent.

EASE is stronger than the nonzero theme rerankers in books and songs in this comparison. We report that result rather than treating a simple comparator as sufficient. The much higher book scores cannot be compared directly with movie or song scores, because the datasets, targets and split rules differ. The next slide examines a separate question: can the hierarchy reduce how much missing metadata we inspect?

### Slide 4 script

For this experiment, we freeze the reference's five recommendations. Both methods see the same missing labels and follow the same sequence of metadata lookups. A lookup reveals one binary feature from the dataset reference. The methods stop when their calculated worst case regret for the first recommendation is below a threshold, or after twenty four lookups.

The hierarchy can sometimes stop earlier because it excludes impossible feature combinations. At fifty percent missing metadata, mean lookups fall from 6.86 to 6.42 for movies, from 15.32 to 14.95 for books, and from 12.25 to 12.09 for songs. Those reductions are 6.5, 2.4 and 1.3 percent respectively. The five recommendation lists stay exactly identical in this experiment.

The saving concerns source reference bits. We have not measured actual language model calls, API charges or questions asked to people. One API response may contain many labels, so saving two bits may save no calls at all. The certificate also concerns the first recommendation under our declared matching model. It does not prove human enjoyment or certify the whole five item list.

The tighter bound mathematically cannot stop later on the shared sequence. The empirical finding is how often earlier stopping occurs and how large the saving is. Presenter 3 will show that the benefit is concentrated and often disappears under severe missingness.

### Presenter 2 cue card

Slide 3 measures independent relevance. Slide 4 measures annotation effort with a fixed list. NDCG is not enjoyment probability. A confidence interval containing zero does not establish improvement or equivalence. Bit savings are not measured call savings. Both methods receive the same candidates and propagation.

## Presenter 3 scripts for slides 5 and 6

### Slide 5 script

The averages from the previous slide hide how concentrated the benefit is. This chart shows the fraction of profiles that save at least one lookup. Nineteen of 320 movie profiles benefit, which is about 5.9 percent. Thirteen of 320 book profiles benefit, about 4.1 percent. Five of 181 song listeners benefit, about 2.8 percent.

These percentages answer a different question from the previous slide. The previous slide showed the reduction in average lookups across everyone. This chart shows how many people receive any reduction. A small number of profiles can save several lookups while most save none.

We kept all profiles in the averages, including those that exhausted their budget. We did not report only successful cases. With the same query sequence, a coherent bound is no larger than the flat bound. Sometimes both methods cross the threshold together, sometimes neither crosses it, and sometimes the hierarchy crosses earlier.

The hierarchy's theoretical advantage therefore does not imply that every user benefits. The song saving is especially fragile as a broad generalization because only five listeners benefit in this sample. We need larger and more varied tests before claiming consistent practical savings. We also tested what happens when substantially more metadata is missing.

### Slide 6 script

Here seventy five percent of the reference labels are hidden, while the budget remains twenty four lookups. Movies receive 129 hierarchy certificates out of 320 profiles, compared with 119 for flat labels. Books receive 42 rather than 39 out of 320. Songs receive 60 rather than 59 out of 181.

For example, only 42 of 320 book profiles reach the hierarchy threshold. The other 278 exhaust the budget without a certificate. That does not necessarily mean their recommendations are bad. It means the method cannot establish its conditional bound with the information and budget available.

We also find lower recommendation relevance for the nonzero theme reranker than the reference in the movie and book stress conditions. Their nominal confidence intervals for that difference are entirely negative. The song estimate is lower too, but its interval includes zero, so we do not assert established song harm from this test.

This explains why logical consistency alone is insufficient. A hierarchy can calculate uncertainty correctly while the learned preference weights predict taste poorly. The certificate assumes valid relationships, correct observed labels and an adequate preference interval. A faulty hierarchy can even create false confidence. Our separate derivation includes a conservative structural fault bound, but the slides' main experiments do not establish that it handles real annotation errors. Presenter 4 will explain what validation recommends and what we can defend as a contribution.

### Presenter 3 cue card

Benefit frequency is 19, 13 and 5 profiles. It differs from mean cost reduction. Stress certificates are 129, 42 and 60. Failure to certify is different from known recommendation failure. The relevance stress failure is a separate measurement. Logical consistency does not validate the taste model.

## Presenter 4 scripts for slides 7 and 8

### Slide 7 script

We select parameters on validation data before examining test performance. The parameter called gamma controls how strongly the theme utility influences ranking. All three validation studies choose gamma equal to zero from the declared grid. That means the selected policy preserves the historical reference ranking.

The earlier slides still use the separately frozen gamma of one half to examine the mechanism with a nonzero theme effect. Comparing two zero weight systems would make the hierarchy irrelevant, so we keep that diagnostic separate from the validation selected deployment result.

There is an important consequence: with gamma zero, genre labels cannot influence that ranking utility, so no genre acquisition is needed for it. The annotation savings under the nonzero diagnostic do not justify deploying a utility model that validation rejected.

This table reports a full catalog audit. EASE scores about 0.6455 for books and 0.1832 for songs, above the references' 0.6190 and 0.1649. The reference is the selected member of our paired model family, not the best possible recommender. Slide 3 restricted methods to the same sixteen candidates, whereas this slide lets these baselines rank the available catalog. That is why their EASE numbers differ. A practical follow-up should compare or adopt strong validated retrieval models before claiming a better complete system.

### Slide 8 script

Our contribution has a precise scope. We derived an exact calculation of joint label and signed preference uncertainty for binary labels linked by implications. Each candidate pair reduces to a minimum cut problem. We also derived a conservative extension for a declared number of structural hierarchy faults and documented cases where flat labels invent impossible uncertainty.

Maximum flow, minimax regret and hierarchical tagging already exist in the literature. We attribute those methods. The specialized formulation is a candidate research contribution; our searches do not prove worldwide originality.

We strengthened its evaluation using held out outcomes in movies, books and actual song recordings. The measured benefit is small, conditional metadata lookup savings. The evaluation also identifies relevance failures and a validation selected fallback. Those limitations are part of the result rather than missing information.

We have not established linked user transfer across the three domains, actual API or human question savings, universal cold start improvement, or a stronger language model. The earlier tiny student experiment did not outperform the hosted teacher. The next substantial test needs reliable independent annotations, a better validated preference model and measured acquisition costs, followed by linked user or prospective user evaluation. Our current result shows when hierarchical consistency helps calculate uncertainty, and why that alone does not guarantee better recommendations.

### Presenter 4 cue card

Gamma zero is a validation decision. Gamma one half is a separate diagnostic. Full catalog differs from the sixteen item shortlist. EASE is established prior art. Exact model computation is separate from preference accuracy. The fault budget extension is conservative. No worldwide first, shared user transfer or stronger SLM claim.

## How to rehearse together

First read the scripts once without slides. Replace any word you cannot explain using the handbook, rather than memorizing an unfamiliar phrase. Then rehearse with the eight slide deck and a timer. Presenter 1 should start a separate two minute timer for the recap. Leave enough time to point to table rows without reading all numbers.

Use the handover at the end of each segment exactly once. Each presenter should know the previous slide's conclusion and the next slide's purpose so the talk sounds connected. If interrupted, answer the direct question in one sentence, give the important qualification, then continue at the next paragraph.

Before presenting, all four should be able to explain five distinctions: labels versus preferences; correctness of a calculation versus usefulness of a model; validation versus test; mean saving versus beneficiary frequency; and three independent domain tests versus linked user cross domain transfer.

## Emergency thirty second explanation

Recros recommends movies, books and songs. Our new research checks whether missing item labels create uncertainty that is actually impossible under a genre hierarchy. We derived an exact conditional calculation and tested it on independent ratings and listening events. It saves a small number of simulated metadata lookups for a minority of profiles. We did not establish better relevance, and validation chooses zero theme weight. The contribution is the documented formulation and its limits, supported by reproducible tests.

## First milestone completeness checklist

The spoken two minute recap covers the literature review, all eight problems, all nine architecture stages, all seven weights, model training, validation results, domain mixing, coverage and novelty, and open evaluations. The handbook reproduces all three original top K rows, describes every proposed store and tool, explains the proposed implementation stack and offline versus online metrics, and distinguishes proposed mechanisms from empirically measured achievements. The reference bibliography is part of the earlier report, not an additional experiment.

## Evidence used

Original first milestone PDF, physical pages 5 to 15, especially 9 to 14. The printed page number is one less than the physical PDF page number. Latest eight slide deck and preserved three domain report at docs/milestone2/hierarchy/domains/RESULT.md. Detailed derivation at docs/milestone2/hierarchy/DERIVATION.md. The scripts are explanations of these sources; they introduce no new experiment or performance claim.
