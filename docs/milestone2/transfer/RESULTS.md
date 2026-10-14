# Source-reading and retrieval result

Eighteen project-selected passages, six per domain. Four criteria, 72 binary source-label decisions. The Codex assistant authored the reference labels before extraction; these are not human gold labels. This measures agreement about these short passages, not preference accuracy.

Protocol SHA-256: `e378725a809740fd00da7e15e08ac04944d042186ab6b0bb77d349160a0ea2b8`. Model: `deepseek/deepseek-v4-flash`.

Extraction precision 1.000, recall 0.840, F1 0.913. TP 21, FP 0, FN 4. Exact-quote/schema rejections: 0.

| Retrieval method | Mean NDCG@3 on requests with positive source labels |
|---|---:|
| Fixed BM25 queries | 0.9018 |
| DeepSeek feature matches | 0.9787 |

11/12 request types have positive labels. The remaining types are reported separately rather than given an artificial ranking score.

| Controlled intervention | Accepted claims afterward | Recommendations / 12 requests |
|---|---:|---:|
| changed_source | 0 | 0/12 |
| fabricated_quote | 0 | 0/12 |
| unknown_feature | 0 | 0/12 |
| deleted_evidence | 0 | 0/12 |

These interventions deliberately corrupt every record. They verify the rejection/abstention mechanism, not the prevalence of real source failures. Exact quotes can still have incorrect feature interpretations.

No population confidence interval, independent label adjudication, satisfaction gain, or SLM result is established. The candidate selection, rubric and source paraphrasing were developed for this prototype. The strongest baseline may tie; disclose the measured comparison.

See `source_labels.json`, `protocol.json`, `model_output.json` and `results.json` for labels, prompts, raw final output and per-request outcomes.
