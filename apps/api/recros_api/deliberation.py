"""Controlled, two-candidate cross-domain tasks over the sourced demo catalog.

Real item descriptions; hypothetical theme-matching utilities. The curated pair
contains one example of each theme by construction. This is not full-catalog
personalization. Private item assignments never enter the pre-inspection view.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import random
import time

from .bridges import verified_facets
from .decision import Action, Problem, World, plan, recommendation


ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = ROOT / 'demo' / 'catalog.real.deepseek.annotated.json'
THEMES = ('grief and loss', 'friendship', 'resistance to authority', 'space exploration')
CONDITIONS = ('both_unknown', 'preference_unknown', 'item_fact_unknown', 'both_known')
METHODS = ('exact', 'one_step', 'information_gain', 'always_ask', 'always_inspect', 'no_actions')


def catalog():
    data = json.loads(CATALOG_PATH.read_text())
    if any(not verified_facets(i) for i in data['items']):
        raise ValueError('The curated catalog has stale or missing evidence')
    return data


def make_case(seed_id: str, target: str, condition: str = 'both_unknown',
              order: int = 0, budget: int = 2) -> dict:
    data = catalog()
    source = next((i for i in data['items'] if i['id'] == seed_id), None)
    if source is None or target not in ('movie', 'book', 'music'):
        raise ValueError('Unknown starting work or target domain')
    if source['domain'] == target:
        raise ValueError('Choose a different target domain')
    if condition not in CONDITIONS or budget not in (0, 1, 2):
        raise ValueError('Unknown condition or action budget')
    first = next(f['concept'] for f in verified_facets(source) if f['concept'] in THEMES)
    second = THEMES[(THEMES.index(first) + 1) % len(THEMES)]
    pair = []
    for concept in (first, second):
        item = next(i for i in data['items'] if i['domain'] == target and
                    concept in {f['concept'] for f in verified_facets(i)})
        pair.append(deepcopy(item))
    if order % 2:
        pair.reverse()
    return {'source': deepcopy(source), 'target': target, 'themes': [first, second],
            'condition': condition, 'budget': budget, 'items': pair,
            'assignment': order % 2,
            'catalog_sha256': hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(),
            'model': data['annotation_run']['requested_model']}


def new_state(case: dict, mode='demo', initial_preference: str | None = None,
              method='exact') -> dict:
    if mode not in ('demo', 'personal') or method not in METHODS:
        raise ValueError('Invalid mode or method')
    known = case['condition'] in ('item_fact_unknown', 'both_known')
    if known and initial_preference not in case['themes']:
        raise ValueError('This condition requires an initial preference')
    if not known and initial_preference is not None:
        raise ValueError('An unknown preference must not be supplied initially')
    now = time.time()
    return {'case': case, 'mode': mode, 'method': method,
            'preference': initial_preference if known else None,
            'inspected': case['condition'] in ('preference_unknown', 'both_known'),
            'history': [], 'remaining': case['budget'], 'revision': 0,
            'status': 'active', 'terminal': None, 'created_at': now,
            'updated_at': now, 'ratings': None, 'feedback': None}


def problem_for(state: dict) -> Problem:
    c = state['case']
    p_known = c['themes'].index(state['preference']) if state['preference'] else None
    worlds, ps, fs = [], [], []
    for p in (0, 1):
        for f in (0, 1):
            if (p_known is not None and p != p_known) or (state['inspected'] and f != c['assignment']):
                continue
            worlds.append(World(f'p{p}_f{f}', (F(int(p == f)), F(int(p != f)))))
            ps.append(p)
            fs.append(f)
    used = {h['kind'] for h in state['history']}
    actions = []
    if 'ask_user' not in used:
        actions.append(Action('ask_user', 'ask_user', F(1, 25), tuple(f'preference_{p}' for p in ps)))
    if 'inspect_evidence' not in used:
        actions.append(Action('inspect_evidence', 'inspect_evidence', F(1, 50), tuple(f'assignment_{f}' for f in fs)))
    return Problem('curated_theme_pair', ('A', 'B'), tuple(worlds), tuple(actions))


def choose(state: dict, method: str | None = None) -> dict:
    if state['status'] != 'active':
        return state['terminal']
    p = problem_for(state)
    method = method or state['method']
    budget = state['remaining']
    if method in ('exact', 'one_step', 'no_actions'):
        return plan(p, budget if method == 'exact' else min(budget, int(method == 'one_step')))
    stop = plan(p, 0)
    if not budget:
        return stop
    if method == 'information_gain':
        scored = []
        for action in p.actions:
            counts = Counter(action.observations)
            entropy = -sum(n / len(p.worlds) * math.log2(n / len(p.worlds)) for n in counts.values())
            scored.append((entropy, -float(action.cost), action.id))
        if stop['loss'] == 0 or not scored or max(scored)[0] == 0:
            return stop
        return {'kind': max(scored)[2]}
    if method in ('always_ask', 'always_inspect'):
        first = 'ask_user' if method == 'always_ask' else 'inspect_evidence'
        ids = {a.id for a in p.actions}
        if first in ids:
            return {'kind': first}
        if stop['loss'] == 0:
            return stop
        return {'kind': next(iter(ids))} if ids else stop
    raise ValueError('Unknown policy')


def receipt(state: dict) -> list[dict]:
    c = state['case']
    result = []
    for alias, item in zip(('A', 'B'), c['items']):
        facet = next(f for f in verified_facets(item) if f['concept'] in c['themes'])
        result.append({'alias': alias, 'id': item['id'], 'title': item['title'],
                       'description': item['description'], 'source_url': item['source_url'],
                       'concept': facet['concept'], 'quote': facet['quote'],
                       'description_sha256': item['annotation']['description_sha256']})
    return result


def public_view(state: dict) -> dict:
    """Single allowed input view for both the exact and direct-LLM policies."""
    c = state['case']
    data = {'source': {k: c['source'][k] for k in ('title', 'domain', 'description', 'source_url')},
            'target_domain': c['target'], 'themes': c['themes'],
            'known_preference': state['preference'], 'evidence_inspected': state['inspected'],
            'remaining_actions': state['remaining'], 'status': state['status'],
            'candidates': receipt(state) if state['inspected'] else [{'alias': 'A'}, {'alias': 'B'}],
            'observations': [{k: v for k, v in h.items() if k != 'elapsed_seconds'}
                             for h in state['history']],
            'assumptions': 'Curated pair: one candidate supports each listed theme. '
                           'Utilities are 1 for the stated desired theme, otherwise 0; '
                           'these are hypothetical matching utilities, not measured satisfaction.',
            'abstention_loss': .45, 'action_costs': {'ask_user': .04, 'inspect_evidence': .02},
            'question': f"For {c['target']}, which direction do you want: {c['themes'][0]}, "
                        f"{c['themes'][1]}, or neither / another reason?"}
    if state['status'] == 'active':
        p = problem_for(state)
        data['possible_worlds'] = [
            {'id': w.id, 'utilities': dict(zip(p.items, map(float, w.utilities))),
             'possible_observations': {a.id: a.observations[i] for a in p.actions}}
            for i, w in enumerate(p.worlds)]
        data['available_actions'] = [a.id for a in p.actions] if state['remaining'] else []
    return data


def act(state: dict, kind: str, answer: str | None = None, item: str | None = None) -> dict:
    if state['status'] != 'active':
        raise ValueError('This session is already finished')
    result = deepcopy(state)
    c = result['case']
    event = {'kind': kind, 'elapsed_seconds': round(time.time() - result['updated_at'], 3)}
    if kind in ('ask_user', 'inspect_evidence'):
        if result['remaining'] <= 0:
            raise ValueError('The information-action budget is exhausted')
        if kind in {h['kind'] for h in result['history']}:
            raise ValueError('An information action may be used only once')
        result['remaining'] -= 1
        if kind == 'ask_user':
            if answer == 'none':
                result['status'] = 'outside_model'
                result['terminal'] = {'kind': 'abstain', 'reason': 'Your preference is outside the two-theme model.',
                                      'loss': None, 'certificate_valid': False}
                event['answer'] = answer
            elif answer in c['themes']:
                if result['preference'] is not None and result['preference'] != answer:
                    result['status'] = 'outside_model'
                    result['terminal'] = {'kind': 'abstain', 'reason': 'Your answer changed the initial preference; the model must be rebuilt.',
                                          'loss': None, 'certificate_valid': False}
                else:
                    result['preference'] = answer
                event['answer'] = answer
                event['observation'] = f"preference_{c['themes'].index(answer)}"
            else:
                raise ValueError('Choose a listed theme or none')
        else:
            result['inspected'] = True
            event['observation'] = f"assignment_{c['assignment']}"
            event['evidence'] = receipt(result)
    elif kind == 'recommend':
        if item not in ('A', 'B'):
            raise ValueError('Recommendations must identify A or B')
        p = problem_for(result)
        j = p.items.index(item)
        worst = max(p.worlds, key=lambda w: max(w.utilities) - w.utilities[j])
        regret = max(worst.utilities) - worst.utilities[j]
        result['status'] = 'complete'
        result['terminal'] = {'kind': 'recommend', 'item': item, 'loss': float(regret),
                              'witness': {'world': worst.id, 'regret': float(regret)},
                              'certificate_valid': True,
                              'certificate_scope': 'Declared finite theme-matching model only'}
        event['item'] = item
    elif kind == 'abstain':
        result['status'] = 'complete'
        result['terminal'] = {'kind': 'abstain', 'loss': .45, 'reason': 'Stopped without choosing a candidate.'}
    else:
        raise ValueError('Unknown action')
    result['history'].append(event)
    result['revision'] += 1
    result['updated_at'] = time.time()
    return result


def browser_view(state: dict) -> dict:
    public = public_view(state)
    choice = choose(state)
    p = problem_for(state) if state['status'] == 'active' else None
    result = {**public, 'mode': state['mode'], 'revision': state['revision'],
              'suggested': json.loads(json.dumps(choice, default=float)),
              'rated': state['ratings'] is not None, 'model': state['case']['model'],
              'certificate_note': 'Conditional on these two themes and the curated pair; not a guarantee about your taste.'}
    if p:
        result['current_counterexample'] = json.loads(json.dumps(recommendation(p, tuple(range(len(p.worlds)))), default=float))
    if state['status'] != 'active':
        # Shown only after stopping for evaluation. Never fed back to a policy.
        result['evaluation_candidates'] = receipt(state)
    return result


def scripted_cases(seed: int = 20261014) -> list[tuple[dict, str]]:
    """24 tasks; repeated items and scripted preferences, NOT 24 independent users."""
    rng = random.Random(seed)
    data = catalog()['items']
    cases = []
    pairs = [(a, b) for a in ('movie', 'book', 'music') for b in ('movie', 'book', 'music') if a != b]
    for pair_index, (source_domain, target) in enumerate(pairs):
        theme = THEMES[pair_index % len(THEMES)]
        source = next(i for i in data if i['domain'] == source_domain and theme in
                      {f['concept'] for f in verified_facets(i)})
        for condition_index, condition in enumerate(CONDITIONS):
            c = make_case(source['id'], target, condition, order=(pair_index + condition_index) % 2)
            preference = c['themes'][(pair_index + condition_index // 2) % 2]
            cases.append((c, preference))
    rng.shuffle(cases)
    return cases
