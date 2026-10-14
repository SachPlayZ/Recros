# Recros literature and novelty review

Reviewed October 13, 2026, before the October 15 presentation.

October 14 extension: [a more ambitious research bet](RESEARCH_BET.md) broadens the one-question experiment to choosing between preference questions, item-evidence inspection, recommendation and abstention. It includes additional prior art and a constructed exact-planning probe. It does not establish new architectural novelty or real-user improvement.

## Decision

**Do not claim a new architecture or a research breakthrough.** The current evidence bridge has close prior art, and the proposed clarification, intent-transfer, distillation and model-routing components also have implemented predecessors. Retain the working system as an engineering contribution and experimental platform. Any next research contribution must come from a clearly specified comparison, independently measured results, and an explicit difference from prior work.

My earlier recommendation of selective semantic transfer was a candidate direction, not a verified originality claim. Calling it “unconventional” was not justified by the literature check. Combining familiar modules or changing the model provider does not, on its own, establish novelty.

This is a targeted scoping review, not an exhaustive systematic review or a certificate of originality. Primary papers and publisher pages were consulted. Search-result dates were not treated as publication dates. Full methods/evaluation sections were inspected for the closest comparisons below; other entries are marked as abstract or publisher-excerpt reviews. None of the papers' reported results has been independently reproduced in Recros.

## Closest prior work

| Work and source | What already exists; implication for Recros | Review depth |
|---|---|---|
| [EviSnap: Faithful Evidence-Cited Explanations for Cold-Start Cross-Domain Recommendation](https://arxiv.org/html/2604.06172) — Dai and El-Roby, 2026 preprint | Offline LLM facets, supporting quotations, shared concepts, editable explanations, and six Books/Movies/Music transfers. Uses a learned linear mapping and rating-error evaluation; our demo uses seed-item overlap. Its limitations explicitly include insufficient review text. This is the closest architectural overlap. Music products are not necessarily individual songs. | Methods §§3–4 and limitations §7 inspected. |
| [Cross-Domain Recommendation Meets Large Language Models](https://arxiv.org/html/2411.19862) — 2024 preprint | Evaluates LLM transfer including Books→Movies and Movies→Music. Music comes from Amazon CDs/Vinyl. The broad three-domain premise is established. | Dataset, task and evaluation sections inspected. |
| [Uncovering Cross-Domain Recommendation Ability of Large Language Models / LLM4CDR](https://arxiv.org/html/2503.07761) — 2025 preprint | Uses source histories and shared-domain features. Tests domain gap, model size and context length. Its ranking experiments use bounded candidate sets with sampled negatives, not full-catalog rankings. | Methods and experimental setup inspected. |
| [IDC-CDR: Cross-domain Recommendation based on Intent Disentanglement and Contrast Learning](https://doi.org/10.1016/j.ipm.2024.103871) — Information Processing & Management, 2024 | Separates latent user intentions and transfers them through graph/contrastive learning. Distinguishing which interest transfers is an existing research problem; this mechanism is not a conversational question policy. | Publisher abstract and method excerpts. |
| [Asking Clarifying Questions for Preference Elicitation With Large Language Models](https://arxiv.org/html/2510.12015) — 2025 preprint | Uses large-model-generated data and a fine-tuned Gemma 7B questioner. MovieLens-derived profiles, simulated users and profile-reconstruction metrics support its evaluation. Both clarification and teacher-to-smaller-questioner training already exist. | Methods and evaluation inspected. |
| [PEBOL: Bayesian Optimization with LLM-Based Acquisition Functions for Natural Language Preference Elicitation](https://arxiv.org/html/2405.00981) — RecSys 2024 | Combines Bayesian preference beliefs with LLM-generated questions. Evaluates simulated interactions and ranked-item recovery. Decision-aware question selection is established. | Methods and simulation protocol inspected. |
| [STYLE: Improving Domain Transferability of Asking Clarification Questions in Large Language Model Powered Conversational Agents](https://aclanthology.org/2024.findings-acl.632/) — Findings of ACL, 2024 | Studies transferring when-to-ask behavior across conversational-search domains. Domain-adaptive clarification is established, although search-domain transfer differs from transferring an individual's entertainment tastes. | Official abstract and publication record. |
| [From reviews to preference profiles: LLM-based transfer for cross-domain recommendation / LIPA](https://doi.org/10.1016/j.eij.2026.100981) — Egyptian Informatics Journal, 2026 | Abstract describes review abstraction into user/item profiles, embedding retrieval, Movies→Books transfer and full-catalog evaluation. Cached semantic profiles are not a new architectural idea. | Publisher abstract only; split and leakage details not independently audited. |
| [SLMRec: Distilling Large Language Models into Small for Sequential Recommendation](https://arxiv.org/abs/2405.17890) — 2024 preprint, revised 2025 | Distills recommendation capabilities into a smaller language model. A cheap model or a student model alone is not a new contribution. | Abstract and selected implementation details. |
| [RDRec: Rationale Distillation for LLM-based Recommendation](https://arxiv.org/abs/2405.10587) — ACL 2024 | Transfers teacher-generated recommendation rationales to a compact model. Cite this if implementing rationale distillation. | Abstract and publication metadata. |
| [RouteLLM: Learning to Route LLMs from Preference Data](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5503a7c69d48a2f86fc00b3dc09de686-Abstract-Conference.html) — ICLR 2025 | Learns when to use stronger versus weaker models under a cost-quality tradeoff. Selective escalation is established outside recommendation too. | Official proceedings abstract. |
| [A Dual-Expert Strategy Integrating LLMs to Mitigate Negative Transfer in Cross-Domain Sequential Recommendation / DuELRec](https://arxiv.org/abs/2608.23131) — 2026 author preprint, reporting acceptance at CIKM 2026 | Uses domain-specific and cross-domain experts to control harmful transfer. Avoid claiming that identifying or reducing negative transfer is new. | Abstract and method overview. |
| [CLAIM: Leading Open-domain Active Clarification of Large Language Models with Uncertainty Measurement](https://arxiv.org/abs/2608.11631) — 2026 preprint | Trains uncertainty-aware clarification behavior. An uncertainty trigger alone is insufficient as a novelty claim. | Abstract and method overview. |

The separate discovery reranker also sits within an established research area. [Fast Greedy MAP Inference for Determinantal Point Process to Improve Recommendation Diversity (NeurIPS 2018)](https://papers.nips.cc/paper/2018/file/dbbf603ff0e99629dda5d75b6f75f966-Paper.pdf) studies relevance/diversity reranking. [PCN-Rec (2026 preprint)](https://arxiv.org/abs/2601.09771) describes recommendation constraints with deterministic certificate checking and repair. Neither citation establishes that our exact feasibility rule is identical, but our implementation and tests do not establish a new optimization algorithm either. Keep the certificate claim limited to discounted predicted scores.

## What this means for “already solved”

Several close ideas have progressed beyond proposals into implementations and reported experiments. Rebuilding their basic architecture and calling it new would be a weak research contribution.

That does not show that every practical cross-domain recommendation problem is solved. Evaluation conditions differ: rating prediction, sampled-candidate ranking, simulated conversations, and real participant judgments answer different questions. For example, the clarification study above measures reconstruction of simulated users' profiles, whereas our intended application needs to recommend items people actually want. This distinction motivates a possible experiment; it does not prove that nobody has run it.

Do not claim that human evaluation is absent from the field: [Affect-aware Cross-Domain Recommendation for Art Therapy via Music Preference Elicitation (2025)](https://arxiv.org/abs/2507.21120), for example, reports a user study in music-to-art transfer. Its application differs from Recros, but it rules out sweeping “first real-user cross-domain study” claims.

## Recommended bounded extension — proposed, not implemented

**Research question: When descriptions are incomplete, does one selectively chosen preference question improve cross-domain recommendations enough to justify the user's effort?**

Treat this as an empirical extension of the cited work. The suspected practical failure is observable in our recovered data: movie/book descriptions and Spotify audio features provide unequal kinds of evidence. A person's answer can clarify their taste; it cannot create missing factual evidence about a target item.

Example: a liked film may suggest science, suspense or family relationships. Ask which matters only when those interpretations lead to meaningfully different candidates. Include “none of these / another reason” so the system does not force a false interpretation. If a song has no reliable thematic description, do not infer its narrative from danceability or energy; use supported attributes or abstain.

This candidate question was not directly answered by the closest papers inspected. That is a reason to investigate, not an established novelty claim. Before a publication-level claim, perform citation chaining and a broader search of sparse-text, interactive and selective recommendation literature.

### Minimum experiment

1. **Freeze the protocol first.** Record catalog, candidate generation, prompts, model IDs, question policy, thresholds, exclusions and primary outcome before seeing held-out judgments. Keep the existing movie-only result separate.
2. **Use a fixed manageable candidate pool for the policy comparison.** Every method sees the same items and allowable metadata. Obtain ratings for the complete pool if reporting within-pool NDCG; otherwise report a blinded comparison with its incomplete-label limitations. Do not call either full-catalog evaluation.
3. **Compare strong controls.** Include content similarity; direct DeepSeek ranking; the existing evidence bridge without a question; the same bridge always asking one question; and the bridge selectively asking. A random-question control can test whether selection adds value. Use the same extraction/ranking backend in the three bridge variants to isolate the question policy.
4. **Separate two kinds of uncertainty.** Test ambiguity about the user's reason independently from missing item metadata. Add a predefined metadata-removal stress test to well-described items, holding the candidate pool constant. Report actual missing-data cases separately from artificial removal.
5. **Collect independent preference judgments.** Participants answer preference questions and judge candidates with method names hidden. Randomize order and use disjoint/counterbalanced tasks to reduce carryover. Do not ask DeepSeek to generate both answers and the final ground truth. Simulations may debug the pipeline, but cannot establish real preference improvement.
6. **Report the cost of asking.** Primary outcome: participant-level difference in recommendation usefulness under a fixed question budget. Also report within-pool ranking quality where labels support it, question rate, response time, abstention rate, supported-explanation rate, tokens and measured latency. Do not invent monetary savings from the subscription price.
7. **Cover and disclose directionality.** Movies→Books, Movies→Songs, Books→Movies, Books→Songs, Songs→Movies, Songs→Books. Show each direction's actual participant/task count. A pair without judgments remains unevaluated. Cluster uncertainty estimates by participant rather than treating every item rating as independent.
8. **Use a stop/go rule.** A selective policy is useful only if it improves usefulness at comparable effort, or preserves a prespecified acceptable usefulness level with fewer questions. Define that tolerance before test results. A confidence interval containing zero is not proof of equivalence. If the always-ask or direct-LLM baseline is better, report it and simplify the system.

With two days remaining, prioritize a small honest pilot and presentation over simultaneous model routing, student training and multiple new architectures. A small participant sample is exploratory. Without participants, present the implemented mechanism and a prepared protocol; do not substitute generated labels and claim success.

An actual SLM comparison remains conditional on verifying a suitably small available model and running it. Hosted access and low price do not establish model size. No model download or extra paid service is required for this review.

## Reuse and attribution

Working on the same problem is not automatically plagiarism. The central attribution issue is presenting someone else's ideas, wording, code or results as one's own; [Oxford's academic guidance](https://www.ox.ac.uk/students/academic/guidance/skills/plagiarism) illustrates this distinction. Your institution's assessment and AI-assistance rules govern your submission and may differ. A well-attributed project can still have insufficient originality for a particular rubric.

- Cite the relevant paper where a method is described, not only in a final reference list.
- Distinguish existing teammate work, later implementation and evaluation changes, and planned experiments. Preserve the history.
- For reused code or data, record the source, version, license and modifications. Citation alone does not grant reuse rights.
- Keep paper results separate from locally reproduced results. Label illustrative examples and model-generated labels.
- Disclose AI assistance as required by the institution; do not present unperformed experiments or unsupported authorship claims.

Suggested provenance ledger:

| Component | Origin to record | Current evidence |
|---|---|---|
| Original application and LightGBM pipeline | Teammate repository and historical commits | Existing implementation; original trained artifacts unavailable |
| Evidence bridge | Recros implementation; related methods cited above | Functional demonstration, not verified novel architecture |
| Discovery reranker | Recros implementation; diversification literature | Predicted-score constraint checks and separate movie pilot |
| Clarification policy | Extension drawing on preference-elicitation literature | Proposed only |
| Data and descriptions | Dataset/summary sources and applicable terms | Local recovery audit and catalog provenance |
| Student language model | Actual model/training provenance when available | Not yet implemented or evaluated |

The [CDR Meets LLMs authors' repository](https://github.com/ajaykv1/CDR_Meets_LLMs) is a useful starting point for benchmark reuse. Its code/data contents, licenses and split validity must be checked before incorporation. Do not join unrelated MovieLens, Spotify and book records into fabricated shared users.

## Presentation wording

Use: “We implement an inspectable cross-domain recommendation prototype, drawing on established concept-transfer and preference-elicitation research. We audit the original evaluation and report a separate discovery tradeoff. Our next proposed experiment tests whether selective clarification helps under incomplete descriptions.”

Avoid: “first evidence-grounded cross-domain recommender,” “first intent-aware recommender,” “first LLM-to-SLM recommendation system,” “solved cold start,” “guaranteed fairness,” or “research breakthrough.”

The actionable next step is a controlled extension with clear attribution, not another broad architecture. A publication-level originality claim remains unestablished.
