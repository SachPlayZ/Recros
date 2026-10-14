"""Detect preference distinctions that a supplied item representation cannot express.

The lower bound is a counting identity for deterministic binary classifiers on
identical feature vectors. It is not a new learning theorem or a test accuracy.
"""
from collections import defaultdict

from .bridges import verified_facets


def audit(profile: dict, catalog: dict) -> dict:
    annotated = {i['id']:i for i in catalog['items']}
    records, pending = [], []
    for item in profile['items']:
        if item.get('identity_status') != 'matched':
            pending.append(item['id'])
            continue
        label = item.get('preference_label')
        if label not in ('like','immense love','dislike'):
            continue
        cached = annotated.get(item['id'], {})
        facets = verified_facets(cached) if cached.get('description') == item.get('description') else []
        features = sorted(f['concept'] for f in facets)
        records.append({**item,'positive':label!='dislike','concepts':features,
                        'facets':facets,
                        'genres_list':sorted(g for g in item.get('genres','').split('|') if g)})
    views = {}
    for name in ('domain_only','domain_and_genres','domain_and_concepts','domain_genres_concepts'):
        groups = defaultdict(list)
        for r in records:
            key = (r['domain'],)
            if name in ('domain_and_genres','domain_genres_concepts'):
                key += (tuple(r['genres_list']),)
            if name in ('domain_and_concepts','domain_genres_concepts'):
                key += (tuple(r['concepts']),)
            groups[key].append(r)
        errors, conflicts = 0, []
        for key, members in groups.items():
            pos = [r for r in members if r['positive']]
            neg = [r for r in members if not r['positive']]
            errors += min(len(pos),len(neg))
            if pos and neg:
                conflicts.append({'feature_vector':key,'positive_ids':[r['id'] for r in pos],
                                  'negative_ids':[r['id'] for r in neg],
                                  'unavoidable_errors':min(len(pos),len(neg)),
                                  'contains_untagged_items':any(not r['concepts'] for r in members)})
        views[name] = {'unavoidable_label_errors':errors,'observed_records':len(records),
                       'conflicts':conflicts}
    genre_conflicts = []
    for g in sorted({g for r in records for g in r['genres_list']}):
        pos = [r['id'] for r in records if r['positive'] and g in r['genres_list']]
        neg = [r['id'] for r in records if not r['positive'] and g in r['genres_list']]
        if pos and neg:
            genre_conflicts.append({'genre':g,'positive_ids':pos,'negative_ids':neg})
    creator_groups = defaultdict(list)
    for r in records:
        creator = r.get('creators', '').strip()
        if creator:
            creator_groups[(r['domain'], creator.casefold())].append(r)
    creator_conflicts = []
    for (domain, _), members in creator_groups.items():
        pos = [r['id'] for r in members if r['positive']]
        neg = [r['id'] for r in members if not r['positive']]
        if pos and neg:
            creator_conflicts.append({'domain':domain,'creator':members[0]['creators'],
                                     'positive_ids':pos,'negative_ids':neg})
    return {'records':records,'pending_identity_ids':pending,'representations':views,
            'shared_genres_with_opposite_labels':genre_conflicts,
            'same_creator_with_opposite_labels':creator_conflicts,
            'scope':'Observed development labels from one participant. For a deterministic binary classifier '
                    'restricted to each supplied feature vector, sum min(positive_count, negative_count) '
                    'is an unavoidable label-error count. This is not a generalization error, a ranking bound, '
                    'or a bound on an LLM allowed additional inputs.',
            'missingness_note':'An empty concept list means this evidence/vocabulary represents no supported '
                               'concept. It does not mean the work has no themes or that untagged works are alike.'}
