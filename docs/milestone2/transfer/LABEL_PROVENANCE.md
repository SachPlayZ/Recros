# Label provenance and experimental boundaries

Updated October 14, 2026. This clarification accompanies the frozen files; it does
not replace their labels, prompts or hashes.

The Codex assistant authored the reference feature sets in `source_labels.json`
before the DeepSeek extraction call. These eighteen project-selected passages are
original paraphrases of attributed public sources. The phrase “single analyst” in
the original protocol means this AI assistant, not a human reviewer. Consequently,
the reported F1 and NDCG measure agreement with an assistant-authored development
reference. They are not independent human ground truth, preference accuracy or a
representative estimate for the recovered catalogue.

The original source-reading protocol has canonical SHA-256
`e378725a809740fd00da7e15e08ac04944d042186ab6b0bb77d349160a0ea2b8`.
Its reference labels, predictions and source paragraphs remain frozen. Exact quotes
and source hashes validate provenance; they do not validate semantic entailment.

The tiny-model evaluation reuses those eighteen passages. Their titles were excluded
from language-model training, including the vocabulary corpus. Nevertheless, the
passages had already been examined during development, and v1 results influenced
v2 design. The comparison is exploratory, not a pristine held-out study. Training
labels for the scaled bank come from DeepSeek; missing features are not known
negative facts about complete works. Training has no music records.

The later [human reading pilot](HUMAN_READING_PILOT.md) is separate. One participant
judged supplied text with model predictions and titles hidden. Selection and all
model predictions were frozen before submission. These judgments were not used
for subsequent training or threshold tuning. The outcome concerns paragraph
interpretation, not enjoyment of the complete works. Repeated paragraph decisions
do not create additional participants.

The scaled 210-work evidence bank has no independent source-label or preference
accuracy evaluation. It was selected by fixed text queries, rather than random
sampling. The full 222,896-item catalogue, 50,066-summary index, 210-work bank,
eighteen development passages, six reading paragraphs, twenty-four scripted tasks
and 93-user movie pilot are different artifacts with different denominators.
