from copy import deepcopy
from fractions import Fraction

import pytest

from recros_api.deliberation import (
    act, browser_view, choose, make_case, new_state, public_view, receipt, scripted_cases,
)
from recros_ml.research.policy_benchmark import parse_decisions, run_local


def test_unknown_private_assignment_does_not_leak_into_any_policy_input():
    a = new_state(make_case('movie:manchester', 'music', order=0))
    b = new_state(make_case('movie:manchester', 'music', order=1))
    assert public_view(a) == public_view(b)
    for method in ('exact', 'one_step', 'information_gain', 'always_ask', 'always_inspect', 'no_actions'):
        assert choose(a, method) == choose(b, method)
    a = act(a, 'ask_user', answer='friendship')
    b = act(b, 'ask_user', answer='friendship')
    assert public_view(a) == public_view(b)
    assert public_view(act(a, 'inspect_evidence')) != public_view(act(b, 'inspect_evidence'))


def test_exact_plan_uses_complementarity_and_refuses_insufficient_budget():
    state = new_state(make_case('movie:manchester', 'music'))
    assert choose(state)['loss'] == Fraction(3, 50)
    assert choose(state, 'one_step')['kind'] == 'abstain'
    one = new_state(make_case('movie:manchester', 'music', budget=1))
    assert choose(one)['kind'] == 'abstain'


def test_unmodeled_or_changed_preference_invalidates_certificate():
    state = new_state(make_case('movie:manchester', 'music'))
    stopped = act(state, 'ask_user', answer='none')
    assert stopped['status'] == 'outside_model'
    assert stopped['terminal']['certificate_valid'] is False
    assert stopped['terminal']['loss'] is None
    with pytest.raises(ValueError):
        act(stopped, 'recommend', item='A')
    known = new_state(make_case('movie:manchester', 'music', condition='both_known'),
                      initial_preference='grief and loss')
    assert act(known, 'ask_user', answer='friendship')['status'] == 'outside_model'


def test_budget_and_once_only_actions_are_enforced_without_mutating_input():
    state = new_state(make_case('movie:manchester', 'music', budget=1))
    before = deepcopy(state)
    with pytest.raises(ValueError):
        act(state, 'ask_user', answer='fabricated')
    assert state == before
    once = act(state, 'inspect_evidence')
    assert state == before
    with pytest.raises(ValueError):
        act(once, 'ask_user', answer='friendship')
    twice = new_state(make_case('movie:manchester', 'music'))
    with pytest.raises(ValueError):
        act(act(twice, 'inspect_evidence'), 'inspect_evidence')


def test_all_cases_grounded_and_truth_matches_declared_assignment():
    cases = scripted_cases()
    assert len(cases) == 24
    assert len({(c['source']['domain'], c['target']) for c, _ in cases}) == 6
    for c, preference in cases:
        s = new_state(c, initial_preference=preference if c['condition'] in ('both_known', 'item_fact_unknown') else None)
        candidates = receipt(s)
        assert candidates[0]['concept'] == c['themes'][c['assignment']]
        assert candidates[1]['concept'] == c['themes'][1-c['assignment']]
        assert all(i['quote'] in i['description'] for i in candidates)
        view = browser_view(s)
        if not s['inspected']:
            assert view['candidates'] == [{'alias':'A'}, {'alias':'B'}]
            assert 'evaluation_candidates' not in view


def test_strong_baseline_tie_and_coverage_are_reported():
    results = run_local(scripted_cases())
    for method in ('exact', 'information_gain'):
        rows = results[method]['episodes']
        assert len(rows) == 24
        assert all(r['completed'] and r['scripted_theme_match'] for r in rows)
        assert sum(r['total_modeled_loss'] for r in rows) == pytest.approx(.72)
    greedy = results['one_step']['episodes']
    assert sum(r['terminal'] == 'abstain' for r in greedy) == 6


@pytest.mark.parametrize('response', [
    {'decisions': []},
    {'decisions': [{'case_id':'x','kind':'invent'}]},
    {'decisions': [{'case_id':'x','kind':'recommend'}]},
    {'decisions': [{'case_id':'x','kind':'ask_user','answer':'friendship'}]},
    {'decisions': [{'case_id':'y','kind':'abstain'}]},
])
def test_invalid_model_outputs_are_not_silently_repaired(response):
    with pytest.raises(ValueError):
        parse_decisions(response, {'x'})
