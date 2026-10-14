"""Full-catalog MovieLens pilot with global time splits and validation-only tuning.

No cross-domain or language-model accuracy claims follow from this experiment.
Run with PYTHONPATH=ml/src:apps/api python -m recros_ml.research.benchmark.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import time
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from recros_api.discovery import Candidate, rerank
from .metrics import bootstrap_mean, exposure_gini, ranking_metrics


def load_data(archive: Path):
    with zipfile.ZipFile(archive) as z:
        with z.open('ml-100k/u.data') as f:
            ratings = pd.read_csv(f, sep='\t', names=['user', 'item', 'rating', 'time'])
        lines = z.read('ml-100k/u.item').decode('latin-1').splitlines()
        items = [line.split('|') for line in lines]
    ratings[['user', 'item']] -= 1
    ratings = ratings.sort_values(['time', 'user', 'item'], kind='stable')
    # This dataset has unique user-item pairs. Fail instead of silently changing the task.
    if ratings.duplicated(['user', 'item']).any():
        raise ValueError('Repeated user-item pairs require an explicit repeat-consumption policy')
    genres = np.array([[int(v) for v in row[5:]] for row in items], dtype=np.float64)
    return ratings, genres


def split_global(ratings):
    times = ratings['time'].to_numpy()
    train_end, val_end = np.quantile(times, [.6, .8]).astype(int)
    return (ratings[ratings.time <= train_end],
            ratings[(ratings.time > train_end) & (ratings.time <= val_end)],
            ratings[ratings.time > val_end], int(train_end), int(val_end))


def fit(history, genres, n_users):
    n_items = len(genres)
    positive = history[history.rating >= 4]
    matrix = csr_matrix((np.ones(len(positive)), (positive.user, positive.item)), shape=(n_users, n_items))
    counts = np.asarray(matrix.sum(axis=0)).ravel()
    cooccurrence = (matrix.T @ matrix).toarray()
    sim = cooccurrence / np.maximum(np.sqrt(counts[:, None] * counts[None, :]), 1)
    sim *= cooccurrence / (cooccurrence + 20)  # fixed shrinkage, no test tuning
    np.fill_diagonal(sim, 0)
    # Keep at most 50 neighbors per source item.
    for row in sim:
        row[np.argsort(-row, kind='stable')[50:]] = 0
    cf = np.asarray(matrix @ sim)
    normalized_genres = genres / np.maximum(np.linalg.norm(genres, axis=1, keepdims=True), 1)
    profiles = np.asarray(matrix @ normalized_genres)
    profiles /= np.maximum(np.linalg.norm(profiles, axis=1, keepdims=True), 1e-12)
    content = profiles @ normalized_genres.T
    observed = np.zeros(n_items, dtype=bool)
    observed[history.item.unique()] = True
    seen = {int(u): set(g.item.astype(int)) for u, g in history.groupby('user')}
    histories = positive.groupby('user').size().to_dict()
    # Long tail = bottom 80% of available items by training-only positive count.
    available_ids = np.flatnonzero(observed)
    order = available_ids[np.lexsort((available_ids, counts[available_ids]))]
    tail = set(order[:int(.8 * len(order))].tolist())
    # Tie-aware popularity percentile avoids arbitrary novelty differences at equal count.
    sorted_counts = np.sort(counts[observed])
    novelty = 1 - (np.searchsorted(sorted_counts, counts, side='left') +
                   np.searchsorted(sorted_counts, counts, side='right')) / (2 * len(sorted_counts))
    return dict(cf=cf, content=content, counts=counts, available=observed, seen=seen,
                histories=histories, tail=tail, novelty=novelty, genres=genres)


def unit_scale(x):
    return x / max(float(x.max()), 1e-12)


def score_users(model, evaluation, method, alpha=0.0, budget=0.0, k=10):
    rows, exposure = [], np.zeros(len(model['counts']))
    skipped = Counter()
    facets = [frozenset(str(g) for g in np.flatnonzero(gs)) for gs in model['genres']]
    for user, events in evaluation.groupby('user'):
        user = int(user)
        # Freeze all profiles at the window start; do not update from eval events.
        if model['histories'].get(user, 0) < 3:
            skipped['fewer_than_3_past_positive_ratings'] += 1
            continue
        known = model['seen'].get(user, set())
        relevant_all = set(events.loc[events.rating >= 4, 'item'].astype(int)) - known
        relevant = {i for i in relevant_all if model['available'][i]}
        skipped['positive_targets_unavailable_at_cutoff'] += len(relevant_all - relevant)
        if not relevant:
            skipped['no_eligible_positive_target'] += 1
            continue
        start = time.perf_counter()
        candidate_ids = [int(i) for i in np.flatnonzero(model['available']) if i not in known]
        pop = unit_scale(np.log1p(model['counts']))
        if method == 'popularity':
            scores = pop
        elif method == 'content':
            scores = model['content'][user]
        elif method in ('itemknn', 'hybrid', 'discovery'):
            cf = unit_scale(model['cf'][user])
            scores = (1 - alpha) * cf + alpha * model['content'][user]
        else:
            raise ValueError(method)
        ranked = sorted(candidate_ids, key=lambda i: (-scores[i], str(i)))
        loss = 0.0
        if method == 'discovery':
            pool = [Candidate(str(i), float(scores[i]), float(model['novelty'][i]), facets[i]) for i in ranked[:100]]
            selected, certificate = rerank(pool, k, budget)
            top = [int(c.key) for c in selected]
            loss = certificate['predicted_loss_fraction']
        else:
            top = ranked[:k]
        elapsed = (time.perf_counter() - start) * 1000
        metrics = ranking_metrics(top, relevant, k)
        ild = [1 - len(facets[a] & facets[b]) / len(facets[a] | facets[b])
               if facets[a] | facets[b] else 0.0
               for j, a in enumerate(top) for b in top[j + 1:]]
        rows.append(dict(user=user, **metrics, tail_share=np.mean([i in model['tail'] for i in top]),
                         ild=np.mean(ild) if ild else 0.0, predicted_loss=loss, ms=elapsed,
                         candidates=len(candidate_ids), past_positives=model['histories'][user]))
        exposure[top] += 1
    if not rows:
        raise ValueError('No eligible evaluation users')
    summary = {key: bootstrap_mean([r[key] for r in rows]) for key in ['ndcg', 'recall', 'map', 'precision', 'tail_share', 'ild']}
    summary.update(users=len(rows), coverage=float(np.count_nonzero(exposure) / model['available'].sum()),
                   exposure_gini=exposure_gini(exposure[model['available']]),
                   predicted_loss_max=max(r['predicted_loss'] for r in rows),
                   latency_ms_p50=float(np.median([r['ms'] for r in rows])),
                   latency_ms_p95=float(np.quantile([r['ms'] for r in rows], .95)),
                   candidates_min=min(r['candidates'] for r in rows),
                   candidates_max=max(r['candidates'] for r in rows), skipped=dict(skipped))
    return summary, rows


def run(archive: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    ratings, genres = load_data(archive)
    train, val, test, train_end, val_end = split_global(ratings)
    n_users = int(ratings.user.max()) + 1
    val_model = fit(train, genres, n_users)
    # Preregistered, small search. No test results used for choosing alpha/budget.
    validations = []
    for alpha in [0.0, .15, .3]:
        summary, _ = score_users(val_model, val, 'hybrid', alpha)
        validations.append(dict(alpha=alpha, budget=0.0, **summary))
    best_alpha = max(validations, key=lambda x: x['ndcg']['mean'])['alpha']
    base_val = next(r for r in validations if r['alpha'] == best_alpha)
    trials = []
    for budget in [.02, .05, .10]:
        summary, _ = score_users(val_model, val, 'discovery', best_alpha, budget)
        trials.append(dict(alpha=best_alpha, budget=budget, **summary))
    eligible = [r for r in trials if r['ndcg']['mean'] >= .95 * base_val['ndcg']['mean']]
    # Fall back to zero if no tested policy meets validation relevance tolerance.
    choice = max([dict(base_val)] + eligible, key=lambda x: (x['coverage'], x['tail_share']['mean'], -x['budget']))
    final_model = fit(pd.concat([train, val]), genres, n_users)
    results, records = {}, {}
    for method in ['popularity', 'content', 'itemknn', 'hybrid', 'discovery']:
        summary, rows = score_users(final_model, test, method,
                                    best_alpha if method in ('hybrid', 'discovery') else 0,
                                    choice['budget'] if method == 'discovery' else 0)
        results[method], records[method] = summary, rows
        print(f"{method}: NDCG@10={summary['ndcg']['mean']:.4f} coverage={summary['coverage']:.4f}", flush=True)
    before = {r['user']: r['ndcg'] for r in records['hybrid']}
    deltas = [r['ndcg'] - before[r['user']] for r in records['discovery']]
    manifest = dict(dataset='MovieLens 100K', source='https://grouplens.org/datasets/movielens/100k/',
                    sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), ratings=len(ratings),
                    users=n_users, items=len(genres), splits=dict(train=len(train), validation=len(val), test=len(test)),
                    train_end_unix=train_end, validation_end_unix=val_end,
                    protocol='Global 60/20/20 time windows; refit on train+validation for test; frozen profiles; full available catalog minus history; rating>=4 relevant; unobserved treated as nonrelevant for offline metrics',
                    candidate_availability='Observed at least once before cutoff; excludes future-only items; historical genre metadata assumed stable',
                    k=10, rerank_pool=100, score_normalization='CF per-user maximum normalization; genre cosine in [0,1]; convex mixture; no offset',
                    tail_definition='Bottom 80% of available items by past positive count; item ID breaks boundary ties',
                    selection='Max validation coverage subject to <=5% relative NDCG loss vs chosen hybrid; tie break tail share then smaller budget',
                    chosen_alpha=best_alpha, chosen_budget=choice['budget'], validation_baselines=validations,
                    validation_rerank=trials, test=results, paired_ndcg_delta=bootstrap_mean(deltas),
                    environment=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, machine=platform.machine()),
                    limitations=['Single-domain pilot; no evidence of cross-domain transfer or SLM benefit',
                                 'One global split; confidence intervals resample users, not datasets or time windows',
                                 'Observed ratings are not randomized exposure; Gini/tail exposure are not provider fairness',
                                 'Predicted utility bound does not bound actual NDCG loss',
                                 'Latency is local scoring/reranking, excludes fit, HTTP, retrieval I/O and language inference'])
    (out / 'results.json').write_text(json.dumps(manifest, indent=2, allow_nan=False))
    with (out / 'per_user.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['method'] + list(records['hybrid'][0]))
        writer.writeheader()
        for method, rows in records.items():
            writer.writerows(dict(method=method, **row) for row in rows)
    lines = ['# MovieLens pilot: measured results', '',
             'This is a **single-domain, non-language-model** experiment, not a reproduction of milestone 1.', '',
             f"Validation chose content weight **{best_alpha}** and predicted utility budget **{choice['budget']:.0%}**.", '',
             '| Method | NDCG@10 (95% user bootstrap CI) | Recall@10 | Coverage@10 | Tail share | Gini ↓ | p95 ms |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for name, r in results.items():
        lo, hi = r['ndcg']['ci95']
        lines.append(f"| {name} | {r['ndcg']['mean']:.4f} [{lo:.4f}, {hi:.4f}] | {r['recall']['mean']:.4f} | {r['coverage']:.2%} | {r['tail_share']['mean']:.2%} | {r['exposure_gini']:.4f} | {r['latency_ms_p95']:.2f} |")
    lines += ['', f"Test users evaluated: {results['hybrid']['users']}. Paired NDCG change (discovery − hybrid): {manifest['paired_ndcg_delta']}.", '',
              '## Protocol', '', manifest['protocol'], '', '## Limits', ''] + ['- ' + x for x in manifest['limitations']]
    (out / 'RESULTS.md').write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, default=Path('ml/data/raw/ml-100k.zip'))
    parser.add_argument('--out', type=Path, default=Path('docs/milestone2/results'))
    args = parser.parse_args()
    run(args.archive, args.out)
