# Recros questions and answers for four presenters

Preparation for the original milestone recap and eight slide three domain presentation

This bank contains 160 anticipated questions with defensible answers. Each presenter has thirty two assigned questions, organized by their slides. Sixteen shared questions cover foundations and project wide criticism. Sixteen advanced questions cover the derivation and can be led by Presenter 4 with support from Presenter 2. It covers likely lines of questioning rather than promising that no judge can ask anything else.

Use the first sentence as an oral answer. The following explanation supplies context if the examiner asks why. Do not memorize unsupported claims to make the project sound stronger. If a requested measurement has not been made, explain exactly what has been measured and what would be needed. The technical handbook gives worked examples and evidence locations.

## Presenter 1 questions about the recap and slide 1

### P1 01 What was the original problem

We wanted recommendations across movies, books and songs that use personal interests while improving discovery, explanation and exposure. The original PDF identifies cold start, sparsity, popularity bias, filter bubbles, feedback loops, explainability, domain isolation and exposure imbalance. These are the product motivations. Our newest experiment addresses a narrower missing metadata uncertainty problem rather than proving that all eight are solved.

### P1 02 What exactly did the first milestone achieve

It established a literature review, a nine stage hybrid architecture and reported an MVP ranker with offline validation. The PDF reports 215,148 training rows, nineteen features, AUC 0.9373 and ranking metrics over 791 users, plus domain mixing and coverage. It explicitly leaves stronger baselines, fairness, explanations and online evaluation open. We distinguish those reported achievements from the newer preserved independent tests.

### P1 03 What are the nine stages

They are onboarding, LLM interpretation, persistent data and memory, candidate generation, compact ranking, diversity and fairness adjustment, explanation and cross domain enhancement, output, and feedback for later retraining. In service terms, the controller interprets the request, retrieval narrows the catalog, the ranker orders candidates, postprocessing handles list goals and the interface records feedback. The PDF is an architecture design, so a listed stage is not automatically a fully validated implementation.

### P1 04 What was the original scoring formula

Its weights were 0.30 user item similarity, 0.20 similar user affinity, 0.15 genre, 0.10 each for novelty, diversity and fairness, and 0.05 recency. They sum to one. Inputs still need compatible scales and precise definitions. The latest isolated hierarchy experiment uses a background score plus gamma weighted facet utility, so it is not a reproduction of all seven original signals.

### P1 05 Why choose those weights

The PDF provides those design weights, but does not establish that they are globally optimal. They prioritize relevance while reserving influence for discovery and exposure. A stronger claim would require validation over alternative weights and objective tradeoffs under a fixed protocol. We should not invent a tuning procedure for the original weights when the PDF does not document one.

### P1 06 Was the original SLM actually a language model

The described implementation was a gradient boosted decision tree, so compact ranker is the more precise term. The PDF uses SLM loosely for its small fast component, but a tabular tree model does not perform next token language modeling. We later trained a separate actual tiny causal language model for source feature extraction. Its evaluation is distinct from the original ranker's AUC.

### P1 07 What does AUC 0.9373 mean

It is the PDF's validation measure of how well the binary classifier orders positive versus negative examples across thresholds. It is not ninety three percent top five recommendation accuracy and not an enjoyment probability. Top K relevance depends on the candidate pool, target definition and ordering near the top. That is why the PDF also reports ranking measures and why the newer studies evaluate NDCG separately.

### P1 08 What did iteration 342 establish

It was the reported best validation boosting iteration under early stopping. An iteration is part of the model's training process, not a count of users or language model conversations. Its significance is that the selected training point optimized the stated validation criterion. Without rerunning the original protocol we should not add claims about convergence or generalization beyond the report.

### P1 09 Why was the original MAP so high

The PDF itself warns that MAP at five may be inflated by validation characteristics. We would need its exact candidate construction, relevance labels and MAP normalization to explain the value confidently. It could not be interpreted responsibly from one number alone. We report 0.9770 as an earlier reported result, while relying on the newer explicit protocols for our latest claims.

### P1 10 Does thirty five percent cross domain output prove transfer

It proves that the reported output mixed domains, not that transferred preferences improved target domain relevance. A cross domain transfer claim needs the same person's source and target data and an independent usefulness comparison. The original 0.3518 fraction and 2.40 domains describe composition. Our latest public sources have unrelated user populations and therefore cannot validate linked user transfer.

### P1 11 What does coverage 4.07 percent mean

It means that about 4.07 percent of the defined catalog received recommendation exposure across the evaluated top twenty lists. It does not mean that only 4.07 percent of recommendations were relevant. Coverage depends on the catalog, number of users and list length. The PDF identifies limited coverage as a weakness, and we keep it separate from individual recommendation quality.

### P1 12 What does the novelty score minus 2.98 mean

It is the original report's mean negative log popularity statistic, whose exact scale needs its underlying popularity definition. We cannot translate it into a percentage or compare it directly with a different implementation. If popularity were a probability, negative log values would be nonnegative, so the reported negative value deserves checking the actual definition. The report's safe qualitative conclusion is that novelty remained a weakness.

### P1 13 Have you completed the whole original architecture

We have working local recommendation and research components, but the PDF's proposed infrastructure and evaluation plan are broader than the verified latest work. A named technology such as Redis, Pinecone or Celery is not proof of a deployed component. We can demonstrate the actual local catalog and graph solver and point to preserved experiments. We should label future production integration and online studies as remaining work.

### P1 14 What changed after the first milestone

We expanded the usable catalog, improved automatic three domain discovery, investigated representations and a tiny extraction model, then developed and evaluated a precise hierarchy uncertainty formulation. The latest tests add independent historical relevance outcomes for movies, books and recordings, strong baselines and failure analysis. Those are separate achievements; they should not be combined into an unmeasured overall accuracy improvement.

### P1 15 What is the current research question

We ask whether respecting relationships among missing item labels removes impossible uncertainty and whether this helps ranking or metadata acquisition. For example, a valid subtype should not be present when its parent is absent. The exact model excludes that completion. The empirical tests find small lookup savings but do not establish improved recommendation relevance, so both parts of the question have distinct answers.

### P1 16 Why is this worth researching if genres already exist

The question concerns decision uncertainty, rather than merely attaching more genre tags. When unknown labels and uncertain signed preferences interact, a flat model can admit impossible worst case worlds. We derive a specialized exact computation and a fault extension, then measure its effect. Hierarchical tagging and graph cuts are prior art; the candidate contribution is the particular formulation and documented evidence, not inventing genres.

## Presenter 1 questions about slide 2

### P1 17 Why are there only 789 movies in the test

The test uses a reliable intersection with theme labels, matched ratings and prior availability, not the entire movie catalog. The source has over twenty million ratings, and 1,242 films match the ontology, but 789 satisfy the test background availability rules. Conservative identity matching excludes ambiguous joins. This limits generalization but avoids assigning one film's outcomes to another film's themes.

### P1 18 Are you really using enough data

The sources contain millions of real events, while the decision layer uses deliberately bounded annotated catalogs. Books have 5,976,479 source ratings and songs have 19,150,868 source plays. Dataset size, evaluated catalog size and test profile count answer different questions. Large sources help fit background models, but 320 or 181 evaluated profiles still limit precision and population scope. More rows alone do not validate intent.

### P1 19 What are the exact book data and splits

We use a 3,000 book subset from Goodbooks, 128 validation profiles and 320 test profiles. Twenty random known ratings form each evaluation profile, and remaining eligible ratings are held out. Background people occupy disjoint ID partitions. There are no explicit timestamps, so this is a cross sectional random evaluation, not a forward temporal book prediction study.

### P1 20 Why not use a chronological split for books

The supplied ratings do not include explicit timestamps, so we cannot truthfully reconstruct when each rating occurred. Inventing time from file order would create a false chronology. We label the book split random and avoid comparing its score directly with the chronological tasks. A time stamped book source would be needed to evaluate future book recommendations with the same temporal interpretation.

### P1 21 What are the movie and song time windows

The movie matched ratings train through 19 February 2006 and validate through 2 October 2009, with later test outcomes. Songs train through 19 February 2008 and validate through 14 October 2008, with later listening outcomes. These are global cutoffs within the declared matched sources. Profiles use permitted past data, and models must not use later outcomes to choose parameters.

### P1 22 Are the users the same across all three domains

No, MovieLens, Goodreads and Last.fm people are unrelated in this study. Numeric IDs cannot be joined across sources. We test algorithmic applicability in three domains independently. To claim transfer of a person's taste from movies to books or songs, we need linked profiles or a prospective collection with source history and independently judged target outcomes.

### P1 23 Did you recruit 821 users

No, the 320 movie, 320 book and 181 song profiles come from historical public datasets. They total 821 evaluated profiles across separate tasks, not 821 newly recruited participants. The project's supplied text review had one participant. We describe historical evaluation and the small human pilot separately to avoid inflating the human evidence.

### P1 24 Why do you call songs recordings

The identity key is a recording MusicBrainz ID. A composition can have different recorded versions and an artist has many works. We join exact recording IDs to genre labels and retain title and artist for display. Using only artist identity as the recommended item would evaluate a different task. Artist metadata is used in one content baseline, but the recommended objects remain recordings.

### P1 25 Does a song play mean the person likes the song

A play is an implicit listening outcome, not a declared liking judgment. We evaluate whether new recordings are played later and learn relative past intensity from log play counts. Repetition may reflect playlists or context. We therefore report held out listening relevance and do not translate the score into enjoyment, a star rating or an explicit dislike when an item is unobserved.

### P1 26 Why did you add four to song play counts

The adapter stores four plus log of one plus plays so existing positive interaction routines can process all observed recording events. It is a software compatibility representation, not an invented four star judgment. The preference fit centers the outcome, which removes the constant. The source and evaluation remain listening events, and we state that clearly in the report.

### P1 27 How do you prevent data leakage

We freeze source identities, partitions and windows, exclude evaluated people from background fitting, and select parameters on validation rather than test. Candidate retrieval does not insert future positives. Repeat plays are aggregated inside their historical windows and book aggregate quality fields do not score popularity. These controls reduce specific leakage risks, while retrospective labels, selection rules and observational exposure still limit the study.

### P1 28 Why select popular subsets if popularity bias is a problem

The local benchmark needs sufficient prior outcomes, reliable recording or book identity and available labels at feasible computation cost. That produces a head biased annotated subset. We disclose that it cannot establish long tail or item cold start performance. The broader product's discovery slots and the independent annotation benchmark are different components and require different evaluation before claiming debiasing success.

### P1 29 Where do the hierarchical labels come from

Movies use the Literary Theme Ontology. Books use Goodbooks shelves with a frozen project genre mapping and separate metadata facets. Songs use published AcousticBrainz genre paths. These sources have different reliability and coverage, and their hierarchies are not our invention. The task masks existing reference bits rather than treating freshly generated LLM labels as independent semantic ground truth.

### P1 30 Are all catalog entries fully labeled

No, the catalog audit shows substantial missing and uneven metadata, especially for songs. The full product contains 222,915 works, but the benchmark uses separate annotated subsets. Geographic or era mentions in text are not verified complete settings, and publication year is not story era. The hierarchy solver preserves unknown values; it does not manufacture complete annotations for all records.

### P1 31 How do you know the downloads were complete

The project records source checksums and pinned file hashes, and rejected incomplete downloads before use. That verifies byte level integrity relative to the published sources. It does not prove that every shelf vote or genre label is correct. Data identity, download integrity and semantic annotation quality are separate checks, with the last still requiring stronger independent validation.

### P1 32 Could the old PDF scores be compared with these new scores

Not as a direct before and after improvement or decline. The earlier reported model and evaluation differ in candidates, source subsets, K, split details and targets. A fair comparison requires a common task and protocol. We recap the PDF's reported results historically, while making our latest claims from the new paired within domain tests and their preserved evidence.

## Presenter 2 questions about slide 3

### P2 01 What is NDCG at five

It measures how well the first five results place evaluation relevant items near the top, normalized by an ideal ranking for that task. Binary relevance contributes one divided by log base two of rank plus one. A score of one means ideal ordering under the reference labels, not guaranteed enjoyment. The handbook works through a two positive example so you can calculate it aloud.

### P2 02 Why use NDCG instead of accuracy

Recommendations are ordered lists, and the first position matters more than a low position. Classification accuracy also depends heavily on the many unobserved user item pairs and an arbitrary decision threshold. NDCG directly evaluates ordering near the displayed positions. We also preserve recall and other measures, because no single number captures discovery, exposure, explanation quality or satisfaction.

### P2 03 What is the difference between precision and recall

Precision divides relevant recommendations by list length; recall divides recovered positives by all eligible held out positives. Two relevant results in a five item list give precision 0.4. If four eligible positives exist, recall is 0.5. Those denominators describe different goals. Unobserved recommendations are nonrelevant under the offline convention, not proven disliked works.

### P2 04 Why only sixteen candidates and five outputs

We isolate a locally feasible decision layer using a common sixteen item retrieved pool and a five item display. The pairwise solver can require N times N minus one cuts, so restricting N controls cost. The experiment does not establish optimal retrieval or full catalog hierarchy performance. Relevant works missed in retrieval cannot be recovered by rearranging these sixteen candidates.

### P2 05 Are the comparisons fair if the pool comes from the reference

They fairly isolate ranking among the same candidates, but the reference retriever shapes what those candidates are. Every paired method receives identical works without inserted future positives. We therefore report a separate full catalog baseline audit and avoid claiming complete system superiority. A stronger study would compare retrieval systems as well as decision layers under a common information budget.

### P2 06 What is the reference model

It is a validation selected mixture of historical collaborative and content signals, with a popularity fallback where needed. Movie content uses genres, book content uses authors and song content uses artists. Movies select content weight zero; books and songs select one half. This reference is the chosen model in the paired family, not the globally strongest possible recommender.

### P2 07 What is EASE

EASE is an established regularized linear collaborative item model introduced by Harald Steck. It learns item to item coefficients from the background interaction matrix with a zero diagonal, then scores candidates from a person's history. It needs no pretrained language weights. We tune its regularization on validation and report it because a credible research evaluation must include a strong simple baseline.

### P2 08 What does flat regret mean

It maximizes challenger advantage using uncertain labels independently after propagating sound known facts, while sharing the same preference vector across the pair. It can admit impossible combinations among still unknown parent and child labels. The hierarchy model keeps those relationships. Flat is therefore a meaningful relaxation rather than a baseline denied obvious propagation or given fewer observed labels.

### P2 09 Why does the hierarchy score slightly lower for books

The coherent model can calculate its declared worst case utility exactly without that utility predicting book preference well. In this sample its NDCG is 0.5994 versus flat 0.5999. The paired interval crosses zero, so that small difference does not establish a general loss against flat. The more important comparison is that both nonzero rerankers are below the reference and EASE here.

### P2 10 Did movies and songs show an improvement

They show small positive point estimates against flat, but not an established improvement. Movie difference is about 0.0010 and song difference about 0.0003, with intervals including zero. A positive average alone is insufficient to headline a gain. It also does not establish that the hierarchy is equivalent or safely noninferior to a stronger baseline.

### P2 11 What does a confidence interval containing zero mean

The estimated difference is compatible with zero under the stated resampling procedure, so we cannot conclude a positive ranking effect from this analysis. It can also include both small gains and losses. It does not mean there is no possible effect or that both methods are proven equal. A noninferiority claim needs a predefined acceptable loss margin and its own analysis.

### P2 12 Why use a paired bootstrap

Every profile receives recommendations from both methods, so their scores are dependent. We first calculate each profile's hierarchy minus flat difference, then resample profiles with replacement and average those paired differences. This retains the shared user comparison and usually provides a more appropriate uncertainty estimate than independently resampling the methods. It still assumes the sampled profiles adequately describe the task population.

### P2 13 Did you correct for testing three domains

The original nominal intervals are preserved, and a supplemental analysis uses twenty thousand resamples with 98.33 percent intervals within each three domain endpoint family. The wider ranking intervals also include zero. This is a descriptive Bonferroni adjustment for that family, not a claim of controlling every comparison made across the entire project or a new parameter selection procedure.

### P2 14 Why are the book scores much higher

The book task has a random split, different source population, target counts and selected catalog. NDCG values across those conditions are not a ranking of intrinsic domain difficulty. We compare methods within each row using common candidates and outcomes. Claiming that books are easier by comparing 0.62 with 0.16 would ignore substantial protocol differences.

### P2 15 What other baselines did you test

The preserved reports include popularity, metadata content, ItemKNN, the reference hybrid, EASE, marginal imputation and a complete annotation diagnostic. The last uses unmasked reference labels and is not a deployable missing data baseline. These comparisons help distinguish logical uncertainty handling from predictive strength. The compact slide emphasizes the main contrast and a strong comparator rather than displaying every stored row.

### P2 16 Does using independently held out ratings solve all evaluation concerns

It strengthens the result compared with scoring against a utility we invented, but historical outcomes remain observational and selectively exposed. Unobserved works are not necessarily disliked, annotations are retrospective, and selected catalogs limit scope. The held out outcome is independent of the matching calculation, while it is not randomized satisfaction evidence. We retain those limitations when interpreting the scores.

## Presenter 2 questions about slide 4

### P2 17 What exactly counts as one lookup

One lookup reveals a single hidden candidate facet bit from the recorded reference. It is an annotation simulation, not a measured LLM request or a question to a person. The reference treats listed facets and ancestors as present and unlisted active facets as zero. Those negative bits are a closed world convention rather than verified semantic absences in complete works.

### P2 18 What stays fixed during acquisition

The reference's five recommendations and the shared adaptive query sequence stay fixed. Both stopping rules inspect the same progressively revealed information and use sound propagation. We measure when each reaches its conditional first item regret threshold or exhausts twenty four lookups. This isolates the effect of the bound, rather than conflating it with better recommendations or different questions.

### P2 19 What is worst case regret in ordinary language

It is how much another candidate could outperform the chosen item in the most unfavorable allowed combination of unknown labels and preference weights. The allowed worlds come from our explicit model, not from every conceivable human taste. Regret zero means no challenger wins within those worlds. A small regret certificate does not guarantee actual enjoyment if the model misses the person's true preferences.

### P2 20 Why does hierarchy reduce regret

It excludes completions that violate valid subtype implications. Maximizing over fewer allowed worlds cannot increase the worst case gap. A flat model can otherwise imagine a disliked subtype present while its liked parent is absent, even if that combination is logically impossible. This produces phantom regret. The implication must be valid, or excluding a real world can instead create false confidence.

### P2 21 Does the flat method already propagate labels

Yes, both methods use sound known fact propagation. A present child establishes its parent and an absent parent excludes children. The difference remains when related labels are still unknown: flat treats their possibilities separately, while exact hierarchy couples them. This avoids constructing a weak baseline that loses merely because it ignores an obvious known fact.

### P2 22 How is the 6.5 percent calculated

We subtract exact mean 6.41875 from flat mean 6.8625 and divide the saving 0.44375 by 6.8625. The resulting reduction is about 6.4663 percent, rounded to 6.5. Books and songs use the same calculation on their unrounded means. Computing from displayed rounded cells can produce a slightly different percentage, so the report preserves exact numbers.

### P2 23 Why are the lookup counts fractional

Each profile uses an integer count, but the slide shows the average across all profiles. Some people save several lookups while many save none. For movies the total saved bits are 142 across 320 profiles, giving 0.44375 mean saving. A fractional mean does not imply a partial annotation operation for an individual.

### P2 24 Does this mean 6.5 percent fewer LLM calls

No actual call saving has been measured. An LLM response may return many labels at once, whereas the simulation counts one binary bit per lookup. Batching, caching, retries, source quality and tokens change real cost. The defensible claim is fewer simulated reference bit lookups under the fixed nonzero matching utility, not measured API charges, latency or human question savings.

### P2 25 What does threshold 0.20 mean

It limits normalized worst case matching regret on the declared utility scale. The normalizer combines background score range and weighted maximum interval magnitudes. It is not twenty percent probability of failure or an eighty percent satisfaction guarantee. Different thresholds trade certification effort against the allowed utility gap and would need sensitivity or operational justification for deployment.

### P2 26 Does the certificate cover the five item list

It checks the first reference item against its fifteen retrieved challengers. The five recommendations remain unchanged, but only that first item receives the reported conditional certificate. The method does not establish optimality of the five item set or compare with the entire catalog. A list level objective involving diversity or position effects would need a different formulation.

### P2 27 Why cap the budget at twenty four

It is the declared local experiment's cost limit and makes unresolved cases visible. It is not a universal optimum or a number learned from actual annotation prices. More queries might improve certification while adding cost. We include budget exhausted runs in mean expenditure and certification denominators so the result cannot conceal difficult cases.

### P2 28 Are unsuccessful profiles included in the saving

Yes, each contributes its actual lookup expenditure up to the cap. We do not average only among successful certificates. A method can exhaust the same budget without passing in both models, contributing zero saving. This keeps the average tied to all evaluated profiles rather than a selectively easy subgroup.

### P2 29 Is earlier stopping a genuine empirical discovery

The earlier or equal ordering follows mathematically from the coherent bound being no larger along the shared sequence. The experiment measures its size and frequency on rating derived profiles. It sometimes saves several queries and frequently saves none. We should not present an inequality built into the method as independent evidence of better human decisions.

### P2 30 How are the next labels selected

The shared adaptive schedule uses history only prevalence entropy and coefficient or ancestor influence to prioritize unknown bits. Roughly, it favors unresolved features that may vary and matter to the utility. It is not a trained conversational preference policy. Both methods receive the same actions, so the comparison isolates stopping bounds rather than optimizing their separate acquisition strategies.

### P2 31 Do added computation costs erase the saving

They can when metadata is cheap. A movie replay added about 27.93 milliseconds mean computation while saving about 0.44375 bits, giving a simplified break even latency near 62.9 milliseconds per bit. We did not measure actual annotation latency, and real services batch labels. This exploratory calculation motivates a real cost study rather than proving current end to end savings.

### P2 32 Why acquire labels if validation sets gamma to zero

No genre acquisition is needed for that zero theme ranking utility. The acquisition experiment uses separately fixed gamma one half to study a nonzero mechanism. Its saving does not justify deploying the model validation rejected. A practical follow-up must first establish an adequate nonzero utility or a separate decision task where checking those facts has value, then measure actual cost savings.

## Presenter 3 questions about slide 5

### P3 01 What exactly does the chart show

It shows the fraction of evaluated profiles saving at least one reference bit lookup at fifty percent masking. The counts are nineteen of 320 movies, thirteen of 320 books and five of 181 songs. These become about 5.9, 4.1 and 2.8 percent. It is not a chart of NDCG, average bit reduction or actual user satisfaction.

### P3 02 Why is movie benefit 5.9 percent here but 6.5 percent before

They use different denominators. Slide 5 divides beneficiaries by all profiles. Slide 4 divides mean saved lookups by mean flat lookups. Nineteen profiles can save several bits each, producing a mean cost reduction that differs from their population fraction. Neither percentage should be relabeled as the other.

### P3 03 Is the benefit too small to matter

The measured average is small and concentrated, so broad practical significance is unestablished. It could matter in a setting with costly individually acquired metadata and an adequate nonzero utility, but we have not measured that setting. Exact computation and a documented conditional saving are defensible outcomes. They are not enough to claim a major production recommendation improvement.

### P3 04 How much does a benefiting movie profile save

The descriptive mean among the nineteen benefiting movie profiles is about 7.47 bits. Across all 320 profiles the mean is 0.44375. The beneficiary only number is much larger because most profiles save nothing. We should present the overall mean and beneficiary frequency first, rather than suggesting 7.47 is typical for every evaluated person.

### P3 05 How can only five song listeners yield a positive interval

A few profiles can contribute enough nonnegative savings to make the bootstrap mean interval positive under the recorded procedure. That does not make the benefit widely shared or stable across other populations. The supplemental adjusted lower endpoint for songs is only about 0.0055 bits. The small beneficiary count is therefore essential context for the numerical interval.

### P3 06 Does every hierarchy profile use fewer labels

No, the hierarchy can stop earlier or at the same time on the shared sequence, and most stop at the same time or exhaust the same budget. A tighter bound need not cross the threshold sooner. The experiment's central distributional finding is that only a minority receive any strict lookup reduction under this configuration.

### P3 07 Can the hierarchy require more labels

Under the valid hard model and identical information sequence, its bound cannot exceed flat, so its threshold stopping time cannot be later. That statement depends on the shared schedule, correct facts and implications. If real methods use different actions, have annotation errors or pay differently for batches, total real costs can differ and this ordering does not settle them.

### P3 08 Why do many people get no benefit

Both models may already pass the threshold, cross it after the same informative query, or remain above it until the budget ends. The active facets may also lack relevant unknown parent subtype interactions. The current reports quantify the observed counts; they do not establish a complete causal taxonomy of every zero saving profile. A dedicated trace analysis could investigate those mechanisms further.

### P3 09 Did you select only easy cases for the chart

The chart uses all sampled test profiles in the declared condition, with unsuccessful cases retained. The cohorts and protocols are saved before scoring, and beneficiary counts derive from paired query traces. Dataset eligibility and popular annotated subset selection still narrow the evaluated population. We disclose those choices rather than claiming a representative sample of all entertainment users.

### P3 10 Does the song hierarchy being larger guarantee more savings

No, the source has 327 facets, but a request uses only its active subset and its particular coefficients and observations. Extra labels that do not influence a meaningful challenger gap may have no effect. Structure, weight signs, information state and threshold matter. Raw ontology size is not a monotonic guarantee of relevance or lookup reduction.

### P3 11 Why not show only a large average improvement

That would hide how few profiles benefit. A responsible recommendation evaluation includes effect magnitude, uncertainty, distribution and failure rate. The chart helps an examiner see that a positive mean saving can coexist with nearly everyone receiving no strict reduction. It makes the practical scope of the result assessable.

### P3 12 Did saving labels change recommendations

No, the acquisition experiment keeps the same five item reference list throughout. Earlier stopping changes the amount of acquired metadata used for a conditional first item bound, not which recommendations a person sees. A ranking comparison occurs separately on slide 3. Keeping these experiments distinct prevents an annotation saving from being described as a relevance gain.

### P3 13 Would users notice the saving

We have not measured a visible user benefit. If annotation were an expensive background process, it might affect latency or cost, but actual calls and end to end response time were not measured. If facts were cached, there might be no noticeable improvement. A user preference question is also a different action from one source reference bit lookup.

### P3 14 Can you generalize these frequencies to other datasets

Not without further tests. They are conditional on the sources, selected catalogs, limited histories, artificial masks, intervals, threshold and cap. A larger representative study or multiple datasets and windows would strengthen the inference. Bootstrap intervals resample these profiles; they do not account for every possible shift in taxonomy, culture or annotation practice.

### P3 15 Did you inspect every beneficiary after seeing results

The raw predictions and query traces are preserved and can be audited, but examples chosen afterward are illustrations rather than independent performance evidence. The numerical chart uses the full frozen sample, not handpicked demonstrations. Any later explanatory trace analysis should be labeled post result analysis and should not alter the original denominator or protocol.

### P3 16 What is the useful message from this slide

Logical consistency can reduce unnecessary uncertainty for some cases, but the benefit is far from universal. The mean saving must be read alongside nineteen, thirteen and five beneficiaries. This points toward studying when hierarchy matters and whether those cases have real acquisition costs, rather than adding tags and assuming all users improve.

## Presenter 3 questions about slide 6

### P3 17 What does seventy five percent missing mean

The experiment hides seventy five percent of the active reference metadata bits for a candidate under its declared mask procedure. It does not remove seventy five percent of the users, interactions or source files. Preferences still come from known history and the query cap remains twenty four. This creates a more difficult metadata uncertainty condition.

### P3 18 What is a certificate

It means the computed normalized first item worst case regret is at most 0.20 under the declared matching model. It is conditional on correct observed labels, valid hierarchy and adequate preference intervals. It is not a guarantee that the person enjoys the work, that every returned item is optimal, or that all catalog candidates have been checked.

### P3 19 What happens to profiles without a certificate

They reach the budget without demonstrating that conditional threshold. Their recommendations still exist, but the checker must label them unresolved rather than certified. For books, 278 of 320 profiles remain uncertified under hierarchy at the stress condition. This does not necessarily prove their recommendations are bad; it shows the information and budget are insufficient for this bound.

### P3 20 Why are book certifications so low

Under this model and mask, only 42 of 320 book profiles pass the threshold within twenty four queries. The structure, active coefficients, challenger scores and uncertainty all affect stopping. We cannot assign a single proven cause from the aggregate count. The defensible conclusion is high unresolved rate in this setting, not that books intrinsically require more questions than other media.

### P3 21 How much does hierarchy improve certificate coverage

At the stress condition it adds ten movie certificates, three book certificates and one song certificate over flat. The total hierarchy counts are 129, 42 and 60. These are conditional first item coverage changes, not accuracy improvements. They remain small relative to the unresolved profiles and should not be presented without the total denominators.

### P3 22 Why not increase the budget until everyone passes

That changes the cost question and may still not validate the utility. More source bits can resolve metadata uncertainty, but a poor preference model can remain wrong even with complete labels. The cap makes the current experiment comparable and reports failures honestly. A follow-up could study the cost certification curve while separately requiring useful independent relevance.

### P3 23 What exactly failed in ranking

The nonzero hierarchy reranker has lower held out NDCG than the reference for movies and books at seventy five percent masking, with nominal paired intervals entirely negative. Movie difference is about minus 0.0143 and book about minus 0.0234. This is a relevance measurement, separate from certification. A mathematically coherent utility can still predict taste poorly.

### P3 24 Did songs also fail

The song point estimate is lower than the reference by about 0.0112, but its nominal interval ranges from minus 0.0247 to plus 0.0025. Because that interval crosses zero, this test does not establish song harm at that nominal level. It does establish that a positive song ranking improvement has not been demonstrated.

### P3 25 How can a method certify a bad recommendation

It certifies only the declared model, so its guarantee may be irrelevant if the person's actual utility lies outside that model. A user might like relatable characters while our facets and weights emphasize genre. Correct calculation cannot make an incomplete taste representation adequate. Wrong observations or invalid implications can additionally invalidate even the model's claimed real world coverage.

### P3 26 What if the genre hierarchy is wrong

Hard enforcement can exclude a real completion and create false confidence. Our recorded parent subtype counterexample has hard modeled regret zero but actual regret one after one implication fails. A separate structural fault bound permits a declared number of violations conservatively. It does not establish that real ontology errors have been calibrated or solved in the three domain tables.

### P3 27 What if a known label is wrong but respects the hierarchy

The structural fault extension does not protect against that error. Observed facts remain hard in its formulation, so a wrong genre that is internally coherent can still exclude the truth. We need source quality controls, uncertainty about observations or an explicitly different noise model. Calling every error a hierarchy fault would obscure which assumptions the bound actually addresses.

### P3 28 Are the preference intervals calibrated

No, they are fixed sensitivity intervals of plus or minus twenty five percent of the learned coefficient magnitude. They do not carry a known coverage probability for human taste. Zero coefficients have zero width, potentially understating uncertainty about unseen properties. The matching certificate assumes the interval model is adequate, which the independent relevance results do not establish.

### P3 29 Does a missing label mean the feature is absent

In the real product it should remain unknown. The benchmark uses unlisted active tags as zero only in its closed world reference, then masks bits for controlled comparison. That allows reproducible simulation but can miss actual themes. The solver's exactness concerns this declared reference model, not exhaustive semantic truth about every movie, book or recording.

### P3 30 Are confidence and accuracy the same

No, confidence here is a worst case bound under an explicitly restricted utility model, while relevance uses independently held out outcomes. A tight bound can be correct for a model that predicts preferences badly. Neither a small numerical regret nor a passing certificate should be relabeled as calibrated satisfaction confidence.

### P3 31 Does this solve cold start

It addresses uncertainty about metadata in limited history tasks, not all forms of cold start. Each evaluated profile supplies twenty known works. We have not tested zero history users, entirely new providers or new unobserved items across the full long tail. Those require explicit separate protocols rather than interpreting a missing tag mask as a complete cold start solution.

### P3 32 Why show failures in a graduation presentation

They define the method's actual usefulness and prevent a misleading claim. The stress test reveals that hierarchy consistency alone does not justify nonzero reranking, and validation accordingly favors the reference. A documented falsifiable result with rigorous boundaries is stronger than claiming universal improvement from selected examples. Our contribution can be assessed honestly as a specialized computation and evaluation.

## Presenter 4 questions about slide 7

### P4 01 What is gamma

It is the strength of the facet utility relative to the known background recommendation score. Zero removes that utility; one half gives it the fixed diagnostic influence used on earlier slides. Gamma differs from alpha, the content collaborative mixture. Its scale belongs to this declared utility model and is not the original PDF's fifteen percent genre weight.

### P4 02 Why did every validation study choose zero

Within the declared grid and paired method family, zero gave the best validation criterion. The learned theme utility did not earn additional ranking weight in these tasks. That is evidence about this fit and interval design, not a theorem that genre is never useful. The choice was made before reading each corresponding test result and is preserved rather than overridden for a favorable narrative.

### P4 03 Does zero mean the project failed

It means the nonzero utility did not justify deployment under the chosen validation objective. The exact formulation and conditional acquisition result remain separate contributions, but they cannot be presented as validated ranking improvement. The negative selection helps identify the next bottleneck: learning useful preferences and measuring real acquisition value. We should acknowledge that the broader product goal remains only partially addressed.

### P4 04 Why use gamma one half in slides 3 to 6

It was frozen separately as a nonzero diagnostic so the hierarchy could actually affect the modeled ranking and certificate. At zero, both methods ignore the facet utility, making a hierarchy comparison trivial. We preserve both findings: nonzero mechanism behavior and validation selected fallback. The diagnostic does not replace validation or justify deploying a rejected setting.

### P4 05 Does retaining the reference prove noninferiority

The selected zero weight policy mechanically preserves the same list in this paired family, but that is not a noninferiority result for the nonzero hierarchy reranker. The earlier fixed nonzero comparisons include losses and uncertainty. A genuine noninferiority study for a changed policy needs a predefined justified loss margin, independent outcomes and an appropriate confidence analysis.

### P4 06 Why is EASE better but the reference still selected

The zero theme selection occurs inside the paired reference and regret family, not across all baseline architectures. EASE is a separately tuned comparator and can outperform the selected reference, especially for books and songs. We report that openly. A stronger complete system should consider a better validated retriever rather than claim the reference is globally optimal.

### P4 07 Why are EASE scores different on slides 3 and 7

Slide 3 restricts EASE to the sixteen reference retrieved candidates. Slide 7 lets it rank all available unseen items, so its chosen recommendations can change. Movies show 0.2320 in the pool and 0.2247 across the catalog; books and songs improve in the full catalog. These are different evaluation scopes, not contradictory copies of the same score.

### P4 08 Why are the reference scores unchanged

The reference's own top five are already contained in its top sixteen retrieval pool. Restricting it to that pool therefore preserves its recommendations. A different model such as EASE may want items outside that pool. This illustrates why same pool testing isolates a decision layer and cannot establish superiority over every full catalog system.

### P4 09 Did you secretly tune parameters on the test

The declared validation grids and selected values are saved, and completed runners refuse to overwrite their results. Test outcomes do not select gamma, alpha or EASE regularization. Some later timing and supplemental interval analyses are explicitly post result descriptions. A local protocol hash supports integrity, but it is not equivalent to external preregistration.

### P4 10 What parameters were tuned

The study selects the content collaborative mixture, EASE regularization and a common theme weight using validation. Gamma's grid is zero, one quarter, one half and one. EASE regularization comes from 100, 1,000 and 10,000. Ridge strength ten, twenty item profiles, interval width and masking settings are declared protocol choices rather than claims of universally optimized hyperparameters.

### P4 11 Why use a common gamma for flat and hierarchy

It keeps their utility strength comparable so a difference can be attributed to the uncertainty model rather than different weights. The validation selection averages their NDCG under each common setting. A separately fixed one half comparison probes the mechanism. Allowing independent favorable settings without a declared procedure could confound the contrast.

### P4 12 Could a different validation metric choose nonzero gamma

Possibly, because an exposure, risk or acquisition objective could prefer different behavior. That would be a new declared task needing justified utility, independent validation and test. We cannot retrospectively choose a metric to make the current result look positive. The latest relevance conclusion is tied to its frozen NDCG criterion and remains negative or unestablished.

### P4 13 Why not use richer LLM preferences instead of ridge coefficients

That is a reasonable future comparator, but it would add source quality, prompting, cost and calibration questions. The current fit is a reproducible history based baseline with explicit intervals. A language model's fluent preference description is not automatically correct. We would freeze the extraction and compare independently held out relevance under the same candidates and information budget.

### P4 14 Can a twenty work history reliably fit many facets

It can produce a regularized linear estimate, but adequacy is uncertain. Correlated facets and missing evidence make coefficients unstable or unidentifiable. Ridge restrains magnitude, while the fixed interval box does not establish calibrated taste coverage. The zero validation weights and relevance failures are evidence that this simple preference representation needs stronger validation.

### P4 15 What deployment choice follows from the current evidence

Do not deploy the nonzero hierarchy reranker as an established relevance improvement. The paired validation family retains the reference, and stronger baselines should be considered for retrieval. Hierarchy checking may be useful for a separately justified nonzero matching task with costly metadata, but actual value and cost remain unmeasured. This is a conditional research recommendation rather than a production success claim.

### P4 16 What is the most important caveat about zero gamma

Genre facts cannot influence that ranking utility, so acquiring them for it is unnecessary. The nonzero lookup saving therefore cannot itself justify deployment. We need either an independently validated useful nonzero utility or a separate information dependent decision task before claiming operational benefit. This distinction prevents mathematically correct savings from being attached to an irrelevant production step.

## Presenter 4 questions about slide 8

### P4 17 What is your actual contribution

We derived a specialized exact formulation for joint uncertainty in incomplete implication linked binary labels and shared signed interval preferences. Each pair reduces to a minimum cut. We also derived a conservative structural fault bound and preserved independent tests showing small annotation savings and ranking limitations. Worldwide originality remains unverified, and known graph, regret and hierarchy methods are attributed.

### P4 18 Is this novel or just an implementation of prior art

The ingredients are prior art, while the explicit tractable specialization and fault extension are candidate project derived results. We provide their assumptions, algebra, implementation and counterexamples so they can be scrutinized. Targeted searches did not establish an identical formulation, but absence in a search is not proof of global priority. We should describe a candidate contribution rather than a first ever invention.

### P4 19 How is this different from ordinary hierarchical tagging

Tagging describes works and their category relations. Our formulation computes worst case candidate advantage when both some tags and signed preference weights are uncertain, with one shared weight vector. It derives an exact cut construction and a fault tolerant upper bound under specified assumptions. The three domain experiment then measures consequences; it does not claim we invented hierarchical genres.

### P4 20 Which prior work do you acknowledge

We acknowledge maximum closure and graph representability, minimax regret and joint feature preference elicitation, the LTO ontology, AcousticBrainz hierarchical music labels and prior fine grained cross domain aspect transfer such as CATN. The handbook provides primary source links. Attribution separates borrowed mathematical machinery and datasets from our particular specialization and measurements.

### P4 21 Could this be accused of plagiarism

We explicitly attribute established ideas, datasets and formulations, and state the scope of the project derived result. Similar research topics do not make an independently explained and properly cited implementation plagiarism. Claiming an established method as our invention would be improper. We avoid unsupported first claims and preserve the derivation so examiners can assess the precise distinction.

### P4 22 What exactly is exact

The hard model's pairwise maximum gap is exact under independent signed intervals, additive utility, correct observations and implication only completion constraints. It is not exact human taste prediction. The structural fault budget extension is generally a conservative upper bound, and individual regret ordering is not a theorem of optimal five item set selection. Each use of exact should name its object and assumptions.

### P4 23 Why use minimum cut

After complementing chosen labels, the pairwise objective becomes linear node weights plus nonnegative binary products represented by auxiliary implications. That is a maximum weight closure problem, which reduces to a source sink cut. The construction avoids enumerating all label and weight worlds. The graph has three m plus two nodes and proportionally many arcs, but a full candidate matrix still needs many pair cuts.

### P4 24 Does the fault extension solve bad annotations

It handles a declared budget of invalid hierarchy implications conservatively. Observed facts remain hard, so wrong labels that obey the hierarchy can still cause false confidence. The utility and interval model can also be wrong. Real annotation noise and a calibrated choice of fault budget have not been evaluated in the slide tables. The extension has mathematical and small exhaustive checks, not a general semantic error guarantee.

### P4 25 Where is the LLM in the latest result

The latest held out decision layer uses source metadata, history derived coefficients and graph optimization, not new language model generated outcome gold. Hosted DeepSeek was used earlier for source feature extraction and explanation experiments. Separating it makes the uncertainty test reproducible and avoids confusing teacher claims with independent outcomes. The latest result does not establish stronger LLM reasoning or an SLM improvement.

### P4 26 What happened to the tiny student model

It was an actual 562,464 parameter causal transformer trained locally, but its extraction quality was poor. In the one participant source review it matched none of seven positive feature judgments and had F1 zero, while DeepSeek matched six. Filtering with teacher evidence left no positive student matches. We report a failed compact extraction trial rather than successful LLM replacement.

### P4 27 Did you show cross domain recommendation improvement

No linked user cross domain relevance improvement is established. The structural film book task uses cross domain candidate directions with scripted preferences, while the latest real outcome tests are independent within domain populations. The product can retrieve movies, books and songs, but that capability is weaker than demonstrating that one domain's history improves another domain's outcomes for the same person.

### P4 28 Did you improve fairness diversity or long tail exposure

The broader product and earlier pilot explore discovery, but the latest hierarchy experiments do not establish those objectives. Tail exposure and coverage are distinct from provider or demographic fairness. The book and song research subsets favor popular annotated works, restricting long tail claims. A future study needs explicit exposure policy, appropriate group or provider data and independent evaluation.

### P4 29 What do the 116 passing tests prove

They support implementation contracts and tested computational properties, including self comparison, temporal isolation, identity matching and solver checks. They do not prove semantic annotation truth, enjoyment, world novelty or population fairness. Unit tests and independent relevance evaluation serve different purposes. We report both without treating a green suite as a recommender quality score.

### P4 30 What is the strongest honest sentence you can defend

We derived and implemented an exact conditional hierarchy uncertainty calculation, added a conservative structural fault bound, and found small simulated annotation savings in three independent domains without established relevance improvement. That sentence states both the computation and empirical boundary. It should not be upgraded to a novel universal AI that solves cold start or beats strong recommendation systems.

### P4 31 What is the next experiment

First establish an adequate preference utility and reliable independent partial annotations, then compare coherent and flat acquisition on identical candidates with measured actual costs and held out relevance. A linked user source or prospective rating study is needed for cross domain claims. Preregister or externally record the protocol, include strong baselines, and define relevance preservation or improvement before looking at outcomes.

### P4 32 Why should the judges reward a result without accuracy gains

The work supplies an explicit tractable derivation, independently checked implementation, transparent datasets and a falsifying evaluation rather than selected anecdotes. That can be a valuable methodological contribution, while its practical significance remains modest. We should let the judges evaluate the rigor and scope honestly. Promising a grade or hiding the zero validation weight would make the defence weaker.

## Shared questions every presenter should know

### S 01 Explain the whole project in thirty seconds

Recros recommends movies, books and songs. Our latest research checks how missing hierarchical labels affect uncertainty. We derived an exact conditional graph calculation and tested it against independent ratings and plays. It saves small numbers of simulated metadata lookups for a minority of profiles, but does not establish better relevance. Validation rejects additional theme weight, and stronger taste and cost evidence are needed for deployment.

### S 02 What is a feature versus a preference

A feature describes an item, such as horror atmosphere. A preference describes how a person responds to that feature in a context. A present feature can have a positive, negative or zero contribution for different people. Learning richer labels does not automatically reveal those weights. This is why our metadata logic and independent relevance evaluation are separate.

### S 03 What is training versus inference

Training adjusts parameters using examples; inference applies the saved parameters to an input. The tiny transformer's training and source extraction are different from the graph solver, whose optimization computes a conditional gap rather than learning language weights. Downloading a dataset or invoking a hosted model does not mean we trained that hosted model ourselves.

### S 04 What is an LLM versus an SLM

Both are language models when they learn or model token sequences, with large and small referring to relative capacity and deployment scale. A compact decision tree ranker is a different machine learning model. The original report's terminology is loose; our separate tiny causal transformer is an actual language model. We avoid pretending that all efficient algorithms are SLMs.

### S 05 Why not use an LLM for every recommendation

That is a useful baseline, but it would need measurement of relevance, grounding, latency, cost and reproducibility under the same candidate information. A model can hallucinate work details or overfit to popular knowledge. The original architecture assigns language understanding and explanation to the LLM and efficient scoring to a compact component. The latest controlled study isolates uncertainty rather than claiming that this division always wins.

### S 06 How does TF IDF differ from a semantic embedding

TF IDF weights lexical terms according to occurrence and rarity in documents. A learned semantic embedding obtains its representation from a trained model and can reflect relationships beyond shared words. Both produce numeric vectors, but neither similarity nor semantic fluency guarantees preference. The current broad catalog uses a TF IDF index; it should not be described as fully LLM embedded.

### S 07 How can full stack developers explain the algorithm

Treat source items as database records, known interactions as event logs and facets as typed properties with unknown values. A reference service retrieves sixteen candidates. The graph service checks their possible utility differences under explicit rules. Its result is a bounded decision quantity, while independent tests judge whether the chosen works match later outcomes. This connects the mathematics to services without erasing its assumptions.

### S 08 Is the product ready for production

There is a working local demonstration and preserved research code, but production claims need end to end load tests, actual acquisition costs, stronger data quality and useful independent preference evaluation. The recorded solver timing excludes several service stages. The current result should be presented as a graduation research prototype with explicit verified components, not a fully validated industrial deployment.

### S 09 What should you say if asked an unmeasured number

Say that it has not been measured, identify the nearest measured quantity and explain the needed experiment. For example, we measured simulated bits, not API dollars. Do not invent an estimate and present it as observed. A short accurate boundary followed by a concrete plan is more defensible than a plausible sounding unsupported statistic.

### S 10 Is the dataset multilingual or geographically fair

Some source records contain language or country metadata, but coverage is uneven and fairness has not been established. Country of production is not story setting, and edition language is not necessarily original language. The separate tasks and popular subsets do not represent every culture or language. We need explicit subgroup definitions and quality audits before making those claims.

### S 11 Do more tags always capture intent better

They can distinguish more item properties, but noisy, missing or irrelevant tags can also hurt. A person's reason may depend on pacing, performance or context that genre does not capture. Our validation selects zero extra theme weight despite the richer structure. Tags improve representational possibility, not guaranteed predictive accuracy.

### S 12 How do you recommend both new and unfamiliar works

The product can use recency metadata and exposure or popularity signals for discovery slots, while excluding known consumed works when history is available. Recently released and unfamiliar are different conditions. A recent work can already be known, and an old work can be new to the person. The latest hierarchy test does not establish causal success of those discovery choices.

### S 13 What is the difference between novelty and novelty of research

Recommendation novelty concerns unfamiliar or less exposed items. Research novelty concerns what new method or finding the project contributes. A list of obscure books does not prove an algorithm is original, and a new derivation does not prove its outputs are novel. We state and evaluate those meanings separately.

### S 14 Can you say the algorithm has zero errors

Only specific computational checks recorded no mismatches under their tested contracts. That does not mean zero semantic errors or perfect recommendation accuracy. The structural experiment records no bound order failures and small oracles agree, while real relevance gains remain unestablished. Correctness and usefulness must always name their task and evidence.

### S 15 Where are the results if a judge wants to inspect them

The three domain report and comparison JSON are under docs/milestone2/hierarchy/domains. The derivation is under docs/milestone2/hierarchy, and the movie holdout has a separate preserved folder. Per profile predictions, validation settings and query traces are saved. The technical handbook maps exact repository paths so the team can open evidence without exposing private participant access tokens.

### S 16 What is the biggest limitation

We have not established a useful nonzero preference model that turns the conditional uncertainty advantage into improved or demonstrably preserved real recommendation value. Validation chooses zero theme weight, actual acquisition costs are unmeasured, and cross domain users are unlinked. The mathematical result is narrower than the full product ambition. Improving the taste model and evaluation is therefore the next priority.

## Advanced derivation questions led by Presenter 4

Presenter 2 should also learn questions T 01 to T 08. The remaining presenters need only the plain language first sentence unless the examiner directly asks them.

### T 01 What are the exact assumptions

Binary facets, implication only constraints, correct observed facts, feasible completion sets, additive utility, independent bounded signed preference intervals and one shared preference vector across the pair. Different items' completions have no extra cross item coupling. These assumptions enable the graph reduction. Nonlinear interactions, arbitrary disjunctions or coupled weights need a different formulation or relaxation.

### T 02 Why must preference weights be shared

Both items should be evaluated by the same possible person in the same world. If we choose separate weights for chosen and challenger, identical known profiles can appear to differ merely because their individual utility intervals are wide. With shared weights, identical facet contributions cancel. This is why the independent per item interval ablation is looser than the flat common weight model.

### T 03 How do you eliminate uncertain weights

For fixed binary challenger a and chosen b, their difference is minus one, zero or one. The maximizing weight is the upper endpoint for plus one and the lower endpoint for minus one; zero cancels. This yields upper times a times one minus b, minus lower times one minus a times b. Independent intervals let us apply that argument coordinate by coordinate.

### T 04 Why complement the chosen labels

Writing y as one minus b makes the pair contribution lower times a plus lower times y plus upper minus lower times a times y, minus lower. The product coefficient is nonnegative. An auxiliary reward node requiring both a and y can represent it in a closure graph. Complementing also reverses the chosen hierarchy arcs.

### T 05 Why reverse the chosen hierarchy edge

Child at most parent becomes one minus child at least one minus parent. In complemented variables that is complemented parent at most complemented child. Therefore a selected complemented parent implies complemented child. Retaining the old direction would enforce the wrong completion set and could produce incorrect bounds or witnesses.

### T 06 Why does the auxiliary node model a product

It receives nonnegative weight upper minus lower and implies both prerequisite nodes. It cannot be selected unless both are selected. If both are selected, maximizing selects it whenever the reward is positive; at zero the objective is unaffected. This reproduces the binary conjunction contribution without allowing an impossible rewarded configuration.

### T 07 What does the minimum cut return

It identifies a maximum weight closed set after source and sink capacities encode positive rewards, negative costs and hard implications. Converting the cut value back and restoring constants gives the exact pair gap. The source side supplies coherent labels and endpoint choices supply a shared weight witness. We independently check that substituting that witness attains the reported value.

### T 08 What is the complexity

Each pair graph has three m plus two nodes and a number of arcs proportional to m plus the implication edges. A standard flow computation solves it without enumerating all label worlds. A full N item comparison needs at most N times N minus one pair cuts. This is not a claim that full catalog ranking is free or that one graph solves every candidate pair simultaneously.

### T 09 Is the normalized phantom gap unbounded

No, the parent subtype construction has raw phantom regret k and coherent regret zero, but its absolute weight sum is two k. Dividing gives one half. Saying that raw regret grows linearly is valid; saying normalized uncertainty becomes arbitrarily large from that construction is not. The structural report separates raw algebra from normalized measurements.

### T 10 Can the model compare an item with itself

Its gap is defined as zero. One physical item's unknown labels cannot simultaneously take two different values as chosen and challenger in one world. A generic independent completion routine would otherwise fabricate a self gap. The code explicitly handles this and meaningful tests cover it.

### T 11 What happens with cycles or inconsistent observations

Implication cycles can express equivalence and must be propagated or solved consistently. If known facts contradict required implications, the hard completion set is empty and an ordinary finite certificate is invalid. The code checks feasibility and tests these cases rather than silently inventing a completion. A fault permitted model may restore feasibility only within its explicitly declared budget.

### T 12 Is the structural fault bound exact

Generally it is conservative, because it minimizes upper bounds from a finite penalty grid rather than solving every budget constrained world exactly. The hard K zero solver is exact under its assumptions. A penalized maximizing witness can exceed the fault budget, so its value is not automatically an attained budget feasible optimum. The implementation records attainment separately.

### T 13 Prove the fault bound in words

In every allowed world the violation count is at most K. Subtracting lambda times violations and then adding lambda K can only increase that world's ordinary gap. Maximizing the penalized gap gives an upper bound for all such worlds. Taking the smallest bound over nonnegative penalties remains valid. This is an attributed Lagrangian argument, not a calibrated semantic uncertainty claim.

### T 14 Can you add arbitrary mutual exclusions

Not while retaining the same general tractability claim. With positive unknown feature weights and arbitrary pairwise exclusions, the gap can encode maximum weight independent set. That includes a hard optimization family. Some special exclusion structures might be tractable, but arbitrary Boolean label systems need different methods. User interface filtering does not automatically extend the theorem.

### T 15 What proves the implementation matches the derivation

We use exhaustive feasible enumeration on 240 small hard model cases and ninety fault cases, plus twelve separately frozen larger MILP comparisons. Returned witnesses are checked and both native and Python backends agree on tested cases. The current suite has 116 passing API and ML tests. These are strong computational checks, while they do not prove semantic truth or worldwide originality.

### T 16 Is native flow always faster than MILP

No universal speed advantage is established. In twelve seeded local cases, native flow has lower median time at the reported sizes, while the initial Python flow backend was slower than MILP at large sizes. Languages, graph structure, presolve and hardware affect timing. We preserve both measurements and state that recorded latency excludes retrieval, fitting and annotation calls.

## Evidence and last rehearsal check

For original reported achievements, use the first milestone PDF physical pages 9 to 15. For current numerical answers, use docs/milestone2/hierarchy/domains/RESULT.md and comparison.json. For theoretical answers, use docs/milestone2/hierarchy/DERIVATION.md and the structural RESULT.md. For the student and human pilot, use the transfer folder's STUDENT_EXPERIMENT.md and HUMAN_READING_PILOT.md. The technical handbook provides primary source citations and full repository locations.

Before the presentation, each person should answer five randomly chosen assigned questions without reading. All four should correctly answer S 01, S 02, S 04 and S 16. Presenter 2 should calculate one NDCG example and one cost percentage. Presenter 3 should state both relevant denominators. Presenter 4 should explain why gamma zero makes genre acquisition unnecessary. Presenter 1 should keep the recap at two minutes and describe earlier values as reported PDF results.
