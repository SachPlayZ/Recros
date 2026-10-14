# Recros technical handbook for the graduation presentation

Explanation of the original milestone and the eight slide three domain results presentation

Prepared 14 October 2026 for a team with full stack experience and no assumed background in machine learning

Recros aims to help people discover movies, books and songs using their interests, while avoiding several weaknesses of ordinary recommendation systems. The original milestone reported a hybrid architecture and preliminary ranking results. The newer work develops a mathematically precise way to reason about missing hierarchical labels and tests it against real historical outcomes in three independent domains. It establishes small simulated annotation savings and documents relevance failures. It does not establish a better general recommendation model or a successful small language model replacement.

Read chapters 1 to 6 before rehearsing. Chapters 7 to 14 explain the current slides. Chapters 15 to 19 supply deeper mathematical, implementation and research context. The four presenter guide contains the timed speech. The question bank contains answers allocated to each presenter. Evidence locations appear throughout so a team member can open the actual result rather than rely on a remembered sentence.

## 1 What a recommender is trying to predict

A recommender starts with a person, a set of available works and incomplete information about what that person will value. Its output is an ordered list. The central question is not simply which items resemble one another. It is which available items the person is likely to find worthwhile in the current situation.

Consider a person who likes a science fiction movie. They may like its problem solving, the lead character, suspense, visual spectacle or soundtrack. A system that stores only science fiction compresses all those reasons into one category. It may recommend another science fiction work that matches the category but misses the actual reason. Adding more labels can make the representation richer, but labels still describe the work. They do not establish which of those properties caused a person's preference.

The full stack analogy is useful. Your catalog resembles a database table of products. A user's history resembles an event log. A recommender is a service that joins those records, transforms them into numeric representations, retrieves plausible products, computes scores and returns an ordered response. Machine learning enters where some of the numeric relationships come from examples rather than handwritten rules. A robust optimization layer can then examine how reliable an ordering is under a declared set of unknown values.

There are at least four different things to get right. The system must identify the work correctly. It must obtain reliable information about its properties. It must learn the user's response to those properties. It must choose a useful ordering under uncertainty. A failure in an earlier step cannot generally be repaired by a more sophisticated later algorithm. Correctly optimizing the wrong representation can confidently return an unsuitable recommendation.

### Explicit and implicit feedback

An explicit rating is a user's direct evaluation, such as four stars. An implicit signal is a recorded action, such as listening to a song. These are different kinds of evidence. A high movie rating is closer to an explicit positive judgment. A song play shows exposure or listening, but it may come from a playlist, autoplay or repetition without strong enjoyment.

Absence is also ambiguous. If a person has not rated a book, they may never have encountered it. If they did not play a recording during a test window, they may still like it. The offline evaluation needs a finite relevance set, so it treats specified unobserved items as nonrelevant for that calculation. That convention does not turn them into genuine dislikes.

The current tests use movie and book ratings of at least four as positive outcomes, and specified later song plays as positive listening outcomes. Presenters should say which outcome a row measures. Do not casually translate all three into satisfaction.

### A user item matrix

Imagine rows for users and columns for items. A cell may contain a rating, play count or positive interaction indicator. Most cells have no observation. This is a sparse user item matrix. Sparse means there are many more possible user item pairs than recorded interactions; it does not mean the source file has few rows.

A dataset with millions of events can still be sparse if it contains many users and works. That is why acquiring a larger dataset does not automatically solve the recommendation problem. It may improve coverage of some users or popular works while leaving new or niche works nearly unobserved. We also have to distinguish event count from unique users, unique items and independent evaluation profiles.

## 2 Machine learning and language models from first principles

### Features labels and parameters

A feature is an input the algorithm can use. For a movie, it might be a genre indicator, release year, text vector or historical audience signal. A target label is the outcome a training example asks a model to predict, such as positive interaction. An item metadata label is a descriptive property such as horror. These two meanings of label should be kept separate: training targets describe an observed task outcome, while metadata labels describe an item.

A parameter is a number adjusted during training. For example, a simple model may learn that a genre indicator receives a positive coefficient for one user's ratings. Training selects parameters to reduce an error on examples. Inference applies those already selected parameters to a new input. Calling a model on a work is inference; downloading or reading a dataset is neither training nor proof that a model has learned from it.

Hyperparameters are settings chosen outside the ordinary parameter fit. Examples here include the mixture weight alpha, theme weight gamma and regularization strength. Validation data chooses those settings. Test data assesses the resulting choices after they are fixed. Changing settings after seeing test results uses the test as further development data.

### Language models and tokens

A language model learns patterns in sequences of tokens. Tokens are pieces of a text representation; they can be words or smaller units depending on the tokenizer. A causal language model predicts the next token using earlier tokens, without looking at future tokens. Repeated next token prediction can generate a passage, a structured label or an answer.

A large language model has substantial learned capacity and usually extensive prior training. A small language model uses fewer parameters or a smaller architecture. Size alone does not determine whether a model is suitable for a task. Its training data, objective, vocabulary and evaluation matter. A small model trained from scratch on a small local corpus should not be expected to reproduce a broadly pretrained hosted model merely because both use transformer layers.

A transformer uses attention to combine information from different positions in a sequence. In a causal model, an attention mask prevents a position from reading future tokens. This is different from the metadata masking in the recommendation experiment. Causal attention masking enforces the text prediction task; metadata masking hides item properties to create controlled uncertainty.

### The terminology issue in the original report

The PDF names its fast component an SLM ranker, but describes a gradient boosted decision tree with nineteen engineered features. A decision tree ensemble is a compact machine learning ranker, not a language model. It processes tabular features using successive decision rules and outputs a prediction or score. It does not learn next token generation simply by being small.

The accurate spoken description is therefore compact ranker when discussing that implementation. The architectural intention was to combine language based reasoning with efficient ranking. Later in this project, an actual tiny causal language model was separately trained and tested. Its task was source feature extraction, rather than the original nineteen feature interaction ranker. Its failure does not automatically invalidate the original ranker, and the original ranker's reported AUC does not validate the tiny language model.

### LLM orchestration and extraction

An orchestrator interprets a request and decides which tools or services to call. In full stack terms, it is a controller that can propose structured tool arguments from natural language. An extractor proposes metadata from source text. An explainer turns selected evidence into readable prose. A ranker scores candidates. These roles can use different algorithms and should have different tests.

For example, a model may correctly read that a story contains an investigation while still failing to predict whether a user will enjoy that story. An explanation may sound convincing while citing a property that never influenced the score. A useful system needs evidence provenance and links between actual score inputs and explanations, rather than fluency alone.

### Content vectors and embeddings

A vector is an ordered list of numbers used to represent an item or user. TF IDF represents text using weighted word or phrase counts. A term appearing in one document but rarely across the catalog may receive more weight than a term occurring everywhere. This makes lexical matching possible without training a large language model.

A learned semantic embedding also represents text as numbers, but its dimensions are learned from a model's training objective. Similarity can then reflect semantic relationships that do not share exact wording. Calling every numeric text representation an LLM embedding is incorrect. The current broad catalog uses a TF IDF index with 35,000 text features; the original PDF proposed sentence transformer embeddings as part of its design.

Similarity means closeness under the selected representation. It does not mean the works are interchangeable or that a person will respond to them identically. The same creator, language or genre can contain both liked and disliked works. A better representation can reduce some collisions, but any claim of preference improvement requires independent outcomes.

## 3 The eight problems in the original milestone

The original PDF's problem statement appears on physical pages 6 and 7, printed pages 5 and 6. These are the motivations for the product. They are not eight separate problems proved solved by the latest eight slides.

### Cold start

User cold start means little or no history for a new person. Item cold start means little or no interaction history for a new work. System cold start means the service is new and lacks an established interaction base. An onboarding quiz can supply explicit preferences for a user. Source text or metadata can supply features for an item. A new platform still needs useful information about both sides.

Recommending a recently released work can provide discovery, but its mere presence in a list is not proof that item cold start is solved. A cold start evaluation must define which interactions are unavailable and compare methods on held out new users or new items. The latest experiments supply twenty known works per profile, so they simulate limited history rather than zero history.

### Data sparsity

Few observations for most user item pairs make estimates uncertain. Collaborative methods may fail to identify reliable neighbors, especially in the long tail. Content information can supplement interaction data, but poor or missing content information creates a different bottleneck. A movie catalog with descriptions and a song catalog containing mainly titles do not offer equal evidence for a narrative feature extractor.

Our new method addresses incomplete metadata under a declared model. It does not magically generate accurate preferences or interactions for every missing cell. Larger source downloads strengthen the empirical test, but the evaluated subsets and limited profiles still constrain what can be concluded.

### Popularity bias

Popular works accumulate many observations and are easier for collaborative models to score. Repeatedly favoring them can reinforce their exposure advantage. A popularity baseline is essential because it can perform well even without personalized reasoning. A method that loses to popularity or a strong collaborative baseline needs a clear explanation of the task where it adds value.

The broad discovery interface introduces less exposed and recent candidates. The current book and song research subsets favor annotated popular items to make local computation and identity matching tractable. Those subsets therefore do not validate performance on the long tail. We report the limitation instead of generalizing from the popular subset to all works.

### Filter bubbles

A system can repeatedly recommend the same types of works because short term relevance rewards similarity to past consumption. Diversity introduces differences within a list. Novelty concerns whether items are unfamiliar or less popular. Cross domain suggestions can expand the domain of exposure. These are related but distinct ideas.

Five highly similar movies can be accurate but offer little diversity. Five unfamiliar items can be novel but irrelevant. A book and a movie adaptation may span domains while repeating essentially the same story. Evaluating useful discovery requires more than counting categories.

### Feedback loops

The system decides what gets shown. Shown items generate clicks or plays. Those events influence the next training cycle. Items that were never shown have no opportunity to generate feedback. Consequently, observed behavior is partly shaped by previous recommendation policies.

Bias aware sampling and exposure correction were proposed in the PDF. The current offline historical logs do not randomize exposure, so they cannot establish that a new policy prevents such loops. A controlled online design or an appropriate counterfactual evaluation would require additional assumptions and data.

### Explainability

A useful explanation tells the user which relevant information influenced the choice. Natural language is convenient, but a plausible generated story is not enough. Source passages can support item properties. Score contributions can support the connection between those properties and a ranking. A user supplied reason can support an explicit preference.

The source reading pilot measures whether text supports specified features. It does not measure whether users find a recommendation explanation helpful or faithful to the ranking. The hierarchy's worst case witness explains an unfavorable modeled world; it is not an ordinary prediction or a guaranteed description of the complete work.

### Cross domain isolation

The product's three domains are movies, books and songs. A user may want recommendations within their starting domain and in the other two. A shared catalog and shared facets make such retrieval possible. True cross domain preference transfer is a stronger claim: information about the same person's taste in one domain should improve recommendations in another, compared with an appropriate baseline.

MovieLens, Goodreads and Last.fm user IDs do not identify the same people. Numeric ID 12 in each source is not a shared user. The latest tests evaluate the same mechanism independently within each domain. The structural film and book experiment uses cross domain candidate directions but scripted preferences. Neither establishes shared user transfer accuracy.

### Fairness and exposure imbalance

Exposure concerns which items or providers receive recommendation positions. User fairness concerns the quality or treatment received by different groups of users. A long tail share or exposure Gini can summarize item distribution, but it does not establish demographic fairness or fair treatment of creators.

The PDF proposed a fairness adjustment and exposure balancing. Our newer ranking and annotation tests do not provide provider group labels, a fairness policy or causal exposure outcomes. A correct answer to a judge is that these remain explicit evaluation targets. Calling a novelty slot a fairness guarantee would overstate the evidence.

## 4 Everything the first milestone reported

This chapter separates design work, reported empirical work and open work. Physical PDF page numbers count the cover as page 1. The printed numbers begin on the abstract, so physical page 14 is printed page 13.

### Literature and design work

The PDF surveys content based filtering, collaborative filtering, knowledge based systems, demographic methods, community methods, hybrids, cross domain systems, social recommenders and recent deep learning and LLM approaches. It concludes that a single approach does not cover all the operational needs. This survey motivates the architecture; it is not an experiment showing Recros beats every surveyed approach.

The architecture contains nine stages. The table gives the full design in familiar service terms. The implementation technologies in the PDF are proposed options, rather than evidence that each service ran in the reproduced local system.

| Stage | Function | Full stack interpretation |
| --- | --- | --- |
| 1 Onboarding | Capture favorites, mood, exploration and avoidance | Form and profile initialization |
| 2 LLM orchestrator | Interpret intent and plan tool use | Request controller with structured tool arguments |
| 3 Memory and data | Persist profile, interactions, user relations and content | Data stores and indexes |
| 4 Candidate generation | Merge content retrieval with similar user retrieval | Search and recommendation candidate services |
| 5 Compact ranker | Combine features into ranking scores | Model scoring service |
| 6 Diversity and fairness | Change ordering or exposure according to explicit goals | Controlled postprocessing |
| 7 Explainer and enhancer | Explain choices and map related works across domains | Evidence based response generation |
| 8 Output | Deliver an ordered list and explanations | API response and user interface |
| 9 Feedback | Record interaction and refresh models later | Event collection and offline jobs |

The proposed profile store contains user information, quiz answers, preferences, exploration level, avoid lists and embeddings. The interaction store contains views, clicks, likes and dislikes, progress, skips, ratings and explicit feedback. The cross user store contains embeddings, a similarity graph, clusters or personas and collective preferences. The content store contains metadata, genres and tags, embeddings, popularity and inter-item links.

The PDF's orchestrator tool inventory includes getting a user profile, history, preferences and embedding; finding similar users; obtaining cluster trends; searching content with filters; and reading item details. These are tool contracts. They do not themselves demonstrate that the orchestrator reliably chooses correct tools or infers user intent.

The proposed stack includes React or Next.js, FastAPI, a vendor LLM API, LightGBM or XGBoost, sentence transformer embeddings, FAISS or Pinecone, PostgreSQL, Redis and Celery. These are architectural choices in physical page 12. The present research uses Python and local files with a FastAPI demonstration and a catalog index. Do not claim all proposed infrastructure was implemented merely because it appears in the design.

### The seven signal formula

The original score assigns the following weights. They sum to one, but that alone does not make the score a calibrated probability or prove that the weights are optimal.

| Signal | Weight | Intended meaning |
| --- | --- | --- |
| User item similarity | 0.30 | Match the user's representation to the item |
| Similar user affinity | 0.20 | Use behavior from comparable users |
| Genre match | 0.15 | Match categorical content preferences |
| Novelty | 0.10 | Encourage discovery of less familiar content |
| Diversity | 0.10 | Adjust for list redundancy or underrepresented types |
| Fairness | 0.10 | Adjust exposure according to the chosen policy |
| Recency | 0.05 | Consider release or publication time |

$$S=0.30S_{ui}+0.20S_{su}+0.15S_g+0.10S_n+0.10S_d+0.10S_f+0.05S_r$$

The seven component scores must have compatible scales for these weights to have their intended meaning. A large raw popularity count would overwhelm a normalized similarity if combined without transformation. Diversity can also depend on which items have already been selected, so it is often a list construction term rather than an independent item attribute. The PDF describes a diversity penalty, although its formula adds a diversity signal. The implementation must define that signal's sign or transform before the number has a precise interpretation.

A simple arithmetic illustration uses component values 0.8, 0.6, 1.0, 0.3, 0.5, 0.4 and 0.9. The corresponding weighted terms are 0.24, 0.12, 0.15, 0.03, 0.05, 0.04 and 0.045, totaling 0.675. This is an illustrative score calculation, not a measured Recros prediction. It shows that a weighted sum can be explained without pretending its output is a 67.5 percent enjoyment probability.

The latest hierarchy research does not reproduce this seven signal formula. It isolates a known background score plus a weighted facet utility. This controlled simplification lets us analyze one uncertainty mechanism. It also means the latest result cannot be described as a verified improvement to all seven original objectives.

### Reported model training

| Original PDF field | Reported value | Location |
| --- | --- | --- |
| Training interaction rows | 215,148 | Physical page 13 table 2 |
| Validation rows | 23,615 | Physical page 13 table 2 |
| Engineered features | 19 | Physical page 13 table 2 |
| Best boosting iteration | 342 | Physical page 13 table 2 |
| Validation binary AUC | 0.9373 | Physical page 13 table 2 |
| Validation users for top K | 791 | Physical pages 13 and 14 |

An iteration in gradient boosting adds or updates the ensemble's capacity according to its training procedure. Early stopping selects a point where validation no longer improves under the chosen criterion. The training rows are user item examples, not necessarily unique users. AUC evaluates ordering of positive and negative classification examples across thresholds. It is different from top five recommendation quality and different from accuracy at a single threshold.

The original report states these values. The current pack does not treat them as newly rerun results under the later strict protocols. If asked for their exact original candidate sampling, target definitions or leakage controls, use the saved original code and artifacts where available. The PDF alone does not specify enough detail to reconstruct every evaluation choice.

### All original ranking results

| K | NDCG at K | Recall at K | MAP at K |
| --- | --- | --- | --- |
| 5 | 0.9205 | 0.7584 | 0.9770 |
| 10 | 0.9138 | 0.8878 | 0.9445 |
| 20 | 0.9368 | 0.9586 | 0.9095 |

These appear in table 3 on physical page 14. NDCG stays above 0.91. Recall rises as more recommendations are allowed. Different metrics can move differently as K changes because their normalization and ranking sensitivity differ. The unusually high MAP at five deserves investigation of its definition, denominator, candidate construction and split. The PDF itself flags potential inflation. It should not be promoted as unqualified proof of near perfect recommendations.

The high earlier NDCG and much lower newer scores are not an established decline in the system. The later experiment changes datasets or intersections, candidate rules, split rules, profiles, model and K. Comparing two measurements numerically is scientifically useful only after ensuring they measure the same task. A strict small score can be more informative than a large score on an insufficiently described test.

### All original cross domain and discovery measurements

| Field | Reported value | Interpretation |
| --- | --- | --- |
| Nonprimary domain fraction | 0.3518 | About 35.18 percent of recommended items outside the primary domain |
| Mean unique domains | 2.40 of 3 | The average list spans more than two domains |
| Coverage at 20 | 0.0407 | About 4.07 percent of the catalog appears across evaluated lists |
| Mean negative log popularity | minus 2.98 | Novelty statistic under the report's popularity definition |

Domain mixing measures the composition of output. It does not establish that transferred preferences made the other domain's items useful. Coverage counts distinct surfaced items relative to an available catalog; it needs a catalog definition and evaluation population. The novelty number cannot be compared with another dataset without knowing popularity normalization and units. If popularity were a probability between zero and one, its negative logarithm would be nonnegative; the report's negative value requires its actual score definition to interpret. Do not invent that definition or convert minus 2.98 into a percentage.

### What remained open in the PDF

The report identifies limited coverage and novelty as next priorities. It also calls for head to head comparisons with collaborative, content and pure LLM baselines; fairness across providers; perceived explanation quality; and online click, completion and retention evaluation. The architecture proposes bias aware sampling and exposure correction, but the reported tables do not demonstrate a causal reduction in feedback loops.

The offline evaluation plan names Precision, Recall, NDCG, MAP and MRR at several K values; intra-list dissimilarity; novelty; catalog coverage; exposure distribution; and reference based explanation measures such as BLEU, ROUGE and BERTScore. The online plan proposes A/B tests for click through, completion, session length and seven or thirty day retention. These were evaluation plans, not all completed measurements. Surface text overlap scores also would not by themselves establish faithful or useful explanations.

## 5 What changed during the newer work

Several separate experiments and product changes accumulated. They should not be merged into one inflated success claim. The latest slides summarize the final three domain extension, while earlier work explains how we arrived at that question.

### Larger working catalog and automatic discovery

The current catalog audit records 222,915 items: 45,437 movies, 6,821 books and 170,657 songs. The broader catalog retrieves across all three domains and can return five recommendations in each, including the starting domain. Preference controls are optional refinements after the automatic recommendations. Recent and less exposed slots support discovery.

The catalog is larger than the evaluation subsets. The research's 789 movies, 3,000 books and 2,000 recordings are intersections chosen for available outcomes, reliable identities, annotations and CPU feasibility. The larger product index demonstrates data and retrieval capability. It does not mean every record has rich labels, every song joins to the recording benchmark or every user has linked cross domain history.

The catalog audit records genre metadata for 42,994 movies and 6,713 books, but no genre field for the recovered song records. Movie language and production country fields are common. Book and song language and country fields are missing in that recovered index. Literal setting or era mentions in descriptions are sparse and are not verified full settings. The benchmark's AcousticBrainz recording labels supplement a separate evaluation corpus; they do not silently label every product song.

### Earlier discovery pilot

An earlier MovieLens pilot used 93 test users and a chronological split. A discovery reranker increased tail share from 0.22 percent for the hybrid to 7.85 percent, while NDCG at ten decreased from 0.1547 to 0.1498. The paired difference interval included zero. This describes an observed discovery tradeoff in one movie task. It does not establish relevance superiority, provider fairness or cross domain transfer.

### Preference planning and representation diagnosis

A scripted decision planning experiment examined which information action to choose in 24 constructed cases. Exact search, an information based policy and the hosted tie decision reached the modeled targets; a one step policy did worse. The experiment had specified hypotheses and scripted outcomes, rather than independent user satisfaction labels. Strong performance inside that model cannot establish that its hypotheses adequately capture actual taste.

A personal development trial then exposed representation collisions: opposite preferences could map to identical small feature vectors. If a model is allowed to see only identical vectors, it cannot deterministically give different predictions to those examples. Adding genres resolved one collision, while another persisted. This is a useful information loss diagnostic, but adapting a representation to one participant's examples is development, not held out generalization.

### The actual tiny language model trial

The later tiny causal model has 562,464 parameters, two transformer layers, width 96, four attention heads and context length 192. It trained from random initialization on this Mac, using 4,000 local summaries, then 135 teacher labeled training records and 33 validation records. It did not use downloaded pretrained model weights.

On eighteen assistant authored development references, the hosted DeepSeek teacher reached F1 0.913 and tiny model version two reached 0.167. Those references informed development, so they are not independent accuracy gold. In a subsequent one person reading pilot, five of six supplied paragraphs received usable judgments, giving twenty binary feature decisions and seven positive judgments. DeepSeek matched six positives, with no extra positives. The student matched none and produced two extra positives. Its F1 was zero.

Intersecting student claims with cached teacher claims removed extra positives but left no positive predictions. Precision with zero predicted positives is undefined, rather than perfect. This is a failed compact extraction experiment with a working implementation. We have not earned a claim that an SLM replaces the teacher. The latest hierarchy result neither retrains that student nor changes its failure.

### The new mathematical direction

The conversation moved from broader labels to the problem of how missing hierarchical labels should affect decisions. The contribution candidate is not the invention of genre tags. It is an explicit tractable formulation of joint uncertain signed preferences and incomplete implication linked labels, with a structural fault bound. The three domain studies then ask whether the resulting mechanism improves independently measured relevance or reduces controlled metadata acquisition.

## 6 Hierarchical multi label representations

### Multi label and hierarchy are different ideas

Multi label means an item can receive several properties simultaneously. A book can be fantasy, adventure and young adult. Hierarchy means some labels imply broader labels. If a correctly defined subgenre is present, its parent is present. A primary genre and a secondary setting are not automatically a parent child relation. Geographic setting, language, publication period, tone and narrative style often belong to parallel facets.

| Relationship | Example | Safe inference |
| --- | --- | --- |
| Subgenre to parent | Space opera to science fiction | Child present implies parent present |
| Parent to subgenre | Science fiction to space opera | Parent present does not force this child |
| Parent absent | Science fiction absent | All children that imply it must be absent |
| Production country to setting | Film produced in India | Story location remains unknown |
| Publication year to era | Book published in 2020 | Story could occur in any era |
| Creator identity to language | A particular artist or author | Work language needs independent evidence |

A hierarchy can therefore improve consistency while still missing aspects of intent. It should not force all properties into a single tree. Genres may allow multiple parents. Our hard formulation supports implication graphs, provided the observations and constraints have a consistent completion. It does not require every work to have exactly one primary category.

### Present absent and unknown

A metadata field can be present, known absent or unknown. These states have distinct meanings. A source that explicitly says there is no time travel can support absence under the relevant rubric. A source that says nothing about time travel generally supports unknown, not absence. Treating unknown as negative can exclude suitable works and produce unjustified confidence.

The experiment uses a closed world reference for reproducibility: listed active tags and ancestors are one; unlisted active tags are zero. It then hides a specified fraction of those bits. These zeros are reference conventions, not proven semantic negatives for the entire work. The solver is exact for the resulting reference model, while the reference itself can be incomplete or wrong.

### Why NovelUpdates does not make the method new

NovelUpdates offers a rich tag vocabulary, useful as candidate secondary facets. Importing a vocabulary does not assign it correctly to all books, movies and songs. A tag's definition, applicability, evidence source, uncertainty and domain compatibility still need a schema and annotation process. Some labels are specific to particular literature traditions or audience categories and cannot be copied as universal genre implications.

Hierarchical multi label tagging and ontology aware recommendation already have substantial precedents. AcousticBrainz itself supplies hierarchical music genres. Our partial NovelUpdates collection and earlier literature search do not establish an exhaustive annotation layer or a new tagging invention. The research question moves to what constraints do to uncertainty and when that is useful under independently measured outcomes.

### Preferences are separate from labels

An item vector might mark science fiction as present. A user's weight for that feature might be positive, zero or negative. A person can like a broad parent while avoiding a subtype, or dislike the broad genre while liking one unusual example. Hierarchical relationships constrain item properties. They do not require preferences to follow the same hierarchy.

The model therefore permits signed weights. A negative learned coefficient is an association under the model, not proof that the person consciously dislikes that feature. In music, coefficients learned from centered play intensity express relative listening intensity, not declared dislikes. This distinction is essential when a judge asks whether the system understands intent.

## 7 Slide 1 and the precise research question

The title slide introduces tests in movies, books and songs. Its subtitle separates independent relevance outcomes from annotation effort. That separation is the organizing principle of the research. The earlier structural proof showed that a coherent label model can remove logically impossible uncertainty. The follow-up needed to establish whether that translates into better ranking or a useful reduction in information acquisition.

There are two experiments. In the relevance experiment, flat and hierarchy methods may reorder the same sixteen retrieved candidates, and their top five are compared with held out ratings or plays. In the acquisition experiment, the five reference recommendations are fixed and the two methods differ only in when their conditional first item bound crosses a threshold. A positive result in one experiment must not be silently reported as a positive result in the other.

The introductory example is a subtype implication. If space opera is a subtype of science fiction, an unknown item cannot coherently be space opera while being outside science fiction. The flat relaxation can temporarily admit that world when both fields are unknown. The hierarchy solver excludes it. Whether this changes a decision depends on the user's signed weights, other candidates and observed information.

This is a computational research question with a user facing motivation. It addresses how to reason about missing metadata without exaggerating uncertainty. It does not claim that human taste is exhausted by the taxonomy or that removing all logical inconsistencies solves cold start. Presenter 1 should introduce the question after the two minute milestone recap rather than begin with an unfamiliar optimization formula.

## 8 Slide 2 and the data pipeline

### Movie identities and outcomes

MovieLens 20M supplies 20,000,263 ratings. The experiment conservatively links MovieLens records to the Literary Theme Ontology using movie metadata, unambiguous title and year information and IMDb identity. It retains 1,242 matched LTO films and 3,841,046 ratings involving those identities. At test time, 789 films have the required prior availability under the declared background data.

The matched ratings use global chronological sixty, twenty and twenty percent windows. Training ends on 19 February 2006, validation ends on 2 October 2009, and test outcomes are later. There are 128 validation profiles and 320 test profiles. Evaluation users are excluded from background popularity and similarity fitting, while their permitted earlier history supplies their individual profiles. Profiles use the last twenty prior ratings and exclude all previously seen items from recommendation candidates.

This is deliberately more conservative than a fuzzy title join. A mistaken identity can assign one film's themes to another's ratings and create a false apparent success. Ambiguous matches are excluded and recorded. Reliable smaller intersections can be scientifically preferable to larger corrupted joins, although exclusion narrows the population to which results generalize.

### Book identities and outcomes

Goodbooks provides 5,976,479 ratings over 10,000 books. The CPU bounded experiment selects 3,000 books from disjoint background users' positive counts and fits on 1,814,381 background ratings. It uses 128 validation profiles and 320 test profiles. The dataset does not expose explicit rating timestamps, so we supply twenty random known ratings per evaluated person and hold out the remaining eligible ratings.

The background, validation and test people occupy disjoint declared user ID partitions. Their numeric IDs are only a reproducible partition key within that source. They do not create identities across datasets. The selection of a popular book subset makes this practical locally but restricts inference about unseen or very obscure works.

Goodbooks book IDs refer to aggregated works, while source shelf tags can refer to a popular edition's Goodreads identity. The mapping is recorded. Shelf labels require at least five votes under this protocol. The feature system has sixty nine facets and thirty eight implications, including a frozen project declared genre mapping, separate themes or tone, edition language and publication period. Publication period describes publication, not the historical era inside the story. Edition language does not necessarily describe the original edition.

The author identifier content baseline deliberately avoids hidden genre bits. Source aggregate average ratings and global rating counts are not used to score popularity. Otherwise aggregate information spanning the evaluation period could contaminate an ostensibly history only comparison. The random book split still has a different interpretation from forward chronological prediction.

### Song identities and outcomes

Last.fm 1K supplies 19,150,868 listening events. AcousticBrainz supplies genre paths for 566,710 recordings. Joining exact recording MusicBrainz identifiers yields 6,574,469 plays of 176,909 recordings across 991 matched listeners. The locally feasible catalog selects 2,000 annotated recordings by distinct background training listeners before evaluation. That selected catalog contains 1,353,724 events.

This is a recording task. An artist may have many songs; a song may have several recorded versions. Matching only on artist would evaluate a different problem. The exact identifier join avoids converting a recording level question into an artist proxy. Display titles and artist names are retained, but identity rests on the recording key.

The song windows end on 19 February 2008 for training and 14 October 2008 for validation. There are 95 validation listeners and 181 test listeners. Twenty recent distinct previously played recordings form a profile. Repeated plays are aggregated only inside their historical window. A test positive is a later played recording absent from the earlier logs. All previously played recordings are excluded from candidates.

For fitting relative facet preference, the outcome is centered logarithmic past play count. Logarithms reduce the influence of very large repeat counts. An internal adapter adds four to that logarithm so existing binary positive routines can consume plays. This is a software adapter, not an invented five star rating. Centering removes the constant from preference regression. Presenters should call the source listening events throughout.

AcousticBrainz provides 327 genre facets and 297 implications, including thirty roots and 297 children. Its genre hierarchy is source authors' prior work. Retrospective genre labels and unlisted subgenre conventions remain limitations. No audio processing occurs in this experiment; the input is logs and published recording metadata.

### Why the three rows are not a cross domain user trial

Each row uses a separate source population, relevance definition, catalog and split. The mechanism transfers as an algorithmic implementation, but an individual user's preference does not transfer between sources. Adding up 320, 320 and 181 gives 821 historical evaluated profiles across tasks, not 821 recruited people in one cross domain study.

The differences also prevent a naive quality ranking between domains. Book NDCG can be higher because its random split exposes a different history and target distribution, not because books are inherently easier. A good comparison is hierarchy versus flat within the same row and protocol. A bad comparison is claiming that a 0.62 book score proves books are four times easier than songs.

## 9 From history to candidates and preference intervals

### Retrieval comes before expensive comparison

The available catalog may contain hundreds or thousands of unseen works for one person. Retrieval narrows it to sixteen plausible candidates using the validation selected historical recommender. The decision layer then compares those candidates. This resembles a search backend retrieving plausible documents before a more expensive reranker examines them.

The sixteen candidates are the same for the paired methods. Future positive works are not inserted to make the test easier. A relevant work omitted during retrieval cannot be recovered by rearranging the shortlist. Consequently, shortlist results isolate the decision layer but do not establish superiority of the entire retrieval system.

The final output contains five items. Ranking each item by its individual worst case regret is a usable ordering procedure, but the pairwise theorem does not solve the optimal five item set problem. A set objective could include joint coverage, redundancy, position dependent utility or sequential feedback. Those would require their own formulation and evaluation.

### Collaborative and content reference models

Popularity ranks by prior background frequency. ItemKNN estimates similarity between items from overlapping historical positive users and recommends items connected to a person's earlier positives. The content model here uses movie genres, book authors or recording artists, depending on the source. The reference hybrid mixes the corresponding content signal and collaborative signal, using validation selected alpha.

Movies select alpha zero in this experiment, so their reference relies on the collaborative component, with a popularity fallback for an empty positive profile. Books and songs select alpha one half. This alpha controls reference retrieval and scoring. Gamma is a different weight controlling the additional facet utility. Confusing them leads to a wrong explanation of slide 7.

EASE is a separately evaluated established linear collaborative model. It learns an item to item coefficient matrix from the historical interaction matrix with regularization and a zero diagonal. The zero diagonal prevents simply copying an observed input item into its own output. It uses no pretrained language model weights.

$$P=(X^{\mathsf T}X+\lambda I)^{-1},\qquad B_{ij}=-\frac{P_{ij}}{P_{jj}}\ (i\ne j),\qquad B_{ii}=0$$

Here X is the background user item matrix, I is the identity matrix and lambda is regularization. A person's history scores candidates through the learned B matrix. Increasing regularization changes how strongly correlations are used. The study selects EASE lambda on validation from 100, 1,000 and 10,000. The selected values are 10,000 for movies, 100 for books and 1,000 for songs. These are choices for these subsets, not universally optimal settings.

### Learning a facet coefficient

The preference fit uses a small ridge regression on the twenty known works. A row contains the work's source facet vector and the target is centered prior rating, or centered log play intensity. Ridge regularization discourages extremely large coefficients when examples are scarce or correlated. With many facets but only twenty observations, an unregularized fit could be highly unstable.

$$\widehat{w}=H^{\mathsf T}(HH^{\mathsf T}+10I)^{-1}y$$

H contains known work features and y contains centered historical outcomes. This dual form solves a regularized linear fit through a small history sized system. The sixteen largest absolute learned coefficients become request seeds, and their ancestors are included. Coefficients are normalized on an absolute sum scale and rounded to integer thousandths for the exact solver. Ancestor coefficients are retained rather than discarded merely because they were added through closure.

The preference interval extends each coefficient by twenty five percent of its absolute value in either direction. This is a fixed sensitivity assumption. It is not a learned ninety five percent confidence interval, a Bayesian posterior or a measurement that contains the true person's weight with known probability. A zero learned coefficient also receives zero width, which can suppress uncertainty about features the short history never revealed. That is one reason the model's exactness does not imply calibrated human intent.

## 10 Slide 3 and ranking evaluation

### Precision Recall and NDCG

Precision at K is the fraction of K recommended items marked relevant in the evaluation. Recall at K is the fraction of all eligible relevant held out items recovered by that list. Precision asks how many displayed works count as relevant; recall asks how many relevant works were found. They can move differently when users have different numbers of positives.

For a five item example with two relevant recommendations and four total eligible positives, precision is two fifths, or 0.4, and recall is two fourths, or 0.5. Both are evaluation conventions; they are not a direct measure of actual dislike for the three unobserved recommended works.

NDCG rewards relevant items earlier in the list. This experiment uses binary relevance. The discounted gain is a relevant indicator divided by the base two logarithm of rank plus one. The ideal gain is the gain from placing as many eligible positives as possible in the earliest positions. Dividing observed by ideal gain gives normalized discounted cumulative gain.

$$\operatorname{DCG@K}=\sum_{r=1}^{K}\frac{\operatorname{rel}_r}{\log_2(r+1)},\qquad \operatorname{NDCG@K}=\frac{\operatorname{DCG@K}}{\operatorname{IDCG@K}}$$

Take five results with relevance pattern one, zero, one, zero, zero and suppose two relevant items exist in the task. Observed gain is one plus one half, because rank three has denominator log base two of four, giving 1.5. Ideal gain is one plus about 0.63093 for ranks one and two, giving 1.63093. NDCG is about 0.9197. Moving the second relevant item from rank three to rank two raises the score to one without changing precision or recall.

If six relevant held out works exist, the ideal top five contains five positives and its denominator is larger. This shows why target counts and candidate availability matter. The implementation gives zero for profiles with no eligible positives; the movie primary mean retains all 320 sampled profiles, including six without an eligible positive target. Removing hard cases after inspecting outcomes would change the estimand.

MAP averages the precision values at relevant positions under its stated normalization. MRR focuses on the reciprocal rank of the first relevant result. AUC evaluates ordering of positive and negative examples across thresholds. These measures answer related but different questions. A high classification AUC does not automatically imply a high top five NDCG in a large catalog.

### The actual slide 3 numbers

| Domain | Reference | EASE in same pool | Flat regret | Hierarchy regret | Hierarchy minus flat |
| --- | --- | --- | --- | --- | --- |
| Movies | 0.2385 | 0.2320 | 0.2311 | 0.2322 | plus 0.0010 |
| Books | 0.6190 | 0.6368 | 0.5999 | 0.5994 | minus 0.0005 |
| Songs | 0.1649 | 0.1813 | 0.1586 | 0.1589 | plus 0.0003 |

All rows use five recommendations, fifty percent missing metadata and the separately fixed nonzero gamma of one half. A theme weight is necessary for the uncertainty mechanism to influence ranking. The table is a diagnostic of that mechanism, not the validation selected deployment policy.

The hierarchy beats flat by a tiny point estimate in movies and songs and is slightly lower in books. A point estimate is the observed sample difference. Its sign alone is not enough to conclude a general improvement. EASE is above both nonzero regret methods in the book and song rows. The experiment also preserves marginal imputation and complete annotation diagnostics outside this compact slide; additional tables are in the result files.

### Paired confidence intervals

Each profile is evaluated by both methods. We subtract flat NDCG from hierarchy NDCG for that same profile, then average those differences. A paired bootstrap resamples profiles with replacement and recomputes the mean difference. It preserves the pairing instead of treating two methods' scores as unrelated samples.

| Domain | Difference | Nominal ninety five percent interval |
| --- | --- | --- |
| Movies | plus 0.0010476 | minus 0.0005310 to plus 0.0028552 |
| Books | minus 0.0005029 | minus 0.0036991 to plus 0.0025762 |
| Songs | plus 0.0002820 | minus 0.0036834 to plus 0.0041676 |

Every interval crosses zero. The evidence does not establish ranking improvement. It also does not establish equivalence or noninferiority. Equivalence would require a justified margin and an appropriate planned analysis showing differences fall inside it. Failure to detect a difference can reflect a small true effect, noisy observations or insufficient sample size.

The original nominal bootstrap uses 2,000 profile resamples. A supplemental analysis uses 20,000 resamples and 98.33 percent intervals to adjust for three domain comparisons within each endpoint family. Those wider relevance intervals also contain zero. This is a descriptive multiplicity adjustment, not a replacement selection procedure or an all tests global error guarantee.

Bootstrap uncertainty concerns the sampled profiles under these datasets and protocols. It does not capture every uncertainty about the ontology, identity matches, time window, reference labels, user exposure or unseen populations. A precise interval cannot repair a biased experimental design. Likewise, resampling 320 historical profiles does not turn them into independent randomized user experiments.

## 11 Slide 4 and metadata acquisition

### Regret as a comparison under uncertainty

Utility is the model's numerical preference score. Regret for a chosen work is how much a challenger could outperform it in the worst allowed world. If every allowed world makes the chosen item at least as good as every challenger, its modeled regret is zero. A positive value says some permitted combination of facts and weights would make a challenger better.

Worst case does not mean most probable. The model considers all allowed completions, including unlikely ones, because it has no probability distribution over the missing facts. This can be appropriate for a conditional guarantee, but can be conservative for average ranking quality. A hierarchy shrinks the allowed set by removing impossible completions, not by predicting which completion is likely.

The acquisition test fixes the reference list. The first item is compared with its fifteen challengers. One lookup reveals one hidden candidate facet bit from the recorded reference. Known facts then propagate along valid implications. An adaptive shared schedule prioritizes unknown bits using history only prevalence entropy and weight or ancestor influence. Both methods receive the same sequence; they differ in their uncertainty calculation and resulting stopping time.

### Threshold budget and normalization

The raw pairwise gap includes background score differences plus gamma times facet gap. It is normalized by the background score range plus the weighted sum of maximum absolute interval endpoints, with a fallback of one if that scale is zero. The normalized threshold is 0.20. This does not mean twenty percent uncertainty in the everyday sense or eighty percent probability of satisfaction. It is a ratio on the specified utility scale.

Each method stops when its first item bound is at most the threshold or after twenty four queries. If no certificate is reached, the actual capped expenditure remains in the mean. Capping limits cost but also produces many unresolved profiles. Reporting only successful certificates would hide those failures and give a different answer.

The five recommendations never change in this experiment. The certificate concerns the first item among the sixteen candidates. It does not assert that all five are the best possible set or that the first item is best across every work in the larger catalog.

### Calculate the percentages correctly

$$\operatorname{Reduction}=\frac{\overline{q}_{\rm flat}-\overline{q}_{\rm hierarchy}}{\overline{q}_{\rm flat}}\times100\%$$

Movies use exact means 6.8625 and 6.41875. Their difference is 0.44375 bits per profile, and dividing by 6.8625 gives about 6.4663 percent. Books use 15.315625 and 14.953125, saving 0.3625 or 2.3669 percent. Songs use 12.2486188 and 12.0939227, saving about 0.1546961 or 1.2630 percent. The slide rounds the displayed means and percentages. Calculate from the unrounded values, not from the rounded cells.

Fractional lookup means are ordinary averages of integer per profile counts. No person performs 0.44375 of a lookup. Some profiles save several integer queries and others save zero. The nominal paired saving intervals are positive. Supplemental three domain adjusted intervals are also positive, but a mean saving's positive interval does not imply a large or broadly shared practical benefit.

### Why tighter bounds cannot stop later here

At each shared information state, every coherent completion is also a flat permitted completion. The maximum gap over the smaller coherent set therefore cannot exceed the flat maximum. If the flat bound already passes the threshold, the exact hierarchy bound passes too. This proves the earlier or equal stopping ordering for this particular shared schedule and assumptions.

The experiment is meaningful for estimating how often the inequality is strict enough to save queries and how large that saving is. It is not independent evidence for the mathematical ordering already built into the models. If methods used different query actions, noisy answers or different reference facts, this simple stopping ordering would no longer settle total cost.

### Bits calls and human questions

The simulation retrieves a single stored binary reference answer. An LLM annotation call might return twenty labels in one response. A human preference question might change several preference weights rather than reveal an item fact. A database cache lookup can be almost free. These actions have different cost models and informational effects.

Therefore 6.5 percent fewer bits is not 6.5 percent fewer tokens, dollars, LLM calls or user questions. To establish those savings, a follow-up needs actual annotation requests, response batches, error rates, caching and latency measurements. If labels are already cached or gamma is zero, buying more labels for this ranking may have no value at all.

## 12 Slides 5 and 6 and where the mechanism fails

### Benefit frequency on slide 5

Only nineteen movie profiles, thirteen book profiles and five song listeners save at least one lookup in the primary condition. The denominators are 320, 320 and 181. Their percentages are 5.9375, 4.0625 and about 2.7624 percent. These are the chart's roughly 5.9, 4.1 and 2.8 percent bars.

The mean lookup reductions on slide 4 are 6.5, 2.4 and 1.3 percent. They use different denominators: mean flat cost rather than number of people. There is no contradiction between a 5.9 percent beneficiary frequency and a 6.5 percent reduction in mean cost. Nineteen movie profiles can collectively save 142 bits, producing 142 divided by 320, or 0.44375 saved bits per evaluated profile. Among beneficiaries that is about 7.47 saved bits, which is not the overall average.

Do not headline the beneficiary only average as a typical user saving. The chart exists to prevent that misleading interpretation. Especially for songs, five benefiting profiles are a small base for generalization. The adjusted interval is positive under the resampling procedure, but uncertainty about different sources, taxonomies and populations remains substantial.

### Certification stress on slide 6

| Domain | Flat certified | Hierarchy certified | Total profiles | Hierarchy not certified |
| --- | --- | --- | --- | --- |
| Movies | 119 | 129 | 320 | 191 |
| Books | 39 | 42 | 320 | 278 |
| Songs | 59 | 60 | 181 | 121 |

The stress condition hides seventy five percent of reference labels and still allows only twenty four lookups. Hierarchy certifies about 40.3 percent of movie profiles, 13.1 percent of book profiles and 33.1 percent of song listeners. Small gains in certificates coexist with high unresolved counts. This is a documented limitation, not a reason to remove the unsuccessful cases.

Failure to certify means the remaining allowed worlds include a challenger gap above the threshold. It does not mean the actual recommendation is necessarily poor. Conversely, passing the threshold is only a statement about the declared utility and allowed worlds. It can coexist with a low held out relevance score if that utility misses taste.

### Relevance failure is a separate outcome

At the stress condition, the nonzero hierarchy movie NDCG is 0.2242 versus reference 0.2385. Its paired difference is minus 0.0143, with nominal interval minus 0.0254 to minus 0.0034. Books show difference minus 0.0234, interval minus 0.0391 to minus 0.0072. These intervals are entirely negative in these planned stress comparisons.

Songs show difference minus 0.0112, interval minus 0.0247 to plus 0.0025. Its point estimate is lower but the interval contains zero. Do not convert this into an established song relevance loss. The stress comparisons concern hierarchy versus reference, whereas slide 3's primary contrast is hierarchy versus flat. A judge may ask which baseline a difference uses, and the answer matters.

### Why accurate logic can coexist with worse recommendations

Suppose a utility rewards science fiction but the user actually liked an engaging character. The solver may exactly compute all allowed science fiction completions and choose conservatively. The calculation is correct for its input, while the input preference model is inadequate. Likewise, a source may omit a central theme, or a twenty item profile may inadequately distinguish liked and disliked subtypes.

There are separate errors from unknown metadata, mistaken metadata, invalid hierarchy edges, inadequate preference intervals and incorrect utility structure. The hard exact theorem handles the declared unknown metadata and interval uncertainty. It assumes observed facts and hierarchy implications are correct. The structural fault extension addresses a declared number of invalid implications conservatively. It does not cure incorrect observed labels that happen to obey the hierarchy, or missing musical qualities such as performance style.

## 13 Slide 7 and the validation selected decision

Gamma is the multiplier on the additional facet utility. A value of zero removes that utility's effect. The validation grid contains zero, one quarter, one half and one. Each domain independently selects zero according to its frozen validation criterion. This occurred before reading the corresponding test performance.

The selection criterion averages flat and hierarchy validation NDCG under the common theme setting. Zero is selected inside that paired model family. It is not a selection over every conceivable recommender and does not prove the reference hybrid is the global best baseline. EASE is tuned separately and can outperform that reference in the reported task.

The zero result is useful because it resists forcing a mathematically attractive mechanism into a ranking where it has not earned predictive value. However, validation is still sample dependent and susceptible to the limitations of its labels and source. A zero setting in three tasks does not prove hierarchical information can never be useful. It says this learned utility and interval design did not improve this validation criterion among the tested settings.

### Why gamma one half still appears elsewhere

The project froze gamma one half as a separate nonzero mechanism diagnostic. At gamma zero, flat and hierarchy ranking are identical with respect to facet gaps. Presenting that identity as successful hierarchy accuracy would be empty. The nonzero diagnostic gives the method a chance to affect decisions and preserves negative findings.

The acquisition benchmark also uses this nonzero utility. Its lookup saving is conditional on checking that utility, rather than justification for using it. With the validation selected zero theme utility, acquiring genre bits for its ranking is unnecessary. This is one of the most important limitations in the pack. The current studies show a possible benefit for costly metadata checking under a declared nonzero utility, but they have not established a deployment context where that utility deserves use.

### Full catalog and same pool numbers

| Domain | Reference full catalog NDCG | EASE full catalog NDCG | Selected theme weight |
| --- | --- | --- | --- |
| Movies | 0.2385 | 0.2247 | 0 |
| Books | 0.6190 | 0.6455 | 0 |
| Songs | 0.1649 | 0.1832 | 0 |

Slide 3 restricts all methods to the sixteen reference retrieved candidates. Slide 7 allows the audited baselines to rank the entire available unseen catalog. EASE may select different works in the full catalog and obtain a different score. That is why movie EASE is 0.2320 in slide 3 but 0.2247 in slide 7, book EASE 0.6368 versus 0.6455, and song EASE 0.1813 versus 0.1832.

The reference's numbers remain the same because its own top five lie within its top sixteen retrieved pool. Other models are constrained differently in the pool comparison. The hierarchy was not run as a full catalog pairwise solver, so the tables cannot establish global superiority over full catalog EASE or another strong retriever.

## 14 Slide 8 and how much has actually been solved

The slide pairs established claims with still unestablished claims. This is a scientific scope statement. It gives the judges a direct way to assess what the project contributes and what evidence is still needed.

| Question | Current answer | Strength of evidence |
| --- | --- | --- |
| Can we remove impossible completions exactly under the declared hard model | Yes | Derivation and independent computation checks |
| Can flat models invent uncertainty that hierarchy removes | Yes | Analytical construction and controlled structural corpus |
| Does the mechanism improve ranking relevance | Not established | Held out tests in all three domains with intervals crossing zero |
| Can it reduce simulated annotation bits | Sometimes by small amounts | Shared schedule experiments with positive mean savings |
| Does that reduce real service cost | Unknown | Actual annotation cost has not been measured |
| Does it improve linked user cross domain transfer | Unknown | The new source populations are not linked |
| Does it solve zero history cold start | Unknown | Evaluated profiles contain twenty known works |
| Does it produce a stronger tiny language model | No evidence of that | The extraction trial failed on the available pilot |
| Is it globally first of its kind | Unverified | Prior art attributed and targeted searches are insufficient proof |

The defensible contribution is an explicit specialized formulation, its implementation, a structural fault extension and reproducible tests showing both usefulness and failure conditions. A negative relevance finding does not erase an algorithmic result. But the algorithmic result must not be sold as a relevance breakthrough. The team can defend the rigor of narrowing claims and testing falsifiable predictions without pretending every original product objective is solved.

## 15 The mathematical result explained step by step

### The variables and assumptions

There are m binary facets. An item has a partial vector with one for present, zero for known absent and an unknown marker for unresolved. An implication from child c to parent p imposes the inequality that the child's indicator cannot exceed the parent's. A complete assignment satisfying the observations and every implication is a coherent completion.

Preferences use the same signed vector w for all items in one comparison. Each coordinate lies in an independent closed interval from L to U. Shared means the challenger and chosen work are evaluated by the same possible person's preferences. Letting each item use a different preference vector exaggerates uncertainty and changes the question.

The utility is additive. Each present facet contributes its weight. The theorem permits arbitrary signs, including a liked parent and disliked subtype. It assumes correct observations, valid implications, nonempty completion sets and no additional cross item completion constraints. The utility is a conditional matching score, not a calibrated probability of enjoyment.

$$u_i(w,x_i)=\sum_{j=1}^{m}w_jx_{ij},\qquad w_j\in[L_j,U_j],\qquad x_{ic}\leq x_{ip}$$

For a chosen item i and challenger k, the pairwise gap maximizes the challenger's advantage across allowed label completions and the shared weight box. The chosen item's worst case regret is the maximum nonnegative pairwise gap over challengers. The minimax choice is the item with the smallest such worst case regret.

$$P(i,k)=\max_{w,x_i,x_k}\sum_{j=1}^{m}w_j(x_{kj}-x_{ij}),\qquad R(i)=\max\left(0,\max_{k\ne i}P(i,k)\right)$$

The item compared with itself must have gap zero. It cannot have one completion as challenger and a different completion as the same chosen item in a single world. Self comparison is explicitly special cased and tested. Otherwise a solver could report uncertainty about an item beating itself.

### Why weight endpoints are sufficient

For one facet, call the challenger indicator a and chosen indicator b. Their difference is minus one, zero or one. If it is one, the maximum weighted advantage uses U. If it is minus one, it uses L because negating a smaller weight yields a larger advantage. If it is zero, that coordinate cancels regardless of its uncertainty.

$$\max_{w\in[L,U]}w(a-b)=Ua(1-b)-L(1-a)b$$

This cancellation is important. If both items have the same complete feature vector, their feature utility difference is zero under every shared w, even if each item's standalone utility interval is wide. Computing two separate utility intervals and subtracting an upper endpoint from a lower endpoint can falsely use different people's weights. The common weight formulation avoids that error.

### Complement the chosen labels

Let y equal one minus b. Rewriting the expression gives a linear part and a product with nonnegative coefficient because U cannot be smaller than L.

$$Ua(1-b)-L(1-a)b=La+Ly+(U-L)ay-L,\qquad y=1-b$$

An auxiliary binary variable z can represent the positive product by requiring z to imply both a and y and giving it weight U minus L. A maximizing solution selects z when both prerequisites are selected and its weight is positive. When that weight is zero, its exact choice does not affect the objective. This turns the objective into a sum of node weights with implication constraints.

The challenger's hierarchy keeps its original direction. For complemented chosen labels, child at most parent transforms into complemented parent at most complemented child, so the arc reverses. Known labels become hard constraints on the corresponding nodes. The constant negative L is retained when converting the solution back to a pair gap.

### Maximum closure and minimum cut

A closed set in a directed graph contains every node that a selected node implies. Each node here carries a positive or negative objective weight. The task is to select a closed set with maximum total weight. That is a known maximum closure problem, not a new invention in this project.

Introduce a source and sink. For a positive node weight, add a source to node capacity equal to that weight. For a negative weight, add a node to sink capacity equal to its absolute value. Implication arcs receive a hard capacity larger than all possible finite objective costs. Cutting a positive node away from the source loses its reward; keeping a negative node on the source side pays its cost. Hard arcs prevent forbidden implication violations in an optimal finite cut.

The minimum source sink cut consequently identifies the best closed set. Its value subtracted from the sum of positive weights gives maximum closed set weight. Subtracting the retained constants gives the original worst case pair gap. The source side also supplies a coherent label witness, and endpoint choices give a shared weight vector attaining that value.

Each facet contributes challenger, complemented chosen and auxiliary nodes, plus source and sink. The graph therefore has three m plus two nodes, and its number of arcs grows proportionally with facets and implication edges. One cut solves one candidate pair. Comparing N items requires at most N times N minus one cuts for a full pair matrix. That is polynomial graph computation under these assumptions, not enumeration of every combination of labels and weights.

### A complete phantom regret example

Take one broad parent feature and a disliked subtype. Assign plus one to the parent and minus one to the subtype. Candidate A has both bits unknown. Candidate B has both absent and utility zero. Coherent completions of A are zero and zero, one and zero, or one and one. Their utilities are zero, one and zero. B never beats A, so A's coherent regret is zero.

The flat model additionally permits parent zero and child one, with A utility minus one. That impossible completion makes B appear to beat A by one. With k independent parent subtype pairs, the flat phantom regret is k while the coherent regret remains zero. After normalization by the absolute weight sum of two k, the phantom gap is one half. It does not become unbounded on the normalized scale.

This construction explains why hierarchy can matter even after unary propagation. All bits are unknown, so there is no observed child truth or parent falsehood to propagate. The advantage arises from relationships between possible unknown values, not from giving the exact model more known labels.

### What the theorem does not cover

The exact reduction depends on additive utility, independent weight intervals and implication constraints. A sum to one preference simplex couples weights and cannot simply be replaced by the same independent box theorem. Arbitrary disjunctions, nonlinear interactions and mutual exclusion constraints can change tractability.

For example, unrestricted mutual exclusions among unknown facets with positive weights can encode maximum weight independent set on an arbitrary graph. That family requires different methods or conservative relaxations. The fact that a genre interface supports AND, OR and exclusion filters does not mean the exact theoretical engine solves arbitrary Boolean formulas by this same reduction.

## 16 Structural faults and conservative protection

The hard hierarchy can falsely certify if an implication is invalid for the true item. In the parent subtype example, allow the actual completion parent zero and subtype one. It gives A utility minus one and regret one, although the hard model excluded it and claimed zero. This counterexample prevents claiming unconditional certainty from a taxonomy.

The extension declares a maximum K of implication violations across the compared pair. Let v count violations. For any nonnegative penalty lambda, maximize the utility gap minus lambda times v. Each violated ontology arc then pays a finite capacity lambda instead of being impossible. Observation and auxiliary product constraints remain hard.

$$P_{\lambda}(i,k)=\max_{w,x_i,x_k}\left[u_k-u_i-\lambda v\right],\qquad P_K(i,k)\leq\min_{\lambda\in\Lambda}\left[\lambda K+P_{\lambda}(i,k)\right]$$

The inequality follows directly: every budget feasible world has v at most K, so adding lambda K to its penalized gap is at least its ordinary gap. Maximizing the penalized expression yields an upper bound, and taking the smallest of these valid upper bounds stays valid. This is a Lagrangian penalty argument using established machinery.

The implementation checks a finite integer penalty grid including zero, powers of two and a terminal value. It is generally a conservative bound, not the exact budget constrained optimum or the optimum over every continuous penalty. A maximizing penalized witness can violate more than K edges. It must not be described as a feasible budget world unless its feasibility and attainment are verified. The code records whether the witness actually attains the upper bound inside the budget.

For K one in the example, the bound rises from zero to one and blocks the false zero certificate. This protects against the declared structural fault type, conditional on a sufficient K and correct observed facts. It does not protect against wrong observed labels that obey the hierarchy, a preference box excluding real taste, or unmodeled context. It also must not propagate observed facts through possibly faulty ontology edges before solving, because that would turn a defeasible relation into a false hard observation.

The latest three domain slide tables use the hard hierarchy comparison. They are not empirical tests of a calibrated fault budget on genuinely noisy extracted labels. The fault bound is a separate derived extension with exhaustive small problem checks. If a judge asks how K is selected for real data, the accurate answer is that we have not established a calibrated selection procedure.

## 17 Structural verification and computational cost

The controlled LTO experiment contains 46 source works, comprising 23 novels and 23 seeded films, with eight target candidates per state. Three metadata masking levels and two preference width conditions create 276 states. There are 195 distinct targets, and overlapping works are reused. These states are not 276 independent people.

The exact solver performs 15,456 pairwise cuts. Mean normalized bound is 0.2491, compared with propagated flat 0.3179 and independent per item utility interval 0.4010, when bounding the same selected candidate. The exact bound is 21.7 percent lower than flat on average and is strictly tighter in 100 of 276 states. This is a conditional uncertainty reduction, not a 21.7 percent gain in accuracy or human satisfaction.

At normalized threshold 0.20, exact certifies 101 states and flat certifies 91. At threshold zero both certify 23. The threshold result therefore depends on the permitted gap; it is not a universal increase in zero regret cases. Scripted broad preferences, artificial masking and closed world reference negatives restrict the interpretation to this constructed task.

The implementation is checked against exhaustive enumeration on 240 small cases with up to five facets, and the fault extension against ninety further small cases with up to four. Enumeration tries every feasible assignment on tiny instances and supplies an independent correctness oracle. A general HiGHS mixed integer solver checks twelve larger frozen scaling cases. Every recorded comparison agrees.

| Active facets | Native cut median milliseconds | MILP median milliseconds | Python cut median milliseconds |
| --- | --- | --- | --- |
| 32 | 0.325 | 4.854 | 1.187 |
| 128 | 0.749 | 5.637 | 4.561 |
| 512 | 2.485 | 13.162 | 27.907 |
| 2,048 | 8.817 | 34.311 | 108.952 |

The measurements use three seeded trees per size on this Mac and include graph or model construction. Native cut is faster than the recorded MILP cases, but the initial Python backend was slower at large sizes. We preserved that failure and then added native integer flow using the same frozen inputs. Integer scaled rational weights give exact flow values under the accepted input contract; a large integer fallback avoids unsafe native overflow.

A movie sixteen candidate pair matrix has a median 67.3 milliseconds and p95 74.4 milliseconds in the recorded experiment. These exclude model fitting, retrieval, source I/O and actual annotation service time. They are not end to end production API latency guarantees.

The separate movie certification replay adds about 27.93 milliseconds of mean computation while saving about 0.44375 bits per profile. Dividing gives about 62.9 milliseconds of uniform per bit acquisition latency to break even under that simplified cost model. Real calls are batched, cached and error prone, and timing order was fixed in this exploratory replay. The calculation identifies a possible tradeoff; it does not establish a measured cost saving on the current service.

## 18 Implementation evidence and reproducibility

### Follow a request through the code

The core uncertainty implementation is apps/api/recros_api/hierarchy_regret.py. Its pair gap function accepts partial labels, lower and upper preference endpoints and implication edges. It builds a closure graph, invokes a flow backend and returns an exact hard model value with a witness. The flat gap function provides the shared weight relaxation; the independent utility function supports an ablation.

The movie study is ml/src/recros_ml/research/hierarchy_holdout.py. It prepares identities and windows, fits background models, creates profiles, computes candidate scores, learns active preference intervals, generates masks, compares methods and records per profile results. Its lookup routine keeps the reference first item fixed while comparing stopping bounds. The book and recording adapter is ml/src/recros_ml/research/domain_holdout.py. The three domain report combines preserved results rather than retuning the movie study.

The current FastAPI service exposes a local hierarchy demonstration. That demonstration illustrates the declared matching calculation. It is not a live experiment enrolling the historical source users, and a selected demonstration example should not be used as an independent performance sample. Broad catalog discovery and the tiny student runtime are separate modules.

### What is frozen and what is tested

The experiment saves source integrity receipts, corpus identities, split cutoffs, profile partitions, validation grids, selected parameters, masks or query traces, per profile recommendations and outcomes. A hash is a digest of file contents; changing the contents changes the expected digest. Checksums catch incomplete downloads and unintended modifications. They do not guarantee that source metadata are semantically correct.

Completed runners refuse to overwrite saved results. A reproduction should use a separate output or clean checkout and the same declared inputs. Repeatedly making new splits until a favorable result appears would weaken the evidence. The movie results are preserved while books and songs are added independently.

The current API and ML suite has 116 passing tests. Those tests cover contracts such as self comparison, implication propagation, exact small cases, background exclusion, temporal isolation, identity matching and EASE equations. Test passing supports implementation correctness for the tested cases. It does not validate that users enjoy recommendations, that annotations are complete or that the project is globally novel.

### Evidence map

| Topic | Repository evidence |
| --- | --- |
| Latest three domain results and limitations | docs/milestone2/hierarchy/domains/RESULT.md |
| Machine readable comparison | docs/milestone2/hierarchy/domains/comparison.json |
| Original movie holdout | docs/milestone2/hierarchy/heldout/RESULT.md |
| Mathematical derivation and scope | docs/milestone2/hierarchy/DERIVATION.md |
| Controlled structural experiment | docs/milestone2/hierarchy/RESULT.md |
| Novelty and attribution review | docs/milestone2/hierarchy/NOVELTY_CHECK.md |
| Product catalog and label coverage | docs/milestone2/CATALOG_DISCOVERY_AUDIT.json |
| Earlier discovery pilot | docs/milestone2/results/RESULTS.md |
| Scripted information planning | docs/milestone2/results/policy/RESULTS.md |
| Representation collisions | docs/milestone2/REPRESENTATION_AUDIT.md |
| Actual tiny language model | docs/milestone2/transfer/STUDENT_EXPERIMENT.md |
| One person source review | docs/milestone2/transfer/HUMAN_READING_PILOT.md |
| Core graph solver | apps/api/recros_api/hierarchy_regret.py |
| Movie experiment | ml/src/recros_ml/research/hierarchy_holdout.py |
| Book and song experiment | ml/src/recros_ml/research/domain_holdout.py |

The first milestone source is /Users/mansitibrewal/Downloads/may_final_report_llmslm.pdf. The current deck is docs/milestone2/deliverables/Recros_three_domain_results.pptx. All relative locations in this chapter are relative to /Users/mansitibrewal/chronicles/Recros.

## 19 Research originality and the next defensible step

Novelty can mean a new model class, a new tractable special case, a new derivation, an improved bound, an empirical finding, or a carefully documented failure condition. These are different contribution types. Our strongest candidate is the specialized exact formulation and its structural fault extension, supported by implementation checks. The three domain extension improves the strength of the evaluation, rather than proving an accuracy breakthrough.

Known prior art includes maximum weight closure and graph cut representability; minimax regret and joint feature and preference elicitation; hierarchical music labels; and fine grained aspect transfer across recommendation domains. We cite those sources. Finding no exact match in a targeted search is not proof of worldwide priority. A paper claiming a first would require a deeper review and external scrutiny.

The most useful next step is to establish a setting where the facet utility predicts independently judged preferences well enough to merit deployment. Then measure whether coherent acquisition preserves relevance while reducing actual annotation expenditure. That study should predefine candidates, utility selection, annotation errors, cost units, stopping threshold and a relevance or noninferiority criterion.

For a cross domain result, recruit people with genuinely linked ratings or judgments across movies, books and songs, or use an appropriate linked source. Freeze a source domain history and evaluate independently obtained target domain outcomes. Compare against strong target only, content, collaborative and LLM based alternatives using the same information budget. A small exploratory pilot can demonstrate feasibility, but it cannot carry broad population claims.

For cold start, create explicit zero or low history conditions, new item conditions and missing metadata conditions separately. For long tail, evaluate the less popular catalog rather than extrapolate from the selected head. For explanations, evaluate support, score faithfulness and user usefulness separately. For the tiny student, improve source training and independent evaluation before claiming compression succeeds. These are proposed follow-ups, not completed results.

### Primary references for deeper reading

GroupLens MovieLens 20M data documentation: https://grouplens.org/datasets/movielens/20m/

Goodbooks source and metadata documentation by Zygmunt Zajac: https://github.com/zygmuntz/goodbooks-10k

Last.fm original source README and permitted academic mirror: https://github.com/eifuentes/lastfm-dataset-1K

AcousticBrainz genre dataset author documentation: https://mtg.github.io/acousticbrainz-genre-dataset/data/

LTO author release used in this project: https://zenodo.org/records/19367236

EASE by Harald Steck in 2019: https://arxiv.org/abs/1905.03375

Metric definitions in RecBole documentation: https://recbole.io/docs/recbole/recbole.evaluator.metrics.html

Picard on maximum closure in 1976: https://doi.org/10.1287/mnsc.22.11.1268

Kolmogorov and Zabih on graph representability in 2004: https://www.cs.cornell.edu/~rdz/Papers/KZ-PAMI04.pdf

Boutilier, Regan and Viappiani on online feature elicitation in 2009: https://icml.cc/2009/papers/427.pdf

Regan and Boutilier on concept and utility elicitation in 2009: https://www.kevinregan.com/files/recsys09.pdf

CATN on fine grained cross domain aspect transfer: https://arxiv.org/html/2005.10549v2

These primary sources support the attributed methods and source provenance. Our own result files supply the measured project numbers. The bibliography in the original PDF is preserved as part of that earlier report; reproducing its citations here would not establish that every earlier empirical claim has been rerun.

## 20 Glossary and common confusions

| Term | Meaning in this project |
| --- | --- |
| Available catalog | Items eligible under the source and history rules |
| Candidate pool | Sixteen retrieved works examined by the decision layer |
| Top K | First K recommended positions |
| Historical profile | Known prior or randomly supplied interactions from one source user |
| Background users | Other users supplying reference similarity and popularity |
| Explicit feedback | Direct ratings or supplied preferences |
| Implicit feedback | Actions such as plays, with ambiguous motivation |
| Facet | A property dimension such as genre, tone or language |
| Metadata bit | Present or absent value for one item facet in the reference |
| Unknown | An unresolved fact rather than a negative fact |
| Implication | Child presence logically requires parent presence |
| Propagation | Inferring required known ancestors or absent descendants |
| Completion | Assignment to all unresolved labels |
| Coherent completion | Assignment satisfying observations and hierarchy |
| Preference weight | The model's contribution for a facet |
| Signed weight | May be positive, negative or zero |
| Interval box | Independent allowed range for each preference coordinate |
| Shared preference | The same possible weights evaluate both candidates |
| Utility | Declared matching score rather than enjoyment probability |
| Pair gap | Largest modeled challenger advantage over a chosen item |
| Regret | Largest nonnegative gap across challengers |
| Minimax | Choose the item with the smallest worst case regret |
| Witness | A feasible modeled completion attaining a computed gap |
| Relaxation | A larger permitted set that can increase a worst case bound |
| Phantom regret | Gap created by impossible feature combinations |
| Closure | Node set containing all implications of its selected nodes |
| Cut | Partition separating graph source and sink with paid capacities |
| Exact | Correct optimum under the declared model assumptions |
| Certificate | Conditional statement that a normalized bound passes the threshold |
| Fault budget | Declared allowed number of implication violations |
| Conservative bound | May exceed the true optimum while remaining an upper bound |
| Gamma | Strength of facet utility in the decision model |
| Alpha | Mixture of content and collaborative reference signals |
| Regularization | Penalty or smoothing that restrains unstable fitted parameters |
| EASE | Established regularized linear collaborative item model |
| ItemKNN | Collaborative item neighbor method |
| TF IDF | Lexical term based numeric text representation |
| Embedding | Numeric representation, often learned but not necessarily an LLM output |
| LLM | Large language model used for language tasks |
| Tiny student | Actual small causal transformer in the separate extraction trial |
| Compact ranker | Efficient nonlanguage model ranking component in the original PDF |
| Training | Adjusting model parameters using examples |
| Inference | Applying already fitted parameters |
| Validation | Selecting settings before the final outcome assessment |
| Test | Evaluating frozen choices on withheld outcomes |
| Leakage | Using information that should not be available for the stated task |
| Masking | Hiding metadata reference bits in the controlled experiment |
| NDCG | Normalized gain that rewards relevant items near the top |
| Precision | Fraction of recommendations marked relevant |
| Recall | Fraction of eligible relevant works recovered |
| MAP | Mean average precision under the implementation's specified convention |
| AUC | Threshold independent ordering of classification positives and negatives |
| Bootstrap | Resampling profiles to describe sample variation |
| Paired contrast | Difference between methods on the same profiles |
| Confidence interval | Uncertainty summary for the estimator under its procedure |
| Noninferiority | A planned claim of not losing more than a justified margin |
| Coverage | Fraction of eligible items receiving recommendation exposure |
| Novelty | Unfamiliarity or low popularity under an explicit definition |
| Diversity | Differences within the recommended set |
| Fairness | Treatment or exposure under an explicit group or provider policy |
| MBID | MusicBrainz identifier specifying recording identity in this task |
| Checksum | Content digest for integrity checking rather than semantic truth |
| Preregistration | Public or external prospective protocol registration, not merely a local hash |

## 21 A worked end to end toy example

This example is invented only to explain the flow. It is not an additional project measurement. A person has a short prior history favoring broad adventure and avoiding a particular distressing subtype. Two candidate items A and B are retrieved. A has unresolved parent and child facets; B has neither. The background scores are equal, and the signed facet weights are plus one for the parent and minus one for the child.

The flat checker permits four assignments for A, including absent parent and present child. That gives A utility minus one, so it reports a possible loss of one against B. The coherent checker permits three assignments because the child implies the parent. Its worst gap is zero. It can therefore certify A at a zero threshold without acquiring either bit, provided the implication and observed facts are correct.

If the hierarchy edge is invalid for the true content, the excluded fourth assignment might occur. A hard zero certificate is then unsafe. Allowing one structural fault restores a bound of one. If the user really dislikes the parent despite the learned positive weight, neither label completion calculation captures the true taste. The preference model must also be adequate.

Now suppose a held out actual rating marks A as disappointing. That does not contradict the graph solver's exact arithmetic. It contradicts any unconditional claim that its utility predicted enjoyment. The real experiment measures that distinction: small metadata acquisition advantages coexist with unestablished or lower relevance.

Finally suppose validation selects gamma zero. Facet utility disappears and only the background score determines ranking. Inspecting parent or child bits cannot change that ranking utility. The earlier hypothetical acquisition saving still explains the mechanism at nonzero gamma, but it is not a reason to purchase labels for the zero weight deployment. This complete chain is the safest explanation of the project's result and limitation.

## 22 Understanding the earlier extraction scores

This chapter explains the F1 values in the separate tiny language model trial. Feature extraction asks whether a supplied passage supports a specified property. It is a classification task on passage and feature pairs, rather than the top five recommendation task. A reference positive says the passage supports the property under the rubric. A predicted positive says the model claims support.

| Outcome | Definition | Example |
| --- | --- | --- |
| True positive or TP | Model claims support and reference agrees | Both identify an investigation in the passage |
| False positive or FP | Model claims support but reference does not | Model invents an investigation without supporting text |
| False negative or FN | Reference supports it but model misses it | Passage describes investigation but model omits the label |
| True negative or TN | Both record no support | Neither finds evidence for that property |

Extraction precision measures how many positive claims are correct. Extraction recall measures how many reference positives the model finds. F1 combines them through a harmonic mean, which penalizes a model that makes few incorrect claims but misses most supported properties. These uses of precision and recall are analogous to recommendation metrics, but their examples and denominators differ.

$$\operatorname{Precision}=\frac{TP}{TP+FP},\qquad \operatorname{Recall}=\frac{TP}{TP+FN},\qquad F_1=\frac{2TP}{2TP+FP+FN}$$

The human source review has seven reference positives. DeepSeek records six true positives, zero false positives and one false negative. Its precision is six divided by six, or one. Recall is six divided by seven, about 0.857. F1 is twelve divided by thirteen, about 0.923. The student records zero true positives, two false positives and seven false negatives, giving F1 zero.

The teacher gated student makes no positive claims. Its precision denominator is zero, so precision is undefined. Its recall remains zero because it misses all seven positives, and its count based F1 is zero. Avoid saying that deleting every claim makes an extractor perfectly accurate. Abstention can prevent unsupported claims, but it also needs coverage and usefulness evaluation.

These are twenty binary decisions from one person's judgments on five usable paragraphs, not twenty independently recruited people. The six paragraph set includes one unsure response and had previously been used as development stimuli. The result measures supplied text support in that small pilot, not complete work understanding or statistical superiority in a wider population. It is also separate from the assistant authored eighteen passage comparison.

A teacher student setup supplies a larger model's answers as training targets for a smaller model. That can reduce annotation effort, but it passes along teacher errors and cannot by itself supply independent evaluation truth. Our student starts from random weights with limited local training, whereas the hosted teacher has very different training resources. The failed result therefore neither proves all small models are incapable nor validates our particular student as a replacement. It documents the actual outcome and points toward better training, evidence and independent evaluation.
