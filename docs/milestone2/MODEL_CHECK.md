# Command Code model access check

DeepSeek is accessible through the existing subscription. No model weights were
downloaded. The default annotation model is now `deepseek/deepseek-v4-flash`, and
the lab serves its saved output without making inference calls during a presentation.

Both calls below used exactly the same 12 descriptions and annotation prompt.
Prompt SHA-256: `f50fd00ccf991fd8f2fa7ac958307d35d07bddc08f827c1a9bb5d5f64f4c1b84`.

| Single call | Ling 3.1 Flash (free) | DeepSeek V4 Flash |
|---|---:|---:|
| CLI-reported duration | 88.65 seconds | 10.43 seconds |
| Input tokens | 18,042 | 17,444 |
| Output tokens | 2,703 | 1,456 |
| Exact-quote/schema accepted facets | 15/15 | 12/12 |
| Dollar charge | Not reported | Not reported |

These are two individual calls, not a controlled latency or pricing benchmark.
Input usage includes Command Code's agent overhead. A cheaper model does not by
itself guarantee fewer input tokens; batching and caching avoid repeated calls.

DeepSeek retained the four shared themes across movies, books and songs and omitted
the three additional “mystery” tags produced by Ling. In particular, Ling's mystery
tag for *Space Oddity* is debatable. This is a qualitative inspection, not an
independently labeled accuracy score. Exact quote validation verifies provenance,
not semantic entailment.

Caches retain final structured outputs and usage metadata, not private reasoning:

- [DeepSeek output](../../demo/catalog.real.deepseek.annotated.json)
- [Ling output](../../demo/catalog.real.annotated.json)

To explicitly regenerate with DeepSeek:

```bash
PYTHONPATH=ml/src:apps/api .venv-research/bin/python -m recros_ml.research.annotate \
  --source demo/catalog.real.json \
  --out demo/catalog.real.deepseek.annotated.json \
  --model deepseek/deepseek-v4-flash
```

This uses the normal `cmd` authentication flow. It does not purchase credits,
switch accounts, or silently fall back to another model.
