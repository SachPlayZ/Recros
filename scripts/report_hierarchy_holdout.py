"""Write the research report from preserved first-run outputs; never retune."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/milestone2/hierarchy/heldout'


def main():
    p = json.loads((OUT/'protocol.json').read_text())
    r = json.loads((OUT/'results.json').read_text())
    a = json.loads((OUT/'audit.json').read_text())
    c = json.loads((OUT/'compute-cost.json').read_text())
    primary = r['fixed_nonzero_by_mask']['0.5']
    stress = r['fixed_nonzero_by_mask']['0.75']
    lookup = primary['lookup']
    improvement = a['by_mask']['0.5']['relative_mean_query_reduction']
    lines = [
        '# Real-rating validation: hierarchy saves annotation effort, without an established ranking gain', '',
        'October 14, 2026. This is a new held-out experiment. The earlier structural results and protocols remain unchanged.', '',
        '## Finding', '',
        f"Across **{primary['users']} held-out historical profiles**, the coherent certificate used **{lookup['hierarchy_queries']['mean']:.2f}** missing-label lookups on average versus **{lookup['flat_queries']['mean']:.2f}** for the flat certificate with the same sound unary propagation. This is **{improvement:.1%} fewer lookups** in the primary 50% masking condition.", '',
        f"The paired mean saving is **{lookup['paired_saved_queries']['mean']:.3f} lookups**, with a 95% user-bootstrap interval **[{lookup['paired_saved_queries']['ci95'][0]:.3f}, {lookup['paired_saved_queries']['ci95'][1]:.3f}]**. Both policies keep exactly the same five recommendations. This is an annotation-effort result, not evidence that the hierarchy improves human enjoyment.", '',
        '**The nonzero-weight hierarchy reranker did not establish higher NDCG than the flat reranker. Validation selected zero theme weight, and the 75% masking stress test found lower NDCG than the historical baseline.** The defensible deployment interpretation is to retain the validated historical ranking and use the hierarchy as a conditional confidence checker when metadata is costly to acquire.', '',
        '## Data and prospective local protocol', '',
        f"- Local source: **{p['source_rows']:,} MovieLens ratings**. Conservative title/year + IMDb matching yielded **{p['matched_movies']:,} LTO-labelled films** and **{p['matched_ratings']:,} matched ratings**. Ambiguous identities were excluded and logged.",
        '- Chronological global cutoffs within matched ratings: train through February 19, 2006; validation through October 2, 2009; later ratings form test outcomes.',
        f"- Split sizes: {p['split_counts']['train']:,} train, {p['split_counts']['validation']:,} validation and {p['split_counts']['test']:,} test ratings.",
        '- 128 validation profiles and 320 distinct test profiles, sampled in disjoint user-ID partitions. Future activity counts establish evaluability; future rating values do not choose profiles or parameters.',
        '- Profiles use only the last 20 prior ratings. Evaluation users are excluded from the background similarity/popularity fit. All previously seen items are excluded from candidates. This simulates limited history, rather than proving zero-history cold start.',
        f"- Test background: {a['background_ratings']:,} prior ratings from other users, {a['available_movies']} available films; {a['candidate_range'][0]}–{a['candidate_range'][1]} unseen candidates per profile.",
        '- Retrieve the same 16 candidates for every decision method without inserting future positives. Rank five. Future rating >=4 is relevant, with unobserved candidates treated as nonrelevant for this offline evaluation. All 320 profiles enter primary means; 314 have an eligible positive target.',
        '- User theme coefficients come from regularized regression on prior ratings, not scripted likes. Each request uses the 16 largest absolute coefficients and their ancestors (22–44 active facets). Independent intervals of ±25% are fixed sensitivity assumptions, not calibrated confidence intervals.',
        '- Target metadata is artificially masked at 50% and 75%. Listed LTO themes and ancestors are 1; unlisted themes are 0 only within this controlled closed-world reference. Unlisted does not establish that a theme is absent in reality.',
        '- Parameters are selected on validation only. The nonzero gamma=.5 comparison was frozen separately from the validation-selected deployment weight to prevent a zero-weight comparison from masquerading as a hierarchy test.',
        f"- Parent protocol SHA-256: `{r['protocol_sha256']}`. This was a local prospective freeze, not an external preregistration. EASE was added in a separately frozen extension before validation scoring; a full-catalog audit was declared during the test run before reading its results.", '',
        '## Real held-out ranking: same 16 candidates, 50% missing labels', '',
        'NDCG discounts relevant recommendations lower in the list. Recall measures how many eligible held-out positives the five recommendations recover. These outcomes are independent historical ratings, not generated matching utilities.', '',
        '| Method | NDCG@5 | 95% user-bootstrap CI | Recall@5 |',
        '|---|---:|---:|---:|',
    ]
    names = {'popularity':'Popularity', 'genre_content':'Genre content', 'itemknn':'ItemKNN', 'hybrid':'Validated historical baseline',
             'ease':'EASE', 'marginal_imputation':'History-only marginal imputation', 'flat_regret':'Flat regret + propagation',
             'hierarchy_regret':'Coherent hierarchy regret', 'complete_annotation_diagnostic':'Complete-annotation diagnostic'}
    for name, m in primary['ranking'].items():
        lo, hi = m['ndcg']['ci95']
        lines.append(f"| {names[name]} | {m['ndcg']['mean']:.4f} | [{lo:.4f}, {hi:.4f}] | {m['recall']['mean']:.4f} |")
    delta = primary['paired_ndcg_hierarchy_minus']['flat_regret']
    lines += ['', f"Primary paired NDCG difference (hierarchy minus flat): **{delta['mean']:+.4f}**, 95% CI **[{delta['ci95'][0]:+.4f}, {delta['ci95'][1]:+.4f}]**. The interval includes zero. This does not establish improvement or noninferiority.", '',
              'The historical baseline is a validation-selected genre/ItemKNN mixture with popularity fallback for an empty positive profile. Validation selects content weight 0. EASE regularization selects 10,000. All nonzero theme comparisons use the same gamma=.5; neither method receives extra labels.', '',
              'The complete-annotation row is a diagnostic using unmasked reference metadata, not a deployable missing-label baseline. Same-pool metrics must not be presented as a full-catalog contest.', '',
              '### Full-catalog baseline audit', '',
              '| Baseline | NDCG@5 | Recall@5 |', '|---|---:|---:|']
    for name,m in a['full_catalog_baselines'].items():
        lines.append(f"| {names[name]} | {m['ndcg']['mean']:.4f} | {m['recall']['mean']:.4f} |")
    lines += ['', 'This audit lets baselines rank the entire available unseen matched-film catalog. We did not run a full-catalog pairwise hierarchy solver, so no global superiority claim follows.', '',
              '## Metadata acquisition: same recommendations, different stopping rules', '',
              'The first item of the fixed historical ranking is checked against its 15 challengers. Both methods see the same adaptive lookup sequence, use sound propagation and stop when normalized worst-case matching regret is <=0.20. Each lookup reveals one bit of the LTO reference. The budget is 24. The five-item recommendation list remains identical throughout; the certificate concerns its first item.', '',
              '| Masked labels | Flat mean lookups | Hierarchy mean lookups | Mean saving, 95% CI | Relative reduction | Flat / hierarchy certified |',
              '|---|---:|---:|---:|---:|---:|']
    for mask, s in r['fixed_nonzero_by_mask'].items():
        q=s['lookup'];v=q['paired_saved_queries'];rel=a['by_mask'][mask]['relative_mean_query_reduction']
        lines.append(f"| {float(mask):.0%} | {q['flat_queries']['mean']:.3f} | {q['hierarchy_queries']['mean']:.3f} | {v['mean']:.3f} [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}] | {rel:.1%} | {q['flat_certified']} / {q['hierarchy_certified']} of 320 |")
    lines += ['', '- Costs include all sampled profiles and cap unsuccessful runs at their actual expenditure. They are not mean costs only among successful certificates.',
              '- At 50% masking, 19/320 profiles save lookups. Among these benefiting profiles the descriptive mean saving is 7.47; it is not a population-wide claim. There are 65 profiles that neither model certifies within the budget.',
              '- At 75% masking, 26/320 profiles save lookups. Only 129/320 receive a coherent certificate, versus 119/320 flat. The high failure rate matters.',
              '- The coherent model can never stop later than the flat model along this shared sequence because its bound is tighter. That ordering is mathematical. The empirical result measures the frequency and magnitude with rating-derived preferences.',
              '- These are simulated metadata annotation lookups. We did not measure human preference questions, actual tagging labor, API annotation cost or source-extraction accuracy.', '',
              '## Stress-test failure and the validation guard', '',
              f"At 75% missing labels and gamma=.5, hierarchy NDCG is **{stress['ranking']['hierarchy_regret']['ndcg']['mean']:.4f}**, versus **{stress['ranking']['hybrid']['ndcg']['mean']:.4f}** for the historical baseline. The paired difference is **{stress['paired_ndcg_hierarchy_minus']['hybrid']['mean']:+.4f}**, 95% CI **[{stress['paired_ndcg_hierarchy_minus']['hybrid']['ci95'][0]:+.4f}, {stress['paired_ndcg_hierarchy_minus']['hybrid']['ci95'][1]:+.4f}]**. This interval is negative in this stress condition.", '',
              'Validation selected gamma=0 before test scoring. Consequently, the selected deployment policy reproduces the historical baseline list exactly and has NDCG@5=0.2385. This is an intentional fallback supported by validation, not a hierarchy accuracy improvement. A nonsignificant difference at 50% masking must not hide the 75% failure.', '',
              '## Computational tradeoff', '',
              f"The 16-item pairwise matrix has median **{primary['pair_matrix_ms']['p50']:.1f} ms**, p95 **{primary['pair_matrix_ms']['p95']:.1f} ms** on this Mac, excluding fitting, retrieval and source I/O.", '',
              f"A separate post-result replay of the primary certification prefixes measures **{c['flat_ms']['mean']:.2f} ms** flat and **{c['hierarchy_ms']['mean']:.2f} ms** coherent computation on average. The added **{c['added_compute_ms']['mean']:.2f} ms** divided by **{c['saved_queries']['mean']:.3f}** saved lookups gives an exploratory mean break-even annotation latency of **{c['break_even_uniform_annotation_latency_ms']:.1f} ms per lookup**.", '',
              'That calculation assumes one uniform per-lookup latency. We did not measure annotation latency. Existing cheap labels may make exact certification unnecessary. This single replay times flat first and excludes fitting/retrieval/I/O, so it is not a production latency guarantee.', '',
              '## Contribution boundary', '',
              'This strengthens the earlier result with independent held-out relevance outcomes, stronger baselines, a quantified acquisition tradeoff and a falsifying stress condition. The candidate contribution remains the specialized exact uncertainty formulation and structural-fault extension, rather than invention of hierarchy tagging, minimax regret, graph cuts, or acquisition-cost analysis.', '',
              'One temporal split and one catalog intersection do not establish generalization. LTO annotations are retrospective and incomplete. Ratings reflect selective historical exposure. There is no new book/song user validation, human trial or SLM accuracy improvement. The original PDF’s seven-signal product ranking formula is not reproduced by this isolated decision-layer experiment.', '',
              '## Reproduction and verification', '',
              'Completed protocols and results are protected against overwrite. A replication uses the same frozen inputs in a separate output directory, rather than creating a new split:', '',
              '```bash',
              'mkdir -p docs/milestone2/hierarchy/heldout-reproduction',
              'cp docs/milestone2/hierarchy/heldout/{protocol,corpus,baseline-extension-protocol,full-catalog-audit-protocol}.json docs/milestone2/hierarchy/heldout-reproduction/',
              'PYTHONPATH=apps/api:ml/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-research/bin/python -m recros_ml.research.hierarchy_holdout validate --out docs/milestone2/hierarchy/heldout-reproduction',
              'PYTHONPATH=apps/api:ml/src OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv-research/bin/python -m recros_ml.research.hierarchy_holdout test --out docs/milestone2/hierarchy/heldout-reproduction',
              '```', '',
              'The local parquet cache is reconstructed by the `freeze` command only in a clean separate experiment; its hash must match the preserved protocol before scoring. The cache comes from the locally downloaded original data. Source hashes, identity exclusions, validation trials, per-user predictions, lookup sequences, full-catalog scores and timing replay are preserved.', '',
              'Verification: 112 API/ML tests pass, including conservative identity matching, temporal isolation, exclusion of evaluation users from background fitting, future-rating-independent sampling, constrained-ridge EASE equations, complete-information utility ranking and lookup stopping invariants.', '',
              '## Primary sources', '',
              '- [MovieLens 20M, GroupLens](https://grouplens.org/datasets/movielens/20m/)',
              '- [LTO v2026.04, author release](https://zenodo.org/records/19367236)',
              '- [EASE, Steck 2019](https://arxiv.org/abs/1905.03375)',
              '- [Metric definitions, RecBole](https://recbole.io/docs/recbole/recbole.evaluator.metrics.html)',
              '- [Derivation and attribution](../DERIVATION.md)', '',
    ]
    (OUT/'RESULT.md').write_text('\n'.join(lines)+'\n')
    print(OUT/'RESULT.md')


if __name__=='__main__': main()
