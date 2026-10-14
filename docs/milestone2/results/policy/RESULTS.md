# Matched-observation policy comparison

**Controlled mechanism experiment: 24 scripted tasks, 12 reused real works, zero participants.**

Six movie/book/song directions × four information conditions. Utilities and costs are hypothetical; the full structured hypothesis table is supplied to every policy. This is not an end-to-end recommendation quality benchmark.

| Policy | Completed | Recommendations | Scripted theme match among recommendations | Mean modeled loss ↓ | Questions | Evidence accesses |
|---|---:|---:|---:|---:|---:|---:|
| exact | 24/24 | 24/24 | 1.000 | 0.030 | 0.500 | 0.500 |
| one_step | 24/24 | 18/24 | 1.000 | 0.128 | 0.250 | 0.250 |
| information_gain | 24/24 | 24/24 | 1.000 | 0.030 | 0.500 | 0.500 |
| always_ask | 24/24 | 24/24 | 1.000 | 0.050 | 1.000 | 0.500 |
| always_inspect | 24/24 | 24/24 | 1.000 | 0.040 | 0.500 | 1.000 |
| no_actions | 24/24 | 6/24 | 1.000 | 0.337 | 0.000 | 0.000 |
| deepseek | 24/24 | 24/24 | 1.000 | 0.030 | 0.500 | 0.500 |

## Condition breakdown

| Policy | Information condition | Completed | Recommendations | Mean modeled loss |
|---|---|---:|---:|---:|
| exact | both_unknown | 6/6 | 6 | 0.060 |
| exact | preference_unknown | 6/6 | 6 | 0.040 |
| exact | item_fact_unknown | 6/6 | 6 | 0.020 |
| exact | both_known | 6/6 | 6 | 0.000 |
| one_step | both_unknown | 6/6 | 0 | 0.450 |
| one_step | preference_unknown | 6/6 | 6 | 0.040 |
| one_step | item_fact_unknown | 6/6 | 6 | 0.020 |
| one_step | both_known | 6/6 | 6 | 0.000 |
| information_gain | both_unknown | 6/6 | 6 | 0.060 |
| information_gain | preference_unknown | 6/6 | 6 | 0.040 |
| information_gain | item_fact_unknown | 6/6 | 6 | 0.020 |
| information_gain | both_known | 6/6 | 6 | 0.000 |
| always_ask | both_unknown | 6/6 | 6 | 0.060 |
| always_ask | preference_unknown | 6/6 | 6 | 0.040 |
| always_ask | item_fact_unknown | 6/6 | 6 | 0.060 |
| always_ask | both_known | 6/6 | 6 | 0.040 |
| always_inspect | both_unknown | 6/6 | 6 | 0.060 |
| always_inspect | preference_unknown | 6/6 | 6 | 0.060 |
| always_inspect | item_fact_unknown | 6/6 | 6 | 0.020 |
| always_inspect | both_known | 6/6 | 6 | 0.020 |
| no_actions | both_unknown | 6/6 | 0 | 0.450 |
| no_actions | preference_unknown | 6/6 | 0 | 0.450 |
| no_actions | item_fact_unknown | 6/6 | 0 | 0.450 |
| no_actions | both_known | 6/6 | 6 | 0.000 |
| deepseek | both_unknown | 6/6 | 6 | 0.060 |
| deepseek | preference_unknown | 6/6 | 6 | 0.040 |
| deepseek | item_fact_unknown | 6/6 | 6 | 0.020 |
| deepseek | both_known | 6/6 | 6 | 0.000 |

## How to read this

- Mean modeled loss is action costs plus worst-case terminal regret within the supplied worlds; abstention costs 0.45.
- Match rate uses scripted theme choices, not human satisfaction. Always read it alongside coverage.
- Information gain is a strong cheap baseline. A tie means this suite does not establish an advantage for exact planning.
- Candidate identity masking and cached evidence access are controlled interventions, not a claim about realistic retrieval difficulty.
- Cases reuse items and share a hand-built structure. No significance test, population interval or novelty claim is justified.
- No SLM was trained or evaluated. DeepSeek is a hosted model accessed through the existing subscription.
- Failure counts are retained. Completed-episode means exclude failures; do not use those means alone to compare an incomplete policy.

Frozen local protocol SHA-256: `2e4dd83d638f73515a2c7cd760c92760fef6fc3ba8727a7a6737bcdb3478c6df`. See [protocol](protocol.json), [full traces](results.json), and `model_calls/` for final outputs and usage. Prompts were fixed before inference, not externally preregistered. Model calls batch up to eight cases; batch latency is not individual inference latency.
