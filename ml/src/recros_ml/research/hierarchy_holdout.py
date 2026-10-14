"""Prospective local protocol: real held-out ratings, simulated missing metadata.

No synthetic preferences are used as relevance judgments. The tag-completion
reference is still closed-world LTO, not an exhaustive human annotation oracle.
The old structural experiment and its frozen files are never modified.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import time

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

from recros_api.hierarchy_regret import flat_gap, pair_gap, propagate
from .hierarchy_experiment import DATA, ROOT, digest, load_lto
from .metrics import bootstrap_mean, exposure_gini, ranking_metrics

OUT = ROOT / 'docs/milestone2/hierarchy/heldout'
CACHE = ROOT / 'ml/data/processed/hierarchy-holdout'
SEED = 314159


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def title_key(value):
    return re.sub(r'[^a-z0-9]', '', str(value).casefold())


def match_movies(items, metadata, links):
    """Only unique title/year -> IMDb -> MovieLens identities; no fuzzy matches."""
    lookup = {}
    for row in metadata.itertuples():
        year = str(row.release_date)[:4]
        imdb = str(row.imdb_id)
        if not re.fullmatch(r'tt\d+', imdb):
            continue
        for title in (row.title, row.original_title):
            lookup.setdefault((title_key(title), year), set()).add(imdb)
    movie_ids = {}
    for row in links.dropna(subset=['imdbId']).itertuples():
        movie_ids.setdefault(f'tt{int(row.imdbId):07d}', set()).add(int(row.movieId))
    matched, excluded = [], []
    for item in sorted(items, key=lambda x: x['id']):
        if item['domain'] != 'movie':
            continue
        year = re.search(r'\((\d{4})\)$', item['id'])
        choices = lookup.get((title_key(item['title']), year.group(1) if year else ''), set())
        if len(choices) != 1:
            excluded.append({'lto_id': item['id'], 'reason': 'nonunique_or_missing_title_year'})
            continue
        imdb = next(iter(choices))
        ids = movie_ids.get(imdb, set())
        if len(ids) != 1:
            excluded.append({'lto_id': item['id'], 'reason': 'nonunique_or_missing_imdb_link'})
            continue
        matched.append({**item, 'movieId': next(iter(ids)), 'imdb_id': imdb, 'year': int(year.group(1))})
    # One ontology record per MovieLens identity. Exclude duplicates, do not select one silently.
    counts = Counter(x['movieId'] for x in matched)
    duplicates = [x for x in matched if counts[x['movieId']] != 1]
    excluded += [{'lto_id': x['id'], 'reason': 'duplicate_lto_identity'} for x in duplicates]
    return [x for x in matched if counts[x['movieId']] == 1], excluded


def split_frames(ratings, train_end, val_end):
    return (ratings[ratings.time <= train_end],
            ratings[(ratings.time > train_end) & (ratings.time <= val_end)],
            ratings[ratings.time > val_end])


def eligible_users(history, future, partition, maximum):
    counts = history.groupby('user').size()
    positives = history[history.rating >= 4].groupby('user').size()
    future_counts = future.groupby('user').size()
    # Future *activity*, not future rating values, determines evaluability.
    users = [int(u) for u in counts.index if counts[u] >= 20 and positives.get(u, 0) >= 3
             and future_counts.get(u, 0) >= 5 and (int(u) % 5 == 0) == (partition == 'validation')]
    rng = np.random.default_rng(SEED + (0 if partition == 'validation' else 1))
    rng.shuffle(users)
    return sorted(users[:maximum]), len(users)


def freeze():
    if (OUT / 'protocol.json').exists():
        raise RuntimeError('Held-out protocol already frozen. Never overwrite it.')
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    themes, edges, closures, items, issues = load_lto()
    metadata = pd.read_csv(ROOT / 'movie_dataset/movies_metadata.csv', low_memory=False)
    links = pd.read_csv(ROOT / 'movie_dataset/links.csv')
    matched, excluded = match_movies(items, metadata, links)
    mapping = {x['movieId']: i for i, x in enumerate(matched)}
    rows, total = [], 0
    for chunk in pd.read_csv(ROOT / 'movie_dataset/rating.csv', chunksize=1_000_000,
                             dtype={'userId': 'int32', 'movieId': 'int32', 'rating': 'float32'}):
        total += len(chunk)
        part = chunk[chunk.movieId.isin(mapping)].copy()
        part['item'] = part.movieId.map(mapping).astype('int32')
        part['user'] = part.userId.astype('int32')
        part['time'] = pd.to_datetime(part.timestamp, utc=True).astype('int64') // 10**9
        rows.append(part[['user', 'item', 'rating', 'time']])
        print(json.dumps({'stage': 'filter_ratings', 'source_rows': total}), flush=True)
    ratings = pd.concat(rows, ignore_index=True).sort_values(['time', 'user', 'item'], kind='stable')
    if ratings.duplicated(['user', 'item']).any():
        raise ValueError('Repeated user-item ratings require an explicit policy.')
    train_end, val_end = np.quantile(ratings.time, [.6, .8]).astype(int)
    train, val, test = split_frames(ratings, train_end, val_end)
    val_users, nval = eligible_users(train, val, 'validation', 128)
    test_users, ntest = eligible_users(pd.concat([train, val]), test, 'test', 320)
    if len(val_users) < 40 or len(test_users) < 80:
        raise ValueError('Too few temporally eligible users; record and design a separate protocol.')
    by_imdb = {}
    for row in metadata.itertuples():
        try:
            genres = [g['name'] for g in ast.literal_eval(str(row.genres))]
        except (ValueError, SyntaxError, KeyError, TypeError):
            genres = []
        by_imdb.setdefault(str(row.imdb_id), set()).update(genres)
    for item in matched:
        item['genres'] = sorted(by_imdb.get(item['imdb_id'], set()))
    corpus = {'items': matched, 'features': sorted(themes), 'edges': edges,
              'closures': {k: sorted(v) for k, v in closures.items()}}
    (OUT / 'corpus.json').write_text(json.dumps(corpus, indent=2) + '\n')
    (OUT / 'identity-exclusions.json').write_text(json.dumps(excluded, indent=2) + '\n')
    ratings.to_parquet(CACHE / 'ratings.parquet', index=False)
    protocol = {
        'created_utc': datetime.now(timezone.utc).isoformat(), 'seed': SEED,
        'question': 'Does coherent partial-label uncertainty improve real held-out ranking, or certify the same ranking with fewer metadata lookups?',
        'source': 'MovieLens 20M ratings joined to public LTO v2026.04 through unique title/year + IMDb IDs',
        'sources': {'ratings': 'https://grouplens.org/datasets/movielens/20m/', 'ontology': 'https://zenodo.org/records/19367236'},
        'source_rows': total, 'matched_movies': len(matched), 'matched_ratings': len(ratings),
        'source_hashes': {str(p.relative_to(ROOT)): sha(p) for p in [DATA, ROOT/'movie_dataset/rating.csv', ROOT/'movie_dataset/links.csv', ROOT/'movie_dataset/movies_metadata.csv']},
        'corpus_sha256': digest(corpus), 'ratings_cache_sha256': sha(CACHE/'ratings.parquet'),
        'train_end': int(train_end), 'validation_end': int(val_end),
        'split_counts': {'train': len(train), 'validation': len(val), 'test': len(test)},
        'validation_users': val_users, 'test_users': test_users,
        'eligible_users': {'validation': nval, 'test': ntest},
        'user_sampling': 'Random seeded samples; disjoint userId modulo-5 partitions; >=20 past matched ratings, >=3 past positives, >=5 future events. Future rating values not used for sampling.',
        'history_limit': 20, 'history_policy': 'Only last 20 pre-window ratings form profiles. All prior seen items are excluded. Evaluation users are excluded from background similarity/popularity fitting.',
        'availability': 'At least one non-evaluation-user rating before the relevant cutoff. Genre/theme metadata assumed static; 2026 annotations are retrospective.',
        'candidate_pool': 16, 'k': 5,
        'retrieval': 'Top 16 available unseen films by validation-selected genre/ItemKNN hybrid; no held-out positives inserted. Same pool for every method.',
        'relevance': 'Held-out rating >=4; unobserved items treated as nonrelevant. Primary metrics include every sampled user; a positive-target subset is also reported.',
        'alpha_grid': [0, .25, .5, .75, 1], 'ridge_lambda': 10,
        'gamma_grid': [0, .25, .5, 1], 'fixed_nonzero_gamma': .5,
        'gamma_selection': 'Max validation NDCG averaged across propagated-flat and coherent methods at primary mask; identical gamma for their comparison. Zero is allowed; separately frozen .5 diagnostic prevents a zero-weight comparison from being presented as a mechanism test.',
        'facets': 'Top 16 absolute ridge coefficients from past ratings plus all ancestors; retain learned coefficients on ancestors. L1 normalize, integer scale 1000.',
        'weight_uncertainty': 'Independent signed intervals +/-25% of each integer coefficient. These are sensitivity intervals, not calibrated confidence intervals.',
        'missing_fractions': [.5, .75], 'primary_missing_fraction': .5,
        'annotation_reference': 'Listed LTO themes + ancestors=1, unlisted=0 only in this closed-world simulation. Facts are independently masked; observed facts propagated for BOTH flat and coherent methods.',
        'imputation_prior': 'Past-profile item annotations only; no hidden target annotation used for its marginal probabilities.',
        'methods': ['popularity', 'genre_content', 'itemknn', 'hybrid', 'marginal_imputation', 'flat_regret', 'hierarchy_regret', 'complete_annotation_diagnostic'],
        'primary_ranking_contrast': 'Paired test-user NDCG@5 at gamma=.5 and missing=.5: hierarchy_regret minus flat_regret. Validation-selected gamma is a separate deployment-policy result. Secondary comparisons to hybrid and marginal imputation.',
        'lookup_experiment': {'gamma': .5, 'threshold': .20, 'max_queries': 24,
                              'recommendation': 'Fixed hybrid list and its first item; compare certification cost, never change ranking between bound methods.',
                              'schedule': 'Shared adaptive schedule: weighted entropy of each unknown candidate/facet using history-only prevalence and ancestor influence; tie by item/feature index.',
                              'stop': 'Normalized worst-case gap of fixed first item <=.20, or 24 single-bit LTO-reference lookups. Queries can reveal absent bits under the closed-world reference.',
                              'scope': 'Metadata annotation lookups, not human preference questions; correctness conditional on box utility and the reference ontology.'},
        'statistics': '2000 paired user bootstrap resamples; masks not treated as independent users. No noninferiority or human-satisfaction claim from a nonsignificant difference.',
        'scope': 'Single-domain real historical-rating evaluation with simulated missing metadata and limited profile histories. Not book/music transfer, zero-history user validation, prospective user study, or SLM improvement.',
        'data_issues': issues,
    }
    (OUT / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    print(json.dumps({'frozen_protocol_sha256': digest(protocol), 'movies': len(matched), 'ratings': len(ratings), 'validation_users': len(val_users), 'test_users': len(test_users)}), flush=True)


def matrices(corpus):
    features = corpus['features']; idx = {f: j for j, f in enumerate(features)}
    tags = [set(i['closure']) for i in corpus['items']]
    x = np.array([[int(f in present) for f in features] for present in tags], dtype=np.float64)
    genres = sorted({g for i in corpus['items'] for g in i['genres']})
    g = np.array([[int(v in i['genres']) for v in genres] for i in corpus['items']], dtype=float)
    g /= np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1)
    return x, g, idx


def background(history, nitems, excluded_users):
    history = history[~history.user.isin(excluded_users)]
    positive = history[history.rating >= 4]
    matrix = csr_matrix((np.ones(len(positive)), (positive.user, positive.item)),
                        shape=(int(history.user.max()) + 1, nitems))
    counts = np.asarray(matrix.sum(axis=0)).ravel()
    common = (matrix.T @ matrix).toarray()
    sim = common / np.maximum(np.sqrt(counts[:, None] * counts[None, :]), 1)
    sim *= common / (common + 20)
    np.fill_diagonal(sim, 0)
    for row in sim:
        row[np.argsort(-row, kind='stable')[50:]] = 0
    available = np.zeros(nitems, dtype=bool); available[history.item.unique()] = True
    pop = np.log1p(counts); pop /= max(float(pop.max()), 1)
    return {'sim': sim, 'gram': common, 'counts': counts, 'popularity': pop, 'available': available}


def fit_ease(gram, regularization):
    """Steck 2019 EASE: inverse Gram, zero diagonal; no downloaded weights."""
    precision = np.linalg.inv(gram + regularization*np.eye(len(gram)))
    weights = -precision / np.diag(precision)[None, :]
    np.fill_diagonal(weights, 0)
    return weights


def profile(history, x, genres, bg, limit=20):
    past = history.sort_values(['time', 'item'], kind='stable').tail(limit)
    ids = past.item.to_numpy(dtype=int)
    positive = past.loc[past.rating >= 4, 'item'].to_numpy(dtype=int)
    cf = bg['sim'][positive].sum(axis=0) if len(positive) else np.zeros(len(x))
    cf /= max(float(cf.max()), 1e-12)
    gp = genres[positive].sum(axis=0) if len(positive) else np.zeros(genres.shape[1])
    gp /= max(float(np.linalg.norm(gp)), 1e-12)
    content = genres @ gp
    y = past.rating.to_numpy(dtype=float); y -= y.mean()
    h = x[ids]
    dual = np.linalg.solve(h @ h.T + 10 * np.eye(len(h)), y)
    weights = h.T @ dual
    return {'cf': cf, 'content': content, 'weights': weights, 'history_ids': ids, 'positive_ids': positive,
            'seen': set(history.item.astype(int)), 'past_count': len(past)}


def ranking(scores, ids, k):
    return sorted(map(int, ids), key=lambda i: (-float(scores[i]), i))[:k]


def cases_for(users, history, evaluation, corpus, x, genres, bg):
    histories = {int(u): g for u, g in history[history.user.isin(users)].groupby('user')}
    evaluations = {int(u): g for u, g in evaluation[evaluation.user.isin(users)].groupby('user')}
    cases = []
    for u in users:
        p = profile(histories[u], x, genres, bg)
        available = [int(i) for i in np.flatnonzero(bg['available']) if i not in p['seen']]
        events = evaluations[u]
        relevant_all = set(events.loc[events.rating >= 4, 'item'].astype(int)) - p['seen']
        relevant = relevant_all & set(available)
        cases.append({'user': u, 'profile': p, 'available': available, 'relevant': relevant,
                      'unavailable_positives': len(relevant_all - relevant), 'future_events': len(events)})
    return cases


def active_model(case, corpus, x, feature_index):
    w = case['profile']['weights']
    seeds = np.argsort(-np.abs(w), kind='stable')[:16]
    active = set()
    for j in seeds:
        active.update(corpus['closures'][corpus['features'][int(j)]])
    names = sorted(active); positions = np.array([feature_index[f] for f in names], dtype=int)
    indexes = {f: j for j, f in enumerate(names)}
    edges = [(indexes[c], indexes[p]) for c, p in corpus['edges'] if c in indexes and p in indexes]
    coefficients = w[positions]
    coefficients = np.rint(1000 * coefficients / max(float(np.abs(coefficients).sum()), 1e-12)).astype(int)
    width = np.rint(.25 * np.abs(coefficients)).astype(int)
    prior = x[case['profile']['history_ids']][:, positions].mean(axis=0)
    return positions, coefficients, coefficients-width, coefficients+width, edges, prior


def regret_matrices(observed, lower, upper, edges):
    states = [propagate(row, edges) for row in observed]
    n = len(states); flat = np.zeros((n, n)); exact = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j: continue
            flat[i, j] = flat_gap(states[i], states[j], lower, upper)
            exact[i, j] = pair_gap(states[i], states[j], lower, upper, edges).value
    if np.any(exact > flat): raise AssertionError('Bound order failed.')
    return states, flat, exact


def regret_order(gaps, base, gamma):
    values = gamma * gaps + base[None, :] - base[:, None]
    worst = np.maximum(values.max(axis=1), 0)
    return np.lexsort((np.arange(len(base)), -base, worst)).tolist(), worst


def lookup_cost(observed, reference, lower, upper, edges, prior, base, gamma=.5, threshold=.20, budget=24):
    """Identical ranking + identical query sequence; separately record stop times."""
    state = [list(propagate(row, edges)) for row in observed]
    normalizer = float(np.max(base)-np.min(base) + gamma * sum(max(abs(l), abs(u)) for l, u in zip(lower, upper))) or 1
    influence = np.maximum(np.abs(lower), np.abs(upper)).astype(float)
    # Parents can reveal multiple weighted descendants via a negative answer.
    for child, parent in edges:
        influence[parent] += max(abs(int(lower[child])), abs(int(upper[child])))
    entropy = -(np.clip(prior, 1e-6, 1-1e-6)*np.log2(np.clip(prior, 1e-6, 1-1e-6))
                + np.clip(1-prior, 1e-6, 1-1e-6)*np.log2(np.clip(1-prior, 1e-6, 1-1e-6)))
    importance = influence * entropy
    stops = {}; initial = {}; last = {}; queried = []
    for step in range(budget+1):
        bounds = {'flat': 0., 'hierarchy': 0.}
        for j in range(1, len(state)):
            offset = float(base[j]-base[0])
            bounds['flat'] = max(bounds['flat'], gamma*flat_gap(state[0], state[j], lower, upper)+offset)
            bounds['hierarchy'] = max(bounds['hierarchy'], gamma*pair_gap(state[0], state[j], lower, upper, edges).value+offset)
        if bounds['hierarchy'] > bounds['flat'] + 1e-8: raise AssertionError('Lookup bound order failed.')
        if step == 0: initial = {k: v/normalizer for k, v in bounds.items()}
        last = {k: v/normalizer for k, v in bounds.items()}
        for method, value in last.items():
            if value <= threshold and method not in stops: stops[method] = step
        if len(stops) == 2 or step == budget: break
        unknown = [(float(importance[j]), -i, -j) for i, row in enumerate(state)
                   for j, value in enumerate(row) if value is None and importance[j] > 0]
        if not unknown: break
        _, ni, nj = max(unknown); i, j = -ni, -nj
        state[i][j] = int(reference[i, j]); queried.append((i, j))
        state = [list(propagate(row, edges)) for row in state]
    spent = len(queried)
    return {'flat_queries': stops.get('flat', spent), 'hierarchy_queries': stops.get('hierarchy', spent),
            'flat_certified': 'flat' in stops, 'hierarchy_certified': 'hierarchy' in stops,
            'initial_flat_bound': initial['flat'], 'initial_hierarchy_bound': initial['hierarchy'],
            'final_flat_bound': last['flat'], 'final_hierarchy_bound': last['hierarchy'],
            'query_sequence': queried}


def prepare_scores(case, alpha, bg):
    p = case['profile']
    hybrid = alpha*p['content'] + (1-alpha)*p['cf']
    # Fallback is fixed and shared: if no profile score, use background popularity.
    if not np.any(hybrid[case['available']]): hybrid = bg['popularity'].copy()
    scores = {'popularity': bg['popularity'], 'genre_content': p['content'], 'itemknn': p['cf'], 'hybrid': hybrid}
    if 'ease' in bg:
        scores['ease'] = bg['ease'][p['positive_ids']].sum(axis=0) if len(p['positive_ids']) else np.zeros(len(hybrid))
    return scores


def evaluate_case(case, alpha, gammas, corpus, x, feature_index, bg, masks, lookup=False):
    scores = prepare_scores(case, alpha, bg)
    pool = ranking(scores['hybrid'], case['available'], 16)
    positions, mid, lower, upper, edges, prior = active_model(case, corpus, x, feature_index)
    reference = x[np.ix_(pool, positions)].astype(int)
    base = np.rint(1000*scores['hybrid'][pool]).astype(int)
    rows = []
    for fraction in masks:
        rng = np.random.default_rng(SEED + case['user']*11 + int(100*fraction))
        missing = rng.random(reference.shape) < fraction
        observed = [[None if missing[i,j] else int(reference[i,j]) for j in range(len(positions))] for i in range(len(pool))]
        clock = time.perf_counter(); states, flat, exact = regret_matrices(observed, lower, upper, edges)
        solve_ms = (time.perf_counter()-clock)*1000
        imputed = np.array([[prior[j] if v is None else v for j,v in enumerate(row)] for row in states])
        lookups = lookup_cost(observed, reference, lower, upper, edges, prior, base) if lookup else None
        for gamma in gammas:
            methods = {name: ranking(score, pool, 5) for name, score in scores.items()}
            fi, fb = regret_order(flat, base, gamma); ei, eb = regret_order(exact, base, gamma)
            methods['flat_regret'] = [pool[i] for i in fi[:5]]
            methods['hierarchy_regret'] = [pool[i] for i in ei[:5]]
            methods['marginal_imputation'] = [pool[i] for i in np.argsort(-(base+gamma*(imputed@mid)), kind='stable')[:5]]
            methods['complete_annotation_diagnostic'] = [pool[i] for i in np.argsort(-(base+gamma*(reference@mid)), kind='stable')[:5]]
            metrics = {name: ranking_metrics(top, case['relevant'], 5) for name, top in methods.items()}
            row = {'user': case['user'], 'missing_fraction': fraction, 'gamma': gamma,
                   'facets': len(positions), 'pool': pool, 'rankings': methods, 'metrics': metrics,
                   'relevant_count': len(case['relevant']), 'retrieved_positive_count': len(set(pool)&case['relevant']),
                   'unavailable_positives': case['unavailable_positives'], 'solve_ms': solve_ms,
                   'exact_flat_same_ranking': methods['flat_regret'] == methods['hierarchy_regret'],
                   'exact_bound_same_item': float(eb[ei[0]]), 'flat_bound_same_item': float(fb[ei[0]])}
            if lookup:
                row['lookup'] = dict(lookups)
                # Verify both cost comparisons really use the same recommendation.
                row['lookup']['fixed_ranking'] = methods['hybrid']
                row['lookup']['fixed_ndcg'] = metrics['hybrid']['ndcg']
            rows.append(row)
    return rows


def load_inputs():
    p = json.loads((OUT/'protocol.json').read_text()); corpus = json.loads((OUT/'corpus.json').read_text())
    if digest(corpus) != p['corpus_sha256'] or sha(CACHE/'ratings.parquet') != p['ratings_cache_sha256']:
        raise ValueError('Frozen input hash mismatch.')
    return p, corpus, pd.read_parquet(CACHE/'ratings.parquet')


def validate():
    if (OUT/'validation.json').exists(): raise RuntimeError('Validation already completed; preserve it.')
    p, corpus, ratings = load_inputs(); train, val, _ = split_frames(ratings,p['train_end'],p['validation_end'])
    x, genres, index = matrices(corpus); excluded = set(p['validation_users']+p['test_users'])
    bg = background(train,len(x),excluded)
    cases = cases_for(p['validation_users'],train,val,corpus,x,genres,bg)
    alpha_trials = []
    for alpha in p['alpha_grid']:
        values = [ranking_metrics(ranking(prepare_scores(c,alpha,bg)['hybrid'],c['available'],5),c['relevant'],5)['ndcg'] for c in cases]
        alpha_trials.append({'alpha':alpha, 'ndcg':float(np.mean(values))})
    alpha = max(alpha_trials,key=lambda v:(v['ndcg'],-v['alpha']))['alpha']
    extension=json.loads((OUT/'baseline-extension-protocol.json').read_text())
    if extension['parent_protocol_sha256']!=digest(p): raise ValueError('Baseline extension mismatch.')
    ease_trials=[]
    for regularization in extension['ease_lambda_grid']:
        bg['ease']=fit_ease(bg['gram'],regularization)
        values=[ranking_metrics(ranking(prepare_scores(c,alpha,bg)['ease'],c['available'],5),c['relevant'],5)['ndcg'] for c in cases]
        ease_trials.append({'lambda':regularization,'ndcg':float(np.mean(values))})
    chosen_lambda=max(ease_trials,key=lambda v:(v['ndcg'],-v['lambda']))['lambda']
    bg['ease']=fit_ease(bg['gram'],chosen_lambda)
    rows = []
    for n,c in enumerate(cases):
        rows.extend(evaluate_case(c,alpha,p['gamma_grid'],corpus,x,index,bg,[.5]))
        if (n+1)%16 == 0: print(json.dumps({'stage':'validation','users':n+1,'total':len(cases)}),flush=True)
    trials=[]
    for gamma in p['gamma_grid']:
        subset=[r for r in rows if r['gamma']==gamma]
        means={name:float(np.mean([r['metrics'][name]['ndcg'] for r in subset])) for name in p['methods']}
        trials.append({'gamma':gamma,'ndcg':means,'selection_mean':(means['flat_regret']+means['hierarchy_regret'])/2})
    gamma=max(trials,key=lambda v:(v['selection_mean'],-v['gamma']))['gamma']
    selection={'protocol_sha256':digest(p),'extension_protocol_sha256':digest(extension),
               'chosen_alpha':alpha,'chosen_gamma':gamma,'alpha_trials':alpha_trials,
               'chosen_ease_lambda':chosen_lambda,'ease_trials':ease_trials,
               'gamma_trials':trials,'background_ratings':int((~train.user.isin(excluded)).sum()),
               'available_movies':int(bg['available'].sum()), 'selection_scope':'Validation users/window only; no test performance consulted.'}
    (OUT/'validation-per-user.json').write_text(json.dumps(rows,indent=2)+'\n')
    (OUT/'validation.json').write_text(json.dumps(selection,indent=2)+'\n')
    print(json.dumps(selection),flush=True)


def summary(rows, corpus, bg):
    methods = list(rows[0]['metrics']); result={}
    for name in methods:
        records=[r['metrics'][name] for r in rows]
        exposure=np.zeros(len(corpus['items']))
        for r in rows: exposure[r['rankings'][name]]+=1
        result[name]={metric:bootstrap_mean([m[metric] for m in records]) for metric in records[0]}
        result[name]['catalog_coverage']=float(np.count_nonzero(exposure)/bg['available'].sum())
        result[name]['exposure_gini']=exposure_gini(exposure[bg['available']])
    paired={}
    for name in ('flat_regret','hybrid','marginal_imputation'):
        paired[name]=bootstrap_mean([r['metrics']['hierarchy_regret']['ndcg']-r['metrics'][name]['ndcg'] for r in rows])
    lookups=[r['lookup'] for r in rows]
    savings=[r['flat_queries']-r['hierarchy_queries'] for r in lookups]
    return {'users':len(rows),'users_with_positive_targets':sum(r['relevant_count']>0 for r in rows),
            'ranking':result,'paired_ndcg_hierarchy_minus':paired,
            'lookup':{'flat_queries':bootstrap_mean([r['flat_queries'] for r in lookups]),
                      'hierarchy_queries':bootstrap_mean([r['hierarchy_queries'] for r in lookups]),
                      'paired_saved_queries':bootstrap_mean(savings),'users_saving_queries':sum(v>0 for v in savings),
                      'flat_certified':sum(r['flat_certified'] for r in lookups),
                      'hierarchy_certified':sum(r['hierarchy_certified'] for r in lookups),
                      'both_certified':sum(r['flat_certified'] and r['hierarchy_certified'] for r in lookups),
                      'same_fixed_recommendations':True},
            'ranking_changed_users':sum(not r['exact_flat_same_ranking'] for r in rows),
            'tighter_bound_users':sum(r['exact_bound_same_item']<r['flat_bound_same_item']-1e-8 for r in rows),
            'candidate_retrieval_recall_mean':float(np.mean([r['retrieved_positive_count']/r['relevant_count'] if r['relevant_count'] else 0 for r in rows])),
            'facets_range':[min(r['facets'] for r in rows),max(r['facets'] for r in rows)],
            'pair_matrix_ms':{'p50':float(np.median([r['solve_ms'] for r in rows])), 'p95':float(np.quantile([r['solve_ms'] for r in rows],.95))}}


def test():
    if (OUT/'results.json').exists(): raise RuntimeError('Test already completed; do not retune or overwrite.')
    started=time.perf_counter(); p,corpus,ratings=load_inputs()
    selection=json.loads((OUT/'validation.json').read_text())
    if selection['protocol_sha256']!=digest(p): raise ValueError('Selection protocol mismatch.')
    train,val,future=split_frames(ratings,p['train_end'],p['validation_end']); history=pd.concat([train,val])
    x,genres,index=matrices(corpus); excluded=set(p['validation_users']+p['test_users'])
    bg=background(history,len(x),excluded); cases=cases_for(p['test_users'],history,future,corpus,x,genres,bg)
    extension=json.loads((OUT/'baseline-extension-protocol.json').read_text())
    if selection['extension_protocol_sha256']!=digest(extension): raise ValueError('Extension protocol mismatch.')
    bg['ease']=fit_ease(bg['gram'],selection['chosen_ease_lambda'])
    rows=[]
    for n,c in enumerate(cases):
        gammas=sorted(set([selection['chosen_gamma'],p['fixed_nonzero_gamma']]))
        rows.extend(evaluate_case(c,selection['chosen_alpha'],gammas,corpus,x,index,bg,p['missing_fractions'],lookup=True))
        if (n+1)%16==0: print(json.dumps({'stage':'test','users':n+1,'total':len(cases),'seconds':round(time.perf_counter()-started,1)}),flush=True)
    report={'protocol_sha256':digest(p),'extension_protocol_sha256':digest(extension),
            'selection_sha256':digest(selection),'chosen_alpha':selection['chosen_alpha'],
            'chosen_gamma':selection['chosen_gamma'],'by_mask':{},'fixed_nonzero_by_mask':{},'seconds':time.perf_counter()-started,
            'environment':{'python':platform.python_version(),'numpy':np.__version__,'machine':platform.machine()},
            'scope':p['scope'], 'first_test_run':True}
    for fraction in p['missing_fractions']:
        report['by_mask'][str(fraction)]=summary([r for r in rows if r['missing_fraction']==fraction and r['gamma']==selection['chosen_gamma']],corpus,bg)
        report['fixed_nonzero_by_mask'][str(fraction)]=summary([r for r in rows if r['missing_fraction']==fraction and r['gamma']==p['fixed_nonzero_gamma']],corpus,bg)
    (OUT/'test-per-user.json').write_text(json.dumps(rows,indent=2)+'\n')
    (OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)


def audit():
    """Additional declared full-catalog and integrity audit; no model retuning."""
    if (OUT/'audit.json').exists(): raise RuntimeError('Audit exists; preserve completed evidence.')
    p,corpus,ratings=load_inputs(); selection=json.loads((OUT/'validation.json').read_text())
    report=json.loads((OUT/'results.json').read_text()); rows=json.loads((OUT/'test-per-user.json').read_text())
    contract=json.loads((OUT/'full-catalog-audit-protocol.json').read_text())
    train,val,future=split_frames(ratings,p['train_end'],p['validation_end']);history=pd.concat([train,val])
    x,genres,index=matrices(corpus);excluded=set(p['validation_users']+p['test_users'])
    bg=background(history,len(x),excluded);bg['ease']=fit_ease(bg['gram'],selection['chosen_ease_lambda'])
    cases=cases_for(p['test_users'],history,future,corpus,x,genres,bg)
    full_rows=[]
    for case in cases:
        scores=prepare_scores(case,selection['chosen_alpha'],bg)
        tops={name:ranking(scores[name],case['available'],5) for name in contract['methods']}
        full_rows.append({'user':case['user'],'metrics':{name:ranking_metrics(top,case['relevant'],5) for name,top in tops.items()},
                          'rankings':tops,'candidates':len(case['available']),'relevant_count':len(case['relevant'])})
    full_results={name:{metric:bootstrap_mean([r['metrics'][name][metric] for r in full_rows])
                        for metric in ('ndcg','recall','precision','map')} for name in contract['methods']}
    checks=[]
    for row in rows:
        assert row['lookup']['hierarchy_queries']<=row['lookup']['flat_queries']
        assert not row['lookup']['flat_certified'] or row['lookup']['hierarchy_certified']
        assert row['lookup']['fixed_ranking']==row['rankings']['hybrid']
        assert len(row['pool'])==len(set(row['pool']))
        if row['gamma']==0:
            assert row['rankings']['flat_regret']==row['rankings']['hierarchy_regret']==row['rankings']['hybrid']
    masks={}
    for fraction in p['missing_fractions']:
        subset=[r for r in rows if r['missing_fraction']==fraction and r['gamma']==p['fixed_nonzero_gamma']]
        positive=[r for r in subset if r['relevant_count']>0]
        savings=[r['lookup']['flat_queries']-r['lookup']['hierarchy_queries'] for r in subset]
        both=[r for r in subset if r['lookup']['flat_certified'] and r['lookup']['hierarchy_certified']]
        # Costs are capped and may be zero even when no certificate is possible.
        failed=[r for r in subset if not r['lookup']['flat_certified'] and not r['lookup']['hierarchy_certified']]
        false_cheap=sum(r['lookup']['flat_queries']==0 for r in failed)
        means=report['fixed_nonzero_by_mask'][str(fraction)]['lookup']
        masks[str(fraction)]={'positive_target_user_ndcg':{name:bootstrap_mean([r['metrics'][name]['ndcg'] for r in positive]) for name in subset[0]['metrics']},
                             'relative_mean_query_reduction':1-means['hierarchy_queries']['mean']/means['flat_queries']['mean'],
                             'users_with_savings':sum(v>0 for v in savings),
                             'mean_savings_among_users_with_savings':float(np.mean([v for v in savings if v>0])) if any(v>0 for v in savings) else 0,
                             'both_certified_users':len(both),
                             'both_certified_paired_saved_queries':bootstrap_mean([r['lookup']['flat_queries']-r['lookup']['hierarchy_queries'] for r in both]),
                             'neither_certified_users':len(failed), 'neither_certified_with_zero_queries':false_cheap,
                             'warnings':['Capped-cost mean is a resource metric, not successful certification for every user.',
                                         'Paired savings among both-certified users is a descriptive selected subset, not a new primary endpoint.']}
    result={'protocol_sha256':digest(p),'audit_protocol_sha256':digest(contract),'results_sha256':digest(report),
            'test_users':len(full_rows),'available_movies':int(bg['available'].sum()),'background_ratings':int((~history.user.isin(excluded)).sum()),
            'candidate_range':[min(r['candidates'] for r in full_rows),max(r['candidates'] for r in full_rows)],
            'full_catalog_baselines':full_results,'by_mask':masks,
            'verified_invariants':['disjoint validation/test users','no future ratings in background fit or profiles',
                                   'same fixed recommendations for the two lookup stopping rules','coherent cost never exceeds propagated-flat cost on the shared schedule',
                                   'zero selected theme weight exactly preserves hybrid ranking','unique candidate identities','frozen corpus/ratings/protocol hashes'],
            'test_rows':len(rows),'unavailable_test_positive_targets':sum(c['unavailable_positives'] for c in cases),
            'limits':['Full-catalog baseline audit is separate from same-pool primary comparison.',
                      'A full-catalog hierarchy reranking experiment was not performed.',
                      'Observed ratings reflect historical exposure; unobserved nonrelevance is an offline approximation.',
                      'LTO absence is not an independently verified negative theme label.',
                      '25% preference-width intervals were a fixed sensitivity assumption, not calibrated user uncertainty.']}
    (OUT/'full-catalog-per-user.json').write_text(json.dumps(full_rows,indent=2)+'\n')
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


def cost_audit():
    """Replay recorded stopping prefixes to measure the cost of certification."""
    if (OUT/'compute-cost.json').exists(): raise RuntimeError('Preserve completed timing audit.')
    p,corpus,ratings=load_inputs(); selection=json.loads((OUT/'validation.json').read_text())
    rows=json.loads((OUT/'test-per-user.json').read_text())
    rows={r['user']:r for r in rows if r['missing_fraction']==.5 and r['gamma']==p['fixed_nonzero_gamma']}
    train,val,future=split_frames(ratings,p['train_end'],p['validation_end']);history=pd.concat([train,val])
    x,genres,index=matrices(corpus);excluded=set(p['validation_users']+p['test_users'])
    bg=background(history,len(x),excluded);cases=cases_for(p['test_users'],history,future,corpus,x,genres,bg)
    records=[]
    # One discarded warm-up for the native cut backend.
    pair_gap([None, None],[None,None],[1,-1],[1,-1],[(1,0)])
    for case in cases:
        row=rows[case['user']];pool=row['pool'];positions,mid,lower,upper,edges,prior=active_model(case,corpus,x,index)
        reference=x[np.ix_(pool,positions)].astype(int)
        rng=np.random.default_rng(SEED+case['user']*11+50);missing=rng.random(reference.shape)<.5
        state=[list(propagate([None if missing[i,j] else int(reference[i,j]) for j in range(len(positions))],edges)) for i in range(len(pool))]
        base=np.rint(1000*prepare_scores(case,selection['chosen_alpha'],bg)['hybrid'][pool]).astype(int)
        timings={'flat':0.,'hierarchy':0.};look=row['lookup']
        steps=max(look['flat_queries'],look['hierarchy_queries'])
        for step in range(steps+1):
            for name,stop in [('flat',look['flat_queries']),('hierarchy',look['hierarchy_queries'])]:
                if step>stop:continue
                clock=time.perf_counter();bound=0.
                for j in range(1,len(state)):
                    value=(flat_gap(state[0],state[j],lower,upper) if name=='flat' else pair_gap(state[0],state[j],lower,upper,edges).value)
                    bound=max(bound,.5*value+float(base[j]-base[0]))
                timings[name]+=(time.perf_counter()-clock)*1000
            if step<steps:
                i,j=look['query_sequence'][step]
                clock=time.perf_counter();state[i][j]=int(reference[i,j]);state=[list(propagate(s,edges)) for s in state]
                elapsed=(time.perf_counter()-clock)*1000
                if step<look['flat_queries']:timings['flat']+=elapsed
                if step<look['hierarchy_queries']:timings['hierarchy']+=elapsed
        records.append({'user':case['user'],'flat_ms':timings['flat'],'hierarchy_ms':timings['hierarchy'],
                        'saved_queries':look['flat_queries']-look['hierarchy_queries']})
    delta=[r['hierarchy_ms']-r['flat_ms'] for r in records];saved=[r['saved_queries'] for r in records]
    result={'protocol_sha256':digest(p),'users':len(records),'mask':.5,
            'timing_scope':'Supplemental post-result single replay on this Mac; certification-prefix computation including propagation, excluding fit, retrieval, source I/O and annotation latency. Flat always timed first; exploratory timing only.',
            'flat_ms':bootstrap_mean([r['flat_ms'] for r in records]),'hierarchy_ms':bootstrap_mean([r['hierarchy_ms'] for r in records]),
            'added_compute_ms':bootstrap_mean(delta),'saved_queries':bootstrap_mean(saved),
            'break_even_uniform_annotation_latency_ms':float(np.mean(delta)/np.mean(saved)),
            'interpretation':'Conditional mean total-latency tradeoff: mean added compute divided by mean saved lookups. No actual human or model annotation latency is measured; cheap existing tags may make the exact certificate unnecessary.'}
    (OUT/'compute-cost-per-user.json').write_text(json.dumps(records,indent=2)+'\n')
    (OUT/'compute-cost.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['freeze','validate','test','audit','cost-audit'])
    parser.add_argument('--out',type=Path,default=OUT,help='Separate replication directory; completed runs are never overwritten.')
    args=parser.parse_args();OUT=args.out
    {'freeze':freeze,'validate':validate,'test':test,'audit':audit,'cost-audit':cost_audit}[args.command]()
