# MovieLens pilot: measured results

This is a **single-domain, non-language-model** experiment, not a reproduction of milestone 1.

Validation chose content weight **0.3** and predicted utility budget **10%**.

| Method | NDCG@10 (95% user bootstrap CI) | Recall@10 | Coverage@10 | Tail share | Gini ↓ | p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| popularity | 0.1556 [0.1102, 0.2052] | 0.1050 | 4.58% | 0.00% | 0.9794 | 0.51 |
| content | 0.0309 [0.0130, 0.0557] | 0.0133 | 10.40% | 81.08% | 0.9609 | 0.53 |
| itemknn | 0.1433 [0.0941, 0.1950] | 0.0615 | 6.56% | 0.00% | 0.9718 | 0.41 |
| hybrid | 0.1547 [0.1043, 0.2071] | 0.0768 | 6.68% | 0.22% | 0.9709 | 0.52 |
| discovery | 0.1498 [0.0990, 0.2041] | 0.0662 | 6.62% | 7.85% | 0.9710 | 2.50 |

Test users evaluated: 93. Paired NDCG change (discovery − hybrid): {'mean': -0.004889343175506139, 'ci95': [-0.011141235311494002, 0.0011444844845043675], 'n': 93}.

## Protocol

Global 60/20/20 time windows; refit on train+validation for test; frozen profiles; full available catalog minus history; rating>=4 relevant; unobserved treated as nonrelevant for offline metrics

## Limits

- Single-domain pilot; no evidence of cross-domain transfer or SLM benefit
- One global split; confidence intervals resample users, not datasets or time windows
- Observed ratings are not randomized exposure; Gini/tail exposure are not provider fairness
- Predicted utility bound does not bound actual NDCG loss
- Latency is local scoring/reranking, excludes fit, HTTP, retrieval I/O and language inference
