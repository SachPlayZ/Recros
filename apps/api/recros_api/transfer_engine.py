"""Source-backed candidate discovery with explicit intent and uncertainty.

The intervals describe a binary source-feature model, never personal liking.
Quote validation establishes provenance only. Interpretations may be wrong.
"""
from __future__ import annotations

from fractions import Fraction as F
import hashlib
from itertools import product
import json
from pathlib import Path

from .decision import Problem, World, plan

ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = ROOT/'demo/transfer/annotated.json'
FEATURES = {
    'inquiry': {'label': 'Investigation and discovery',
                'description': 'A search, puzzle, evaluation, or problem-solving process.',
                'definition': 'Explicit investigation, discovery through searching, evaluating an unknown, or technical problem solving. A mystery genre alone is insufficient.'},
    'unease': {'label': 'An unsettling atmosphere',
               'description': 'An ominous setting or a presentation described as unsettling.',
               'definition': 'Explicit ominous, unsettling, hallucinatory or threatening presentation or atmosphere. Ordinary danger in an adventure is insufficient.'},
    'interiority': {'label': 'Inner feelings and reflection',
                    'description': 'A focus on personal feelings, memory, or self-reflection.',
                    'definition': 'Explicit focus on inner feelings, personal reflection, memory, identity or subjective fears. A character simply appearing is insufficient.'},
    'connection': {'label': 'Care and human connection',
                   'description': 'People caring for, helping, or reconnecting with one another.',
                   'definition': 'Explicit mutual support, caregiving, reconnection, belonging or human bonding. Merely naming a group is insufficient.'},
}


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def load_catalog(path=None):
    return json.loads(Path(path or CATALOG_PATH).read_text())


def validate_evidence(item):
    annotation = item.get('annotation', {})
    text = item.get('evidence_text', '')
    rows, rejected, seen = [], [], set()
    if annotation.get('evidence_sha256') != text_hash(text):
        return [], [{'reason': 'Source version changed or annotation missing.'}]
    for claim in annotation.get('claims', []):
        if not isinstance(claim, dict):
            rejected.append({'reason': 'Malformed claim.'})
            continue
        feature, quote = claim.get('feature'), claim.get('quote')
        if feature not in FEATURES:
            reason = 'Unknown feature.'
        elif feature in seen:
            reason = 'Duplicate feature.'
        elif not isinstance(quote, str) or len(quote.strip()) < 8 or quote not in text:
            reason = 'Quotation is not an exact substantial span of the current source.'
        else:
            reason = None
        if reason:
            rejected.append({'claim': claim, 'reason': reason})
        else:
            rows.append({'feature': feature, 'quote': quote,
                         'source_url': item['source_url'],
                         'source_kind': item.get('source_kind', ''),
                         'evidence_kind': item.get('evidence_kind', '')})
            seen.add(feature)
    return rows, rejected


def select(catalog, target_domain, goals, *, inspected=True, removed=None,
           excluded_ids=(), max_regret=F(1, 4)):
    """Recommend only within the declared source-feature utility model.

    Missing features retain [0,1]. They are never factual negative labels.
    Independent interval corners are an explicit conservative assumption.
    No user/target ratings are consumed by this function.
    """
    if target_domain not in ('movie', 'book', 'music'):
        raise ValueError('Unknown target domain.')
    if len(goals) > 2 or len(set(goals)) != len(goals) or any(g not in FEATURES for g in goals):
        raise ValueError('Choose one or two distinct supported criteria.')
    if not isinstance(max_regret, F) or not 0 <= max_regret <= 1:
        raise ValueError('Invalid model regret bound.')
    if not goals:
        return {'kind': 'ask_user', 'message': 'Choose what you want from this request.',
                'candidates': [], 'trace': ['No request criterion supplied.']}
    items = sorted((i for i in catalog['items'] if i['domain'] == target_domain
                    and i['id'] not in excluded_ids), key=lambda i: i['id'])
    if not items:
        return {'kind': 'abstain', 'message': 'No eligible candidates in the evidence catalog.',
                'candidates': [], 'trace': ['No eligible items.']}
    if len(items) > 10:
        raise ValueError('This bounded research model supports at most ten candidates per domain.')
    rows = []
    for item in items:
        claims, rejected = validate_evidence(item) if inspected else ([], [])
        claims = [c for c in claims if not removed or
                  (item['id'], c['feature']) != (removed['item_id'], removed['feature'])]
        selected = [c for c in claims if c['feature'] in goals]
        missing = [g for g in goals if g not in {c['feature'] for c in selected}]
        lower = F(len(selected), len(goals))
        rows.append({'id': item['id'], 'title': item['title'], 'creators': item.get('creators', ''),
                     'domain': item['domain'], 'source_url': item['source_url'],
                     'source_kind': item.get('source_kind', ''),
                     'evidence_text': item['evidence_text'] if inspected else None,
                     'evidence': selected, 'missing_features': missing,
                     'rejected_claims': rejected, 'lower': lower, 'upper': F(1)})
    if not inspected:
        return {'kind': 'inspect_evidence', 'message': 'Retrieve the cached passages before judging a match.',
                'candidates': [{k:v for k,v in r.items() if k not in ('lower','upper')} for r in rows],
                'trace': ['Intent supplied.', 'Candidate evidence has not been inspected.']}
    # Enumerating endpoints suffices for a deterministic minimax-regret choice.
    # Each scalar interval already conservatively allows any missing criteria.
    corners = [tuple(sorted({r['lower'], r['upper']})) for r in rows]
    worlds = tuple(World(f'corner-{n}', tuple(values))
                   for n, values in enumerate(product(*corners)))
    problem = Problem('source-feature-match', tuple(r['id'] for r in rows), worlds, (), max_regret)
    decision = plan(problem, 0)
    best = decision if decision['kind']=='recommend' else decision['best_recommendation']
    eligible = [r for r in rows if r['lower'] > 0 and F(1)-r['lower'] <= max_regret]
    # With a single candidate, relative regret is zero even without any evidence.
    # A positive evidence floor prevents that trivial certificate from granting fit.
    supported = decision['kind']=='recommend' and best['item'] in {r['id'] for r in eligible}
    trace = ['Intent supplied.', f'Retrieved {len(items)} cached source records.',
             'Missing criteria remain unknown.',
             f'Require at least {float(1-max_regret):.2f} of requested criteria to have source support, even with one candidate.',
             f'Checked {len(worlds)} interval corners in the declared feature model.']
    return {'kind': 'recommend' if supported else 'abstain',
            'item_id': best['item'] if supported else None,
            'message': 'Evidence-backed candidates to explore.' if supported else
                       'The current passages do not support enough of your request to choose confidently.',
            'goals': goals, 'target_domain': target_domain,
            'candidates': [{**{k:v for k,v in r.items() if k not in ('lower','upper')},
                            'score_interval': [float(r['lower']),float(r['upper'])],
                            'worst_case_regret': float(max((o['upper']-r['lower'] for o in rows if o['id']!=r['id']),default=F(0))),
                            'eligible': r['id'] in {e['id'] for e in eligible}}
                           for r in sorted(rows,key=lambda r:(-r['lower'],r['id']))],
            'certificate': {'modeled_regret': float(best['loss']), 'bound': float(max_regret),
                            'worlds_checked': len(worlds), 'witness': {k:(float(v) if isinstance(v,F) else v)
                                                                      for k,v in best['witness'].items()},
                            'minimum_source_support':float(1-max_regret),
                            'scope': 'Conditional on the binary feature interpretation and independent intervals. '
                                     'It does not bound liking, fright, engagement or satisfaction.'},
            'trace': trace,
            'scope': 'Project-selected evidence catalog. Quotes come from the supplied dataset summaries or attributed source paraphrases. '
                     'Exact quotations establish provenance; their feature interpretation needs human review.'}


def discover(catalog, target_domain, goals, *, inspected=True, removed=None, excluded_ids=()):
    current = select(catalog,target_domain,goals,inspected=inspected,removed=removed,excluded_ids=excluded_ids)
    if removed:
        baseline = select(catalog,target_domain,goals,inspected=inspected,excluded_ids=excluded_ids)
        current['intervention'] = {'removed': removed, 'before_kind': baseline['kind'],
                                   'before_item_id': baseline.get('item_id'),
                                   'changed_choice': (baseline['kind'],baseline.get('item_id')) !=
                                                     (current['kind'],current.get('item_id'))}
    return current
