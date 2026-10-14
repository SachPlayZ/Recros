# One-person supplied-text reading pilot

Completed October 14, 2026, at 08:53:49 UTC. Model outputs and source selection were
frozen before this submission. No subsequent model training used these judgments.

One participant reviewed six paragraphs, two each about films, books and songs.
The form hid titles and model predictions. It asked which of four explicitly
defined source features the displayed text supports, and offered “Unsure.” Five
paragraphs were judged; one was marked unsure and excluded. The judged set contains
twenty binary decisions and seven positive judgments. This is **one participant**,
not twenty independent observations.

| Frozen interpretation | Matching positives (TP) | Extra positives (FP) | Missed positives (FN) | F1 |
|---|---:|---:|---:|---:|
| DeepSeek teacher | 6 | 0 | 1 | 0.923 |
| Tiny causal LM v2 | 0 | 2 | 7 | 0.000 |
| Tiny LM with cached teacher gate | 0 | 0 | 7 | 0.000 |

DeepSeek precision is 6/6 and recall 6/7 in this small review. The gate retained
**no positive predictions**, so its precision is undefined, not 1. It removed two
extra labels while providing no useful positive matches. Abstention cannot count
as successful interpretation or recommendation quality.

The user marked the House of Leaves paragraph unsure. On A Ghost Story, the user
also judged inquiry supported, which the teacher missed. These judgments concern
the supplied paragraph and rubric; they do not adjudicate complete works.

The sample was selected by fixed SHA-256 ordering with seed
`recros-independent-reading-20261014`; the selected IDs and frozen prediction/source
hashes are in `review_protocol.json`. Aggregate metrics are in
`human_reading_results.json`. Private individual answers and access credentials
remain in the ignored local directory.

The reviewer supplied the development preferences earlier in the session. The
source paragraphs were also already used in the assistant-reference comparison.
Thus these are new human judgments on a development stimulus set, not a new
population sample or an untouched external test set. No satisfaction, real
cross-domain preference improvement, calibrated uncertainty or statistical
superiority claim follows from this pilot.
