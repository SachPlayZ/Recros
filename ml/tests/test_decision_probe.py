"""Check decision semantics and certificate limits, not a recommendation score."""
from dataclasses import replace
from fractions import Fraction as F
from itertools import combinations

import pytest

from recros_ml.research.decision_probe import (
    compatible_worlds, fixtures, plan, recommendation, replay,
)


def cases():
    return {p.id: p for p in fixtures()}


def test_diagnosis_distinguishes_preference_from_evidence():
    c = cases()
    assert plan(c['preference_unknown'], 1)['kind'] == 'ask_user'
    assert plan(c['item_fact_unknown'], 1)['kind'] == 'inspect_evidence'
    assert plan(c['both_known'], 2)['loss'] == 0
    assert plan(c['uncertain_but_ranking_stable'], 2)['kind'] == 'recommend'


def test_complementarity_defeats_one_step_but_not_two_step_planning():
    p = cases()['both_unknown']
    assert plan(p, 0)['loss'] == F(9, 20)
    assert plan(p, 1)['kind'] == 'abstain'
    two = plan(p, 2)
    assert two['loss'] == F(3, 50)
    for i in range(len(p.worlds)):
        result = replay(p, two, i)
        assert result['terminal_loss'] == 0
        assert {a['action'] for a in result['trace']} == {'ask_preference', 'inspect_item_fact'}


def test_unavailable_evidence_and_high_cost_do_not_force_an_action():
    for name in ('item_evidence_unavailable', 'information_too_costly'):
        assert plan(cases()[name], 2)['kind'] == 'abstain'


def test_witness_attains_bound_for_every_nonempty_world_subset():
    p = cases()['both_unknown']
    for size in range(1, len(p.worlds) + 1):
        for active in combinations(range(len(p.worlds)), size):
            decision = recommendation(p, active)
            actual = [replay(p, decision, i)['terminal_loss'] for i in active]
            assert max(actual) == decision['loss']
            witness = next(i for i in active if p.worlds[i].id == decision['witness']['world'])
            assert replay(p, decision, witness)['terminal_loss'] == decision['loss']


def test_exhaustive_policy_loss_equals_certificate_and_more_budget_cannot_hurt():
    for fixture in fixtures():
        for cost in (F(0), F(1, 100), F(1, 5), F(1)):
            p = replace(fixture, actions=tuple(replace(a, cost=cost) for a in fixture.actions))
            losses = []
            for horizon in range(4):
                decision = plan(p, horizon)
                observed = [replay(p, decision, i)['total_loss'] for i in range(len(p.worlds))]
                assert max(observed) == decision['loss']
                losses.append(decision['loss'])
            assert losses == sorted(losses, reverse=True)


def test_omitted_world_invalidates_real_world_interpretation_of_certificate():
    complete = cases()['both_unknown']
    # Pretending just one world is possible yields a zero-regret certificate.
    decision = recommendation(complete, (0,))
    assert decision['loss'] == 0
    # It can be completely wrong in an omitted world. Never label it confidence.
    assert replay(complete, decision, 1)['terminal_loss'] == 1


def test_unknown_response_and_malformed_models_fail_explicitly():
    p = cases()['both_unknown']
    with pytest.raises(ValueError, match='outside the hypothesis set'):
        compatible_worlds(p, (0, 1), p.actions[0], 'none_of_these')
    with pytest.raises(ValueError):
        replace(p, items=('duplicate', 'duplicate'))
    with pytest.raises(ValueError):
        replace(p, actions=(replace(p.actions[0], cost=F(-1)),))
    with pytest.raises(ValueError):
        plan(p, -1)
    with pytest.raises(ValueError):
        recommendation(p, ())
